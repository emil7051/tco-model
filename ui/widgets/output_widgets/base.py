"""
Base classes for output widgets in the TCO Model application.

This module provides base classes for displaying calculation results.
"""

import streamlit as st
import pandas as pd
import logging
from typing import Dict, Any, Optional, List
from abc import abstractmethod

from ui.widgets.base import BaseWidget

logger = logging.getLogger(__name__)

class OutputWidget(BaseWidget):
    """Base class for output widgets."""
    
    def __init__(self, title: Optional[str] = None):
        """
        Initialize an output widget.
        
        Args:
            title: Optional title to display above the widget
        """
        super().__init__()
        self.title = title
    
    def render(self, params: Dict[str, Any]) -> None:
        """
        Render the output widget in the Streamlit UI.
        
        Args:
            params: Current calculation results
        """
        if self.title:
            st.subheader(self.title)
            
        self.render_content(params)
    
    @abstractmethod
    def render_content(self, params: Dict[str, Any]) -> None:
        """
        Render the content of the output widget.
        
        Args:
            params: Current calculation results
        """
        pass


def format_currency(value: Any) -> str:
    """
    Format a number as currency (e.g., $1,234.56).
    
    Args:
        value: Numerical value to format
        
    Returns:
        Formatted currency string
    """
    if value is None or pd.isna(value):
        return "N/A"
    
    try:
        if isinstance(value, str):
            value = float(value.replace("$", "").replace(",", ""))
        return f"${value:,.2f}"
    except (TypeError, ValueError):
        logger.debug(f"Could not format value '{value}' as currency.")
        return "N/A"


def format_value_by_type(value: Any, unit: str) -> str:
    """
    Format a value based on its unit type.
    
    Args:
        value: The value to format
        unit: The unit type (e.g., 'AUD', 'AUD/km', 'Year')
        
    Returns:
        Formatted value as a string
    """
    if unit == 'AUD':
        return format_currency(value)
    elif unit == 'AUD/km':
        return f"{value:.2f}" if value is not None else "N/A"
    else:
        return str(value) if value is not None else "N/A"


def is_valid_dataframe(df: Optional[pd.DataFrame]) -> bool:
    """
    Check if a DataFrame is valid and not empty.
    
    Args:
        df: DataFrame to check
        
    Returns:
        True if valid and not empty, False otherwise
    """
    return df is not None and isinstance(df, pd.DataFrame) and not df.empty


@st.cache_data 
def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    """
    Convert a Pandas DataFrame to CSV bytes for download.
    
    Args:
        df: DataFrame to convert
        
    Returns:
        Bytes representation of the CSV
    """
    if df is None or df.empty:
        return b""
    return df.to_csv(index=False).encode('utf-8') 