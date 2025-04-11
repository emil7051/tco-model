import streamlit as st
import datetime # Add datetime import

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

    with st.sidebar.expander("General", expanded=True):
        # Use simple flat keys matching the intended session state structure
        # Removed: st.text_input("Scenario Name", key="name")
        # Removed: st.number_input("Start Year", step=1, format="%d", key="start_year")
        # Set start year programmatically later
        # Change End Year to Life Cycle (Years)
        st.number_input(
            "Life Cycle (Years)", 
            min_value=1, 
            max_value=30, # Set max value to 30
            step=1, 
            format="%d", 
            key="analysis_years", 
            help="Duration of the analysis in years (1-30). Default is 15.",
            value=params.get('analysis_years', 15) # Ensure default is used
        )
        st.text_area("Description", key="description")


    with st.sidebar.expander("Economic", expanded=False):
        # Use params for initial value, key modifies session_state['discount_rate']
        # Value from session state (params) is already scaled to percentage in ui/state.py
        st.number_input("Discount Rate (%)", min_value=0.0, max_value=20.0, step=0.1, format="%.1f", key="discount_rate", help="Real discount rate (0-20%).", value=params.get('discount_rate', 0.0))
        st.number_input("Inflation Rate (%)", min_value=0.0, max_value=10.0, step=0.1, format="%.1f", key="inflation_rate", help="General inflation rate (0-10%).", value=params.get('inflation_rate', 0.0))
        st.selectbox("Financing Method", options=["loan", "cash"], key="financing_method")
        # Check the current value in session state for conditional display
        if st.session_state.scenario_params['financing_method'] == 'loan':
            st.number_input("Loan Term (years)", min_value=1, max_value=15, step=1, key="loan_term")
            st.number_input("Loan Interest Rate (%)", min_value=0.0, max_value=20.0, step=0.1, format="%.1f", key="interest_rate", help="Loan interest rate (0-20%).", value=params.get('interest_rate', 0.0))
            st.number_input("Down Payment (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.1f", key="down_payment_pct", help="Down payment percentage (0-100%).", value=params.get('down_payment_pct', 0.0))


    with st.sidebar.expander("Operational", expanded=True):
        st.number_input("Annual Mileage (km)", min_value=0.0, step=1000.0, format="%.0f", key="annual_mileage")


    with st.sidebar.expander("Electric Vehicle", expanded=True):
        st.text_input("EV Name/Model", key="electric_vehicle_name")
        st.number_input("EV Purchase Price (AUD)", min_value=0.0, step=1000.0, format="%.0f", key="electric_vehicle_price")
        st.number_input("EV Battery Capacity (kWh)", min_value=0.0, step=1.0, format="%.1f", key="electric_vehicle_battery_capacity")
        st.number_input("EV Energy Consumption (kWh/km)", min_value=0.0, step=0.01, format="%.2f", key="electric_vehicle_energy_consumption")
        st.number_input("EV Battery Warranty (years)", min_value=0, step=1, key="electric_vehicle_battery_warranty")
        st.number_input("EV Residual Value (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.1f", key="electric_residual_value_pct", help="Residual value as % of purchase price (0-100%).", value=params.get('electric_residual_value_pct', 0.0))


    with st.sidebar.expander("Diesel Vehicle", expanded=True):
        st.text_input("Diesel Name/Model", key="diesel_vehicle_name")
        st.number_input("Diesel Purchase Price (AUD)", min_value=0.0, step=1000.0, format="%.0f", key="diesel_vehicle_price")
        st.number_input("Diesel Fuel Consumption (L/100km)", min_value=0.0, step=0.1, format="%.1f", key="diesel_vehicle_fuel_consumption")
        st.number_input("Diesel Residual Value (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.1f", key="diesel_residual_value_pct", help="Residual value as % of purchase price (0-100%).", value=params.get('diesel_residual_value_pct', 0.0))


    with st.sidebar.expander("Infrastructure (EV)", expanded=False):
        st.number_input("Charger Hardware Cost (AUD)", min_value=0.0, step=100.0, format="%.0f", key="charger_cost")
        st.number_input("Charger Installation Cost (AUD)", min_value=0.0, step=100.0, format="%.0f", key="charger_installation_cost")
        st.number_input("Charger Lifespan (years)", min_value=1, step=1, key="charger_lifespan")


    with st.sidebar.expander("Maintenance", expanded=False):
        st.number_input("EV Maintenance Cost (AUD/km)", min_value=0.0, step=0.01, format="%.2f", key="electric_maintenance_cost_per_km")
        st.number_input("Diesel Maintenance Cost (AUD/km)", min_value=0.0, step=0.01, format="%.2f", key="diesel_maintenance_cost_per_km")


    with st.sidebar.expander("Insurance & Registration", expanded=False):
        st.number_input("EV Insurance Cost Factor", min_value=0.0, step=0.01, format="%.2f", key="electric_insurance_cost_factor", help="Factor relative to base cost (e.g., 1.0 = base, 1.1 = 10% higher).")
        st.number_input("Diesel Insurance Cost Factor", min_value=0.0, step=0.01, format="%.2f", key="diesel_insurance_cost_factor", help="Factor relative to base cost.")
        st.number_input("Annual Registration Cost (AUD)", min_value=0.0, step=100.0, format="%.0f", key="annual_registration_cost")


    with st.sidebar.expander("Battery Replacement (EV)", expanded=False):
        st.checkbox("Enable Battery Replacement", key="enable_battery_replacement")
        if st.session_state.scenario_params['enable_battery_replacement']:
            replace_mode = st.radio("Replacement Trigger", ["Fixed Year", "Capacity Threshold"], key="battery_replace_mode")
            if replace_mode == "Fixed Year":
                # Determine min/max years based on current year and analysis duration
                current_year = datetime.datetime.now().year
                analysis_years = st.session_state.scenario_params.get('analysis_years', 1) # Default to 1 if not set
                max_year = current_year + analysis_years -1
                st.number_input("Battery Replacement Year", min_value=current_year, max_value=max_year, step=1, key="battery_replacement_year")
            else: # Capacity Threshold
                # Use .get() for safety, provide default 0.0. Value from params is already scaled.
                initial_threshold_display = (params.get('battery_replacement_threshold', 0.0) or 0.0)
                st.number_input("Battery Capacity Threshold (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.1f", key="battery_replacement_threshold", help="Replace when capacity drops below this % (0-100%).", value=initial_threshold_display)


    # Note: Editing electricity_prices and diesel_prices dicts requires a more complex UI
    # (e.g., editable dataframe or dynamic inputs). This is omitted for now.
    st.sidebar.caption("Note: Annual energy prices are loaded from config and not editable here.")

    # Comments about percentage conversion are kept as they explain the necessary preprocessing step.
    # ... (existing comments remain) ...
