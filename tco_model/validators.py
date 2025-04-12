"""
Validators for TCO Model inputs.

This module provides validation functions and classes to ensure data integrity
and appropriate constraints for TCO model calculations.
"""
from typing import Any, Dict, List, Union, Optional, Callable
from pydantic import validator, root_validator, Field
import datetime


def validate_positive(value: float, field_name: str) -> float:
    """
    Validate that a value is positive (> 0).
    
    Args:
        value: The value to validate
        field_name: The name of the field for error messages
        
    Returns:
        The original value if valid
        
    Raises:
        ValueError: If value is not positive
    """
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value


def validate_non_negative(value: float, field_name: str) -> float:
    """
    Validate that a value is non-negative (>= 0).
    
    Args:
        value: The value to validate
        field_name: The name of the field for error messages
        
    Returns:
        The original value if valid
        
    Raises:
        ValueError: If value is negative
    """
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def validate_percentage(value: float, field_name: str, allow_zero: bool = True) -> float:
    """
    Validate that a value is a valid percentage (0-100, optionally disallowing 0).
    
    Args:
        value: The percentage value to validate
        field_name: The name of the field for error messages
        allow_zero: Whether to allow 0 as a valid value
        
    Returns:
        The original value if valid
        
    Raises:
        ValueError: If value is not a valid percentage
    """
    if allow_zero:
        if value < 0 or value > 100:
            raise ValueError(f"{field_name} must be between 0 and 100")
    else:
        if value <= 0 or value > 100:
            raise ValueError(f"{field_name} must be between 0 and 100 (exclusive of 0)")
    return value


def validate_year(value: int, field_name: str, min_year: int = 1900, max_year: int = 2100) -> int:
    """
    Validate that a value is a valid year within a specified range.
    
    Args:
        value: The year to validate
        field_name: The name of the field for error messages
        min_year: The minimum allowed year
        max_year: The maximum allowed year
        
    Returns:
        The original value if valid
        
    Raises:
        ValueError: If value is not a valid year
    """
    if value < min_year or value > max_year:
        raise ValueError(f"{field_name} must be between {min_year} and {max_year}")
    return value


def validate_in_range(value: float, field_name: str, min_value: float, max_value: float,
                    include_min: bool = True, include_max: bool = True) -> float:
    """
    Validate that a value is within a specified range.
    
    Args:
        value: The value to validate
        field_name: The name of the field for error messages
        min_value: The minimum allowed value
        max_value: The maximum allowed value
        include_min: Whether the minimum value is inclusive
        include_max: Whether the maximum value is inclusive
        
    Returns:
        The original value if valid
        
    Raises:
        ValueError: If value is not within the specified range
    """
    min_check = value >= min_value if include_min else value > min_value
    max_check = value <= max_value if include_max else value < max_value
    
    if not (min_check and max_check):
        min_symbol = "[" if include_min else "("
        max_symbol = "]" if include_max else ")"
        raise ValueError(f"{field_name} must be in range {min_symbol}{min_value}, {max_value}{max_symbol}")
    
    return value


def validate_dict_keys(value: Dict, required_keys: List[str], field_name: str) -> Dict:
    """
    Validate that a dictionary contains all required keys.
    
    Args:
        value: The dictionary to validate
        required_keys: List of keys that must be present
        field_name: The name of the field for error messages
        
    Returns:
        The original dictionary if valid
        
    Raises:
        ValueError: If any required keys are missing
    """
    missing_keys = [key for key in required_keys if key not in value]
    if missing_keys:
        raise ValueError(f"{field_name} is missing required keys: {', '.join(missing_keys)}")
    return value


def validate_dict_values(value: Dict, validator_fn: Callable, field_name: str) -> Dict:
    """
    Validate that all values in a dictionary pass a validator function.
    
    Args:
        value: The dictionary to validate
        validator_fn: Function that takes a value and returns True if valid
        field_name: The name of the field for error messages
        
    Returns:
        The original dictionary if valid
        
    Raises:
        ValueError: If any values fail validation
    """
    invalid_keys = [key for key, val in value.items() if not validator_fn(val)]
    if invalid_keys:
        raise ValueError(f"{field_name} has invalid values for keys: {', '.join(invalid_keys)}")
    return value


def validate_list_items(value: List, validator_fn: Callable, field_name: str) -> List:
    """
    Validate that all items in a list pass a validator function.
    
    Args:
        value: The list to validate
        validator_fn: Function that takes an item and returns True if valid
        field_name: The name of the field for error messages
        
    Returns:
        The original list if valid
        
    Raises:
        ValueError: If any items fail validation
    """
    invalid_indices = [i for i, item in enumerate(value) if not validator_fn(item)]
    if invalid_indices:
        raise ValueError(f"{field_name} has invalid items at indices: {', '.join(map(str, invalid_indices))}")
    return value


def validate_date_sequence(dates: List[datetime.date], field_name: str) -> List[datetime.date]:
    """
    Validate that a list of dates is in chronological order.
    
    Args:
        dates: The list of dates to validate
        field_name: The name of the field for error messages
        
    Returns:
        The original list if valid
        
    Raises:
        ValueError: If the dates are not in chronological order
    """
    if not all(dates[i] < dates[i+1] for i in range(len(dates)-1)):
        raise ValueError(f"{field_name} must be in chronological order")
    return dates


def validate_consistent_length(list1: List, list2: List, field1_name: str, field2_name: str) -> None:
    """
    Validate that two lists have the same length.
    
    Args:
        list1: The first list
        list2: The second list
        field1_name: The name of the first field for error messages
        field2_name: The name of the second field for error messages
        
    Raises:
        ValueError: If the lists have different lengths
    """
    if len(list1) != len(list2):
        raise ValueError(f"{field1_name} and {field2_name} must have the same length")


def validate_consistent_years(year_values: Dict[int, Any], start_year: int, years: int, field_name: str) -> Dict[int, Any]:
    """
    Validate that a dictionary of year-keyed values has entries for each year in the analysis period.
    
    Args:
        year_values: Dictionary with years as keys
        start_year: First year of the analysis period
        years: Number of years in the analysis period
        field_name: The name of the field for error messages
        
    Returns:
        The original dictionary if valid
        
    Raises:
        ValueError: If any years are missing
    """
    required_years = set(range(start_year, start_year + years))
    provided_years = set(year_values.keys())
    
    missing_years = required_years - provided_years
    if missing_years:
        raise ValueError(f"{field_name} is missing values for years: {', '.join(map(str, sorted(missing_years)))}")
    
    return year_values
