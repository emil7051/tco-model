import pytest
import math
import numpy as np
import numpy_financial as npf # Add numpy_financial import
from unittest.mock import MagicMock, patch
import copy
from pydantic import ValidationError
import logging

# Import components to test
from tco_model.components import (
    CostComponent,
    AcquisitionCost,
    EnergyCost,
    MaintenanceCost,
    InfrastructureCost,
    BatteryReplacementCost,
    InsuranceCost,
    RegistrationCost,
    ResidualValue,
    CarbonTaxCost,
    RoadUserChargeCost,
    get_battery_cost_per_kwh # Import the helper function
)

# Import dependencies needed for components
# Import specific model types needed for configuration
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
from tco_model.vehicles import (
    Vehicle, ElectricVehicle, DieselVehicle, 
    EnergyConsumptionStrategy, MaintenanceStrategy, # Import base strategy protocols
    ElectricConsumptionStrategy, DieselConsumptionStrategy, # Keep for potential direct use if needed
    ElectricMaintenanceStrategy, DieselMaintenanceStrategy # Keep for potential direct use if needed
)

# --- Updated Base Configurations for Fixtures ---

BASE_EV_DATA = {
    "name": "Fixture EV",
    "vehicle_type": "rigid_bet", # Use specific type from maintenance keys
    "base_purchase_price_aud": 80000,
    "lifespan_years": 15,
    "residual_value_percent_projections": {5: 0.4, 10: 0.2, 15: 0.1}, # Scaled 0.0-1.0
    "base_registration_cost_aud": 450,
    "energy_consumption_kwh_per_km": 0.22,
    "battery_capacity_kwh": 65.0,
    "battery_pack_cost_aud_per_kwh_projections": {2025: 170, 2030: 100, 2035: 75}, # New name
    "battery_warranty_years": 8,
    "battery_cycle_life": 1500,
    "battery_depth_of_discharge_percent": 80.0, # Scaled 0-100
    "charging_efficiency_percent": 90.0, # Scaled 0-100
    "purchase_price_annual_decrease_rate_real": 0.01 # Renamed
}

BASE_DIESEL_DATA = {
    "name": "Fixture Diesel",
    "vehicle_type": "rigid_diesel", # Use specific type from maintenance keys
    "base_purchase_price_aud": 70000,
    "lifespan_years": 12,
    "residual_value_percent_projections": {5: 0.5, 10: 0.3, 12: 0.15}, # Scaled 0.0-1.0
    "base_registration_cost_aud": 550,
    "fuel_consumption_l_per_100km": 9.0,
    "co2_emission_factor_kg_per_l": 2.68 # Renamed
}

# Using nested Pydantic models for configuration
BASE_SCENARIO_CONFIG = {
    "name": "Base Test Scenario Components",
    "description": "Base scenario for testing components",
    "analysis_period_years": 10, # Renamed
    "analysis_start_year": 2025, # Renamed
    # Vehicles added in fixture below
    "economic_parameters": EconomicParameters(
        discount_rate_percent_real=4.0, # Renamed, Scaled 0-100
        inflation_rate_percent=2.0 # Renamed, Scaled 0-100
    ),
    "operational_parameters": OperationalParameters(
        annual_mileage_km=18000 # Renamed
    ),
    "financing_options": FinancingOptions(
        financing_method="cash",
        down_payment_percent=20.0, # Renamed, Scaled 0-100
        loan_term_years=5, # Renamed
        loan_interest_rate_percent=6.0 # Renamed, Scaled 0-100
    ),
    "infrastructure_costs": InfrastructureCosts(
        selected_charger_cost_aud=4000, # Renamed
        selected_installation_cost_aud=1500, # Renamed
        charger_maintenance_annual_rate_percent=1.0, # Renamed, Scaled 0-100
        charger_lifespan_years=10 # Renamed
    ),
    "electricity_price_projections": ElectricityPriceProjections( # Updated Structure
        selected_scenario_name="stable", # Renamed
        scenarios=[
            {"name": "stable", "prices": {
                2025: ElectricityPricePoint(price_aud_per_kwh_or_range=0.25),
                2030: ElectricityPricePoint(price_aud_per_kwh_or_range=0.25),
                2035: ElectricityPricePoint(price_aud_per_kwh_or_range=0.25)
            }},
            {"name": "increasing", "prices": {
                2025: ElectricityPricePoint(price_aud_per_kwh_or_range=0.25),
                2030: ElectricityPricePoint(price_aud_per_kwh_or_range=0.30),
                2035: ElectricityPricePoint(price_aud_per_kwh_or_range=0.35)
            }}
        ]
    ),
    "diesel_price_projections": DieselPriceProjections( # Renamed + Updated Structure
        selected_scenario_name="stable", # Renamed
        scenarios=[
            {"name": "stable", "data": DieselPriceScenarioData(
                price_aud_per_l_or_projection={2025: 1.60, 2030: 1.60, 2035: 1.60}
            )},
            {"name": "increasing", "data": DieselPriceScenarioData(
                price_aud_per_l_or_projection={2025: 1.60, 2030: 1.80, 2035: 2.00}
            )}
        ]
    ),
    "maintenance_costs_detailed": MaintenanceCosts( # Updated Structure
        costs_by_type={
            "rigid_bet": MaintenanceDetail(annual_cost_min_aud=400, annual_cost_max_aud=800),
            "rigid_diesel": MaintenanceDetail(annual_cost_min_aud=1200, annual_cost_max_aud=2500)
        }
    ),
    "insurance_registration_costs": InsuranceRegistrationCosts( # Renamed + Updated Structure
        electric=InsuranceRegistrationDetail(
            base_annual_cost_aud=15000, # Assuming this was insurance cost
            annual_rate_percent_of_value=0 # Assuming no % rate based on old structure
        ),
        diesel=InsuranceRegistrationDetail(
            base_annual_cost_aud=8000, # Assuming this was insurance cost
            annual_rate_percent_of_value=0 # Assuming no % rate based on old structure
        )
        # Registration is now part of Vehicle definition, not here
    ),
    "carbon_tax_config": CarbonTaxConfig( # Updated Structure
        include_carbon_tax=True, # Renamed
        initial_rate_aud_per_tonne_co2e=28.0, # Renamed
        annual_increase_rate_percent=3.0 # Renamed, Scaled 0-100
    ),
    "road_user_charge_config": RoadUserChargeConfig( # Updated Structure
        include_road_user_charge=True, # Renamed
        initial_charge_aud_per_km=0.04, # Renamed
        annual_increase_rate_percent=1.0 # Renamed, Scaled 0-100
    ),
    "general_cost_increase_rates": GeneralCostIncreaseRates( # Updated Structure
        maintenance_annual_increase_rate_percent=1.0, # Renamed, Scaled 0-100
        insurance_annual_increase_rate_percent=1.0, # Renamed, Scaled 0-100
        registration_annual_increase_rate_percent=1.0 # Renamed, Scaled 0-100
    ),
    "battery_replacement_config": BatteryReplacementConfig( # Updated Structure
        enable_battery_replacement=True, # Renamed
        annual_degradation_rate_percent=2.0, # Renamed, Scaled 0-100
        replacement_threshold_fraction=0.7, # Renamed, Scaled 0-1
        force_replacement_year_index=None # Renamed, 0-based
    )
    # Note: base_electricity_price_aud_per_kwh and base_diesel_price_aud_per_l are gone
    # Note: battery_pack_cost_aud_per_kwh_projections is now added directly
}

# --- Dummy Strategies for Mock Vehicle ---
class MockEnergyStrategy:
    def calculate_consumption(self, distance_km: float) -> float:
        return 0.0
    @property
    def unit(self) -> str:
        return "mock_unit"

class MockMaintenanceStrategy:
     def calculate_base_annual_cost(self, vehicle: 'Vehicle', scenario: 'Scenario') -> float:
         # Return a simple value or 0 for mock testing
         return 10.0 # Example base cost

# --- Helper Mock Vehicle Class (Updated) ---
class MockVehicle(Vehicle):
    """A basic mock vehicle for testing components, implementing abstract methods."""
    # Add specific mock fields if needed by components being tested
    # mock_specific_param: float = 0.0 

    # Implement abstract strategy properties
    _mock_energy_strategy = MockEnergyStrategy()
    _mock_maint_strategy = MockMaintenanceStrategy()

    @property
    def energy_consumption_strategy(self) -> EnergyConsumptionStrategy:
        return self._mock_energy_strategy

    @property
    def maintenance_strategy(self) -> MaintenanceStrategy:
        return self._mock_maint_strategy

    # No need to override calculate_energy_consumption or calculate_annual_energy_cost
    # as the base class methods will use the strategies above.
    # No need for maintenance_key property anymore.

    # Need to initialize with base fields required by Vehicle
    def __init__(self, **data):
        # Provide default base values suitable for component testing
        default_data = {
            "name": "Mock Vehicle",
            "vehicle_type": "rigid", # Or another valid Literal value
            "base_purchase_price_aud": 10000,
            "lifespan_years": 10,
            "residual_value_percent_projections": {5: 0.5, 10: 0.1},
            "base_registration_cost_aud": 100,
        }
        # Allow overriding defaults with passed data
        final_data = {**default_data, **data}
        super().__init__(**final_data)

# --- Fixtures ---
@pytest.fixture
def mock_vehicle_instance():
    """Creates a mock vehicle object for testing components."""
    # Pass any specific mock params if needed, e.g.:
    # return MockVehicle(mock_specific_param=5.0)
    return MockVehicle()

@pytest.fixture
def basic_scenario():
    """Provides a basic, valid Scenario object for testing components."""
    scenario_config = copy.deepcopy(BASE_SCENARIO_CONFIG)
    try:
        # Create vehicle instances
        ev_instance = ElectricVehicle(**copy.deepcopy(BASE_EV_DATA))
        dv_instance = DieselVehicle(**copy.deepcopy(BASE_DIESEL_DATA))

        # Add vehicles and the battery cost projection to the config dictionary
        scenario_config['electric_vehicle'] = ev_instance
        scenario_config['diesel_vehicle'] = dv_instance
        # Add battery projections directly to the scenario config dict before Pydantic creation
        scenario_config['battery_pack_cost_aud_per_kwh_projections'] = ev_instance.battery_pack_cost_aud_per_kwh_projections

        # Create and return the Scenario instance
        return Scenario(**scenario_config)
    except ValidationError as e:
        pytest.fail(f"Failed to create basic_scenario fixture: {e}")


# --- Component Tests (Updated) ---

# 1. Acquisition Cost
def test_acquisition_cash(basic_scenario):
    """Test acquisition cost calculation for cash payment."""
    component = AcquisitionCost()
    # Ensure financing method is cash (default in fixture)
    cash_scenario = basic_scenario
    assert cash_scenario.financing_options.financing_method == "cash"
    vehicle = cash_scenario.electric_vehicle
    cost_y0 = component.calculate_annual_cost(year=cash_scenario.analysis_start_year, vehicle=vehicle, scenario=cash_scenario, calculation_year_index=0, total_mileage_km=0)
    cost_y1 = component.calculate_annual_cost(year=cash_scenario.analysis_start_year + 1, vehicle=vehicle, scenario=cash_scenario, calculation_year_index=1, total_mileage_km=0)
    assert cost_y0 == vehicle.base_purchase_price_aud # Updated attribute
    assert cost_y1 == 0

def test_acquisition_loan(basic_scenario):
    """Test acquisition cost calculation for loan financing."""
    component = AcquisitionCost()
    # Update financing options for this test
    loan_options = FinancingOptions(
        financing_method="loan",
        down_payment_percent=10.0, # Updated scale
        loan_term_years=5, # Updated name
        loan_interest_rate_percent=7.0 # Updated name & scale
    )
    loan_scenario = basic_scenario.model_copy(update={"financing_options": loan_options})
    vehicle = loan_scenario.diesel_vehicle

    # Use updated attribute names from scenario and vehicle
    down_payment_fraction = loan_scenario.financing_options.down_payment_percent / 100.0
    down_payment = vehicle.base_purchase_price_aud * down_payment_fraction
    loan_amount = vehicle.base_purchase_price_aud - down_payment
    interest_rate_fraction = loan_scenario.financing_options.loan_interest_rate_percent / 100.0
    loan_term = loan_scenario.financing_options.loan_term_years

    try:
        annual_payment = -npf.pmt(interest_rate_fraction, loan_term, loan_amount)
    except ImportError:
        pytest.skip("numpy_financial not installed, skipping loan payment check.")
        annual_payment = 0

    cost_y0 = component.calculate_annual_cost(year=loan_scenario.analysis_start_year, vehicle=vehicle, scenario=loan_scenario, calculation_year_index=0, total_mileage_km=0)
    assert cost_y0 == pytest.approx(down_payment)

    cost_y1 = component.calculate_annual_cost(year=loan_scenario.analysis_start_year + 1, vehicle=vehicle, scenario=loan_scenario, calculation_year_index=1, total_mileage_km=0)
    assert cost_y1 == pytest.approx(annual_payment)

    # Use updated attribute name for loan term
    cost_after = component.calculate_annual_cost(year=loan_scenario.analysis_start_year + loan_term + 1, vehicle=vehicle, scenario=loan_scenario, calculation_year_index=loan_term + 1, total_mileage_km=0)
    assert cost_after == 0

def test_acquisition_loan_zero_interest(basic_scenario):
    """Test loan calculation with zero interest rate."""
    component = AcquisitionCost()
    zero_interest_options = basic_scenario.financing_options.model_copy(update={
        "financing_method": "loan",
        "loan_interest_rate_percent": 0.0 # Updated name & scale
    })
    zero_interest_scenario = basic_scenario.model_copy(update={"financing_options": zero_interest_options})
    vehicle = zero_interest_scenario.electric_vehicle

    # Use updated attribute names
    down_payment_fraction = zero_interest_scenario.financing_options.down_payment_percent / 100.0
    down_payment = vehicle.base_purchase_price_aud * down_payment_fraction
    loan_amount = vehicle.base_purchase_price_aud - down_payment
    loan_term = zero_interest_scenario.financing_options.loan_term_years
    expected_payment = loan_amount / loan_term if loan_term > 0 else 0

    cost_y1 = component.calculate_annual_cost(year=zero_interest_scenario.analysis_start_year + 1, vehicle=vehicle, scenario=zero_interest_scenario, calculation_year_index=1, total_mileage_km=0)
    assert cost_y1 == pytest.approx(expected_payment)

def test_acquisition_unsupported_method(basic_scenario):
    """Test acquisition cost calculation with an unsupported financing method."""
    component = AcquisitionCost()
    # Update financing options directly
    unsupported_options = basic_scenario.financing_options.model_copy(update={"financing_method": "lease"})
    unsupported_scenario = basic_scenario.model_copy(update={"financing_options": unsupported_options})

    with pytest.raises(ValueError, match="Unsupported financing method: lease"):
        component.calculate_annual_cost(year=unsupported_scenario.analysis_start_year, vehicle=unsupported_scenario.electric_vehicle, scenario=unsupported_scenario, calculation_year_index=0, total_mileage_km=0)


# 2. Energy Cost
def test_energy_cost_electric(basic_scenario):
    component = EnergyCost()
    vehicle = basic_scenario.electric_vehicle
    year_index = 2
    # Use updated attribute name for mileage
    annual_mileage = basic_scenario.operational_parameters.annual_mileage_km
    # Use updated method parameters
    consumption_kwh = vehicle.calculate_energy_consumption(annual_mileage)
    # Use updated method name and key
    price_year_2 = basic_scenario.get_annual_price('electricity_price_aud_per_kwh', year_index)
    # Use updated method parameters for cost calculation
    expected_cost = vehicle.calculate_annual_energy_cost(annual_mileage, price_year_2)

    calculated_cost = component.calculate_annual_cost(year=basic_scenario.analysis_start_year + year_index, vehicle=vehicle, scenario=basic_scenario, calculation_year_index=year_index, total_mileage_km=0)
    assert calculated_cost == pytest.approx(expected_cost, abs=1e-2)

def test_energy_cost_diesel(basic_scenario):
    component = EnergyCost()
    vehicle = basic_scenario.diesel_vehicle
    year_index = 4
    # Use updated attribute name for mileage
    annual_mileage = basic_scenario.operational_parameters.annual_mileage_km
    # Use updated method parameters
    consumption_l = vehicle.calculate_energy_consumption(annual_mileage)
    # Use updated method name and key
    price_year_4 = basic_scenario.get_annual_price('diesel_price_aud_per_l', year_index)
     # Use updated method parameters for cost calculation
    expected_cost = vehicle.calculate_annual_energy_cost(annual_mileage, price_year_4)

    calculated_cost = component.calculate_annual_cost(year=basic_scenario.analysis_start_year + year_index, vehicle=vehicle, scenario=basic_scenario, calculation_year_index=year_index, total_mileage_km=0)
    assert calculated_cost == pytest.approx(expected_cost, abs=1e-2)

def test_energy_cost_missing_price(basic_scenario, caplog):
    component = EnergyCost()
    vehicle = basic_scenario.electric_vehicle
    # Use updated internal cache name and keys
    with patch.object(basic_scenario, '_generated_prices_cache', {
        'diesel_price_aud_per_l': [1.0],
        'carbon_tax_aud_per_tonne': [1.0] # Example other key
        }):
        caplog.set_level(logging.WARNING)
        # Use updated key in error message check
        with pytest.raises(ValueError, match=f"Electricity price \(electricity_price_aud_per_kwh\) for year index 0 not found in cache."):
             component.calculate_annual_cost(year=basic_scenario.analysis_start_year, vehicle=vehicle, scenario=basic_scenario, calculation_year_index=0, total_mileage_km=0)
    # Check if a warning was logged by get_annual_price (internal detail, might change)
    # assert "Cost type key 'electricity_price_aud_per_kwh' not found" in caplog.text

def test_energy_cost_unsupported_vehicle(basic_scenario, mock_vehicle_instance):
    component = EnergyCost()
    # Mock vehicle uses MockEnergyStrategy with unit "mock_unit"
    with pytest.raises(TypeError, match="Unsupported energy unit 'mock_unit' from vehicle's strategy."):
        component.calculate_annual_cost(year=basic_scenario.analysis_start_year, vehicle=mock_vehicle_instance, scenario=basic_scenario, calculation_year_index=0, total_mileage_km=0)


# 3. Maintenance Cost
def test_maintenance_cost_electric(basic_scenario):
    component = MaintenanceCost()
    vehicle = basic_scenario.electric_vehicle # vehicle_type is 'rigid_bet'
    year_index = 3
    # Use updated attribute name and structure
    maint_details = basic_scenario.maintenance_costs_detailed.costs_by_type['rigid_bet']
    # Use updated attribute names within MaintenanceDetail
    base_avg = (maint_details.annual_cost_min_aud + maint_details.annual_cost_max_aud) / 2.0
    # Use updated attribute name and scale
    increase_rate_fraction = basic_scenario.general_cost_increase_rates.maintenance_annual_increase_rate_percent / 100.0
    expected_cost = base_avg * (1 + increase_rate_fraction) ** year_index
    calculated_cost = component.calculate_annual_cost(year=basic_scenario.analysis_start_year + year_index, vehicle=vehicle, scenario=basic_scenario, calculation_year_index=year_index, total_mileage_km=0)
    assert calculated_cost == pytest.approx(expected_cost, abs=1e-2)

def test_maintenance_cost_diesel(basic_scenario):
    component = MaintenanceCost()
    vehicle = basic_scenario.diesel_vehicle # vehicle_type is 'rigid_diesel'
    year_index = 5
    # Use updated attribute name and structure
    maint_details = basic_scenario.maintenance_costs_detailed.costs_by_type['rigid_diesel']
     # Use updated attribute names within MaintenanceDetail
    base_avg = (maint_details.annual_cost_min_aud + maint_details.annual_cost_max_aud) / 2.0
    # Use updated attribute name and scale
    increase_rate_fraction = basic_scenario.general_cost_increase_rates.maintenance_annual_increase_rate_percent / 100.0
    expected_cost = base_avg * (1 + increase_rate_fraction) ** year_index
    calculated_cost = component.calculate_annual_cost(year=basic_scenario.analysis_start_year + year_index, vehicle=vehicle, scenario=basic_scenario, calculation_year_index=year_index, total_mileage_km=0)
    assert calculated_cost == pytest.approx(expected_cost, abs=1e-2)

def test_maintenance_cost_missing_detail(basic_scenario, mock_vehicle_instance):
    component = MaintenanceCost()
    # Mock vehicle uses MockMaintenanceStrategy. The strategy itself handles missing details (if needed).
    # This test now just checks that the component correctly calls the strategy and applies the increase rate.
    expected_base_cost = mock_vehicle_instance.maintenance_strategy.calculate_base_annual_cost(mock_vehicle_instance, basic_scenario)
    year_index = 2
    increase_rate_percent = basic_scenario.general_cost_increase_rates.maintenance_annual_increase_rate_percent
    increase_factor = (1 + (increase_rate_percent / 100.0)) ** year_index
    expected_adjusted_cost = expected_base_cost * increase_factor

    # Use the mock vehicle instance
    cost = component.calculate_annual_cost(
        year=basic_scenario.analysis_start_year + year_index,
        vehicle=mock_vehicle_instance,
        scenario=basic_scenario,
        calculation_year_index=year_index,
        total_mileage_km=0
    )
    assert cost == pytest.approx(expected_adjusted_cost)
    # No need to check for specific log messages here, as that's the strategy's responsibility.


# 4. Infrastructure Cost
def test_infrastructure_cost_diesel(basic_scenario):
    component = InfrastructureCost()
    cost = component.calculate_annual_cost(year=basic_scenario.analysis_start_year, vehicle=basic_scenario.diesel_vehicle, scenario=basic_scenario, calculation_year_index=0, total_mileage_km=0)
    assert cost == 0

def test_infrastructure_cost_electric_during_lifespan(basic_scenario):
    component = InfrastructureCost()
    # Use updated attribute names and scale
    base_maint_fraction = basic_scenario.infrastructure_costs.charger_maintenance_annual_rate_percent / 100.0
    capital_cost = basic_scenario.infrastructure_costs.selected_charger_cost_aud + basic_scenario.infrastructure_costs.selected_installation_cost_aud
    base_maint = capital_cost * base_maint_fraction
    maint_increase_rate_fraction = basic_scenario.general_cost_increase_rates.maintenance_annual_increase_rate_percent / 100.0 # Uses general maintenance increase
    year_index = 5
    maintenance_cost = base_maint * (1 + maint_increase_rate_fraction) ** year_index

    # Calculate amortized capital cost
    lifespan = basic_scenario.infrastructure_costs.charger_lifespan_years # Updated name
    amortized_capital = capital_cost / lifespan if lifespan > 0 else 0

    expected_cost = amortized_capital + maintenance_cost

    calculated_cost = component.calculate_annual_cost(year=basic_scenario.analysis_start_year + year_index, vehicle=basic_scenario.electric_vehicle, scenario=basic_scenario, calculation_year_index=year_index, total_mileage_km=0)
    assert calculated_cost == pytest.approx(expected_cost, abs=1e-2)

def test_infrastructure_cost_electric_after_lifespan(basic_scenario):
    component = InfrastructureCost()
    # Use updated attribute name
    charger_lifespan = basic_scenario.infrastructure_costs.charger_lifespan_years
    year_index_after = charger_lifespan
    # Calculation should return 0 after the charger lifespan expires
    cost = component.calculate_annual_cost(year=basic_scenario.analysis_start_year + year_index_after, vehicle=basic_scenario.electric_vehicle, scenario=basic_scenario, calculation_year_index=year_index_after, total_mileage_km=0)
    assert cost == 0.0

def test_infrastructure_cost_zero_lifespan(basic_scenario):
    component = InfrastructureCost()
    # Create updated InfrastructureCosts object
    zero_lifespan_infra = basic_scenario.infrastructure_costs.model_copy(update={'charger_lifespan_years': 0})
    mod_scenario = basic_scenario.model_copy(update={"infrastructure_costs": zero_lifespan_infra})

    # Capital cost amortization is 0 if lifespan is 0.
    # Maintenance cost should still apply in year 0.
    base_maint_fraction = mod_scenario.infrastructure_costs.charger_maintenance_annual_rate_percent / 100.0
    capital_cost = mod_scenario.infrastructure_costs.selected_charger_cost_aud + mod_scenario.infrastructure_costs.selected_installation_cost_aud
    base_maint = capital_cost * base_maint_fraction
    maint_increase_rate_fraction = mod_scenario.general_cost_increase_rates.maintenance_annual_increase_rate_percent / 100.0
    expected_cost_y0 = base_maint * (1 + maint_increase_rate_fraction) ** 0

    cost_y0 = component.calculate_annual_cost(year=mod_scenario.analysis_start_year, vehicle=mod_scenario.electric_vehicle, scenario=mod_scenario, calculation_year_index=0, total_mileage_km=0)
    assert cost_y0 == pytest.approx(expected_cost_y0)


# 5. Battery Replacement Cost
def test_battery_replacement_diesel(basic_scenario):
    component = BatteryReplacementCost()
    cost = component.calculate_annual_cost(year=basic_scenario.analysis_start_year + 5, vehicle=basic_scenario.diesel_vehicle, scenario=basic_scenario, calculation_year_index=5, total_mileage_km=0)
    assert cost == 0

def test_battery_replacement_disabled(basic_scenario):
    # Update the nested config object
    mod_config = basic_scenario.battery_replacement_config.model_copy(update={"enable_battery_replacement": False})
    mod_scenario = basic_scenario.model_copy(update={"battery_replacement_config": mod_config})
    component = BatteryReplacementCost()
    cost = component.calculate_annual_cost(year=mod_scenario.analysis_start_year + 5, vehicle=mod_scenario.electric_vehicle, scenario=mod_scenario, calculation_year_index=5, total_mileage_km=0)
    assert cost == 0

def test_battery_replacement_fixed_year(basic_scenario):
    replacement_year_index = 5 # Force replacement in the 6th year (index 5)
    # Update nested config
    mod_config = basic_scenario.battery_replacement_config.model_copy(update={
        "force_replacement_year_index": replacement_year_index
    })
    mod_scenario = basic_scenario.model_copy(update={
        "battery_replacement_config": mod_config,
        "analysis_start_year": 2025 # Keep for clarity
    })
    # Modify the vehicle IN THE COPIED SCENARIO to have a shorter warranty
    mod_scenario.electric_vehicle.battery_warranty_years = 4 # Warranty expires before replacement index (5)

    component = BatteryReplacementCost()
    annual_mileage = mod_scenario.operational_parameters.annual_mileage_km

    # Check non-triggering years
    for i in range(replacement_year_index):
        cost = component.calculate_annual_cost(
            year=mod_scenario.analysis_start_year + i,
            vehicle=mod_scenario.electric_vehicle,
            scenario=mod_scenario,
            calculation_year_index=i,
            total_mileage_km=i * annual_mileage # Pass cumulative mileage
        )
        assert cost == 0.0, f"Cost should be 0 in year index {i}"

    # Check triggering year
    replacement_calendar_year = mod_scenario.analysis_start_year + replacement_year_index # Should be 2030
    # get_battery_cost_per_kwh expects the *calendar* year
    cost_per_kwh = get_battery_cost_per_kwh(replacement_calendar_year, mod_scenario, mod_scenario.electric_vehicle)
    expected_cost = mod_scenario.electric_vehicle.battery_capacity_kwh * cost_per_kwh

    calculated_cost = component.calculate_annual_cost(
        year=replacement_calendar_year,
        vehicle=mod_scenario.electric_vehicle,
        scenario=mod_scenario,
        calculation_year_index=replacement_year_index,
        total_mileage_km=replacement_year_index * annual_mileage # Cumulative mileage up to *start* of trigger year
    )
    assert calculated_cost == pytest.approx(expected_cost)

    # Check year after replacement (should be 0)
    cost_after = component.calculate_annual_cost(
        year=replacement_calendar_year + 1,
        vehicle=mod_scenario.electric_vehicle,
        scenario=mod_scenario,
        calculation_year_index=replacement_year_index + 1,
        total_mileage_km=(replacement_year_index + 1) * annual_mileage
    )
    assert cost_after == 0.0, "Cost should be 0 after replacement year"


def test_battery_replacement_threshold(basic_scenario):
    threshold = 0.75 # Scale 0-1
    trigger_year_index = 4 # Assume degradation drops below threshold in the 5th year (index 4)
    # Update nested config
    mod_config = basic_scenario.battery_replacement_config.model_copy(update={
        "replacement_threshold_fraction": threshold, # Updated name
        "force_replacement_year_index": None # Ensure fixed year is off
    })
    mod_scenario = basic_scenario.model_copy(update={
        "battery_replacement_config": mod_config,
        "analysis_start_year": 2025
    })
    # Modify the vehicle IN THE COPIED SCENARIO to have a shorter warranty
    mod_scenario.electric_vehicle.battery_warranty_years = 3 # Warranty expires before replacement index (4)

    component = BatteryReplacementCost()
    annual_mileage = mod_scenario.operational_parameters.annual_mileage_km

    # Mock the degradation calculation
    with patch.object(mod_scenario.electric_vehicle, 'calculate_battery_degradation_factor') as mock_degrade:
        def side_effect(age_years, total_mileage_km):
            # Degradation is checked at the *start* of the year index, for that age.
            # Year index 4 corresponds to age_years=5.
            if age_years == trigger_year_index + 1: # Check for age 5 (start of year index 4)
                return threshold - 0.01 # Below threshold
            else:
                return threshold + 0.1 # Above threshold
        mock_degrade.side_effect = side_effect

        # Simulate years leading up to replacement
        cumulative_mileage = 0.0
        for i in range(trigger_year_index):
            cost = component.calculate_annual_cost(
                year=mod_scenario.analysis_start_year + i,
                vehicle=mod_scenario.electric_vehicle,
                scenario=mod_scenario,
                calculation_year_index=i,
                total_mileage_km=cumulative_mileage
            )
            assert cost == 0.0, f"Cost should be 0 in year index {i}"
            cumulative_mileage += annual_mileage # Accumulate mileage

        # Check triggering year (year index 4, calendar year 2029)
        replacement_calendar_year = mod_scenario.analysis_start_year + trigger_year_index

        # Verify degradation check works as expected before cost calculation
        # At the start of year index 4, vehicle age is 5
        degradation = mod_scenario.electric_vehicle.calculate_battery_degradation_factor(
             age_years = trigger_year_index + 1, # Age is index + 1
             total_mileage_km=cumulative_mileage # Mileage *before* current year
        )
        assert degradation < threshold # Verify mock setup is correct

        cost_per_kwh = get_battery_cost_per_kwh(replacement_calendar_year, mod_scenario, mod_scenario.electric_vehicle)
        expected_cost = mod_scenario.electric_vehicle.battery_capacity_kwh * cost_per_kwh

        calculated_cost = component.calculate_annual_cost(
            year=replacement_calendar_year,
            vehicle=mod_scenario.electric_vehicle,
            scenario=mod_scenario,
            calculation_year_index=trigger_year_index,
            total_mileage_km=cumulative_mileage # Pass cumulative mileage up to start of year
        )
        assert calculated_cost == pytest.approx(expected_cost)
        cumulative_mileage += annual_mileage # Update mileage after cost calc

        # Check year after replacement (should be 0)
        cost_after = component.calculate_annual_cost(
            year=replacement_calendar_year + 1,
            vehicle=mod_scenario.electric_vehicle,
            scenario=mod_scenario,
            calculation_year_index=trigger_year_index + 1,
            total_mileage_km=cumulative_mileage
        )
        assert cost_after == 0.0, "Cost should be 0 after replacement year"

def test_battery_replacement_warranty_trigger(basic_scenario):
    threshold = 0.75 # Scale 0-1
    warranty_years = basic_scenario.electric_vehicle.battery_warranty_years # Should be 8
    # Update nested config
    mod_config = basic_scenario.battery_replacement_config.model_copy(update={
        "replacement_threshold_fraction": threshold,
        "force_replacement_year_index": None
    })
    mod_scenario = basic_scenario.model_copy(update={"battery_replacement_config": mod_config})
    annual_mileage = mod_scenario.operational_parameters.annual_mileage_km

    with patch.object(mod_scenario.electric_vehicle, 'calculate_battery_degradation_factor') as mock_degrade:
        def side_effect(age_years, total_mileage_km):
            # Simulate degradation below threshold always
            return threshold - 0.01
        mock_degrade.side_effect = side_effect

        # Replacement should trigger the year *after* warranty ends, if degradation is low
        # Warranty ends *after* year index 7 (age 8). Trigger check happens at start of year index 8 (age 9)
        trigger_year_index = warranty_years

        # Check year *before* warranty ends (should be 0)
        cost_before = BatteryReplacementCost().calculate_annual_cost(
             year=mod_scenario.analysis_start_year + trigger_year_index - 1,
             vehicle=mod_scenario.electric_vehicle,
             scenario=mod_scenario,
             calculation_year_index=trigger_year_index - 1,
             total_mileage_km=(trigger_year_index - 1) * annual_mileage
        )
        assert cost_before == 0.0

        replacement_calendar_year = mod_scenario.analysis_start_year + trigger_year_index # Year 2025 + 8 = 2033
        cost_per_kwh = get_battery_cost_per_kwh(replacement_calendar_year, mod_scenario, mod_scenario.electric_vehicle)
        expected_cost = mod_scenario.electric_vehicle.battery_capacity_kwh * cost_per_kwh # 65 * 100 = 6500 (using 2030 projection value)

        calculated_cost = BatteryReplacementCost().calculate_annual_cost(
            year=replacement_calendar_year,
            vehicle=mod_scenario.electric_vehicle,
            scenario=mod_scenario,
            calculation_year_index=trigger_year_index,
            total_mileage_km=trigger_year_index * annual_mileage
        )
        assert calculated_cost == pytest.approx(expected_cost)


# 6. Insurance Cost
def test_insurance_cost_electric(basic_scenario):
    component = InsuranceCost()
    vehicle = basic_scenario.electric_vehicle
    year_index = 2
    # Use updated attribute names and structure
    base_cost = basic_scenario.insurance_registration_costs.electric.base_annual_cost_aud
    increase_rate_fraction = basic_scenario.general_cost_increase_rates.insurance_annual_increase_rate_percent / 100.0
    expected_cost = base_cost * (1 + increase_rate_fraction) ** year_index
    # Assume percentage rate is 0 for this test based on fixture setup
    calculated_cost = component.calculate_annual_cost(year=basic_scenario.analysis_start_year + year_index, vehicle=vehicle, scenario=basic_scenario, calculation_year_index=year_index, total_mileage_km=0)
    assert calculated_cost == pytest.approx(expected_cost, abs=1e-2)

def test_insurance_cost_diesel(basic_scenario):
    component = InsuranceCost()
    vehicle = basic_scenario.diesel_vehicle
    year_index = 4
     # Use updated attribute names and structure
    base_cost = basic_scenario.insurance_registration_costs.diesel.base_annual_cost_aud
    increase_rate_fraction = basic_scenario.general_cost_increase_rates.insurance_annual_increase_rate_percent / 100.0
    expected_cost = base_cost * (1 + increase_rate_fraction) ** year_index
    # Assume percentage rate is 0
    calculated_cost = component.calculate_annual_cost(year=basic_scenario.analysis_start_year + year_index, vehicle=vehicle, scenario=basic_scenario, calculation_year_index=year_index, total_mileage_km=0)
    assert calculated_cost == pytest.approx(expected_cost, abs=1e-2)

def test_insurance_cost_missing_detail(basic_scenario, mock_vehicle_instance):
    component = InsuranceCost()
    # Modify the scenario to remove details for one type (e.g., electric)
    mod_insurance_costs = InsuranceRegistrationCosts(
        diesel=basic_scenario.insurance_registration_costs.diesel # Keep diesel
        # electric=... is omitted
    )
    mod_scenario = basic_scenario.model_copy(update={"insurance_registration_costs": mod_insurance_costs})

    # Test with the electric vehicle, whose details are now missing
    with patch('logging.warning') as mock_warning:
        cost = component.calculate_annual_cost(
            year=basic_scenario.analysis_start_year,
            vehicle=basic_scenario.electric_vehicle, # Use EV
            scenario=mod_scenario,
            calculation_year_index=0,
            total_mileage_km=0
        )
        assert cost == 0.0
        # Check if a warning was logged
        mock_warning.assert_called_once_with(
             "Insurance details not found for vehicle type 'electric'. Returning 0 cost."
        )


# 7. Registration Cost
def test_registration_cost(basic_scenario):
    component = RegistrationCost()
    year_index = 4
    # Use updated attribute name and scale
    increase_rate_fraction = basic_scenario.general_cost_increase_rates.registration_annual_increase_rate_percent / 100.0

    # Test EV
    ev_vehicle = basic_scenario.electric_vehicle
    ev_base = ev_vehicle.base_registration_cost_aud # Use updated vehicle attribute
    expected_ev_cost = ev_base * (1 + increase_rate_fraction) ** year_index
    calculated_ev_cost = component.calculate_annual_cost(year=basic_scenario.analysis_start_year + year_index, vehicle=ev_vehicle, scenario=basic_scenario, calculation_year_index=year_index, total_mileage_km=0)
    assert calculated_ev_cost == pytest.approx(expected_ev_cost, abs=1e-2)

    # Test Diesel
    dv_vehicle = basic_scenario.diesel_vehicle
    diesel_base = dv_vehicle.base_registration_cost_aud # Use updated vehicle attribute
    expected_diesel_cost = diesel_base * (1 + increase_rate_fraction) ** year_index
    calculated_diesel_cost = component.calculate_annual_cost(year=basic_scenario.analysis_start_year + year_index, vehicle=dv_vehicle, scenario=basic_scenario, calculation_year_index=year_index, total_mileage_km=0)
    assert calculated_diesel_cost == pytest.approx(expected_diesel_cost, abs=1e-2)


# 8. Residual Value
def test_residual_value_before_final_year(basic_scenario):
    component = ResidualValue()
    # Use updated attribute name
    non_final_year_index = basic_scenario.analysis_period_years - 2
    cost = component.calculate_annual_cost(year=basic_scenario.analysis_start_year + non_final_year_index, vehicle=basic_scenario.electric_vehicle, scenario=basic_scenario, calculation_year_index=non_final_year_index, total_mileage_km=0)
    assert cost == 0

def test_residual_value_final_year_electric(basic_scenario):
    component = ResidualValue()
     # Use updated attribute name
    final_year_index = basic_scenario.analysis_period_years - 1
    vehicle_age_at_end = basic_scenario.analysis_period_years
    # Use updated method name
    expected_value = basic_scenario.electric_vehicle.calculate_residual_value_aud(vehicle_age_at_end)
    calculated_value = component.calculate_annual_cost(year=basic_scenario.analysis_start_year + final_year_index, vehicle=basic_scenario.electric_vehicle, scenario=basic_scenario, calculation_year_index=final_year_index, total_mileage_km=0)
    # Residual value is negative cost
    assert calculated_value == pytest.approx(-expected_value)

def test_residual_value_final_year_diesel(basic_scenario):
    component = ResidualValue()
    # Use updated attribute name
    final_year_index = basic_scenario.analysis_period_years - 1
    vehicle_age_at_end = basic_scenario.analysis_period_years
    # Use updated method name
    expected_value = basic_scenario.diesel_vehicle.calculate_residual_value_aud(vehicle_age_at_end)
    calculated_value = component.calculate_annual_cost(year=basic_scenario.analysis_start_year + final_year_index, vehicle=basic_scenario.diesel_vehicle, scenario=basic_scenario, calculation_year_index=final_year_index, total_mileage_km=0)
    # Residual value is negative cost
    assert calculated_value == pytest.approx(-expected_value)


# 9. Carbon Tax Cost
def test_carbon_tax_cost_electric(basic_scenario):
    component = CarbonTaxCost()
    cost = component.calculate_annual_cost(year=basic_scenario.analysis_start_year, vehicle=basic_scenario.electric_vehicle, scenario=basic_scenario, calculation_year_index=0, total_mileage_km=0)
    assert cost == 0

def test_carbon_tax_cost_diesel(basic_scenario):
    component = CarbonTaxCost()
    vehicle = basic_scenario.diesel_vehicle
    year_index = 3
    # Use updated attribute name
    annual_mileage = basic_scenario.operational_parameters.annual_mileage_km
    fuel_consumption_l = vehicle.calculate_energy_consumption(annual_mileage)
    # Use updated attribute name
    emission_factor_kg_per_l = vehicle.co2_emission_factor_kg_per_l
    # Use updated attribute name and structure
    base_tax_rate_per_tonne = basic_scenario.carbon_tax_config.initial_rate_aud_per_tonne_co2e
    # Use updated attribute name, structure, and scale
    increase_rate_fraction = basic_scenario.carbon_tax_config.annual_increase_rate_percent / 100.0
    # Calculate current tax rate based on base and increase
    current_tax_rate = base_tax_rate_per_tonne * (1 + increase_rate_fraction) ** year_index
    # Emission factor is kg/L, rate is AUD/tonne. Convert emission factor to tonne/L.
    emission_factor_tonne_per_l = emission_factor_kg_per_l / 1000.0
    expected_cost = fuel_consumption_l * emission_factor_tonne_per_l * current_tax_rate

    calculated_cost = component.calculate_annual_cost(year=basic_scenario.analysis_start_year + year_index, vehicle=vehicle, scenario=basic_scenario, calculation_year_index=year_index, total_mileage_km=0)
    assert calculated_cost == pytest.approx(expected_cost, abs=1e-2)

def test_carbon_tax_cost_disabled(basic_scenario):
    component = CarbonTaxCost()
    # Update nested config flag
    mod_config = basic_scenario.carbon_tax_config.model_copy(update={"include_carbon_tax": False})
    mod_scenario = basic_scenario.model_copy(update={"carbon_tax_config": mod_config})
    cost = component.calculate_annual_cost(year=mod_scenario.analysis_start_year, vehicle=mod_scenario.diesel_vehicle, scenario=mod_scenario, calculation_year_index=0, total_mileage_km=0)
    assert cost == 0


# 10. Road User Charge Cost
def test_road_user_charge(basic_scenario):
    component = RoadUserChargeCost()
    vehicle = basic_scenario.electric_vehicle # RUC applies to all typically
    year_index = 6
    # Use updated attribute name and structure
    base_charge = basic_scenario.road_user_charge_config.initial_charge_aud_per_km
    # Use updated attribute name, structure, and scale
    increase_rate_fraction = basic_scenario.road_user_charge_config.annual_increase_rate_percent / 100.0
    current_charge = base_charge * (1 + increase_rate_fraction) ** year_index
    # Use updated attribute name
    annual_mileage = basic_scenario.operational_parameters.annual_mileage_km
    expected_cost = annual_mileage * current_charge
    calculated_cost = component.calculate_annual_cost(year=basic_scenario.analysis_start_year + year_index, vehicle=vehicle, scenario=basic_scenario, calculation_year_index=year_index, total_mileage_km=0)
    assert calculated_cost == pytest.approx(expected_cost, abs=1e-2)

def test_road_user_charge_disabled(basic_scenario):
    component = RoadUserChargeCost()
    # Update nested config flag
    mod_config = basic_scenario.road_user_charge_config.model_copy(update={"include_road_user_charge": False})
    mod_scenario = basic_scenario.model_copy(update={"road_user_charge_config": mod_config})
    cost = component.calculate_annual_cost(year=mod_scenario.analysis_start_year, vehicle=mod_scenario.electric_vehicle, scenario=mod_scenario, calculation_year_index=0, total_mileage_km=0)
    assert cost == 0 