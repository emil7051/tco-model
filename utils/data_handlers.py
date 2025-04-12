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
# Use TypeAlias for better readability in Python 3.10+
# from typing import TypeAlias
# For compatibility with older versions, stick to basic typing
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

# Type Aliases for clarity (consider using TypeAlias if Python 3.10+ is guaranteed)
YamlData = Dict[str, Any]
JsonData = Dict[str, Any]
ScenarioId = str
ScenarioName = str
FilePath = str
DirectoryPath = str

class DataLoadError(Exception):
    """Exception raised for errors in the data loading process."""
    pass

@st.cache_data(ttl=3600, show_spinner=False)
def load_yaml_data(file_name: str, data_dir: DirectoryPath = DEFAULTS_DIR) -> YamlData:
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
    file_path: FilePath = os.path.join(data_dir, file_name)
    try:
        with open(file_path, 'r') as f:
            data: YamlData = yaml.safe_load(f)
            if data is None: # Handle empty YAML file case
                logger.warning(f"YAML file {file_path} is empty.")
                return {}
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
def load_json_data(file_name: str, data_dir: DirectoryPath = DEFAULTS_DIR) -> JsonData:
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
    file_path: FilePath = os.path.join(data_dir, file_name)
    try:
        with open(file_path, 'r') as f:
            data: JsonData = json.load(f)
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
def load_csv_data(file_name: str, data_dir: DirectoryPath = DEFAULTS_DIR, **kwargs: Any) -> pd.DataFrame:
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
    file_path: FilePath = os.path.join(data_dir, file_name)
    try:
        data: pd.DataFrame = pd.read_csv(file_path, **kwargs)
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
# Defining more specific types for loaded data where known
VehicleSpecsData = Dict[str, List[Dict[str, Any]]] # Assuming structure like {'ev_models': [...], 'diesel_models': [...]} 
EnergyPricesData = Dict[str, Dict[str, Any]] # e.g., {'electricity': {...}, 'diesel': {...}}
BatteryCostsData = Dict[str, Any] # Structure might vary per scenario
IncentivesData = Dict[str, Any] # Structure might vary
ScenarioData = Dict[str, Any]

@st.cache_data(ttl=3600, show_spinner=False)
def load_vehicle_specs(data_dir: DirectoryPath = DEFAULTS_DIR) -> VehicleSpecsData:
    """
    Loads vehicle specifications with validation.

    Args:
        data_dir: The directory containing the data file

    Returns:
        A dictionary containing vehicle specifications
    """
    data: YamlData = load_yaml_data(VEHICLE_SPECS_FILE, data_dir)

    # Basic validation
    if not data or not isinstance(data, dict):
        raise DataLoadError(f"Invalid vehicle specs data structure in {VEHICLE_SPECS_FILE}")

    required_keys = ['ev_models', 'diesel_models']
    for key in required_keys:
        if key not in data:
            raise DataLoadError(f"Missing required key '{key}' in {VEHICLE_SPECS_FILE}")
        if not isinstance(data[key], list):
             raise DataLoadError(f"Key '{key}' in {VEHICLE_SPECS_FILE} should be a list")

    logger.info(f"Loaded {len(data.get('ev_models', []))} EV models and "
                f"{len(data.get('diesel_models', []))} diesel models")
    # Perform casting here if needed, or rely on Pydantic models later
    return data # Type checking might complain here, requires more specific parsing or Pydantic

@st.cache_data(ttl=3600, show_spinner=False)
def load_energy_prices(data_dir: DirectoryPath = DEFAULTS_DIR) -> EnergyPricesData:
    """
    Loads energy price projections with validation.

    Args:
        data_dir: The directory containing the data file

    Returns:
        A dictionary containing energy price projections
    """
    data: YamlData = load_yaml_data(ENERGY_PRICES_FILE, data_dir)

    # Basic validation
    if not data or not isinstance(data, dict):
        raise DataLoadError(f"Invalid energy prices data structure in {ENERGY_PRICES_FILE}")

    required_keys = ['electricity', 'diesel']
    for key in required_keys:
        if key not in data:
            raise DataLoadError(f"Missing required key '{key}' in {ENERGY_PRICES_FILE}")
        if not isinstance(data[key], dict):
             raise DataLoadError(f"Key '{key}' in {ENERGY_PRICES_FILE} should be a dictionary")

    logger.info(f"Loaded energy price projections with "
                f"{len(data.get('electricity', {}).keys())} electricity scenarios and "
                f"{len(data.get('diesel', {}).keys())} diesel scenarios")
    return data # Type checking might complain here

@st.cache_data(ttl=3600, show_spinner=False)
def load_battery_costs(data_dir: DirectoryPath = DEFAULTS_DIR) -> BatteryCostsData:
    """
    Loads battery cost projections with validation.

    Args:
        data_dir: The directory containing the data file

    Returns:
        A dictionary containing battery cost projections
    """
    data: YamlData = load_yaml_data(BATTERY_COSTS_FILE, data_dir)

    # Basic validation
    if not data or not isinstance(data, dict):
        raise DataLoadError(f"Invalid battery costs data structure in {BATTERY_COSTS_FILE}")

    # Ensure we have at least one scenario
    if len(data.keys()) == 0:
        raise DataLoadError(f"No battery cost scenarios found in {BATTERY_COSTS_FILE}")

    logger.info(f"Loaded {len(data.keys())} battery cost scenarios")
    return data

@st.cache_data(ttl=3600, show_spinner=False)
def load_incentives(data_dir: DirectoryPath = DEFAULTS_DIR) -> IncentivesData:
    """
    Loads incentive data with validation.

    Args:
        data_dir: The directory containing the data file

    Returns:
        A dictionary containing incentive data
    """
    try:
        data: YamlData = load_yaml_data(INCENTIVES_FILE, data_dir)
        logger.info(f"Loaded incentive data with {len(data.keys()) if data else 0} incentive types")
        return data
    except DataLoadError:
        # If incentives file isn't found or is invalid, return an empty dict
        logger.warning(f"No valid incentives data found in {data_dir}/{INCENTIVES_FILE}. Using empty defaults.")
        return {}

@st.cache_data(ttl=3600, show_spinner=False)
def list_available_scenarios() -> List[Tuple[ScenarioId, ScenarioName]]:
    """
    Lists all available scenario files in the scenarios directory.

    Returns:
        A list of tuples containing (scenario_id, scenario_name)
    """
    scenarios: List[Tuple[ScenarioId, ScenarioName]] = []
    scenario_dir: DirectoryPath = SCENARIOS_DIR
    try:
        if not os.path.exists(scenario_dir):
            logger.warning(f"Scenarios directory {scenario_dir} not found")
            return []
            
        for filename in os.listdir(scenario_dir):
            if filename.endswith(SCENARIO_EXTENSION):
                scenario_id: ScenarioId = filename.replace(SCENARIO_EXTENSION, '')

                # Try to get the scenario name from the file
                try:
                    # Use load_yaml_data directly for consistency and error handling
                    data: YamlData = load_yaml_data(filename, scenario_dir)
                    scenario_name: ScenarioName = data.get('name', scenario_id) 
                except DataLoadError:
                    # If loading fails, use ID as name and log a warning
                    scenario_name = scenario_id
                    logger.warning(f"Could not load scenario name from {filename}. Using ID.")
                except Exception as e:
                     # Catch other potential errors during loading
                    scenario_name = scenario_id
                    logger.error(f"Unexpected error loading scenario name from {filename}: {e}")

                scenarios.append((scenario_id, scenario_name))

        logger.info(f"Found {len(scenarios)} scenario files in {scenario_dir}")
        return scenarios
    except FileNotFoundError: # Should be caught by os.path.exists now
        logger.warning(f"Scenarios directory {scenario_dir} not found")
        return []
    except Exception as e:
        logger.error(f"Error listing scenarios in {scenario_dir}: {e}")
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def load_scenario(scenario_id: ScenarioId) -> ScenarioData:
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
    scenario_dir: DirectoryPath = SCENARIOS_DIR
    try:
        data: YamlData = load_yaml_data(filename, scenario_dir)
        logger.info(f"Loaded scenario '{scenario_id}' ({data.get('name', 'unnamed')})")
        return data
    except DataLoadError as e:
        logger.error(f"Error loading scenario {scenario_id}: {e}")
        # Re-raise with a more specific message for the user/caller
        raise DataLoadError(f"Unable to load scenario '{scenario_id}'. Check file format and existence.")

def save_scenario(scenario_id: ScenarioId, scenario_data: ScenarioData) -> bool:
    """
    Saves a scenario configuration to disk.

    Args:
        scenario_id: The ID to use for the scenario (will be the filename without extension)
        scenario_data: The scenario data to save

    Returns:
        True if saving was successful, False otherwise
    """
    scenario_dir: DirectoryPath = SCENARIOS_DIR
    if not os.path.exists(scenario_dir):
        try:
            os.makedirs(scenario_dir)
            logger.info(f"Created scenarios directory: {scenario_dir}")
        except OSError as e: # Catch specific OS error
            logger.error(f"Error creating scenarios directory {scenario_dir}: {e}")
            return False
        except Exception as e: # Catch other potential errors
             logger.error(f"Unexpected error creating scenarios directory {scenario_dir}: {e}")
             return False

    filename = f"{scenario_id}{SCENARIO_EXTENSION}"
    file_path: FilePath = os.path.join(scenario_dir, filename)

    try:
        with open(file_path, 'w') as f:
            yaml.dump(scenario_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Successfully saved scenario '{scenario_id}' to {file_path}")
        # Clear the cache for this scenario and the list
        load_scenario.clear()
        list_available_scenarios.clear()
        return True
    except IOError as e: # Catch file I/O errors
        logger.error(f"Error writing scenario {scenario_id} to {file_path}: {e}")
        return False
    except Exception as e: # Catch other potential errors (e.g., YAML dump error)
        logger.error(f"Unexpected error saving scenario {scenario_id} to {file_path}: {e}")
        return False

DataCatalog = Dict[str, Dict[str, Any]]

def get_data_catalog() -> DataCatalog:
    """
    Returns a catalog of all available data sources with metadata.

    Returns:
        A dictionary mapping data types to metadata about each source
    """
    defaults_dir: DirectoryPath = DEFAULTS_DIR
    scenarios_dir: DirectoryPath = SCENARIOS_DIR
    vehicle_specs_path: FilePath = os.path.join(defaults_dir, VEHICLE_SPECS_FILE)
    energy_prices_path: FilePath = os.path.join(defaults_dir, ENERGY_PRICES_FILE)
    battery_costs_path: FilePath = os.path.join(defaults_dir, BATTERY_COSTS_FILE)
    incentives_path: FilePath = os.path.join(defaults_dir, INCENTIVES_FILE)

    try:
        catalog: DataCatalog = {
            "vehicle_specs": {
                "source": vehicle_specs_path,
                "description": "Vehicle specifications for electric and diesel vehicles",
                "last_modified": get_file_modification_time(vehicle_specs_path),
            },
            "energy_prices": {
                "source": energy_prices_path,
                "description": "Energy price projections for electricity and diesel",
                "last_modified": get_file_modification_time(energy_prices_path),
            },
            "battery_costs": {
                "source": battery_costs_path,
                "description": "Battery cost projections",
                "last_modified": get_file_modification_time(battery_costs_path),
            },
            "incentives": {
                "source": incentives_path,
                "description": "Available incentives and policies",
                "last_modified": get_file_modification_time(incentives_path),
            },
            "scenarios": {
                "source": scenarios_dir,
                "description": "User-defined scenario configurations",
                # Use a separate try-except for scenario listing in case it fails
                "count": 0 # Default count
            }
        }
        try:
             catalog["scenarios"]["count"] = len(list_available_scenarios())
        except Exception as e:
            logger.error(f"Could not count scenarios for catalog: {e}")

        return catalog
    except Exception as e:
        logger.error(f"Error generating data catalog: {e}")
        return {}

def get_file_modification_time(file_path: FilePath) -> Optional[str]:
    """
    Gets the last modification time of a file as a formatted string.

    Args:
        file_path: Path to the file

    Returns:
        Formatted date-time string or None if file doesn't exist or error occurs
    """
    try:
        if os.path.exists(file_path):
            mod_time_epoch = os.path.getmtime(file_path)
            # Use UTC for consistency
            mod_time_dt = pd.Timestamp(mod_time_epoch, unit='s', tz='UTC')
            return mod_time_dt.strftime('%Y-%m-%d %H:%M:%S %Z')
        else:
            logger.warning(f"File not found when checking modification time: {file_path}")
            return None
    except OSError as e:
        logger.error(f"OS error getting modification time for {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting modification time for {file_path}: {e}")
        return None
