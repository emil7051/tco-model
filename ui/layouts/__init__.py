"""
Layout managers for the TCO Model application.

This package provides layout managers for organizing widgets in the UI.
"""

from ui.layouts.tab_layout import TabLayoutManager, AccordionLayoutManager
from ui.layouts.side_by_side_layout import SideBySideLayoutManager, ComparisonLayoutManager

__all__ = [
    'TabLayoutManager',
    'AccordionLayoutManager',
    'SideBySideLayoutManager', 
    'ComparisonLayoutManager',
] 