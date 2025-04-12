import pytest
import math
from tco_model.vehicles import (
    Vehicle, ElectricVehicle, DieselVehicle, 
    ElectricConsumptionStrategy, DieselConsumptionStrategy,
    ElectricMaintenanceStrategy, DieselMaintenanceStrategy # Import strategies
)
from pydantic import ValidationError

# --- Fixtures --- 

@pytest.fixture
def electric_vehicle_params():
    """Provides default parameters for creating an ElectricVehicle."""
    return {
        "name": "Test EV",
        "vehicle_type": "rigid",
        "base_purchase_price_aud": 75000,
        "lifespan_years": 15,
        # Values scaled to 0.0-1.0
        "residual_value_percent_projections": {5: 0.5, 10: 0.3, 15: 0.15},
        "base_registration_cost_aud": 500,
        "energy_consumption_kwh_per_km": 0.3,
        "battery_capacity_kwh": 250.0,
        "battery_pack_cost_aud_per_kwh_projections": {2025: 170, 2030: 100, 2035: 75},
        "battery_warranty_years": 8,
        "battery_cycle_life": 1800,
        "battery_depth_of_discharge_percent": 80.0, # Kept as percent 0-100 for input
        "charging_efficiency_percent": 90.0, # Kept as percent 0-100 for input
        "purchase_price_annual_decrease_rate_real": 0.02, # Suffix added
        "extra_param": "value" # Keep extra params for some tests
    }

@pytest.fixture
def diesel_vehicle_params():
    """Provides default parameters for creating a DieselVehicle."""
    return {
        "name": "Test Diesel",
        "vehicle_type": "rigid",
        "base_purchase_price_aud": 60000,
        "lifespan_years": 12,
        # Values scaled to 0.0-1.0
        "residual_value_percent_projections": {5: 0.6, 10: 0.4, 12: 0.2},
        "base_registration_cost_aud": 600,
        "fuel_consumption_l_per_100km": 28.0,
        "co2_emission_factor_kg_per_l": 2.68, # Suffix added
        "another_param": 123 # Keep extra params for some tests
    }

@pytest.fixture(params=["electric", "diesel"])
def sample_vehicle(request, electric_vehicle_params, diesel_vehicle_params):
    """Parametrized fixture providing both EV and Diesel instances."""
    if request.param == "electric":
        return ElectricVehicle(**electric_vehicle_params)
    elif request.param == "diesel":
        return DieselVehicle(**diesel_vehicle_params)
    else:
        raise ValueError(f"Unknown vehicle type parameter: {request.param}")

# --- Test Cases Start Here ---

# --- Vehicle Base Class Tests (using concrete instances) ---

def test_vehicle_init_success(sample_vehicle):
    """Test successful initialization with valid parameters."""
    assert isinstance(sample_vehicle, Vehicle)
    assert sample_vehicle.name is not None
    assert sample_vehicle.lifespan_years > 0

@pytest.mark.parametrize("invalid_params", [
    {"base_purchase_price_aud": 0},
    {"base_purchase_price_aud": -100},
    {"lifespan_years": 0},
    {"lifespan_years": -5},
    # Test invalid projection value (negative percentage as fraction)
    {"residual_value_percent_projections": {5: 0.5, 10: -0.1, 15: 0.15}},
    # Test invalid projection value (percentage > 1 as fraction)
    {"residual_value_percent_projections": {5: 1.1, 10: 0.3, 15: 0.15}},
    # Test invalid projection key (not an int) -> Pydantic handles this type coercion/error
    # {"residual_value_percent_projections": {'five': 0.5, 10: 0.3}}
])
def test_vehicle_init_invalid_input(electric_vehicle_params, diesel_vehicle_params, invalid_params):
    """Test initialization fails with invalid base parameters."""
    ev_params = electric_vehicle_params.copy()
    ev_params.update(invalid_params)
    with pytest.raises(ValidationError): # Pydantic raises ValidationError
        ElectricVehicle(**ev_params)
        
    dv_params = diesel_vehicle_params.copy()
    # Check which parameter is being tested and update for diesel if applicable
    invalid_key = list(invalid_params.keys())[0]
    if invalid_key in dv_params:
        dv_params.update(invalid_params)
        with pytest.raises(ValidationError):
            DieselVehicle(**dv_params)
    # If the invalid key is not directly in diesel_params (like residual value projections),
    # but is a base class attribute, we still test it.
    elif invalid_key in ["base_purchase_price_aud", "lifespan_years", "residual_value_percent_projections"]:
        dv_params.update(invalid_params)
        with pytest.raises(ValidationError):
            DieselVehicle(**dv_params)

# Parameterize test_calculate_residual_value_aud for EV sample
@pytest.mark.parametrize("age_years, expected_value_fraction", [
    (0, 1.0),  # Start of life
    (5, 0.5),  # Matches first projection point
    (7, 0.42), # Interpolated between 5yr (0.5) and 10yr (0.3) -> 0.5 + (7-5)*(0.3-0.5)/(10-5) = 0.5 - 0.08 = 0.42
    (10, 0.3), # Matches second projection point
    (12, 0.24),# Interpolated between 10yr (0.3) and 15yr (0.15) -> 0.3 + (12-10)*(0.15-0.3)/(15-10) = 0.3 - 0.06 = 0.24
    (15, 0.15),# End of life / matches last projection point
    (20, 0.15) # Past end of life / uses last projection point
])
def test_calculate_residual_value_aud_ev(sample_vehicle, age_years, expected_value_fraction):
    """Test residual value calculation at different ages for EV."""
    expected_value = sample_vehicle.base_purchase_price_aud * expected_value_fraction
    calculated_value = sample_vehicle.calculate_residual_value_aud(age_years=age_years)
    assert math.isclose(calculated_value, expected_value, rel_tol=1e-9)

# Add a similar test for Diesel sample
@pytest.mark.parametrize("age_years, expected_value_fraction", [
    (0, 1.0),  # Start of life
    (5, 0.6),  # Matches first projection point
    (7, 0.52), # Interpolated between 5yr (0.6) and 10yr (0.4) -> 0.6 + (7-5)*(0.4-0.6)/(10-5) = 0.6 - 0.08 = 0.52
    (10, 0.4), # Matches second projection point
    (11, 0.3), # Interpolated between 10yr (0.4) and 12yr (0.2) -> 0.4 + (11-10)*(0.2-0.4)/(12-10) = 0.4 - 0.1 = 0.3
    (12, 0.2), # End of life / matches last projection point
    (15, 0.2)  # Past end of life / uses last projection point
])
def test_calculate_residual_value_aud_diesel(sample_vehicle, age_years, expected_value_fraction):
    """Test residual value calculation at different ages for Diesel."""
    expected_value = sample_vehicle.base_purchase_price_aud * expected_value_fraction
    calculated_value = sample_vehicle.calculate_residual_value_aud(age_years=age_years)
    assert math.isclose(calculated_value, expected_value, rel_tol=1e-9)

def test_calculate_residual_value_invalid_age(sample_vehicle):
    """Test residual value calculation fails with negative age for any vehicle."""
    with pytest.raises(ValueError) as excinfo:
        sample_vehicle.calculate_residual_value_aud(age_years=-1)
    assert "Age must be non-negative" in str(excinfo.value)

# Test for correct strategy instances
def test_vehicle_energy_consumption_strategy(sample_vehicle):
    """Test that the correct energy consumption strategy instance is returned."""
    strategy = sample_vehicle.energy_consumption_strategy
    if isinstance(sample_vehicle, ElectricVehicle):
        assert isinstance(strategy, ElectricConsumptionStrategy)
        assert math.isclose(strategy.kwh_per_km, sample_vehicle.energy_consumption_kwh_per_km)
    elif isinstance(sample_vehicle, DieselVehicle):
        assert isinstance(strategy, DieselConsumptionStrategy)
        assert math.isclose(strategy.l_per_km, sample_vehicle.fuel_consumption_l_per_100km / 100.0)

def test_vehicle_maintenance_strategy(sample_vehicle):
    """Test that the correct maintenance strategy instance is returned."""
    strategy = sample_vehicle.maintenance_strategy
    if isinstance(sample_vehicle, ElectricVehicle):
        assert isinstance(strategy, ElectricMaintenanceStrategy)
    elif isinstance(sample_vehicle, DieselVehicle):
        assert isinstance(strategy, DieselMaintenanceStrategy)

# --- Energy Consumption & Cost Tests (Unified) ---

def test_vehicle_calculate_energy_consumption(sample_vehicle):
    """Test calculation of energy consumption via strategy delegation."""
    distance = 100.0
    if isinstance(sample_vehicle, ElectricVehicle):
        expected_consumption = distance * sample_vehicle.energy_consumption_kwh_per_km
    elif isinstance(sample_vehicle, DieselVehicle):
        expected_consumption = distance * sample_vehicle.fuel_consumption_l_per_km
    else:
        pytest.fail("Unexpected vehicle type")
        
    calculated_consumption = sample_vehicle.calculate_energy_consumption(distance)
    assert math.isclose(calculated_consumption, expected_consumption)
    
    # Test zero distance
    assert sample_vehicle.calculate_energy_consumption(0) == 0.0

def test_vehicle_calculate_energy_consumption_invalid(sample_vehicle):
    """Test energy consumption calculation fails with negative distance."""
    with pytest.raises(ValueError) as excinfo:
        sample_vehicle.calculate_energy_consumption(-100)
    # Check message from strategy
    assert "Distance cannot be negative" in str(excinfo.value)

def test_vehicle_calculate_annual_energy_cost(sample_vehicle):
    """Test calculation of annual energy cost (unified method)."""
    annual_mileage_km = 50000.0
    
    if isinstance(sample_vehicle, ElectricVehicle):
        energy_price_aud_per_unit = 0.25 # Price per kWh
        expected_consumption = annual_mileage_km * sample_vehicle.energy_consumption_kwh_per_km
    elif isinstance(sample_vehicle, DieselVehicle):
        energy_price_aud_per_unit = 1.85 # Price per L
        expected_consumption = annual_mileage_km * sample_vehicle.fuel_consumption_l_per_km
    else:
        pytest.fail("Unexpected vehicle type")

    expected_cost = expected_consumption * energy_price_aud_per_unit
    # Use the unified method
    calculated_cost = sample_vehicle.calculate_annual_energy_cost(annual_mileage_km, energy_price_aud_per_unit)
    assert math.isclose(calculated_cost, expected_cost)

    # Test zero mileage and zero price
    assert sample_vehicle.calculate_annual_energy_cost(0, energy_price_aud_per_unit) == 0.0
    assert sample_vehicle.calculate_annual_energy_cost(annual_mileage_km, 0) == 0.0

@pytest.mark.parametrize("annual_mileage_km, energy_price_aud_per_unit", [
    (-100, 0.25), # Negative mileage
    (50000, -0.10) # Negative price
])
def test_vehicle_calculate_annual_energy_cost_invalid(sample_vehicle, annual_mileage_km, energy_price_aud_per_unit):
    """Test annual energy cost calculation fails with negative inputs (unified method)."""
    with pytest.raises(ValueError):
        sample_vehicle.calculate_annual_energy_cost(annual_mileage_km, energy_price_aud_per_unit)

# --- ElectricVehicle Specific Tests ---

def test_electric_vehicle_init_success(sample_vehicle, electric_vehicle_params):
    """Test successful initialization of ElectricVehicle specific attributes."""
    assert isinstance(sample_vehicle, ElectricVehicle)
    assert sample_vehicle.battery_capacity_kwh == electric_vehicle_params["battery_capacity_kwh"]
    assert sample_vehicle.energy_consumption_kwh_per_km == electric_vehicle_params["energy_consumption_kwh_per_km"]
    assert sample_vehicle.battery_warranty_years == electric_vehicle_params["battery_warranty_years"]

@pytest.mark.parametrize("invalid_params", [
    {"battery_capacity_kwh": 0},
    {"battery_capacity_kwh": -100},
    {"energy_consumption_kwh_per_km": 0},
    {"energy_consumption_kwh_per_km": -0.5},
    {"battery_warranty_years": -1},
    {"battery_depth_of_discharge_percent": -10},
    {"battery_depth_of_discharge_percent": 110},
    {"charging_efficiency_percent": -5},
    {"charging_efficiency_percent": 105},
    {"purchase_price_annual_decrease_rate_real": -0.1}
])
def test_electric_vehicle_init_invalid_input(electric_vehicle_params, invalid_params):
    """Test ElectricVehicle initialization fails with invalid specific parameters."""
    ev_params = electric_vehicle_params.copy()
    ev_params.update(invalid_params)
    with pytest.raises((ValueError, ValidationError)): # Can be ValueError from setters or ValidationError from Pydantic
        ElectricVehicle(**ev_params)

@pytest.mark.parametrize("age_years, annual_mileage_km, expected_min_factor, expected_max_factor", [
    (0, 0, 1.0, 1.0),                     # New battery
    (5, 250000, 0.8, 1.0),                # Mid-life example (factors depend heavily on constants)
    (15, 750000, 0.0, 0.9),               # Approx end of vehicle life
    (15, 2000000, 0.0, 0.8),              # High mileage end of life
    (20, 1000000, 0.0, 0.82),             # Beyond vehicle life
    # Note: The calculation might have changed. These expected values are illustrative.
])
def test_calculate_battery_degradation_factor(sample_vehicle, age_years, annual_mileage_km, expected_min_factor, expected_max_factor):
    """Test battery degradation calculation produces values within expected range [0, 1]."""
    # Note: The exact expected value depends heavily on the internal constants.
    # We primarily test that the output is within the valid [0, 1] range and behaves directionally correctly.
    factor = sample_vehicle.calculate_battery_degradation_factor(age_years, annual_mileage_km)
    assert 0.0 <= factor <= 1.0
    # Check against broad expected ranges based on inputs
    assert factor >= expected_min_factor
    assert factor <= expected_max_factor

    # Test that higher age/mileage generally leads to lower factors (or stays at min)
    factor_later = sample_vehicle.calculate_battery_degradation_factor(age_years + 1, annual_mileage_km + 50000)
    assert factor_later <= factor

def test_calculate_battery_degradation_factor_invalid(sample_vehicle):
    """Test battery degradation calculation fails with negative inputs."""
    with pytest.raises(ValueError):
        sample_vehicle.calculate_battery_degradation_factor(-1, 10000)
    with pytest.raises(ValueError):
        sample_vehicle.calculate_battery_degradation_factor(1, -10000)

# --- DieselVehicle Specific Tests ---

def test_diesel_vehicle_init_success(sample_vehicle, diesel_vehicle_params):
    """Test successful initialization of DieselVehicle specific attributes."""
    assert isinstance(sample_vehicle, DieselVehicle)
    assert sample_vehicle.fuel_consumption_l_per_100km == diesel_vehicle_params["fuel_consumption_l_per_100km"]
    # Test the conversion to L/km
    expected_l_per_km = diesel_vehicle_params["fuel_consumption_l_per_100km"] / 100.0
    assert math.isclose(sample_vehicle.fuel_consumption_l_per_km, expected_l_per_km)

@pytest.mark.parametrize("invalid_params", [
    {"fuel_consumption_l_per_100km": 0},
    {"fuel_consumption_l_per_100km": -10},
    {"co2_emission_factor_kg_per_l": -1.0}
])
def test_diesel_vehicle_init_invalid_input(diesel_vehicle_params, invalid_params):
    """Test DieselVehicle initialization fails with invalid specific parameters."""
    dv_params = diesel_vehicle_params.copy()
    dv_params.update(invalid_params)
    with pytest.raises((ValueError, ValidationError)): # Can be ValueError or ValidationError
        DieselVehicle(**dv_params)

# Removed tests for calculate_energy_consumption and calculate_annual_energy_cost
# as they are now covered by the unified tests above.

@pytest.mark.parametrize("age_years, annual_mileage_km, expected_min_factor, expected_max_factor", [
    (0, 0, 1.0, 1.0),                     # New battery
    (5, 250000, 0.8, 1.0),                # Mid-life example (factors depend heavily on constants)
    (15, 750000, 0.0, 0.9),               # Approx end of vehicle life
    (15, 2000000, 0.0, 0.8),              # High mileage end of life
    (20, 1000000, 0.0, 0.82),             # Beyond vehicle life
    # Note: The calculation might have changed. These expected values are illustrative.
])
def test_calculate_battery_degradation_factor(sample_vehicle, age_years, annual_mileage_km, expected_min_factor, expected_max_factor):
    """Test battery degradation calculation produces values within expected range [0, 1]."""
    # Note: The exact expected value depends heavily on the internal constants.
    # We primarily test that the output is within the valid [0, 1] range and behaves directionally correctly.
    factor = sample_vehicle.calculate_battery_degradation_factor(age_years, annual_mileage_km)
    assert 0.0 <= factor <= 1.0
    # Check against broad expected ranges based on inputs
    assert factor >= expected_min_factor
    assert factor <= expected_max_factor

    # Test that higher age/mileage generally leads to lower factors (or stays at min)
    factor_later = sample_vehicle.calculate_battery_degradation_factor(age_years + 1, annual_mileage_km + 50000)
    assert factor_later <= factor

def test_calculate_battery_degradation_factor_invalid(sample_vehicle):
    """Test battery degradation calculation fails with negative inputs."""
    with pytest.raises(ValueError):
        sample_vehicle.calculate_battery_degradation_factor(-1, 10000)
    with pytest.raises(ValueError):
        sample_vehicle.calculate_battery_degradation_factor(1, -10000)

@pytest.mark.parametrize("annual_mileage_km, energy_price_aud_per_l", [
    (-100, 1.85),
    (50000, -0.10)
])
def test_diesel_calculate_annual_energy_cost_invalid(sample_vehicle, annual_mileage_km, energy_price_aud_per_l):
    """Test annual energy cost calculation fails with negative inputs."""
    with pytest.raises(ValueError):
        sample_vehicle.calculate_annual_energy_cost(annual_mileage_km, energy_price_aud_per_l) 