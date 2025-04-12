from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
import numpy as np # Needed for financial calculations like PMT
import numpy_financial as npf # Import the financial functions
import logging
from pydantic import PrivateAttr
import math

# Import utility for data loading
from utils.data_handlers import load_battery_costs

# Import necessary classes from other modules
from .vehicles import Vehicle, ElectricVehicle, DieselVehicle
from .scenarios import Scenario

logger = logging.getLogger(__name__)

# Global variable to cache battery costs (simple cache)
_cached_battery_costs: Optional[Dict[int, float]] = None

def get_battery_cost_per_kwh(year: int, scenario: Scenario, vehicle: Optional[Vehicle] = None) -> float:
    """Gets the battery cost per kWh for a given year.
    Prioritizes vehicle projections, then scenario projections, then default cache/load.
    Uses simple interpolation/extrapolation if the exact year is not found.
    """
    global _cached_battery_costs

    costs = None

    # 1. Check Vehicle object if it's an EV
    if isinstance(vehicle, ElectricVehicle) and hasattr(vehicle, 'battery_pack_cost_projections_aud_per_kwh') and vehicle.battery_pack_cost_projections_aud_per_kwh:
        costs = vehicle.battery_pack_cost_projections_aud_per_kwh
        logger.debug(f"Using battery cost projections from vehicle '{vehicle.name}'.")

    # 2. Check if scenario provides specific projections (less likely intended path)
    if costs is None and hasattr(scenario, 'battery_cost_projections') and scenario.battery_cost_projections:
        costs = scenario.battery_cost_projections
        logger.debug(f"Using battery cost projections provided directly in scenario '{scenario.name}'.")

    # 3. If not found on vehicle or scenario, try loading from default and using cache
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
        """Return the vehicle acquisition cost based on financing method."""
        
        financing_method = scenario.financing_method.lower()
        purchase_price = vehicle.purchase_price
        
        if financing_method == 'cash':
            # Full purchase price in year 0 (index 0), 0 otherwise
            return purchase_price if calculation_year_index == 0 else 0.0
        
        elif financing_method == 'loan':
            if calculation_year_index == 0:
                # Year 0: Down payment
                down_payment = purchase_price * scenario.down_payment_pct
                return down_payment
            elif 1 <= calculation_year_index <= scenario.loan_term:
                # Years 1 to loan_term: Calculate annual loan payment
                loan_amount = purchase_price * (1.0 - scenario.down_payment_pct)
                interest_rate = scenario.interest_rate
                loan_term = scenario.loan_term
                
                # Handle zero interest rate separately to avoid numpy errors
                if interest_rate == 0:
                    annual_payment = loan_amount / loan_term if loan_term > 0 else 0.0
                elif loan_term > 0:
                    # Use npf.pmt now
                    annual_payment = -npf.pmt(interest_rate, loan_term, loan_amount)
                else: 
                    annual_payment = 0.0 # No payment if term is 0
                    
                return annual_payment
            else:
                # After loan term, cost is 0
                return 0.0
        else:
            raise ValueError(f"Unsupported financing method: {scenario.financing_method}")


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
                 # Match test expectation exactly
                 raise ValueError(f"Electricity price for year {year} not found")
            return vehicle.calculate_annual_energy_cost(annual_mileage, energy_price)
            
        elif isinstance(vehicle, DieselVehicle):
            energy_price = scenario.get_annual_price('diesel', calculation_year_index)
            if energy_price is None:
                 # Match test expectation exactly
                 raise ValueError(f"Diesel price for year {year} not found")
            return vehicle.calculate_annual_energy_cost(annual_mileage, energy_price)
            
        else:
            raise TypeError("Vehicle type not supported for EnergyCost calculation.")


class MaintenanceCost(CostComponent):
    """Calculates annual maintenance costs."""
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        """
        Calculates the maintenance cost for a given year.
        Uses the detailed annual min/max from the scenario based on vehicle type.
        Applies the annual maintenance increase rate.
        """
        # Determine vehicle type key suffix
        type_suffix = "bet" if isinstance(vehicle, ElectricVehicle) else "diesel"
        # Determine vehicle class key prefix (assuming 'rigid' or 'articulated')
        class_prefix = getattr(vehicle, 'vehicle_type', 'rigid') # Default to rigid if type is missing
        detail_key = f"{class_prefix}_{type_suffix}"

        if detail_key not in scenario.maintenance_costs_detailed:
            # logger.warning(f"MaintenanceCost: Detailed costs for '{detail_key}' not found in scenario. Returning 0.")
            # return 0.0
            # Raise KeyError if the specific key is missing
            raise KeyError(f"MaintenanceCost: Detailed costs for key '{detail_key}' not found in scenario.maintenance_costs_detailed.")

        maint_details = scenario.maintenance_costs_detailed[detail_key]
        try:
            # Use average of min/max for calculation
            min_cost = float(maint_details.get('annual_min', 0))
            max_cost = float(maint_details.get('annual_max', 0))
            base_annual_cost = (min_cost + max_cost) / 2.0
        except (TypeError, ValueError):
             logger.error(f"MaintenanceCost: Invalid min/max values for '{detail_key}'. {maint_details}")
             return 0.0 # Or raise error

        # Apply annual increase rate
        increase_factor = (1 + scenario.maintenance_increase_rate) ** calculation_year_index
        adjusted_annual_cost = base_annual_cost * increase_factor
        return adjusted_annual_cost


class InfrastructureCost(CostComponent):
    """Calculates annual infrastructure costs (charger maintenance)."""

    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        """Calculates the annual charger maintenance cost, applying only to EVs."""
        if not isinstance(vehicle, ElectricVehicle):
            return 0.0 # No infrastructure cost for non-EVs

        # Use simplified structure from scenario.infrastructure_costs
        charger_lifespan = scenario.infrastructure_costs.get('charger_lifespan', 10) # Default 10
        if calculation_year_index >= charger_lifespan:
            return 0.0 # No maintenance after charger lifespan

        capital_cost = scenario.infrastructure_costs.get('selected_charger_cost', 0) + \
                       scenario.infrastructure_costs.get('selected_installation_cost', 0)
        maintenance_rate = scenario.infrastructure_costs.get('charger_maintenance_percent', 0)
        
        # Maintenance cost doesn't typically escalate with a general rate in this model
        # It's a fixed percentage of the initial capital cost.
        # Calculate amortized upfront cost for the current year
        amortized_upfront_cost = 0.0
        if charger_lifespan > 0:
            # Cost applies during the charger's lifespan (years 0 to lifespan-1)
            if 0 <= calculation_year_index < charger_lifespan:
                amortized_upfront_cost = capital_cost / charger_lifespan
        elif charger_lifespan == 0:
             # If lifespan is 0, full cost is in year 0
             amortized_upfront_cost = capital_cost if calculation_year_index == 0 else 0.0
        # If lifespan < 0, treat as 0 cost (or raise error, but 0 is safer)
        
        # Calculate Annual Maintenance Cost
        # Based on initial charger_cost, increased annually
        base_annual_maintenance = capital_cost * maintenance_rate
        current_annual_maintenance = base_annual_maintenance * ((1 + scenario.maintenance_increase_rate) ** calculation_year_index)
        
        # Total cost is amortized capital plus current year's maintenance
        total_annual_cost = amortized_upfront_cost + current_annual_maintenance
        return total_annual_cost


class BatteryReplacementCost(CostComponent):
    """Handles battery replacement costs for electric vehicles."""

    # _replacement_occurred: bool = PrivateAttr(default=False) # Track if replacement happened
    def __init__(self):
        """Initialize component state."""
        self._replacement_occurred = False

    def reset(self):
        """Reset state for a new calculation run."""
        self._replacement_occurred = False

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

        # --- Check for replacement trigger ---
        trigger_replacement = False
        reason = ""

        # 1. Check forced replacement year
        if scenario.force_battery_replacement_year is not None and \
           scenario.force_battery_replacement_year == (calculation_year_index + 1):
            trigger_replacement = True
            reason = f"forced in year {calculation_year_index + 1}"

        # 2. Check degradation threshold (only if not forced)
        elif scenario.battery_replacement_threshold is not None:
            # Calculate age and mileage at the END of the current year
            age_at_year_end = calculation_year_index + 1
            mileage_at_year_end = total_mileage_km + scenario.annual_mileage

            try:
                capacity_factor = vehicle.calculate_battery_degradation_factor(age_at_year_end, mileage_at_year_end)
                logger.debug(f"Year index {calculation_year_index}: Age={age_at_year_end}, Mileage={mileage_at_year_end:.0f}, Capacity Factor={capacity_factor:.3f}")
            except AttributeError:
                logger.error("Failed to calculate battery degradation. Vehicle object might be missing required methods or attributes.", exc_info=True)
                return 0.0 # Avoid error propagation
            except Exception as e:
                logger.error(f"Error calculating battery degradation factor: {e}", exc_info=True)
                return 0.0

            # Trigger replacement if capacity factor drops below threshold
            if capacity_factor <= scenario.battery_replacement_threshold:
                trigger_replacement = True
                reason = f"threshold ({capacity_factor:.3f} <= {scenario.battery_replacement_threshold})"

        # --- Calculate cost if replacement is triggered ---
        if trigger_replacement:
            age_at_replacement = calculation_year_index + 1 # Age at end of year when trigger happens

            # Check if cost is covered by warranty
            cost_covered_by_warranty = False
            if hasattr(vehicle, 'battery_warranty_years') and vehicle.battery_warranty_years is not None:
                # Warranty covers if failure occurs AT or BEFORE warranty expiration age
                if age_at_replacement <= vehicle.battery_warranty_years:
                    cost_covered_by_warranty = True
                    logger.info(f"Battery replacement triggered ({reason}) in year index {calculation_year_index} (age {age_at_replacement}), but covered by warranty ({vehicle.battery_warranty_years} years).")

            # Mark replacement as occurred regardless of warranty coverage
            self._replacement_occurred = True

            if not cost_covered_by_warranty:
                replacement_cost = self._calculate_replacement_cost(year, vehicle, scenario)
                logger.info(f"Battery replacement triggered ({reason}) in year index {calculation_year_index} (age {age_at_replacement}). Cost: {replacement_cost:.2f}")
                return replacement_cost
            else:
                # Replacement needed but covered by warranty, cost is 0 for TCO
                return 0.0

        # No replacement in this year
        return 0.0

    def _calculate_replacement_cost(self, year: int, vehicle: ElectricVehicle, scenario: Scenario) -> float:
        """Helper to calculate the battery replacement cost for a given year."""
        # Get cost per kWh for the replacement year, passing the vehicle
        cost_per_kwh = get_battery_cost_per_kwh(year, scenario, vehicle)
        replacement_cost = vehicle.battery_capacity_kwh * cost_per_kwh
        return replacement_cost


class InsuranceCost(CostComponent):
    """Calculates annual insurance costs."""

    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        """
        Calculates annual insurance cost based on vehicle purchase price, 
        scenario base rate, vehicle-specific factor, and annual increase rate.
        """
        # Determine vehicle type key (use prime mover proxy for now)
        # TODO: Refine key based on actual vehicle type (rigid/articulated) if data becomes available
        ins_key = "electric_prime_mover" if isinstance(vehicle, ElectricVehicle) else "diesel_prime_mover"

        try:
            # Access nested insurance dictionary
            base_annual_cost = float(scenario.insurance_and_registration['insurance'][ins_key])
        except (KeyError, TypeError, ValueError):
             logger.warning(f"InsuranceCost: Could not find or parse base insurance cost for key '{ins_key}' in scenario.insurance_and_registration. Returning 0.")
             return 0.0

        # Apply annual increase rate
        increase_factor = (1 + scenario.insurance_increase_rate) ** calculation_year_index
        adjusted_annual_cost = base_annual_cost * increase_factor
        return adjusted_annual_cost


class RegistrationCost(CostComponent):
    """Calculates annual registration costs."""
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        """
        Calculates annual registration cost based on scenario base rate and annual increase rate.
        Assumes registration cost is the same for both vehicle types unless specified otherwise.
        """
        # Base cost now comes from the vehicle object itself
        base_registration_cost = getattr(vehicle, 'registration_cost', 0)

        # Apply annual increase rate
        increase_factor = (1 + scenario.registration_increase_rate) ** calculation_year_index
        current_year_cost = base_registration_cost * increase_factor
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
