"""
Utility functions for converting between different units and formats in the TCO Model.

This module includes functions for:
- Unit conversions (e.g., L/100km to kWh/km)
- Value format conversions (e.g., percentage to decimal)
- Date and time format conversions
"""
# Standard library imports
import datetime
from typing import Dict, List, Optional, Union, NewType, Any

# Application-specific imports
from config.constants import (
    DEFAULT_CURRENCY, DIESEL_ENERGY_CONTENT, KWH_TO_MJ_FACTOR
)

# Custom Types
Percentage = NewType('Percentage', float)
Decimal = NewType('Decimal', float)
LitersPer100KM = NewType('LitersPer100KM', float)
KWHPerKM = NewType('KWHPerKM', float)
KWH = NewType('KWH', float)
MJ = NewType('MJ', float)
YearIndex = NewType('YearIndex', int)
AUD = NewType('AUD', float)
Kilometres = NewType('Kilometres', float)

def percentage_to_decimal(percentage: Percentage) -> Decimal:
    """
    Convert a percentage value to its decimal equivalent.
    
    Args:
        percentage: A percentage value (e.g., 7.5 for 7.5%)
        
    Returns:
        The decimal equivalent (e.g., 0.075)
    """
    return Decimal(percentage / 100.0)


def decimal_to_percentage(decimal: Decimal) -> Percentage:
    """
    Convert a decimal value to its percentage equivalent.
    
    Args:
        decimal: A decimal value (e.g., 0.075)
        
    Returns:
        The percentage equivalent (e.g., 7.5)
    """
    return Percentage(decimal * 100.0)


def l_per_100km_to_kwh_per_km(fuel_consumption: LitersPer100KM, energy_conversion_factor: float = DIESEL_ENERGY_CONTENT) -> KWHPerKM:
    """
    Convert diesel fuel consumption in L/100km to energy consumption in kWh/km.
    
    Args:
        fuel_consumption: Fuel consumption in L/100km
        energy_conversion_factor: Energy content of diesel (kWh/L), default from constants
        
    Returns:
        Energy consumption in kWh/km
    """
    # First convert to L/km, then multiply by energy content
    return KWHPerKM((fuel_consumption / 100.0) * energy_conversion_factor)


def kwh_per_km_to_l_per_100km(energy_consumption: KWHPerKM, energy_conversion_factor: float = DIESEL_ENERGY_CONTENT) -> LitersPer100KM:
    """
    Convert energy consumption in kWh/km to diesel equivalent in L/100km.
    
    Args:
        energy_consumption: Energy consumption in kWh/km
        energy_conversion_factor: Energy content of diesel (kWh/L), default from constants
        
    Returns:
        Fuel consumption in L/100km
    """
    # Convert to L/km, then to L/100km
    return LitersPer100KM((energy_consumption / energy_conversion_factor) * 100.0)


def kwh_to_mj(kwh: KWH) -> MJ:
    """
    Convert kilowatt-hours to megajoules.
    
    Args:
        kwh: Energy in kilowatt-hours
        
    Returns:
        Energy in megajoules
    """
    return MJ(kwh * KWH_TO_MJ_FACTOR)  # 1 kWh = 3.6 MJ


def mj_to_kwh(mj: MJ) -> KWH:
    """
    Convert megajoules to kilowatt-hours.
    
    Args:
        mj: Energy in megajoules
        
    Returns:
        Energy in kilowatt-hours
    """
    return KWH(mj / KWH_TO_MJ_FACTOR)  # 1 kWh = 3.6 MJ


def flatten_nested_dict(nested_dict: Dict[str, Any], parent_key: str = '', separator: str = '_') -> Dict[str, Any]:
    """
    Flatten a nested dictionary structure into a single-level dictionary.
    
    Args:
        nested_dict: A dictionary potentially containing nested dictionaries
        parent_key: The parent key for the current recursive call
        separator: The character to use to separate nested keys
        
    Returns:
        A flattened dictionary
    """
    flat_dict: Dict[str, Any] = {}
    for key, value in nested_dict.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        
        if isinstance(value, dict):
            flat_dict.update(flatten_nested_dict(value, new_key, separator))
        else:
            flat_dict[new_key] = value
            
    return flat_dict


def unflatten_dict(flat_dict: Dict[str, Any], separator: str = '_') -> Dict[str, Any]:
    """
    Convert a flattened dictionary back to a nested structure.
    
    Args:
        flat_dict: A dictionary with keys that represent nested paths
        separator: The character used to separate nested keys
        
    Returns:
        A nested dictionary
    """
    result: Dict[str, Any] = {}
    
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


def format_currency(value: Union[float, AUD], currency: str = DEFAULT_CURRENCY, decimals: int = 0) -> str:
    """
    Format a value as currency.
    
    Args:
        value: The value to format
        currency: The currency code (default from constants)
        decimals: The number of decimal places (default: 0)
        
    Returns:
        Formatted currency string
    """
    if decimals == 0:
        return f"{currency} {value:,.0f}"
    else:
        return f"{currency} {value:,.{decimals}f}"


def format_percentage(value: Union[float, Decimal], decimals: int = 1) -> str:
    """
    Format a decimal value as a percentage string.
    
    Args:
        value: The decimal value to format (e.g., 0.075)
        decimals: The number of decimal places (default: 1)
        
    Returns:
        Formatted percentage string (e.g., "7.5%")
    """
    # Ensure the input is treated as a float for formatting
    float_value = float(value)
    return f"{float_value * 100:.{decimals}f}%"


def calculate_annual_projection(
    base_value: Union[float, AUD],
    annual_increase_rate: Decimal,
    year_index: YearIndex
) -> Union[float, AUD]:
    """
    Calculate a projected value based on a base value and annual increase rate.
    
    Args:
        base_value: The starting value
        annual_increase_rate: Annual increase rate as a decimal (e.g., 0.05 for 5%)
        year_index: The year index (0-based) for which to calculate the projection
        
    Returns:
        The projected value
    """
    # Determine return type based on input base_value type
    projected_value = base_value * (1 + annual_increase_rate) ** year_index
    if isinstance(base_value, AUD):
        return AUD(projected_value)
    else:
        return projected_value
