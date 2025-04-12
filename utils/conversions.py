"""
Utility functions for converting between different units and formats in the TCO Model.

This module includes functions for:
- Unit conversions (e.g., L/100km to kWh/km)
- Value format conversions (e.g., percentage to decimal)
- Date and time format conversions
"""
from typing import Dict, List, Union, Optional
import datetime


def percentage_to_decimal(percentage: float) -> float:
    """
    Convert a percentage value to its decimal equivalent.
    
    Args:
        percentage: A percentage value (e.g., 7.5 for 7.5%)
        
    Returns:
        The decimal equivalent (e.g., 0.075)
    """
    return percentage / 100.0


def decimal_to_percentage(decimal: float) -> float:
    """
    Convert a decimal value to its percentage equivalent.
    
    Args:
        decimal: A decimal value (e.g., 0.075)
        
    Returns:
        The percentage equivalent (e.g., 7.5)
    """
    return decimal * 100.0


def l_per_100km_to_kwh_per_km(fuel_consumption: float, energy_conversion_factor: float = 10.0) -> float:
    """
    Convert diesel fuel consumption in L/100km to energy consumption in kWh/km.
    
    Args:
        fuel_consumption: Fuel consumption in L/100km
        energy_conversion_factor: Energy content of diesel (kWh/L), default 10.0
        
    Returns:
        Energy consumption in kWh/km
    """
    # First convert to L/km, then multiply by energy content
    return (fuel_consumption / 100.0) * energy_conversion_factor


def kwh_per_km_to_l_per_100km(energy_consumption: float, energy_conversion_factor: float = 10.0) -> float:
    """
    Convert energy consumption in kWh/km to diesel equivalent in L/100km.
    
    Args:
        energy_consumption: Energy consumption in kWh/km
        energy_conversion_factor: Energy content of diesel (kWh/L), default 10.0
        
    Returns:
        Fuel consumption in L/100km
    """
    # Convert to L/km, then to L/100km
    return (energy_consumption / energy_conversion_factor) * 100.0


def kwh_to_mj(kwh: float) -> float:
    """
    Convert kilowatt-hours to megajoules.
    
    Args:
        kwh: Energy in kilowatt-hours
        
    Returns:
        Energy in megajoules
    """
    return kwh * 3.6  # 1 kWh = 3.6 MJ


def mj_to_kwh(mj: float) -> float:
    """
    Convert megajoules to kilowatt-hours.
    
    Args:
        mj: Energy in megajoules
        
    Returns:
        Energy in kilowatt-hours
    """
    return mj / 3.6  # 1 kWh = 3.6 MJ


def flatten_nested_dict(nested_dict: Dict, parent_key: str = '', separator: str = '_') -> Dict:
    """
    Flatten a nested dictionary structure into a single-level dictionary.
    
    Args:
        nested_dict: A dictionary potentially containing nested dictionaries
        parent_key: The parent key for the current recursive call
        separator: The character to use to separate nested keys
        
    Returns:
        A flattened dictionary
    """
    flat_dict = {}
    for key, value in nested_dict.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        
        if isinstance(value, dict):
            flat_dict.update(flatten_nested_dict(value, new_key, separator))
        else:
            flat_dict[new_key] = value
            
    return flat_dict


def unflatten_dict(flat_dict: Dict, separator: str = '_') -> Dict:
    """
    Convert a flattened dictionary back to a nested structure.
    
    Args:
        flat_dict: A dictionary with keys that represent nested paths
        separator: The character used to separate nested keys
        
    Returns:
        A nested dictionary
    """
    result = {}
    
    for key, value in flat_dict.items():
        parts = key.split(separator)
        d = result
        
        # Navigate to the appropriate nested dictionary
        for part in parts[:-1]:
            if part not in d:
                d[part] = {}
            d = d[part]
        
        # Set the value in the deepest level
        d[parts[-1]] = value
        
    return result


def format_currency(value: float, currency: str = 'AUD', decimals: int = 0) -> str:
    """
    Format a value as currency.
    
    Args:
        value: The value to format
        currency: The currency code (default: 'AUD')
        decimals: The number of decimal places (default: 0)
        
    Returns:
        Formatted currency string
    """
    if decimals == 0:
        return f"{currency} {value:,.0f}"
    else:
        return f"{currency} {value:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format a decimal value as a percentage string.
    
    Args:
        value: The decimal value to format (e.g., 0.075)
        decimals: The number of decimal places (default: 1)
        
    Returns:
        Formatted percentage string (e.g., "7.5%")
    """
    return f"{value * 100:.{decimals}f}%"


def calculate_annual_projection(
    base_value: float, 
    annual_increase_rate: float, 
    year_index: int
) -> float:
    """
    Calculate a projected value based on a base value and annual increase rate.
    
    Args:
        base_value: The starting value
        annual_increase_rate: Annual increase rate as a decimal (e.g., 0.05 for 5%)
        year_index: The year index (0-based) for which to calculate the projection
        
    Returns:
        The projected value
    """
    return base_value * (1 + annual_increase_rate) ** year_index
