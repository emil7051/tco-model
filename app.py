# app.py
import streamlit as st
import copy  # To copy scenario params from session state
from pydantic import ValidationError
import logging

# Placeholder imports - replace with actual implementations later
# from ui.layout import create_layout
# from ui.outputs import display_results
# from ui.state import initialize_session_state
# from tco_model.model import TCOCalculator
# from tco_model.scenarios import Scenario

# Configure logging
logger = logging.getLogger(__name__)

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
    logger.debug(f"Starting preprocessing with flat params: {processed}")

    # 1. Convert percentages back to decimals
    percent_keys = [
        'discount_rate', 'inflation_rate', 'interest_rate', 
        'down_payment_pct', 'electric_residual_value_pct', 
        'diesel_residual_value_pct', 'battery_replacement_threshold',
        # Add any other percentage fields from Scenario/Vehicle models if needed
        'charger_maintenance_percent' # Example: this is in Scenario model
    ]
    for key in percent_keys:
        # Check if the key exists and is a number (int or float)
        if key in processed and isinstance(processed[key], (int, float)):
             # Divide by 100 only if it's not None (avoid error with None/100)
             if processed[key] is not None:
                 processed[key] = processed[key] / 100.0
    logger.debug(f"Params after percentage conversion: {processed}")


    # 2. Handle conditional battery replacement logic based on radio button
    # We set the *unused* field to None based on the mode selected in the UI
    if 'battery_replace_mode' in st.session_state: 
        if st.session_state['battery_replace_mode'] == "Fixed Year":
            processed['battery_replacement_threshold'] = None 
            logger.debug("Battery mode set to 'Fixed Year', threshold set to None.")
            # Note: 'battery_replacement_year' should already exist in processed if this mode was selected in UI
        else: # Capacity Threshold selected
            processed['battery_replacement_year'] = None
            logger.debug("Battery mode set to 'Capacity Threshold', year set to None.")
            # Note: 'battery_replacement_threshold' should exist (and be converted above) if this mode was selected

    # 3. Initialize structure
    nested_params = {}
    ev_params = {}
    diesel_params = {}

    # 4. Define mapping from flat UI keys to nested structure locations and final keys
    # Add ALL required fields from Scenario, ElectricVehicle, DieselVehicle Pydantic models
    # Format: ('flat_ui_key', 'target_dict_name', 'final_model_key')
    # target_dict_name: 'scenario', 'ev', 'diesel'
    key_mapping = [
        # Scenario Top-Level
        ('name', 'scenario', 'name'),
        ('description', 'scenario', 'description'),
        ('start_year', 'scenario', 'start_year'),
        ('analysis_years', 'scenario', 'analysis_years'), # Map directly from UI input
        # ('end_year', 'scenario', 'end_year'), # We calculate analysis_years instead
        ('discount_rate', 'scenario', 'discount_rate_real'), # Rename applied later
        # ('inflation_rate', 'scenario', 'inflation_rate'), # Not in Scenario model
        ('financing_method', 'scenario', 'financing_method'),
        ('loan_term', 'scenario', 'loan_term'),
        ('interest_rate', 'scenario', 'interest_rate'),
        ('down_payment_pct', 'scenario', 'down_payment_pct'),
        ('annual_mileage', 'scenario', 'annual_mileage'),
        ('electricity_price', 'scenario', 'electricity_price'), # Required
        ('diesel_price', 'scenario', 'diesel_price'),           # Required
        ('charger_cost', 'scenario', 'charger_cost'),
        ('charger_installation_cost', 'scenario', 'charger_installation_cost'),
        ('charger_lifespan', 'scenario', 'charger_lifespan'),
        ('charger_maintenance_percent', 'scenario', 'charger_maintenance_percent'),
        ('annual_registration_cost', 'scenario', 'annual_registration_cost'), # Required top-level
        ('electric_maintenance_cost_per_km', 'scenario', 'electric_maintenance_cost_per_km'), # Required top-level
        ('diesel_maintenance_cost_per_km', 'scenario', 'diesel_maintenance_cost_per_km'),   # Required top-level
        ('electric_insurance_cost_factor', 'scenario', 'electric_insurance_cost_factor'), # Required top-level
        ('diesel_insurance_cost_factor', 'scenario', 'diesel_insurance_cost_factor'),   # Required top-level
        ('enable_battery_replacement', 'scenario', 'enable_battery_replacement'),
        ('battery_replacement_threshold', 'scenario', 'battery_replacement_threshold'),
        ('battery_replacement_year', 'scenario', 'force_battery_replacement_year'), # Rename applied later
        # Add increase rates (assuming they are in flat_params)
        ('electricity_price_increase', 'scenario', 'electricity_price_increase'),
        ('diesel_price_increase', 'scenario', 'diesel_price_increase'),
        ('carbon_tax_increase_rate', 'scenario', 'carbon_tax_increase_rate'),
        ('road_user_charge_increase_rate', 'scenario', 'road_user_charge_increase_rate'),
        ('maintenance_increase_rate', 'scenario', 'maintenance_increase_rate'),
        ('insurance_increase_rate', 'scenario', 'insurance_increase_rate'),
        ('registration_increase_rate', 'scenario', 'registration_increase_rate'),
        # Flags
        ('include_carbon_tax', 'scenario', 'include_carbon_tax'),
        ('include_road_user_charge', 'scenario', 'include_road_user_charge'),
        # Battery specific top-level
        ('battery_degradation_rate', 'scenario', 'battery_degradation_rate'),
        
        # Electric Vehicle Nested
        ('electric_vehicle_name', 'ev', 'name'),
        ('electric_vehicle_price', 'ev', 'purchase_price'), # Renamed
        ('electric_vehicle_battery_capacity', 'ev', 'battery_capacity_kwh'), # Renamed
        ('electric_vehicle_energy_consumption', 'ev', 'energy_consumption_kwh_per_km'), # Renamed
        ('electric_vehicle_battery_warranty', 'ev', 'battery_warranty_years'), # Renamed
        ('electric_residual_value_pct', 'ev', 'residual_value_percent'), # Renamed
        ('electric_maintenance_cost_per_km', 'ev', 'maintenance_cost_per_km'), # Nested required
        ('electric_insurance_cost_factor', 'ev', 'insurance_cost_percent'), # Renamed AND nested required
        ('annual_registration_cost', 'ev', 'registration_cost'), # Use top-level UI input for nested required field
        # Required EV fields potentially missing from UI/flat_params:
        ('electric_vehicle_battery_replacement_cost_per_kwh', 'ev', 'battery_replacement_cost_per_kwh'), # Assume key exists in flat_params from init
        ('electric_vehicle_battery_cycle_life', 'ev', 'battery_cycle_life'), # Assume key exists in flat_params from init
        ('electric_vehicle_battery_depth_of_discharge', 'ev', 'battery_depth_of_discharge'), # Assume key exists in flat_params from init
        ('electric_vehicle_charging_efficiency', 'ev', 'charging_efficiency'), # Assume key exists in flat_params from init

        # Diesel Vehicle Nested
        ('diesel_vehicle_name', 'diesel', 'name'),
        ('diesel_vehicle_price', 'diesel', 'purchase_price'), # Renamed
        ('diesel_vehicle_fuel_consumption', 'diesel', 'fuel_consumption_l_per_100km'), # Renamed
        ('diesel_residual_value_pct', 'diesel', 'residual_value_percent'), # Renamed
        ('diesel_maintenance_cost_per_km', 'diesel', 'maintenance_cost_per_km'), # Nested required
        ('diesel_insurance_cost_factor', 'diesel', 'insurance_cost_percent'), # Renamed AND nested required
        ('annual_registration_cost', 'diesel', 'registration_cost'), # Use top-level UI input for nested required field
        # Required Diesel fields potentially missing from UI/flat_params:
        ('diesel_vehicle_co2_emission_factor', 'diesel', 'co2_emission_factor') # Assume key exists in flat_params from init
    ]

    # 5. Populate nested dictionaries based on mapping
    for flat_key, target_dict_name, final_key in key_mapping:
        if flat_key in processed:
            value = processed[flat_key]
            if target_dict_name == 'scenario':
                nested_params[final_key] = value # Use final key directly for scenario for simplicity
            elif target_dict_name == 'ev':
                ev_params[final_key] = value
            elif target_dict_name == 'diesel':
                diesel_params[final_key] = value
        else:
            # Log if a mapped key expected from UI/init is missing in the processed dict
            logger.warning(f"Mapped key '{flat_key}' not found in processed parameters during restructuring.")

    # 6. Calculate analysis_years - REMOVED
    # if 'start_year' in nested_params and 'end_year' in processed: # Use end_year from processed dict
    #     try:
    #         start = int(nested_params['start_year'])
    #         end = int(processed['end_year'])
    #         if end >= start:
    #              nested_params['analysis_years'] = end - start + 1
    #              # Remove end_year if it accidentally got added to nested_params via mapping
    #              nested_params.pop('end_year', None)
    #         else:
    #              logger.error("End year cannot be before start year.")
    #              # Potentially raise error or set default analysis_years? Pydantic will catch missing required field.
    #     except (TypeError, ValueError):
    #         logger.error("Could not calculate analysis_years due to invalid start/end year.")
    #         # Pydantic validation will likely fail due to missing analysis_years
    # else:
    #     logger.warning("Could not calculate analysis_years: start_year or end_year missing from parameters.")


    # 7. Final renames/adjustments for top-level Scenario keys
    if 'discount_rate_real' in nested_params: # Check if key exists from mapping
        pass # Already mapped to correct name
    if 'force_battery_replacement_year' in nested_params: # Check if key exists from mapping
        pass # Already mapped to correct name

    # 8. Add the fully populated nested vehicle dictionaries
    nested_params['electric_vehicle'] = ev_params
    nested_params['diesel_vehicle'] = diesel_params
    
    logger.debug(f"Preprocessing finished. Returning nested params: {nested_params}")
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
