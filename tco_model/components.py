from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type, NewType, List
import numpy as np # Needed for financial calculations like PMT
import numpy_financial as npf # Import the financial functions
import logging
from pydantic import PrivateAttr
import math

# Import utility for data loading
from utils.data_handlers import load_battery_costs, YamlData, DirectoryPath
# Import custom types from utils
from utils.financial import AUD, Years, Percentage, Rate
from utils.conversions import Kilometres, KWH, LitersPer100KM, KWHPerKM, YearIndex

# Import necessary classes from other modules
from .vehicles import Vehicle, ElectricVehicle, DieselVehicle
from .scenarios import Scenario

logger = logging.getLogger(__name__)

# Define CalendarYear type
CalendarYear = NewType('CalendarYear', int)
# Battery costs dictionary type
BatteryCostProjections = Dict[CalendarYear, AUD] # Year -> Cost/kWh

# Global variable to cache battery costs (simple cache)
_cached_battery_costs: Optional[BatteryCostProjections] = None

def get_battery_cost_per_kwh(year: CalendarYear, scenario: Scenario, vehicle: Optional[Vehicle] = None) -> AUD:
    """Gets the battery cost per kWh (AUD) for a given calendar year.
    Prioritizes vehicle projections, then scenario projections, then default cache/load.
    Uses simple interpolation/extrapolation if the exact year is not found.
    """
    global _cached_battery_costs

    costs: Optional[BatteryCostProjections] = None

    # 1. Check Scenario object for explicitly provided projections first
    # Assuming scenario stores projections as Dict[int, float] or similar
    if scenario.battery_pack_cost_aud_per_kwh_projections:
        costs = scenario.battery_pack_cost_aud_per_kwh_projections # Assume Scenario already returns correct type
        logger.debug(f"Using battery cost projections provided explicitly in scenario '{scenario.name}'.")

    # 2. Check Vehicle object if it's an EV and scenario didn't provide projections
    elif isinstance(vehicle, ElectricVehicle) and hasattr(vehicle, 'battery_pack_cost_aud_per_kwh_projections') and vehicle.battery_pack_cost_aud_per_kwh_projections:
        costs = vehicle.battery_pack_cost_aud_per_kwh_projections # Assume Vehicle already returns correct type
        logger.debug(f"Using battery cost projections from vehicle '{vehicle.name}'.")

    # 3. If not found on vehicle or scenario, try loading from default and using cache
    if costs is None:
        if _cached_battery_costs is None:
            logger.info("Attempting to load default battery costs (not provided in scenario or vehicle). Cache empty.")
            # Assuming load_battery_costs returns YamlData (Dict[str, Any])
            loaded_data: YamlData = load_battery_costs()
            if loaded_data and 'battery_pack_cost_aud_per_kwh' in loaded_data:
                raw_costs = loaded_data['battery_pack_cost_aud_per_kwh']
                if isinstance(raw_costs, dict):
                    try:
                        # Convert keys to CalendarYear (int) and values to AUD (float)
                        _cached_battery_costs = {CalendarYear(int(k)): AUD(float(v)) for k, v in raw_costs.items()}
                        logger.info(f"Loaded and cached default battery costs: {len(_cached_battery_costs)} entries.")
                    except (ValueError, TypeError) as e:
                        logger.error(f"Error converting loaded battery cost data to Dict[CalendarYear, AUD]: {e}")
                        _cached_battery_costs = {}
                else:
                     _cached_battery_costs = {}
                     logger.warning(f"Default battery costs key 'battery_pack_cost_aud_per_kwh' is not a dictionary.")
            else:
                _cached_battery_costs = {}
                logger.warning("Could not load default battery costs or key 'battery_pack_cost_aud_per_kwh' not found.")
        costs = _cached_battery_costs
        if costs:
             logger.debug("Using cached default battery costs.")

    # Handle case where no cost data is available at all
    if not costs:
        fallback_cost = AUD(100.0) # Fallback cost if no data is available
        logger.warning(f"No battery cost data found for year {year}. Using fallback cost: {fallback_cost:.2f} AUD/kWh")
        return fallback_cost

    # Sort years for interpolation/extrapolation
    sorted_years: List[CalendarYear] = sorted(costs.keys())

    if year in costs:
        return costs[year]
    elif year < sorted_years[0]:
        # Extrapolate backwards (use first available year's cost)
        cost: AUD = costs[sorted_years[0]]
        logger.debug(f"Year {year} before projection range. Using cost from {sorted_years[0]}: {cost:.2f}")
        return cost
    elif year > sorted_years[-1]:
        # Extrapolate forwards (use last available year's cost)
        cost: AUD = costs[sorted_years[-1]]
        logger.debug(f"Year {year} after projection range. Using cost from {sorted_years[-1]}: {cost:.2f}")
        return cost
    else:
        # Interpolate linearly between the two closest years
        prev_year: CalendarYear = max(y for y in sorted_years if y < year)
        next_year: CalendarYear = min(y for y in sorted_years if y > year)
        prev_cost: AUD = costs[prev_year]
        next_cost: AUD = costs[next_year]

        if next_year == prev_year: # Should not happen with sorted list check
             return prev_cost

        # Linear interpolation: ensure calculation uses floats, then cast back to AUD
        interpolation_factor: float = (float(year) - float(prev_year)) / (float(next_year) - float(prev_year))
        interpolated_cost_float: float = float(prev_cost) + interpolation_factor * (float(next_cost) - float(prev_cost))
        interpolated_cost: AUD = AUD(interpolated_cost_float)
        logger.debug(f"Interpolating battery cost for year {year} between {prev_year} and {next_year}. Result: {interpolated_cost:.2f}")
        return interpolated_cost


class CostComponent(ABC):
    """Abstract base class for all cost components."""

    @abstractmethod
    def calculate_annual_cost(
        self,
        year: CalendarYear,
        vehicle: Vehicle,
        scenario: Scenario,
        calculation_year_index: YearIndex,
        total_mileage_km: Kilometres
    ) -> AUD:
        """
        Calculate the cost (AUD) for this component for a specific calendar year.

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
    """Handles vehicle acquisition costs (purchase price and loan payments)."""

    def calculate_annual_cost(
        self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: YearIndex, total_mileage_km: Kilometres
    ) -> AUD:
        """Return the vehicle acquisition cost (AUD) based on financing method."""

        financing_method: str = scenario.financing_options.financing_method.lower()
        purchase_price: AUD = vehicle.base_purchase_price_aud

        if financing_method == 'cash':
            # Full purchase price in year 0 (index 0), 0 otherwise
            return purchase_price if calculation_year_index == 0 else AUD(0.0)

        elif financing_method == 'loan':
            down_payment_percent: Percentage = scenario.financing_options.down_payment_percent
            loan_term_years: Years = scenario.financing_options.loan_term_years
            interest_rate_percent: Percentage = scenario.financing_options.loan_interest_rate_percent

            if calculation_year_index == 0:
                # Year 0: Down payment
                down_payment_fraction: float = float(down_payment_percent) / 100.0
                down_payment: AUD = AUD(purchase_price * down_payment_fraction)
                return down_payment
            elif 1 <= calculation_year_index <= loan_term_years:
                # Years 1 to loan_term: Calculate annual loan payment
                down_payment_fraction = float(down_payment_percent) / 100.0
                loan_amount: AUD = AUD(purchase_price * (1.0 - down_payment_fraction))
                interest_rate_fraction: Rate = Rate(float(interest_rate_percent) / 100.0)

                # Handle zero interest rate separately to avoid numpy errors
                annual_payment_float: float
                if interest_rate_fraction == 0:
                    annual_payment_float = float(loan_amount) / loan_term_years if loan_term_years > 0 else 0.0
                elif loan_term_years > 0:
                    # Use npf.pmt now
                    annual_payment_float = -npf.pmt(interest_rate_fraction, loan_term_years, float(loan_amount))
                else:
                    annual_payment_float = 0.0 # No payment if term is 0

                return AUD(annual_payment_float)
            else:
                # After loan term, cost is 0
                return AUD(0.0)
        else:
            raise ValueError(f"Unsupported financing method: {scenario.financing_options.financing_method}")


class EnergyCost(CostComponent):
    """Handles energy costs (fuel/electricity)."""

    def calculate_annual_cost(
        self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: YearIndex, total_mileage_km: Kilometres
    ) -> AUD:
        """Calculate energy cost (AUD) for the specified year using scenario prices and the vehicle's strategy."""
        annual_mileage: Kilometres = scenario.operational_parameters.annual_mileage_km

        # Determine the correct price key based on the vehicle's energy unit
        energy_unit: str = vehicle.energy_consumption_strategy.unit
        energy_price_key: str
        if energy_unit == 'kWh':
            energy_price_key = 'electricity_price_aud_per_kwh'
        elif energy_unit == 'L':
            energy_price_key = 'diesel_price_aud_per_l'
        else:
            raise TypeError(f"Unsupported energy unit '{energy_unit}' from vehicle's strategy.")

        # Scenario.get_annual_price returns Optional[float] or similar
        energy_price_opt: Optional[float] = scenario.get_annual_price(energy_price_key, calculation_year_index)
        if energy_price_opt is None:
             raise ValueError(f"{energy_unit} price (key: {energy_price_key}) for year {year} (index {calculation_year_index}) not found")
        energy_price_aud_per_unit: AUD = AUD(energy_price_opt)

        # Call the unified calculate_annual_energy_cost method on the vehicle
        # Ensure the vehicle method accepts Kilometres and returns AUD
        annual_cost: AUD = vehicle.calculate_annual_energy_cost(
            annual_mileage_km=annual_mileage,
            energy_price_aud_per_unit=energy_price_aud_per_unit
        )
        return annual_cost


class MaintenanceCost(CostComponent):
    """Calculates annual maintenance costs using a strategy pattern."""

    def calculate_annual_cost(
        self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: YearIndex, total_mileage_km: Kilometres
    ) -> AUD:
        """
        Calculates the maintenance cost (AUD) for a given year using the vehicle's strategy.
        Applies the general annual maintenance increase rate.
        """
        # Get the appropriate strategy from the vehicle (assuming it returns a strategy object)
        strategy = vehicle.maintenance_strategy

        # Calculate the base annual cost using the strategy (assuming returns AUD)
        base_annual_cost: AUD = strategy.calculate_base_annual_cost(vehicle, scenario)

        # Apply general annual increase rate from scenario
        increase_rate_percent: Percentage = scenario.general_cost_increase_rates.maintenance_annual_increase_rate_percent
        increase_factor: float = (1.0 + (float(increase_rate_percent) / 100.0)) ** calculation_year_index
        adjusted_annual_cost: AUD = AUD(base_annual_cost * increase_factor)

        return adjusted_annual_cost


class InfrastructureCost(CostComponent):
    """Calculates annual infrastructure costs (charger installation and maintenance)."""

    _installation_cost_calculated: bool = PrivateAttr(default=False)

    def reset(self) -> None:
        self._installation_cost_calculated = False

    def calculate_annual_cost(
        self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: YearIndex, total_mileage_km: Kilometres
    ) -> AUD:
        """Calculates the annual infrastructure cost (AUD) (installation + maintenance)."""
        if not isinstance(vehicle, ElectricVehicle):
            return AUD(0.0) # No infrastructure cost for non-EVs

        infra_config = scenario.infrastructure_costs # Access renamed container
        annual_cost_float: float = 0.0

        # Installation cost (assumed in year 0)
        # This component is called annually, need state to only add installation once
        if calculation_year_index == 0 and not self._installation_cost_calculated:
            # Charger cost + Installation cost (assuming these are AUD)
            annual_cost_float += float(infra_config.selected_charger_cost_aud)
            annual_cost_float += float(infra_config.selected_installation_cost_aud)
            self._installation_cost_calculated = True # Mark as calculated for this run

        # Annual Maintenance Cost (percentage of hardware cost)
        maintenance_rate_percent: Percentage = infra_config.charger_maintenance_annual_rate_percent
        maintenance_rate_fraction: float = float(maintenance_rate_percent) / 100.0
        charger_cost: AUD = infra_config.selected_charger_cost_aud
        annual_cost_float += float(charger_cost) * maintenance_rate_fraction

        # TODO: Add logic for charger REPLACEMENT based on lifespan_years?
        # If charger_lifespan_years triggers a replacement within the analysis period,
        # we would need to add the selected_charger_cost_aud and selected_installation_cost_aud
        # again in that specific year. This requires careful handling of state or
        # calculation logic similar to battery replacement.
        # For now, only includes initial cost and ongoing maintenance.

        return AUD(annual_cost_float)


class BatteryReplacementCost(CostComponent):
    """Calculates the cost of battery replacement based on degradation or forced year."""

    _replacement_year_index: Optional[YearIndex] = PrivateAttr(default=None)
    _cost_calculated: bool = PrivateAttr(default=False)

    def reset(self) -> None:
        """Reset state for a new calculation run."""
        self._replacement_year_index = None
        self._cost_calculated = False

    def calculate_annual_cost(
        self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: YearIndex, total_mileage_km: Kilometres
    ) -> AUD:
        """Calculate battery replacement cost (AUD), which occurs only once."""
        # This method needs the vehicle to be ElectricVehicle
        if not isinstance(vehicle, ElectricVehicle):
            return AUD(0.0)

        batt_config = scenario.battery_replacement_config # Access renamed container

        if not batt_config.enable_battery_replacement:
            return AUD(0.0)

        # If cost already calculated for this run, return 0
        if self._cost_calculated:
            return AUD(0.0)

        # Determine if replacement happens THIS year (index)
        replacement_occurs_this_year: bool = False
        if self._replacement_year_index is None: # Only determine replacement year once
            # Check for forced replacement first
            # Assume force_replacement_year_index is YearIndex type
            forced_year_index: Optional[YearIndex] = batt_config.force_replacement_year_index
            if forced_year_index is not None and forced_year_index == calculation_year_index:
                self._replacement_year_index = calculation_year_index
                logger.info(f"Battery replacement forced in year {year} (index {calculation_year_index}) for {vehicle.name}.")
                replacement_occurs_this_year = True
            else:
                # Check degradation threshold if not forced
                # Assume replacement_threshold_fraction is float (0-1)
                degradation_threshold: Optional[float] = batt_config.replacement_threshold_fraction
                if degradation_threshold is not None:
                    # Calculate current degradation state
                    # Note: vehicle.calculate_battery_degradation_factor needs age_years (Years)
                    age_years = Years(calculation_year_index) # Assuming calculation_year_index is the age in years
                    # Assuming method returns float (0-1)
                    remaining_capacity_fraction: float = vehicle.calculate_battery_degradation_factor(age_years, total_mileage_km)

                    if remaining_capacity_fraction <= degradation_threshold:
                        self._replacement_year_index = calculation_year_index
                        logger.info(f"Battery degradation threshold ({degradation_threshold:.2f}) reached in year {year} (index {calculation_year_index}). Remaining: {remaining_capacity_fraction:.2f}. Triggering replacement for {vehicle.name}.")
                        replacement_occurs_this_year = True
        elif self._replacement_year_index == calculation_year_index:
             replacement_occurs_this_year = True # Already determined replacement happens now

        # If replacement happens this year, calculate and return cost
        if replacement_occurs_this_year:
            # We know vehicle is ElectricVehicle here due to the check at the start
            replacement_cost: AUD = self._calculate_replacement_cost(year, vehicle, scenario)
            self._cost_calculated = True # Mark as calculated for this run
            return replacement_cost
        else:
            return AUD(0.0) # No replacement cost this year

    def _calculate_replacement_cost(self, year: CalendarYear, vehicle: ElectricVehicle, scenario: Scenario) -> AUD:
        """Helper to calculate the actual cost (AUD) of replacement in a given calendar year."""
        # Assume vehicle.battery_capacity_kwh returns KWH
        battery_capacity: KWH = vehicle.battery_capacity_kwh
        # Assume get_battery_cost_per_kwh returns AUD
        cost_per_kwh: AUD = get_battery_cost_per_kwh(year, scenario, vehicle)
        replacement_cost_float: float = float(battery_capacity) * float(cost_per_kwh)
        replacement_cost: AUD = AUD(replacement_cost_float)
        logger.debug(f"Calculated battery replacement cost in year {year} for {vehicle.name}: {replacement_cost:.2f} AUD ({battery_capacity} kWh * {cost_per_kwh:.2f} AUD/kWh)")
        return replacement_cost


class InsuranceCost(CostComponent):
    """Calculates annual insurance costs."""

    def calculate_annual_cost(
        self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: YearIndex, total_mileage_km: Kilometres
    ) -> AUD:
        """
        Calculates the insurance cost (AUD) for a given year.
        Uses detailed costs from scenario, potentially based on vehicle value.
        Applies the annual insurance increase rate.
        """
        ins_reg_costs = scenario.insurance_registration_costs # Access renamed container
        increase_rate_percent: Percentage = scenario.general_cost_increase_rates.insurance_annual_increase_rate_percent

        # Get the correct detail object based on vehicle type (assuming it has cost_type, etc.)
        detail: Any # Replace Any with a specific type if available
        if isinstance(vehicle, ElectricVehicle):
            detail = ins_reg_costs.electric
        elif isinstance(vehicle, DieselVehicle):
            detail = ins_reg_costs.diesel
        else:
             raise TypeError("Vehicle type not supported for InsuranceCost calculation.")

        # Calculate base cost for the year based on type
        base_cost_float: float = 0.0
        if detail.cost_type == 'fixed':
            # Assume base_annual_cost_aud is AUD
            base_cost_float = float(detail.base_annual_cost_aud)
        elif detail.cost_type == 'percentage_of_value':
            # Assume annual_rate_percent_of_value is Percentage
            rate_percent: Optional[Percentage] = detail.annual_rate_percent_of_value
            if rate_percent is None:
                 raise ValueError(f"Insurance cost type is 'percentage_of_value' but annual_rate_percent_of_value is not set for {vehicle.__class__.__name__}")
            # Need current vehicle value (residual value)
            age_years = Years(calculation_year_index) # Assume age matches index
            # Assume calculate_residual_value_aud returns AUD
            current_value: AUD = vehicle.calculate_residual_value_aud(age_years)
            base_cost_float = float(current_value) * (float(rate_percent) / 100.0)
        else:
            raise ValueError(f"Unsupported insurance cost_type: {detail.cost_type}")

        # Apply annual increase rate
        increase_factor: float = (1.0 + (float(increase_rate_percent) / 100.0)) ** calculation_year_index
        adjusted_annual_cost_float: float = base_cost_float * increase_factor
        return AUD(adjusted_annual_cost_float)


class RegistrationCost(CostComponent):
    """Calculates annual registration costs."""

    def calculate_annual_cost(
        self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: YearIndex, total_mileage_km: Kilometres
    ) -> AUD:
        """
        Calculates the registration cost (AUD) for a given year.
        Uses the base cost from the vehicle and applies the scenario's increase rate.
        """
        # Assume base_registration_cost_aud is AUD
        base_cost: AUD = vehicle.base_registration_cost_aud
        # Assume registration_annual_increase_rate_percent is Percentage
        increase_rate_percent: Percentage = scenario.general_cost_increase_rates.registration_annual_increase_rate_percent

        # Apply annual increase rate
        increase_factor: float = (1.0 + (float(increase_rate_percent) / 100.0)) ** calculation_year_index
        adjusted_annual_cost_float: float = float(base_cost) * increase_factor
        return AUD(adjusted_annual_cost_float)


class ResidualValue(CostComponent):
    """Calculates the residual value (negative cost) in the final year."""

    def calculate_annual_cost(
        self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: YearIndex, total_mileage_km: Kilometres
    ) -> AUD:
        """
        Returns the negative residual value (AUD) only in the final year of the analysis period.
        """
        # Assume analysis_period_years is Years
        analysis_period: Years = scenario.analysis_period_years
        final_year_index: YearIndex = YearIndex(analysis_period - 1)

        if calculation_year_index == final_year_index:
            # Calculate residual value at the end of the analysis period
            age_at_end: Years = analysis_period
            # Assume calculate_residual_value_aud returns AUD
            residual_value: AUD = vehicle.calculate_residual_value_aud(age_at_end)
            # Return as a negative cost
            return AUD(-float(residual_value))
        else:
            return AUD(0.0)


class CarbonTaxCost(CostComponent):
    """Calculates annual carbon tax cost for diesel vehicles."""

    def calculate_annual_cost(
        self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: YearIndex, total_mileage_km: Kilometres
    ) -> AUD:
        """
        Calculates the carbon tax cost (AUD) based on emissions and the annual tax rate.
        Applies only to diesel vehicles if enabled in the scenario.
        """
        if not isinstance(vehicle, DieselVehicle):
            return AUD(0.0)

        if not scenario.carbon_tax_config.include_carbon_tax:
            return AUD(0.0)

        # Assume annual_mileage_km is Kilometres
        annual_mileage: Kilometres = scenario.operational_parameters.annual_mileage_km

        # Calculate annual fuel consumption
        # Assume calculate_energy_consumption returns float (litres for Diesel)
        fuel_consumption_l: float = vehicle.calculate_energy_consumption(annual_mileage)

        # Calculate annual CO2 emissions in tonnes
        # Assume co2_emission_factor_kg_per_l is float
        co2_kg_per_l: float = vehicle.co2_emission_factor_kg_per_l
        total_co2_kg: float = fuel_consumption_l * co2_kg_per_l
        total_co2_tonnes: float = total_co2_kg / 1000.0

        # Get the carbon tax rate for the current year
        tax_rate_key: str = 'carbon_tax_rate_aud_per_tonne'
        # Assume get_annual_price returns Optional[float]
        tax_rate_opt: Optional[float] = scenario.get_annual_price(tax_rate_key, calculation_year_index)

        if tax_rate_opt is None:
             raise ValueError(f"Carbon tax rate (key: {tax_rate_key}) for year {year} (index {calculation_year_index}) not found")
        tax_rate_aud_per_tonne: AUD = AUD(tax_rate_opt)

        # Calculate annual carbon tax cost
        annual_tax_cost_float: float = total_co2_tonnes * float(tax_rate_aud_per_tonne)
        return AUD(annual_tax_cost_float)


class RoadUserChargeCost(CostComponent):
    """Calculates annual road user charge cost."""

    def calculate_annual_cost(
        self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
        calculation_year_index: YearIndex, total_mileage_km: Kilometres
    ) -> AUD:
        """
        Calculates the road user charge (AUD) based on annual mileage and the annual charge rate.
        Applies only if enabled in the scenario.
        """
        if not scenario.road_user_charge_config.include_road_user_charge:
            return AUD(0.0)

        # Assume annual_mileage_km is Kilometres
        annual_mileage: Kilometres = scenario.operational_parameters.annual_mileage_km

        # Get the road user charge rate for the current year
        charge_rate_key: str = 'road_user_charge_aud_per_km'
        # Assume get_annual_price returns Optional[float]
        charge_rate_opt: Optional[float] = scenario.get_annual_price(charge_rate_key, calculation_year_index)

        if charge_rate_opt is None:
             raise ValueError(f"Road user charge rate (key: {charge_rate_key}) for year {year} (index {calculation_year_index}) not found")
        charge_aud_per_km: AUD = AUD(charge_rate_opt)

        # Calculate annual road user charge cost
        annual_charge_cost_float: float = float(annual_mileage) * float(charge_aud_per_km)
        return AUD(annual_charge_cost_float)


# Example of how to potentially add a new cost component
# class TollCost(CostComponent):
#     """Calculates annual toll costs (example)."""
#     def calculate_annual_cost(
#         self, year: CalendarYear, vehicle: Vehicle, scenario: Scenario,
#         calculation_year_index: YearIndex, total_mileage_km: Kilometres
#     ) -> AUD:
#         # Access relevant parameters from scenario or vehicle
#         # e.g., scenario.operational_parameters.estimated_annual_toll_cost
#         # Apply increase rates if necessary
#         base_toll = scenario.operational_parameters.get('estimated_annual_toll_cost', 0) # Hypothetical
#         increase_rate = scenario.general_cost_increase_rates.get('tolls', 0.02) # Hypothetical
#         increase_factor = (1 + increase_rate) ** calculation_year_index
#         return base_toll * increase_factor
