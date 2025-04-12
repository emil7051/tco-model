# Standard library imports
from datetime import datetime
import logging
import os
from typing import Any, Dict, List, Optional, Union

# Third-party imports
from pydantic import (
    BaseModel, ConfigDict, Field, PrivateAttr, ValidationInfo,
    field_validator, model_validator, validator
)
import yaml

# Application-specific imports
from .vehicles import DieselVehicle, ElectricVehicle

logger = logging.getLogger(__name__)


# --- Component Models for Scenario ---

class EconomicParameters(BaseModel):
    discount_rate_percent_real: float = Field(..., description="Real annual discount rate (e.g., 3.0 for 3%)", ge=0)
    inflation_rate_percent: Optional[float] = Field(2.5, description="Assumed general inflation rate (e.g., 2.5 for 2.5%)", ge=0)

class OperationalParameters(BaseModel):
    annual_mileage_km: float = Field(..., description="Average annual kilometers driven", gt=0)

class FinancingOptions(BaseModel):
    financing_method: str = Field("loan", description="Method of vehicle acquisition (cash or loan)")
    down_payment_percent: float = Field(20.0, description="Down payment percentage for loan financing (e.g., 20.0 for 20%)", ge=0, le=100.0)
    loan_term_years: int = Field(5, description="Loan term in years", gt=0)
    loan_interest_rate_percent: float = Field(5.0, description="Annual interest rate for loan (e.g., 5.0 for 5%)", ge=0)

class InfrastructureCosts(BaseModel):
    """Models costs associated with charging infrastructure."""
    charger_hardware_costs_aud: Optional[Dict[str, float]] = Field(None, description="Costs for different types of charger hardware (AUD)")
    selected_charger_cost_aud: float = Field(..., description="Cost of the selected charger hardware (AUD)", ge=0)
    selected_installation_cost_aud: float = Field(..., description="Cost of installing the selected charger (AUD)", ge=0)
    charger_maintenance_annual_rate_percent: float = Field(1.0, description="Annual charger maintenance as a percentage of hardware cost (e.g., 1.0 for 1%)", ge=0)
    charger_lifespan_years: int = Field(10, description="Lifespan of the charger in years", gt=0)
    # Add other relevant fields if they exist in the dictionary
    model_config = ConfigDict(extra='allow') # Allow extra fields if dict structure varies

class ElectricityPricePoint(BaseModel):
    """Represents a single price point, which could be a single value or a range."""
    price_aud_per_kwh_or_range: Union[float, List[float]] = Field(..., description="Price in AUD/kWh or a [min, max] range")

    @validator('price_aud_per_kwh_or_range')
    def check_list_length(cls, v):
        if isinstance(v, list):
            if len(v) != 2:
                raise ValueError("Price range list must contain exactly two values [min, max]")
            if v[0] > v[1]:
                 raise ValueError("Min price cannot be greater than max price in range")
        return v

    def get_average_price_aud_per_kwh(self) -> float:
        """Returns the average price, or the single value if not a range."""
        if isinstance(self.price_aud_per_kwh_or_range, list):
            return sum(self.price_aud_per_kwh_or_range) / 2.0
        return float(self.price_aud_per_kwh_or_range)

class ElectricityPriceScenario(BaseModel):
    """Represents projected electricity prices for a named scenario."""
    name: str
    prices: Dict[int, ElectricityPricePoint] # Year -> PricePoint

class ElectricityPriceProjections(BaseModel):
    """Container for multiple electricity price scenarios."""
    scenarios: List[ElectricityPriceScenario]
    selected_scenario_name: str = Field(..., description="Name of the electricity price scenario to use")

    @model_validator(mode='before')
    @classmethod
    def check_selected_scenario_exists(cls, values):
        scenarios = values.get('scenarios')
        selected_name = values.get('selected_scenario_name')
        if scenarios and selected_name:
            if not any(s.get('name') == selected_name for s in scenarios if isinstance(s, dict)) and \
               not any(s.name == selected_name for s in scenarios if not isinstance(s, dict)):
                raise ValueError(f"Selected electricity scenario '{selected_name}' not found in provided scenarios.")
        return values

class DieselPriceScenarioData(BaseModel):
    """Represents diesel price data, either a single value or yearly projections."""
    price_aud_per_l_or_projection: Union[float, Dict[int, float]] = Field(..., description="Constant price (AUD/L) or projection {year: price}")

    def get_price_aud_per_l_for_year(self, year: int, analysis_start_year: int, analysis_period_years: int) -> float:
        """Gets the diesel price for a specific analysis year using interpolation/extrapolation."""
        if isinstance(self.price_aud_per_l_or_projection, (int, float)):
            # Constant price
            return float(self.price_aud_per_l_or_projection)
        elif isinstance(self.price_aud_per_l_or_projection, dict):
            prices = self.price_aud_per_l_or_projection
            if not prices:
                raise ValueError("Diesel price projection dictionary cannot be empty.")

            sorted_proj_years = sorted(prices.keys())

            if year in prices:
                return float(prices[year])
            elif year < sorted_proj_years[0]:
                # Extrapolate backwards (use first year's price)
                return float(prices[sorted_proj_years[0]])
            elif year > sorted_proj_years[-1]:
                # Extrapolate forwards (use last year's price)
                return float(prices[sorted_proj_years[-1]])
            else:
                # Interpolate linearly
                prev_year = max(y for y in sorted_proj_years if y < year)
                next_year = min(y for y in sorted_proj_years if y > year)
                prev_price = float(prices[prev_year])
                next_price = float(prices[next_year])

                if next_year == prev_year: return prev_price # Should not happen

                interpolation_factor = (year - prev_year) / (next_year - prev_year)
                interpolated_price = prev_price + interpolation_factor * (next_price - prev_price)
                return interpolated_price
        else:
             raise ValueError(f"Invalid diesel price data format: {self.price_aud_per_l_or_projection}")

class DieselPriceScenario(BaseModel):
    """Represents a named diesel price scenario."""
    name: str
    data: DieselPriceScenarioData

class DieselPriceProjections(BaseModel):
    """Container for multiple diesel price scenarios."""
    scenarios: List[DieselPriceScenario]
    selected_scenario_name: str = Field(..., description="Name of the diesel price scenario to use")

    @model_validator(mode='before')
    @classmethod
    def check_selected_scenario_exists(cls, values):
        scenarios = values.get('scenarios')
        selected_name = values.get('selected_scenario_name')
        if scenarios and selected_name:
            if not any(s.get('name') == selected_name for s in scenarios if isinstance(s, dict)) and \
               not any(s.name == selected_name for s in scenarios if not isinstance(s, dict)):
                raise ValueError(f"Selected diesel scenario '{selected_name}' not found in provided scenarios.")
        return values

class MaintenanceDetail(BaseModel):
    """Detailed maintenance costs for a specific component or schedule."""
    # Example fields - adjust based on actual dictionary keys used
    schedule_type: Optional[str] = Field(None, description="e.g., 'annual', 'km_interval'")
    annual_cost_min_aud: Optional[float] = Field(None, description="Minimum annual cost (AUD)", ge=0)
    annual_cost_max_aud: Optional[float] = Field(None, description="Maximum annual cost (AUD)", ge=0)
    cost_aud_per_km: Optional[float] = Field(None, description="Cost per km (AUD/km)", ge=0)
    service_interval_km: Optional[int] = Field(None, description="Kilometer interval for service", gt=0)
    # Allow flexibility
    model_config = ConfigDict(extra='allow')

class MaintenanceCosts(BaseModel):
    """Container for detailed maintenance costs per vehicle type, keyed by vehicle sub-type."""
    # Keys should match patterns like 'rigid_bet', 'articulated_diesel' etc.
    costs_by_type: Dict[str, MaintenanceDetail] = Field(..., description="Detailed maintenance costs keyed by type (e.g., 'rigid_bet'), containing dicts with keys like 'annual_min', 'annual_max'")

class InsuranceRegistrationDetail(BaseModel):
    """Detailed insurance and registration costs."""
    # Example fields - adjust based on actual dictionary keys used
    base_annual_cost_aud: float = Field(..., description="Base annual cost (AUD)", ge=0)
    cost_type: str = Field("fixed", description="Type of cost ('fixed', 'percentage_of_value')")
    annual_rate_percent_of_value: Optional[float] = Field(None, description="Annual rate as % of vehicle value (e.g., 1.5 for 1.5%)", ge=0)
    # Allow flexibility
    model_config = ConfigDict(extra='allow')

class InsuranceRegistrationCosts(BaseModel):
    """Container for insurance and registration costs per vehicle type."""
    electric: InsuranceRegistrationDetail
    diesel: InsuranceRegistrationDetail

class CarbonTaxConfig(BaseModel):
    include_carbon_tax: bool = Field(True, description="Include carbon tax in calculations")
    initial_rate_aud_per_tonne_co2e: float = Field(0.0, description="Initial carbon tax rate (AUD/tonne CO2e)", ge=0)
    annual_increase_rate_percent: float = Field(0.0, description="Annual increase rate for carbon tax (e.g., 2.0 for 2%)", ge=0)

class RoadUserChargeConfig(BaseModel):
    include_road_user_charge: bool = Field(True, description="Include road user charge in calculations")
    initial_charge_aud_per_km: float = Field(0.0, description="Initial road user charge (AUD/km)", ge=0)
    annual_increase_rate_percent: float = Field(0.0, description="Annual increase rate for road user charge (e.g., 1.0 for 1%)", ge=0)

class GeneralCostIncreaseRates(BaseModel):
    maintenance_annual_increase_rate_percent: float = Field(0.0, description="Annual increase rate for maintenance costs (e.g., 1.5 for 1.5%)", ge=0)
    insurance_annual_increase_rate_percent: float = Field(0.0, description="Annual increase rate for insurance costs (e.g., 1.0 for 1%)", ge=0)
    registration_annual_increase_rate_percent: float = Field(0.0, description="Annual increase rate for registration costs (e.g., 0.5 for 0.5%)", ge=0)

class BatteryReplacementConfig(BaseModel):
    enable_battery_replacement: bool = Field(True, description="Enable battery replacement logic")
    annual_degradation_rate_percent: float = Field(2.0, description="Annual battery capacity degradation rate (e.g., 2.0 for 2%)", ge=0, le=100.0)
    replacement_threshold_fraction: Optional[float] = Field(0.7, description="Capacity threshold (fraction, 0 to 1) to trigger replacement", ge=0, le=1.0)
    force_replacement_year_index: Optional[int] = Field(None, description="Force battery replacement in this specific year index (0-based)", ge=0)

# --- End Component Models ---


class Scenario(BaseModel):
    """Represents a TCO calculation scenario using composed parameter objects."""

    # General
    name: str = Field(default="Default Scenario", description="Unique identifier for the scenario")
    description: Optional[str] = Field(None, description="Optional description")
    analysis_period_years: int = Field(..., description="Duration of the analysis in years", gt=0)
    analysis_start_year: int = Field(datetime.now().year, description="Starting calendar year for the analysis")

    # Economic Parameters
    economic_parameters: EconomicParameters

    # Operational Parameters
    operational_parameters: OperationalParameters

    # Vehicles (Nested models remain)
    electric_vehicle: ElectricVehicle
    diesel_vehicle: DieselVehicle

    # Financing Options
    financing_options: FinancingOptions

    # Infrastructure (EV Specific)
    infrastructure_costs: InfrastructureCosts

    # --- Base Prices / Rates (Year 0) --- (Keep for potential overrides or simple scenarios)
    base_electricity_price_aud_per_kwh: Optional[float] = Field(None, description="Optional: Base electricity price (AUD/kWh) for start year if not using projections", ge=0)
    base_diesel_price_aud_per_l: Optional[float] = Field(None, description="Optional: Base diesel price (AUD/L) for start year if not using projections", ge=0)

    # --- Price Projections / Scenarios ---
    electricity_price_projections: Optional[ElectricityPriceProjections] = Field(None, description="Electricity price projections")
    diesel_price_projections: Optional[DieselPriceProjections] = Field(None, description="Diesel price projections")

    # --- Detailed Costs ---
    maintenance_costs_detailed: Dict[str, Dict[str, Any]] = Field(..., description="Detailed maintenance costs keyed by type (e.g., 'rigid_bet'), containing dicts with keys like 'annual_min', 'annual_max'")
    insurance_registration_costs: InsuranceRegistrationCosts

    # --- Other Costs / Taxes ---
    carbon_tax_config: CarbonTaxConfig
    road_user_charge_config: RoadUserChargeConfig

    # --- General Cost Increase Rates ---
    general_cost_increase_rates: GeneralCostIncreaseRates

    # --- Flags / Options ---
    # Flags moved into specific config objects (CarbonTaxConfig, RoadUserChargeConfig, BatteryReplacementConfig)

    # Battery Replacement (EV Specific)
    battery_replacement_config: BatteryReplacementConfig

    # Optional: Field for explicitly provided battery cost projections (overrides default loading)
    battery_pack_cost_aud_per_kwh_projections: Optional[Dict[int, float]] = Field(None, description="Optional: Explicit battery pack cost projections (AUD/kWh by year)")

    # --- Internal State ---
    _generated_prices_cache: Dict[str, List[float]] = PrivateAttr(default_factory=dict)

    # Use ConfigDict for Pydantic v2 configuration
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True
    )

    # --- Computed Properties & Validators ---
    @property
    def analysis_end_year(self) -> int:
        """Calculate the end year from start_year and analysis_years."""
        return self.analysis_start_year + self.analysis_period_years - 1

    @property
    def analysis_calendar_years(self) -> List[int]:
        """Returns the list of calendar years in the analysis period."""
        return list(range(self.analysis_start_year, self.analysis_start_year + self.analysis_period_years))

    @model_validator(mode='after')
    def _calculate_and_cache_annual_prices(self) -> 'Scenario':
        """Generate annual price series for relevant costs after model initialization.
           Uses selected projections/scenarios for energy, and base+increase for others.
           Caches the results in _generated_prices_cache.
        """
        if not hasattr(self, '_generated_prices_cache'):
             self._generated_prices_cache = {}
        self._generated_prices_cache.clear()

        years = self.analysis_period_years
        start_year = self.analysis_start_year

        # 1. Carbon Tax and Road User Charge (from config objects)
        ct_base = self.carbon_tax_config.initial_rate_aud_per_tonne_co2e
        ct_inc = self.carbon_tax_config.annual_increase_rate_percent / 100.0
        ruc_base = self.road_user_charge_config.initial_charge_aud_per_km
        ruc_inc = self.road_user_charge_config.annual_increase_rate_percent / 100.0

        self._generated_prices_cache['carbon_tax_rate_aud_per_tonne'] = [ct_base * ((1 + ct_inc) ** i) for i in range(years)]
        self._generated_prices_cache['road_user_charge_aud_per_km'] = [ruc_base * ((1 + ruc_inc) ** i) for i in range(years)]

        # 2. Electricity Prices (from projections or base)
        elec_prices = []
        if self.electricity_price_projections:
            selected_scen_name = self.electricity_price_projections.selected_scenario_name
            selected_scen = next((s for s in self.electricity_price_projections.scenarios if s.name == selected_scen_name), None)
            if selected_scen:
                 proj_prices = selected_scen.prices # Dict[int, ElectricityPricePoint]
                 sorted_proj_years = sorted(proj_prices.keys())

                 for i in range(years):
                     current_year = start_year + i
                     if current_year in proj_prices:
                         elec_prices.append(proj_prices[current_year].get_average_price_aud_per_kwh())
                     elif current_year < sorted_proj_years[0]:
                          elec_prices.append(proj_prices[sorted_proj_years[0]].get_average_price_aud_per_kwh()) # Extrapolate back
                     elif current_year > sorted_proj_years[-1]:
                          elec_prices.append(proj_prices[sorted_proj_years[-1]].get_average_price_aud_per_kwh()) # Extrapolate forward
                     else:
                         # Interpolate
                         prev_year = max(y for y in sorted_proj_years if y < current_year)
                         next_year = min(y for y in sorted_proj_years if y > current_year)
                         prev_price = proj_prices[prev_year].get_average_price_aud_per_kwh()
                         next_price = proj_prices[next_year].get_average_price_aud_per_kwh()
                         interpolation_factor = (current_year - prev_year) / (next_year - prev_year)
                         interpolated_price = prev_price + interpolation_factor * (next_price - prev_price)
                         elec_prices.append(interpolated_price)
            else:
                 logger.warning(f"Selected electricity scenario '{selected_scen_name}' not found during price generation. Using base price if available.")
                 if self.base_electricity_price_aud_per_kwh is not None:
                     elec_prices = [self.base_electricity_price_aud_per_kwh] * years
                 else:
                      raise ValueError("Electricity prices are required (either projections or base price).")

        elif self.base_electricity_price_aud_per_kwh is not None:
            elec_prices = [self.base_electricity_price_aud_per_kwh] * years # Assume constant base price if no projections
        else:
             raise ValueError("Electricity prices are required (either projections or base price).")

        self._generated_prices_cache['electricity_price_aud_per_kwh'] = elec_prices


        # 3. Diesel Prices (from projections or base)
        diesel_prices = []
        if self.diesel_price_projections:
            selected_scen_name = self.diesel_price_projections.selected_scenario_name
            selected_scen = next((s for s in self.diesel_price_projections.scenarios if s.name == selected_scen_name), None)
            if selected_scen:
                 for i in range(years):
                      current_year = start_year + i
                      diesel_prices.append(selected_scen.data.get_price_aud_per_l_for_year(current_year, start_year, years))
            else:
                 logger.warning(f"Selected diesel scenario '{selected_scen_name}' not found during price generation. Using base price if available.")
                 if self.base_diesel_price_aud_per_l is not None:
                     diesel_prices = [self.base_diesel_price_aud_per_l] * years
                 else:
                      raise ValueError("Diesel prices are required (either projections or base price).")

        elif self.base_diesel_price_aud_per_l is not None:
             diesel_prices = [self.base_diesel_price_aud_per_l] * years # Assume constant base price
        else:
             raise ValueError("Diesel prices are required (either projections or base price).")

        self._generated_prices_cache['diesel_price_aud_per_l'] = diesel_prices

        # 4. General Cost Increase Rates (applied within components where needed)
        # These are stored in `general_cost_increase_rates` and accessed directly.

        logger.debug(f"Generated and cached annual prices for scenario '{self.name}'.")
        return self

    def get_annual_price(self, cost_type_key: str, calculation_year_index: int) -> Optional[float]:
        """Retrieve a pre-calculated annual price for a given cost type and year index.

        Args:
            cost_type_key: The key for the cost type (e.g., 'electricity_price_aud_per_kwh', 'diesel_price_aud_per_l',
                           'carbon_tax_rate_aud_per_tonne', 'road_user_charge_aud_per_km').
            calculation_year_index: The 0-based index of the calculation year within the analysis period.

        Returns:
            The calculated price for that year, or None if the index is invalid or key not found.
        """
        if calculation_year_index < 0 or calculation_year_index >= self.analysis_period_years:
            logger.error(f"Invalid year index {calculation_year_index} requested for scenario '{self.name}'.")
            return None

        if not self._generated_prices_cache:
             logger.warning(f"Price cache was empty for scenario '{self.name}'. Recalculating...")
             self._calculate_and_cache_annual_prices()

        price_series = self._generated_prices_cache.get(cost_type_key)

        if price_series is None:
            logger.error(f"Price series for key '{cost_type_key}' not found in scenario '{self.name}' cache.")
            return None # Or raise error?

        if calculation_year_index >= len(price_series):
             logger.error(f"Year index {calculation_year_index} out of bounds for cached price series '{cost_type_key}' (length {len(price_series)}).")
             return None # Or raise error?

        return price_series[calculation_year_index]

    @field_validator('battery_replacement_config')
    @classmethod
    def check_replacement_year_bounds(cls, v: BatteryReplacementConfig, info: ValidationInfo):
        """Validate that force_replacement_year_index is within the analysis period if set."""
        if v.force_replacement_year_index is not None and 'analysis_period_years' in info.data:
             analysis_years = info.data['analysis_period_years']
             if v.force_replacement_year_index >= analysis_years:
                 raise ValueError(f"force_replacement_year_index ({v.force_replacement_year_index}) "
                                  f"must be less than analysis_period_years ({analysis_years}). Note: 0-based index.")
        # Can add more validation for the threshold vs degradation if needed
        return v

    @classmethod
    def from_file(cls, filepath: str) -> 'Scenario':
        """Load a scenario from a YAML file."""
        logger.info(f"Loading scenario from: {filepath}")
        if not os.path.exists(filepath):
            logger.error(f"Scenario file not found: {filepath}")
            raise FileNotFoundError(f"Scenario file not found: {filepath}")
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
            if data is None:
                 raise ValueError(f"YAML file is empty or invalid: {filepath}")
            scenario = cls(**data)
            logger.info(f"Successfully loaded scenario: {scenario.name}")
            return scenario
        except yaml.YAMLError as e:
            logger.error(f"Error parsing scenario YAML file {filepath}: {e}", exc_info=True)
            raise ValueError(f"Error parsing scenario YAML file: {e}") from e
        except Exception as e: # Catch Pydantic validation errors and others
            logger.error(f"Error creating Scenario object from file {filepath}: {e}", exc_info=True)
            raise ValueError(f"Error creating Scenario object from file: {e}") from e

    def to_file(self, filepath: str) -> None:
        """Save the current scenario configuration to a YAML file."""
        logger.info(f"Saving scenario '{self.name}' to: {filepath}")
        try:
            data_to_save = self.model_dump(exclude={'_generated_prices_cache'})

            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, 'w') as f:
                yaml.dump(data_to_save, f, sort_keys=False, default_flow_style=False)
            logger.info(f"Successfully saved scenario '{self.name}'.")
        except Exception as e:
            logger.error(f"Error saving scenario '{self.name}' to file {filepath}: {e}", exc_info=True)
            raise IOError(f"Failed to save scenario to {filepath}") from e

    def to_dict(self) -> Dict[str, Any]:
        """Convert the scenario model to a dictionary (excluding internal state)."""
        return self.model_dump(exclude={'_generated_prices_cache'})

    def with_modifications(self, **kwargs) -> 'Scenario':
        """Creates a new Scenario instance with specified modifications."""
        current_data = self.model_dump(exclude={'_generated_prices_cache'})

        try:
             updated_scenario = self.model_copy(update=kwargs, deep=True)
             logger.info(f"Created modified scenario based on '{self.name}'.")
             return updated_scenario
        except Exception as e:
             logger.error(f"Failed to create modified scenario: {e}", exc_info=True)
             raise ValueError(f"Failed to apply modifications: {e}") from e


def load_scenario_from_config(config_path: str) -> Scenario:
    """Loads the TCO calculation scenario from a YAML configuration file."""
    return Scenario.from_file(config_path)

def save_scenario_to_config(scenario: Scenario, config_path: str) -> None:
    """Saves the TCO calculation scenario to a YAML configuration file."""
    scenario.to_file(config_path)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    EXAMPLE_YAML = 'config/scenario_example.yaml'

    if os.path.exists(EXAMPLE_YAML):
        try:
            scenario = Scenario.from_file(EXAMPLE_YAML)
            print(f"\nLoaded Scenario: {scenario.name}")
            print(f"Analysis Period: {scenario.analysis_period_years} years")
            print(f"Start Year: {scenario.analysis_start_year}")
            print(f"Discount Rate: {scenario.economic_parameters.discount_rate_percent_real}%")
            print(f"EV Name: {scenario.electric_vehicle.name}")
            print(f"Diesel Name: {scenario.diesel_vehicle.name}")

            print("\nGenerated Prices (Year 0):")
            print(f"  Electricity: {scenario.get_annual_price('electricity_price_aud_per_kwh', 0):.4f} AUD/kWh")
            print(f"  Diesel: {scenario.get_annual_price('diesel_price_aud_per_l', 0):.4f} AUD/L")
            print(f"  Carbon Tax: {scenario.get_annual_price('carbon_tax_rate_aud_per_tonne', 0):.2f} AUD/tonne")
            print(f"  Road User Charge: {scenario.get_annual_price('road_user_charge_aud_per_km', 0):.4f} AUD/km")

            modified_scenario = scenario.with_modifications(
                name="Modified Example Scenario",
                economic_parameters={'discount_rate_percent_real': 4.5}
            )
            print(f"\nModified Scenario Discount Rate: {modified_scenario.economic_parameters.discount_rate_percent_real}%")

            output_dir = 'output'
            os.makedirs(output_dir, exist_ok=True)
            save_path = os.path.join(output_dir, 'modified_scenario_example.yaml')
            modified_scenario.to_file(save_path)
            print(f"Saved modified scenario to: {save_path}")

        except (FileNotFoundError, ValueError, IOError) as e:
            print(f"\nError processing scenario: {e}")
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
            import traceback
            traceback.print_exc()

    else:
        print(f"\nExample YAML file not found at '{EXAMPLE_YAML}'. Cannot run example.")
