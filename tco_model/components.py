from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import numpy as np # Needed for financial calculations like PMT
import logging

# Import utility for data loading
from utils.data_handlers import load_battery_costs

# Import necessary classes from other modules
from .vehicles import Vehicle, ElectricVehicle, DieselVehicle
from .scenario import Scenario

logger = logging.getLogger(__name__)

# Global variable to cache battery costs (simple cache)
_cached_battery_costs: Optional[Dict[int, float]] = None

def get_battery_cost_per_kwh(year: int, scenario: Scenario) -> float:
    """Gets the battery cost per kWh for a given year from scenario or cached data.
    Uses simple interpolation/extrapolation if the exact year is not found.
    """
    global _cached_battery_costs

    # Load from scenario if available and not empty
    costs = scenario.battery_cost_projections
    if not costs:
        # Load from default file if not in scenario and not cached
        if _cached_battery_costs is None:
            loaded_data = load_battery_costs()
            if loaded_data and 'battery_pack_cost_aud_per_kwh' in loaded_data:
                # Convert keys to integers
                _cached_battery_costs = {int(k): v for k, v in loaded_data['battery_pack_cost_aud_per_kwh'].items()}
                logger.info("Loaded and cached default battery costs.")
            else:
                _cached_battery_costs = {}
                logger.warning("Could not load default battery costs. Using fallback.")
        costs = _cached_battery_costs

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
    """Handles vehicle acquisition costs, including purchase and financing."""
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario, 
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        """Calculate acquisition-related costs for the specified year."""
        
        purchase_price = vehicle.purchase_price
        # start_year = scenario.start_year # Not needed directly
        
        if scenario.financing_method == 'cash':
            # Full cost is incurred only in the first year (index 0)
            return purchase_price if calculation_year_index == 0 else 0.0
        
        elif scenario.financing_method == 'loan':
            loan_term = scenario.loan_term
            down_payment_pct = scenario.down_payment_pct
            interest_rate = scenario.interest_rate
            
            # Down payment in the first year (index 0)
            down_payment_cost = purchase_price * down_payment_pct if calculation_year_index == 0 else 0.0
            
            # Loan payments for the duration of the loan term (index 0 to loan_term - 1)
            # Note: numpy pmt calculates payment for periods 1 to n. The total payments
            # over the term should equal the principal + interest. We spread the cost
            # including the downpayment over the analysis.
            # Let's simplify: calculate total loan payment and spread annually.
            loan_payment_cost = 0.0
            if 0 <= calculation_year_index < loan_term: # Payments occur for 'loan_term' years
                loan_amount = purchase_price * (1 - down_payment_pct)
                
                # Handle zero interest rate case to avoid division by zero
                if interest_rate == 0:
                    if loan_term == 0: 
                         annual_payment = 0.0 # Avoid division by zero
                    else:
                         annual_payment = loan_amount / loan_term
                else:
                    # Calculate annual payment using numpy's pmt function
                    # np.pmt(rate, nper, pv)
                    try:
                        annual_payment = -np.pmt(interest_rate, loan_term, loan_amount)
                    except ZeroDivisionError:
                        annual_payment = 0.0 
                loan_payment_cost = annual_payment

            # Return the sum of down payment (only year 0) and loan payment (during term)
            return down_payment_cost + loan_payment_cost
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
        """Calculate maintenance cost based on annual mileage, base cost/km, and increase rate."""
        annual_mileage = scenario.annual_mileage
        increase_rate = scenario.maintenance_increase_rate
        
        if isinstance(vehicle, ElectricVehicle):
            base_cost_per_km = vehicle.maintenance_cost_per_km # Assumes vehicle has this attribute
        elif isinstance(vehicle, DieselVehicle):
            base_cost_per_km = vehicle.maintenance_cost_per_km # Assumes vehicle has this attribute
        else:
            raise TypeError("Vehicle type not supported for MaintenanceCost calculation.")
            
        # Calculate the cost per km for the current year
        current_cost_per_km = base_cost_per_km * ((1 + increase_rate) ** calculation_year_index)
        
        return annual_mileage * current_cost_per_km


class InfrastructureCost(CostComponent):
    """Handles charging infrastructure costs (upfront and maintenance)."""
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        """Calculate amortized infrastructure cost and annual maintenance for the specified year."""
        # Only applies to electric vehicles
        if not isinstance(vehicle, ElectricVehicle):
            return 0.0
        
        upfront_cost = scenario.infrastructure_cost # Combined charger + installation
        lifespan = scenario.infrastructure_lifespan
        maintenance_percent = scenario.infrastructure_maintenance_percent
        
        amortization_cost = 0.0
        if lifespan > 0:
            # Assume single purchase at start, amortized over lifespan
            if calculation_year_index == 0: # Cost occurs at beginning of year 0
                 amortization_cost = upfront_cost
                 # If using simple annual amortization:
                 # amortization_cost = upfront_cost / lifespan if 0 <= calculation_year_index < lifespan else 0.0
                 # Let's stick to upfront cost in year 0 as per common TCO convention
        elif upfront_cost > 0: # Lifespan 0 or less, full cost upfront
            amortization_cost = upfront_cost if calculation_year_index == 0 else 0.0

        # Calculate annual maintenance cost based on the upfront cost
        maintenance_cost = upfront_cost * maintenance_percent
        
        # Total cost for the year is upfront cost (year 0) + annual maintenance
        # Note: Amortization approach was changed to upfront cost in year 0.
        total_cost = (amortization_cost if calculation_year_index == 0 else 0.0) + maintenance_cost
        
        return total_cost


class BatteryReplacementCost(CostComponent):
    """Handles battery replacement costs for electric vehicles."""
    
    _replacement_occurred: bool = False

    def __init__(self):
        self._replacement_occurred = False # Reset for each instance

    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        """Calculate battery replacement cost if applicable for the specified year."""
        if not isinstance(vehicle, ElectricVehicle) or not scenario.enable_battery_replacement or self._replacement_occurred:
            return 0.0
            
        vehicle_age_at_year_end = calculation_year_index + 1
        # Calculate total mileage at the *end* of the current year for degradation check
        total_mileage_km_at_year_end = total_mileage_km + scenario.annual_mileage
        replacement_triggered = False

        # 1. Forced replacement year check
        if scenario.force_battery_replacement_year is not None:
            if calculation_year_index == scenario.force_battery_replacement_year - 1:
                replacement_triggered = True
                logger.info(f"Battery replacement forced in year {year} (Index {calculation_year_index}) by scenario.")

        # 2. Degradation threshold check (only if not forced and threshold is set)
        elif scenario.battery_replacement_threshold is not None:
            try:
                # Use the vehicle's degradation calculation method
                degradation_factor = vehicle.calculate_battery_degradation_factor(
                    age_years=vehicle_age_at_year_end, 
                    total_mileage_km=total_mileage_km_at_year_end
                )
                
                # Trigger if remaining capacity is at or below the threshold
                if degradation_factor <= scenario.battery_replacement_threshold:
                     replacement_triggered = True
                     logger.info(f"Battery replacement triggered by degradation factor ({degradation_factor:.2%}) reaching threshold ({scenario.battery_replacement_threshold:.2%}) in year {year} (Index {calculation_year_index}).")

            except AttributeError:
                 logger.error(f"Vehicle {vehicle.name} missing calculate_battery_degradation_factor method.")
            except Exception as e:
                logger.error(f"Error calculating battery degradation factor: {e}")

        # Calculate cost if triggered
        if replacement_triggered:
            try:
                battery_price_per_kwh = get_battery_cost_per_kwh(year, scenario)
                battery_capacity = vehicle.battery_capacity_kwh
                replacement_cost = battery_capacity * battery_price_per_kwh
                logger.info(f"Calculated battery replacement cost for year {year}: {replacement_cost:.2f} AUD ({battery_capacity} kWh * {battery_price_per_kwh:.2f} AUD/kWh)")
                self._replacement_occurred = True # Mark replacement as done
                return replacement_cost
            except AttributeError:
                logger.error("Vehicle missing 'battery_capacity_kwh' attribute.")
                return 0.0 # Avoid returning partial cost
            except Exception as e:
                logger.error(f"Error calculating battery replacement cost: {e}")
                return 0.0

        return 0.0


class InsuranceCost(CostComponent):
    """Handles insurance costs, assumed as a percentage of purchase price, increasing annually."""
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        """Calculate insurance cost for the specified year."""
        # Use the insurance cost percent defined directly on the vehicle model
        try:
             base_insurance_percent = vehicle.insurance_cost_percent
        except AttributeError:
             logger.warning(f"Vehicle {vehicle.name} missing 'insurance_cost_percent' attribute. Using fallback 0.")
             base_insurance_percent = 0.0
             
        increase_rate = scenario.insurance_increase_rate

        # Calculate the insurance cost percent for the current year
        current_year_percent = base_insurance_percent * ((1 + increase_rate) ** calculation_year_index)
        annual_cost = vehicle.purchase_price * current_year_percent

        return annual_cost


class RegistrationCost(CostComponent):
    """Handles registration costs, using vehicle-specific base cost and scenario increase rate."""
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        """Returns the fixed annual registration cost from the scenario."""
        # TODO: Could potentially vary by vehicle type or year based on policy
        # Use the registration cost defined directly on the vehicle model
        base_registration_cost = vehicle.registration_cost
        increase_rate = scenario.registration_increase_rate

        # Calculate the registration cost for the current year
        current_year_cost = base_registration_cost * ((1 + increase_rate) ** calculation_year_index)

        return current_year_cost


class ResidualValue(CostComponent):
    """Handles residual value calculation (applied as a negative cost in the final year)."""
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        """Calculates the residual value recovery in the final year."""
        analysis_period_years = scenario.end_year - scenario.start_year + 1
        
        # Residual value is recovered only in the final year of the analysis period
        if calculation_year_index == analysis_period_years - 1:
            vehicle_age_at_end = analysis_period_years
            try:
                # Use the vehicle's own method to calculate residual value
                residual_value = vehicle.calculate_residual_value(age_years=vehicle_age_at_end)
                # Return as a negative cost (i.e., income/value recovery)
                return -residual_value 
            except AttributeError:
                logger.error("Warning: vehicle missing calculate_residual_value method.")
                return 0.0 # Fallback
            except Exception as e:
                 logger.error(f"Error calculating residual value: {e}")
                 return 0.0 # Fallback
        else:
            # No residual value recovery in other years
            return 0.0

class CarbonTaxCost(CostComponent):
    """Handles carbon tax costs for diesel vehicles."""

    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: int, total_mileage_km: float
    ) -> float:
        if not isinstance(vehicle, DieselVehicle) or not scenario.include_carbon_tax:
            return 0.0

        annual_mileage = scenario.annual_mileage
        # CO2 emission factor in kg CO2e/L
        emission_factor_kg_per_l = vehicle.co2_emission_factor
        # Energy consumption in L/km
        consumption_l_per_km = vehicle.energy_consumption

        # Calculate annual fuel consumption in Liters
        annual_fuel_l = annual_mileage * consumption_l_per_km

        # Calculate total annual CO2 emissions in kg
        total_co2_kg = annual_fuel_l * emission_factor_kg_per_l
        # Convert kg to tonnes (1 tonne = 1000 kg)
        total_co2_tonnes = total_co2_kg / 1000.0

        # Get the carbon tax rate for the current year
        current_tax_rate = scenario.get_annual_price('carbon_tax', calculation_year_index)
        if current_tax_rate is None:
             logger.error(f"Carbon tax rate for year index {calculation_year_index} (Year {year}) not found.")
             return 0.0

        # Calculate annual carbon tax cost
        annual_carbon_tax = total_co2_tonnes * current_tax_rate
        return annual_carbon_tax

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
