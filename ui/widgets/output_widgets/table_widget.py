"""
Table widgets for displaying TCO data in the application.

This module provides widgets for displaying tabular data from TCO calculations.
"""

import streamlit as st
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional, Callable

from ui.widgets.output_widgets.base import OutputWidget, format_currency, is_valid_dataframe, convert_df_to_csv

logger = logging.getLogger(__name__)

class TableWidget(OutputWidget):
    """Base class for table output widgets."""
    
    def __init__(self, title: str, enable_download: bool = True):
        """
        Initialize a table widget.
        
        Args:
            title: Table title to display
            enable_download: Whether to show download button for CSV
        """
        super().__init__(title)
        self.enable_download = enable_download
    
    def format_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Format the dataframe for display.
        
        Child classes should override this to apply specific formatting.
        
        Args:
            df: Dataframe to format
            
        Returns:
            Formatted dataframe
        """
        return df
    
    def get_download_label(self) -> str:
        """Get the label for the download button."""
        return f"Download {self.title} as CSV"
    
    def render_content(self, params: Dict[str, Any]) -> None:
        """
        Render the table content.
        
        Args:
            params: Current calculation results
        """
        # Get dataframe from child class
        df = self.get_dataframe(params)
        
        if df is not None and not df.empty:
            # Format dataframe for display
            display_df = self.format_dataframe(df)
            
            # Display the table
            st.dataframe(display_df, use_container_width=True)
            
            # Add download button if enabled
            if self.enable_download:
                csv = convert_df_to_csv(df)
                st.download_button(
                    label=self.get_download_label(),
                    data=csv,
                    file_name=f"{self.title.lower().replace(' ', '_')}.csv",
                    mime='text/csv',
                )
        else:
            st.info("No data available for display.")
    
    def get_dataframe(self, params: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """
        Get the dataframe to display.
        
        Child classes must implement this method to extract the relevant
        dataframe from the parameters.
        
        Args:
            params: Current calculation results
            
        Returns:
            Dataframe to display or None if no data available
        """
        return None


class TCOSummaryTable(TableWidget):
    """Table showing TCO summary data."""
    
    def __init__(self):
        super().__init__("TCO Summary")
    
    def get_dataframe(self, params: Dict[str, Any]) -> Optional[pd.DataFrame]:
        if 'tco_summary' not in params or not is_valid_dataframe(params['tco_summary']):
            return None
        return params['tco_summary']
    
    def format_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format monetary values as currency."""
        formatted_df = df.copy()
        
        # Format all numeric columns as currency except 'Vehicle' column
        for col in formatted_df.columns:
            if col != 'Vehicle':
                formatted_df[col] = formatted_df[col].apply(format_currency)
                
        return formatted_df


class TCOBreakdownTable(TableWidget):
    """Table showing detailed cost breakdown per year."""
    
    def __init__(self, vehicle_type: str):
        """
        Initialize a TCO breakdown table.
        
        Args:
            vehicle_type: Vehicle type to display ("electric" or "diesel")
        """
        super().__init__(f"{vehicle_type.title()} Cost Breakdown")
        self.vehicle_type = vehicle_type
    
    def get_dataframe(self, params: Dict[str, Any]) -> Optional[pd.DataFrame]:
        key = f"{self.vehicle_type}_yearly_costs"
        if key not in params or not is_valid_dataframe(params[key]):
            return None
        return params[key]
    
    def format_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format monetary values as currency."""
        formatted_df = df.copy()
        
        # Format all numeric columns as currency except 'Year' column
        for col in formatted_df.columns:
            if col != 'Year':
                formatted_df[col] = formatted_df[col].apply(format_currency)
                
        return formatted_df


class ComparisonTable(TableWidget):
    """Table showing side-by-side comparison of vehicle parameters."""
    
    def __init__(self):
        super().__init__("Vehicle Comparison")
    
    def get_dataframe(self, params: Dict[str, Any]) -> Optional[pd.DataFrame]:
        if 'vehicle_comparison' not in params or not is_valid_dataframe(params['vehicle_comparison']):
            return None
        return params['vehicle_comparison']
    
    def format_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format values according to their type."""
        formatted_df = df.copy()
        
        # Format values based on Parameter type
        for i, row in formatted_df.iterrows():
            param = row['Parameter']
            if 'cost' in param.lower() or 'price' in param.lower() or 'value' in param.lower():
                for col in formatted_df.columns:
                    if col != 'Parameter' and pd.notna(row[col]):
                        formatted_df.at[i, col] = format_currency(row[col])
                        
        return formatted_df


class SensitivityTable(TableWidget):
    """Table showing sensitivity analysis results."""
    
    def __init__(self):
        super().__init__("Sensitivity Analysis Results")
    
    def get_dataframe(self, params: Dict[str, Any]) -> Optional[pd.DataFrame]:
        if 'sensitivity_analysis' not in params or not is_valid_dataframe(params['sensitivity_analysis']):
            return None
        return params['sensitivity_analysis']
    
    def format_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format impact values as currency."""
        formatted_df = df.copy()
        
        # Format Impact column as currency with +/- sign
        formatted_df['Impact'] = formatted_df['Impact'].apply(
            lambda x: f"+{format_currency(x)}" if x > 0 else format_currency(x)
        )
        
        # Sort by absolute impact
        if 'abs_impact' not in formatted_df.columns:
            formatted_df['abs_impact'] = formatted_df['Impact'].apply(
                lambda x: abs(float(x.replace('$', '').replace(',', '').replace('+', '')))
            )
        
        formatted_df = formatted_df.sort_values('abs_impact', ascending=False)
        formatted_df = formatted_df.drop(columns=['abs_impact'])
        
        return formatted_df 