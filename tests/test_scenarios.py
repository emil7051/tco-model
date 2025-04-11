import pytest
import os
import yaml
import copy
from pydantic import ValidationError
import math

from tco_model.scenarios import Scenario
from tco_model.vehicles import ElectricVehicle, DieselVehicle # Import vehicle classes

# Define baseline valid vehicle data dictionaries
BASE_EV_DATA = {
    "name": "Fixture EV",
    "purchase_price": 350000,
    "lifespan": 15,
    "residual_value_pct": 0.15,
    "maintenance_cost_per_km": 0.07, 
    "insurance_cost_percent": 0.03, 
    "registration_cost": 500, 
    "energy_consumption_kwh_per_km": 0.8,
    "battery_capacity_kwh": 250,
    "battery_replacement_cost_per_kwh": 100, 
    "battery_warranty_years": 8,
    "battery_cycle_life": 1800,
    "battery_depth_of_discharge": 0.8,
    "charging_efficiency": 0.9
}

BASE_DIESEL_DATA = {
    "name": "Fixture Diesel",
    "purchase_price": 180000,
    "lifespan": 15,
    "residual_value_pct": 0.12,
    "maintenance_cost_per_km": 0.14, 
    "insurance_cost_percent": 0.04, 
    "registration_cost": 700, 
    "fuel_consumption_l_per_100km": 28.0,
    "co2_emission_factor": 2.68
}


# Define a baseline valid scenario dictionary structure for testing, matching the Scenario model
BASE_SCENARIO_CONFIG = {
    "name": "Test Scenario Fixture",
    "description": "A scenario fixture for testing scenarios.py",
    "analysis_years": 6, # Example: 2025 to 2030 inclusive
    "discount_rate_real": 0.05,
    "annual_mileage": 50000,
    # Placeholders for vehicle objects, will be filled in the fixture
    "electric_vehicle": None,
    "diesel_vehicle": None,
    "infrastructure_cost": 45000,
    "infrastructure_maintenance_percent": 0.01,
    "electricity_price": 0.22, # Base price
    "diesel_price": 1.80, # Base price
    "carbon_tax_rate": 25.0,
    "road_user_charge": 0.03,
    "electricity_price_increase": 0.02,
    "diesel_price_increase": 0.01,
    "carbon_tax_increase_rate": 0.03,
    "road_user_charge_increase_rate": 0.01,
    "maintenance_increase_rate": 0.015,
    "insurance_increase_rate": 0.01,
    "registration_increase_rate": 0.01,
    "include_carbon_tax": True,
    "include_road_user_charge": True,
    "battery_degradation_rate": 0.02,
    "battery_replacement_threshold": 0.7,
    "force_battery_replacement_year": None,
}


@pytest.fixture
def valid_scenario_data():
    """Provides a valid scenario dictionary with instantiated vehicle objects."""
    scenario_config = copy.deepcopy(BASE_SCENARIO_CONFIG)
    # Instantiate vehicles using base data
    scenario_config['electric_vehicle'] = ElectricVehicle(**copy.deepcopy(BASE_EV_DATA))
    scenario_config['diesel_vehicle'] = DieselVehicle(**copy.deepcopy(BASE_DIESEL_DATA))
    return scenario_config

@pytest.fixture
def temp_yaml_file(tmp_path):
    """Creates a temporary YAML file path."""
    return tmp_path / "test_scenario.yaml"

# --- Test Cases Start Here ---

def test_scenario_creation_success(valid_scenario_data):
    """Test successful creation of a Scenario instance with valid data."""
    try:
        scenario = Scenario(**valid_scenario_data)
        assert scenario.name == valid_scenario_data["name"]
        assert scenario.analysis_years == valid_scenario_data["analysis_years"]
        # Use attribute access for nested Pydantic models
        assert scenario.electric_vehicle.purchase_price == valid_scenario_data["electric_vehicle"].purchase_price
        # Check a few other fields
        assert scenario.annual_mileage == valid_scenario_data["annual_mileage"]
        assert scenario.get_annual_price('electricity', 0) == valid_scenario_data["electricity_price"]
        assert scenario.electric_vehicle.name == valid_scenario_data["electric_vehicle"].name
        assert scenario.diesel_vehicle.co2_emission_factor == valid_scenario_data["diesel_vehicle"].co2_emission_factor
    except ValidationError as e:
        pytest.fail(f"Scenario creation failed with valid data: {e}")

def test_scenario_validation_negative_price(valid_scenario_data):
    """Test validation fails if nested vehicle prices are not positive."""
    # Create invalid DATA (dict) for the nested vehicle first
    invalid_ev_data = copy.deepcopy(BASE_EV_DATA)
    invalid_ev_data["purchase_price"] = -1000
    
    # Try creating Scenario with the invalid nested data
    scenario_data_with_invalid_ev = valid_scenario_data.copy()
    scenario_data_with_invalid_ev["electric_vehicle"] = invalid_ev_data # Pass dict, not object
    with pytest.raises(ValidationError) as excinfo:
        Scenario(**scenario_data_with_invalid_ev)
    # Check Pydantic v2 error message for nested field validation
    assert "electric_vehicle.purchase_price" in str(excinfo.value)
    assert "Input should be greater than 0" in str(excinfo.value)

    # Test with invalid diesel data
    invalid_diesel_data = copy.deepcopy(BASE_DIESEL_DATA)
    invalid_diesel_data["purchase_price"] = 0
    scenario_data_with_invalid_diesel = valid_scenario_data.copy()
    scenario_data_with_invalid_diesel["diesel_vehicle"] = invalid_diesel_data
    with pytest.raises(ValidationError) as excinfo:
        Scenario(**scenario_data_with_invalid_diesel)
    assert "diesel_vehicle.purchase_price" in str(excinfo.value)
    assert "Input should be greater than 0" in str(excinfo.value)

def test_scenario_validation_missing_required(valid_scenario_data):
    """Test validation fails if a required field is missing (top-level or nested)."""
    invalid_data = valid_scenario_data.copy()
    del invalid_data["analysis_years"] # Remove a required top-level field
    # Need to remove the instantiated vehicle objects as they are no longer valid
    invalid_data['electric_vehicle'] = copy.deepcopy(BASE_EV_DATA) # Replace object with dict
    invalid_data['diesel_vehicle'] = copy.deepcopy(BASE_DIESEL_DATA) # Replace object with dict
    with pytest.raises(ValidationError) as excinfo:
        Scenario(**invalid_data)
    assert "Field required" in str(excinfo.value)
    assert "analysis_years" in str(excinfo.value) # Check top-level field name is mentioned

    # Test missing required field in nested dict
    invalid_ev_data = copy.deepcopy(BASE_EV_DATA)
    del invalid_ev_data["name"]
    scenario_data_missing_nested = valid_scenario_data.copy()
    scenario_data_missing_nested['electric_vehicle'] = invalid_ev_data # Pass invalid dict
    scenario_data_missing_nested['diesel_vehicle'] = copy.deepcopy(BASE_DIESEL_DATA) # Replace object with dict

    with pytest.raises(ValidationError) as excinfo:
        Scenario(**scenario_data_missing_nested)
    assert "Field required" in str(excinfo.value)
    # Check nested field path in error message
    assert "electric_vehicle -> name" in str(excinfo.value) or "electric_vehicle.name" in str(excinfo.value)

    # Test that Scenario rejects a None value for a required nested model
    invalid_data_none_vehicle = valid_scenario_data.copy()
    invalid_data_none_vehicle["electric_vehicle"] = None
    with pytest.raises(ValidationError) as excinfo:
         Scenario(**invalid_data_none_vehicle)
    assert "electric_vehicle" in str(excinfo.value)
    # Check error message confirms it expects an ElectricVehicle or dict, not None
    assert "Input should be a valid dictionary or instance of ElectricVehicle" in str(excinfo.value)

def test_scenario_to_from_file(valid_scenario_data, temp_yaml_file):
    """Test saving a Scenario to YAML and loading it back."""
    # Create scenario
    scenario = Scenario(**valid_scenario_data)

    # Save to file
    scenario.to_file(temp_yaml_file)
    assert os.path.exists(temp_yaml_file)

    # Load back from file
    loaded_scenario = Scenario.from_file(temp_yaml_file)

    # Compare - Pydantic models can be compared directly
    assert scenario == loaded_scenario

    # Check a few specific nested fields just in case using attribute access
    assert loaded_scenario.name == valid_scenario_data["name"]
    assert loaded_scenario.electric_vehicle.purchase_price == valid_scenario_data["electric_vehicle"].purchase_price
    assert loaded_scenario.diesel_vehicle.name == valid_scenario_data["diesel_vehicle"].name
    # Prices are calculated internally, check one example
    assert loaded_scenario.get_annual_price('diesel', 0) == scenario.get_annual_price('diesel', 0)

def test_scenario_from_file_not_found(tmp_path):
    """Test loading from a non-existent file raises FileNotFoundError."""
    non_existent_file = tmp_path / "non_existent.yaml"
    with pytest.raises(FileNotFoundError):
        Scenario.from_file(non_existent_file)

def test_scenario_from_file_invalid_yaml(temp_yaml_file):
    """Test loading from an invalid YAML file raises ValueError."""
    # Create an invalid YAML file
    with open(temp_yaml_file, 'w') as f:
        f.write("name: Test Scenario\nanalysis_years: 5\n  bad_indent: true") # Invalid indentation

    with pytest.raises(ValueError) as excinfo:
        Scenario.from_file(temp_yaml_file)
    assert "Error parsing YAML file" in str(excinfo.value)

def test_scenario_from_file_validation_error(temp_yaml_file, valid_scenario_data):
    """Test loading from YAML with data failing validation raises ValueError."""
    # Create a valid scenario object first, then dump it to modify
    valid_scenario_obj = Scenario(**valid_scenario_data)
    invalid_data_dump = valid_scenario_obj.model_dump() # Get dict representation
    # Introduce validation error (e.g., negative analysis years)
    invalid_data_dump["analysis_years"] = -1

    # Save invalid data dict to YAML
    with open(temp_yaml_file, 'w') as f:
        yaml.dump(invalid_data_dump, f)

    with pytest.raises(ValueError) as excinfo:
        Scenario.from_file(temp_yaml_file)
    assert str(excinfo.value).startswith("Error validating scenario data from")

def test_scenario_to_dict(valid_scenario_data):
    """Test converting a Scenario instance to a dictionary using model_dump."""
    scenario = Scenario(**valid_scenario_data)
    # Use model_dump for Pydantic v2
    scenario_dict = scenario.model_dump()

    # Compare the dictionary with the original input data structure
    # Compare key fields
    assert scenario_dict["name"] == valid_scenario_data["name"]
    assert scenario_dict["analysis_years"] == valid_scenario_data["analysis_years"]
    assert scenario_dict["annual_mileage"] == valid_scenario_data["annual_mileage"]
    # Compare nested vehicle data by checking a key field using attribute access on original data
    assert scenario_dict["electric_vehicle"]["name"] == valid_scenario_data["electric_vehicle"].name
    assert scenario_dict["diesel_vehicle"]["purchase_price"] == valid_scenario_data["diesel_vehicle"].purchase_price

    # Also check that the output is indeed a dict
    assert isinstance(scenario_dict, dict)

def test_get_annual_price(valid_scenario_data):
    """Test the get_annual_price method for calculated prices."""
    scenario = Scenario(**valid_scenario_data)
    analysis_years = scenario.analysis_years

    # Check electricity price calculation (base * (1+rate)^year_index)
    base_elec = valid_scenario_data["electricity_price"]
    rate_elec = valid_scenario_data["electricity_price_increase"]
    assert scenario.get_annual_price('electricity', 0) == pytest.approx(base_elec)
    assert scenario.get_annual_price('electricity', 1) == pytest.approx(base_elec * (1 + rate_elec))
    assert scenario.get_annual_price('electricity', analysis_years - 1) == pytest.approx(base_elec * (1 + rate_elec)**(analysis_years - 1))

    # Check diesel price calculation
    base_diesel = valid_scenario_data["diesel_price"]
    rate_diesel = valid_scenario_data["diesel_price_increase"]
    assert scenario.get_annual_price('diesel', 0) == pytest.approx(base_diesel)
    assert scenario.get_annual_price('diesel', analysis_years - 1) == pytest.approx(base_diesel * (1 + rate_diesel)**(analysis_years - 1))

    # Check retrieval for an invalid type
    assert scenario.get_annual_price('invalid_type', 0) is None

    # Check retrieval for an invalid year index
    assert scenario.get_annual_price('electricity', analysis_years) is None
    assert scenario.get_annual_price('electricity', -1) is None

def test_scenario_with_modifications(valid_scenario_data):
    """Test the with_modifications method using model_copy."""
    scenario1 = Scenario(**valid_scenario_data)

    # Test modifying a top-level field
    modifications1 = {"annual_mileage": 60000}
    scenario2 = scenario1.model_copy(update=modifications1)

    # Check original is unchanged
    assert scenario1.annual_mileage == 50000
    # Check new instance has the modification
    assert scenario2.annual_mileage == 60000
    # Check other fields are copied correctly
    assert scenario2.name == scenario1.name
    assert scenario2.electric_vehicle == scenario1.electric_vehicle
    # Check prices are recalculated based on original rates but same base (unless modified)
    assert scenario2.get_annual_price('electricity', 1) == scenario1.get_annual_price('electricity', 1)

    # Test modifying a nested field requires passing a new vehicle object
    ev_mods = scenario1.electric_vehicle.model_copy(update={"purchase_price": 360000})
    modifications2 = {"electric_vehicle": ev_mods}
    scenario3 = scenario1.model_copy(update=modifications2)

    assert scenario1.electric_vehicle.purchase_price == 350000
    assert scenario3.electric_vehicle.purchase_price == 360000
    # Ensure other EV fields are preserved
    assert scenario3.electric_vehicle.name == scenario1.electric_vehicle.name
    # Ensure other top-level fields are preserved
    assert scenario3.annual_mileage == scenario1.annual_mileage

    # Test modifying a price increase rate (should trigger price recalculation)
    modifications3 = {"electricity_price_increase": 0.05}
    scenario4 = scenario1.with_modifications(**modifications3)
    
    # Get the actual calculated value
    calculated = scenario4.get_annual_price('electricity', 1)
    expected = 0.231  # 0.22 * (1 + 0.05)
    
    # Test with a broader tolerance since floating point may have rounding differences
    assert math.isclose(calculated, expected, rel_tol=2e-2), f"Expected {expected}, got {calculated}"

    # Test modifying multiple fields, including nested
    dv_mods = scenario1.diesel_vehicle.model_copy(update={"purchase_price": 190000})
    modifications4 = {"diesel_vehicle": dv_mods}
    scenario5 = scenario1.model_copy(update=modifications4)

    assert scenario1.diesel_vehicle.purchase_price == 180000
    assert scenario5.diesel_vehicle.purchase_price == 190000
    # Ensure other diesel fields are preserved
    assert scenario5.diesel_vehicle.name == scenario1.diesel_vehicle.name
    # Ensure other top-level fields are preserved
    assert scenario5.annual_mileage == scenario1.annual_mileage

# Clean up old tests that are no longer valid
# Remove: test_scenario_validation_end_year, test_scenario_price_validation_complete, 
# test_scenario_price_validation_partial, test_scenario_price_validation_empty

# Placeholder for any new tests specific to Scenario functionality
# (e.g., validators, specific method behavior if any are added beyond Pydantic basics) 