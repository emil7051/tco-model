# app.py
import streamlit as st
import copy  # To copy scenario params from session state
from pydantic import ValidationError
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Import implementations
from ui.state import initialize_session_state
from ui.inputs import create_input_sidebar
from ui.outputs import display_results 
from tco_model.model import TCOCalculator
from tco_model.scenarios import Scenario
from utils.preprocessing import preprocess_ui_params  # Import the new preprocessing module
from config.constants import (
    PAGE_TITLE, PAGE_ICON, PAGE_LAYOUT, SIDEBAR_STATE,
    APP_TITLE, APP_DESCRIPTION, SCENARIO_SUCCESS_MSG,
    SCENARIO_CONFIG_ERROR_MSG, CALCULATION_ERROR_MSG, CALCULATION_SPINNER_MSG
)

# --- Main Application Logic --- 
def main():
    # Setup page configuration
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout=PAGE_LAYOUT,
        initial_sidebar_state=SIDEBAR_STATE
    )
    
    st.title(APP_TITLE)
    st.markdown(APP_DESCRIPTION)

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

        # 2. Preprocess & restructure params using the new utility function
        processed_nested_params = preprocess_ui_params(current_flat_params)

        # 3. Validate and create the Scenario object using the updated nested structure
        scenario = Scenario(**processed_nested_params)
        st.sidebar.success(SCENARIO_SUCCESS_MSG)

    except ValidationError as e:
        st.sidebar.error(SCENARIO_CONFIG_ERROR_MSG)
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
            with st.spinner(CALCULATION_SPINNER_MSG):
                results = calculator.calculate(scenario)
        except Exception as e:
            st.error(f"{CALCULATION_ERROR_MSG} {e}")
            # Store error in results dict for display
            results = {"error": str(e)}
    
    # --- Display Results --- 
    display_results(results) 

if __name__ == "__main__":
    main()
