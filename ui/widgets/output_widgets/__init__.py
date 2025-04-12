"""
Output widgets for the TCO Model application.

This package provides widgets for displaying TCO calculation results.
"""

from ui.widgets.output_widgets.base import OutputWidget, format_currency, format_value_by_type, is_valid_dataframe, convert_df_to_csv
from ui.widgets.output_widgets.chart_widget import (
    ChartWidget, TCOComparisonChart, TCOPerKmChart, 
    CostBreakdownPieChart, SensitivityAnalysisChart
)
from ui.widgets.output_widgets.table_widget import (
    TableWidget, TCOSummaryTable, TCOBreakdownTable,
    ComparisonTable, SensitivityTable
)
from ui.widgets.output_widgets.summary_widget import (
    SummaryWidget, TCOSummaryMetrics, 
    DetailedBreakdownWidget, KeyFindingsWidget
)
from ui.widgets.output_widgets.sensitivity_widget import (
    SensitivityAnalysisWidget, WhatIfAnalysisWidget
)

__all__ = [
    # Base widgets
    'OutputWidget',
    'format_currency',
    'format_value_by_type',
    'is_valid_dataframe',
    'convert_df_to_csv',
    
    # Chart widgets
    'ChartWidget',
    'TCOComparisonChart',
    'TCOPerKmChart',
    'CostBreakdownPieChart',
    'SensitivityAnalysisChart',
    
    # Table widgets
    'TableWidget',
    'TCOSummaryTable',
    'TCOBreakdownTable',
    'ComparisonTable',
    'SensitivityTable',
    
    # Summary widgets
    'SummaryWidget',
    'TCOSummaryMetrics',
    'DetailedBreakdownWidget',
    'KeyFindingsWidget',
    
    # Sensitivity analysis widgets
    'SensitivityAnalysisWidget',
    'WhatIfAnalysisWidget'
] 