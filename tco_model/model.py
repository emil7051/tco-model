# Standard library imports
from datetime import datetime
import logging
from typing import Dict, List, Optional, Tuple, Type, Any, Set, Union, Callable
from functools import lru_cache
import time

# Third-party imports
import numpy as np
import pandas as pd

# Application-specific imports
from .components import (
    AcquisitionCost, BatteryReplacementCost, CarbonTaxCost, CostComponent, 
    EnergyCost, InfrastructureCost, InsuranceCost, MaintenanceCost,
    RegistrationCost, ResidualValue, RoadUserChargeCost
)
from .scenarios import Scenario
from .vehicles import DieselVehicle, ElectricVehicle, Vehicle
from .optimizations import (
    timed, optimize_dataframe, performance_monitor, 
    batch_process, vectorized_calculation, cached
)

# Configure module logger
logger = logging.getLogger(__name__)

# Importing performance monitoring utilities from optimizations module instead


class TCOCalculator:
    """
    Calculates and compares Total Cost of Ownership for electric and diesel vehicles.
    
    This class handles the full TCO calculation workflow including:
    - Determining applicable cost components based on vehicle type and scenario
    - Calculating annual costs for each component
    - Applying discounting and aggregating costs
    - Computing key metrics like LCOD and parity year
    
    Attributes:
        _component_classes (List[Type[CostComponent]]): Ordered list of cost component classes
        _component_cache (Dict): Cache for component instances to avoid repeated initialization
        _calculation_cache (Dict): Cache for calculation results
        _performance_stats (PerformanceMonitor): Performance tracking (using global monitor)
    """

    def __init__(self):
        """Initialize the TCO Calculator with a standard set of cost components."""
        # Define the standard list of component classes to use
        self._component_classes: List[Type[CostComponent]] = [
            AcquisitionCost,
            EnergyCost,
            MaintenanceCost,
            InfrastructureCost,
            BatteryReplacementCost,
            InsuranceCost,
            RegistrationCost,
            CarbonTaxCost,
            RoadUserChargeCost,
            ResidualValue # Keep ResidualValue last as it's often negative
        ]
        # Component instance cache to avoid recreating component objects
        self._component_cache: Dict[Type[CostComponent], CostComponent] = {}
        
        # Calculation results cache
        self._calculation_cache: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking - use the global instance from optimizations module
        self._performance_stats = performance_monitor

    def _get_applicable_components(self, vehicle: Vehicle, scenario: Scenario) -> List[CostComponent]:
        """
        Returns instances of components applicable to the vehicle type and scenario settings.
        
        Args:
            vehicle: The vehicle to calculate costs for
            scenario: The scenario containing calculation parameters
            
        Returns:
            List of applicable cost component instances
        """
        applicable_components = []
        
        # Use cached component instances or create new ones if needed
        for comp_class in self._component_classes:
            # Get or create component instance
            component = self._get_component_instance(comp_class)
            
            # Check if component should be applied to this vehicle/scenario
            if not self._is_component_applicable(component, vehicle, scenario):
                continue
                
            # Reset stateful components for a new calculation run
            self._reset_component_if_needed(component)
                
            applicable_components.append(component)

        return applicable_components

    def _get_component_instance(self, component_class: Type[CostComponent]) -> CostComponent:
        """Get a cached component instance or create a new one if not cached."""
        if component_class not in self._component_cache:
            self._component_cache[component_class] = component_class()
        return self._component_cache[component_class]
    
    def _reset_component_if_needed(self, component: CostComponent) -> None:
        """Reset a stateful component if it has a reset method."""
        if hasattr(component, 'reset') and callable(getattr(component, 'reset')):
            component.reset()
        
    def _is_component_applicable(self, component: CostComponent, vehicle: Vehicle, scenario: Scenario) -> bool:
        """
        Determines if a cost component applies to the given vehicle and scenario.
        
        Args:
            component: The cost component to check
            vehicle: The vehicle to check applicability for
            scenario: The scenario containing configuration parameters
            
        Returns:
            True if the component is applicable, False otherwise
        """
        # EV-specific components (only apply to ElectricVehicle)
        if isinstance(component, (InfrastructureCost, BatteryReplacementCost)):
            if not isinstance(vehicle, ElectricVehicle):
                return False
                
            # Additionally check if battery replacement is enabled
            if isinstance(component, BatteryReplacementCost) and not scenario.battery_replacement_config.enable_battery_replacement:
                return False
        
        # Diesel-specific components (only apply to DieselVehicle)
        if isinstance(component, CarbonTaxCost):
            if not isinstance(vehicle, DieselVehicle) or not scenario.carbon_tax_config.include_carbon_tax:
                return False
        
        # Components that depend on scenario flags
        if isinstance(component, RoadUserChargeCost) and not scenario.road_user_charge_config.include_road_user_charge:
            return False
        
        return True

    @timed("annual_costs_calculation")
    def _calculate_annual_costs_undiscounted(self, vehicle: Vehicle, scenario: Scenario) -> pd.DataFrame:
        """
        Calculate undiscounted annual costs for each applicable component for a single vehicle.
        
        Args:
            vehicle: The vehicle to calculate costs for
            scenario: The scenario containing calculation parameters
            
        Returns:
            DataFrame with undiscounted annual costs by component and year
        """
        # Get applicable components for this vehicle and scenario
        applicable_components = self._get_applicable_components(vehicle, scenario)
        component_names = [comp.__class__.__name__ for comp in applicable_components]
        
        # Initialize base calculation arrays
        analysis_years = scenario.analysis_period_years
        year_indices = np.array(range(analysis_years))
        calendar_years = np.array(scenario.analysis_calendar_years)
        
        # Pre-calculate cumulative mileage for all years (for components that need it)
        annual_mileage = scenario.operational_parameters.annual_mileage_km
        mileage_array = np.concatenate(([0.0], np.cumsum(np.full(analysis_years - 1, annual_mileage))))
        
        # Create dataframe shell
        annual_costs_data = {
            'Year': calendar_years,
            'YearIndex': year_indices,
            **{name: np.zeros(analysis_years) for name in component_names}
        }
        
        # Process each component and calculate costs
        for component in applicable_components:
            comp_name = component.__class__.__name__
            logger.debug(f"Calculating costs for component: {comp_name}")
            annual_costs_data[comp_name] = self._calculate_component_costs(
                component=component,
                years=calendar_years,
                year_indices=year_indices,
                vehicle=vehicle,
                scenario=scenario,
                cumulative_mileage_start_of_year=mileage_array
            )
        
        # Convert to DataFrame and add a Total column
        df = pd.DataFrame(annual_costs_data)
        df = self._add_total_column(df)
        
        # Set Year as index
        df.set_index('Year', inplace=True)
        df.drop(columns=['YearIndex'], inplace=True)
        
        # Optimize the dataframe for memory usage
        return optimize_dataframe(df)

    def _calculate_component_costs(self, component, years, year_indices, vehicle, scenario, cumulative_mileage_start_of_year) -> np.ndarray:
        """
        Calculate costs for a single component across all years, using vectorized calculation if available.
        
        Args:
            component: Cost component to calculate
            years: Array of calendar years
            year_indices: Array of year indices (0-based)
            vehicle: Vehicle object
            scenario: Scenario object
            cumulative_mileage_start_of_year: Array of cumulative mileage at the start of each year index
            
        Returns:
            Array of annual costs for this component
        """
        costs = np.zeros(len(years))
        
        # Try vectorized calculation first if available
        if hasattr(component, 'calculate_vectorized') and callable(getattr(component, 'calculate_vectorized')):
            try:
                vectorized_costs = component.calculate_vectorized(
                    years=years,
                    vehicle=vehicle,
                    scenario=scenario,
                    year_indices=year_indices,
                    total_mileage_km=cumulative_mileage_start_of_year
                )
                costs = np.array(vectorized_costs)
                logger.debug(f"Using vectorized calculation for {component.__class__.__name__}")
                return costs
            except Exception as e:
                logger.error(f"Error in vectorized calculation for {component.__class__.__name__}: {e}", exc_info=True)
                # Fall back to individual year calculation
        
        # Process individual years in batches for better performance
        BATCH_SIZE = 5
        for batch_start in range(0, len(years), BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, len(years))
            batch_years = year_indices[batch_start:batch_end]
            
            # Calculate costs for this batch
            for i, year_index in enumerate(batch_years):
                current_year = years[batch_start + i]
                current_mileage = cumulative_mileage_start_of_year[batch_start + i]
                costs[batch_start + i] = self._calculate_year_cost(
                    component=component,
                    year=current_year,
                    calculation_year_index=year_index,
                    vehicle=vehicle,
                    scenario=scenario, 
                    total_mileage_km=current_mileage
                )
                
        return costs
    
    def _calculate_year_cost(self, component, year, calculation_year_index, vehicle, scenario, total_mileage_km) -> float:
        """Calculate cost for a specific component and year with error handling."""
        try:
            cost = component.calculate_annual_cost(
                year=year,
                vehicle=vehicle,
                scenario=scenario,
                calculation_year_index=calculation_year_index,
                total_mileage_km=total_mileage_km
            )
            return cost if pd.notna(cost) else 0.0
        except Exception as e:
            logger.error(f"Error calculating {component.__class__.__name__} for {vehicle.name} "
                        f"in year index {calculation_year_index}: {e}", exc_info=True)
            return 0.0  # Return zero if calculation fails
    
    def _add_total_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add a Total column summing all cost components and handle missing values."""
        component_cost_columns = [col for col in df.columns if col != 'Year']
        df['Total'] = df[component_cost_columns].sum(axis=1, skipna=True)
        df = df.fillna(0.0)  # Fill any NaN values with 0 for consistency
        return df

    @timed("discounting")
    def _apply_discounting(self, undiscounted_df: pd.DataFrame, scenario: Scenario) -> pd.DataFrame:
        """
        Apply discounting to annual costs to get present values.
        
        Args:
            undiscounted_df: DataFrame with undiscounted annual costs
            scenario: The scenario object containing the discount rate
            
        Returns:
            DataFrame with discounted annual costs
        """
        if undiscounted_df.empty:
            logger.warning("Empty DataFrame provided for discounting, returning empty DataFrame.")
            return pd.DataFrame()
        
        # Make a copy to avoid modifying the original
        discounted_df = undiscounted_df.copy()
        
        # Calculate discount factors using vectorized operations
        years = np.arange(len(discounted_df))
        discount_rate_percent = scenario.economic_parameters.discount_rate_percent_real
        discount_rate = discount_rate_percent / 100.0
        discount_factors = 1 / np.power(1 + discount_rate, years)
        
        # Apply discount factors to all cost columns except 'Year'
        cost_columns = [col for col in discounted_df.columns if col != 'Year']
        discounted_df[cost_columns] = discounted_df[cost_columns].multiply(discount_factors, axis=0)
        
        return optimize_dataframe(discounted_df)

    @cached("tco_calculation:{scenario.name}")
    def calculate(self, scenario: Scenario) -> Dict[str, Any]:
        """
        Perform the full TCO calculation for the given scenario.
        
        Uses caching to avoid redundant calculations for the same scenario.
        
        Args:
            scenario: The Scenario object containing all input parameters.
            
        Returns:
            A dictionary containing detailed results including undiscounted and discounted
            annual costs, total TCO, LCOD, parity year, and analysis years.
        """
        # Start timing the calculation
        start_time = time.time()
        logger.info(f"Starting TCO calculation for scenario: {scenario.name}")
        
        # Initialize results with scenario metadata
        results = self._initialize_results(scenario)
        
        try:
            # Validate vehicle data
            if not self._validate_vehicles(scenario, results):
                return results
            
            # Calculate costs for both vehicle types
            results = self._calculate_vehicle_costs(scenario, results)
            
            # Calculate metrics
            results = self._calculate_comparison_metrics(results, scenario)
            
            # Record total calculation time
            self._record_calculation_time(start_time, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error during TCO calculation: {e}", exc_info=True)
            results['error'] = f"Calculation failed: {e}"
            return results  # Return partial results with error message
    
    def _initialize_results(self, scenario: Scenario) -> Dict[str, Any]:
        """Initialize the results dictionary with scenario metadata."""
        return {
            'scenario_name': scenario.name,
            'analysis_period_years': scenario.analysis_period_years,
            'start_year': scenario.analysis_start_year,
            'discount_rate_percent': scenario.economic_parameters.discount_rate_percent_real,
            'vehicles': {
                'electric': {'name': scenario.electric_vehicle.name, 'costs_calculated': False},
                'diesel': {'name': scenario.diesel_vehicle.name, 'costs_calculated': False}
            },
            'errors': [],
            'warnings': []
        }
    
    def _validate_vehicles(self, scenario: Scenario, results: Dict[str, Any]) -> bool:
        """Validate that both vehicle types are present in the scenario."""
        electric_vehicle = scenario.electric_vehicle
        diesel_vehicle = scenario.diesel_vehicle
        
        if not electric_vehicle or not diesel_vehicle:
            error_msg = "Scenario missing electric or diesel vehicle"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            return False
        
        return True
    
    def _calculate_vehicle_costs(self, scenario: Scenario, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate costs for both vehicle types and add to results."""
        # Get vehicle instances
        electric_vehicle = scenario.electric_vehicle
        diesel_vehicle = scenario.diesel_vehicle
        
        # 1. Calculate undiscounted annual costs for both vehicle types
        logger.info(f"Calculating costs for {electric_vehicle.name} (Electric)")
        electric_undisc = self._calculate_annual_costs_undiscounted(electric_vehicle, scenario)
        
        logger.info(f"Calculating costs for {diesel_vehicle.name} (Diesel)")
        diesel_undisc = self._calculate_annual_costs_undiscounted(diesel_vehicle, scenario)
        
        results['vehicles']['electric']['undiscounted_annual_costs'] = electric_undisc
        results['vehicles']['diesel']['undiscounted_annual_costs'] = diesel_undisc
        
        # 2. Apply discounting
        logger.info("Applying discounting...")
        electric_disc = self._apply_discounting(electric_undisc, scenario)
        diesel_disc = self._apply_discounting(diesel_undisc, scenario)
        
        results['vehicles']['electric']['discounted_annual_costs'] = electric_disc
        results['vehicles']['diesel']['discounted_annual_costs'] = diesel_disc
        
        # 3. Calculate total TCO (sum of *discounted* total costs)
        total_tco_ev = electric_disc['Total'].sum() if not electric_disc.empty else 0
        total_tco_diesel = diesel_disc['Total'].sum() if not diesel_disc.empty else 0
        
        results['vehicles']['electric']['total_discounted_tco'] = total_tco_ev
        results['vehicles']['diesel']['total_discounted_tco'] = total_tco_diesel
        logger.info(f"Total Discounted TCO - EV: {total_tco_ev:,.2f}, Diesel: {total_tco_diesel:,.2f}")
        
        # 4. Calculate Levelized Cost of Driving (LCOD) using discounted TCO
        results['vehicles']['electric']['lcod_aud_per_km'] = self._calculate_lcod(total_tco_ev, scenario)
        results['vehicles']['diesel']['lcod_aud_per_km'] = self._calculate_lcod(total_tco_diesel, scenario)
        
        # 5. Find parity year using *undiscounted* cumulative costs
        results['parity_info'] = self._find_parity_year_undiscounted(
            electric_cumulative_undisc=electric_undisc['Total'].cumsum(),
            diesel_cumulative_undisc=diesel_undisc['Total'].cumsum(),
            year_series=electric_undisc['Year']  # Pass Year series for mapping index to year
        )
        
        return results
    
    def _calculate_comparison_metrics(self, results: Dict[str, Any], scenario: Scenario) -> Dict[str, Any]:
        """Calculate and add comparison metrics to results."""
        # Add LCOD comparison metrics
        ev_lcod = results['vehicles']['electric'].get('lcod_aud_per_km')
        diesel_lcod = results['vehicles']['diesel'].get('lcod_aud_per_km')
        
        if ev_lcod is not None and diesel_lcod is not None:
            results['lcod_difference'] = diesel_lcod - ev_lcod
            results['lcod_percentage_savings'] = ((diesel_lcod - ev_lcod) / diesel_lcod * 100) if diesel_lcod > 0 else 0
        
        # Add TCO comparison metrics
        ev_tco = results['vehicles']['electric'].get('total_discounted_tco', 0)
        diesel_tco = results['vehicles']['diesel'].get('total_discounted_tco', 0)
        
        results['tco_difference'] = diesel_tco - ev_tco
        results['tco_ev_to_diesel_ratio'] = ev_tco / diesel_tco if diesel_tco != 0 else float('inf')
        
        # Add parity information
        parity_info = results['parity_info']
        if parity_info['parity_year_undiscounted'] is not None:
            results['years_to_parity'] = parity_info['parity_year_undiscounted'] - 1  # First year is year 1, so adjust for years count
            logger.info(f"Undiscounted TCO Parity Year: {parity_info['parity_year_undiscounted']}")
        else:
            results['years_to_parity'] = None
            logger.info("Undiscounted TCO Parity not reached in analysis period")
            
        return results
    
    def _record_calculation_time(self, start_time: float, results: Dict[str, Any]) -> None:
        """Record the calculation time and add to results."""
        elapsed = time.time() - start_time
        self._performance_stats.record("total_calculation", elapsed)
        results['calculation_time_s'] = round(elapsed, 4)
    
    def invalidate_calculation_cache(self, scenario_name_prefix: str = "") -> None:
        """
        Invalidates the calculation cache to force recalculation on next call.
        Call this method when scenario parameters change.
        """
        self._calculation_cache.clear()
        logger.info("TCO calculation cache cleared")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for recent calculations.
        
        Returns:
            Dictionary with performance metrics
        """
        return self._performance_stats.get_report()
    
    def reset_performance_stats(self) -> None:
        """Reset all performance tracking metrics."""
        self._performance_stats.reset()
        logger.info("Performance statistics reset.")

    @timed("lcod_calculation")
    def _calculate_lcod(self, total_discounted_tco: float, scenario: Scenario) -> Optional[float]:
        """
        Calculate Levelized Cost of Driving (per km).
        
        Uses total discounted TCO divided by total *undiscounted* mileage.
        
        Args:
            total_discounted_tco: The total discounted TCO value
            scenario: The scenario containing mileage and analysis period data
            
        Returns:
            LCOD value in AUD/km or None if calculation fails
        """
        if total_discounted_tco is None or np.isnan(total_discounted_tco):
            logger.warning("Cannot calculate LCOD with invalid TCO value")
            return None
            
        # Calculate total undiscounted mileage over the analysis period
        total_undiscounted_km = scenario.operational_parameters.annual_mileage_km * scenario.analysis_period_years
        
        if total_undiscounted_km == 0:
            logger.warning("Total undiscounted mileage is zero, cannot calculate LCOD.")
            return None
            
        lcod = total_discounted_tco / total_undiscounted_km
        return lcod

    @timed("parity_calculation")
    def _find_parity_year_undiscounted(
        self, 
        electric_cumulative_undisc: pd.Series, 
        diesel_cumulative_undisc: pd.Series, 
        year_series: pd.Series
    ) -> Optional[int]:
        """
        Find the first year when undiscounted electric cumulative TCO is <= undiscounted diesel cumulative TCO.
        
        Args:
            electric_cumulative_undisc: Cumulative electric vehicle costs (undiscounted)
            diesel_cumulative_undisc: Cumulative diesel vehicle costs (undiscounted)
            year_series: The year numbers corresponding to each cost entry
            
        Returns:
            The first year when EV TCO <= diesel TCO, or None if parity is never reached
        """
        try:
            if electric_cumulative_undisc.empty or diesel_cumulative_undisc.empty:
                logger.warning("Empty cost series provided for parity calculation")
                return None
                
            # Find indices where electric <= diesel
            parity_indices = electric_cumulative_undisc.index[electric_cumulative_undisc <= diesel_cumulative_undisc]
            
            if not parity_indices.empty:
                first_parity_index = parity_indices[0]
                # Map the DataFrame index back to the actual analysis year (using the 'Year' column)
                parity_year_number = year_series.iloc[first_parity_index]
                return int(parity_year_number)
            else:
                logger.info("Parity not reached within analysis period")
                return None  # Parity not reached
                
        except IndexError:
            logger.warning("Index error while finding parity year, likely due to empty series.")
            return None
        except Exception as e:
            logger.error(f"Error finding undiscounted parity year: {e}", exc_info=True)
            return None
            
    def parallel_calculate(self, scenarios: List[Scenario]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate TCO for multiple scenarios in parallel or sequentially.
        
        Args:
            scenarios: List of scenarios to analyze
            
        Returns:
            Dictionary mapping scenario names to their results
        """
        results = {}
        
        # For now, implement sequential processing
        # This could be enhanced with parallel processing in the future
        for scenario in scenarios:
            results[scenario.name] = self.calculate(scenario)
            
        return results
