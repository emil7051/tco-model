"""
Output management for the TCO Model application.

This module provides a facade for the output widgets, simplifying the main application code.
"""

import streamlit as st
import logging
from typing import Dict, Any, List, Optional

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

class OutputDashboard:
    """Manages the display of TCO calculation results."""
    
    def __init__(self):
        """Initialize the output dashboard."""
        self.tab_layout = None
        self.initialize_layouts()
    
    def initialize_layouts(self) -> None:
        """Initialize the tab layout and widgets for the dashboard."""
        self.tab_layout = TabLayoutManager("TCO Analysis Results")
        
        # Tab 1: Overview
        overview_widgets = [
            TCOSummaryMetrics(),
            TCOComparisonChart(),
            KeyFindingsWidget()
        ]
        self.tab_layout.add_tab("Overview", overview_widgets)
        
        # Tab 2: Cost Breakdown
        breakdown_layout = SideBySideLayoutManager()
        breakdown_layout.set_column_title(0, "Electric Vehicle")
        breakdown_layout.set_column_title(1, "Diesel Vehicle")
        
        breakdown_layout.add_widget_to_column(0, CostBreakdownPieChart("electric"))
        breakdown_layout.add_widget_to_column(0, DetailedBreakdownWidget("electric"))
        breakdown_layout.add_widget_to_column(1, CostBreakdownPieChart("diesel"))
        breakdown_layout.add_widget_to_column(1, DetailedBreakdownWidget("diesel"))
        
        self.tab_layout.add_tab("Cost Breakdown", [breakdown_layout])
        
        # Tab 3: Detailed Analysis
        detailed_widgets = [
            TCOPerKmChart(),
            TCOSummaryTable(),
            TCOBreakdownTable("electric"),
            TCOBreakdownTable("diesel")
        ]
        self.tab_layout.add_tab("Detailed Analysis", detailed_widgets)
        
        # Tab 4: Sensitivity Analysis
        sensitivity_widgets = [
            SensitivityAnalysisWidget(),
            WhatIfAnalysisWidget()
        ]
        self.tab_layout.add_tab("Sensitivity", sensitivity_widgets)
    
    def render(self, params: Dict[str, Any]) -> None:
        """
        Render the output dashboard.
        
        Args:
            params: TCO calculation results to display
        """
        if params is None or not isinstance(params, dict):
            st.error("No valid TCO calculation results available for display.")
            return
        
        # Check if we have TCO results in the params
        if 'tco_summary' not in params or params['tco_summary'] is None or params['tco_summary'].empty:
            st.warning("Run the TCO calculation first to see results.")
            return
        
        # Render the dashboard
        self.tab_layout.render(params)


def create_output_dashboard(params: Dict[str, Any]) -> None:
    """
    Create and render the output dashboard.
    
    This function is the main entry point for displaying TCO results in the UI.
    
    Args:
        params: TCO calculation results to display
    """
    dashboard = OutputDashboard()
    dashboard.render(params) 