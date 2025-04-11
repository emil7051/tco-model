import pytest
import pandas as pd
import numpy as np # Import numpy for approx
from tco_model.model import TCOCalculator
from tco_model.scenario import Scenario
from tco_model.vehicles import ElectricVehicle, DieselVehicle

# A minimal but complete scenario fixture for testing
@pytest.fixture
def basic_scenario():
    """Provides a basic, valid Scenario object for testing."""
    return Scenario(
        analysis_years=5,
        discount_rate_real=0.03,
        electricity_price=0.20,  # $/kWh
        diesel_price=1.50,  # $/L
        road_user_charge=0.05, # $/km
        carbon_tax_rate=30, # $/tonne CO2e
        annual_mileage=15000,
        electric_vehicle=ElectricVehicle(
            name="Test EV",
            purchase_price=60000,
            residual_value_percent=0.40,
            energy_consumption=0.25,  # kWh/km
            maintenance_cost_per_km=0.03,
            insurance_cost_percent=0.02,
            registration_cost=500,
            battery_capacity_kwh=70,
            battery_replacement_cost_per_kwh=100,
            battery_cycle_life=1500,
            battery_depth_of_discharge=0.8,
            charging_efficiency=0.9
        ),
        diesel_vehicle=DieselVehicle(
            name="Test Diesel",
            purchase_price=50000,
            residual_value_percent=0.35,
            energy_consumption=0.10,  # L/km
            maintenance_cost_per_km=0.05,
            insurance_cost_percent=0.025,
            registration_cost=600,
            co2_emission_factor=2.68 # kg CO2e/L
        ),
        infrastructure_cost=5000,
        infrastructure_maintenance_percent=0.01,
        battery_degradation_rate=0.02, # Annual capacity loss
        insurance_increase_rate=0.01,
        registration_increase_rate=0.01,
        maintenance_increase_rate=0.01,
        electricity_price_increase=0.02,
        diesel_price_increase=0.03,
        carbon_tax_increase_rate=0.05,
        road_user_charge_increase_rate=0.01,
        include_carbon_tax=True,
        include_road_user_charge=True,
        force_battery_replacement_year=None
    )

@pytest.fixture
def calculator():
    """Provides a TCOCalculator instance."""
    return TCOCalculator()

def test_tco_calculator_init(calculator):
    """Tests TCOCalculator initialization."""
    assert isinstance(calculator, TCOCalculator)

def test_calculate_returns_dictionary(calculator, basic_scenario):
    """Tests that the calculate method returns a dictionary."""
    results = calculator.calculate(basic_scenario)
    assert isinstance(results, dict)

def test_calculate_result_keys(calculator, basic_scenario):
    """Tests that the results dictionary contains the expected keys."""
    results = calculator.calculate(basic_scenario)
    expected_keys = [
        'electric_annual_costs',
        'diesel_annual_costs',
        'electric_total_tco',
        'diesel_total_tco',
        'electric_lcod',
        'diesel_lcod',
        'parity_year'
    ]
    for key in expected_keys:
        assert key in results

def test_calculate_dataframe_shape(calculator, basic_scenario):
    """Tests the shape of the annual cost DataFrames."""
    results = calculator.calculate(basic_scenario)
    years = basic_scenario.analysis_years
    # Expected columns: Year + 10 components + Total = 12 cols for EV
    # Expected columns: Year + 8 components + Total = 10 cols for Diesel
    # Need to be careful as Residual Value is often negative.
    # Let's get columns dynamically from the calculator's known components
    # Use the calculator fixture instance passed to the test
    ev_components = calculator._get_applicable_components(basic_scenario.electric_vehicle, basic_scenario)
    diesel_components = calculator._get_applicable_components(basic_scenario.diesel_vehicle, basic_scenario)

    # +1 for Year, +1 for Total column
    expected_ev_cols = len(ev_components) + 2
    expected_diesel_cols = len(diesel_components) + 2

    assert results['electric_annual_costs'].shape == (years, expected_ev_cols)
    assert results['diesel_annual_costs'].shape == (years, expected_diesel_cols)
    assert 'Year' in results['electric_annual_costs'].columns
    assert 'Year' in results['diesel_annual_costs'].columns
    assert 'Total' in results['electric_annual_costs'].columns
    assert 'Total' in results['diesel_annual_costs'].columns


def test_calculate_spot_check_values(calculator, basic_scenario):
    """Performs spot checks on specific calculated values."""
    results = calculator.calculate(basic_scenario)
    ev_costs = results['electric_annual_costs']
    diesel_costs = results['diesel_annual_costs']

    # Example Spot Check: Diesel Energy Cost Year 1 (undiscounted)
    # Diesel L/km = 0.10
    # Annual km = 15000
    # Annual L = 15000 * 0.10 = 1500
    # Diesel price Year 1 = 1.50 * (1 + 0.03)^0 = 1.50
    # Energy Cost Year 1 = 1500 * 1.50 = 2250
    expected_diesel_energy_y1 = 2250.0
    assert diesel_costs.loc[0, 'EnergyCost'] == pytest.approx(expected_diesel_energy_y1)

    # Example Spot Check: EV Acquisition Cost Year 1 (undiscounted)
    # Purchase price = 60000
    expected_ev_acq_y1 = 60000.0
    assert ev_costs.loc[0, 'AcquisitionCost'] == pytest.approx(expected_ev_acq_y1)

    # Example Spot Check: EV Infrastructure Cost Year 1 (undiscounted)
    # Infrastructure cost = 5000
    expected_ev_infra_y1 = 5000.0
    assert ev_costs.loc[0, 'InfrastructureCost'] == pytest.approx(expected_ev_infra_y1)

    # Example Spot Check: Diesel Maintenance Cost Year 2 (undiscounted)
    # Maintenance cost/km = 0.05
    # Maintenance increase rate = 0.01
    # Cost/km Year 2 = 0.05 * (1 + 0.01)^1 = 0.0505
    # Annual km = 15000
    # Maintenance Cost Year 2 = 15000 * 0.0505 = 757.5
    expected_diesel_maint_y2 = 757.5
    assert diesel_costs.loc[1, 'MaintenanceCost'] == pytest.approx(expected_diesel_maint_y2)

    # Example Spot Check: Diesel Residual Value Year 5 (undiscounted)
    # Purchase price = 50000
    # Residual value % = 0.35
    # Residual value = 50000 * 0.35 = 17500
    # Should be negative in the cost table
    expected_diesel_resid_y5 = -17500.0
    assert diesel_costs.loc[4, 'ResidualValue'] == pytest.approx(expected_diesel_resid_y5)

    # Example Spot Check: Total TCO (discounted sum of annual totals)
    # Manual discounting is complex, let's just check if the total matches the sum of the 'Total' column discounted
    discount_rate = basic_scenario.discount_rate_real
    years = basic_scenario.analysis_years
    discount_factors = pd.Series([(1 + discount_rate)**(-i) for i in range(years)])

    calculated_ev_total_tco = (ev_costs['Total'] * discount_factors).sum()
    calculated_diesel_total_tco = (diesel_costs['Total'] * discount_factors).sum()

    assert results['electric_total_tco'] == pytest.approx(calculated_ev_total_tco)
    assert results['diesel_total_tco'] == pytest.approx(calculated_diesel_total_tco)


def test_lcod_calculation(calculator, basic_scenario):
    """Tests the Levelized Cost of Driving (LCOD) calculation."""
    results = calculator.calculate(basic_scenario)
    total_km = basic_scenario.annual_mileage * basic_scenario.analysis_years

    expected_ev_lcod = results['electric_total_tco'] / total_km
    expected_diesel_lcod = results['diesel_total_tco'] / total_km

    assert results['electric_lcod'] == pytest.approx(expected_ev_lcod)
    assert results['diesel_lcod'] == pytest.approx(expected_diesel_lcod)
    assert results['electric_lcod'] > 0
    assert results['diesel_lcod'] > 0


def test_parity_year_calculation(calculator, basic_scenario):
    """Tests the parity year calculation logic."""
    # Modify scenario slightly to ensure parity happens within the timeframe for testing
    scenario_with_parity = basic_scenario.model_copy(deep=True)
    # Make EV cheaper initially or Diesel more expensive quickly
    scenario_with_parity.electric_vehicle.purchase_price = 45000
    scenario_with_parity.diesel_price_increase = 0.15 # Faster increase
    scenario_with_parity.analysis_years = 10 # Longer period

    results_parity = calculator.calculate(scenario_with_parity)
    ev_cum_costs = results_parity['electric_annual_costs']['Total'].cumsum()
    diesel_cum_costs = results_parity['diesel_annual_costs']['Total'].cumsum()

    # Find the first year where EV cumulative cost <= Diesel cumulative cost
    parity_years = np.where(ev_cum_costs <= diesel_cum_costs)[0]
    expected_parity_year = parity_years[0] + 1 if len(parity_years) > 0 else None # +1 for 1-based year index

    assert results_parity['parity_year'] == expected_parity_year
    assert expected_parity_year is not None # Ensure parity was found in this modified scenario

    # Test case where parity is never reached
    scenario_no_parity = basic_scenario.model_copy(deep=True)
    scenario_no_parity.electric_vehicle.purchase_price = 100000 # Make EV very expensive
    scenario_no_parity.diesel_price = 1.0 # Make diesel cheap
    scenario_no_parity.diesel_price_increase = 0.01

    results_no_parity = calculator.calculate(scenario_no_parity)
    assert results_no_parity['parity_year'] is None


def test_calculate_edge_case_short_period(calculator, basic_scenario):
    """Tests calculation with a very short analysis period (1 year)."""
    scenario_short = basic_scenario.model_copy(update={'analysis_years': 1})
    results = calculator.calculate(scenario_short)

    assert results['electric_annual_costs'].shape[0] == 1
    assert results['diesel_annual_costs'].shape[0] == 1
    # TCO should just be the Year 1 total (since discount factor is 1 for year 0/index 0)
    assert results['electric_total_tco'] == pytest.approx(results['electric_annual_costs'].loc[0, 'Total'])
    assert results['diesel_total_tco'] == pytest.approx(results['diesel_annual_costs'].loc[0, 'Total'])
    # LCOD calculation
    total_km = scenario_short.annual_mileage * 1
    assert results['electric_lcod'] == pytest.approx(results['electric_total_tco'] / total_km)
    assert results['diesel_lcod'] == pytest.approx(results['diesel_total_tco'] / total_km)
    # Parity unlikely in 1 year unless costs are very skewed
    ev_y1_total = results['electric_annual_costs'].loc[0, 'Total']
    diesel_y1_total = results['diesel_annual_costs'].loc[0, 'Total']
    expected_parity = 1 if ev_y1_total <= diesel_y1_total else None
    assert results['parity_year'] == expected_parity


def test_calculate_edge_case_zero_discount(calculator, basic_scenario):
    """Tests calculation with a zero discount rate."""
    scenario_zero_discount = basic_scenario.model_copy(update={'discount_rate_real': 0.0})
    results = calculator.calculate(scenario_zero_discount)

    # Total TCO should be the simple sum of annual totals
    expected_ev_total = results['electric_annual_costs']['Total'].sum()
    expected_diesel_total = results['diesel_annual_costs']['Total'].sum()

    assert results['electric_total_tco'] == pytest.approx(expected_ev_total)
    assert results['diesel_total_tco'] == pytest.approx(expected_diesel_total)

    # LCOD uses the TCO, so it should still work
    total_km = basic_scenario.annual_mileage * basic_scenario.analysis_years
    assert results['electric_lcod'] == pytest.approx(expected_ev_total / total_km)
    assert results['diesel_lcod'] == pytest.approx(expected_diesel_total / total_km)

    # Parity logic remains the same, just based on undiscounted cumulative sums
    ev_cum_costs = results['electric_annual_costs']['Total'].cumsum()
    diesel_cum_costs = results['diesel_annual_costs']['Total'].cumsum()
    parity_years = np.where(ev_cum_costs <= diesel_cum_costs)[0]
    expected_parity_year = parity_years[0] + 1 if len(parity_years) > 0 else None
    assert results['parity_year'] == expected_parity_year