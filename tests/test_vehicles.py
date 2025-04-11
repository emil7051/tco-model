import pytest
import math

from tco_model.vehicles import Vehicle, ElectricVehicle, DieselVehicle

# --- Fixtures --- 

@pytest.fixture
def electric_vehicle_params():
    """Provides default parameters for creating an ElectricVehicle."""
    return {
        "name": "Test EV",
        "purchase_price": 350000.0,
        "lifespan": 15,
        "residual_value_pct": 0.15,
        "maintenance_cost_per_km": 0.07,
        "insurance_cost_percent": 0.03,
        "registration_cost": 500.0,
        "battery_capacity_kwh": 250.0,
        "energy_consumption_kwh_per_km": 0.8,
        "battery_warranty_years": 8,
        "battery_replacement_cost_per_kwh": 100.0,
        "battery_cycle_life": 1800,
        "battery_depth_of_discharge": 0.8,
        "charging_efficiency": 0.9,
        "extra_param": "value"
    }

@pytest.fixture
def diesel_vehicle_params():
    """Provides default parameters for creating a DieselVehicle."""
    return {
        "name": "Test Diesel",
        "purchase_price": 180000.0,
        "lifespan": 15,
        "residual_value_pct": 0.12,
        "maintenance_cost_per_km": 0.14,
        "insurance_cost_percent": 0.04,
        "registration_cost": 700.0,
        "fuel_consumption_l_per_100km": 28.0,
        "co2_emission_factor": 2.68,
        "another_param": 123
    }

@pytest.fixture
def sample_electric_vehicle(electric_vehicle_params):
    """Creates a sample ElectricVehicle instance for testing."""
    return ElectricVehicle(**electric_vehicle_params)

@pytest.fixture
def sample_diesel_vehicle(diesel_vehicle_params):
    """Creates a sample DieselVehicle instance for testing."""
    return DieselVehicle(**diesel_vehicle_params)

# --- Test Cases Start Here ---

# --- Vehicle Base Class Tests (using concrete instances) ---

def test_vehicle_init_success(sample_electric_vehicle, sample_diesel_vehicle, electric_vehicle_params, diesel_vehicle_params):
    """Test successful initialization of base Vehicle attributes."""
    # Test Electric Vehicle
    assert sample_electric_vehicle.name == electric_vehicle_params["name"]
    assert sample_electric_vehicle.purchase_price == electric_vehicle_params["purchase_price"]
    assert sample_electric_vehicle.lifespan == electric_vehicle_params["lifespan"]
    assert sample_electric_vehicle.residual_value_pct == electric_vehicle_params["residual_value_pct"]
    assert sample_electric_vehicle.additional_params["extra_param"] == "value"

    # Test Diesel Vehicle
    assert sample_diesel_vehicle.name == diesel_vehicle_params["name"]
    assert sample_diesel_vehicle.purchase_price == diesel_vehicle_params["purchase_price"]
    assert sample_diesel_vehicle.lifespan == diesel_vehicle_params["lifespan"]
    assert sample_diesel_vehicle.residual_value_pct == diesel_vehicle_params["residual_value_pct"]
    assert sample_diesel_vehicle.additional_params["another_param"] == 123

@pytest.mark.parametrize("invalid_params", [
    {"purchase_price": 0}, 
    {"purchase_price": -100},
    {"lifespan": 0},
    {"lifespan": -5},
    {"residual_value_pct": -0.1},
    {"residual_value_pct": 1.1}
])
def test_vehicle_init_invalid_input(electric_vehicle_params, diesel_vehicle_params, invalid_params):
    """Test initialization fails with invalid base parameters."""
    ev_params = electric_vehicle_params.copy()
    ev_params.update(invalid_params)
    with pytest.raises(ValueError):
        ElectricVehicle(**ev_params)
        
    diesel_params = diesel_vehicle_params.copy()
    diesel_params.update(invalid_params)
    with pytest.raises(ValueError):
        DieselVehicle(**diesel_params)

@pytest.mark.parametrize("age, expected_factor", [
    (0, 1.0), # Start of life
    (5, 1.0 - (1.0 - 0.15) / 15 * 5), # Mid-life (using EV residual pct)
    (15, 0.15), # End of life
    (20, 0.15)  # Beyond lifespan
])
def test_calculate_residual_value(sample_electric_vehicle, age, expected_factor):
    """Test residual value calculation at different ages."""
    expected_value = sample_electric_vehicle.purchase_price * expected_factor
    calculated_value = sample_electric_vehicle.calculate_residual_value(age_years=age)
    assert math.isclose(calculated_value, expected_value, rel_tol=1e-9)

def test_calculate_residual_value_invalid_age(sample_diesel_vehicle):
    """Test residual value calculation fails with negative age."""
    with pytest.raises(ValueError) as excinfo:
        sample_diesel_vehicle.calculate_residual_value(age_years=-1)
    assert "Age must be non-negative" in str(excinfo.value)

# --- ElectricVehicle Specific Tests ---

def test_electric_vehicle_init_success(sample_electric_vehicle, electric_vehicle_params):
    """Test successful initialization of ElectricVehicle specific attributes."""
    assert sample_electric_vehicle.battery_capacity_kwh == electric_vehicle_params["battery_capacity_kwh"]
    assert sample_electric_vehicle.energy_consumption_kwh_per_km == electric_vehicle_params["energy_consumption_kwh_per_km"]
    assert sample_electric_vehicle.battery_warranty_years == electric_vehicle_params["battery_warranty_years"]

@pytest.mark.parametrize("invalid_params", [
    {"battery_capacity_kwh": 0},
    {"battery_capacity_kwh": -100},
    {"energy_consumption_kwh_per_km": 0},
    {"energy_consumption_kwh_per_km": -0.5},
    {"battery_warranty_years": -1}
])
def test_electric_vehicle_init_invalid_input(electric_vehicle_params, invalid_params):
    """Test ElectricVehicle initialization fails with invalid specific parameters."""
    ev_params = electric_vehicle_params.copy()
    ev_params.update(invalid_params)
    with pytest.raises(ValueError):
        ElectricVehicle(**ev_params)

def test_ev_calculate_energy_consumption(sample_electric_vehicle):
    """Test calculation of energy consumption for EV."""
    distance = 100.0
    expected_consumption = distance * sample_electric_vehicle.energy_consumption_kwh_per_km
    calculated_consumption = sample_electric_vehicle.calculate_energy_consumption(distance)
    assert math.isclose(calculated_consumption, expected_consumption)
    
    # Test zero distance
    assert sample_electric_vehicle.calculate_energy_consumption(0) == 0.0

def test_ev_calculate_energy_consumption_invalid(sample_electric_vehicle):
    """Test energy consumption calculation fails with negative distance."""
    with pytest.raises(ValueError) as excinfo:
        sample_electric_vehicle.calculate_energy_consumption(-100)
    assert "Distance cannot be negative" in str(excinfo.value)

def test_ev_calculate_annual_energy_cost(sample_electric_vehicle):
    """Test calculation of annual energy cost for EV."""
    mileage = 50000.0
    price_kwh = 0.25
    expected_cost = (mileage * sample_electric_vehicle.energy_consumption_kwh_per_km) * price_kwh
    calculated_cost = sample_electric_vehicle.calculate_annual_energy_cost(mileage, price_kwh)
    assert math.isclose(calculated_cost, expected_cost)

    # Test zero mileage and zero price
    assert sample_electric_vehicle.calculate_annual_energy_cost(0, price_kwh) == 0.0
    assert sample_electric_vehicle.calculate_annual_energy_cost(mileage, 0) == 0.0

@pytest.mark.parametrize("mileage, price", [
    (-100, 0.25), 
    (50000, -0.10)
])
def test_ev_calculate_annual_energy_cost_invalid(sample_electric_vehicle, mileage, price):
    """Test annual energy cost calculation fails with negative inputs."""
    with pytest.raises(ValueError):
        sample_electric_vehicle.calculate_annual_energy_cost(mileage, price)

@pytest.mark.parametrize("age, mileage, expected_min_factor, expected_max_factor", [
    (0, 0, 1.0, 1.0),                     # New battery
    (5, 250000, 0.8, 1.0),                # Mid-life example (factors depend heavily on constants)
    (15, 750000, 0.0, 0.9),               # Approx end of vehicle life
    (15, 2000000, 0.0, 0.8),              # High mileage end of life
    (20, 1000000, 0.0, 0.8)               # Beyond vehicle life
])
def test_calculate_battery_degradation_factor(sample_electric_vehicle, age, mileage, expected_min_factor, expected_max_factor):
    """Test battery degradation calculation produces values within expected range [0, 1]."""
    # Note: The exact expected value depends heavily on the internal constants.
    # We primarily test that the output is within the valid [0, 1] range and behaves directionally correctly.
    factor = sample_electric_vehicle.calculate_battery_degradation_factor(age, mileage)
    assert 0.0 <= factor <= 1.0
    # Check against broad expected ranges based on inputs
    assert factor >= expected_min_factor 
    assert factor <= expected_max_factor

    # Test that higher age/mileage generally leads to lower factors (or stays at min)
    factor_later = sample_electric_vehicle.calculate_battery_degradation_factor(age + 1, mileage + 50000)
    assert factor_later <= factor 


def test_calculate_battery_degradation_factor_invalid(sample_electric_vehicle):
    """Test battery degradation calculation fails with negative inputs."""
    with pytest.raises(ValueError):
        sample_electric_vehicle.calculate_battery_degradation_factor(-1, 10000)
    with pytest.raises(ValueError):
        sample_electric_vehicle.calculate_battery_degradation_factor(1, -10000)

# --- DieselVehicle Specific Tests ---

def test_diesel_vehicle_init_success(sample_diesel_vehicle, diesel_vehicle_params):
    """Test successful initialization of DieselVehicle specific attributes."""
    assert sample_diesel_vehicle.fuel_consumption_l_per_100km == diesel_vehicle_params["fuel_consumption_l_per_100km"]
    # Test the conversion to L/km
    expected_l_per_km = diesel_vehicle_params["fuel_consumption_l_per_100km"] / 100.0
    assert math.isclose(sample_diesel_vehicle.fuel_consumption_l_per_km, expected_l_per_km)

@pytest.mark.parametrize("invalid_params", [
    {"fuel_consumption_l_per_100km": 0},
    {"fuel_consumption_l_per_100km": -10}
])
def test_diesel_vehicle_init_invalid_input(diesel_vehicle_params, invalid_params):
    """Test DieselVehicle initialization fails with invalid specific parameters."""
    dv_params = diesel_vehicle_params.copy()
    dv_params.update(invalid_params)
    with pytest.raises(ValueError):
        DieselVehicle(**dv_params)

def test_diesel_calculate_energy_consumption(sample_diesel_vehicle):
    """Test calculation of energy consumption for Diesel."""
    distance = 100.0
    expected_consumption = distance * sample_diesel_vehicle.fuel_consumption_l_per_km
    calculated_consumption = sample_diesel_vehicle.calculate_energy_consumption(distance)
    assert math.isclose(calculated_consumption, expected_consumption)
    
    # Test zero distance
    assert sample_diesel_vehicle.calculate_energy_consumption(0) == 0.0

def test_diesel_calculate_energy_consumption_invalid(sample_diesel_vehicle):
    """Test energy consumption calculation fails with negative distance."""
    with pytest.raises(ValueError) as excinfo:
        sample_diesel_vehicle.calculate_energy_consumption(-100)
    assert "Distance cannot be negative" in str(excinfo.value)

def test_diesel_calculate_annual_energy_cost(sample_diesel_vehicle):
    """Test calculation of annual energy cost for Diesel."""
    mileage = 50000.0
    price_l = 1.85
    expected_cost = (mileage * sample_diesel_vehicle.fuel_consumption_l_per_km) * price_l
    calculated_cost = sample_diesel_vehicle.calculate_annual_energy_cost(mileage, price_l)
    assert math.isclose(calculated_cost, expected_cost)

    # Test zero mileage and zero price
    assert sample_diesel_vehicle.calculate_annual_energy_cost(0, price_l) == 0.0
    assert sample_diesel_vehicle.calculate_annual_energy_cost(mileage, 0) == 0.0

@pytest.mark.parametrize("mileage, price", [
    (-100, 1.85),
    (50000, -0.10)
])
def test_diesel_calculate_annual_energy_cost_invalid(sample_diesel_vehicle, mileage, price):
    """Test annual energy cost calculation fails with negative inputs."""
    with pytest.raises(ValueError):
        sample_diesel_vehicle.calculate_annual_energy_cost(mileage, price) 