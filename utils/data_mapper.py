"""
Data mapping utilities for transforming between UI state and model structures.

This module provides a clean, centralized way to transform data between:
1. UI flat dictionary format (with percentages as 0-100)
2. Model nested structure format (with percentages as 0-1)
"""

from typing import Dict, Any, List, Optional, Union
import logging
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

# ---- Constants ----

# Keys that represent percentages in the model
PERCENTAGE_KEYS = [
    'discount_rate_real', 'inflation_rate', 'interest_rate',
    'down_payment_pct', 'battery_replacement_threshold',
    'charger_maintenance_percent', 'maintenance_increase_rate',
    'insurance_increase_rate', 'registration_increase_rate',
    'carbon_tax_increase_rate', 'road_user_charge_increase_rate'
]

# Keys that must be present in the final model
REQUIRED_KEYS = [
    'name', 'analysis_years', 'start_year', 'annual_mileage',
    'discount_rate_real', 'electric_vehicle', 'diesel_vehicle'
]

# Keys that should be integers
INTEGER_KEYS = [
    'analysis_years', 'start_year', 'loan_term',
    'battery_replacement_year', 'charger_lifespan'
]

# Keys that should be floats
FLOAT_KEYS = [
    'annual_mileage', 'discount_rate', 'inflation_rate', 
    'interest_rate', 'down_payment_pct', 'battery_replacement_threshold',
    'charger_maintenance_percent', 'electric_vehicle_price',
    'diesel_vehicle_price', 'electric_vehicle_energy_consumption',
    'diesel_vehicle_fuel_consumption', 'electric_vehicle_battery_capacity'
]

# Mapping from model keys to UI display keys
MODEL_TO_UI_KEY_MAP = {
    # Vehicle-specific
    'purchase_price': 'price',
    'battery_capacity_kwh': 'battery_capacity',
    'energy_consumption_kwh_per_km': 'energy_consumption',
    'battery_warranty_years': 'battery_warranty',
    'fuel_consumption_l_per_100km': 'fuel_consumption',
    # Scenario keys
    'discount_rate_real': 'discount_rate',
    'force_battery_replacement_year': 'battery_replacement_year',
    # Infrastructure keys
    'selected_charger_cost': 'charger_cost',
    'selected_installation_cost': 'charger_installation_cost',
}

# Mapping from UI display keys back to model keys
UI_TO_MODEL_KEY_MAP = {v: k for k, v in MODEL_TO_UI_KEY_MAP.items()}

# ---- Utility Functions ----

def flatten_scenario_dict(nested_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a nested scenario dictionary to a flat UI-friendly format.
    
    Args:
        nested_dict: The nested dictionary from a Scenario model
        
    Returns:
        A flattened dictionary suitable for UI display
    """
    try:
        flat_dict = {}
        
        # Process electric vehicle data
        if 'electric_vehicle' in nested_dict:
            _flatten_vehicle_dict(nested_dict['electric_vehicle'], 'electric_vehicle', flat_dict)
        else:
            logger.warning("No 'electric_vehicle' key found in nested dictionary")
        
        # Process diesel vehicle data
        if 'diesel_vehicle' in nested_dict:
            _flatten_vehicle_dict(nested_dict['diesel_vehicle'], 'diesel_vehicle', flat_dict)
        else:
            logger.warning("No 'diesel_vehicle' key found in nested dictionary")
        
        # Process top-level keys
        for key, value in nested_dict.items():
            if key not in ['electric_vehicle', 'diesel_vehicle']:
                _process_top_level_key(key, value, flat_dict)
        
        # Ensure default values for essential fields
        if 'analysis_years' not in flat_dict:
            flat_dict['analysis_years'] = 15  # Default
            logger.info("Applied default analysis_years=15")
            
        # Ensure numeric types are correct
        _ensure_numeric_types(flat_dict)
        
        return flat_dict
    
    except Exception as e:
        logger.error(f"Error flattening scenario dict: {e}", exc_info=True)
        # Return at least an empty dict to prevent further errors
        return {}

def unflatten_to_scenario_dict(flat_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a flattened UI dictionary back to a nested dictionary for Scenario model.
    
    Args:
        flat_dict: The flat dictionary from UI state
        
    Returns:
        A nested dictionary suitable for creating a Scenario model
    """
    try:
        # Make a copy to avoid modifying the original
        working_dict = flat_dict.copy()
        
        # Apply intelligent defaults based on context
        _apply_intelligent_defaults(working_dict)
        
        # Ensure numeric types are correct
        _ensure_numeric_types(working_dict)
        
        nested_dict = {}
        nested_dict['electric_vehicle'] = {}
        nested_dict['diesel_vehicle'] = {}
        
        # Convert UI percentages back to decimals for model
        _convert_percentages_to_decimals(working_dict)
        
        # Handle battery replacement logic
        _process_battery_replacement_params(working_dict)
        
        # Map parameters to the proper nested structure
        _map_params_to_nested_structure(working_dict, nested_dict)
        
        # Check that all required keys are present
        _validate_required_keys(nested_dict)
        
        return nested_dict
    
    except Exception as e:
        logger.error(f"Error unflattening to scenario dict: {e}", exc_info=True)
        raise ValueError(f"Failed to create model structure: {e}")

# ---- Helper Functions ----

def _flatten_vehicle_dict(vehicle_dict: Dict[str, Any], prefix: str, 
                         target_dict: Dict[str, Any]) -> None:
    """
    Flatten a vehicle dictionary into the target flat dictionary.
    
    Args:
        vehicle_dict: Source vehicle dictionary
        prefix: Prefix to apply to keys (e.g., 'electric_vehicle')
        target_dict: Target flat dictionary for results
    """
    try:
        for key, value in vehicle_dict.items():
            # Handle complex nested structures
            if isinstance(value, (dict, list)) and key not in ['residual_value_projections', 'battery_pack_cost_projections_aud_per_kwh']:
                logger.debug(f"Preserving complex nested field: {key}")
                target_dict[f"{prefix}_{key}"] = value
                continue
                
            # Map the key name if needed
            ui_key = MODEL_TO_UI_KEY_MAP.get(key, key)
            flat_key = f"{prefix}_{ui_key}" if ui_key != 'name' else f"{prefix}_name"
            
            # Scale percentages for UI display
            if key in PERCENTAGE_KEYS and value is not None:
                target_dict[flat_key] = value * 100.0
            else:
                target_dict[flat_key] = value
    except Exception as e:
        logger.error(f"Error flattening {prefix} dict: {e}")

def _process_top_level_key(key: str, value: Any, target_dict: Dict[str, Any]) -> None:
    """
    Process a top-level key from the nested dictionary.
    
    Args:
        key: The key to process
        value: The value to process
        target_dict: Target flat dictionary for results
    """
    try:
        # Preserve complex nested structures that UI needs
        if isinstance(value, (dict, list)) and key in [
            'infrastructure_costs', 'electricity_price_projections',
            'diesel_price_scenarios', 'maintenance_costs_detailed',
            'insurance_and_registration'
        ]:
            target_dict[key] = value
            
            # Special handling for infrastructure nested values
            if key == 'infrastructure_costs':
                for infra_key, infra_value in value.items():
                    if infra_key in ['selected_charger_cost', 'selected_installation_cost', 
                                   'charger_maintenance_percent', 'charger_lifespan']:
                        ui_key = MODEL_TO_UI_KEY_MAP.get(infra_key, infra_key)
                        
                        # Scale percentages for UI
                        if infra_key in PERCENTAGE_KEYS and infra_value is not None:
                            target_dict[ui_key] = infra_value * 100.0
                        else:
                            target_dict[ui_key] = infra_value
            return
            
        # Standard top-level keys
        ui_key = MODEL_TO_UI_KEY_MAP.get(key, key)
        
        # Scale percentages for UI display
        if key in PERCENTAGE_KEYS and value is not None:
            target_dict[ui_key] = value * 100.0
        else:
            target_dict[ui_key] = value
    except Exception as e:
        logger.error(f"Error processing top-level key {key}: {e}")

def _convert_percentages_to_decimals(params: Dict[str, Any]) -> None:
    """
    Convert percentage values from UI (0-100) to decimal values (0-1) for the model.
    
    Args:
        params: Dictionary to process (modified in-place)
    """
    try:
        ui_percent_keys = [UI_TO_MODEL_KEY_MAP.get(k, k) for k in UI_TO_MODEL_KEY_MAP]
        ui_percent_keys.extend([
            'discount_rate', 'inflation_rate', 'interest_rate',
            'down_payment_pct', 'battery_replacement_threshold',
            'charger_maintenance_percent'
        ])
        
        for key in ui_percent_keys:
            if key in params and isinstance(params[key], (int, float)) and params[key] is not None:
                params[key] = params[key] / 100.0
        
        logger.debug(f"Converted percentage values to decimals")
    except Exception as e:
        logger.error(f"Error converting percentages to decimals: {e}")

def _process_battery_replacement_params(params: Dict[str, Any]) -> None:
    """
    Handle conditional battery replacement logic based on UI selection.
    
    Args:
        params: Dictionary to process (modified in-place)
    """
    try:
        if 'battery_replace_mode' in params:
            if params['battery_replace_mode'] == "Fixed Year":
                params['battery_replacement_threshold'] = None
                logger.debug("Battery mode set to 'Fixed Year', threshold set to None.")
            else:  # Capacity Threshold selected
                params['battery_replacement_year'] = None
                logger.debug("Battery mode set to 'Capacity Threshold', year set to None.")
        else:
            logger.warning("'battery_replace_mode' key not found in params during preprocessing.")
            if not params.get('enable_battery_replacement', False):
                params['battery_replacement_threshold'] = None
                params['battery_replacement_year'] = None
    except Exception as e:
        logger.error(f"Error processing battery replacement parameters: {e}")

def _ensure_numeric_types(params: Dict[str, Any]) -> None:
    """
    Ensure numeric fields have the correct types.
    
    Args:
        params: Dictionary to process (modified in-place)
    """
    try:
        # Process integer fields
        for key in INTEGER_KEYS:
            if key in params and params[key] is not None:
                try:
                    params[key] = int(params[key])
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert {key} to integer. Using existing value.")
                    
        # Process float fields
        for key in FLOAT_KEYS:
            if key in params and params[key] is not None:
                try:
                    params[key] = float(params[key])
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert {key} to float. Using existing value.")
    except Exception as e:
        logger.error(f"Error ensuring numeric types: {e}")

def _apply_intelligent_defaults(params: Dict[str, Any]) -> None:
    """
    Apply intelligent defaults based on context.
    
    Args:
        params: Dictionary to process (modified in-place)
    """
    try:
        # Default financing parameters if method is 'loan'
        if params.get('financing_method') == 'loan':
            if 'loan_term' not in params or params['loan_term'] is None:
                params['loan_term'] = 5
                logger.info("Applied default loan_term=5 for loan financing method")
            if 'interest_rate' not in params or params['interest_rate'] is None:
                params['interest_rate'] = 5.0  # 5%
                logger.info("Applied default interest_rate=5.0% for loan financing method")
            if 'down_payment_pct' not in params or params['down_payment_pct'] is None:
                params['down_payment_pct'] = 20.0  # 20%
                logger.info("Applied default down_payment_pct=20.0% for loan financing method")
            
        # Battery replacement defaults
        if params.get('enable_battery_replacement', False):
            if 'battery_replace_mode' not in params:
                params['battery_replace_mode'] = "Fixed Year"
                logger.info("Applied default battery replacement mode 'Fixed Year'")
                
            if params.get('battery_replace_mode') == "Fixed Year":
                if 'battery_replacement_year' not in params or params['battery_replacement_year'] is None:
                    # Set to middle of analysis period if possible
                    analysis_years = params.get('analysis_years', 15)
                    params['battery_replacement_year'] = max(1, min(analysis_years - 1, analysis_years // 2))
                    logger.info(f"Applied default battery_replacement_year={params['battery_replacement_year']}")
                    
            elif params.get('battery_replace_mode') == "Capacity Threshold":
                if 'battery_replacement_threshold' not in params or params['battery_replacement_threshold'] is None:
                    params['battery_replacement_threshold'] = 70.0  # 70%
                    logger.info("Applied default battery_replacement_threshold=70.0%")
                    
        # General defaults
        if 'discount_rate' not in params or params['discount_rate'] is None:
            params['discount_rate'] = 5.0  # 5%
            logger.info("Applied default discount_rate=5.0%")
            
        if 'inflation_rate' not in params or params['inflation_rate'] is None:
            params['inflation_rate'] = 2.5  # 2.5%
            logger.info("Applied default inflation_rate=2.5%")
            
    except Exception as e:
        logger.error(f"Error applying intelligent defaults: {e}")

def _map_params_to_nested_structure(flat_params: Dict[str, Any], 
                                   nested_params: Dict[str, Any]) -> None:
    """
    Map parameters from flat structure to nested structure based on defined mapping.
    
    Args:
        flat_params: Source flat dictionary
        nested_params: Target nested dictionary
    """
    # Define the key mapping (flat_key, target_dict, final_key)
    key_mapping = [
        # Scenario top-level
        ('name', 'scenario', 'name'),
        ('description', 'scenario', 'description'),
        ('analysis_years', 'scenario', 'analysis_years'),
        ('start_year', 'scenario', 'start_year'),
        ('annual_mileage', 'scenario', 'annual_mileage'),
        ('enable_battery_replacement', 'scenario', 'enable_battery_replacement'),
        ('battery_replacement_year', 'scenario', 'force_battery_replacement_year'),
        ('battery_replacement_threshold', 'scenario', 'battery_replacement_threshold'),
        ('financing_method', 'scenario', 'financing_method'),
        ('loan_term', 'scenario', 'loan_term'),
        ('interest_rate', 'scenario', 'interest_rate'),
        ('down_payment_pct', 'scenario', 'down_payment_pct'),
        
        # Detailed dictionaries to preserve
        ('electricity_price_projections', 'scenario', 'electricity_price_projections'),
        ('diesel_price_scenarios', 'scenario', 'diesel_price_scenarios'),
        ('maintenance_costs_detailed', 'scenario', 'maintenance_costs_detailed'),
        ('insurance_and_registration', 'scenario', 'insurance_and_registration'),
        ('infrastructure_costs', 'scenario', 'infrastructure_costs'),
        
        # Selection keys
        ('selected_electricity_scenario', 'scenario', 'selected_electricity_scenario'),
        ('selected_diesel_scenario', 'scenario', 'selected_diesel_scenario'),
        
        # Electric Vehicle
        ('electric_vehicle_name', 'ev', 'name'),
        ('electric_vehicle_price', 'ev', 'purchase_price'),
        ('electric_vehicle_battery_capacity', 'ev', 'battery_capacity_kwh'),
        ('electric_vehicle_energy_consumption', 'ev', 'energy_consumption_kwh_per_km'),
        ('electric_vehicle_battery_warranty', 'ev', 'battery_warranty_years'),
        ('electric_vehicle_residual_value_projections', 'ev', 'residual_value_projections'),
        ('annual_registration_cost', 'ev', 'registration_cost'),
        ('electric_vehicle_battery_pack_cost_projections_aud_per_kwh', 'ev', 'battery_pack_cost_projections_aud_per_kwh'),
        ('electric_vehicle_battery_cycle_life', 'ev', 'battery_cycle_life'),
        ('electric_vehicle_battery_depth_of_discharge', 'ev', 'battery_depth_of_discharge'),
        ('electric_vehicle_charging_efficiency', 'ev', 'charging_efficiency'),
        ('electric_vehicle_purchase_price_annual_decrease_real', 'ev', 'purchase_price_annual_decrease_real'),
        
        # Diesel Vehicle
        ('diesel_vehicle_name', 'diesel', 'name'),
        ('diesel_vehicle_price', 'diesel', 'purchase_price'),
        ('diesel_vehicle_fuel_consumption', 'diesel', 'fuel_consumption_l_per_100km'),
        ('diesel_vehicle_residual_value_projections', 'diesel', 'residual_value_projections'),
        ('annual_registration_cost', 'diesel', 'registration_cost'),
        ('diesel_vehicle_co2_emission_factor', 'diesel', 'co2_emission_factor')
    ]

    for flat_key, target_dict_name, final_key in key_mapping:
        try:
            if flat_key in flat_params:
                value = flat_params[flat_key]
                if target_dict_name == 'scenario':
                    nested_params[final_key] = value
                elif target_dict_name == 'ev':
                    nested_params['electric_vehicle'][final_key] = value
                elif target_dict_name == 'diesel':
                    nested_params['diesel_vehicle'][final_key] = value
            else:
                # Skip warning for conditionally removed battery parameters
                if not ((flat_key == 'battery_replacement_threshold' and 
                        flat_params.get('battery_replace_mode') == "Fixed Year") or 
                        (flat_key == 'battery_replacement_year' and 
                        flat_params.get('battery_replace_mode') == "Capacity Threshold")):
                    # Only log as warning if the key is actually required
                    if final_key in REQUIRED_KEYS:
                        logger.warning(f"Required key '{flat_key}' missing during mapping to {final_key}")
                    else:
                        logger.debug(f"Optional key '{flat_key}' not found during mapping to {final_key}")
        except Exception as e:
            logger.error(f"Error mapping {flat_key} to {final_key}: {e}")
            # Continue processing other keys rather than failing completely

def _validate_required_keys(nested_params: Dict[str, Any]) -> None:
    """
    Validate that all required keys are present in the nested structure.
    
    Args:
        nested_params: The nested dictionary to validate
        
    Raises:
        ValueError: If any required keys are missing
    """
    missing_keys = []
    
    # Check top-level required keys
    for key in ['name', 'analysis_years', 'start_year', 'annual_mileage', 'discount_rate_real']:
        if key not in nested_params:
            missing_keys.append(key)
            
    # Check electric vehicle required keys
    if 'electric_vehicle' not in nested_params:
        missing_keys.append('electric_vehicle')
    else:
        for key in ['name', 'purchase_price', 'battery_capacity_kwh', 'energy_consumption_kwh_per_km']:
            if key not in nested_params['electric_vehicle']:
                missing_keys.append(f"electric_vehicle.{key}")
                
    # Check diesel vehicle required keys
    if 'diesel_vehicle' not in nested_params:
        missing_keys.append('diesel_vehicle')
    else:
        for key in ['name', 'purchase_price', 'fuel_consumption_l_per_100km']:
            if key not in nested_params['diesel_vehicle']:
                missing_keys.append(f"diesel_vehicle.{key}")
                
    if missing_keys:
        error_msg = f"Missing required keys in scenario parameters: {', '.join(missing_keys)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

def invalidate_calculation_cache():
    """
    Invalidate any cached calculation results when parameters change.
    
    Should be called whenever scenario parameters are changed.
    """
    import streamlit as st
    if 'cached_results' in st.session_state:
        del st.session_state['cached_results']
        logger.debug("Calculation cache invalidated due to parameter changes")