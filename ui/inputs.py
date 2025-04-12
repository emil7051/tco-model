# Standard library imports
import datetime
import logging

# Third-party imports
import streamlit as st

# Application-specific imports
from config.constants import (
    DEFAULT_ANALYSIS_YEARS, DEFAULT_ANNUAL_MILEAGE, DEFAULT_BATTERY_REPLACEMENT_THRESHOLD,
    DEFAULT_BATTERY_REPLACEMENT_YEAR, DEFAULT_DESCRIPTION, DEFAULT_DIESEL_FUEL_CONSUMPTION,
    DEFAULT_DIESEL_NAME, DEFAULT_DIESEL_PRICE, DEFAULT_DISCOUNT_RATE, DEFAULT_DOWN_PAYMENT_PCT,
    DEFAULT_EV_BATTERY_CAPACITY, DEFAULT_EV_ENERGY_CONSUMPTION, DEFAULT_EV_NAME, 
    DEFAULT_EV_PRICE, DEFAULT_INFLATION_RATE, DEFAULT_INTEREST_RATE, DEFAULT_SCENARIO_NAME,
    CURRENT_YEAR, MAX_ANALYSIS_YEARS, MIN_ANALYSIS_YEARS
)

logger = logging.getLogger(__name__)

def create_input_sidebar():
    """Creates the sidebar UI for inputting TCO scenario parameters."""
    st.sidebar.title("Scenario Parameters")

    # Ensure scenario_params exists in session state
    if 'scenario_params' not in st.session_state:
        st.sidebar.error("Scenario parameters not initialized. Please run the app main script.")
        st.stop() # Stop execution if state isn't initialized

    # Use a local variable for easier access, especially for setting initial values.
    # Streamlit widgets will update the session_state directly via their keys.
    params = st.session_state['scenario_params'] 
    # Make a deep copy to avoid modifying the original state unintentionally if needed
    # params = copy.deepcopy(st.session_state['scenario_params']) 

    with st.sidebar.expander("General", expanded=True):
        # Use simple flat keys matching the intended session state structure
        st.text_input("Scenario Name", key="name")
        st.number_input(
            "Start Year", 
            min_value=CURRENT_YEAR, 
            max_value=CURRENT_YEAR + 30,
            step=1, 
            format="%d", 
            key="start_year",
            value=params.get('start_year', CURRENT_YEAR) # Default from state or current year
        )
        st.number_input(
            "Life Cycle (Years)", 
            min_value=MIN_ANALYSIS_YEARS, 
            max_value=MAX_ANALYSIS_YEARS, # Set max value to 30
            step=1, 
            format="%d", 
            key="analysis_years", 
            help="Duration of the analysis in years (1-30). Default is 15.",
            value=params.get('analysis_years', DEFAULT_ANALYSIS_YEARS) # Ensure default is used
        )
        st.text_area("Description", key="description", value=params.get('description', DEFAULT_DESCRIPTION))


    with st.sidebar.expander("Economic", expanded=False):
        # Use params for initial value, key modifies session_state['discount_rate']
        # Value from session state (params) is already scaled to percentage in ui/state.py
        st.number_input("Discount Rate (%)", min_value=0.0, max_value=20.0, step=0.1, format="%.1f", key="discount_rate", help="Real discount rate (0-20%).", value=params.get('discount_rate', DEFAULT_DISCOUNT_RATE))
        st.number_input("Inflation Rate (%)", min_value=0.0, max_value=10.0, step=0.1, format="%.1f", key="inflation_rate", help="General inflation rate (0-10%).", value=params.get('inflation_rate', DEFAULT_INFLATION_RATE))
        st.selectbox("Financing Method", options=["loan", "cash"], key="financing_method", index=0 if params.get('financing_method') == 'loan' else 1)
        # Check the current value in session state for conditional display
        if st.session_state['financing_method'] == 'loan': 
            st.number_input("Loan Term (years)", min_value=1, max_value=15, step=1, key="loan_term", value=params.get('loan_term', 5))
            st.number_input("Loan Interest Rate (%)", min_value=0.0, max_value=20.0, step=0.1, format="%.1f", key="interest_rate", help="Loan interest rate (0-20%).", value=params.get('interest_rate', DEFAULT_INTEREST_RATE))
            st.number_input("Down Payment (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.1f", key="down_payment_pct", help="Down payment percentage (0-100%).", value=params.get('down_payment_pct', DEFAULT_DOWN_PAYMENT_PCT))


    with st.sidebar.expander("Operational", expanded=True):
        st.number_input("Annual Mileage (km)", min_value=0.0, step=1000.0, format="%.0f", key="annual_mileage", value=params.get('annual_mileage', DEFAULT_ANNUAL_MILEAGE))


    with st.sidebar.expander("Electric Vehicle", expanded=True):
        st.text_input("EV Name/Model", key="electric_vehicle_name", value=params.get('electric_vehicle_name', DEFAULT_EV_NAME))
        st.number_input("EV Purchase Price (AUD)", min_value=0.0, step=1000.0, format="%.0f", key="electric_vehicle_price", value=params.get('electric_vehicle_price', DEFAULT_EV_PRICE))
        st.number_input("EV Battery Capacity (kWh)", min_value=0.0, step=1.0, format="%.1f", key="electric_vehicle_battery_capacity", value=params.get('electric_vehicle_battery_capacity', DEFAULT_EV_BATTERY_CAPACITY))
        st.number_input("EV Energy Consumption (kWh/km)", min_value=0.0, step=0.01, format="%.2f", key="electric_vehicle_energy_consumption", value=params.get('electric_vehicle_energy_consumption', DEFAULT_EV_ENERGY_CONSUMPTION))
        st.number_input("EV Battery Warranty (years)", min_value=0, step=1, key="electric_vehicle_battery_warranty", value=params.get('electric_vehicle_battery_warranty', 8))
        # Residual value is now loaded from projections - display info or omit input
        if 'electric_vehicle_residual_value_projections' in params:
             st.caption("EV Residual Value: Loaded from scenario")
             # st.write(params['electric_vehicle_residual_value_projections']) # Optionally display the dict
        # Removed: st.number_input("EV Residual Value (%)", ...) 


    with st.sidebar.expander("Diesel Vehicle", expanded=True):
        st.text_input("Diesel Name/Model", key="diesel_vehicle_name", value=params.get('diesel_vehicle_name', DEFAULT_DIESEL_NAME))
        st.number_input("Diesel Purchase Price (AUD)", min_value=0.0, step=1000.0, format="%.0f", key="diesel_vehicle_price", value=params.get('diesel_vehicle_price', DEFAULT_DIESEL_PRICE))
        st.number_input("Diesel Fuel Consumption (L/100km)", min_value=0.0, step=0.1, format="%.1f", key="diesel_vehicle_fuel_consumption", value=params.get('diesel_vehicle_fuel_consumption', DEFAULT_DIESEL_FUEL_CONSUMPTION))
        # Residual value is now loaded from projections - display info or omit input
        if 'diesel_vehicle_residual_value_projections' in params:
            st.caption("Diesel Residual Value: Loaded from scenario")
            # st.write(params['diesel_vehicle_residual_value_projections']) # Optionally display the dict
        # Removed: st.number_input("Diesel Residual Value (%)", ...)


    with st.sidebar.expander("Infrastructure (EV)", expanded=False):
        # Use the flattened keys from state.py ('charger_cost', 'charger_installation_cost', etc.)
        st.number_input("Charger Hardware Cost (AUD)", min_value=0.0, step=100.0, format="%.0f", key="charger_cost", value=float(params.get('charger_cost', 50000.0)))
        st.number_input("Charger Installation Cost (AUD)", min_value=0.0, step=100.0, format="%.0f", key="charger_installation_cost", value=float(params.get('charger_installation_cost', 55000.0)))
        st.number_input("Charger Lifespan (years)", min_value=1, step=1, key="charger_lifespan", value=params.get('charger_lifespan', 10))
        st.number_input("Charger Maintenance (% of Capital)", min_value=0.0, max_value=10.0, step=0.1, format="%.1f", key="charger_maintenance_percent", help="Annual maintenance cost as % of hardware + install cost (0-10%).", value=params.get('charger_maintenance_percent', 1.5))


    # Maintenance and Insurance/Reg are now loaded from scenario file structures
    # These expanders could display the loaded values or allow selection of type (e.g. rigid vs articulated)
    # For now, just indicate they are loaded from the scenario.
    with st.sidebar.expander("Maintenance & Other Costs", expanded=False):
        st.caption("Maintenance: Loaded from scenario (based on vehicle type)")
        st.caption("Insurance: Loaded from scenario (based on vehicle type)")
        st.number_input("Annual Registration Cost (AUD)", min_value=0.0, step=100.0, format="%.0f", key="annual_registration_cost", value=params.get('annual_registration_cost', 5000.0))
        st.number_input("Carbon Tax Rate (AUD/tonne CO2e)", min_value=0.0, step=1.0, format="%.2f", key="carbon_tax_rate", value=params.get('carbon_tax_rate', 30.0))
        st.number_input("Road User Charge (AUD/km)", min_value=0.0, step=0.01, format="%.2f", key="road_user_charge", value=params.get('road_user_charge', 0.0))
        # Add inputs for the general increase rates
        st.number_input("Maintenance Cost Increase Rate (%/yr)", min_value=0.0, step=0.1, format="%.1f", key="maintenance_increase_rate", help="Annual real increase for maintenance.", value=params.get('maintenance_increase_rate', 0.0) * 100)
        st.number_input("Insurance Cost Increase Rate (%/yr)", min_value=0.0, step=0.1, format="%.1f", key="insurance_increase_rate", help="Annual real increase for insurance.", value=params.get('insurance_increase_rate', 0.0) * 100)
        st.number_input("Registration Cost Increase Rate (%/yr)", min_value=0.0, step=0.1, format="%.1f", key="registration_increase_rate", help="Annual real increase for registration.", value=params.get('registration_increase_rate', 0.0) * 100)
        st.number_input("Carbon Tax Increase Rate (%/yr)", min_value=0.0, step=0.1, format="%.1f", key="carbon_tax_increase_rate", help="Annual real increase for carbon tax.", value=params.get('carbon_tax_increase_rate', 0.0) * 100)
        st.number_input("Road User Charge Increase Rate (%/yr)", min_value=0.0, step=0.1, format="%.1f", key="road_user_charge_increase_rate", help="Annual real increase for RUC.", value=params.get('road_user_charge_increase_rate', 0.0) * 100)


    # New expander for energy pricing using projections
    with st.sidebar.expander("Energy Pricing", expanded=False):
        # Electricity Scenario Selection
        elec_scenarios = list(params.get('electricity_price_projections', {}).keys())
        selected_elec = params.get('selected_electricity_scenario', elec_scenarios[0] if elec_scenarios else None)
        elec_index = elec_scenarios.index(selected_elec) if selected_elec in elec_scenarios else 0
        if elec_scenarios:
            st.selectbox("Electricity Price Scenario", options=elec_scenarios, key="selected_electricity_scenario", index=elec_index)
        else:
            st.warning("No electricity price projections found in scenario.")
        
        # Diesel Scenario Selection
        diesel_scenarios = list(params.get('diesel_price_scenarios', {}).keys())
        selected_diesel = params.get('selected_diesel_scenario', diesel_scenarios[0] if diesel_scenarios else None)
        diesel_index = diesel_scenarios.index(selected_diesel) if selected_diesel in diesel_scenarios else 0
        if diesel_scenarios:
            st.selectbox("Diesel Price Scenario", options=diesel_scenarios, key="selected_diesel_scenario", index=diesel_index)
        else:
            st.warning("No diesel price scenarios found in scenario.")
        
        # Optionally, keep base price inputs for manual override (commented out)
        # st.number_input("Base Electricity Price (AUD/kWh)", min_value=0.0, step=0.01, format="%.2f", key="electricity_price_base", value=params.get('electricity_price_base', 0.0))
        # st.number_input("Base Diesel Price (AUD/L)", min_value=0.0, step=0.01, format="%.2f", key="diesel_price_base", value=params.get('diesel_price_base', 0.0))


    with st.sidebar.expander("Battery Replacement (EV)", expanded=False):
        st.checkbox("Enable Battery Replacement", key="enable_battery_replacement", value=params.get('enable_battery_replacement', True))
        # Use key directly with st.session_state for conditional check
        if st.session_state['enable_battery_replacement']:
            replace_mode = st.radio("Replacement Trigger", ["Fixed Year", "Capacity Threshold"], key="battery_replace_mode")
            if replace_mode == "Fixed Year":
                # Determine min/max years based on current year and analysis duration
                start_year = params.get('start_year', CURRENT_YEAR)
                analysis_years = params.get('analysis_years', 1) # Default to 1 if not set
                min_replace_year = start_year # Cannot replace before start
                max_replace_year = start_year + analysis_years - 1
                # Calculate the 1-based index year relative to analysis start
                min_replace_index = 1
                max_replace_index = analysis_years
                st.number_input("Battery Replacement Year (Index)", 
                                min_value=min_replace_index, 
                                max_value=max_replace_index, 
                                step=1, 
                                key="battery_replacement_year", 
                                help=f"Year index within analysis period (1 to {max_replace_index}).",
                                value=params.get('battery_replacement_year', DEFAULT_BATTERY_REPLACEMENT_YEAR) # Default replacement year index
                                )
            else: # Capacity Threshold
                # Use .get() for safety, provide default 0.0. Value from params is already scaled.
                initial_threshold_display = (params.get('battery_replacement_threshold', 0.0) or 0.0)
                st.number_input("Battery Capacity Threshold (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.1f", key="battery_replacement_threshold", help="Replace when capacity drops below this % (0-100%).", value=initial_threshold_display) 

# Comments about percentage conversion and flattening logic are crucial for understanding state management.
# These processes happen in ui/state.py (_flatten_scenario_dict) and app.py (_preprocess_sidebar_params)
