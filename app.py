# app.py
import streamlit as st
import copy  # To copy scenario params from session state
from pydantic import ValidationError

# Placeholder imports - replace with actual implementations later
# from ui.layout import create_layout
# from ui.outputs import display_results
# from ui.state import initialize_session_state
# from tco_model.model import TCOCalculator
# from tco_model.scenarios import Scenario

# Import actual implementations
from ui.state import initialize_session_state
from ui.inputs import create_input_sidebar
from ui.outputs import display_results # Import the real function
from tco_model.model import TCOCalculator
from tco_model.scenarios import Scenario

# --- Placeholder Functions --- 
# Removed placeholder initialize_session_state
# Removed placeholder create_layout
# Removed placeholder create_input_sidebar
# Removed placeholder TCOCalculator class
# Removed placeholder Scenario class

def _preprocess_sidebar_params(flat_params: dict) -> dict:
    """Convert sidebar params (flat dict, % as numbers) to nested structure for Scenario model."""
    processed = flat_params.copy()

    # 1. Convert percentages to decimals
    percent_keys = [
        'discount_rate', 'inflation_rate', 'interest_rate', 
        'down_payment_pct', 'electric_residual_value_pct', 
        'diesel_residual_value_pct', 'battery_replacement_threshold'
    ]
    for key in percent_keys:
        if key in processed and isinstance(processed[key], (int, float)):
            if processed[key] is not None: # Check for None explicitly
                processed[key] = processed[key] / 100.0

    # 2. Handle conditional battery replacement logic
    if 'battery_replace_mode' in st.session_state: # Check radio button state
        if st.session_state['battery_replace_mode'] == "Fixed Year":
            processed['battery_replacement_threshold'] = None 
            # Ensure battery_replacement_year exists and is valid, else Pydantic validation fails
        else: # Capacity Threshold selected
            processed['battery_replacement_year'] = None
            # Ensure battery_replacement_threshold exists and is valid (already converted if needed)
            # If it was None originally and threshold mode is selected, Pydantic validation will catch it if required

    # 3. Restructure into nested format for Scenario model
    nested_params = {}
    ev_params = {}
    diesel_params = {}

    # Define keys for each section
    # Based on tco_model/scenarios.py and tco_model/vehicles.py structure
    scenario_keys = [
        'name', 'description', 'start_year', 'end_year', 'discount_rate',
        'inflation_rate', 'financing_method', 'loan_term', 'interest_rate', 
        'down_payment_pct', 'annual_mileage', 'electricity_prices', 'diesel_prices',
        'charger_cost', 'charger_installation_cost', 'charger_lifespan',
        'annual_registration_cost', 'enable_battery_replacement', 
        'battery_replacement_threshold', 'battery_replacement_year'
    ] 
    ev_keys = [
        'electric_vehicle_name', 'electric_vehicle_price', 
        'electric_vehicle_battery_capacity', 'electric_vehicle_energy_consumption', 
        'electric_vehicle_battery_warranty', 'electric_residual_value_pct',
        'electric_maintenance_cost_per_km', 'electric_insurance_cost_factor'
    ]
    diesel_keys = [
        'diesel_vehicle_name', 'diesel_vehicle_price', 
        'diesel_vehicle_fuel_consumption', 'diesel_residual_value_pct', 
        'diesel_maintenance_cost_per_km', 'diesel_insurance_cost_factor'
    ]

    # Populate nested dictionaries
    for key, value in processed.items():
        if key in scenario_keys:
            nested_params[key] = value
        elif key in ev_keys:
            # Remove prefix and store in ev_params
            clean_key = key.replace('electric_vehicle_', '').replace('electric_','') # Tidy up key name
            ev_params[clean_key] = value
        elif key in diesel_keys:
            # Remove prefix and store in diesel_params
            clean_key = key.replace('diesel_vehicle_', '').replace('diesel_','') # Tidy up key name
            diesel_params[clean_key] = value
        # Ignore keys not relevant to the Scenario model (like 'battery_replace_mode')

    # Add the nested vehicle dictionaries
    nested_params['electric_vehicle'] = ev_params
    nested_params['diesel_vehicle'] = diesel_params
    
    # Rename keys to match Scenario model fields exactly
    key_renames = {
        'name': 'name', # Example if a rename was needed
        'price': 'purchase_price',
        'battery_capacity': 'battery_capacity_kwh',
        'energy_consumption': 'energy_consumption_kwh_per_km',
        'battery_warranty': 'battery_warranty_years',
        'residual_value_pct': 'residual_value_percent', # Pydantic field uses 'percent'
        'maintenance_cost_per_km': 'maintenance_cost_per_km', 
        'insurance_cost_factor': 'insurance_cost_percent', # Pydantic field uses 'percent'
        'fuel_consumption': 'fuel_consumption_l_per_100km'
    }

    # Apply renames within nested dicts
    nested_params['electric_vehicle'] = {key_renames.get(k, k): v for k, v in nested_params['electric_vehicle'].items()}
    nested_params['diesel_vehicle'] = {key_renames.get(k, k): v for k, v in nested_params['diesel_vehicle'].items()}

    # Rename top-level keys if necessary (e.g., discount_rate to discount_rate_real)
    if 'discount_rate' in nested_params:
        nested_params['discount_rate_real'] = nested_params.pop('discount_rate')
    # Rename others if needed... 
    # Assume other top-level keys match for now, or add more renames here.

    return nested_params

# --- Main Application Logic --- 
def main():
    # Setup page configuration
    st.set_page_config(
        page_title="Heavy Vehicle TCO Modeller",
        page_icon="🚚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("Australian Heavy Vehicle TCO Modeller")
    st.markdown("""
    Compare the Total Cost of Ownership (TCO) for Battery Electric Trucks (BETs) 
    and Internal Combustion Engine (ICE) diesel trucks in Australia.
    
    Adjust parameters in the sidebar to customize your analysis.
    """)

    # Initialize session state (loads default scenario if needed)
    initialize_session_state()
    
    # Create input sidebar - this directly modifies st.session_state['scenario_params']
    create_input_sidebar()
    
    # --- Create Scenario from current state ---
    scenario = None
    results = None
    try:
        # 1. Get a copy of the current flat params from session state
        current_flat_params = st.session_state['scenario_params'].copy()
        
        # 2. Preprocess & restructure params
        processed_nested_params = _preprocess_sidebar_params(current_flat_params)

        # 3. Validate and create the Scenario object using the nested structure
        scenario = Scenario(**processed_nested_params)
        st.sidebar.success("Scenario parameters loaded successfully.")

    except ValidationError as e:
        st.sidebar.error("Scenario Configuration Error:")
        # Display specific validation errors nicely
        error_details = e.errors()
        for error in error_details:
            field = " -> ".join(map(str, error['loc'])) # Handle nested fields if any
            st.sidebar.error(f"- **{field}**: {error['msg']}")
        # Prevent calculation if scenario is invalid
        st.stop()
    except Exception as e:
        st.sidebar.error(f"An unexpected error occurred creating the scenario: {e}")
        st.stop()

    # --- Perform Calculation ---
    if scenario: # Only proceed if scenario creation was successful
        calculator = TCOCalculator()
        try:
            # Use st.spinner for feedback during calculation
            with st.spinner("Calculating TCO... Please wait."):
                results = calculator.calculate(scenario)
        except Exception as e:
            st.error(f"Error during TCO calculation: {e}")
            # Store error in results dict for display
            results = {"error": str(e)}
    
    # --- Display Results --- 
    display_results(results) 

if __name__ == "__main__":
    main()
