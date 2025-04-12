# app.py
import streamlit as st
import copy
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
from utils.data_mapper import unflatten_to_scenario_dict  # Import the new mapper
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

        # 2. Convert to nested structure using our improved mapper
        processed_nested_params = unflatten_to_scenario_dict(current_flat_params)

        # 3. Validate and create the Scenario object with the nested structure
        scenario = Scenario(**processed_nested_params)
        st.sidebar.success(SCENARIO_SUCCESS_MSG)

    except ValidationError as e:
        st.sidebar.error(SCENARIO_CONFIG_ERROR_MSG)
        # Group validation errors by component for better readability
        error_details = e.errors()
        grouped_errors = {}
        
        # Group errors by parent object
        for error in error_details:
            path = error['loc']
            parent = path[0] if path else "general"
            if parent not in grouped_errors:
                grouped_errors[parent] = []
            grouped_errors[parent].append((path, error['msg']))
        
        # Display errors grouped by component
        for parent, errors in grouped_errors.items():
            st.sidebar.markdown(f"**{parent.title()} Issues:**")
            for path, msg in errors:
                field = " → ".join(map(str, path))
                st.sidebar.error(f"- {field}: {msg}")
        st.stop()
    except Exception as e:
        logger.error(f"Error creating scenario: {e}", exc_info=True)
        st.sidebar.error(f"An unexpected error occurred creating the scenario: {e}")
        st.stop()

    # --- Perform Calculation ---
    if scenario:
        # Invalidate any cached results in session state
        if 'cached_results' in st.session_state:
            del st.session_state['cached_results']
            logger.debug("Calculation cache invalidated")
            
        calculator = TCOCalculator()
        try:
            with st.spinner(CALCULATION_SPINNER_MSG):
                results = calculator.calculate(scenario)
        except Exception as e:
            logger.error(f"Calculation error: {e}", exc_info=True)
            st.error(f"{CALCULATION_ERROR_MSG} {e}")
            results = {"error": str(e)}
    
    # --- Display Results --- 
    display_results(results) 

if __name__ == "__main__":
    main()