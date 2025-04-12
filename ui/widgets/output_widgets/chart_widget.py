"""
Chart widgets for visualizing TCO data in the application.

This module provides widgets for displaying different types of charts for TCO results.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from abc import abstractmethod

from ui.widgets.output_widgets.base import OutputWidget, format_currency, is_valid_dataframe

logger = logging.getLogger(__name__)

class ChartWidget(OutputWidget):
    """Base class for chart output widgets."""
    
    def __init__(self, title: str, height: int = 400):
        """
        Initialize a chart widget.
        
        Args:
            title: Chart title to display
            height: Chart height in pixels
        """
        super().__init__(title)
        self.height = height
        
    @abstractmethod
    def create_chart(self, data: Dict[str, Any]) -> Optional[Union[go.Figure, px.Figure]]:
        """
        Create the chart visualization.
        
        Args:
            data: The data to visualize
            
        Returns:
            A Plotly figure object or None if chart cannot be created
        """
        pass
        
    def render_content(self, params: Dict[str, Any]) -> None:
        """
        Render the chart content.
        
        Args:
            params: Current calculation results
        """
        fig = self.create_chart(params)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True, height=self.height)
        else:
            st.info("Insufficient data to create chart.")


class TCOComparisonChart(ChartWidget):
    """Bar chart comparing TCO between vehicle types."""
    
    def __init__(self, height: int = 400):
        super().__init__("Total Cost of Ownership Comparison", height)
    
    def create_chart(self, data: Dict[str, Any]) -> Optional[go.Figure]:
        if 'tco_summary' not in data or not is_valid_dataframe(data['tco_summary']):
            return None
            
        df = data['tco_summary']
        
        # Create grouped bar chart
        fig = go.Figure()
        
        vehicles = df['Vehicle'].unique()
        cost_types = [col for col in df.columns if col not in ['Vehicle', 'Total']]
        
        # Add bars for each cost type
        for cost_type in cost_types:
            fig.add_trace(go.Bar(
                x=vehicles,
                y=df[cost_type],
                name=cost_type,
                hovertemplate="%{x}<br>%{y:$,.2f}"
            ))
        
        # Add total TCO text annotations
        for i, vehicle in enumerate(vehicles):
            total = df.loc[df['Vehicle'] == vehicle, 'Total'].values[0]
            fig.add_annotation(
                x=vehicle,
                y=total,
                text=f"Total: {format_currency(total)}",
                showarrow=True,
                arrowhead=1,
                yshift=10
            )
        
        # Customize layout
        fig.update_layout(
            barmode='stack',
            yaxis_title="Cost (AUD)",
            legend_title="Cost Components",
            hovermode="closest"
        )
        
        return fig


class TCOPerKmChart(ChartWidget):
    """Line chart showing TCO per km over distance."""
    
    def __init__(self, height: int = 400):
        super().__init__("TCO per Kilometer vs. Distance", height)
    
    def create_chart(self, data: Dict[str, Any]) -> Optional[px.Figure]:
        if 'tco_per_km' not in data or not is_valid_dataframe(data['tco_per_km']):
            return None
            
        df = data['tco_per_km']
        
        fig = px.line(
            df, 
            x='Distance', 
            y='TCO_per_km',
            color='Vehicle',
            labels={
                'Distance': 'Distance (km)',
                'TCO_per_km': 'Cost per Kilometer (AUD/km)',
                'Vehicle': 'Vehicle Type'
            }
        )
        
        # Add breakeven point annotation if it exists
        if 'breakeven_distance' in data and data['breakeven_distance']:
            breakeven = data['breakeven_distance']
            fig.add_vline(
                x=breakeven,
                line_dash="dash",
                line_color="green",
                annotation_text=f"Breakeven: {breakeven:,.0f} km",
                annotation_position="top right"
            )
        
        fig.update_traces(mode='lines+markers')
        
        return fig


class CostBreakdownPieChart(ChartWidget):
    """Pie chart showing cost breakdown for a single vehicle type."""
    
    def __init__(self, vehicle_type: str, height: int = 400):
        """
        Initialize a cost breakdown pie chart.
        
        Args:
            vehicle_type: Vehicle type to display ("electric" or "diesel")
            height: Chart height in pixels
        """
        super().__init__(f"{vehicle_type.title()} Vehicle Cost Breakdown", height)
        self.vehicle_type = vehicle_type
    
    def create_chart(self, data: Dict[str, Any]) -> Optional[go.Figure]:
        if 'tco_breakdown' not in data or not is_valid_dataframe(data['tco_breakdown']):
            return None
            
        df = data['tco_breakdown']
        
        # Filter for the specified vehicle type
        df_vehicle = df[df['Vehicle'] == self.vehicle_type.title()]
        
        if df_vehicle.empty:
            return None
            
        # Get cost components (exclude Vehicle and Total columns)
        components = [col for col in df_vehicle.columns if col not in ['Vehicle', 'Total']]
        values = df_vehicle[components].values[0]
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=components,
            values=values,
            hole=0.4,
            textinfo='label+percent',
            hovertemplate="%{label}<br>%{value:$,.2f}<br>%{percent}"
        )])
        
        # Add total annotation in the center
        total = df_vehicle['Total'].values[0]
        fig.update_layout(
            annotations=[{
                'text': f"Total:<br>{format_currency(total)}",
                'x': 0.5, 'y': 0.5,
                'font_size': 14,
                'showarrow': False
            }]
        )
        
        return fig


class SensitivityAnalysisChart(ChartWidget):
    """Tornado chart for sensitivity analysis."""
    
    def __init__(self, height: int = 500):
        super().__init__("Sensitivity Analysis", height)
    
    def create_chart(self, data: Dict[str, Any]) -> Optional[go.Figure]:
        if 'sensitivity_analysis' not in data or not is_valid_dataframe(data['sensitivity_analysis']):
            return None
            
        df = data['sensitivity_analysis']
        
        # Sort by absolute impact
        df['abs_impact'] = df['Impact'].abs()
        df = df.sort_values('abs_impact', ascending=True)
        
        # Create horizontal bar chart
        fig = go.Figure()
        
        # Add bars for positive and negative impacts
        positive_impacts = df[df['Impact'] >= 0]
        negative_impacts = df[df['Impact'] < 0]
        
        fig.add_trace(go.Bar(
            y=positive_impacts['Parameter'],
            x=positive_impacts['Impact'],
            orientation='h',
            name='Increase TCO',
            marker_color='rgba(219, 64, 82, 0.7)',
            hovertemplate="%{y}<br>Impact: +%{x:$,.2f}"
        ))
        
        fig.add_trace(go.Bar(
            y=negative_impacts['Parameter'],
            x=negative_impacts['Impact'],
            orientation='h',
            name='Decrease TCO',
            marker_color='rgba(50, 171, 96, 0.7)',
            hovertemplate="%{y}<br>Impact: %{x:$,.2f}"
        ))
        
        # Add zero line
        fig.add_shape(
            type='line',
            x0=0, y0=-0.5,
            x1=0, y1=len(df) - 0.5,
            line=dict(color='black', width=1, dash='solid')
        )
        
        # Customize layout
        fig.update_layout(
            xaxis_title="Impact on TCO (AUD)",
            barmode='relative',
            legend_title="TCO Impact",
            margin=dict(l=150)  # Add margin for parameter labels
        )
        
        return fig 