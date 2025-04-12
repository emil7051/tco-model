"""
Sensitivity analysis widgets for the TCO Model application.

This module provides widgets for visualizing how TCO varies with changes to input parameters.
"""

import streamlit as st
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional, Tuple

from ui.widgets.output_widgets.base import OutputWidget, format_currency, is_valid_dataframe
from ui.widgets.output_widgets.chart_widget import SensitivityAnalysisChart
from ui.widgets.output_widgets.table_widget import SensitivityTable

logger = logging.getLogger(__name__)

class SensitivityAnalysisWidget(OutputWidget):
    """Widget to display TCO sensitivity analysis results."""
    
    def __init__(self):
        """Initialize the sensitivity analysis widget."""
        super().__init__("Sensitivity Analysis")
        
        # Initialize child widgets
        self.chart = SensitivityAnalysisChart()
        self.table = SensitivityTable()
    
    def render_content(self, params: Dict[str, Any]) -> None:
        """
        Render the sensitivity analysis content.
        
        Args:
            params: Current calculation results
        """
        if 'sensitivity_analysis' not in params or not is_valid_dataframe(params['sensitivity_analysis']):
            st.info("No sensitivity analysis data available.")
            return
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Chart", "Table", "Insights"])
        
        # Tab 1: Tornado chart
        with tab1:
            self.chart.render(params)
        
        # Tab 2: Data table
        with tab2:
            self.table.render(params)
        
        # Tab 3: Insights
        with tab3:
            self._render_insights(params)
    
    def _render_insights(self, params: Dict[str, Any]) -> None:
        """
        Render insights derived from sensitivity analysis.
        
        Args:
            params: Current calculation results
        """
        df = params['sensitivity_analysis']
        
        if df.empty:
            st.info("No sensitivity data available for insights.")
            return
        
        # Sort by absolute impact
        if 'abs_impact' not in df.columns:
            df['abs_impact'] = df['Impact'].abs()
        
        df_sorted = df.sort_values('abs_impact', ascending=False)
        
        # Show top 3 most influential parameters
        st.subheader("Most Influential Parameters")
        top_params = df_sorted.head(3)
        
        for _, row in top_params.iterrows():
            with st.container():
                impact_text = f"Increases TCO by {format_currency(abs(row['Impact']))}" if row['Impact'] > 0 else f"Decreases TCO by {format_currency(abs(row['Impact']))}"
                st.metric(
                    label=row['Parameter'],
                    value=impact_text
                )
                
                # Add recommendation based on parameter
                if row['Impact'] > 0:
                    st.write(f"**Recommendation**: Consider strategies to reduce {row['Parameter'].lower()} to improve TCO.")
                else:
                    st.write(f"**Recommendation**: This parameter provides cost advantages. Consider leveraging it further.")
                
                st.divider()
        
        # Display the variance
        if len(df) > 0:
            max_impact = df['abs_impact'].max()
            min_impact = df['abs_impact'].min()
            range_impact = max_impact - min_impact
            
            if max_impact > 0:
                st.subheader("Variance Analysis")
                st.write(f"The range of parameter impacts spans {format_currency(range_impact)}, indicating the variability in how different factors affect TCO.")
                
                # Calculate coefficient of variation if possible
                if 'tco_summary' in params and not params['tco_summary'].empty:
                    total_tco = params['tco_summary']['Total'].iloc[0]
                    if total_tco > 0:
                        relative_impact = (max_impact / total_tco) * 100
                        st.write(f"The most impactful parameter can change the TCO by up to {relative_impact:.1f}% of the total cost.")


class WhatIfAnalysisWidget(OutputWidget):
    """Widget to interactively explore what-if scenarios with parameter changes."""
    
    def __init__(self, title: str = "What-If Analysis"):
        """
        Initialize the what-if analysis widget.
        
        Args:
            title: Widget title
        """
        super().__init__(title)
    
    def render_content(self, params: Dict[str, Any]) -> None:
        """
        Render the what-if analysis content.
        
        Args:
            params: Current calculation results
        """
        if 'sensitivity_analysis' not in params or not is_valid_dataframe(params['sensitivity_analysis']):
            st.info("No sensitivity data available for what-if analysis.")
            return
        
        st.write("Explore how changes to key parameters affect the Total Cost of Ownership.")
        
        # Get parameters from sensitivity analysis
        df = params['sensitivity_analysis']
        parameters = df['Parameter'].tolist()
        
        # Select parameters to adjust
        selected_params = st.multiselect(
            "Select parameters to adjust:",
            parameters,
            max_selections=3
        )
        
        if not selected_params:
            st.info("Select at least one parameter to perform what-if analysis.")
            return
        
        # Create sliders for selected parameters
        param_adjustments = {}
        for param in selected_params:
            # Default range of ±20%
            default_val = 0
            min_val = -20
            max_val = 20
            
            param_adjustments[param] = st.slider(
                f"Adjust {param} (%)",
                min_value=min_val,
                max_value=max_val,
                value=default_val,
                step=5
            )
        
        # Calculate impact of adjustments
        if st.button("Calculate Impact"):
            self._calculate_impact(params, param_adjustments, df)
    
    def _calculate_impact(self, params: Dict[str, Any], adjustments: Dict[str, float], sensitivity_df: pd.DataFrame) -> None:
        """
        Calculate and display the impact of parameter adjustments.
        
        Args:
            params: Current calculation results
            adjustments: Dictionary of parameter adjustments (%)
            sensitivity_df: Sensitivity analysis dataframe
        """
        if 'tco_summary' not in params or params['tco_summary'] is None or params['tco_summary'].empty:
            st.error("TCO summary data not available.")
            return
        
        # Get base TCO
        base_tco = params['tco_summary']['Total'].iloc[0]
        
        # Calculate adjusted TCO
        total_impact = 0
        impacts = []
        
        for param, adjustment in adjustments.items():
            # Find parameter in sensitivity data
            param_data = sensitivity_df[sensitivity_df['Parameter'] == param]
            
            if not param_data.empty:
                # Get impact per 1% change (assuming linearity)
                base_impact = param_data['Impact'].values[0]
                # Scale by the adjustment percentage
                impact = (base_impact / 10) * adjustment  # Assuming sensitivity is for 10% change
                
                total_impact += impact
                impacts.append((param, impact))
        
        # Calculate new TCO
        adjusted_tco = base_tco + total_impact
        
        # Display results
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                label="Original TCO",
                value=format_currency(base_tco)
            )
            
            st.metric(
                label="Adjusted TCO",
                value=format_currency(adjusted_tco),
                delta=format_currency(adjusted_tco - base_tco)
            )
        
        with col2:
            st.subheader("Impact Breakdown")
            
            for param, impact in impacts:
                delta_text = "+" if impact >= 0 else ""
                st.write(f"{param}: {delta_text}{format_currency(impact)}")
            
            st.write("---")
            st.write(f"**Total Impact**: {format_currency(total_impact)}")
        
        # Show percentage change
        if base_tco > 0:
            percent_change = (total_impact / base_tco) * 100
            st.info(f"The combined parameter adjustments result in a {percent_change:.2f}% change in TCO.") 