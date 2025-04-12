import pytest
import pandas as pd
import numpy as np # Import numpy for approx
from tco_model.model import TCOCalculator
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
from pydantic import ValidationError # Import ValidationError

# Updated fixture with new structure and names
@pytest.fixture
def basic_scenario():
    """Provides a basic, valid Scenario object for testing."""
    ev_data = {
        "name": "Test EV",
        "vehicle_type": "rigid_bet", # Use specific type
        "base_purchase_price_aud": 60000, # Renamed
        "lifespan_years": 12, # Renamed
        "residual_value_percent_projections": {5: 60.0, 10: 40.0, 12: 40.0}, # Renamed, Scaled
        "base_registration_cost_aud": 500, # Renamed
        "energy_consumption_kwh_per_km": 0.25,
        "battery_capacity_kwh": 70.0,
        "battery_pack_cost_aud_per_kwh_projections": {2025: 150, 2030: 90}, # Renamed
        "battery_warranty_years": 8,
        "battery_cycle_life": 1500,
        "battery_depth_of_discharge_percent": 80.0, # Renamed, Scaled
        "charging_efficiency_percent": 90.0, # Renamed, Scaled
        "purchase_price_annual_decrease_rate_real": 0.01 # Renamed
    }
    diesel_data = {
        "name": "Test Diesel",
        "vehicle_type": "rigid_diesel", # Use specific type
        "base_purchase_price_aud": 50000, # Renamed
        "lifespan_years": 15, # Renamed
        "residual_value_percent_projections": {5: 50.0, 10: 30.0, 15: 15.0}, # Renamed, Scaled
        "base_registration_cost_aud": 600, # Renamed
        "fuel_consumption_l_per_100km": 10.0,
        "co2_emission_factor_kg_per_l": 2.68 # Renamed
    }
    
    scenario_dict = {
        "name": "Model Test Scenario",
        "description": "Scenario for testing TCOCalculator",
        "analysis_period_years": 5, # Renamed
        "analysis_start_year": 2025, # Renamed
        "economic_parameters": EconomicParameters(
            discount_rate_percent_real=3.0, # Renamed, Scaled
            inflation_rate_percent=2.0 # Renamed, Scaled
        ),
        "operational_parameters": OperationalParameters(
            annual_mileage_km=15000 # Renamed
        ),
        "electric_vehicle": ElectricVehicle(**ev_data),
        "diesel_vehicle": DieselVehicle(**diesel_data),
        "financing_options": FinancingOptions(
            financing_method="loan",
            down_payment_percent=10.0, # Renamed, Scaled
            loan_term_years=4, # Renamed
            loan_interest_rate_percent=8.0 # Renamed, Scaled
        ),
        "infrastructure_costs": InfrastructureCosts(
            selected_charger_cost_aud=5000, # Renamed
            selected_installation_cost_aud=1000, # Renamed
            charger_maintenance_annual_rate_percent=1.0, # Renamed, Scaled
            charger_lifespan_years=10 # Renamed
        ),
        "electricity_price_projections": ElectricityPriceProjections( # Updated structure
            selected_scenario_name="test_elec", # Renamed
            scenarios=[{"name": "test_elec", "prices": {
                2025: ElectricityPricePoint(price_aud_per_kwh_or_range=0.20),
                2030: ElectricityPricePoint(price_aud_per_kwh_or_range=0.25)
            }}]
        ),
        "diesel_price_projections": DieselPriceProjections( # Renamed, Updated structure
            selected_scenario_name="test_diesel", # Renamed
            scenarios=[{"name": "test_diesel", "data": DieselPriceScenarioData(
                price_aud_per_l_or_projection={2025: 1.50, 2030: 1.80} # Updated name
            )}]
        ),
        "maintenance_costs_detailed": MaintenanceCosts( # Updated structure
            costs_by_type={
                "rigid_bet": MaintenanceDetail(annual_cost_min_aud=500, annual_cost_max_aud=1000), # Updated names
                "rigid_diesel": MaintenanceDetail(annual_cost_min_aud=1500, annual_cost_max_aud=3000) # Updated names
            }
        ),
        "insurance_registration_costs": InsuranceRegistrationCosts( # Renamed, Updated structure
            electric=InsuranceRegistrationDetail(base_annual_cost_aud=10000, annual_rate_percent_of_value=0), # Updated names
            diesel=InsuranceRegistrationDetail(base_annual_cost_aud=7000, annual_rate_percent_of_value=0) # Updated names
        ),
        "carbon_tax_config": CarbonTaxConfig( # Updated structure
            include_carbon_tax=True, # Renamed
            initial_rate_aud_per_tonne_co2e=30.0, # Renamed
            annual_increase_rate_percent=5.0 # Renamed, Scaled
        ),
        "road_user_charge_config": RoadUserChargeConfig( # Updated structure
            include_road_user_charge=True, # Renamed
            initial_charge_aud_per_km=0.05, # Renamed
            annual_increase_rate_percent=1.0 # Renamed, Scaled
        ),
        "general_cost_increase_rates": GeneralCostIncreaseRates( # Updated structure
            maintenance_annual_increase_rate_percent=1.0, # Renamed, Scaled
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

    # Add battery projections separately as it's expected at the top level by Scenario model
    scenario_dict['battery_pack_cost_aud_per_kwh_projections'] = ev_data['battery_pack_cost_aud_per_kwh_projections']

    try:
        return Scenario(**scenario_dict)
    except ValidationError as e:
        print(f"Validation Error creating basic_scenario fixture: {e}")
        pytest.fail(f"Fixture basic_scenario failed validation: {e}")

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
        'analysis_period_years', # Renamed key
        'electric_annual_costs_undiscounted',
        'diesel_annual_costs_undiscounted',
        'electric_annual_costs_discounted',
        'diesel_annual_costs_discounted',
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
    years = basic_scenario.analysis_period_years # Use updated attribute name

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
    ev_costs = results['electric_annual_costs_undiscounted']
    diesel_costs = results['diesel_annual_costs_undiscounted']

    # Example Spot Check: Diesel Energy Cost Year 1 (undiscounted)
    # Use updated attribute name
    annual_mileage = basic_scenario.operational_parameters.annual_mileage_km
    # Access fuel consumption per km directly from vehicle object
    fuel_l_per_km = basic_scenario.diesel_vehicle.fuel_consumption_l_per_km
    annual_l = annual_mileage * fuel_l_per_km
    # Diesel price Year 1 (index 0)
    diesel_price_y1 = basic_scenario.get_annual_price('diesel_price_aud_per_l', 0)
    expected_diesel_energy_y1 = annual_l * diesel_price_y1
    assert diesel_costs.loc[0, 'EnergyCost'] == pytest.approx(expected_diesel_energy_y1)

    # Example Spot Check: EV Acquisition Cost Year 1 (undiscounted)
    # Financing method is 'loan'
    # Use updated attribute names
    down_payment_fraction = basic_scenario.financing_options.down_payment_percent / 100.0
    expected_ev_acq_y1 = basic_scenario.electric_vehicle.base_purchase_price_aud * down_payment_fraction
    assert ev_costs.loc[0, 'AcquisitionCost'] == pytest.approx(expected_ev_acq_y1)

    # Example Spot Check: EV Infrastructure Cost Year 1 (undiscounted)
    # Use updated attribute names
    infra = basic_scenario.infrastructure_costs
    capital_cost = infra.selected_charger_cost_aud + infra.selected_installation_cost_aud
    lifespan = infra.charger_lifespan_years
    amortized_capital = capital_cost / lifespan if lifespan > 0 else 0
    # Use updated attribute name and scale
    maint_rate_fraction = infra.charger_maintenance_annual_rate_percent / 100.0
    base_maint = capital_cost * maint_rate_fraction
    # Use updated attribute name and scale for increase rate
    maint_increase_rate_fraction = basic_scenario.general_cost_increase_rates.maintenance_annual_increase_rate_percent / 100.0
    maintenance_cost_y1 = base_maint * (1 + maint_increase_rate_fraction) ** 0 # year_index = 0
    expected_ev_infra_y1 = amortized_capital + maintenance_cost_y1
    assert ev_costs.loc[0, 'InfrastructureCost'] == pytest.approx(expected_ev_infra_y1)

    # Example Spot Check: Diesel Maintenance Cost Year 2 (undiscounted)
    # Use updated attribute names and structure
    maint_details = basic_scenario.maintenance_costs_detailed.costs_by_type['rigid_diesel']
    base_avg_maint = (maint_details.annual_cost_min_aud + maint_details.annual_cost_max_aud) / 2.0
    # Use updated attribute name and scale for increase rate
    maint_increase_rate_fraction = basic_scenario.general_cost_increase_rates.maintenance_annual_increase_rate_percent / 100.0
    expected_diesel_maint_y2 = base_avg_maint * (1 + maint_increase_rate_fraction) ** 1 # year_index = 1
    assert diesel_costs.loc[1, 'MaintenanceCost'] == pytest.approx(expected_diesel_maint_y2)

    # Example Spot Check: Diesel Residual Value Year 5 (undiscounted)
    # Final year of analysis (index 4)
    analysis_years = basic_scenario.analysis_period_years # Use updated name
    # Use updated method name
    calculated_rv = basic_scenario.diesel_vehicle.calculate_residual_value_aud(age_years=analysis_years)
    expected_diesel_resid_y5 = -calculated_rv # Negative cost in the final year
    # Index is final_year_index = analysis_years - 1 = 4
    assert diesel_costs.loc[analysis_years - 1, 'ResidualValue'] == pytest.approx(expected_diesel_resid_y5)

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
    # Use updated attribute names
    total_km = basic_scenario.operational_parameters.annual_mileage_km * basic_scenario.analysis_period_years

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
    # Modify scenario slightly
    # Use updated attribute name
    ev_mods = basic_scenario.electric_vehicle.model_copy(update={"base_purchase_price_aud": 45000})
    # Create updated DieselPriceProjections structure
    new_diesel_proj = DieselPriceProjections(
        selected_scenario_name="faster_increase",
        scenarios=[{"name": "faster_increase", "data": DieselPriceScenarioData(
            price_aud_per_l_or_projection={2025: 1.50, 2030: 2.50, 2035: 3.50}, # Faster increase example
            annual_increase_rate_percent=15.0 # Explicit increase rate example (Scaled 0-100)
        )}]
    )
    scenario_with_parity = basic_scenario.model_copy(update={
        "electric_vehicle": ev_mods,
        "diesel_price_projections": new_diesel_proj, # Use updated structure
        "analysis_period_years": 10 # Use updated attribute name
    })

    results_parity = calculator.calculate(scenario_with_parity)
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
    # Use updated attribute name
    ev_expensive_mods = basic_scenario.electric_vehicle.model_copy(update={"base_purchase_price_aud": 100000})
    # Create updated DieselPriceProjections structure for cheap diesel
    cheap_diesel_proj = DieselPriceProjections(
        selected_scenario_name="cheap_slow",
        scenarios=[{"name": "cheap_slow", "data": DieselPriceScenarioData(
            price_aud_per_l_or_projection={2025: 1.0, 2030: 1.1, 2035: 1.2}, # Cheap, slow increase
            annual_increase_rate_percent=1.0 # Scaled 0-100
        )}]
    )
    scenario_no_parity = basic_scenario.model_copy(update={
        "electric_vehicle": ev_expensive_mods,
        "diesel_price_projections": cheap_diesel_proj, # Use updated structure
        "analysis_period_years": 10 # Use updated attribute name
    })
    results_no_parity = calculator.calculate(scenario_no_parity)
    assert results_no_parity['parity_year'] is None, "Parity year should be None when EV is significantly more expensive."

def test_calculate_edge_case_short_period(calculator, basic_scenario):
    """Tests calculation with a very short analysis period (1 year)."""
    # Use updated attribute name
    scenario_short = basic_scenario.model_copy(update={'analysis_period_years': 1})
    results = calculator.calculate(scenario_short)
    
    assert results['electric_annual_costs_undiscounted'].shape[0] == 1
    assert results['diesel_annual_costs_undiscounted'].shape[0] == 1
    assert results['electric_annual_costs_discounted'].shape[0] == 1
    assert results['diesel_annual_costs_discounted'].shape[0] == 1
    assert results['analysis_period_years'] == 1 # Check renamed key
    # Check totals are calculated
    assert pd.notna(results['electric_total_tco'])
    assert pd.notna(results['diesel_total_tco'])

def test_calculate_edge_case_zero_discount(calculator, basic_scenario):
    """Tests calculation with a zero discount rate."""
    # Create updated EconomicParameters object
    zero_discount_params = basic_scenario.economic_parameters.model_copy(update={'discount_rate_percent_real': 0.0})
    # Use updated attribute name and nested model
    scenario_zero_discount = basic_scenario.model_copy(update={'economic_parameters': zero_discount_params})
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