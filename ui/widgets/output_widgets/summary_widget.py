"""
Summary widgets for displaying key TCO metrics in the application.

This module provides widgets for presenting key findings and metrics
from TCO calculations in a concise format.
"""

import streamlit as st
import pandas as pd
import logging
from typing import Dict, Any, List, Optional, Tuple

from ui.widgets.output_widgets.base import OutputWidget, format_currency

logger = logging.getLogger(__name__)

class SummaryWidget(OutputWidget):
    """Base class for summary output widgets."""
    
    def __init__(self, title: str = "Summary"):
        """
        Initialize a summary widget.
        
        Args:
            title: Widget title to display
        """
        super().__init__(title)


class TCOSummaryMetrics(SummaryWidget):
    """Widget to display key TCO metrics as streamlit metrics."""
    
    def __init__(self):
        super().__init__("TCO Key Metrics")
    
    def render_content(self, params: Dict[str, Any]) -> None:
        """
        Render the key TCO metrics.
        
        Args:
            params: Current calculation results
        """
        if 'tco_summary' not in params or params['tco_summary'] is None or params['tco_summary'].empty:
            st.info("No TCO data available for display.")
            return
            
        # Extract key metrics
        tco_df = params['tco_summary']
        
        # Create columns for metrics
        col1, col2, col3 = st.columns(3)
        
        # Column 1: Total TCO for each vehicle
        with col1:
            st.subheader("Total TCO")
            
            for _, row in tco_df.iterrows():
                vehicle = row['Vehicle']
                total = row['Total']
                st.metric(
                    label=f"{vehicle}",
                    value=format_currency(total)
                )
        
        # Column 2: Cost per km at average distance
        with col2:
            st.subheader("Cost per km")
            
            if 'tco_per_km' in params and not params['tco_per_km'].empty:
                per_km_df = params['tco_per_km']
                # Get the middle distance value
                distances = per_km_df['Distance'].unique()
                mid_dist = distances[len(distances) // 2]
                
                for vehicle in tco_df['Vehicle'].unique():
                    vehicle_km_cost = per_km_df.loc[
                        (per_km_df['Vehicle'] == vehicle) & 
                        (per_km_df['Distance'] == mid_dist), 
                        'TCO_per_km'
                    ].values
                    
                    if len(vehicle_km_cost) > 0:
                        st.metric(
                            label=f"{vehicle} @ {mid_dist:,.0f} km",
                            value=f"${vehicle_km_cost[0]:.2f}/km"
                        )
            else:
                st.info("Cost per km data not available")
        
        # Column 3: Savings or Breakeven
        with col3:
            if len(tco_df) >= 2:
                st.subheader("Potential Savings")
                
                vehicles = tco_df['Vehicle'].tolist()
                costs = tco_df['Total'].tolist()
                
                # Calculate difference
                diff = costs[1] - costs[0]
                diff_formatted = format_currency(abs(diff))
                
                if diff > 0:
                    st.metric(
                        label=f"{vehicles[0]} vs {vehicles[1]}",
                        value=diff_formatted,
                        delta="Savings"
                    )
                else:
                    st.metric(
                        label=f"{vehicles[0]} vs {vehicles[1]}",
                        value=diff_formatted,
                        delta="Additional cost",
                        delta_color="inverse"
                    )
                    
                # Show breakeven distance if available
                if 'breakeven_distance' in params and params['breakeven_distance']:
                    st.metric(
                        label="Breakeven Distance",
                        value=f"{params['breakeven_distance']:,.0f} km"
                    )
            else:
                st.info("Comparison requires at least two vehicles")


class DetailedBreakdownWidget(SummaryWidget):
    """Widget to display detailed cost breakdown with descriptions."""
    
    def __init__(self, vehicle_type: str):
        """
        Initialize a detailed breakdown widget.
        
        Args:
            vehicle_type: Vehicle type to display ("electric" or "diesel")
        """
        super().__init__(f"{vehicle_type.title()} Vehicle Detailed Breakdown")
        self.vehicle_type = vehicle_type
    
    def render_content(self, params: Dict[str, Any]) -> None:
        """
        Render the detailed cost breakdown.
        
        Args:
            params: Current calculation results
        """
        # Get breakdown data for this vehicle type
        if 'tco_breakdown' not in params or params['tco_breakdown'] is None or params['tco_breakdown'].empty:
            st.info("No detailed breakdown data available.")
            return
            
        df = params['tco_breakdown']
        df_vehicle = df[df['Vehicle'] == self.vehicle_type.title()]
        
        if df_vehicle.empty:
            st.info(f"No breakdown data available for {self.vehicle_type.title()} vehicle.")
            return
            
        # Get the cost components (excluding Vehicle and Total)
        components = [col for col in df_vehicle.columns if col not in ['Vehicle', 'Total']]
        
        # Create expanders for each cost component
        for component in components:
            value = df_vehicle[component].values[0]
            with st.expander(f"{component}: {format_currency(value)}"):
                self._render_component_details(component, value, params)
    
    def _render_component_details(self, component: str, value: float, params: Dict[str, Any]) -> None:
        """
        Render detailed information about a cost component.
        
        Args:
            component: The cost component name
            value: The cost component value
            params: Current calculation results
        """
        # Add descriptions based on component type
        if component == "Purchase Price":
            st.write("Initial vehicle purchase cost, before accounting for residual value.")
            
            # Show depreciation info if available
            if f"{self.vehicle_type}_vehicle_residual_value_projections" in params:
                residual_data = params[f"{self.vehicle_type}_vehicle_residual_value_projections"]
                if isinstance(residual_data, pd.DataFrame) and not residual_data.empty:
                    st.caption("Residual Value Schedule:")
                    st.dataframe(residual_data, use_container_width=True)
        
        elif component == "Energy/Fuel":
            if self.vehicle_type == "electric":
                st.write("Total electricity costs over the analysis period.")
                if "electricity_price" in params:
                    st.metric("Electricity Price", f"${params['electricity_price']:.4f}/kWh")
            else:
                st.write("Total diesel fuel costs over the analysis period.")
                if "diesel_price" in params:
                    st.metric("Diesel Price", f"${params['diesel_price']:.2f}/L")
        
        elif component == "Maintenance":
            st.write("Scheduled and unscheduled maintenance costs over the analysis period.")
            if f"{self.vehicle_type}_maintenance_schedule" in params:
                maint_data = params[f"{self.vehicle_type}_maintenance_schedule"]
                if isinstance(maint_data, pd.DataFrame) and not maint_data.empty:
                    st.dataframe(maint_data, use_container_width=True)
        
        elif component == "Infrastructure":
            if self.vehicle_type == "electric":
                st.write("Charging infrastructure costs, including installation and maintenance.")
            else:
                st.write("Fueling infrastructure costs, if any.")
        
        elif component == "Battery Replacement":
            if self.vehicle_type == "electric":
                st.write("Cost of battery replacements, if applicable during the analysis period.")
                if "battery_replacement_year" in params:
                    st.metric("Replacement Year", params["battery_replacement_year"])
            else:
                st.write("Not applicable for diesel vehicles.")
        
        else:
            st.write(f"Total {component.lower()} costs over the analysis period.")
            
        # Display percentage of total
        if 'tco_summary' in params and not params['tco_summary'].empty:
            total = params['tco_summary'].loc[
                params['tco_summary']['Vehicle'] == self.vehicle_type.title(), 
                'Total'
            ].values[0]
            
            if total > 0:
                percentage = (value / total) * 100
                st.metric("Percentage of Total TCO", f"{percentage:.1f}%")


class KeyFindingsWidget(SummaryWidget):
    """Widget to display key findings and insights."""
    
    def __init__(self):
        super().__init__("Key Findings")
    
    def render_content(self, params: Dict[str, Any]) -> None:
        """
        Render the key findings about the TCO analysis.
        
        Args:
            params: Current calculation results
        """
        if 'tco_summary' not in params or params['tco_summary'] is None or params['tco_summary'].empty:
            st.info("No TCO data available to generate findings.")
            return
            
        # Extract data
        tco_df = params['tco_summary']
        
        if len(tco_df) < 2:
            st.info("Comparison requires at least two vehicles to generate findings.")
            return
            
        # Get vehicle costs
        vehicles = tco_df['Vehicle'].tolist()
        costs = tco_df['Total'].tolist()
        
        # Create columns for findings
        col1, col2 = st.columns(2)
        
        with col1:
            # Overall conclusion
            st.subheader("Overall Cost Comparison")
            
            diff = costs[1] - costs[0]
            if diff > 0:
                st.success(f"The {vehicles[0]} has a lower TCO by {format_currency(abs(diff))}.")
            elif diff < 0:
                st.error(f"The {vehicles[1]} has a lower TCO by {format_currency(abs(diff))}.")
            else:
                st.info("Both vehicles have the same total cost of ownership.")
                
            # Breakeven analysis
            if 'breakeven_distance' in params and params['breakeven_distance']:
                breakeven = params['breakeven_distance']
                annual_distance = params.get('annual_distance', 0)
                
                if annual_distance > 0:
                    years_to_breakeven = breakeven / annual_distance
                    
                    st.subheader("Breakeven Analysis")
                    if years_to_breakeven <= params.get('analysis_period', float('inf')):
                        st.info(f"Breakeven occurs at {breakeven:,.0f} km (approximately {years_to_breakeven:.1f} years).")
                    else:
                        st.warning(f"Breakeven does not occur within the analysis period.")
        
        with col2:
            # Cost component insights
            st.subheader("Component Insights")
            
            # Get cost components (excluding Vehicle and Total)
            components = [col for col in tco_df.columns if col not in ['Vehicle', 'Total']]
            
            # Find biggest cost difference
            component_diffs = []
            for component in components:
                component_diff = tco_df.iloc[1][component] - tco_df.iloc[0][component]
                component_diffs.append((component, component_diff))
            
            # Sort by absolute difference
            component_diffs.sort(key=lambda x: abs(x[1]), reverse=True)
            
            # Show biggest difference
            if component_diffs:
                biggest_component, biggest_diff = component_diffs[0]
                
                if biggest_diff > 0:
                    st.info(f"The largest cost difference is in **{biggest_component}**, where {vehicles[0]} saves {format_currency(abs(biggest_diff))}.")
                elif biggest_diff < 0:
                    st.info(f"The largest cost difference is in **{biggest_component}**, where {vehicles[1]} saves {format_currency(abs(biggest_diff))}.")
            
            # Sensitivity insights
            if 'sensitivity_analysis' in params and not params['sensitivity_analysis'].empty:
                st.subheader("Sensitivity Insights")
                
                sensitivity_df = params['sensitivity_analysis']
                if not sensitivity_df.empty:
                    most_sensitive = sensitivity_df.iloc[0]
                    st.info(f"The TCO model is most sensitive to changes in **{most_sensitive['Parameter']}**.") 