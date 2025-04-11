import pytest
import math
import numpy as np
from unittest.mock import MagicMock # For mocking vehicle methods if needed

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
    ResidualValue
)

# Import dependencies needed for components
from tco_model.scenarios import Scenario
from tco_model.vehicles import Vehicle, ElectricVehicle, DieselVehicle

# --- Helper Mock Vehicle Class ---
class MockVehicle(Vehicle):
    """A basic mock vehicle for testing unsupported types."""
    def __init__(self): 
        super().__init__(name="Mock", purchase_price=1, annual_mileage=1) # Basic init
    # Add dummy implementations for abstract/required methods if any
    def calculate_energy_consumption(self, distance_km: float) -> float:
        return 0.0
    def calculate_residual_value(self, age_years: int) -> float:
        return 0.0

# --- Re-use Fixtures from other test files (or redefine if needed) ---
# It might be cleaner to define specific fixtures here tailored for component tests
# or import them if the testing structure supports it easily.
# For now, let's redefine simplified versions here.

@pytest.fixture
def sample_scenario_params():
    """Provides a dictionary of parameters for a sample Scenario."""
    start_year = 2025
    end_year = 2030 # Shorter period for simpler testing
    analysis_period = end_year - start_year + 1
    return {
        "name": "Component Test Scenario",
        "start_year": start_year,
        "end_year": end_year,
        "discount_rate": 0.05,
        "inflation_rate": 0.02,
        "financing_method": "loan", # Default to loan for testing acquisition
        "loan_term": 5,
        "interest_rate": 0.06,
        "down_payment_pct": 0.2,
        "annual_mileage": 50000.0,
        "electricity_prices": {str(y): 0.20 + 0.01 * (y - start_year) for y in range(start_year, end_year + 1)},
        "diesel_prices": {str(y): 1.80 + 0.02 * (y - start_year) for y in range(start_year, end_year + 1)},
        "charger_cost": 40000.0,
        "charger_installation_cost": 10000.0,
        "charger_lifespan": 10,
        "electric_maintenance_cost_per_km": 0.07,
        "diesel_maintenance_cost_per_km": 0.14,
        "electric_insurance_cost_factor": 1.1,
        "diesel_insurance_cost_factor": 1.0,
        "annual_registration_cost": 4500.0,
        "enable_battery_replacement": True, # Enable for testing
        "battery_replacement_year": 2028, # Example fixed year
        "battery_replacement_threshold": 0.7, # Example threshold
        # Add required vehicle params even though vehicle objects are separate
        "electric_vehicle_name": "Test EV",
        "electric_vehicle_price": 350000.0,
        "electric_vehicle_battery_capacity": 250.0,
        "electric_vehicle_energy_consumption": 0.8,
        "electric_vehicle_battery_warranty": 8,
        "electric_residual_value_pct": 0.15,
        "diesel_vehicle_name": "Test Diesel",
        "diesel_vehicle_price": 180000.0,
        "diesel_vehicle_fuel_consumption": 28.0,
        "diesel_residual_value_pct": 0.12
    }

@pytest.fixture
def sample_scenario(sample_scenario_params):
    """Creates a sample Scenario instance."""
    return Scenario(**sample_scenario_params)

@pytest.fixture
def sample_electric_vehicle(sample_scenario_params):
    """Creates a sample ElectricVehicle instance based on scenario params."""
    # Extract only relevant vehicle params
    ev_params = {
        "name": sample_scenario_params["electric_vehicle_name"],
        "purchase_price": sample_scenario_params["electric_vehicle_price"],
        "battery_capacity_kwh": sample_scenario_params["electric_vehicle_battery_capacity"],
        "energy_consumption_kwh_per_km": sample_scenario_params["electric_vehicle_energy_consumption"],
        "battery_warranty_years": sample_scenario_params["electric_vehicle_battery_warranty"],
        "annual_mileage": sample_scenario_params["annual_mileage"],
        "lifespan": sample_scenario_params["end_year"] - sample_scenario_params["start_year"] + 1, # Match scenario length
        "residual_value_pct": sample_scenario_params["electric_residual_value_pct"]
    }
    return ElectricVehicle(**ev_params)

@pytest.fixture
def sample_diesel_vehicle(sample_scenario_params):
    """Creates a sample DieselVehicle instance based on scenario params."""
    dv_params = {
        "name": sample_scenario_params["diesel_vehicle_name"],
        "purchase_price": sample_scenario_params["diesel_vehicle_price"],
        "fuel_consumption_l_per_100km": sample_scenario_params["diesel_vehicle_fuel_consumption"],
        "annual_mileage": sample_scenario_params["annual_mileage"],
        "lifespan": sample_scenario_params["end_year"] - sample_scenario_params["start_year"] + 1,
        "residual_value_pct": sample_scenario_params["diesel_residual_value_pct"]
    }
    return DieselVehicle(**dv_params)

# --- Component Instance Fixtures --- 
@pytest.fixture
def acquisition_cost(): return AcquisitionCost()

@pytest.fixture
def energy_cost(): return EnergyCost()

@pytest.fixture
def maintenance_cost(): return MaintenanceCost()

@pytest.fixture
def infrastructure_cost(): return InfrastructureCost()

@pytest.fixture
def battery_replacement_cost(): return BatteryReplacementCost()

@pytest.fixture
def insurance_cost(): return InsuranceCost()

@pytest.fixture
def registration_cost(): return RegistrationCost()

@pytest.fixture
def residual_value(): return ResidualValue()

# --- Test Cases Start Here --- 

# --- AcquisitionCost Tests ---

def test_acquisition_cash(acquisition_cost, sample_electric_vehicle, sample_scenario):
    """Test acquisition cost calculation for cash payment."""
    # Modify scenario for cash payment
    scenario = sample_scenario.with_modifications(financing_method='cash')
    price = sample_electric_vehicle.purchase_price
    
    # Cost should be full price in year 0 (index 0)
    cost_y0 = acquisition_cost.calculate_annual_cost(scenario.start_year, sample_electric_vehicle, scenario, 0, 0)
    assert math.isclose(cost_y0, price)
    
    # Cost should be 0 in subsequent years
    cost_y1 = acquisition_cost.calculate_annual_cost(scenario.start_year + 1, sample_electric_vehicle, scenario, 1, scenario.annual_mileage)
    assert cost_y1 == 0.0
    cost_y5 = acquisition_cost.calculate_annual_cost(scenario.start_year + 5, sample_electric_vehicle, scenario, 5, scenario.annual_mileage * 5)
    assert cost_y5 == 0.0

def test_acquisition_loan(acquisition_cost, sample_diesel_vehicle, sample_scenario):
    """Test acquisition cost calculation for loan payment."""
    # Use default scenario which has loan settings
    vehicle = sample_diesel_vehicle
    scenario = sample_scenario
    price = vehicle.purchase_price
    dp_pct = scenario.down_payment_pct
    loan_term = scenario.loan_term
    rate = scenario.interest_rate
    loan_amount = price * (1.0 - dp_pct)
    
    # Year 0 (index 0): Down payment
    expected_cost_y0 = price * dp_pct
    cost_y0 = acquisition_cost.calculate_annual_cost(scenario.start_year, vehicle, scenario, 0, 0)
    assert math.isclose(cost_y0, expected_cost_y0)
    
    # Year 1 to loan_term (index 1 to loan_term): Annual loan payment
    # Use numpy.pmt to calculate expected annual payment
    expected_annual_payment = -np.pmt(rate, loan_term, loan_amount)
    
    for i in range(1, loan_term + 1):
        year = scenario.start_year + i
        total_mileage = scenario.annual_mileage * i
        cost_yi = acquisition_cost.calculate_annual_cost(year, vehicle, scenario, i, total_mileage)
        assert math.isclose(cost_yi, expected_annual_payment, rel_tol=1e-7)

    # Year after loan_term (index loan_term + 1)
    cost_y_after = acquisition_cost.calculate_annual_cost(scenario.start_year + loan_term + 1, vehicle, scenario, loan_term + 1, 0)
    assert cost_y_after == 0.0

def test_acquisition_loan_zero_interest(acquisition_cost, sample_electric_vehicle, sample_scenario):
    """Test acquisition cost calculation for loan with zero interest."""
    scenario = sample_scenario.with_modifications(interest_rate=0.0)
    vehicle = sample_electric_vehicle
    price = vehicle.purchase_price
    dp_pct = scenario.down_payment_pct
    loan_term = scenario.loan_term
    loan_amount = price * (1.0 - dp_pct)

    # Year 0: Down payment (same as before)
    expected_cost_y0 = price * dp_pct
    cost_y0 = acquisition_cost.calculate_annual_cost(scenario.start_year, vehicle, scenario, 0, 0)
    assert math.isclose(cost_y0, expected_cost_y0)

    # Year 1 to loan_term: Annual payment is simply loan amount / term
    expected_annual_payment = loan_amount / loan_term
    for i in range(1, loan_term + 1):
        year = scenario.start_year + i
        cost_yi = acquisition_cost.calculate_annual_cost(year, vehicle, scenario, i, 0)
        assert math.isclose(cost_yi, expected_annual_payment)

    # Year after loan_term
    cost_y_after = acquisition_cost.calculate_annual_cost(scenario.start_year + loan_term + 1, vehicle, scenario, loan_term + 1, 0)
    assert cost_y_after == 0.0

def test_acquisition_unsupported_method(acquisition_cost, sample_electric_vehicle, sample_scenario):
    """Test that an unsupported financing method raises ValueError."""
    scenario = sample_scenario.with_modifications(financing_method='lease') # Unsupported
    with pytest.raises(ValueError) as excinfo:
        acquisition_cost.calculate_annual_cost(scenario.start_year, sample_electric_vehicle, scenario, 0, 0)
    assert "Unsupported financing method" in str(excinfo.value)

# --- EnergyCost Tests ---

def test_energy_cost_electric(energy_cost, sample_electric_vehicle, sample_scenario):
    """Test energy cost calculation for ElectricVehicle."""
    vehicle = sample_electric_vehicle
    scenario = sample_scenario
    year = scenario.start_year + 2 # Example year
    calc_year_index = 2
    total_mileage = scenario.annual_mileage * calc_year_index
    
    # Expected calculation: annual_mileage * consumption_per_km * price_for_year
    price_kwh = scenario.electricity_prices[str(year)]
    expected_cost = scenario.annual_mileage * vehicle.energy_consumption_kwh_per_km * price_kwh
    
    calculated_cost = energy_cost.calculate_annual_cost(year, vehicle, scenario, calc_year_index, total_mileage)
    assert math.isclose(calculated_cost, expected_cost)

def test_energy_cost_diesel(energy_cost, sample_diesel_vehicle, sample_scenario):
    """Test energy cost calculation for DieselVehicle."""
    vehicle = sample_diesel_vehicle
    scenario = sample_scenario
    year = scenario.start_year + 3 # Example year
    calc_year_index = 3
    total_mileage = scenario.annual_mileage * calc_year_index
    
    # Expected calculation: annual_mileage * consumption_per_km * price_for_year
    price_l = scenario.diesel_prices[str(year)]
    expected_cost = scenario.annual_mileage * vehicle.fuel_consumption_l_per_km * price_l
    
    calculated_cost = energy_cost.calculate_annual_cost(year, vehicle, scenario, calc_year_index, total_mileage)
    assert math.isclose(calculated_cost, expected_cost)

def test_energy_cost_missing_price(energy_cost, sample_electric_vehicle, sample_scenario):
    """Test ValueError if energy price for the year is missing."""
    vehicle = sample_electric_vehicle
    scenario = sample_scenario
    invalid_year = scenario.end_year + 5 # Year outside the defined price range
    
    with pytest.raises(ValueError) as excinfo:
        energy_cost.calculate_annual_cost(invalid_year, vehicle, scenario, 10, 0) 
    assert f"Electricity price for year {invalid_year} not found" in str(excinfo.value)

    # Test for Diesel too
    vehicle_diesel = sample_diesel_vehicle
    with pytest.raises(ValueError) as excinfo_diesel:
        energy_cost.calculate_annual_cost(invalid_year, vehicle_diesel, scenario, 10, 0)
    assert f"Diesel price for year {invalid_year} not found" in str(excinfo_diesel.value)


def test_energy_cost_unsupported_vehicle(energy_cost, sample_scenario):
    """Test TypeError for unsupported vehicle types."""
    # Use the module-level MockVehicle
    mock_vehicle = MockVehicle()
    with pytest.raises(TypeError) as excinfo:
        energy_cost.calculate_annual_cost(sample_scenario.start_year, mock_vehicle, sample_scenario, 0, 0)
    assert "Vehicle type not supported" in str(excinfo.value)

# --- MaintenanceCost Tests ---

def test_maintenance_cost_electric(maintenance_cost, sample_electric_vehicle, sample_scenario):
    """Test maintenance cost calculation for ElectricVehicle."""
    vehicle = sample_electric_vehicle
    scenario = sample_scenario
    year = scenario.start_year + 1
    calc_year_index = 1
    total_mileage = scenario.annual_mileage * calc_year_index
    
    # Expected: annual_mileage * electric_maintenance_cost_per_km
    expected_cost = scenario.annual_mileage * scenario.electric_maintenance_cost_per_km
    
    calculated_cost = maintenance_cost.calculate_annual_cost(year, vehicle, scenario, calc_year_index, total_mileage)
    assert math.isclose(calculated_cost, expected_cost)

def test_maintenance_cost_diesel(maintenance_cost, sample_diesel_vehicle, sample_scenario):
    """Test maintenance cost calculation for DieselVehicle."""
    vehicle = sample_diesel_vehicle
    scenario = sample_scenario
    year = scenario.start_year + 1
    calc_year_index = 1
    total_mileage = scenario.annual_mileage * calc_year_index
    
    # Expected: annual_mileage * diesel_maintenance_cost_per_km
    expected_cost = scenario.annual_mileage * scenario.diesel_maintenance_cost_per_km
    
    calculated_cost = maintenance_cost.calculate_annual_cost(year, vehicle, scenario, calc_year_index, total_mileage)
    assert math.isclose(calculated_cost, expected_cost)

def test_maintenance_cost_unsupported_vehicle(maintenance_cost, sample_scenario):
    """Test TypeError for unsupported vehicle types."""
    # Use the module-level MockVehicle
    mock_vehicle = MockVehicle()
    with pytest.raises(TypeError) as excinfo:
        maintenance_cost.calculate_annual_cost(sample_scenario.start_year, mock_vehicle, sample_scenario, 0, 0)
    assert "Vehicle type not supported" in str(excinfo.value)

# --- InfrastructureCost Tests ---

def test_infrastructure_cost_diesel(infrastructure_cost, sample_diesel_vehicle, sample_scenario):
    """Test infrastructure cost is zero for DieselVehicle."""
    cost = infrastructure_cost.calculate_annual_cost(sample_scenario.start_year, sample_diesel_vehicle, sample_scenario, 0, 0)
    assert cost == 0.0

def test_infrastructure_cost_electric_during_lifespan(infrastructure_cost, sample_electric_vehicle, sample_scenario):
    """Test amortized infrastructure cost during charger lifespan for EV."""
    vehicle = sample_electric_vehicle
    scenario = sample_scenario
    total_infra_cost = scenario.charger_cost + scenario.charger_installation_cost
    lifespan = scenario.charger_lifespan
    expected_annual_cost = total_infra_cost / lifespan
    
    # Test first year (index 0)
    cost_y0 = infrastructure_cost.calculate_annual_cost(scenario.start_year, vehicle, scenario, 0, 0)
    assert math.isclose(cost_y0, expected_annual_cost)
    
    # Test mid-lifespan year (e.g., index 5)
    cost_y5 = infrastructure_cost.calculate_annual_cost(scenario.start_year + 5, vehicle, scenario, 5, 0)
    assert math.isclose(cost_y5, expected_annual_cost)
    
    # Test last year of lifespan (index lifespan - 1)
    cost_y_last = infrastructure_cost.calculate_annual_cost(scenario.start_year + lifespan - 1, vehicle, scenario, lifespan - 1, 0)
    assert math.isclose(cost_y_last, expected_annual_cost)

def test_infrastructure_cost_electric_after_lifespan(infrastructure_cost, sample_electric_vehicle, sample_scenario):
    """Test infrastructure cost is zero after charger lifespan for EV."""
    vehicle = sample_electric_vehicle
    scenario = sample_scenario
    lifespan = scenario.charger_lifespan
    
    # Test year right after lifespan ends (index lifespan)
    cost_y_after = infrastructure_cost.calculate_annual_cost(scenario.start_year + lifespan, vehicle, scenario, lifespan, 0)
    assert cost_y_after == 0.0
    
    # Test much later year
    cost_y_later = infrastructure_cost.calculate_annual_cost(scenario.start_year + lifespan + 5, vehicle, scenario, lifespan + 5, 0)
    assert cost_y_later == 0.0

def test_infrastructure_cost_zero_lifespan(infrastructure_cost, sample_electric_vehicle, sample_scenario):
    """Test infrastructure cost with zero lifespan (full cost in year 0)."""
    scenario = sample_scenario.with_modifications(charger_lifespan=0)
    vehicle = sample_electric_vehicle
    expected_cost_y0 = scenario.charger_cost + scenario.charger_installation_cost
    
    # Year 0
    cost_y0 = infrastructure_cost.calculate_annual_cost(scenario.start_year, vehicle, scenario, 0, 0)
    assert math.isclose(cost_y0, expected_cost_y0)
    
    # Year 1
    cost_y1 = infrastructure_cost.calculate_annual_cost(scenario.start_year + 1, vehicle, scenario, 1, 0)
    assert cost_y1 == 0.0

# --- BatteryReplacementCost Tests ---

# Placeholder cost used in the component
PLACEHOLDER_BATTERY_COST_PER_KWH = 100 

def test_battery_replacement_diesel(battery_replacement_cost, sample_diesel_vehicle, sample_scenario):
    """Test battery replacement cost is zero for DieselVehicle."""
    cost = battery_replacement_cost.calculate_annual_cost(sample_scenario.start_year, sample_diesel_vehicle, sample_scenario, 0, 0)
    assert cost == 0.0

def test_battery_replacement_disabled(battery_replacement_cost, sample_electric_vehicle, sample_scenario):
    """Test cost is zero for EV if replacement is disabled in scenario."""
    scenario = sample_scenario.with_modifications(enable_battery_replacement=False)
    vehicle = sample_electric_vehicle
    year = scenario.battery_replacement_year # Year it would trigger if enabled
    calc_year_index = year - scenario.start_year
    total_mileage = calc_year_index * scenario.annual_mileage
    
    cost = battery_replacement_cost.calculate_annual_cost(year, vehicle, scenario, calc_year_index, total_mileage)
    assert cost == 0.0

def test_battery_replacement_fixed_year(battery_replacement_cost, sample_electric_vehicle, sample_scenario):
    """Test cost is triggered at the fixed battery_replacement_year."""
    scenario = sample_scenario.with_modifications(battery_replacement_threshold=None) # Ensure only fixed year applies
    vehicle = sample_electric_vehicle
    replacement_year = scenario.battery_replacement_year
    calc_year_index = replacement_year - scenario.start_year
    total_mileage = calc_year_index * scenario.annual_mileage
    
    expected_cost = vehicle.battery_capacity_kwh * PLACEHOLDER_BATTERY_COST_PER_KWH
    
    # Test year before replacement
    cost_before = battery_replacement_cost.calculate_annual_cost(replacement_year - 1, vehicle, scenario, calc_year_index - 1, total_mileage - scenario.annual_mileage)
    assert cost_before == 0.0
    
    # Test replacement year
    cost_trigger = battery_replacement_cost.calculate_annual_cost(replacement_year, vehicle, scenario, calc_year_index, total_mileage)
    assert math.isclose(cost_trigger, expected_cost)
    
    # Test year after replacement (should be 0 due to simple one-replacement logic)
    cost_after = battery_replacement_cost.calculate_annual_cost(replacement_year + 1, vehicle, scenario, calc_year_index + 1, total_mileage + scenario.annual_mileage)
    assert cost_after == 0.0

def test_battery_replacement_threshold(battery_replacement_cost, sample_electric_vehicle, sample_scenario):
    """Test cost is triggered when degradation threshold is met."""
    # Set fixed year to None, rely only on threshold
    replacement_threshold = 0.75 # Use a slightly different threshold for clarity
    scenario = sample_scenario.with_modifications(battery_replacement_year=None, battery_replacement_threshold=replacement_threshold)
    vehicle = sample_electric_vehicle
    
    # Mock the degradation factor calculation
    vehicle.calculate_battery_degradation_factor = MagicMock()
    
    expected_cost = vehicle.battery_capacity_kwh * PLACEHOLDER_BATTERY_COST_PER_KWH
    trigger_year_index = 4 # Let's assume threshold is met at the end of year index 4
    trigger_year = scenario.start_year + trigger_year_index
    mileage_before_trigger_year = trigger_year_index * scenario.annual_mileage
    mileage_at_trigger_year_end = mileage_before_trigger_year + scenario.annual_mileage
    age_at_trigger_year_end = trigger_year_index + 1

    # --- Simulate year *before* threshold is met ---
    # Degradation factor is above threshold
    vehicle.calculate_battery_degradation_factor.return_value = replacement_threshold + 0.05 
    cost_before = battery_replacement_cost.calculate_annual_cost(
        trigger_year - 1, vehicle, scenario, 
        trigger_year_index - 1, mileage_before_trigger_year - scenario.annual_mileage
    )
    # Check mock wasn't called in the year before (or called but didn't trigger)
    # The component calls it for the *end* of the current year.
    # So for year index 3, it checks degradation at end of year 4.
    assert cost_before == 0.0
    # Ensure mock was called correctly for the end of the year *before* trigger year
    # battery_replacement_cost(year=2028, ..., calc_year_index=3, total_mileage=150000) -> check degradation at age=4, mileage=200000
    # vehicle.calculate_battery_degradation_factor.assert_called_with(age_years=age_at_trigger_year_end-1, total_mileage_km=mileage_at_trigger_year_end - scenario.annual_mileage) 

    # --- Simulate year *when* threshold is met --- 
    # Set mock to return value *below* threshold for the end of this year
    vehicle.calculate_battery_degradation_factor.return_value = replacement_threshold - 0.01 
    cost_trigger = battery_replacement_cost.calculate_annual_cost(
        trigger_year, vehicle, scenario, 
        trigger_year_index, mileage_before_trigger_year
    )
    # Check mock was called with correct parameters for end of trigger year
    vehicle.calculate_battery_degradation_factor.assert_called_with(age_years=age_at_trigger_year_end, total_mileage_km=mileage_at_trigger_year_end)
    assert math.isclose(cost_trigger, expected_cost)

    # --- Simulate year *after* threshold was met --- 
    # Degradation still low, but shouldn't trigger again
    vehicle.calculate_battery_degradation_factor.return_value = replacement_threshold - 0.05 
    cost_after = battery_replacement_cost.calculate_annual_cost(
        trigger_year + 1, vehicle, scenario, 
        trigger_year_index + 1, mileage_at_trigger_year_end
    )
    # Should be 0 because current implementation only replaces once
    assert cost_after == 0.0 

def test_battery_replacement_warranty_trigger(battery_replacement_cost, sample_electric_vehicle, sample_scenario):
    """Test cost is triggered based on warranty expiry and threshold (simplified)."""
    # Ensure fixed year is not set, rely on threshold + warranty check
    replacement_threshold = 0.75
    warranty_years = 5 # Set a shorter warranty for test
    scenario = sample_scenario.with_modifications(
        battery_replacement_year=None, 
        battery_replacement_threshold=replacement_threshold,
        electric_vehicle_battery_warranty=warranty_years # Update scenario param if component uses it, else vehicle param matters
    )
    # Make sure vehicle reflects warranty if component reads from vehicle
    vehicle = sample_electric_vehicle
    vehicle.battery_warranty_years = warranty_years 
    
    # Mock degradation
    vehicle.calculate_battery_degradation_factor = MagicMock()
    expected_cost = vehicle.battery_capacity_kwh * PLACEHOLDER_BATTERY_COST_PER_KWH
    
    warranty_end_year_index = warranty_years # Index when vehicle age == warranty years
    warranty_end_year = scenario.start_year + warranty_end_year_index
    mileage_at_warranty_end = warranty_end_year_index * scenario.annual_mileage

    # --- Simulate year *before* warranty ends (degradation ok) ---
    vehicle.calculate_battery_degradation_factor.return_value = replacement_threshold + 0.1
    cost_before = battery_replacement_cost.calculate_annual_cost(warranty_end_year - 1, vehicle, scenario, warranty_end_year_index - 1, mileage_at_warranty_end - scenario.annual_mileage)
    assert cost_before == 0.0
    
    # --- Simulate warranty end year (threshold met) ---
    # Set mock to return value *below* threshold for the warranty check
    vehicle.calculate_battery_degradation_factor.return_value = replacement_threshold - 0.01
    cost_trigger = battery_replacement_cost.calculate_annual_cost(warranty_end_year, vehicle, scenario, warranty_end_year_index, mileage_at_warranty_end)
    
    # Warranty check uses degradation at *start* of warranty end year (age == warranty_years)
    vehicle.calculate_battery_degradation_factor.assert_called_with(age_years=warranty_years, total_mileage_km=mileage_at_warranty_end)
    assert math.isclose(cost_trigger, expected_cost)

    # --- Simulate warranty end year (threshold NOT met) ---
    vehicle.calculate_battery_degradation_factor.return_value = replacement_threshold + 0.01
    cost_not_triggered = battery_replacement_cost.calculate_annual_cost(warranty_end_year, vehicle, scenario, warranty_end_year_index, mileage_at_warranty_end)
    assert cost_not_triggered == 0.0

# --- InsuranceCost Tests ---

# Placeholder base rate used in the component implementation
PLACEHOLDER_INSURANCE_BASE_RATE = 0.05

def test_insurance_cost_electric(insurance_cost, sample_electric_vehicle, sample_scenario):
    """Test insurance cost calculation for ElectricVehicle."""
    vehicle = sample_electric_vehicle
    scenario = sample_scenario
    year = scenario.start_year + 2
    calc_year_index = 2
    total_mileage = 0 # Not used by current simple implementation
    
    # Expected: purchase_price * base_rate * ev_factor
    expected_cost = vehicle.purchase_price * PLACEHOLDER_INSURANCE_BASE_RATE * scenario.electric_insurance_cost_factor
    
    calculated_cost = insurance_cost.calculate_annual_cost(year, vehicle, scenario, calc_year_index, total_mileage)
    assert math.isclose(calculated_cost, expected_cost)

def test_insurance_cost_diesel(insurance_cost, sample_diesel_vehicle, sample_scenario):
    """Test insurance cost calculation for DieselVehicle."""
    vehicle = sample_diesel_vehicle
    scenario = sample_scenario
    year = scenario.start_year + 2
    calc_year_index = 2
    total_mileage = 0 # Not used
    
    # Expected: purchase_price * base_rate * diesel_factor
    expected_cost = vehicle.purchase_price * PLACEHOLDER_INSURANCE_BASE_RATE * scenario.diesel_insurance_cost_factor
    
    calculated_cost = insurance_cost.calculate_annual_cost(year, vehicle, scenario, calc_year_index, total_mileage)
    assert math.isclose(calculated_cost, expected_cost)

def test_insurance_cost_unsupported_vehicle(insurance_cost, sample_scenario):
    """Test TypeError for unsupported vehicle types."""
    # Use the module-level MockVehicle
    mock_vehicle = MockVehicle()
    with pytest.raises(TypeError) as excinfo:
        insurance_cost.calculate_annual_cost(sample_scenario.start_year, mock_vehicle, sample_scenario, 0, 0)
    assert "Vehicle type not supported" in str(excinfo.value)

# --- RegistrationCost Tests ---

def test_registration_cost(registration_cost, sample_electric_vehicle, sample_diesel_vehicle, sample_scenario):
    """Test that registration cost returns the fixed value from the scenario."""
    scenario = sample_scenario
    expected_cost = scenario.annual_registration_cost
    
    # Test for EV, year 0
    cost_ev_y0 = registration_cost.calculate_annual_cost(scenario.start_year, sample_electric_vehicle, scenario, 0, 0)
    assert cost_ev_y0 == expected_cost
    
    # Test for Diesel, year 3
    cost_diesel_y3 = registration_cost.calculate_annual_cost(scenario.start_year + 3, sample_diesel_vehicle, scenario, 3, scenario.annual_mileage * 3)
    assert cost_diesel_y3 == expected_cost
    
    # Test for EV, last year
    last_year_index = scenario.end_year - scenario.start_year
    cost_ev_last = registration_cost.calculate_annual_cost(scenario.end_year, sample_electric_vehicle, scenario, last_year_index, 0)
    assert cost_ev_last == expected_cost

# --- ResidualValue Tests ---

def test_residual_value_before_final_year(residual_value, sample_electric_vehicle, sample_scenario):
    """Test residual value cost is zero before the final analysis year."""
    scenario = sample_scenario
    final_year_index = scenario.end_year - scenario.start_year
    
    # Test year 0
    cost_y0 = residual_value.calculate_annual_cost(scenario.start_year, sample_electric_vehicle, scenario, 0, 0)
    assert cost_y0 == 0.0
    
    # Test year before final year
    cost_y_penultimate = residual_value.calculate_annual_cost(scenario.end_year - 1, sample_electric_vehicle, scenario, final_year_index - 1, 0)
    assert cost_y_penultimate == 0.0

def test_residual_value_final_year_electric(residual_value, sample_electric_vehicle, sample_scenario):
    """Test residual value recovery in the final year for ElectricVehicle."""
    vehicle = sample_electric_vehicle
    scenario = sample_scenario
    final_year = scenario.end_year
    final_year_index = final_year - scenario.start_year
    analysis_period_years = final_year_index + 1
    
    # Expected value is negative of the vehicle's residual value at the end of the analysis period
    expected_value = -vehicle.calculate_residual_value(age_years=analysis_period_years)
    
    calculated_cost = residual_value.calculate_annual_cost(final_year, vehicle, scenario, final_year_index, 0)
    assert math.isclose(calculated_cost, expected_value)

def test_residual_value_final_year_diesel(residual_value, sample_diesel_vehicle, sample_scenario):
    """Test residual value recovery in the final year for DieselVehicle."""
    vehicle = sample_diesel_vehicle
    scenario = sample_scenario
    final_year = scenario.end_year
    final_year_index = final_year - scenario.start_year
    analysis_period_years = final_year_index + 1
    
    # Expected value is negative of the vehicle's residual value
    expected_value = -vehicle.calculate_residual_value(age_years=analysis_period_years)
    
    calculated_cost = residual_value.calculate_annual_cost(final_year, vehicle, scenario, final_year_index, 0)
    assert math.isclose(calculated_cost, expected_value) 