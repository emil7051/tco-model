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

class Scenario(BaseModel):
    """Represents a TCO calculation scenario with all input parameters.

    Holds configuration for the analysis period, economic factors, operational assumptions,
    vehicle specifications (as nested objects), and cost parameters.
    Automatically calculates annual price series for escalating costs.
    """

    # General
    name: str = Field(default="Default Scenario", description="Unique identifier for the scenario")
    description: Optional[str] = Field(None, description="Optional description")
    analysis_years: int = Field(..., description="Duration of the analysis in years", gt=0)
    start_year: int = Field(2025, description="Starting year for the analysis")

    # Economic
    discount_rate_real: float = Field(..., description="Real annual discount rate (e.g., 0.03 for 3%)", ge=0)
    inflation_rate: Optional[float] = Field(0.025, description="Assumed general inflation rate for converting real to nominal if needed", ge=0)

    # Operational
    annual_mileage: float = Field(..., description="Average annual kilometers driven", gt=0)

    # Vehicles (Nested models)
    electric_vehicle: ElectricVehicle
    diesel_vehicle: DieselVehicle

    # Financing Options
    financing_method: str = Field("loan", description="Method of vehicle acquisition (cash or loan)")
    down_payment_pct: float = Field(0.2, description="Down payment percentage for loan financing", ge=0, le=1.0)
    loan_term: int = Field(5, description="Loan term in years", gt=0)
    interest_rate: float = Field(0.05, description="Annual interest rate for loan", ge=0)

    # Infrastructure (EV Specific) - Now a nested structure
    # charger_cost: float = Field(0.0, description="Upfront charger cost (AUD)", ge=0)
    # charger_installation_cost: float = Field(0.0, description="Upfront charger installation cost (AUD)", ge=0)
    # charger_maintenance_percent: float = Field(0.01, description="Annual charger maintenance as a percentage of upfront cost", ge=0)
    # charger_lifespan: int = Field(10, description="Lifespan of the charger in years", gt=0)
    infrastructure_costs: Dict[str, Union[float, int, Dict[str, float]]] = Field(..., description="Dictionary containing infrastructure costs like charger hardware, installation, maintenance percentage")

    # --- Base Prices / Rates (Year 0) --- (Kept for potential overrides or simple scenarios)
    electricity_price_base: Optional[float] = Field(None, description="Optional: Base electricity price (AUD/kWh) for year 0 if not using projections", ge=0)
    diesel_price_base: Optional[float] = Field(None, description="Optional: Base diesel price (AUD/L) for year 0 if not using projections", ge=0)

    # --- Price Projections / Scenarios --- (Primary source based on updated_data)
    electricity_price_projections: Dict[str, Dict[int, Union[float, List[float]]]] = Field(..., description="Projected electricity prices (AUD/kWh) under different scenarios (e.g., average_flat_rate, off_peak_tou)")
    diesel_price_scenarios: Dict[str, Union[float, Dict[int, float]]] = Field(..., description="Diesel price scenarios (AUD/L) (e.g., baseline_2025, low_stable, medium_increase)")
    selected_electricity_scenario: str = Field(..., description="Name of the electricity price scenario to use from projections")
    selected_diesel_scenario: str = Field(..., description="Name of the diesel price scenario to use")

    # --- Detailed Maintenance Costs --- (Replaces simple per/km)
    maintenance_costs_detailed: Dict[str, Dict[str, Union[float, str]]] = Field(..., description="Detailed maintenance costs (e.g., annual min/max) per vehicle type")

    # --- Insurance and Registration --- (Replaces factors)
    insurance_and_registration: Dict[str, Dict[str, Union[float, int, str]]] = Field(..., description="Insurance and registration costs per vehicle type")

    # --- Carbon Tax --- (Keep base + rate)
    carbon_tax_rate: float = Field(0.0, description="Initial carbon tax rate (AUD/tonne CO2e)", ge=0)
    carbon_tax_increase_rate: float = Field(0.0, description="Annual increase rate for carbon tax", ge=0)

    # --- Road User Charge --- (Keep base + rate)
    road_user_charge: float = Field(0.0, description="Initial road user charge (AUD/km)", ge=0)
    road_user_charge_increase_rate: float = Field(0.0, description="Annual increase rate for road user charge", ge=0)

    # --- Removed deprecated cost fields --- 
    # electric_maintenance_cost_per_km: float = Field(..., description="Base maintenance cost for electric vehicles (AUD/km)", ge=0)
    # diesel_maintenance_cost_per_km: float = Field(..., description="Base maintenance cost for diesel vehicles (AUD/km)", ge=0)
    # insurance_base_rate: float = Field(0.03, description="Base annual insurance rate as a fraction of purchase price", ge=0)
    # electric_insurance_cost_factor: float = Field(1.0, description="Multiplier factor for EV insurance cost relative to base rate", ge=0)
    # diesel_insurance_cost_factor: float = Field(1.0, description="Multiplier factor for Diesel insurance cost relative to base rate", ge=0)
    # annual_registration_cost: float = Field(..., description="Base annual registration cost (AUD)", ge=0)

    # --- Removed price increase rates - now handled by projections/scenarios --- 
    # electricity_price_increase: float = Field(0.0, description="Annual increase rate for electricity price", ge=0)
    # diesel_price_increase: float = Field(0.0, description="Annual increase rate for diesel price", ge=0)

    # --- Keep general cost increase rates for items NOT covered by specific projections --- 
    maintenance_increase_rate: float = Field(0.0, description="Annual increase rate for maintenance costs (applied to detailed costs)", ge=0)
    insurance_increase_rate: float = Field(0.0, description="Annual increase rate for insurance costs", ge=0)
    registration_increase_rate: float = Field(0.0, description="Annual increase rate for registration costs", ge=0)

    # --- Flags / Options ---
    include_carbon_tax: bool = Field(True, description="Include carbon tax in calculations for applicable vehicles")
    include_road_user_charge: bool = Field(True, description="Include road user charge in calculations")
    enable_battery_replacement: bool = Field(True, description="Enable battery replacement logic")

    # Battery Replacement (EV Specific)
    battery_degradation_rate: float = Field(0.02, description="Annual battery capacity degradation rate (used for replacement logic)", ge=0, le=1.0)
    # Threshold at which capacity triggers replacement, if force_battery_replacement_year is not set.
    # Example: 0.7 means replacement happens when capacity drops to 70% or below.
    battery_replacement_threshold: Optional[float] = Field(0.7, description="Capacity threshold (fraction) to trigger battery replacement", ge=0, le=1.0)
    force_battery_replacement_year: Optional[int] = Field(None, description="Force battery replacement in this specific year (1-based index, e.g., 8 for year 8)", ge=1)

    # Battery pack cost projections moved to ElectricVehicle model
    # battery_cost_projections: Optional[Dict[int, float]] = Field(None, description="Optional override for battery cost projections (Year: AUD/kWh)")

    # Internal cache for calculated annual prices. Handled by Pydantic/PrivateAttr.
    _generated_prices: Dict[str, List[float]] = PrivateAttr(default_factory=dict)
    # Optional: Cache for battery costs loaded from external file could be added here if needed Scenario-wide
    # _battery_costs_lookup: Dict[int, float] = PrivateAttr(default_factory=dict)

    # --- Add missing fields previously handled by kwargs or assumed --- 
    # These should match fields expected by components, but might not be directly on Scenario
    # if they are better suited to be on Vehicle. Check component logic.
    # Example (these were previously assumed or passed via kwargs in tests):
    # battery_cost_projections: Optional[Dict[int, float]] = Field(None, description="Optional override for battery cost projections (Year: AUD/kWh)")

    # Use ConfigDict for Pydantic v2 configuration
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )
    
    # Add computed property for end_year
    @property
    def end_year(self) -> int:
        """Calculate the end year from start_year and analysis_years."""
        return self.start_year + self.analysis_years - 1

    @model_validator(mode='after')
    def _calculate_annual_prices(self) -> 'Scenario':
        """Generate annual price series for relevant costs after model initialization.
           Uses selected projections/scenarios for energy, and base+increase for others.
        """
        self._generated_prices = {} # Ensure cache is cleared before recalculation

        # 1. Carbon Tax and Road User Charge (Base + Increase Rate)
        prices_to_generate_simple = {
            'carbon_tax': (self.carbon_tax_rate, self.carbon_tax_increase_rate),
            'road_user_charge': (self.road_user_charge, self.road_user_charge_increase_rate)
        }
        for name, (base_price, increase_rate) in prices_to_generate_simple.items():
            self._generated_prices[name] = [
                base_price * ((1 + increase_rate) ** i) for i in range(self.analysis_years)
            ]

        # 2. Electricity Prices (from selected projection scenario)
        if self.selected_electricity_scenario not in self.electricity_price_projections:
            raise ValueError(f"Selected electricity scenario '{self.selected_electricity_scenario}' not found in projections.")
        elec_proj = self.electricity_price_projections[self.selected_electricity_scenario]
        elec_prices = []
        years_available = sorted(elec_proj.keys())
        for i in range(self.analysis_years):
            current_year = self.start_year + i
            # Find the closest available year <= current_year
            proj_year = max((y for y in years_available if y <= current_year), default=years_available[0])
            price_data = elec_proj[proj_year]
            # Handle range [min, max] vs single value - Use average for now
            if isinstance(price_data, list) and len(price_data) == 2:
                elec_prices.append(sum(price_data) / 2.0)
            elif isinstance(price_data, (int, float)):
                elec_prices.append(float(price_data))
            else:
                 raise ValueError(f"Invalid price data format for year {proj_year} in electricity scenario '{self.selected_electricity_scenario}': {price_data}")
        self._generated_prices['electricity'] = elec_prices

        # 3. Diesel Prices (from selected projection scenario)
        if self.selected_diesel_scenario not in self.diesel_price_scenarios:
            raise ValueError(f"Selected diesel scenario '{self.selected_diesel_scenario}' not found in projections.")
        diesel_proj_data = self.diesel_price_scenarios[self.selected_diesel_scenario]
        diesel_prices = []
        # Handle different structures: could be a single baseline or yearly projections
        if isinstance(diesel_proj_data, dict): # Yearly projections
            diesel_proj = diesel_proj_data
            years_available = sorted(diesel_proj.keys())
            for i in range(self.analysis_years):
                current_year = self.start_year + i
                proj_year = max((y for y in years_available if y <= current_year), default=years_available[0])
                diesel_prices.append(float(diesel_proj[proj_year]))
        elif isinstance(diesel_proj_data, (int, float)): # Single baseline value (e.g., baseline_2025)
             # Assume constant if only one value provided for the scenario name
             # A better approach might be to require yearly structure even for flat scenarios.
             # For now, assume constant.
             base_price = float(diesel_proj_data)
             # Could optionally apply diesel_price_increase if defined, but projections should ideally cover this.
             # Let's stick to the projection value.
             diesel_prices = [base_price] * self.analysis_years
        else:
            raise ValueError(f"Invalid data format for diesel scenario '{self.selected_diesel_scenario}': {diesel_proj_data}")
        self._generated_prices['diesel'] = diesel_prices

        # Note: Other costs like maintenance, insurance, registration are handled directly
        # by components using the detailed dictionaries and applying their increase rates annually.
        # They don't need a pre-generated price list in _generated_prices here.

        logger.debug(f"Generated annual price series for scenario '{self.name}'.")
        return self

    # Method for cost components to access prices easily
    def get_annual_price(self, cost_type: str, year_index: int) -> Optional[float]:
        """Retrieve the calculated price for a specific cost type and year index (0-based).

        Args:
            cost_type: The type of cost (e.g., 'electricity', 'diesel', 'carbon_tax').
            year_index: The 0-based index of the analysis year (0 to analysis_years - 1).

        Returns:
            The calculated price for that year, or None if not found.
        """
        if cost_type in self._generated_prices:
            price_series = self._generated_prices[cost_type]
            if 0 <= year_index < len(price_series):
                return price_series[year_index]
            else:
                logger.warning(f"Year index {year_index} out of bounds for {cost_type} price series (Length: {len(price_series)}). Scenario: '{self.name}'")
        else:
            logger.warning(f"Cost type '{cost_type}' not found in generated price series for scenario '{self.name}'. Available: {list(self._generated_prices.keys())}")
        return None

    # Use field_validator for Pydantic v2
    @field_validator('force_battery_replacement_year')
    @classmethod
    def check_replacement_year_bounds(cls, v: Optional[int], info: ValidationInfo):
        """Ensure forced replacement year is within analysis period."""
        # 'values' is deprecated, use info.data
        if v is not None and 'analysis_years' in info.data and info.data['analysis_years'] is not None:
            if v > info.data['analysis_years']:
                raise ValueError(f"force_battery_replacement_year ({v}) cannot be greater than analysis_years ({info.data['analysis_years']})")
        return v

    @classmethod
    def from_file(cls, filepath: str) -> 'Scenario':
        """Load scenario from a YAML file, handling nested vehicle objects."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Scenario file not found: {filepath}")
        logger.info(f"Loading scenario from: {filepath}")
        with open(filepath, 'r') as f:
            try:
                data = yaml.safe_load(f)
                if data is None:
                    raise ValueError(f"Scenario file is empty or invalid: {filepath}")
            except yaml.YAMLError as e:
                logger.error(f"Error parsing YAML file {filepath}: {e}")
                raise ValueError(f"Error parsing YAML file {filepath}: {e}")

        try:
            # Pydantic v2 automatically handles nested models if the structure matches
            # No need to manually instantiate unless structure is different.
            instance = cls(**data)
            logger.info(f"Successfully loaded and validated scenario: {instance.name}")
            return instance
        except Exception as e:
            # Log the detailed validation error
            logger.error(f"Error validating data from {filepath}: {e}", exc_info=True)
            # Re-raise a more informative error
            raise ValueError(f"Error validating scenario data from {filepath}. Check structure and types. Details: {e}")

    def to_file(self, filepath: str) -> None:
        """Save scenario to a YAML file, handling nested models."""
        logger.info(f"Saving scenario '{self.name}' to: {filepath}")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        # model_dump with mode='json' handles nested Pydantic models correctly for YAML serialization
        data = self.model_dump(mode='json', exclude_none=True) # exclude_none for cleaner output
        try:
            with open(filepath, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Scenario '{self.name}' saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save scenario to {filepath}: {e}", exc_info=True)
            raise # Re-raise the exception after logging

    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario to a dictionary, including nested models."""
        return self.model_dump(mode='json')

    def with_modifications(self, **kwargs) -> 'Scenario':
        """Create a new Scenario instance with updated parameters.

        Handles updates to top-level fields and nested vehicle dictionaries.
        Ensures the new instance is validated and price series are regenerated.

        Args:
            **kwargs: Keyword arguments of parameters to update.

        Returns:
            A new Scenario instance with the modifications applied.

        Raises:
            ValueError: If modifications can't be applied.
        """
        # Use Pydantic's recommended way for creating a modified copy
        try:
            # Create a new instance with updated fields
            new_instance = self.model_copy(update=kwargs)
            
            # Explicitly ensure price series are regenerated if price-related parameters are changed
            # This is needed because while model_copy runs model_validator for basic validation,
            # it might not fully regenerate all derived values like price series with the new parameters
            price_related_params = {
                'selected_electricity_scenario', 'selected_diesel_scenario',
                'carbon_tax_rate', 'carbon_tax_increase_rate',
                'road_user_charge', 'road_user_charge_increase_rate'
            }
            
            # If any price-related parameter was modified, explicitly recalculate prices
            # This ensures that the price series in _generated_prices are consistent with the new parameters
            if any(param in kwargs for param in price_related_params):
                new_instance._calculate_annual_prices()
                
            logger.debug(f"Created modified scenario based on '{self.name}'. Updates: {kwargs}")
            return new_instance
        except Exception as e:
             logger.error(f"Error creating modified scenario: {e}. Updates provided: {kwargs}", exc_info=True)
             raise ValueError(f"Failed to apply modifications: {e}")


# Example Usage (Optional - for testing or demonstration)
if __name__ == '__main__':
    # Define some vehicle instances (assuming ElectricVehicle/DieselVehicle classes are defined)
    ev = ElectricVehicle(
        name="Sample EV", purchase_price=50000, residual_value_percent=0.4, energy_consumption=0.2,
        maintenance_cost_per_km=0.05, insurance_cost_percent=0.03, registration_cost=300,
        battery_capacity_kwh=60, battery_replacement_cost_per_kwh=120, battery_cycle_life=1800,
        battery_depth_of_discharge=0.8, charging_efficiency=0.9
    )
    dv = DieselVehicle(
        name="Sample Diesel", purchase_price=40000, residual_value_percent=0.3, energy_consumption=0.08,
        maintenance_cost_per_km=0.07, insurance_cost_percent=0.035, registration_cost=500,
        co2_emission_factor=2.68
    )

    # Create a scenario instance
    try:
        scenario_data = {
            "name": "Test Scenario",
            "analysis_years": 10,
            "discount_rate_real": 0.05,
            "annual_mileage": 20000,
            "electric_vehicle": ev.model_dump(), # Pass as dict for Pydantic init
            "diesel_vehicle": dv.model_dump(),
            "infrastructure_cost": 3000,
            "electricity_price_base": 0.22,
            "diesel_price_base": 1.80,
            "carbon_tax_rate": 25,
            "road_user_charge": 0.03,
            "selected_electricity_scenario": "average_flat_rate",
            "selected_diesel_scenario": "baseline_2025",
            "maintenance_increase_rate": 0.01,
            "insurance_increase_rate": 0.01,
            "registration_increase_rate": 0.01,
        }
        test_scenario = Scenario(**scenario_data)

        print("Scenario created successfully:", test_scenario.name)
        print("EV Price Year 0:", test_scenario.get_annual_price('electricity', 0))
        print("EV Price Year 5:", test_scenario.get_annual_price('electricity', 5))
        print("Diesel Price Year 9:", test_scenario.get_annual_price('diesel', 9))
        print("Carbon Tax Year 2:", test_scenario.get_annual_price('carbon_tax', 2))

        # Test modification
        modified_scenario = test_scenario.with_modifications(annual_mileage=25000, electricity_price_base=0.25)
        print("\nModified Scenario:")
        print("New Mileage:", modified_scenario.annual_mileage)
        print("New EV Price Year 0:", modified_scenario.get_annual_price('electricity', 0))

        # Test file operations (create a dummy directory)
        test_dir = "_test_scenario_output"
        os.makedirs(test_dir, exist_ok=True)
        file_path = os.path.join(test_dir, "test_scenario.yaml")
        modified_scenario.to_file(file_path)
        print(f"\nSaved modified scenario to {file_path}")

        loaded_scenario = Scenario.from_file(file_path)
        print(f"Loaded scenario '{loaded_scenario.name}' successfully from file.")
        print("Loaded Mileage:", loaded_scenario.annual_mileage)
        print("Loaded EV Name:", loaded_scenario.electric_vehicle.name)

        # Clean up dummy file/dir
        # import shutil
        # shutil.rmtree(test_dir)
        # print("Cleaned up test directory.")

    except Exception as e:
        print(f"\nError during example usage: {e}")
        import traceback
        traceback.print_exc()
