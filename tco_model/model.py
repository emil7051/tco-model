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
        _performance_stats (PerformanceStats): Performance tracking
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
            if comp_class not in self._component_cache:
                self._component_cache[comp_class] = comp_class()
            
            instance = self._component_cache[comp_class]
            
            # Perform applicability checks
            if not self._is_component_applicable(instance, vehicle, scenario):
                continue
                
            # Reset stateful components for a new calculation run
            if hasattr(instance, 'reset') and callable(getattr(instance, 'reset')):
                instance.reset()
                
            applicable_components.append(instance)

        return applicable_components
        
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
        # Basic applicability checks
        if isinstance(component, (InfrastructureCost, BatteryReplacementCost)) and not isinstance(vehicle, ElectricVehicle):
            return False  # Skip EV-only costs for Diesel
        
        if isinstance(component, CarbonTaxCost):
            if not isinstance(vehicle, DieselVehicle) or not scenario.include_carbon_tax:
                return False  # Skip carbon tax if not Diesel or not included
        
        if isinstance(component, RoadUserChargeCost) and not scenario.include_road_user_charge:
            return False  # Skip RUC if not included
        
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
        applicable_components = self._get_applicable_components(vehicle, scenario)
        component_names = [comp.__class__.__name__ for comp in applicable_components]
        
        # Use numpy arrays for better performance with vectorized operations
        years = np.array(range(scenario.analysis_years))
        calendar_years = np.array([datetime.now().year + year_index for year_index in years])
        
        # Pre-calculate cumulative mileage for all years
        mileage_array = np.cumsum(np.full(len(years), scenario.annual_mileage))
        
        # Initialize the data structure for annual costs using numpy arrays for better performance
        annual_costs_data = {name: np.zeros(scenario.analysis_years) for name in component_names}
        annual_costs_data['Year'] = calendar_years
        
        # Process components in batches for better performance
        BATCH_SIZE = 5  # Process years in batches of 5 for better performance
        
        for comp_instance in applicable_components:
            comp_name = comp_instance.__class__.__name__
            costs = np.zeros(len(years))
            
            # Check if component supports vectorized calculation
            if hasattr(comp_instance, 'calculate_vectorized') and callable(getattr(comp_instance, 'calculate_vectorized')):
                try:
                    # Use vectorized calculation if available
                    vectorized_costs = comp_instance.calculate_vectorized(
                        years=calendar_years,
                        vehicle=vehicle,
                        scenario=scenario,
                        year_indices=years,
                        total_mileage_km=mileage_array
                    )
                    costs = np.array(vectorized_costs)
                except Exception as e:
                    logger.error(f"Error in vectorized calculation for {comp_name}: {e}", exc_info=True)
                    # Fall back to non-vectorized calculation if vectorized fails
            
            # Process in batches if not using vectorized calculation or if vectorized failed
            if not hasattr(comp_instance, 'calculate_vectorized') or np.all(costs == 0):
                # Process in batches for better performance
                for batch_start in range(0, len(years), BATCH_SIZE):
                    batch_end = min(batch_start + BATCH_SIZE, len(years))
                    batch_years = years[batch_start:batch_end]
                    
                    # Calculate costs for this batch
                    for i, year_index in enumerate(batch_years):
                        current_calendar_year = calendar_years[batch_start + i]
                        try:
                            cost = comp_instance.calculate_annual_cost(
                                year=current_calendar_year,
                                vehicle=vehicle,
                                scenario=scenario,
                                calculation_year_index=year_index,
                                total_mileage_km=mileage_array[batch_start + i]
                            )
                            costs[batch_start + i] = cost if pd.notna(cost) else 0.0
                        except Exception as e:
                            logger.error(f"Error calculating {comp_name} for {vehicle.name} "
                                        f"in year index {year_index}: {e}", exc_info=True)
                            costs[batch_start + i] = np.nan
            
            annual_costs_data[comp_name] = costs
        
        # Convert to DataFrame and add a Total column
        df = pd.DataFrame(annual_costs_data)
        component_cost_columns = [col for col in df.columns if col != 'Year']
        df['Total'] = df[component_cost_columns].sum(axis=1, skipna=True)
        
        # Fill any NaN values with 0 for consistency
        df = df.fillna(0.0)
        
        # Optimize the dataframe for memory usage
        return optimize_dataframe(df)

    @timed("discounting")
    def _apply_discounting(self, undiscounted_df: pd.DataFrame, discount_rate: float) -> pd.DataFrame:
        """
        Apply discounting to annual costs to get present values.
        
        Args:
            undiscounted_df: DataFrame with undiscounted annual costs
            discount_rate: Real discount rate to apply
            
        Returns:
            DataFrame with discounted annual costs
        """
        if undiscounted_df.empty:
            logger.warning("Empty DataFrame provided for discounting, returning empty DataFrame.")
            return pd.DataFrame()
        
        # Make a copy to avoid modifying the original
        discounted_df = undiscounted_df.copy()
        
        # Use vectorized numpy operations for better performance
        years = np.arange(len(discounted_df))
        # Calculate discount factors as a numpy array for vectorized multiplication
        discount_factors = 1 / np.power(1 + discount_rate, years)
        
        # Apply discount factors to all cost columns (exclude 'Year' column) at once
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
            results = self._calculate_comparison_metrics(results)
            
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
            'analysis_years': scenario.analysis_years,
            'annual_mileage': scenario.annual_mileage,
            'discount_rate': scenario.discount_rate_real,
            'error': None
        }
    
    def _validate_vehicles(self, scenario: Scenario, results: Dict[str, Any]) -> bool:
        """Validate that both vehicle types are present in the scenario."""
        electric_vehicle = scenario.electric_vehicle
        diesel_vehicle = scenario.diesel_vehicle
        
        if not electric_vehicle or not diesel_vehicle:
            error_msg = "Scenario missing electric or diesel vehicle"
            logger.error(error_msg)
            results['error'] = error_msg
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
        
        results['electric_annual_costs_undiscounted'] = electric_undisc
        results['diesel_annual_costs_undiscounted'] = diesel_undisc
        
        # 2. Apply discounting
        logger.info("Applying discounting...")
        electric_disc = self._apply_discounting(electric_undisc, scenario.discount_rate_real)
        diesel_disc = self._apply_discounting(diesel_undisc, scenario.discount_rate_real)
        
        results['electric_annual_costs_discounted'] = electric_disc
        results['diesel_annual_costs_discounted'] = diesel_disc
        
        # 3. Calculate total TCO (sum of *discounted* total costs)
        total_tco_ev = electric_disc['Total'].sum() if not electric_disc.empty else 0
        total_tco_diesel = diesel_disc['Total'].sum() if not diesel_disc.empty else 0
        
        results['electric_total_tco'] = total_tco_ev
        results['diesel_total_tco'] = total_tco_diesel
        logger.info(f"Total Discounted TCO - EV: {total_tco_ev:,.2f}, Diesel: {total_tco_diesel:,.2f}")
        
        # 4. Calculate Levelized Cost of Driving (LCOD) using discounted TCO
        results['electric_lcod'] = self._calculate_lcod(total_tco_ev, scenario)
        results['diesel_lcod'] = self._calculate_lcod(total_tco_diesel, scenario)
        
        # 5. Find parity year using *undiscounted* cumulative costs
        results['parity_year'] = self._find_parity_year_undiscounted(
            electric_undisc['Total'].cumsum(),
            diesel_undisc['Total'].cumsum(),
            electric_undisc['Year']  # Pass Year series for mapping index to year
        )
        
        return results
    
    def _calculate_comparison_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate and add comparison metrics to results."""
        # Add LCOD comparison metrics
        ev_lcod = results.get('electric_lcod')
        diesel_lcod = results.get('diesel_lcod')
        
        if ev_lcod is not None and diesel_lcod is not None:
            results['lcod_difference'] = diesel_lcod - ev_lcod
            results['lcod_percentage_savings'] = ((diesel_lcod - ev_lcod) / diesel_lcod * 100) if diesel_lcod > 0 else 0
        
        # Add TCO comparison metrics
        ev_tco = results.get('electric_total_tco', 0)
        diesel_tco = results.get('diesel_total_tco', 0)
        
        results['tco_difference'] = diesel_tco - ev_tco
        results['tco_ev_to_diesel_ratio'] = ev_tco / diesel_tco if diesel_tco != 0 else float('inf')
        
        # Add parity information
        parity_year = results.get('parity_year')
        if parity_year:
            results['years_to_parity'] = parity_year - 1  # First year is year 1, so adjust for years count
            logger.info(f"Undiscounted TCO Parity Year: {parity_year}")
        else:
            results['years_to_parity'] = None
            logger.info("Undiscounted TCO Parity not reached in analysis period")
            
        return results
    
    def _record_calculation_time(self, start_time: float, results: Dict[str, Any]) -> None:
        """Record the calculation time and add to results."""
        elapsed = time.time() - start_time
        self._performance_stats.record("total_calculation", elapsed)
        results['calculation_time_seconds'] = round(elapsed, 4)
    
    def invalidate_calculation_cache(self) -> None:
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
        return performance_monitor.get_report()
    
    def reset_performance_stats(self) -> None:
        """Reset all performance tracking metrics."""
        performance_monitor.reset()

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
        total_undiscounted_km = scenario.annual_mileage * scenario.analysis_years
        
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
