import streamlit as st
from tco_model.scenarios import Scenario
import os
from typing import Dict, Any
import datetime
import logging

logger = logging.getLogger(__name__)

# DEFAULT_SCENARIO_PATH = "config/scenarios/urban_delivery.yaml" # Old path
DEFAULT_SCENARIO_PATH = "config/scenarios/default_2025_projections.yaml" # New default path

def _flatten_scenario_dict(nested_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Flattens the nested scenario dictionary and prepares values for UI widgets."""
    flat_dict = {}
    
    # Define keys that represent percentages and need scaling
    percent_keys_in_model = [
        'discount_rate_real', 'inflation_rate', 'interest_rate', 
        'down_payment_pct',
        # Residual value is now a dict, not a single pct
        # 'electric_residual_value_percent', 
        # 'diesel_residual_value_percent', 
        'battery_replacement_threshold',
        # Insurance is now in a dict, not a simple factor/percent
        # 'electric_insurance_cost_percent', 'diesel_insurance_cost_percent', 
        'charger_maintenance_percent' # Still needed if using simplified infra inputs
    ]
    
    # Define key renames from model to UI state
    key_renames_to_ui = {
        # Vehicle
        'purchase_price': 'price',
        'battery_capacity_kwh': 'battery_capacity',
        'energy_consumption_kwh_per_km': 'energy_consumption',
        'battery_warranty_years': 'battery_warranty',
        # Residual value is now a dict, not renamed here
        # 'residual_value_percent': 'residual_value_pct', 
        # Insurance is now a dict
        # 'insurance_cost_percent': 'insurance_cost_factor',
        'fuel_consumption_l_per_100km': 'fuel_consumption',
        # Scenario
        'discount_rate_real': 'discount_rate',
        'force_battery_replacement_year': 'battery_replacement_year',
        # Infrastructure - Flatten the selected values from the new structure
        'selected_charger_cost': 'charger_cost', # From infrastructure_costs dict
        'selected_installation_cost': 'charger_installation_cost', # From infrastructure_costs dict
        # 'charger_maintenance_percent' - no rename needed, directly used if flattening
        # 'charger_lifespan' - no rename needed, directly used if flattening
    }

    # Process nested vehicle dictionaries first
    if 'electric_vehicle' in nested_dict:
        for vk, vv in nested_dict['electric_vehicle'].items():
            # Skip complex dicts we don't flatten directly (like projections)
            if isinstance(vv, (dict, list)) and vk not in ['residual_value_projections', 'battery_pack_cost_projections_aud_per_kwh']: 
                 logger.warning(f"Skipping complex field {vk} in electric_vehicle during flattening.")
                 continue
            if vk == 'residual_value_projections' or vk == 'battery_pack_cost_projections_aud_per_kwh':
                flat_dict[f"electric_vehicle_{vk}"] = vv # Keep the dict structure for potential display/use
                continue # Don't apply rename or percentage scaling
                
            ui_key = key_renames_to_ui.get(vk, vk)
            flat_key = f"electric_vehicle_{ui_key}" if ui_key != 'name' else 'electric_vehicle_name'
            if vk in percent_keys_in_model and vv is not None:
                flat_dict[flat_key] = vv * 100.0
            else:
                flat_dict[flat_key] = vv
                
    if 'diesel_vehicle' in nested_dict:
        for vk, vv in nested_dict['diesel_vehicle'].items():
             # Skip complex dicts we don't flatten directly (like projections)
            if isinstance(vv, (dict, list)) and vk != 'residual_value_projections':
                 logger.warning(f"Skipping complex field {vk} in diesel_vehicle during flattening.")
                 continue
            if vk == 'residual_value_projections':
                flat_dict[f"diesel_vehicle_{vk}"] = vv # Keep the dict structure
                continue # Don't apply rename or percentage scaling
                
            ui_key = key_renames_to_ui.get(vk, vk)
            flat_key = f"diesel_vehicle_{ui_key}" if ui_key != 'name' else 'diesel_vehicle_name'
            if vk in percent_keys_in_model and vv is not None:
                flat_dict[flat_key] = vv * 100.0
            else:
                flat_dict[flat_key] = vv

    # Process top-level keys (excluding processed vehicle dictionaries)
    for key, value in nested_dict.items():
        if key not in ['electric_vehicle', 'diesel_vehicle']:
            # Skip complex dicts we don't flatten directly for UI inputs (handled by select boxes etc.)
            if isinstance(value, (dict, list)) and key not in ['infrastructure_costs', 'electricity_price_projections', 'diesel_price_scenarios', 'maintenance_costs_detailed', 'insurance_and_registration']:
                 logger.warning(f"Skipping complex field {key} during top-level flattening.")
                 continue
            # Keep full dicts for selection later in UI
            if key in ['electricity_price_projections', 'diesel_price_scenarios', 'maintenance_costs_detailed', 'insurance_and_registration']:
                flat_dict[key] = value # Store the full dictionary
                continue
                
            # Flatten selected infra values if they exist in the nested dict
            if key == 'infrastructure_costs':
                # Keep track of the original dictionary
                original_infra_dict = value 
                for ik, iv in value.items():
                    if ik in ['selected_charger_cost', 'selected_installation_cost', 'charger_maintenance_percent', 'charger_lifespan']:
                        ui_key = key_renames_to_ui.get(ik, ik)
                        if ik in percent_keys_in_model and iv is not None:
                            flat_dict[ui_key] = iv * 100.0
                        else:
                            flat_dict[ui_key] = iv
                # Store the original nested dictionary as well
                flat_dict[key] = original_infra_dict 
                continue # Finished processing infra dict

            # Standard flattening for other top-level keys
            ui_key = key_renames_to_ui.get(key, key)
            if key in percent_keys_in_model and value is not None:
                flat_dict[ui_key] = value * 100.0
            else:
                flat_dict[ui_key] = value
                
    # Ensure default analysis years is present if not loaded
    if 'analysis_years' not in flat_dict:
         flat_dict['analysis_years'] = 15 # Default if missing from file

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
            
            # Set start_year from the loaded scenario file if available
            if 'start_year' in flat_scenario_params:
                logger.info(f"Session state initialized with start_year: {flat_scenario_params['start_year']}")
            else:
                # Fallback to current year if not in file (should be present though)
                current_year = datetime.datetime.now().year
                flat_scenario_params['start_year'] = current_year
                logger.warning(f"'start_year' not found in scenario file, using current year: {current_year}")

            # Store the flattened parameters in session state
            st.session_state['scenario_params'] = flat_scenario_params
            
            # Store the original nested dictionary
            st.session_state['original_nested_scenario'] = nested_scenario_dict
            
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
