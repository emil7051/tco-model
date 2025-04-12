"""
Preprocessing utilities for transforming UI parameters to model format.

DEPRECATED: This module is being replaced by utils.data_mapper. Please use that module instead.
This module now simply forwards to data_mapper for backward compatibility.
"""
# Standard library imports
import logging
import warnings
from typing import Any, Dict

# Application-specific imports
# Ensure data_mapper exists and the import is valid
try:
    from utils.data_mapper import unflatten_to_scenario_dict
except ImportError:
    # Provide a fallback or raise a more informative error if data_mapper is critical
    logger.error("Failed to import from utils.data_mapper. Preprocessing module is non-functional.")
    # Define a dummy function to avoid NameError if needed, though the module is deprecated
    def unflatten_to_scenario_dict(params: Dict[str, Any]) -> Dict[str, Any]:
        return params

logger = logging.getLogger(__name__)

# Type alias for flat parameters dictionary
FlatParams = Dict[str, Any]
# Type alias for the nested scenario dictionary (structure defined in data_mapper/Scenario)
NestedParams = Dict[str, Any]

def preprocess_ui_params(flat_params: FlatParams) -> NestedParams:
    """
    Convert sidebar params (flat dict, % as numbers) into the nested structure for the Scenario model.
    
    DEPRECATED: Please use utils.data_mapper.unflatten_to_scenario_dict instead.
    
    Args:
        flat_params: A dictionary of UI parameters with flat structure
        
    Returns:
        A nested parameter dictionary compatible with the Scenario model
    """
    warnings.warn(
        "preprocess_ui_params is deprecated and will be removed in a future version. "
        "Please use utils.data_mapper.unflatten_to_scenario_dict instead.",
        DeprecationWarning, 
        stacklevel=2
    )
    # Simply forward to the new implementation
    # The return type depends on the actual implementation in data_mapper
    return unflatten_to_scenario_dict(flat_params)

# The following functions are deprecated and only included for backward compatibility.
# They should not be used in new code.

def _convert_percentages_to_decimals(params: NestedParams) -> None:
    """
    DEPRECATED: Use utils.data_mapper._convert_percentages_to_decimals instead.
    
    Convert percentage values from UI (0-100) to decimal values (0-1) for the model.
    """
    warnings.warn(
        "_convert_percentages_to_decimals is deprecated. Use data_mapper implementation instead.", 
        DeprecationWarning, 
        stacklevel=2
    )
    # This function is now a no-op as the functionality has been moved
    logger.warning("Called deprecated _convert_percentages_to_decimals - no action taken")

def _process_battery_replacement_params(params: NestedParams) -> None:
    """
    DEPRECATED: Use utils.data_mapper._process_battery_replacement_params instead.
    
    Handle conditional battery replacement logic based on UI selection.
    """
    warnings.warn(
        "_process_battery_replacement_params is deprecated. Use data_mapper implementation instead.", 
        DeprecationWarning, 
        stacklevel=2
    )
    # This function is now a no-op as the functionality has been moved
    logger.warning("Called deprecated _process_battery_replacement_params - no action taken")

def _set_vehicle_types_and_lifespans(flat_params: FlatParams, nested_params: NestedParams) -> None:
    """
    DEPRECATED: Vehicle type handling has been moved to data_mapper.
    
    Extract vehicle types from session state and set lifespans.
    """
    warnings.warn(
        "_set_vehicle_types_and_lifespans is deprecated. Use data_mapper implementation instead.", 
        DeprecationWarning, 
        stacklevel=2
    )
    # This function is now a no-op as the functionality has been moved
    logger.warning("Called deprecated _set_vehicle_types_and_lifespans - no action taken")

def _map_parameters_to_nested_structure(flat_params: FlatParams, nested_params: NestedParams) -> None:
    """
    DEPRECATED: Use utils.data_mapper._map_parameters_to_nested_structure instead.
    
    Map parameters from flat structure to nested structure based on defined mapping.
    """
    warnings.warn(
        "_map_parameters_to_nested_structure is deprecated. Use data_mapper implementation instead.", 
        DeprecationWarning, 
        stacklevel=2
    )
    # This function is now a no-op as the functionality has been moved
    logger.warning("Called deprecated _map_parameters_to_nested_structure - no action taken")

def _ensure_registration_costs(flat_params: FlatParams, nested_params: NestedParams) -> None:
    """
    DEPRECATED: Use utils.data_mapper implementation instead.
    
    Ensure registration costs are properly set for both vehicle types.
    """
    warnings.warn(
        "_ensure_registration_costs is deprecated. Use data_mapper implementation instead.", 
        DeprecationWarning, 
        stacklevel=2
    )
    # This function is now a no-op as the functionality has been moved
    logger.warning("Called deprecated _ensure_registration_costs - no action taken")