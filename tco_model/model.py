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

# Configure module logger
logger = logging.getLogger(__name__)

# Performance monitoring utilities
class PerformanceStats:
    """Simple class to track performance metrics for TCO calculations."""
    
    def __init__(self):
        self.timings = {}
        self.call_counts = {}
        
    def record(self, operation: str, elapsed: float) -> None:
        """Record the time taken for an operation."""
        if operation not in self.timings:
            self.timings[operation] = 0.0
            self.call_counts[operation] = 0
        
        self.timings[operation] += elapsed
        self.call_counts[operation] += 1
        
    def get_report(self) -> Dict[str, Any]:
        """Generate a performance report."""
        report = {
            'timings': {k: round(v, 4) for k, v in self.timings.items()},
            'call_counts': self.call_counts.copy(),
            'avg_times': {
                k: round(v / self.call_counts.get(k, 1), 4) 
                for k, v in self.timings.items()
            }
        }
        
        # Calculate total time and percentage breakdown
        total_time = sum(self.timings.values())
        if total_time > 0:
            report['total_time'] = round(total_time, 4)
            report['percentages'] = {
                k: round((v / total_time) * 100, 2) 
                for k, v in self.timings.items()
            }
        
        return report
    
    def reset(self) -> None:
        """Reset all performance metrics."""
        self.timings = {}
        self.call_counts = {}


# Function decorator for timing operations
def timed(operation_name: str = None):
    """Decorator to time function execution and record metrics."""
    def decorator(func):
        nonlocal operation_name
        if operation_name is None:
            operation_name = func.__qualname__
            
        def wrapper(*args, **kwargs):
            instance = args[0] if args else None
            
            # Only time if the instance has performance stats
            if instance and hasattr(instance, '_performance_stats'):
                start_time = time.time()
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                
                instance._performance_stats.record(operation_name, elapsed)
                return result
            else:
                # Just call the function if no stats tracking
                return func(*args, **kwargs)
                
        return wrapper
    return decorator


def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize a DataFrame for memory usage and performance.
    
    Applies memory-saving techniques like downcast and category conversion.
    """
    result = df.copy()
    
    # Optimize numeric columns
    for col in result.select_dtypes(include=['int']).columns:
        result[col] = pd.to_numeric(result[col], downcast='integer')
        
    for col in result.select_dtypes(include=['float']).columns:
        result[col] = pd.to_numeric(result[col], downcast='float')
    
    # Convert object columns with few unique values to category
    for col in result.select_dtypes(include=['object']).columns:
        if result[col].nunique() / len(result) < 0.5:  # If less than 50% unique values
            result[col] = result[col].astype('category')
    
    return result


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
        
        # Performance tracking
        self._performance_stats = PerformanceStats()

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
        years = list(range(scenario.analysis_years))
        
        # Initialize the data structure for annual costs
        annual_costs_data = {name: [0.0] * scenario.analysis_years for name in component_names}
        annual_costs_data['Year'] = [datetime.now().year + year_index for year_index in years]
        
        total_mileage_km = 0.0

        # Calculate costs for each year and component
        for year_index in years:
            current_calendar_year = datetime.now().year + year_index
            
            # Calculate costs for each applicable component
            for comp_instance in applicable_components:
                comp_name = comp_instance.__class__.__name__
                try:
                    cost = comp_instance.calculate_annual_cost(
                        year=current_calendar_year,
                        vehicle=vehicle,
                        scenario=scenario,
                        calculation_year_index=year_index,
                        total_mileage_km=total_mileage_km
                    )
                    # Ensure cost is numeric, default to 0 if calculation returns None or NaN
                    annual_costs_data[comp_name][year_index] = cost if pd.notna(cost) else 0.0
                except Exception as e:
                    logger.error(f"Error calculating {comp_name} for {vehicle.name} in year index {year_index}: {e}", exc_info=True)
                    annual_costs_data[comp_name][year_index] = np.nan  # Mark as NaN on error
            
            # Update total mileage for next year's calculations
            total_mileage_km += scenario.annual_mileage
        
        # Convert to DataFrame and add a Total column
        df = pd.DataFrame(annual_costs_data)
        component_cost_columns = [col for col in df.columns if col != 'Year']
        df['Total'] = df[component_cost_columns].sum(axis=1)
        
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
        
        # Calculate discount factors for each year
        years = list(range(len(discounted_df)))
        discount_factors = [(1 / ((1 + discount_rate) ** year)) for year in years]
        
        # Apply discount factors to all cost columns (exclude 'Year' column)
        for col in discounted_df.columns:
            if col != 'Year':
                discounted_df[col] = discounted_df[col] * discount_factors
        
        return optimize_dataframe(discounted_df)

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
        # Check if we have a cached result for this scenario
        cache_key = f"{scenario.name}_{id(scenario)}"
        if cache_key in self._calculation_cache:
            logger.info(f"Using cached results for scenario: {scenario.name}")
            return self._calculation_cache[cache_key]
            
        # Start timing the calculation
        start_time = time.time()
        logger.info(f"Starting TCO calculation for scenario: {scenario.name}")
        
        results = {
            'scenario_name': scenario.name,
            'analysis_years': scenario.analysis_years,
            'annual_mileage': scenario.annual_mileage,
            'discount_rate': scenario.discount_rate_real,
            'error': None
        }
        
        try:
            # Get vehicle instances from the scenario
            electric_vehicle = scenario.electric_vehicle
            diesel_vehicle = scenario.diesel_vehicle
            
            if not electric_vehicle or not diesel_vehicle:
                error_msg = "Scenario missing electric or diesel vehicle"
                logger.error(error_msg)
                results['error'] = error_msg
                return results
            
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
            lcod_ev = self._calculate_lcod(total_tco_ev, scenario)
            lcod_diesel = self._calculate_lcod(total_tco_diesel, scenario)
            
            results['electric_lcod'] = lcod_ev
            results['diesel_lcod'] = lcod_diesel
            logger.info(f"LCOD - EV: {lcod_ev:.3f} AUD/km, Diesel: {lcod_diesel:.3f} AUD/km")
            
            # 5. Find parity year using *undiscounted* cumulative costs
            parity_year = self._find_parity_year_undiscounted(
                electric_undisc['Total'].cumsum(),
                diesel_undisc['Total'].cumsum(),
                electric_undisc['Year']  # Pass Year series for mapping index to year
            )
            
            results['parity_year'] = parity_year
            logger.info(f"Undiscounted TCO Parity Year: {parity_year if parity_year else 'None'}")
            
            # 6. Add summary metrics
            results['tco_difference'] = total_tco_diesel - total_tco_ev
            results['tco_ev_to_diesel_ratio'] = total_tco_ev / total_tco_diesel if total_tco_diesel != 0 else float('inf')
            
            # Record total calculation time
            elapsed = time.time() - start_time
            self._performance_stats.record("total_calculation", elapsed)
            results['calculation_time_seconds'] = round(elapsed, 4)
            
            # Cache the results
            self._calculation_cache[cache_key] = results
            
            return results
            
        except Exception as e:
            logger.error(f"Error during TCO calculation: {e}", exc_info=True)
            results['error'] = f"Calculation failed: {e}"
            return results  # Return partial results with error message
    
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
        return self._performance_stats.get_report()
    
    def reset_performance_stats(self) -> None:
        """Reset all performance tracking metrics."""
        self._performance_stats.reset()

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
