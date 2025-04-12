import streamlit as st
from tco_model.scenarios import Scenario
import os
import datetime
import logging
from typing import Dict, Any

# Import the new data mapper functions
from utils.data_mapper import flatten_scenario_dict

logger = logging.getLogger(__name__)

DEFAULT_SCENARIO_PATH = "config/scenarios/default_2025_projections.yaml"

def initialize_session_state():
    """
    Initializes the Streamlit session state with default scenario parameters (flattened).
    
    Uses the improved data mapper to create a consistent UI state from the model.
    """
    if 'scenario_params' not in st.session_state:
        try:
            # Load the default scenario
            if not os.path.exists(DEFAULT_SCENARIO_PATH):
                st.error(f"Default scenario file not found: {DEFAULT_SCENARIO_PATH}")
                st.stop()
                
            scenario = Scenario.from_file(DEFAULT_SCENARIO_PATH)
            
            # Convert scenario model to nested dict
            nested_scenario_dict = scenario.to_dict()
            
            # Use the improved flatten function from data_mapper
            flat_scenario_params = flatten_scenario_dict(nested_scenario_dict)
            
            # Set start_year from the loaded scenario file if available
            if 'start_year' not in flat_scenario_params:
                current_year = datetime.datetime.now().year
                flat_scenario_params['start_year'] = current_year
                logger.warning(f"'start_year' not found in scenario file, using current year: {current_year}")

            # Store the flattened parameters in session state
            st.session_state['scenario_params'] = flat_scenario_params
            
            # Store the original nested dictionary
            st.session_state['original_nested_scenario'] = nested_scenario_dict
            
            # Set up battery replacement radio button state
            if scenario.enable_battery_replacement:
                if scenario.force_battery_replacement_year is not None:
                    st.session_state['battery_replace_mode'] = "Fixed Year"
                elif scenario.battery_replacement_threshold is not None:
                    st.session_state['battery_replace_mode'] = "Capacity Threshold"
                else:
                    st.session_state['battery_replace_mode'] = "Fixed Year" 
            else:
                st.session_state['battery_replace_mode'] = "Fixed Year"

        except FileNotFoundError:
            st.error(f"Default scenario file not found at: {DEFAULT_SCENARIO_PATH}")
            st.stop()
        except ValueError as e:
            st.error(f"Error loading or validating default scenario file ({DEFAULT_SCENARIO_PATH}): {e}")
            st.stop()
        except Exception as e:
            st.error(f"An unexpected error occurred during state initialization: {e}")
            st.stop()