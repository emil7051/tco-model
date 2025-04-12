"""
Central configuration management for the TCO Model application.

This module provides a centralized approach to managing application 
configuration, constants, and default values.
"""

import os
import yaml
import logging
import glob
from typing import Dict, Any, Optional
from copy import deepcopy

logger = logging.getLogger(__name__)

# Helper function for deep merging dictionaries
def _deep_merge(source: Dict[str, Any], destination: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge source dict into destination dict."""
    for key, value in source.items():
        if isinstance(value, dict):
            # Get node or create one
            node = destination.setdefault(key, {})
            _deep_merge(value, node)
        else:
            destination[key] = value
    return destination

class ConfigurationManager:
    """
    Manages application configuration by loading defaults and merging scenarios.

    Loads base configuration from YAML files in the defaults directory
    and allows merging specific scenario configurations on top.
    """
    
    # Directory paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CONFIG_DIR = os.path.join(BASE_DIR, "config")
    SCENARIOS_DIR = os.path.join(CONFIG_DIR, "scenarios")
    DEFAULTS_DIR = os.path.join(CONFIG_DIR, "defaults")
    
    # Default configuration paths
    DEFAULT_SCENARIO_PATH = os.path.join(SCENARIOS_DIR, "default_2025_projections.yaml")
    
    # Status Messages
    SCENARIO_SUCCESS_MSG = "Scenario parameters loaded successfully."
    SCENARIO_CONFIG_ERROR_MSG = "Scenario Configuration Error:"
    CALCULATION_ERROR_MSG = "Error during TCO calculation:"
    CALCULATION_SPINNER_MSG = "Calculating TCO... Please wait."
    
    # Default Values
    # CURRENT_YEAR = 2023
    # DEFAULT_CURRENCY = "AUD"
    
    # Economic Defaults
    # DEFAULT_DISCOUNT_RATE = 7.0  # %
    # DEFAULT_INFLATION_RATE = 2.5  # %
    # DEFAULT_INTEREST_RATE = 7.0  # %
    # DEFAULT_DOWN_PAYMENT_PCT = 20.0  # %
    # DEFAULT_CARBON_TAX_RATE = 30.0  # AUD/tonne CO2e
    # DEFAULT_ROAD_USER_CHARGE = 0.0  # AUD/km
    
    # Analysis Defaults
    # DEFAULT_ANALYSIS_YEARS = 15
    # MIN_ANALYSIS_YEARS = 1
    # MAX_ANALYSIS_YEARS = 30
    # DEFAULT_ANNUAL_MILEAGE = 40000.0  # km
    
    # Vehicle Defaults
    # DEFAULT_EV_NAME = "EV Default"
    # DEFAULT_EV_PRICE = 400000.0  # AUD
    # DEFAULT_EV_BATTERY_CAPACITY = 300.0  # kWh
    # DEFAULT_EV_ENERGY_CONSUMPTION = 0.7  # kWh/km
    # DEFAULT_EV_BATTERY_WARRANTY = 8  # years
    
    # DEFAULT_DIESEL_NAME = "Diesel Default"
    # DEFAULT_DIESEL_PRICE = 200000.0  # AUD
    # DEFAULT_DIESEL_FUEL_CONSUMPTION = 28.6  # L/100km
    
    # Registration and Insurance
    # DEFAULT_ANNUAL_REGISTRATION_COST = 5000.0  # AUD
    
    # Conversion factors (REMOVED - Use constants.py)
    # DIESEL_CO2_EMISSION_FACTOR = 2.68
    
    def __init__(self):
        """Initializes the ConfigurationManager by loading base defaults."""
        self.base_config: Dict[str, Any] = self._load_base_defaults()

    def _load_base_defaults(self) -> Dict[str, Any]:
        """Loads and merges all YAML files from the defaults directory."""
        base_config = {}
        default_files = glob.glob(os.path.join(self.DEFAULTS_DIR, "*.yaml"))

        if not default_files:
            logger.warning(f"No default configuration files found in {self.DEFAULTS_DIR}")
            return {}

        # Sort files to ensure consistent load order (optional, but good practice)
        default_files.sort()

        for file_path in default_files:
            logger.info(f"Loading default config file: {file_path}")
            config_data = self.load_config_file(file_path)
            if config_data:
                # Use deep merge to handle nested dictionaries
                base_config = _deep_merge(config_data, base_config)
            else:
                logger.warning(f"Failed to load or empty config file: {file_path}")

        logger.info(f"Loaded {len(default_files)} default config files.")
        return base_config

    def get_scenario_config(self, scenario_file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Loads a specific scenario YAML and merges it onto the base defaults.

        If no scenario_file_path is provided, returns a copy of the base defaults.

        Args:
            scenario_file_path: Path to the scenario YAML file.

        Returns:
            A dictionary containing the merged configuration.
        """
        # Start with a deep copy of the base configuration
        final_config = deepcopy(self.base_config)

        if scenario_file_path is None:
            logger.info("No scenario file provided, returning base default configuration.")
            return final_config # Return base defaults if no scenario specified

        if not os.path.isabs(scenario_file_path):
            scenario_file_path = os.path.join(self.SCENARIOS_DIR, scenario_file_path)

        logger.info(f"Loading scenario config file: {scenario_file_path}")
        scenario_data = self.load_config_file(scenario_file_path)

        if scenario_data:
            # Deep merge scenario data onto the base configuration
            final_config = _deep_merge(scenario_data, final_config)
            logger.info(f"Successfully merged scenario: {scenario_file_path}")
        else:
            logger.warning(f"Failed to load or empty scenario file: {scenario_file_path}. Using base defaults.")

        return final_config

    def load_config_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load a configuration file (YAML) and return its contents.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            Dictionary containing the configuration data or None if error
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"Configuration file not found: {file_path}")
                return None
                
            with open(file_path, 'r') as f:
                config_data = yaml.safe_load(f)
                
            if config_data is None:
                logger.warning(f"Configuration file is empty or invalid YAML: {file_path}")
                return {} # Return empty dict for empty files
                
            return config_data
            
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading configuration file {file_path}: {e}", exc_info=True)
            return None
    
    def save_config_file(self, file_path: str, config_data: Dict[str, Any]) -> bool:
        """
        Save configuration data to a YAML file.
        
        Args:
            file_path: Path to save the configuration file
            config_data: Configuration data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                
            with open(file_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
                
            logger.info(f"Configuration file saved successfully: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration file {file_path}: {e}", exc_info=True)
            return False
    
    def get_available_scenarios(self) -> Dict[str, str]:
        """
        Get a list of available scenario files.
        
        Returns:
            Dictionary mapping scenario names to file paths
        """
        scenarios = {}
        try:
            if not os.path.exists(self.SCENARIOS_DIR):
                logger.warning(f"Scenarios directory not found: {self.SCENARIOS_DIR}")
                return scenarios
                
            scenario_files = [f for f in os.listdir(self.SCENARIOS_DIR) if f.endswith('.yaml')]
            
            for file_name in scenario_files:
                file_path = os.path.join(self.SCENARIOS_DIR, file_name)
                try:
                    # Quick peek for name without loading full file if possible
                    # For simplicity here, we still load it fully
                    # A better approach might parse only the 'name' field if files are large
                    scenario_data = self.load_config_file(file_path)
                    if scenario_data and 'name' in scenario_data:
                        # Use name from YAML if available
                        name = scenario_data['name']
                        # Check for duplicate names
                        if name in scenarios:
                            logger.warning(f"Duplicate scenario name '{name}' found in {file_name} and {os.path.basename(scenarios[name])}. Using file name for the latter.")
                            # Fallback to filename if name already exists
                            name_from_file = os.path.splitext(file_name)[0]
                            scenarios[name_from_file] = file_path
                        else:
                            scenarios[name] = file_path
                    elif scenario_data is not None: # File loaded but no 'name' field or is empty
                        # Use the file name as a fallback if 'name' field is missing
                        name = os.path.splitext(file_name)[0]
                        if name in scenarios:
                            logger.warning(f"Duplicate scenario name '{name}' (from filename) found for {file_name} and {os.path.basename(scenarios[name])}. Skipping {file_name}.")
                        else:
                            scenarios[name] = file_path
                    # If scenario_data is None (load failed), it's already logged in load_config_file
                except Exception as e:
                    # This catch might be redundant if load_config_file handles its exceptions
                    logger.warning(f"Failed to process scenario file {file_path}: {e}")
            
            return scenarios
            
        except Exception as e:
            logger.error(f"Error getting available scenarios: {e}", exc_info=True)
            return scenarios 