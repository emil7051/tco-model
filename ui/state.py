import streamlit as st
from tco_model.scenarios import Scenario
import os
from typing import Dict, Any
import datetime
import logging

logger = logging.getLogger(__name__)

DEFAULT_SCENARIO_PATH = "config/scenarios/urban_delivery.yaml"

def _flatten_scenario_dict(nested_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Flattens the nested scenario dictionary and prepares values for UI widgets."""
    flat_dict = {}
    
    # Define keys that represent percentages and need scaling
    percent_keys_in_model = [
        'discount_rate_real', 'inflation_rate', 'interest_rate', 
        'down_payment_pct', 'electric_residual_value_percent', 
        'diesel_residual_value_percent', 'battery_replacement_threshold',
        'electric_insurance_cost_percent', 'diesel_insurance_cost_percent', # Added insurance
        'charger_maintenance_percent' # Ensure this is included if needed
    ]
    
    # Define key renames from model to UI state
    key_renames_to_ui = {
        'purchase_price': 'price',
        'battery_capacity_kwh': 'battery_capacity',
        'energy_consumption_kwh_per_km': 'energy_consumption',
        'battery_warranty_years': 'battery_warranty',
        'residual_value_percent': 'residual_value_pct', 
        'insurance_cost_percent': 'insurance_cost_factor', # Map to UI's factor name
        'fuel_consumption_l_per_100km': 'fuel_consumption',
        'discount_rate_real': 'discount_rate', # Top level rename
        'force_battery_replacement_year': 'battery_replacement_year' # Rename for UI
    }

    # Process nested dictionaries first
    if 'electric_vehicle' in nested_dict:
        for vk, vv in nested_dict['electric_vehicle'].items():
            ui_key = key_renames_to_ui.get(vk, vk)
            flat_key = f"electric_vehicle_{ui_key}" if ui_key != 'name' else 'electric_vehicle_name'
            if vk in percent_keys_in_model and vv is not None:
                flat_dict[flat_key] = vv * 100.0
            else:
                flat_dict[flat_key] = vv
                
    if 'diesel_vehicle' in nested_dict:
        for vk, vv in nested_dict['diesel_vehicle'].items():
            ui_key = key_renames_to_ui.get(vk, vk)
            flat_key = f"diesel_vehicle_{ui_key}" if ui_key != 'name' else 'diesel_vehicle_name'
            if vk in percent_keys_in_model and vv is not None:
                flat_dict[flat_key] = vv * 100.0
            else:
                flat_dict[flat_key] = vv

    # Process top-level keys (excluding vehicle dictionaries)
    for key, value in nested_dict.items():
        if key not in ['electric_vehicle', 'diesel_vehicle']:
            ui_key = key_renames_to_ui.get(key, key)
            if key in percent_keys_in_model and value is not None:
                flat_dict[ui_key] = value * 100.0
            else:
                flat_dict[ui_key] = value

    return flat_dict

def initialize_session_state():
    """Initializes the Streamlit session state with default scenario parameters (flattened)."""
    if 'scenario_params' not in st.session_state:
        try:
            # Load the default scenario
            if not os.path.exists(DEFAULT_SCENARIO_PATH):
                st.error(f"Default scenario file not found: {DEFAULT_SCENARIO_PATH}")
                st.stop()
                
            scenario = Scenario.from_file(DEFAULT_SCENARIO_PATH)
            
            # Convert scenario model to nested dict
            nested_scenario_dict = scenario.to_dict()
            
            # Flatten the dictionary and prepare for UI
            flat_scenario_params = _flatten_scenario_dict(nested_scenario_dict)
            
            # Set start_year to the current year
            current_year = datetime.datetime.now().year
            flat_scenario_params['start_year'] = current_year
            logger.info(f"Session state initialized with start_year: {current_year}")
            
            # Set default analysis years to 15
            flat_scenario_params['analysis_years'] = 15
            logger.info(f"Default analysis_years set to 15 in session state.")

            # Store the flattened parameters in session state
            st.session_state['scenario_params'] = flat_scenario_params
            
            # Store the original scenario object for potential later use (e.g. reset)
            # st.session_state['default_scenario_object'] = scenario 
            
            # Store the radio button state based on the original scenario object
            if scenario.enable_battery_replacement:
                 if scenario.force_battery_replacement_year is not None:
                     st.session_state['battery_replace_mode'] = "Fixed Year"
                 elif scenario.battery_replacement_threshold is not None:
                     st.session_state['battery_replace_mode'] = "Capacity Threshold"
                 else:
                     # Default if enabled but neither is set (should be handled by validation ideally)
                     st.session_state['battery_replace_mode'] = "Fixed Year" 
            else:
                 st.session_state['battery_replace_mode'] = "Fixed Year" # Default selection if disabled

        except FileNotFoundError:
            st.error(f"Default scenario file not found at: {DEFAULT_SCENARIO_PATH}")
            st.stop()
        except ValueError as e:
            st.error(f"Error loading or validating default scenario file ({DEFAULT_SCENARIO_PATH}): {e}")
            st.stop()
        except Exception as e:
            st.error(f"An unexpected error occurred during state initialization: {e}")
            st.stop()
