"""
Preprocessing utilities for transforming UI parameters to model format.

This module handles the conversion of flat UI parameters into the nested structure 
required by the Scenario model.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def preprocess_ui_params(flat_params: dict) -> dict:
    """
    Convert sidebar params (flat dict, % as numbers) into the nested structure for the Scenario model.
    
    Args:
        flat_params: A dictionary of UI parameters with flat structure
        
    Returns:
        A nested parameter dictionary compatible with the Scenario model
    """
    processed_flat = flat_params.copy()
    nested_params = {}
    logger.debug(f"Starting preprocessing with flat params: {processed_flat}")
    
    # Convert percentages back to decimals
    _convert_percentages_to_decimals(processed_flat)
    
    # Handle conditional battery replacement logic
    _process_battery_replacement_params(processed_flat)
    
    # Initialize required sub-dictionaries
    nested_params['electric_vehicle'] = {}
    nested_params['diesel_vehicle'] = {}
    
    # Set vehicle types and lifespans
    _set_vehicle_types_and_lifespans(processed_flat, nested_params)
    
    # Populate nested dictionaries based on mapping
    _map_parameters_to_nested_structure(processed_flat, nested_params)
    
    # Ensure registration costs are set correctly
    _ensure_registration_costs(processed_flat, nested_params)
    
    logger.debug(f"Preprocessing finished. Returning constructed nested params: {nested_params}")
    return nested_params

def _convert_percentages_to_decimals(params: Dict[str, Any]) -> None:
    """Convert percentage values from UI (0-100) to decimal values (0-1) for the model."""
    percent_keys = [
        'discount_rate', 'inflation_rate', 'interest_rate',
        'down_payment_pct',
        'battery_replacement_threshold',
        'charger_maintenance_percent', 
        'maintenance_increase_rate', 'insurance_increase_rate',
        'registration_increase_rate', 'carbon_tax_increase_rate',
        'road_user_charge_increase_rate'
    ]
    
    for key in percent_keys:
        if key in params and isinstance(params[key], (int, float)) and params[key] is not None:
            params[key] = params[key] / 100.0
    
    logger.debug(f"Converted percentage values to decimals")

def _process_battery_replacement_params(params: Dict[str, Any]) -> None:
    """Handle conditional battery replacement logic based on UI selection."""
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

def _set_vehicle_types_and_lifespans(flat_params: Dict[str, Any], nested_params: Dict[str, Any]) -> None:
    """Extract vehicle types from session state and set lifespans."""
    import streamlit as st
    
    original_nested = st.session_state.get('original_nested_scenario', {})
    original_ev = original_nested.get('electric_vehicle', {})
    original_diesel = original_nested.get('diesel_vehicle', {})

    nested_params['electric_vehicle']['vehicle_type'] = original_ev.get('vehicle_type', 'rigid')
    nested_params['diesel_vehicle']['vehicle_type'] = original_diesel.get('vehicle_type', 'rigid')

    if 'analysis_years' in flat_params:
        nested_params['electric_vehicle']['lifespan'] = flat_params['analysis_years']
        nested_params['diesel_vehicle']['lifespan'] = flat_params['analysis_years']
    else:
        logger.warning("'analysis_years' not found in flat_params, cannot set vehicle lifespan.")

def _map_parameters_to_nested_structure(flat_params: Dict[str, Any], nested_params: Dict[str, Any]) -> None:
    """Map parameters from flat structure to nested structure based on defined mapping."""
    # Define mapping from flat UI keys to nested structure locations and final keys
    key_mapping = [
        # Scenario Top-Level
        ('name', 'scenario', 'name'),
        ('description', 'scenario', 'description'),
        ('start_year', 'scenario', 'start_year'),
        ('analysis_years', 'scenario', 'analysis_years'),
        ('inflation_rate', 'scenario', 'inflation_rate'),
        ('financing_method', 'scenario', 'financing_method'),
        ('loan_term', 'scenario', 'loan_term'),
        ('interest_rate', 'scenario', 'interest_rate'),
        ('down_payment_pct', 'scenario', 'down_payment_pct'),
        ('annual_mileage', 'scenario', 'annual_mileage'),
        # Infrastructure related keys
        ('charger_cost', 'scenario', 'selected_charger_cost'),
        ('charger_installation_cost', 'scenario', 'selected_installation_cost'),
        ('charger_lifespan', 'scenario', 'charger_lifespan'),
        ('charger_maintenance_percent', 'scenario', 'charger_maintenance_percent'),
        # Other scenario keys
        ('carbon_tax_rate', 'scenario', 'carbon_tax_rate'),
        ('road_user_charge', 'scenario', 'road_user_charge'),
        ('enable_battery_replacement', 'scenario', 'enable_battery_replacement'),
        ('battery_replacement_threshold', 'scenario', 'battery_replacement_threshold'),
        ('battery_replacement_year', 'scenario', 'force_battery_replacement_year'),
        ('carbon_tax_increase_rate', 'scenario', 'carbon_tax_increase_rate'),
        ('road_user_charge_increase_rate', 'scenario', 'road_user_charge_increase_rate'),
        ('maintenance_increase_rate', 'scenario', 'maintenance_increase_rate'),
        ('insurance_increase_rate', 'scenario', 'insurance_increase_rate'),
        ('registration_increase_rate', 'scenario', 'registration_increase_rate'),
        ('include_carbon_tax', 'scenario', 'include_carbon_tax'),
        ('include_road_user_charge', 'scenario', 'include_road_user_charge'),
        ('battery_degradation_rate', 'scenario', 'battery_degradation_rate'),
        ('discount_rate', 'scenario', 'discount_rate_real'),

        # Pass through complex dictionary structures loaded during init
        ('electricity_price_projections', 'scenario', 'electricity_price_projections'),
        ('diesel_price_scenarios', 'scenario', 'diesel_price_scenarios'),
        ('maintenance_costs_detailed', 'scenario', 'maintenance_costs_detailed'),
        ('insurance_and_registration', 'scenario', 'insurance_and_registration'),
        ('infrastructure_costs', 'scenario', 'infrastructure_costs'),

        # Selection keys from UI
        ('selected_electricity_scenario', 'scenario', 'selected_electricity_scenario'),
        ('selected_diesel_scenario', 'scenario', 'selected_diesel_scenario'),

        # Electric Vehicle Nested
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

        # Diesel Vehicle Nested
        ('diesel_vehicle_name', 'diesel', 'name'),
        ('diesel_vehicle_price', 'diesel', 'purchase_price'),
        ('diesel_vehicle_fuel_consumption', 'diesel', 'fuel_consumption_l_per_100km'),
        ('diesel_vehicle_residual_value_projections', 'diesel', 'residual_value_projections'),
        ('annual_registration_cost', 'diesel', 'registration_cost'),
        ('diesel_vehicle_co2_emission_factor', 'diesel', 'co2_emission_factor')
    ]

    for flat_key, target_dict_name, final_key in key_mapping:
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
            if not ((flat_key == 'battery_replacement_threshold' and flat_params.get('battery_replace_mode') == "Fixed Year") or 
                    (flat_key == 'battery_replacement_year' and flat_params.get('battery_replace_mode') == "Capacity Threshold")):
                logger.warning(f"Mapped key '{flat_key}' not found in processed flat parameters during restructuring.")

def _ensure_registration_costs(flat_params: Dict[str, Any], nested_params: Dict[str, Any]) -> None:
    """Ensure registration costs are properly set for both vehicle types."""
    default_reg_cost = 5000.0
    reg_cost_from_flat = flat_params.get('annual_registration_cost')

    if reg_cost_from_flat is not None and isinstance(reg_cost_from_flat, (int, float)):
        final_reg_cost = reg_cost_from_flat
    else:
        final_reg_cost = default_reg_cost
        logger.warning(f"'annual_registration_cost' key not found or invalid. Using default: {final_reg_cost}")

    if 'electric_vehicle' in nested_params:
        nested_params['electric_vehicle']['registration_cost'] = final_reg_cost
    if 'diesel_vehicle' in nested_params:
        nested_params['diesel_vehicle']['registration_cost'] = final_reg_cost 