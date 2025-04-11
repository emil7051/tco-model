import pytest
import os
import yaml
from pydantic import ValidationError

from tco_model.scenarios import Scenario

# Define a baseline valid scenario dictionary for testing
BASE_SCENARIO_DATA = {
    "name": "Test Scenario",
    "description": "A scenario for testing purposes",
    "start_year": 2025,
    "end_year": 2030,
    "discount_rate": 0.05,
    "inflation_rate": 0.02,
    "financing_method": "cash",
    "loan_term": 5, # Included even if financing is cash, should be ignored
    "interest_rate": 0.06,
    "down_payment_pct": 0.2,
    "annual_mileage": 50000,
    "electric_vehicle_name": "Test EV",
    "electric_vehicle_price": 350000,
    "electric_vehicle_battery_capacity": 250,
    "electric_vehicle_energy_consumption": 0.8,
    "electric_vehicle_battery_warranty": 8,
    "diesel_vehicle_name": "Test Diesel",
    "diesel_vehicle_price": 180000,
    "diesel_vehicle_fuel_consumption": 28,
    # Add other required fields with sensible defaults
    "electricity_prices": {str(y): 0.22 for y in range(2025, 2031)},
    "diesel_prices": {str(y): 1.80 for y in range(2025, 2031)},
    "charger_cost": 40000,
    "charger_installation_cost": 45000,
    "charger_lifespan": 10,
    "electric_maintenance_cost_per_km": 0.07,
    "diesel_maintenance_cost_per_km": 0.14,
    "electric_insurance_cost_factor": 1.0,
    "diesel_insurance_cost_factor": 1.0,
    "annual_registration_cost": 4500,
    "enable_battery_replacement": False,
    "battery_replacement_year": None,
    "battery_replacement_threshold": 0.7,
    "electric_residual_value_pct": 0.15,
    "diesel_residual_value_pct": 0.12
}

@pytest.fixture
def valid_scenario_data():
    """Provides a deep copy of the base valid scenario data."""
    import copy
    return copy.deepcopy(BASE_SCENARIO_DATA)

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
        assert scenario.start_year == valid_scenario_data["start_year"]
        assert scenario.end_year == valid_scenario_data["end_year"]
        assert scenario.electric_vehicle_price == valid_scenario_data["electric_vehicle_price"]
        # Check a few other fields
        assert scenario.financing_method == "cash"
        assert scenario.annual_mileage == 50000
        assert scenario.electricity_prices == valid_scenario_data["electricity_prices"]
    except ValidationError as e:
        pytest.fail(f"Scenario creation failed with valid data: {e}")

def test_scenario_validation_end_year(valid_scenario_data):
    """Test validation fails if end_year is not after start_year."""
    invalid_data = valid_scenario_data.copy()
    invalid_data["end_year"] = invalid_data["start_year"] # End year same as start year
    with pytest.raises(ValidationError) as excinfo:
        Scenario(**invalid_data)
    assert "end_year must be after start_year" in str(excinfo.value)

    invalid_data["end_year"] = invalid_data["start_year"] - 1 # End year before start year
    with pytest.raises(ValidationError) as excinfo:
        Scenario(**invalid_data)
    assert "end_year must be after start_year" in str(excinfo.value)

def test_scenario_validation_negative_price(valid_scenario_data):
    """Test validation fails if vehicle prices are not positive."""
    invalid_data = valid_scenario_data.copy()
    invalid_data["electric_vehicle_price"] = -1000
    with pytest.raises(ValidationError) as excinfo:
        Scenario(**invalid_data)
    # Check for Pydantic v2 style error message for greater_than (gt)
    assert "Input should be greater than 0" in str(excinfo.value)
    # assert "electric_vehicle_price" in str(excinfo.value) # Check field name is mentioned
    
    invalid_data = valid_scenario_data.copy() # Reset
    invalid_data["diesel_vehicle_price"] = 0
    with pytest.raises(ValidationError) as excinfo:
        Scenario(**invalid_data)
    assert "Input should be greater than 0" in str(excinfo.value)
    # assert "diesel_vehicle_price" in str(excinfo.value)

def test_scenario_validation_missing_required(valid_scenario_data):
    """Test validation fails if a required field is missing."""
    invalid_data = valid_scenario_data.copy()
    del invalid_data["electric_vehicle_name"] # Remove a required field
    with pytest.raises(ValidationError) as excinfo:
        Scenario(**invalid_data)
    # Check for Pydantic v2 style error message for missing field
    assert "Field required" in str(excinfo.value)
    assert "'electric_vehicle_name'" in str(excinfo.value) # Check field name is mentioned

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
    
    # Check a few specific fields just in case
    assert loaded_scenario.name == valid_scenario_data["name"]
    assert loaded_scenario.electricity_prices == valid_scenario_data["electricity_prices"]

def test_scenario_from_file_not_found(tmp_path):
    """Test loading from a non-existent file raises FileNotFoundError."""
    non_existent_file = tmp_path / "non_existent.yaml"
    with pytest.raises(FileNotFoundError):
        Scenario.from_file(non_existent_file)

def test_scenario_from_file_invalid_yaml(temp_yaml_file):
    """Test loading from an invalid YAML file raises ValueError."""
    # Create an invalid YAML file
    with open(temp_yaml_file, 'w') as f:
        f.write("name: Test Scenario\nstart_year: 2025\n  bad_indent: true") # Invalid indentation
        
    with pytest.raises(ValueError) as excinfo:
        Scenario.from_file(temp_yaml_file)
    assert "Error parsing YAML file" in str(excinfo.value)

def test_scenario_from_file_validation_error(temp_yaml_file, valid_scenario_data):
    """Test loading from YAML with data failing validation raises ValueError."""
    invalid_data = valid_scenario_data.copy()
    invalid_data["end_year"] = invalid_data["start_year"] - 1 # Invalid data

    # Save invalid data to YAML
    with open(temp_yaml_file, 'w') as f:
        yaml.dump(invalid_data, f)

    with pytest.raises(ValueError) as excinfo:
        Scenario.from_file(temp_yaml_file)
    assert "Error validating data from" in str(excinfo.value)
    # The underlying Pydantic error should be part of the message
    assert "end_year must be after start_year" in str(excinfo.value)

def test_scenario_to_dict(valid_scenario_data):
    """Test converting a Scenario instance to a dictionary."""
    scenario = Scenario(**valid_scenario_data)
    scenario_dict = scenario.to_dict()
    
    # Compare the dictionary with the original input data
    # Note: Pydantic might add defaults or transform data, so compare keys from original
    for key, value in valid_scenario_data.items():
        assert key in scenario_dict
        # Special handling for nested dicts like prices if necessary
        if isinstance(value, dict):
            assert scenario_dict[key] == value
        else:
            # Floating point comparisons might need tolerance, but should be exact here
            assert scenario_dict[key] == value
    
    # Also check that the output is indeed a dict
    assert isinstance(scenario_dict, dict)

def test_scenario_price_validation_complete(valid_scenario_data):
    """Test price validation when all years are present."""
    data = valid_scenario_data.copy()
    start = data['start_year']
    end = data['end_year']
    # Ensure the fixture data already covers all years
    assert all(str(y) in data['electricity_prices'] for y in range(start, end + 1))
    assert all(str(y) in data['diesel_prices'] for y in range(start, end + 1))
    
    scenario = Scenario(**data)
    # Check that the prices were not modified (i.e., no defaults added)
    assert scenario.electricity_prices == data['electricity_prices']
    assert scenario.diesel_prices == data['diesel_prices']

def test_scenario_price_validation_partial(valid_scenario_data):
    """Test price validation fills in missing years with defaults."""
    data = valid_scenario_data.copy()
    start = data['start_year']
    end = data['end_year']
    
    # Remove some years from the price data
    if str(start + 1) in data['electricity_prices']: del data['electricity_prices'][str(start + 1)]
    if str(end -1) in data['diesel_prices']: del data['diesel_prices'][str(end - 1)]
    
    scenario = Scenario(**data)
    
    # Check that the missing years were filled with defaults
    # Default electricity: 0.20, Default diesel: 1.70 (as per Scenario model)
    assert scenario.electricity_prices[str(start + 1)] == 0.20
    assert scenario.diesel_prices[str(end - 1)] == 1.70
    
    # Check that existing years were preserved
    assert scenario.electricity_prices[str(start)] == valid_scenario_data['electricity_prices'][str(start)]
    assert scenario.diesel_prices[str(end)] == valid_scenario_data['diesel_prices'][str(end)]
    
    # Check that all years are now present
    assert all(str(y) in scenario.electricity_prices for y in range(start, end + 1))
    assert all(str(y) in scenario.diesel_prices for y in range(start, end + 1))

def test_scenario_price_validation_empty(valid_scenario_data):
    """Test price validation populates fully empty price dicts with defaults."""
    data = valid_scenario_data.copy()
    start = data['start_year']
    end = data['end_year']
    
    # Set price dicts to empty
    data['electricity_prices'] = {}
    data['diesel_prices'] = {}
    
    scenario = Scenario(**data)
    
    # Check that all years were filled with defaults
    assert all(scenario.electricity_prices[str(y)] == 0.20 for y in range(start, end + 1))
    assert all(scenario.diesel_prices[str(y)] == 1.70 for y in range(start, end + 1))
    assert len(scenario.electricity_prices) == (end - start + 1)
    assert len(scenario.diesel_prices) == (end - start + 1)

def test_scenario_with_modifications(valid_scenario_data):
    """Test the with_modifications method."""
    scenario1 = Scenario(**valid_scenario_data)
    
    # Define modifications
    modifications = {
        "name": "Modified Scenario Name",
        "annual_mileage": 60000,
        "discount_rate": 0.08
    }
    
    # Create modified scenario
    scenario2 = scenario1.with_modifications(**modifications)
    
    # Check that the new scenario has the modified values
    assert scenario2.name == "Modified Scenario Name"
    assert scenario2.annual_mileage == 60000
    assert scenario2.discount_rate == 0.08
    
    # Check that the original scenario remains unchanged
    assert scenario1.name == valid_scenario_data["name"]
    assert scenario1.annual_mileage == valid_scenario_data["annual_mileage"]
    assert scenario1.discount_rate == valid_scenario_data["discount_rate"]
    
    # Check that other fields were copied correctly
    assert scenario1.start_year == scenario2.start_year
    assert scenario1.electric_vehicle_price == scenario2.electric_vehicle_price
    
    # Ensure it returns a new instance, not the same object
    assert id(scenario1) != id(scenario2)

# --- Test Cases Start Here --- 