"""
Output management for the TCO Model application.

This module provides a facade for the output widgets, simplifying the main application code.
"""

import streamlit as st
import logging
from typing import Dict, Any, List, Optional, TypedDict

from ui.layouts.tab_layout import TabLayoutManager
from ui.layouts.side_by_side_layout import SideBySideLayoutManager, ComparisonLayoutManager

from ui.widgets.output_widgets.chart_widget import (
    TCOComparisonChart, TCOPerKmChart, CostBreakdownPieChart
)
from ui.widgets.output_widgets.table_widget import (
    TCOSummaryTable, TCOBreakdownTable, ComparisonTable
)
from ui.widgets.output_widgets.summary_widget import (
    TCOSummaryMetrics, DetailedBreakdownWidget, KeyFindingsWidget
)
from ui.widgets.output_widgets.sensitivity_widget import (
    SensitivityAnalysisWidget, WhatIfAnalysisWidget
)

logger = logging.getLogger(__name__)

# Define a placeholder type for TCO results. Ideally, this would be a Pydantic model
# or a more specific TypedDict matching the actual structure from the model calculation.
TcoResults = Dict[str, Any]

class OutputDashboard:
    """Manages the display of TCO calculation results."""
    
    def __init__(self):
        """Initialize the output dashboard."""
        # Initialize tab_layout to None and assert its type after initialization
        self.tab_layout: Optional[TabLayoutManager] = None
        self.initialize_layouts()
    
    def initialize_layouts(self) -> None:
        """Initialize the tab layout and widgets for the dashboard."""
        # TODO: Define a BaseWidget protocol/interface that all widgets implement
        # WidgetList = List[BaseWidget]

        self.tab_layout = TabLayoutManager("TCO Analysis Results")
        
        # Tab 1: Overview
        # Assuming widgets conform to a common interface
        overview_widgets: List[Any] = [
            TCOSummaryMetrics(),
            TCOComparisonChart(),
            KeyFindingsWidget()
        ]
        self.tab_layout.add_tab("Overview", overview_widgets)
        
        # Tab 2: Cost Breakdown
        breakdown_layout = SideBySideLayoutManager()
        breakdown_layout.set_column_title(0, "Electric Vehicle")
        breakdown_layout.set_column_title(1, "Diesel Vehicle")
        
        # Assuming widgets conform to a common interface
        breakdown_layout.add_widget_to_column(0, CostBreakdownPieChart("electric"))
        breakdown_layout.add_widget_to_column(0, DetailedBreakdownWidget("electric"))
        breakdown_layout.add_widget_to_column(1, CostBreakdownPieChart("diesel"))
        breakdown_layout.add_widget_to_column(1, DetailedBreakdownWidget("diesel"))
        
        # Add the layout manager itself as a widget to the tab
        self.tab_layout.add_tab("Cost Breakdown", [breakdown_layout])
        
        # Tab 3: Detailed Analysis
        # Assuming widgets conform to a common interface
        detailed_widgets: List[Any] = [
            TCOPerKmChart(),
            TCOSummaryTable(),
            TCOBreakdownTable("electric"), # Assuming constructor takes vehicle type
            TCOBreakdownTable("diesel")
        ]
        self.tab_layout.add_tab("Detailed Analysis", detailed_widgets)
        
        # Tab 4: Sensitivity Analysis
        # Assuming widgets conform to a common interface
        sensitivity_widgets: List[Any] = [
            SensitivityAnalysisWidget(),
            WhatIfAnalysisWidget()
        ]
        self.tab_layout.add_tab("Sensitivity", sensitivity_widgets)
    
    def render(self, results: Optional[TcoResults]) -> None:
        """
        Render the output dashboard.
        
        Args:
            results: TCO calculation results dictionary to display, or None.
        """
        if results is None:
            st.info("Run the TCO calculation to see results.")
            return

        if not isinstance(results, dict):
            st.error("Invalid TCO calculation results format received.")
            logger.error(f"Received invalid results format: {type(results)}")
            return

        # Check for calculation errors first
        if errors := results.get('errors'):
            st.error(f"TCO calculation failed: {'; '.join(errors)}")
            return

        # Basic check for essential results structure needed for rendering
        vehicles_data = results.get('vehicles')
        if not isinstance(vehicles_data, dict) or \
           'electric' not in vehicles_data or 'diesel' not in vehicles_data or \
           not isinstance(vehicles_data['electric'], dict) or \
           not isinstance(vehicles_data['diesel'], dict) or \
           vehicles_data['electric'].get('total_discounted_tco') is None or \
           vehicles_data['diesel'].get('total_discounted_tco') is None:
            st.warning("TCO results are incomplete or in an unexpected format. Cannot display dashboard.")
            logger.warning(f"Incomplete TCO results received: {results}")
            return

        # Ensure tab_layout was initialized
        if self.tab_layout is None:
             st.error("Output dashboard layout was not initialized correctly.")
             logger.error("OutputDashboard render called before initialize_layouts completed.")
             return

        # Render the dashboard using the results dictionary
        self.tab_layout.render(results)


def create_output_dashboard(results: Optional[TcoResults]) -> None:
    """
    Create and render the output dashboard.
    
    This function is the main entry point for displaying TCO results in the UI.
    
    Args:
        results: TCO calculation results dictionary to display, or None.
    """
    dashboard = OutputDashboard()
    dashboard.render(results) 