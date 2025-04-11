import yaml
import os
import logging

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR = "config/defaults"

# Define filenames as constants
VEHICLE_SPECS_FILE = "vehicle_specs.yaml"
ENERGY_PRICES_FILE = "energy_prices.yaml"
BATTERY_COSTS_FILE = "battery_costs.yaml"

def load_yaml_data(file_name: str, data_dir: str = DEFAULT_DATA_DIR) -> dict | None:
    """Loads data from a YAML file located in the specified data directory.

    Args:
        file_name: The name of the YAML file (e.g., 'vehicle_specs.yaml').
        data_dir: The directory containing the data file, relative to the project root.

    Returns:
        A dictionary containing the loaded data, or None if an error occurs.
    """
    file_path = os.path.join(data_dir, file_name)
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
            logger.info(f"Successfully loaded data from {file_path}")
            return data
    except FileNotFoundError:
        logger.error(f"Error: Data file not found at {file_path}")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading {file_path}: {e}")
        return None

def load_vehicle_specs(data_dir: str = DEFAULT_DATA_DIR) -> dict | None:
    """Loads vehicle specifications from 'vehicle_specs.yaml'."""
    return load_yaml_data(VEHICLE_SPECS_FILE, data_dir)

def load_energy_prices(data_dir: str = DEFAULT_DATA_DIR) -> dict | None:
    """Loads energy prices from 'energy_prices.yaml'."""
    return load_yaml_data(ENERGY_PRICES_FILE, data_dir)

def load_battery_costs(data_dir: str = DEFAULT_DATA_DIR) -> dict | None:
    """Loads battery cost projections from 'battery_costs.yaml'."""
    return load_yaml_data(BATTERY_COSTS_FILE, data_dir)
