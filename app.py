#!/usr/bin/env python3
# app.py
import streamlit as st
import copy
from pydantic import ValidationError
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Import implementations
from ui.state import initialize_session_state, ConfigManager
from ui.input_manager import create_input_sidebar
from ui.output_manager import create_output_dashboard
from tco_model.model import TCOCalculator
from tco_model.scenarios import Scenario
from utils.data_mapper import unflatten_to_scenario_dict
from config import constants # Import constants

def configure_page():
    """
    Configure Streamlit page settings and display basic app information.
    """
    # Setup page configuration
    st.set_page_config(
        page_title=constants.PAGE_TITLE,
        page_icon=constants.PAGE_ICON,
        layout=constants.PAGE_LAYOUT,
        initial_sidebar_state=constants.SIDEBAR_STATE
    )
    
    st.title(constants.APP_TITLE)
    st.markdown(constants.APP_DESCRIPTION)

def create_scenario_from_params():
    """
    Create a Scenario object from the current session state parameters.
    
    Returns:
        tuple: (scenario, error_message)
            - scenario: The created Scenario object or None if error
            - error_message: Error message if creation failed, None otherwise
    """
    try:
        # 1. Get a copy of the current flat params from session state
        current_flat_params = st.session_state['scenario_params'].copy()

        # 2. Convert to nested structure using our improved mapper
        processed_nested_params = unflatten_to_scenario_dict(current_flat_params)

        # 3. Validate and create the Scenario object with the nested structure
        scenario = Scenario(**processed_nested_params)
        st.sidebar.success(constants.SCENARIO_SUCCESS_MSG)
        return scenario, None

    except ValidationError as e:
        error_details = e.errors()
        grouped_errors = _group_validation_errors(error_details)
        return None, grouped_errors
    except Exception as e:
        logger.error(f"Error creating scenario: {e}", exc_info=True)
        return None, f"An unexpected error occurred creating the scenario: {e}"

def _group_validation_errors(error_details):
    """
    Group validation errors by component for better readability.
    
    Args:
        error_details: List of error dictionaries from ValidationError
        
    Returns:
        dict: Errors grouped by component
    """
    grouped_errors = {}
    
    # Group errors by parent object
    for error in error_details:
        path = error['loc']
        parent = path[0] if path else "general"
        if parent not in grouped_errors:
            grouped_errors[parent] = []
        grouped_errors[parent].append((path, error['msg']))
    
    return grouped_errors

def display_validation_errors(grouped_errors):
    """
    Display validation errors in the sidebar with improved formatting.
    
    Args:
        grouped_errors: Dictionary of errors grouped by component
    """
    st.sidebar.error(constants.SCENARIO_CONFIG_ERROR_MSG)
    st.sidebar.markdown("**Please correct the following issues:**")
    
    # Display errors grouped by component
    for parent, errors in grouped_errors.items():
        # Format parent component name (e.g., electric_vehicle -> Electric Vehicle)
        parent_title = parent.replace("_", " ").title()
        st.sidebar.markdown(f"**{parent_title}**")
        
        # Display individual errors for the component
        for path, msg in errors:
            # Format field path (e.g., ('electric_vehicle', 'battery_capacity') -> 'Battery Capacity')
            # We take the last part of the path for the specific field name
            field_name = path[-1] if path else "Unknown Field"
            formatted_field = field_name.replace("_", " ").title()
            
            # Construct and display the error message
            st.sidebar.error(f"*   _{formatted_field}_: {msg}")

def perform_calculation(scenario):
    """
    Perform TCO calculation based on the provided scenario.
    
    Args:
        scenario: Validated Scenario object
        
    Returns:
        dict: Calculation results or error
    """
    # Invalidate any cached results in session state
    if 'cached_results' in st.session_state:
        del st.session_state['cached_results']
        logger.debug("Calculation cache invalidated")
        
    calculator = TCOCalculator()
    try:
        with st.spinner(constants.CALCULATION_SPINNER_MSG):
            results = calculator.calculate(scenario)
        return results
    except Exception as e:
        logger.error(f"Calculation error: {e}", exc_info=True)
        st.error(f"{constants.CALCULATION_ERROR_MSG} {e}")
        return {"error": str(e)}
    
def main():
    """
    Main application logic orchestrating the TCO calculation workflow.
    """
    # Setup the page
    configure_page()

    # Initialize session state (loads default scenario if needed)
    initialize_session_state()
    
    # Create input sidebar - this directly modifies st.session_state['scenario_params']
    create_input_sidebar()
    
    # --- Create Scenario from current state ---
    scenario, error = create_scenario_from_params()
    
    if error:
        if isinstance(error, dict):
            display_validation_errors(error)
        else:
            st.sidebar.error(error)
        st.stop()
        
    # --- Perform Calculation if scenario is valid ---
    results = None
    if scenario:
        results = perform_calculation(scenario)
    
    # --- Display Results --- 
    create_output_dashboard(results) 

if __name__ == "__main__":
    main()