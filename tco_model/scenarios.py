from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator, model_validator, PrivateAttr
import yaml
import os
import logging
from datetime import datetime

# Import vehicle classes
from .vehicles import ElectricVehicle, DieselVehicle

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

    # Economic
    discount_rate_real: float = Field(..., description="Real annual discount rate (e.g., 0.03 for 3%)", ge=0)

    # Operational
    annual_mileage: float = Field(..., description="Average annual kilometers driven", gt=0)

    # Vehicles (Nested models)
    electric_vehicle: ElectricVehicle
    diesel_vehicle: DieselVehicle

    # Infrastructure (EV Specific)
    infrastructure_cost: float = Field(0.0, description="Upfront infrastructure cost (e.g., charger, installation) (AUD)", ge=0)
    infrastructure_maintenance_percent: float = Field(0.01, description="Annual infrastructure maintenance as a percentage of upfront cost", ge=0)

    # --- Base Prices / Rates (Year 0) ---
    electricity_price: float = Field(..., description="Initial electricity price (AUD/kWh)", ge=0)
    diesel_price: float = Field(..., description="Initial diesel price (AUD/L)", ge=0)
    carbon_tax_rate: float = Field(0.0, description="Initial carbon tax rate (AUD/tonne CO2e)", ge=0)
    road_user_charge: float = Field(0.0, description="Initial road user charge (AUD/km)", ge=0)

    # --- Annual Increase Rates --- (e.g., 0.02 for 2% increase)
    electricity_price_increase: float = Field(0.0, description="Annual increase rate for electricity price", ge=0)
    diesel_price_increase: float = Field(0.0, description="Annual increase rate for diesel price", ge=0)
    carbon_tax_increase_rate: float = Field(0.0, description="Annual increase rate for carbon tax", ge=0)
    road_user_charge_increase_rate: float = Field(0.0, description="Annual increase rate for road user charge", ge=0)
    maintenance_increase_rate: float = Field(0.0, description="Annual increase rate for maintenance costs (applied to vehicle's base rate)", ge=0)
    insurance_increase_rate: float = Field(0.0, description="Annual increase rate for insurance costs (applied to vehicle's base rate)", ge=0)
    registration_increase_rate: float = Field(0.0, description="Annual increase rate for registration costs (applied to vehicle's base rate)", ge=0)

    # --- Flags / Options ---
    include_carbon_tax: bool = Field(True, description="Include carbon tax in calculations for applicable vehicles")
    include_road_user_charge: bool = Field(True, description="Include road user charge in calculations")

    # Battery Replacement (EV Specific)
    battery_degradation_rate: float = Field(0.02, description="Annual battery capacity degradation rate (used for replacement logic)", ge=0, le=1.0)
    # Threshold at which capacity triggers replacement, if force_battery_replacement_year is not set.
    # Example: 0.7 means replacement happens when capacity drops to 70% or below.
    battery_replacement_threshold: Optional[float] = Field(0.7, description="Capacity threshold (fraction) to trigger battery replacement", ge=0, le=1.0)
    force_battery_replacement_year: Optional[int] = Field(None, description="Force battery replacement in this specific year (1-based index, e.g., 8 for year 8)", ge=1)

    # Internal cache for calculated annual prices. Handled by Pydantic/PrivateAttr.
    _generated_prices: Dict[str, List[float]] = PrivateAttr(default_factory=dict)
    # Optional: Cache for battery costs loaded from external file could be added here if needed Scenario-wide
    # _battery_costs_lookup: Dict[int, float] = PrivateAttr(default_factory=dict)

    @model_validator(mode='after')
    def _calculate_annual_prices(self) -> 'Scenario':
        """Generate annual price series for relevant costs after model initialization."""
        prices_to_generate = {
            'electricity': (self.electricity_price, self.electricity_price_increase),
            'diesel': (self.diesel_price, self.diesel_price_increase),
            'carbon_tax': (self.carbon_tax_rate, self.carbon_tax_increase_rate),
            'road_user_charge': (self.road_user_charge, self.road_user_charge_increase_rate)
        }
        self._generated_prices = {}
        for name, (base_price, increase_rate) in prices_to_generate.items():
            self._generated_prices[name] = [
                base_price * ((1 + increase_rate) ** i) for i in range(self.analysis_years)
            ]
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

    @validator('force_battery_replacement_year')
    def check_replacement_year_bounds(cls, v, values):
        """Ensure forced replacement year is within analysis period."""
        if v is not None and 'analysis_years' in values:
            if v > values['analysis_years']:
                raise ValueError(f"force_battery_replacement_year ({v}) cannot be greater than analysis_years ({values['analysis_years']})")
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
        """

        # Use Pydantic's recommended way for creating a modified copy
        # This automatically handles validation and runs model_validator again.
        try:
            # model_copy generates a new instance with updated fields
            new_instance = self.model_copy(update=kwargs)
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
            "electricity_price": 0.22,
            "diesel_price": 1.80,
            "carbon_tax_rate": 25,
            "road_user_charge": 0.03,
            "electricity_price_increase": 0.02,
            "diesel_price_increase": 0.01,
            "carbon_tax_increase_rate": 0.03,
            "road_user_charge_increase_rate": 0.01,
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
        modified_scenario = test_scenario.with_modifications(annual_mileage=25000, electricity_price=0.25)
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
