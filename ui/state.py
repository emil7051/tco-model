"""
Handles Streamlit session state management for the TCO Model application.

This module initializes and manages the application state, ensuring consistent
data is available across the UI components.
"""

import streamlit as st
import os
import datetime
import logging
from typing import Dict, Any, Optional, NewType

from tco_model.scenarios import Scenario
# Removed import: from utils.data_mapper import flatten_scenario_dict, unflatten_to_scenario_dict
from config.config_manager import ConfigurationManager as CoreConfigManager
from pydantic import ValidationError # Import ValidationError

logger = logging.getLogger(__name__)

# Type Alias
FilePath = NewType('FilePath', str)
BaseConfigDict = Dict[str, Any]

class ConfigManager:
    """
    Manages scenario loading and state transformation for the UI.
    This class centralizes scenario file loading and UI state preparation.
    """

    @classmethod
    def load_scenario(cls, filepath: FilePath) -> Optional[Scenario]:
        """
        Load a scenario from the given file path using Scenario.from_file.

        Args:
            filepath: Path to the scenario file.

        Returns:
            Scenario object if loaded successfully, None otherwise.
        """
        if not filepath:
            logger.error("load_scenario called without a filepath.")
            return None

        try:
            # Scenario.from_file handles existence checks and validation
            scenario: Scenario = Scenario.from_file(filepath)
            logger.info(f"Scenario loaded: {scenario.name} from {filepath}")
            return scenario
        except FileNotFoundError:
            logger.error(f"Scenario file not found at: {filepath}")
            st.error(f"Error: Scenario file not found at {filepath}")
            return None
        except ValidationError as e: # Catch ValidationError specifically
            logger.error(f"Error validating scenario file ({filepath}): {e}")
            st.error(f"Error loading or validating scenario file {filepath}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading scenario file {filepath}: {e}", exc_info=True)
            st.error(f"An unexpected error occurred while loading {filepath}. Check logs.")
            return None

    @classmethod
    def setup_battery_replacement_ui_state(cls, scenario: Scenario) -> None:
        """
        Set up the UI state for battery replacement options based on scenario config.
        This method now directly updates st.session_state based on the passed scenario.

        Args:
            scenario: The Scenario object with nested battery replacement config.
        """
        # Access config through the nested model
        # Assuming scenario.battery_replacement_config is guaranteed by Scenario model
        config = scenario.battery_replacement_config
        if config.enable_battery_replacement:
            if config.force_replacement_year_index is not None:
                # Set UI mode based on which model config is set
                st.session_state['battery_replace_mode'] = "Fixed Year"
            elif config.replacement_threshold_fraction is not None:
                st.session_state['battery_replace_mode'] = "Capacity Threshold"
            else:
                # Default UI mode if specific settings aren't present but replacement is enabled
                st.session_state['battery_replace_mode'] = "Fixed Year"
                logger.warning("Battery replacement enabled but neither year nor threshold set. Defaulting UI mode to 'Fixed Year'.")
        else:
            # Default UI mode if replacement is disabled
            st.session_state['battery_replace_mode'] = "Fixed Year"

def initialize_session_state() -> None:
    """
    Initialize the Streamlit session state with the default Scenario object.

    Loads the base default configuration using CoreConfigManager, creates a
    default Scenario object, and stores it directly in st.session_state['scenario'].
    Sets up UI-specific state like battery replacement mode.
    """
    # Use 'scenario' as the key for the main object
    if 'scenario' not in st.session_state:
        try:
            core_config_manager = CoreConfigManager()
            # Assume get_base_config() returns the fully resolved *nested* dict
            # suitable for Scenario(**base_config_dict)
            base_config_dict: Optional[BaseConfigDict] = core_config_manager.get_base_config()

            if not base_config_dict:
                 logger.error("CoreConfigManager did not provide base configuration.")
                 st.error("Failed to load default configuration. Check logs.")
                 st.stop()
                 return # Explicit return after stop

            # Create the default Scenario object from the base config dictionary
            # Pydantic will validate the structure based on the Scenario model definition
            scenario: Scenario = Scenario(**base_config_dict)
            logger.info("Default scenario created from base configuration.")

            # Store the Scenario object directly in session state
            st.session_state['scenario'] = scenario

            # Set up battery replacement UI state based on the default scenario
            # Pass the scenario object directly
            ConfigManager.setup_battery_replacement_ui_state(st.session_state['scenario'])

            # Initialize calculation results to None
            if 'calculation_results' not in st.session_state:
                st.session_state['calculation_results'] = None

        except ValidationError as val_err:
             logger.error(f"Validation error initializing Scenario from base config: {val_err}", exc_info=True)
             st.error(f"Error validating default configuration: {val_err}")
             st.stop()
        except Exception as e:
            logger.error(f"Unexpected error during state initialization: {e}", exc_info=True)
            st.error(f"An unexpected error occurred during state initialization: {e}")
            st.stop()

# Ensure other functions using 'scenario_params' are updated later
# or that the usage points to 'scenario' and accesses attributes.