from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import numpy as np # Needed for financial calculations like PMT
import logging
from pydantic import PrivateAttr

# Import utility for data loading
from utils.data_handlers import load_battery_costs

# Import necessary classes from other modules
from .vehicles import Vehicle, ElectricVehicle, DieselVehicle
from .scenarios import Scenario

logger = logging.getLogger(__name__)

# Global variable to cache battery costs (simple cache)
_cached_battery_costs: Optional[Dict[int, float]] = None

def get_battery_cost_per_kwh(year: int, scenario: Scenario) -> float:
    """Gets the battery cost per kWh for a given year from scenario or cached data.
    Uses simple interpolation/extrapolation if the exact year is not found.
    Checks scenario.battery_cost_projections first.
    """
    global _cached_battery_costs

    costs = None
    # Check if scenario provides specific projections
    if hasattr(scenario, 'battery_cost_projections') and scenario.battery_cost_projections:
        costs = scenario.battery_cost_projections
        logger.debug(f"Using battery cost projections provided in scenario '{scenario.name}'.")
    
    # If not in scenario, try loading from default and using cache
    if costs is None:
        if _cached_battery_costs is None:
            logger.info("Attempting to load default battery costs (not provided in scenario). Cache empty.")
            loaded_data = load_battery_costs() # Assumes load_battery_costs exists and works
            if loaded_data and 'battery_pack_cost_aud_per_kwh' in loaded_data:
                try:
                    # Convert keys to integers
                    _cached_battery_costs = {int(k): float(v) for k, v in loaded_data['battery_pack_cost_aud_per_kwh'].items()}
                    logger.info(f"Loaded and cached default battery costs: {len(_cached_battery_costs)} entries.")
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting loaded battery cost data to dict[int, float]: {e}")
                    _cached_battery_costs = {}
            else:
                _cached_battery_costs = {}
                logger.warning("Could not load default battery costs or key 'battery_pack_cost_aud_per_kwh' not found.")
        costs = _cached_battery_costs
        if costs:
             logger.debug("Using cached default battery costs.")

    # Handle case where no cost data is available at all
    if not costs:
        fallback_cost = 100.0 # Fallback cost if no data is available
        logger.warning(f"No battery cost data found for year {year}. Using fallback cost: {fallback_cost:.2f} AUD/kWh")
        return fallback_cost

    # Sort years for interpolation/extrapolation
    sorted_years = sorted(costs.keys())

    if year in costs:
        return costs[year]
    elif year < sorted_years[0]:
        # Extrapolate backwards (use first available year's cost)
        cost = costs[sorted_years[0]]
        logger.debug(f"Year {year} before projection range. Using cost from {sorted_years[0]}: {cost:.2f}")
        return cost
    elif year > sorted_years[-1]:
        # Extrapolate forwards (use last available year's cost)
        cost = costs[sorted_years[-1]]
        logger.debug(f"Year {year} after projection range. Using cost from {sorted_years[-1]}: {cost:.2f}")
        return cost
    else:
        # Interpolate linearly between the two closest years
        prev_year = max(y for y in sorted_years if y < year)
        next_year = min(y for y in sorted_years if y > year)
        prev_cost = costs[prev_year]
        next_cost = costs[next_year]

        if next_year == prev_year: # Should not happen with sorted list check
             return prev_cost

        # Linear interpolation
        interpolation_factor = (year - prev_year) / (next_year - prev_year)
        interpolated_cost = prev_cost + interpolation_factor * (next_cost - prev_cost)
        logger.debug(f"Interpolating battery cost for year {year} between {prev_year} and {next_year}. Result: {interpolated_cost:.2f}")
        return interpolated_cost


class CostComponent(ABC):
    """Abstract base class for all cost components."""
    
    @abstractmethod
    def calculate_annual_cost(
        self, 
        year: int, 
        vehicle: Vehicle, 
        scenario: Scenario,
        calculation_year_index: int, # 0 for start_year, 1 for start_year+1, etc.
        total_mileage_km: float # Accumulated mileage up to the start of the current year
    ) -> float:
        """
        Calculate the cost for this component for a specific year.
        
        Args:
            year: The calendar year of analysis (e.g., 2025, 2026).
            vehicle: The specific Vehicle instance (Electric or Diesel).
            scenario: The Scenario object containing all parameters.
            calculation_year_index: The zero-based index of the calculation year within the analysis period.
            total_mileage_km: The total mileage accumulated by the vehicle before the start of this year.
            
        Returns:
            The calculated cost for this component in the given year (in AUD).
        """
        pass


class AcquisitionCost(CostComponent):
    """Handles vehicle acquisition costs (purchase price in year 0)."""
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario, 
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        """Return the vehicle purchase price only in the first year (index 0)."""
        
        # Simple model: full cost is incurred only in the first year (index 0)
        return vehicle.purchase_price if calculation_year_index == 0 else 0.0
        
        # Removed previous logic based on scenario.financing_method, loan_term etc.
        # If financing needs to be modelled, it should be added back with parameters
        # either on the Scenario or potentially as a separate Financing component.


class EnergyCost(CostComponent):
    """Handles energy costs (fuel/electricity)."""
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario, 
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        """Calculate energy cost for the specified year using scenario prices."""
        annual_mileage = scenario.annual_mileage
        
        if isinstance(vehicle, ElectricVehicle):
            energy_price = scenario.get_annual_price('electricity', calculation_year_index)
            if energy_price is None:
                 raise ValueError(f"Electricity price for year index {calculation_year_index} (Year {year}) not found.")
            return vehicle.calculate_annual_energy_cost(annual_mileage, energy_price)
            
        elif isinstance(vehicle, DieselVehicle):
            energy_price = scenario.get_annual_price('diesel', calculation_year_index)
            if energy_price is None:
                 raise ValueError(f"Diesel price for year index {calculation_year_index} (Year {year}) not found.")
            return vehicle.calculate_annual_energy_cost(annual_mileage, energy_price)
            
        else:
            raise TypeError("Vehicle type not supported for EnergyCost calculation.")


class MaintenanceCost(CostComponent):
    """Handles maintenance and repair costs, applying annual increase."""
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        """Calculate maintenance cost based on annual mileage, vehicle base cost/km, and scenario increase rate."""
        annual_mileage = scenario.annual_mileage
        increase_rate = scenario.maintenance_increase_rate
        
        # Access base cost directly from vehicle object (now a required field)
        base_cost_per_km = vehicle.maintenance_cost_per_km 
        
        # Calculate the cost for the current year, adjusting for the increase rate
        # Cost for year = Annual Mileage * Base Cost/km * (1 + Increase Rate) ^ Year Index
        current_year_cost_per_km = base_cost_per_km * ((1 + increase_rate) ** calculation_year_index)
        return annual_mileage * current_year_cost_per_km


class InfrastructureCost(CostComponent):
    """Handles upfront and ongoing infrastructure costs (e.g., chargers)."""

    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        """Calculate infrastructure costs (upfront cost in year 0 + annual maintenance)."""
        # This component should only apply to Electric Vehicles
        if not isinstance(vehicle, ElectricVehicle):
            return 0.0

        upfront_cost = scenario.infrastructure_cost if calculation_year_index == 0 else 0.0
        
        # Annual maintenance cost (applied every year including year 0)
        maintenance_cost = scenario.infrastructure_cost * scenario.infrastructure_maintenance_percent
        
        return upfront_cost + maintenance_cost
        
        # Removed previous logic based on infrastructure_lifespan
        # Assumes maintenance is paid annually from year 0 onwards on the initial investment.


class BatteryReplacementCost(CostComponent):
    """Handles battery replacement costs for electric vehicles."""
    
    _replacement_occurred: bool = PrivateAttr(default=False) # Track if replacement happened to avoid multiple triggers

    # Reset state if needed (e.g., if used across multiple scenarios/vehicles without re-instantiation)
    # def reset(self): self._replacement_occurred = False 
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        """Calculate battery replacement cost if triggered by forced year or degradation threshold."""
        
        # Only applies to ElectricVehicles
        if not isinstance(vehicle, ElectricVehicle):
            return 0.0
            
        # Prevent multiple replacements
        if self._replacement_occurred:
             return 0.0

        # Ensure calculation year index is valid
        if not 0 <= calculation_year_index < scenario.analysis_years:
            logger.warning(f"BatteryReplacementCost: calculation_year_index {calculation_year_index} out of bounds for analysis_years {scenario.analysis_years}.")
            return 0.0

        # 1. Check if forced replacement year matches current year (1-based index)
        if scenario.force_battery_replacement_year is not None and \
           scenario.force_battery_replacement_year == (calculation_year_index + 1):
            replacement_cost = self._calculate_replacement_cost(year, vehicle, scenario)
            logger.info(f"Battery replacement forced in year {year} (index {calculation_year_index}). Cost: {replacement_cost:.2f}")
            self._replacement_occurred = True
            return replacement_cost

        # 2. Check degradation threshold (only if force_replacement_year is not set or not met yet)
        if scenario.force_battery_replacement_year is None and scenario.battery_replacement_threshold is not None:
            # Calculate current battery capacity factor
            # total_mileage_km is mileage *before* the start of the current year
            current_mileage = total_mileage_km # Use mileage up to start of year
            current_age_years = calculation_year_index # Age at start of year
            
            try:
                capacity_factor = vehicle.calculate_battery_degradation_factor(current_age_years, current_mileage)
            except AttributeError:
                logger.error("Failed to calculate battery degradation. Vehicle object might be missing required methods or attributes.", exc_info=True)
                return 0.0 # Avoid error propagation
            except Exception as e:
                logger.error(f"Error calculating battery degradation factor: {e}", exc_info=True)
                return 0.0

            # Trigger replacement if capacity factor drops below threshold
            if capacity_factor <= scenario.battery_replacement_threshold:
                replacement_cost = self._calculate_replacement_cost(year, vehicle, scenario)
                logger.info(f"Battery replacement triggered by threshold ({scenario.battery_replacement_threshold:.1%}) in year {year} (index {calculation_year_index}). Capacity factor: {capacity_factor:.1%}. Cost: {replacement_cost:.2f}")
                self._replacement_occurred = True
                return replacement_cost

        # No replacement in this year
        return 0.0

    def _calculate_replacement_cost(self, year: int, vehicle: ElectricVehicle, scenario: Scenario) -> float:
        """Helper to calculate the actual cost of battery replacement."""
        # Get cost per kWh for the replacement year
        cost_per_kwh = get_battery_cost_per_kwh(year, scenario) 
        
        # Calculate total cost
        # Ensure vehicle has the battery_capacity_kwh attribute
        if hasattr(vehicle, 'battery_capacity_kwh'):
             replacement_cost = vehicle.battery_capacity_kwh * cost_per_kwh
             return replacement_cost
        else:
             logger.error(f"Cannot calculate battery replacement cost: Vehicle {vehicle.name} missing 'battery_capacity_kwh' attribute.")
             return 0.0 # Avoid errors if attribute is missing


class InsuranceCost(CostComponent):
    """Handles annual insurance costs, based on vehicle price and increase rate."""

    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        """Calculate insurance cost based on vehicle price, base rate (% from vehicle), and scenario increase rate."""
        increase_rate = scenario.insurance_increase_rate
        
        # Access base rate (as % of purchase price) from vehicle object
        try:
            base_insurance_percent = vehicle.insurance_cost_percent
        except AttributeError:
             logger.warning(f"Vehicle {vehicle.name} missing 'insurance_cost_percent' attribute. Using fallback 0.")
             base_insurance_percent = 0.0
        
        # Calculate base annual insurance cost
        base_annual_cost = vehicle.purchase_price * base_insurance_percent
        
        # Apply annual increase rate
        current_year_cost = base_annual_cost * ((1 + increase_rate) ** calculation_year_index)
        return current_year_cost


class RegistrationCost(CostComponent):
    """Handles annual vehicle registration costs, applying annual increase."""
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        """Calculate registration cost based on vehicle base cost and scenario increase rate."""
        increase_rate = scenario.registration_increase_rate
        
        # Access base cost directly from vehicle object
        try:
            base_registration_cost = vehicle.registration_cost
        except AttributeError:
            logger.warning(f"Vehicle {vehicle.name} missing 'registration_cost' attribute. Using fallback 0.")
            base_registration_cost = 0.0

        # Apply annual increase rate
        current_year_cost = base_registration_cost * ((1 + increase_rate) ** calculation_year_index)
        return current_year_cost


class ResidualValue(CostComponent):
    """Handles the residual value of the vehicle at the end of the analysis."""
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        """Calculate residual value as a negative cost only in the final analysis year."""
        
        # Residual value is realized only at the end of the analysis period
        if calculation_year_index == scenario.analysis_years - 1:
            # Calculate age at the end of the analysis
            vehicle_age_at_end = scenario.analysis_years
            
            residual_value = vehicle.calculate_residual_value(age_years=vehicle_age_at_end)
            # Return as a negative cost
            logger.debug(f"Calculated residual value for {vehicle.name} at end of {scenario.analysis_years} years: {-residual_value:.2f}")
            return -residual_value
        else:
            # No residual value cost in other years
            return 0.0

class CarbonTaxCost(CostComponent):
    """Handles carbon tax costs for diesel vehicles."""

    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        """Calculate carbon tax cost for the specified year based on fuel consumption and tax rate."""
        
        # Only applies to Diesel Vehicles and if the scenario includes the tax
        if not isinstance(vehicle, DieselVehicle) or not scenario.include_carbon_tax:
            return 0.0
        
        # Get the carbon tax rate for the current year from the scenario
        carbon_tax_rate = scenario.get_annual_price('carbon_tax', calculation_year_index)
        if carbon_tax_rate is None:
             logger.warning(f"Carbon tax rate for year index {calculation_year_index} (Year {year}) not found. Skipping tax.")
             return 0.0
        if carbon_tax_rate < 0: # Ensure rate is not negative
            logger.warning(f"Negative carbon tax rate ({carbon_tax_rate}) found for year {year}. Using 0.")
            carbon_tax_rate = 0.0

        # Calculate annual fuel consumption
        try:
            # Access fuel consumption per km from the vehicle object
            consumption_l_per_km = vehicle.fuel_consumption_l_per_km 
            annual_consumption_l = scenario.annual_mileage * consumption_l_per_km
        except AttributeError:
            logger.error(f"Diesel vehicle {vehicle.name} missing 'fuel_consumption_l_per_km' attribute. Cannot calculate carbon tax.")
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating fuel consumption for carbon tax: {e}")
            return 0.0

        # Get CO2 emission factor (kg CO2e per litre) from vehicle
        try:
            co2_factor_kg_per_l = vehicle.co2_emission_factor
        except AttributeError:
            logger.error(f"Diesel vehicle {vehicle.name} missing 'co2_emission_factor' attribute. Cannot calculate carbon tax.")
            return 0.0
            
        # Convert kg CO2e to tonnes CO2e (1 tonne = 1000 kg)
        co2_factor_tonnes_per_l = co2_factor_kg_per_l / 1000.0 
        
        # Calculate total annual CO2e tonnes
        total_tonnes_co2e = annual_consumption_l * co2_factor_tonnes_per_l
        
        # Calculate total annual carbon tax cost
        carbon_tax_cost = total_tonnes_co2e * carbon_tax_rate
        
        return carbon_tax_cost

class RoadUserChargeCost(CostComponent):
    """Handles road user charges based on mileage."""

    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        if not scenario.include_road_user_charge:
            return 0.0

        annual_mileage = scenario.annual_mileage
        # Get the road user charge rate ($/km) for the current year
        current_charge_rate = scenario.get_annual_price('road_user_charge', calculation_year_index)

        if current_charge_rate is None:
            logger.error(f"Road user charge rate for year index {calculation_year_index} (Year {year}) not found.")
            return 0.0

        # Calculate annual road user charge cost
        annual_charge = annual_mileage * current_charge_rate
        return annual_charge
