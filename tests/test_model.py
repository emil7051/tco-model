import pytest
import pandas as pd
import numpy as np # Import numpy for approx
from tco_model.model import TCOCalculator
from tco_model.scenarios import Scenario
from tco_model.vehicles import ElectricVehicle, DieselVehicle

# A minimal but complete scenario fixture for testing
@pytest.fixture
def basic_scenario():
    """Provides a basic, valid Scenario object for testing."""
    # Define vehicle data as dicts first
    ev_data = {
        "name": "Test EV",
        "purchase_price": 60000,
        "lifespan": 12, # Example value
        "residual_value_pct": 0.40, 
        "maintenance_cost_per_km": 0.03, 
        "insurance_cost_percent": 0.02, 
        "registration_cost": 500, 
        "energy_consumption_kwh_per_km": 0.25,  
        "battery_capacity_kwh": 70,
        "battery_replacement_cost_per_kwh": 100, 
        "battery_warranty_years": 8, # Uses default if omitted
        "battery_cycle_life": 1500, 
        "battery_depth_of_discharge": 0.8, 
        "charging_efficiency": 0.9 
    }
    diesel_data = {
        "name": "Test Diesel",
        "purchase_price": 50000,
        "lifespan": 15, # Example value
        "residual_value_pct": 0.35, 
        "maintenance_cost_per_km": 0.05, 
        "insurance_cost_percent": 0.025, 
        "registration_cost": 600, 
        "fuel_consumption_l_per_100km": 10.0,  
        "co2_emission_factor": 2.68 # kg CO2e/L
    }
    
    return Scenario(
        analysis_years=5,
        discount_rate_real=0.03,
        electricity_price=0.20,  # $/kWh
        diesel_price=1.50,  # $/L
        road_user_charge=0.05, # $/km
        carbon_tax_rate=30, # $/tonne CO2e
        annual_mileage=15000,
        electric_vehicle=ElectricVehicle(**ev_data), # Instantiate vehicle
        diesel_vehicle=DieselVehicle(**diesel_data), # Instantiate vehicle
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
        'error', # Should be present, hopefully None
        'analysis_years',
        'electric_annual_costs_undiscounted', # Updated key
        'diesel_annual_costs_undiscounted', # Updated key
        'electric_annual_costs_discounted', # Updated key
        'diesel_annual_costs_discounted', # Updated key
        'electric_total_tco',
        'diesel_total_tco',
        'electric_lcod',
        'diesel_lcod',
        'parity_year'
    ]
    # Check if actual keys contain all expected keys
    missing_keys = [key for key in expected_keys if key not in results]
    assert not missing_keys, f"Missing expected keys in results: {missing_keys}"
    # Optionally, check for unexpected extra keys if strictness is needed
    # extra_keys = [key for key in results if key not in expected_keys]
    # assert not extra_keys, f"Found unexpected keys in results: {extra_keys}"

def test_calculate_dataframe_shape(calculator, basic_scenario):
    """Tests the shape of the annual cost DataFrames."""
    results = calculator.calculate(basic_scenario)
    years = basic_scenario.analysis_years

    # Get component names dynamically from the calculator (safer than hardcoding)
    ev_components = calculator._get_applicable_components(basic_scenario.electric_vehicle, basic_scenario)
    diesel_components = calculator._get_applicable_components(basic_scenario.diesel_vehicle, basic_scenario)
    ev_comp_names = [comp.__class__.__name__ for comp in ev_components]
    diesel_comp_names = [comp.__class__.__name__ for comp in diesel_components]

    # +1 for Year, +1 for Total column
    expected_ev_cols = len(ev_comp_names) + 2 
    expected_diesel_cols = len(diesel_comp_names) + 2

    # Check undiscounted dataframe first
    df_ev_undisc = results['electric_annual_costs_undiscounted']
    df_diesel_undisc = results['diesel_annual_costs_undiscounted']
    
    assert isinstance(df_ev_undisc, pd.DataFrame), "EV undiscounted costs should be a DataFrame"
    assert isinstance(df_diesel_undisc, pd.DataFrame), "Diesel undiscounted costs should be a DataFrame"
    assert df_ev_undisc.shape == (years, expected_ev_cols), f"EV undiscounted shape mismatch. Expected: ({years}, {expected_ev_cols}), Got: {df_ev_undisc.shape}"
    assert df_diesel_undisc.shape == (years, expected_diesel_cols), f"Diesel undiscounted shape mismatch. Expected: ({years}, {expected_diesel_cols}), Got: {df_diesel_undisc.shape}"
    assert 'Year' in df_ev_undisc.columns
    assert 'Year' in df_diesel_undisc.columns
    assert 'Total' in df_ev_undisc.columns
    assert 'Total' in df_diesel_undisc.columns
    # Check if all component names are present as columns
    assert all(name in df_ev_undisc.columns for name in ev_comp_names), f"Missing EV component columns: {[n for n in ev_comp_names if n not in df_ev_undisc.columns]}"
    assert all(name in df_diesel_undisc.columns for name in diesel_comp_names), f"Missing Diesel component columns: {[n for n in diesel_comp_names if n not in df_diesel_undisc.columns]}"
    
    # Check discounted dataframe has the same shape and columns
    df_ev_disc = results['electric_annual_costs_discounted']
    df_diesel_disc = results['diesel_annual_costs_discounted']
    assert df_ev_disc.shape == df_ev_undisc.shape, "EV discounted shape should match undiscounted"
    assert df_diesel_disc.shape == df_diesel_undisc.shape, "Diesel discounted shape should match undiscounted"
    assert list(df_ev_disc.columns) == list(df_ev_undisc.columns), "EV discounted columns should match undiscounted"
    assert list(df_diesel_disc.columns) == list(df_diesel_undisc.columns), "Diesel discounted columns should match undiscounted"

def test_calculate_spot_check_values(calculator, basic_scenario):
    """Performs spot checks on specific calculated values (using undiscounted dataframe)."""
    results = calculator.calculate(basic_scenario)
    ev_costs = results['electric_annual_costs_undiscounted'] # Use undiscounted for simpler checks
    diesel_costs = results['diesel_annual_costs_undiscounted'] # Use undiscounted for simpler checks

    # Example Spot Check: Diesel Energy Cost Year 1 (undiscounted)
    # Fuel L/100km = 10.0 -> L/km = 0.10
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
    # Maintenance % = 0.01 -> 5000 * 0.01 = 50
    # Cost Year 1 (index 0) = Upfront + Maintenance = 5000 + 50 = 5050
    expected_ev_infra_y1 = 5050.0 
    assert ev_costs.loc[0, 'InfrastructureCost'] == pytest.approx(expected_ev_infra_y1)

    # Example Spot Check: Diesel Maintenance Cost Year 2 (undiscounted)
    # Maintenance cost/km = 0.05
    # Maintenance increase rate = 0.01
    # Cost/km Year 2 (index 1) = 0.05 * (1 + 0.01)^1 = 0.0505
    # Annual km = 15000
    # Maintenance Cost Year 2 = 15000 * 0.0505 = 757.5
    expected_diesel_maint_y2 = 757.5
    assert diesel_costs.loc[1, 'MaintenanceCost'] == pytest.approx(expected_diesel_maint_y2)

    # Example Spot Check: Diesel Residual Value Year 5 (undiscounted)
    # Final year of analysis (index 4)
    # Purchase price = 50000
    # Residual value % = 0.35
    # Age at end = 5 years
    # Lifespan = 15 years
    # Depreciation rate = (1 - 0.35) / 15 = 0.65 / 15 = 0.04333...
    # Current value pct = 1.0 - (0.04333... * 5) = 1.0 - 0.21666... = 0.78333...
    # Residual value = 50000 * 0.35 = 17500 (This is realized at end of life, not necessarily end of analysis)
    # The component calculates residual value based on vehicle.calculate_residual_value(age=analysis_years)
    # Age = 5 years
    calculated_rv = basic_scenario.diesel_vehicle.calculate_residual_value(age_years=5)
    expected_diesel_resid_y5 = -calculated_rv # Negative cost in the final year
    assert diesel_costs.loc[4, 'ResidualValue'] == pytest.approx(expected_diesel_resid_y5)

    # Example Spot Check: Total TCO matches sum of discounted totals
    # Use discounted dataframe for this check
    ev_costs_disc = results['electric_annual_costs_discounted']
    diesel_costs_disc = results['diesel_annual_costs_discounted']
    
    calculated_ev_total_tco = ev_costs_disc['Total'].sum()
    calculated_diesel_total_tco = diesel_costs_disc['Total'].sum()

    assert results['electric_total_tco'] == pytest.approx(calculated_ev_total_tco)
    assert results['diesel_total_tco'] == pytest.approx(calculated_diesel_total_tco)

def test_lcod_calculation(calculator, basic_scenario):
    """Tests the Levelized Cost of Driving (LCOD) calculation."""
    results = calculator.calculate(basic_scenario)
    total_km = basic_scenario.annual_mileage * basic_scenario.analysis_years

    # LCOD uses total discounted TCO
    expected_ev_lcod = results['electric_total_tco'] / total_km if total_km else 0
    expected_diesel_lcod = results['diesel_total_tco'] / total_km if total_km else 0

    assert results['electric_lcod'] == pytest.approx(expected_ev_lcod)
    assert results['diesel_lcod'] == pytest.approx(expected_diesel_lcod)
    # Allow LCOD to be zero if mileage or TCO is zero
    assert results['electric_lcod'] >= 0
    assert results['diesel_lcod'] >= 0

def test_parity_year_calculation(calculator, basic_scenario):
    """Tests the parity year calculation logic using undiscounted costs."""
    # Modify scenario slightly to ensure parity happens within the timeframe for testing
    ev_mods = basic_scenario.electric_vehicle.model_copy(update={"purchase_price": 45000})
    scenario_with_parity = basic_scenario.model_copy(update={
        "electric_vehicle": ev_mods,
        "diesel_price_increase": 0.15, # Faster increase
        "analysis_years": 10 # Longer period
    })

    results_parity = calculator.calculate(scenario_with_parity)
    # Use undiscounted results for parity check
    ev_costs_undisc = results_parity['electric_annual_costs_undiscounted']
    diesel_costs_undisc = results_parity['diesel_annual_costs_undiscounted']
    
    ev_cum_costs = ev_costs_undisc['Total'].cumsum()
    diesel_cum_costs = diesel_costs_undisc['Total'].cumsum()

    # Find the first year (1-based) where EV cumulative cost <= Diesel cumulative cost
    parity_index = np.where(ev_cum_costs <= diesel_cum_costs)[0]
    expected_parity_year = parity_index[0] + 1 if len(parity_index) > 0 else None

    assert results_parity['parity_year'] == expected_parity_year
    # This specific modified scenario should find parity
    assert expected_parity_year is not None, "Parity year was expected but not found in the modified scenario."

    # Test case where parity is never reached
    ev_expensive_mods = basic_scenario.electric_vehicle.model_copy(update={"purchase_price": 100000})
    scenario_no_parity = basic_scenario.model_copy(update={
        "electric_vehicle": ev_expensive_mods,
        "diesel_price": 1.0, # Make diesel cheap
        "diesel_price_increase": 0.01
    })
    results_no_parity = calculator.calculate(scenario_no_parity)
    assert results_no_parity['parity_year'] is None, "Parity year should be None when EV is significantly more expensive."

def test_calculate_edge_case_short_period(calculator, basic_scenario):
    """Tests calculation with a very short analysis period (1 year)."""
    scenario_short = basic_scenario.model_copy(update={'analysis_years': 1})
    results = calculator.calculate(scenario_short)
    
    assert results['electric_annual_costs_undiscounted'].shape[0] == 1
    assert results['diesel_annual_costs_undiscounted'].shape[0] == 1
    assert results['electric_annual_costs_discounted'].shape[0] == 1
    assert results['diesel_annual_costs_discounted'].shape[0] == 1
    assert results['analysis_years'] == 1
    # Check totals are calculated
    assert pd.notna(results['electric_total_tco'])
    assert pd.notna(results['diesel_total_tco'])

def test_calculate_edge_case_zero_discount(calculator, basic_scenario):
    """Tests calculation with a zero discount rate."""
    scenario_zero_discount = basic_scenario.model_copy(update={'discount_rate_real': 0.0})
    results = calculator.calculate(scenario_zero_discount)
    
    # Total TCO should be the simple sum of undiscounted annual totals
    expected_ev_total = results['electric_annual_costs_undiscounted']['Total'].sum()
    expected_diesel_total = results['diesel_annual_costs_undiscounted']['Total'].sum()
    
    assert results['electric_total_tco'] == pytest.approx(expected_ev_total)
    assert results['diesel_total_tco'] == pytest.approx(expected_diesel_total)
    
    # Discounted dataframe should be identical to undiscounted
    pd.testing.assert_frame_equal(
        results['electric_annual_costs_discounted'], 
        results['electric_annual_costs_undiscounted']
    )
    pd.testing.assert_frame_equal(
        results['diesel_annual_costs_discounted'], 
        results['diesel_annual_costs_undiscounted']
    )