"""
Data handling utilities for the TCO Model.

This module centralizes data loading operations with caching mechanisms and 
provides a consistent interface for accessing different data types.
"""
# Standard library imports
import json
import logging
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, Union

# Third-party imports
import pandas as pd
import streamlit as st
import yaml

# Application-specific imports
from config.constants import (
    DEFAULT_CONFIG_DIR, DEFAULTS_DIR, SCENARIOS_DIR
)

logger = logging.getLogger(__name__)

# Define file constants
VEHICLE_SPECS_FILE = "vehicle_specs.yaml"
ENERGY_PRICES_FILE = "energy_prices.yaml"
BATTERY_COSTS_FILE = "battery_costs.yaml"
INCENTIVES_FILE = "incentives.yaml"
SCENARIO_EXTENSION = ".yaml"

class DataLoadError(Exception):
    """Exception raised for errors in the data loading process."""
    pass

@st.cache_data(ttl=3600, show_spinner=False)
def load_yaml_data(file_name: str, data_dir: str = DEFAULTS_DIR) -> Dict:
    """
    Loads data from a YAML file with Streamlit caching.

    Args:
        file_name: The name of the YAML file (e.g., 'vehicle_specs.yaml')
        data_dir: The directory containing the data file, relative to the project root

    Returns:
        A dictionary containing the loaded data

    Raises:
        DataLoadError: If the file cannot be loaded or parsed
    """
    file_path = os.path.join(data_dir, file_name)
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
            logger.info(f"Successfully loaded data from {file_path}")
            return data
    except FileNotFoundError:
        error_msg = f"Data file not found at {file_path}"
        logger.error(f"Error: {error_msg}")
        raise DataLoadError(error_msg)
    except yaml.YAMLError as e:
        error_msg = f"Error parsing YAML file {file_path}: {e}"
        logger.error(error_msg)
        raise DataLoadError(error_msg)
    except Exception as e:
        error_msg = f"An unexpected error occurred while loading {file_path}: {e}"
        logger.error(error_msg)
        raise DataLoadError(error_msg)

@st.cache_data(ttl=3600, show_spinner=False)
def load_json_data(file_name: str, data_dir: str = DEFAULTS_DIR) -> Dict:
    """
    Loads data from a JSON file with Streamlit caching.

    Args:
        file_name: The name of the JSON file
        data_dir: The directory containing the data file, relative to the project root

    Returns:
        A dictionary containing the loaded data

    Raises:
        DataLoadError: If the file cannot be loaded or parsed
    """
    file_path = os.path.join(data_dir, file_name)
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            logger.info(f"Successfully loaded data from {file_path}")
            return data
    except FileNotFoundError:
        error_msg = f"Data file not found at {file_path}"
        logger.error(f"Error: {error_msg}")
        raise DataLoadError(error_msg)
    except json.JSONDecodeError as e:
        error_msg = f"Error parsing JSON file {file_path}: {e}"
        logger.error(error_msg)
        raise DataLoadError(error_msg)
    except Exception as e:
        error_msg = f"An unexpected error occurred while loading {file_path}: {e}"
        logger.error(error_msg)
        raise DataLoadError(error_msg)

@st.cache_data(ttl=3600, show_spinner=False)
def load_csv_data(file_name: str, data_dir: str = DEFAULTS_DIR, **kwargs) -> pd.DataFrame:
    """
    Loads data from a CSV file with Streamlit caching.

    Args:
        file_name: The name of the CSV file
        data_dir: The directory containing the data file, relative to the project root
        **kwargs: Additional arguments to pass to pandas.read_csv

    Returns:
        A pandas DataFrame containing the loaded data

    Raises:
        DataLoadError: If the file cannot be loaded or parsed
    """
    file_path = os.path.join(data_dir, file_name)
    try:
        data = pd.read_csv(file_path, **kwargs)
        logger.info(f"Successfully loaded data from {file_path}")
        return data
    except FileNotFoundError:
        error_msg = f"Data file not found at {file_path}"
        logger.error(f"Error: {error_msg}")
        raise DataLoadError(error_msg)
    except pd.errors.EmptyDataError:
        error_msg = f"The CSV file {file_path} is empty"
        logger.error(error_msg)
        raise DataLoadError(error_msg)
    except pd.errors.ParserError as e:
        error_msg = f"Error parsing CSV file {file_path}: {e}"
        logger.error(error_msg)
        raise DataLoadError(error_msg)
    except Exception as e:
        error_msg = f"An unexpected error occurred while loading {file_path}: {e}"
        logger.error(error_msg)
        raise DataLoadError(error_msg)

# Specific data loaders with caching and validation

@st.cache_data(ttl=3600, show_spinner=False)
def load_vehicle_specs(data_dir: str = DEFAULTS_DIR) -> Dict:
    """
    Loads vehicle specifications with validation.

    Args:
        data_dir: The directory containing the data file

    Returns:
        A dictionary containing vehicle specifications
    """
    data = load_yaml_data(VEHICLE_SPECS_FILE, data_dir)
    
    # Basic validation
    if not data or not isinstance(data, dict):
        raise DataLoadError(f"Invalid vehicle specs data structure in {VEHICLE_SPECS_FILE}")
    
    required_keys = ['ev_models', 'diesel_models']
    for key in required_keys:
        if key not in data:
            raise DataLoadError(f"Missing required key '{key}' in {VEHICLE_SPECS_FILE}")
    
    logger.info(f"Loaded {len(data.get('ev_models', []))} EV models and "
                f"{len(data.get('diesel_models', []))} diesel models")
    return data

@st.cache_data(ttl=3600, show_spinner=False)
def load_energy_prices(data_dir: str = DEFAULTS_DIR) -> Dict:
    """
    Loads energy price projections with validation.

    Args:
        data_dir: The directory containing the data file

    Returns:
        A dictionary containing energy price projections
    """
    data = load_yaml_data(ENERGY_PRICES_FILE, data_dir)
    
    # Basic validation
    if not data or not isinstance(data, dict):
        raise DataLoadError(f"Invalid energy prices data structure in {ENERGY_PRICES_FILE}")
    
    required_keys = ['electricity', 'diesel']
    for key in required_keys:
        if key not in data:
            raise DataLoadError(f"Missing required key '{key}' in {ENERGY_PRICES_FILE}")
    
    logger.info(f"Loaded energy price projections with "
                f"{len(data.get('electricity', {}).keys())} electricity scenarios and "
                f"{len(data.get('diesel', {}).keys())} diesel scenarios")
    return data

@st.cache_data(ttl=3600, show_spinner=False)
def load_battery_costs(data_dir: str = DEFAULTS_DIR) -> Dict:
    """
    Loads battery cost projections with validation.

    Args:
        data_dir: The directory containing the data file

    Returns:
        A dictionary containing battery cost projections
    """
    data = load_yaml_data(BATTERY_COSTS_FILE, data_dir)
    
    # Basic validation
    if not data or not isinstance(data, dict):
        raise DataLoadError(f"Invalid battery costs data structure in {BATTERY_COSTS_FILE}")
    
    # Ensure we have at least one scenario
    if len(data.keys()) == 0:
        raise DataLoadError(f"No battery cost scenarios found in {BATTERY_COSTS_FILE}")
    
    logger.info(f"Loaded {len(data.keys())} battery cost scenarios")
    return data

@st.cache_data(ttl=3600, show_spinner=False)
def load_incentives(data_dir: str = DEFAULTS_DIR) -> Dict:
    """
    Loads incentive data with validation.

    Args:
        data_dir: The directory containing the data file

    Returns:
        A dictionary containing incentive data
    """
    try:
        data = load_yaml_data(INCENTIVES_FILE, data_dir)
        logger.info(f"Loaded incentive data with {len(data.keys()) if data else 0} incentive types")
        return data
    except DataLoadError:
        # If incentives file isn't found or is invalid, return an empty dict
        logger.warning(f"No valid incentives data found in {data_dir}/{INCENTIVES_FILE}. Using empty defaults.")
        return {}

@st.cache_data(ttl=3600, show_spinner=False)
def list_available_scenarios() -> List[Tuple[str, str]]:
    """
    Lists all available scenario files in the scenarios directory.

    Returns:
        A list of tuples containing (scenario_id, scenario_name)
    """
    scenarios = []
    try:
        for filename in os.listdir(SCENARIOS_DIR):
            if filename.endswith(SCENARIO_EXTENSION):
                scenario_id = filename.replace(SCENARIO_EXTENSION, '')
                
                # Try to get the scenario name from the file
                try:
                    data = load_yaml_data(filename, SCENARIOS_DIR)
                    scenario_name = data.get('name', scenario_id)
                except:
                    scenario_name = scenario_id
                
                scenarios.append((scenario_id, scenario_name))
        
        logger.info(f"Found {len(scenarios)} scenario files")
        return scenarios
    except FileNotFoundError:
        logger.warning(f"Scenarios directory {SCENARIOS_DIR} not found")
        return []
    except Exception as e:
        logger.error(f"Error listing scenarios: {e}")
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def load_scenario(scenario_id: str) -> Dict:
    """
    Loads a specific scenario configuration by ID.

    Args:
        scenario_id: The ID of the scenario to load (filename without extension)

    Returns:
        A dictionary containing the scenario configuration

    Raises:
        DataLoadError: If the scenario cannot be loaded
    """
    filename = f"{scenario_id}{SCENARIO_EXTENSION}"
    try:
        data = load_yaml_data(filename, SCENARIOS_DIR)
        logger.info(f"Loaded scenario '{scenario_id}' ({data.get('name', 'unnamed')})")
        return data
    except DataLoadError as e:
        logger.error(f"Error loading scenario {scenario_id}: {e}")
        raise DataLoadError(f"Unable to load scenario '{scenario_id}': {e}")

def save_scenario(scenario_id: str, scenario_data: Dict) -> bool:
    """
    Saves a scenario configuration to disk.

    Args:
        scenario_id: The ID to use for the scenario (will be the filename without extension)
        scenario_data: The scenario data to save

    Returns:
        True if saving was successful, False otherwise
    """
    if not os.path.exists(SCENARIOS_DIR):
        try:
            os.makedirs(SCENARIOS_DIR)
        except Exception as e:
            logger.error(f"Error creating scenarios directory: {e}")
            return False
    
    filename = f"{scenario_id}{SCENARIO_EXTENSION}"
    file_path = os.path.join(SCENARIOS_DIR, filename)
    
    try:
        with open(file_path, 'w') as f:
            yaml.dump(scenario_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Successfully saved scenario '{scenario_id}' to {file_path}")
        # Clear the cache for this scenario
        load_scenario.clear()
        list_available_scenarios.clear()
        return True
    except Exception as e:
        logger.error(f"Error saving scenario {scenario_id} to {file_path}: {e}")
        return False

def get_data_catalog() -> Dict[str, Dict]:
    """
    Returns a catalog of all available data sources with metadata.

    Returns:
        A dictionary mapping data types to metadata about each source
    """
    try:
        catalog = {
            "vehicle_specs": {
                "source": f"{DEFAULTS_DIR}/{VEHICLE_SPECS_FILE}",
                "description": "Vehicle specifications for electric and diesel vehicles",
                "last_modified": get_file_modification_time(os.path.join(DEFAULTS_DIR, VEHICLE_SPECS_FILE)),
            },
            "energy_prices": {
                "source": f"{DEFAULTS_DIR}/{ENERGY_PRICES_FILE}",
                "description": "Energy price projections for electricity and diesel",
                "last_modified": get_file_modification_time(os.path.join(DEFAULTS_DIR, ENERGY_PRICES_FILE)),
            },
            "battery_costs": {
                "source": f"{DEFAULTS_DIR}/{BATTERY_COSTS_FILE}",
                "description": "Battery cost projections",
                "last_modified": get_file_modification_time(os.path.join(DEFAULTS_DIR, BATTERY_COSTS_FILE)),
            },
            "incentives": {
                "source": f"{DEFAULTS_DIR}/{INCENTIVES_FILE}",
                "description": "Available incentives and policies",
                "last_modified": get_file_modification_time(os.path.join(DEFAULTS_DIR, INCENTIVES_FILE)),
            },
            "scenarios": {
                "source": SCENARIOS_DIR,
                "description": "User-defined scenario configurations",
                "count": len(list_available_scenarios())
            }
        }
        return catalog
    except Exception as e:
        logger.error(f"Error generating data catalog: {e}")
        return {}

def get_file_modification_time(file_path: str) -> Optional[str]:
    """
    Gets the last modification time of a file as a formatted string.

    Args:
        file_path: Path to the file

    Returns:
        Formatted date-time string or None if file doesn't exist
    """
    try:
        if os.path.exists(file_path):
            mod_time = os.path.getmtime(file_path)
            return pd.to_datetime(mod_time, unit='s').strftime('%Y-%m-%d %H:%M:%S')
        return None
    except Exception:
        return None
