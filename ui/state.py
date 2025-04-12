"""
Handles Streamlit session state management for the TCO Model application.

This module initializes and manages the application state, ensuring consistent
data is available across the UI components.
"""

import streamlit as st
import os
import datetime
import logging
from typing import Dict, Any, Optional

from tco_model.scenarios import Scenario
from utils.data_mapper import flatten_scenario_dict
# Import the core config manager
from config.config_manager import ConfigurationManager as CoreConfigManager

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Manages scenario loading (from specific files) and state transformation for the UI.
    
    This class centralizes scenario file loading and UI state preparation.
    """
    
    @classmethod
    def load_scenario(cls, filepath: str) -> Optional[Scenario]:
        """
        Load a scenario from the given file path.

        Args:
            filepath: Path to the scenario file. Must be provided.

        Returns:
            Scenario object if loaded successfully, None otherwise
        """
        if not filepath:
            logger.error("load_scenario called without a filepath.")
            return None

        target_path = filepath
        
        try:
            if not os.path.exists(target_path):
                logger.error(f"Scenario file not found: {target_path}")
                return None
                
            # Use CoreConfigManager's method to load a specific scenario file
            # This assumes CoreConfigManager provides a way to load *just* a file
            # Let's instantiate CoreConfigManager to use its file loading logic
            # Note: This might be inefficient if CoreConfigManager re-loads defaults each time.
            # A better approach might be a static method on CoreConfigManager if available,
            # or refactoring the loading logic out. For now, we use get_scenario_config.
            # scenario_dict = core_config_manager.get_scenario_config(target_path) 
            # scenario = Scenario(**scenario_dict) # Create scenario from the potentially merged dict

            scenario = Scenario.from_file(target_path) # Revert to direct loading for specific files
            logger.info(f"Scenario loaded: {scenario.name} from {target_path}")
            return scenario
            
        except FileNotFoundError:
            logger.error(f"Scenario file not found at: {target_path}")
            return None
        except ValueError as e:
            logger.error(f"Error validating scenario file ({target_path}): {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading scenario file {target_path}: {e}", exc_info=True)
            return None
    
    @classmethod
    def scenario_to_session_state(cls, scenario: Scenario) -> Dict[str, Any]:
        """
        Convert a scenario to a session state dictionary.
        
        Args:
            scenario: The Scenario object to convert
            
        Returns:
            Dictionary suitable for storing in session state
        """
        # Convert scenario model to nested dict
        nested_scenario_dict = scenario.to_dict()
        
        # Flatten the nested dictionary for UI display
        flat_scenario_params = flatten_scenario_dict(nested_scenario_dict)
        
        return flat_scenario_params
    
    @classmethod
    def ensure_required_ui_fields(cls, params: Dict[str, Any]) -> None:
        """
        Ensure all required UI fields are present in the parameters dictionary.
        
        Args:
            params: Parameter dictionary to check and update
        """
        # Set start_year if missing
        if 'start_year' not in params:
            current_year = datetime.datetime.now().year
            params['start_year'] = current_year
            logger.info(f"Setting missing 'start_year' to current year: {current_year}")

    @classmethod
    def setup_battery_replacement_ui_state(cls, scenario: Scenario) -> None:
        """
        Set up the UI state for battery replacement options based on scenario settings.
        
        Args:
            scenario: The Scenario object with battery replacement settings
        """
        if scenario.enable_battery_replacement:
            if scenario.force_battery_replacement_year is not None:
                st.session_state['battery_replace_mode'] = "Fixed Year"
            elif scenario.battery_replacement_threshold is not None:
                st.session_state['battery_replace_mode'] = "Capacity Threshold"
            else:
                # Default UI mode if specific settings aren't present but replacement is enabled
                st.session_state['battery_replace_mode'] = "Fixed Year" 
        else:
            # Default UI mode if replacement is disabled
            st.session_state['battery_replace_mode'] = "Fixed Year"


def initialize_session_state() -> None:
    """
    Initialize the Streamlit session state with default parameters.
    
    Loads the base default configuration using CoreConfigManager, creates a 
    default Scenario object, converts it to a flat dictionary for the UI,
    and stores it in the session state. Also sets up UI-specific state values.
    """
    # Only initialize if the scenario parameters don't already exist
    if 'scenario_params' not in st.session_state:
        try:
            # Instantiate the core config manager to access base defaults
            core_config_manager = CoreConfigManager()
            
            # Get the base configuration dictionary loaded from YAML files
            # Assuming it's stored in an attribute like 'base_config'
            base_config_dict = core_config_manager.base_config
            
            if not base_config_dict:
                 logger.error("CoreConfigManager did not load base configuration.")
                 st.error("Failed to load default configuration. Check logs.")
                 st.stop()

            # Create the default Scenario object from the base config dictionary
            scenario = Scenario(**base_config_dict)
            logger.info("Default scenario created from base configuration.")

            # Convert scenario to flat dictionary for UI and store in session state
            # Use the local ConfigManager's utility methods for UI state prep
            flat_scenario_params = ConfigManager.scenario_to_session_state(scenario)
            
            # Apply any needed defaults for UI-specific fields
            ConfigManager.ensure_required_ui_fields(flat_scenario_params)
            
            # Store data in session state
            st.session_state['scenario_params'] = flat_scenario_params
            # Store the original nested structure for reference if needed
            st.session_state['original_nested_scenario'] = scenario.to_dict() 
            
            # Set up battery replacement UI state based on the default scenario
            ConfigManager.setup_battery_replacement_ui_state(scenario)
            
        except Exception as e:
            logger.error(f"Unexpected error during state initialization: {e}", exc_info=True)
            st.error(f"An unexpected error occurred during state initialization: {e}")
            st.stop()