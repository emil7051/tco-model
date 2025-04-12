import pytest
import os
import yaml
import copy
from pydantic import ValidationError
import math

# Import specific models needed for scenario definition
from tco_model.scenarios import (
    Scenario,
    EconomicParameters,
    OperationalParameters,
    FinancingOptions,
    InfrastructureCosts,
    ElectricityPriceProjections, ElectricityPricePoint,
    DieselPriceProjections, DieselPriceScenarioData,
    MaintenanceCosts, MaintenanceDetail,
    InsuranceRegistrationCosts, InsuranceRegistrationDetail,
    CarbonTaxConfig,
    RoadUserChargeConfig,
    GeneralCostIncreaseRates,
    BatteryReplacementConfig
)
from tco_model.vehicles import ElectricVehicle, DieselVehicle

# Updated baseline valid vehicle data dictionaries
BASE_EV_DATA = {
    "name": "Fixture EV",
    "vehicle_type": "rigid_bet", # Use specific type
    "base_purchase_price_aud": 80000, # Renamed
    "lifespan_years": 15, # Renamed
    "residual_value_percent_projections": {5: 40.0, 10: 20.0, 15: 10.0}, # Renamed, Scaled
    "base_registration_cost_aud": 450, # Renamed
    "energy_consumption_kwh_per_km": 0.22,
    "battery_capacity_kwh": 65.0,
    "battery_pack_cost_aud_per_kwh_projections": {2025: 170, 2030: 100, 2035: 75}, # Renamed
    "battery_warranty_years": 8,
    "battery_cycle_life": 1500,
    "battery_depth_of_discharge_percent": 80.0, # Renamed, Scaled
    "charging_efficiency_percent": 90.0, # Renamed, Scaled
    "purchase_price_annual_decrease_rate_real": 0.01 # Renamed
}

BASE_DIESEL_DATA = {
    "name": "Fixture Diesel",
    "vehicle_type": "rigid_diesel", # Use specific type
    "base_purchase_price_aud": 70000, # Renamed
    "lifespan_years": 12, # Renamed
    "residual_value_percent_projections": {5: 50.0, 10: 30.0, 12: 15.0}, # Renamed, Scaled
    "base_registration_cost_aud": 550, # Renamed
    "fuel_consumption_l_per_100km": 9.0,
    "co2_emission_factor_kg_per_l": 2.68 # Renamed
}


# Updated baseline valid scenario dictionary structure
BASE_SCENARIO_CONFIG = {
    "name": "Test Scenario Fixture",
    "description": "A scenario fixture for testing scenarios.py",
    "analysis_period_years": 6, # Renamed
    "analysis_start_year": 2025, # Renamed
    # Placeholders for vehicle objects, filled in fixture
    "electric_vehicle": None,
    "diesel_vehicle": None,
    "economic_parameters": EconomicParameters(
        discount_rate_percent_real=5.0, # Renamed, Scaled
        inflation_rate_percent=2.0 # Renamed, Scaled
    ),
    "operational_parameters": OperationalParameters(
        annual_mileage_km=50000 # Renamed
    ),
    "financing_options": FinancingOptions(
        financing_method="cash",
        down_payment_percent=20.0, # Renamed, Scaled
        loan_term_years=5, # Renamed
        loan_interest_rate_percent=6.0 # Renamed, Scaled
    ),
    "infrastructure_costs": InfrastructureCosts(
        selected_charger_cost_aud=3000, # Renamed
        selected_installation_cost_aud=1000, # Renamed
        charger_maintenance_annual_rate_percent=1.0, # Renamed, Scaled
        charger_lifespan_years=8 # Renamed
    ),
    "electricity_price_projections": ElectricityPriceProjections( # Updated structure
        selected_scenario_name="scenario_a", # Renamed
        scenarios=[{"name": "scenario_a", "prices": {
            2025: ElectricityPricePoint(price_aud_per_kwh_or_range=0.22),
            2030: ElectricityPricePoint(price_aud_per_kwh_or_range=0.25)
        }}]
    ),
    "diesel_price_projections": DieselPriceProjections( # Renamed, Updated structure
        selected_scenario_name="scenario_b", # Renamed
        scenarios=[{"name": "scenario_b", "data": DieselPriceScenarioData(
            price_aud_per_l_or_projection={2025: 1.80, 2030: 1.90} # Updated name
        )}]
    ),
    "maintenance_costs_detailed": MaintenanceCosts( # Updated structure
        costs_by_type={
            "rigid_bet": MaintenanceDetail(annual_cost_min_aud=450, annual_cost_max_aud=900), # Updated names
            "rigid_diesel": MaintenanceDetail(annual_cost_min_aud=1300, annual_cost_max_aud=2800) # Updated names
        }
    ),
    "insurance_registration_costs": InsuranceRegistrationCosts( # Renamed, Updated structure
        electric=InsuranceRegistrationDetail(base_annual_cost_aud=12000, annual_rate_percent_of_value=0), # Updated names
        diesel=InsuranceRegistrationDetail(base_annual_cost_aud=9000, annual_rate_percent_of_value=0) # Updated names
        # Registration costs are now part of Vehicle data
    ),
    "carbon_tax_config": CarbonTaxConfig( # Updated structure
        include_carbon_tax=True, # Renamed
        initial_rate_aud_per_tonne_co2e=25.0, # Renamed
        annual_increase_rate_percent=3.0 # Renamed, Scaled
    ),
    "road_user_charge_config": RoadUserChargeConfig( # Updated structure
        include_road_user_charge=True, # Renamed
        initial_charge_aud_per_km=0.03, # Renamed
        annual_increase_rate_percent=1.0 # Renamed, Scaled
    ),
    "general_cost_increase_rates": GeneralCostIncreaseRates( # Updated structure
        maintenance_annual_increase_rate_percent=1.5, # Renamed, Scaled
        insurance_annual_increase_rate_percent=1.0, # Renamed, Scaled
        registration_annual_increase_rate_percent=1.0 # Renamed, Scaled
    ),
    "battery_replacement_config": BatteryReplacementConfig( # Updated structure
        enable_battery_replacement=True, # Renamed
        annual_degradation_rate_percent=2.0, # Renamed, Scaled
        replacement_threshold_fraction=0.7, # Renamed
        force_replacement_year_index=None # Renamed
    )
}


@pytest.fixture
def valid_scenario_data():
    """Provides a valid scenario dictionary with instantiated vehicle objects."""
    scenario_config = copy.deepcopy(BASE_SCENARIO_CONFIG)
    # Instantiate vehicles
    ev_instance = ElectricVehicle(**copy.deepcopy(BASE_EV_DATA))
    diesel_instance = DieselVehicle(**copy.deepcopy(BASE_DIESEL_DATA))
    scenario_config['electric_vehicle'] = ev_instance
    scenario_config['diesel_vehicle'] = diesel_instance
    # Add battery projections separately as required by Scenario model
    scenario_config['battery_pack_cost_aud_per_kwh_projections'] = ev_instance.battery_pack_cost_aud_per_kwh_projections
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
        assert scenario.analysis_period_years == valid_scenario_data["analysis_period_years"] # Renamed
        # Use attribute access for nested models
        assert scenario.electric_vehicle.base_purchase_price_aud == valid_scenario_data["electric_vehicle"].base_purchase_price_aud # Renamed
        assert scenario.operational_parameters.annual_mileage_km == valid_scenario_data["operational_parameters"].annual_mileage_km # Renamed

        # Check price lookup (keys are updated)
        # Get base price from the structured projections
        selected_elec_scen_name = valid_scenario_data["electricity_price_projections"].selected_scenario_name
        elec_scenarios = {s['name']: s for s in valid_scenario_data["electricity_price_projections"].scenarios}
        elec_prices = elec_scenarios[selected_elec_scen_name]['prices']
        start_year = valid_scenario_data["analysis_start_year"]
        expected_elec_price_y0 = elec_prices[start_year].price_aud_per_kwh_or_range
        assert scenario.get_annual_price('electricity_price_aud_per_kwh', 0) == pytest.approx(expected_elec_price_y0)

        assert scenario.electric_vehicle.name == valid_scenario_data["electric_vehicle"].name
        assert scenario.diesel_vehicle.co2_emission_factor_kg_per_l == valid_scenario_data["diesel_vehicle"].co2_emission_factor_kg_per_l # Renamed
    except ValidationError as e:
        pytest.fail(f"Scenario creation failed with valid data: {e}")

def test_scenario_validation_negative_price(valid_scenario_data):
    """Test validation fails if nested vehicle prices are not positive."""
    invalid_ev_data = copy.deepcopy(BASE_EV_DATA)
    invalid_ev_data["base_purchase_price_aud"] = -1000 # Use renamed attribute

    scenario_data_with_invalid_ev = copy.deepcopy(valid_scenario_data)
    scenario_data_with_invalid_ev["electric_vehicle"] = invalid_ev_data # Pass dict
    # Remove potentially conflicting battery projection from top level if passing dict
    scenario_data_with_invalid_ev.pop('battery_pack_cost_aud_per_kwh_projections', None)

    with pytest.raises(ValidationError) as excinfo:
        Scenario(**scenario_data_with_invalid_ev)
    assert "electric_vehicle.base_purchase_price_aud" in str(excinfo.value)
    assert "Input should be greater than 0" in str(excinfo.value)

    invalid_diesel_data = copy.deepcopy(BASE_DIESEL_DATA)
    invalid_diesel_data["base_purchase_price_aud"] = 0 # Use renamed attribute
    scenario_data_with_invalid_diesel = copy.deepcopy(valid_scenario_data)
    scenario_data_with_invalid_diesel["diesel_vehicle"] = invalid_diesel_data # Pass dict
    with pytest.raises(ValidationError) as excinfo:
        Scenario(**scenario_data_with_invalid_diesel)
    assert "diesel_vehicle.base_purchase_price_aud" in str(excinfo.value)
    assert "Input should be greater than 0" in str(excinfo.value)

def test_scenario_validation_missing_required(valid_scenario_data):
    """Test validation fails if a required field is missing (top-level or nested model)."""
    invalid_data_missing_top_level = copy.deepcopy(valid_scenario_data)
    del invalid_data_missing_top_level["analysis_period_years"] # Remove renamed required field
    # Remove instantiated objects as they might become invalid if base scenario changes
    invalid_data_missing_top_level['electric_vehicle'] = copy.deepcopy(BASE_EV_DATA)
    invalid_data_missing_top_level['diesel_vehicle'] = copy.deepcopy(BASE_DIESEL_DATA)
    invalid_data_missing_top_level.pop('battery_pack_cost_aud_per_kwh_projections', None)

    with pytest.raises(ValidationError) as excinfo:
        Scenario(**invalid_data_missing_top_level)
    assert "Field required" in str(excinfo.value)
    assert "analysis_period_years" in str(excinfo.value)

    # Test missing required nested Pydantic model
    invalid_data_missing_nested_model = copy.deepcopy(valid_scenario_data)
    del invalid_data_missing_nested_model["economic_parameters"]
    invalid_data_missing_nested_model['electric_vehicle'] = copy.deepcopy(BASE_EV_DATA)
    invalid_data_missing_nested_model['diesel_vehicle'] = copy.deepcopy(BASE_DIESEL_DATA)
    invalid_data_missing_nested_model.pop('battery_pack_cost_aud_per_kwh_projections', None)
    with pytest.raises(ValidationError) as excinfo:
         Scenario(**invalid_data_missing_nested_model)
    assert "Field required" in str(excinfo.value)
    assert "economic_parameters" in str(excinfo.value)

    # Test missing required field within a nested model (using dict representation)
    invalid_economic_data = copy.deepcopy(valid_scenario_data["economic_parameters"].model_dump())
    del invalid_economic_data["discount_rate_percent_real"]
    scenario_data_missing_nested_field = copy.deepcopy(valid_scenario_data)
    scenario_data_missing_nested_field["economic_parameters"] = invalid_economic_data # Pass dict
    scenario_data_missing_nested_field['electric_vehicle'] = copy.deepcopy(BASE_EV_DATA)
    scenario_data_missing_nested_field['diesel_vehicle'] = copy.deepcopy(BASE_DIESEL_DATA)
    scenario_data_missing_nested_field.pop('battery_pack_cost_aud_per_kwh_projections', None)
    with pytest.raises(ValidationError) as excinfo:
        Scenario(**scenario_data_missing_nested_field)
    assert "Field required" in str(excinfo.value)
    assert "economic_parameters -> discount_rate_percent_real" in str(excinfo.value) or \
           "economic_parameters.discount_rate_percent_real" in str(excinfo.value)

    # Test Scenario rejects None for a required nested vehicle object
    invalid_data_none_vehicle = copy.deepcopy(valid_scenario_data)
    invalid_data_none_vehicle["electric_vehicle"] = None
    with pytest.raises(ValidationError) as excinfo:
         Scenario(**invalid_data_none_vehicle)
    assert "electric_vehicle" in str(excinfo.value)
    assert "Input should be a valid dictionary or instance of ElectricVehicle" in str(excinfo.value)

def test_scenario_to_from_file(valid_scenario_data, temp_yaml_file):
    """Test saving a Scenario to YAML and loading it back."""
    scenario = Scenario(**valid_scenario_data)
    scenario.to_file(temp_yaml_file)
    assert os.path.exists(temp_yaml_file)
    loaded_scenario = Scenario.from_file(temp_yaml_file)
    assert scenario == loaded_scenario

    # Check specific nested fields using attribute access
    assert loaded_scenario.name == valid_scenario_data["name"]
    assert loaded_scenario.economic_parameters.discount_rate_percent_real == valid_scenario_data["economic_parameters"].discount_rate_percent_real
    assert loaded_scenario.electric_vehicle.base_purchase_price_aud == valid_scenario_data["electric_vehicle"].base_purchase_price_aud
    assert loaded_scenario.diesel_vehicle.name == valid_scenario_data["diesel_vehicle"].name

    # Check price lookup (use updated key)
    start_year = valid_scenario_data["analysis_start_year"]
    selected_diesel_scen_name = valid_scenario_data["diesel_price_projections"].selected_scenario_name
    diesel_scenarios = {s['name']: s for s in valid_scenario_data["diesel_price_projections"].scenarios}
    diesel_data = diesel_scenarios[selected_diesel_scen_name]['data']
    expected_diesel_price_y0 = diesel_data.price_aud_per_l_or_projection[start_year]
    assert loaded_scenario.get_annual_price('diesel_price_aud_per_l', 0) == pytest.approx(expected_diesel_price_y0)

def test_scenario_from_file_not_found(tmp_path):
    """Test loading from a non-existent file raises FileNotFoundError."""
    non_existent_file = tmp_path / "non_existent.yaml"
    with pytest.raises(FileNotFoundError):
        Scenario.from_file(non_existent_file)

def test_scenario_from_file_invalid_yaml(temp_yaml_file):
    """Test loading from an invalid YAML file raises ValueError."""
    with open(temp_yaml_file, 'w') as f:
        f.write("name: Test Scenario\nanalysis_period_years: 5\n  economic_parameters:\n    bad_indent: true") # Invalid indentation within nested

    with pytest.raises(ValueError) as excinfo:
        Scenario.from_file(temp_yaml_file)
    assert "Error parsing YAML file" in str(excinfo.value)

def test_scenario_from_file_validation_error(temp_yaml_file, valid_scenario_data):
    """Test loading from YAML with data failing validation raises ValueError."""
    valid_scenario_obj = Scenario(**valid_scenario_data)
    invalid_data_dump = valid_scenario_obj.model_dump()
    # Introduce validation error in a nested field
    invalid_data_dump["economic_parameters"]["discount_rate_percent_real"] = -10.0 # Use renamed field

    with open(temp_yaml_file, 'w') as f:
        yaml.dump(invalid_data_dump, f, default_flow_style=False)

    with pytest.raises(ValueError) as excinfo:
        Scenario.from_file(temp_yaml_file)
    assert str(excinfo.value).startswith("Error validating scenario data from")

def test_scenario_to_dict(valid_scenario_data):
    """Test converting a Scenario instance to a dictionary using model_dump."""
    scenario = Scenario(**valid_scenario_data)
    scenario_dict = scenario.model_dump()

    assert scenario_dict["name"] == valid_scenario_data["name"]
    assert scenario_dict["analysis_period_years"] == valid_scenario_data["analysis_period_years"] # Renamed
    # Check nested model dict
    assert scenario_dict["operational_parameters"]["annual_mileage_km"] == valid_scenario_data["operational_parameters"].annual_mileage_km # Renamed
    # Compare nested vehicle data
    assert scenario_dict["electric_vehicle"]["name"] == valid_scenario_data["electric_vehicle"].name
    assert scenario_dict["diesel_vehicle"]["base_purchase_price_aud"] == valid_scenario_data["diesel_vehicle"].base_purchase_price_aud # Renamed

    assert isinstance(scenario_dict, dict)
    # Check that nested models are also dicts
    assert isinstance(scenario_dict["economic_parameters"], dict)
    assert isinstance(scenario_dict["electric_vehicle"], dict)

def test_get_annual_price(valid_scenario_data):
    """Test the get_annual_price method for calculated prices using updated keys."""
    scenario = Scenario(**valid_scenario_data)
    analysis_years = scenario.analysis_period_years # Renamed
    start_year = scenario.analysis_start_year # Renamed

    # --- Check Electricity Price --- 
    elec_proj = scenario.electricity_price_projections
    selected_elec_scen_name = elec_proj.selected_scenario_name
    elec_scenarios = {s['name']: s for s in elec_proj.scenarios}
    elec_prices_dict = elec_scenarios[selected_elec_scen_name]['prices']
    # Find the price for the start year
    base_elec_price = elec_prices_dict[start_year].price_aud_per_kwh_or_range
    assert scenario.get_annual_price('electricity_price_aud_per_kwh', 0) == pytest.approx(base_elec_price)
    # Add a test for interpolation or lookup if applicable (depends on internal logic)

    # --- Check Diesel Price --- 
    diesel_proj = scenario.diesel_price_projections
    selected_diesel_scen_name = diesel_proj.selected_scenario_name
    diesel_scenarios = {s['name']: s for s in diesel_proj.scenarios}
    diesel_data = diesel_scenarios[selected_diesel_scen_name]['data']
    # Price for start year
    base_diesel_price = diesel_data.get_price_aud_per_l_for_year(start_year, analysis_years=analysis_years, analysis_start_year=start_year)
    assert scenario.get_annual_price('diesel_price_aud_per_l', 0) == pytest.approx(base_diesel_price)

    # --- Check Carbon Tax --- 
    # Use updated attribute names and structure
    base_carbon = scenario.carbon_tax_config.initial_rate_aud_per_tonne_co2e
    rate_carbon_percent = scenario.carbon_tax_config.annual_increase_rate_percent
    rate_carbon_fraction = rate_carbon_percent / 100.0
    for i in range(analysis_years):
        expected_carbon = base_carbon * (1 + rate_carbon_fraction) ** i
        # Use updated key 'carbon_tax_aud_per_tonne'
        assert scenario.get_annual_price('carbon_tax_aud_per_tonne', i) == pytest.approx(expected_carbon)

    # --- Check RUC --- 
    # Use updated attribute names and structure
    base_ruc = scenario.road_user_charge_config.initial_charge_aud_per_km
    rate_ruc_percent = scenario.road_user_charge_config.annual_increase_rate_percent
    rate_ruc_fraction = rate_ruc_percent / 100.0
    for i in range(analysis_years):
        expected_ruc = base_ruc * (1 + rate_ruc_fraction) ** i
        # Use updated key 'road_user_charge_aud_per_km'
        assert scenario.get_annual_price('road_user_charge_aud_per_km', i) == pytest.approx(expected_ruc)

    # Test non-existent price type (key should be specific)
    with pytest.raises(ValueError, match="Cost type key 'non_existent_key' not found"): # Expect specific error now
        scenario.get_annual_price('non_existent_key', 0)

    # Test index out of bounds
    with pytest.raises(ValueError, match=f"Year index {analysis_years} out of bounds"): # Expect specific error now
        scenario.get_annual_price('electricity_price_aud_per_kwh', analysis_years)

def test_scenario_with_modifications(valid_scenario_data):
    """Test model_copy for modifications."""
    scenario1 = Scenario(**valid_scenario_data)

    # Modify a nested field within a nested Pydantic model
    new_op_params = scenario1.operational_parameters.model_copy(update={"annual_mileage_km": 60000})
    scenario2 = scenario1.model_copy(update={"operational_parameters": new_op_params})

    # Check original is unchanged
    assert scenario1.operational_parameters.annual_mileage_km == 50000
    # Check new instance has the modification
    assert scenario2.operational_parameters.annual_mileage_km == 60000
    # Check other fields are copied
    assert scenario2.name == scenario1.name
    assert scenario2.economic_parameters == scenario1.economic_parameters
    assert scenario2.electric_vehicle == scenario1.electric_vehicle
    # Check prices remain the same if underlying rates didn't change
    assert scenario2.get_annual_price('electricity_price_aud_per_kwh', 1) == scenario1.get_annual_price('electricity_price_aud_per_kwh', 1)

    # Modify a nested vehicle object
    ev_mods = scenario1.electric_vehicle.model_copy(update={"base_purchase_price_aud": 90000})
    scenario3 = scenario1.model_copy(update={"electric_vehicle": ev_mods})

    assert scenario1.electric_vehicle.base_purchase_price_aud == 80000
    assert scenario3.electric_vehicle.base_purchase_price_aud == 90000
    assert scenario3.electric_vehicle.name == scenario1.electric_vehicle.name
    assert scenario3.operational_parameters == scenario1.operational_parameters

    # Modify a field within a config model that affects price calculations
    new_carbon_config = scenario1.carbon_tax_config.model_copy(update={"annual_increase_rate_percent": 5.0})
    scenario4 = scenario1.model_copy(update={"carbon_tax_config": new_carbon_config})

    # Check the price recalculation
    price1_y1 = scenario1.get_annual_price('carbon_tax_aud_per_tonne', 1)
    price4_y1 = scenario4.get_annual_price('carbon_tax_aud_per_tonne', 1)
    assert price4_y1 != price1_y1 # Prices should differ due to rate change
    # Calculate expected new price
    expected_price4_y1 = scenario4.carbon_tax_config.initial_rate_aud_per_tonne_co2e * (1 + 5.0/100.0) ** 1
    assert price4_y1 == pytest.approx(expected_price4_y1)

    # Modify multiple fields, including nested vehicle and config
    dv_mods = scenario1.diesel_vehicle.model_copy(update={"base_purchase_price_aud": 75000})
    new_finance_config = scenario1.financing_options.model_copy(update={"financing_method": "loan"})
    scenario5 = scenario1.model_copy(update={
        "diesel_vehicle": dv_mods,
        "financing_options": new_finance_config
    })

    assert scenario1.diesel_vehicle.base_purchase_price_aud == 70000
    assert scenario5.diesel_vehicle.base_purchase_price_aud == 75000
    assert scenario1.financing_options.financing_method == "cash"
    assert scenario5.financing_options.financing_method == "loan"
    assert scenario5.operational_parameters == scenario1.operational_parameters

# Remove old tests that are no longer valid due to structural changes

# Placeholder for any new tests specific to Scenario functionality
# (e.g., validators, specific method behavior if any are added beyond Pydantic basics) 