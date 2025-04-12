"""
Side-by-side layout manager for the TCO Model application.

This module provides a layout manager for displaying content in adjacent columns.
"""

import streamlit as st
import logging
from typing import Dict, Any, List, Optional, Tuple, Union

from ui.widgets.base import BaseWidget

logger = logging.getLogger(__name__)

class SideBySideLayoutManager:
    """
    Layout manager for organizing widgets into side-by-side columns.
    
    This class provides a way to arrange widgets in adjacent columns
    for visual comparison.
    """
    
    def __init__(self, title: Optional[str] = None, num_columns: int = 2):
        """
        Initialize a side-by-side layout manager.
        
        Args:
            title: Optional title to display above the columns
            num_columns: Number of columns to create (default: 2)
        """
        self.title = title
        self.num_columns = max(1, min(num_columns, 8))  # Limit to 1-8 columns
        self.columns: List[List[BaseWidget]] = [[] for _ in range(self.num_columns)]
        self.column_titles: List[Optional[str]] = [None for _ in range(self.num_columns)]
    
    def add_widget_to_column(self, column_index: int, widget: BaseWidget) -> None:
        """
        Add a widget to a specific column.
        
        Args:
            column_index: The index of the column (0-based)
            widget: Widget to add to the column
        
        Raises:
            IndexError: If column_index is out of range
        """
        if 0 <= column_index < self.num_columns:
            self.columns[column_index].append(widget)
        else:
            raise IndexError(f"Column index {column_index} is out of range (0-{self.num_columns-1})")
    
    def set_column_title(self, column_index: int, title: str) -> None:
        """
        Set the title for a specific column.
        
        Args:
            column_index: The index of the column (0-based)
            title: Title for the column
        
        Raises:
            IndexError: If column_index is out of range
        """
        if 0 <= column_index < self.num_columns:
            self.column_titles[column_index] = title
        else:
            raise IndexError(f"Column index {column_index} is out of range (0-{self.num_columns-1})")
    
    def render(self, params: Dict[str, Any]) -> None:
        """
        Render the side-by-side layout.
        
        Args:
            params: Parameters to pass to each widget's render method
        """
        if self.title:
            st.header(self.title)
        
        # Create columns (always with equal width now)
        cols = st.columns(self.num_columns)
        
        # Render widgets in each column
        for i, column_widgets in enumerate(self.columns):
            with cols[i]:
                # Display column title if set
                if self.column_titles[i]:
                    st.subheader(self.column_titles[i])
                
                # Render each widget in the column
                for widget in column_widgets:
                    widget.render(params)


class ComparisonLayoutManager(SideBySideLayoutManager):
    """
    Layout manager for comparing two scenarios side by side.
    
    This specialized side-by-side layout is designed for comparing
    two alternative scenarios with labeled columns.
    """
    
    def __init__(self, title: str = "Comparison", left_title: str = "Scenario A", right_title: str = "Scenario B"):
        """
        Initialize a comparison layout manager.
        
        Args:
            title: Title to display above the comparison
            left_title: Title for the left column
            right_title: Title for the right column
        """
        super().__init__(title, num_columns=2)
        self.set_column_title(0, left_title)
        self.set_column_title(1, right_title)
    
    def add_to_left(self, widget: BaseWidget) -> None:
        """
        Add a widget to the left column.
        
        Args:
            widget: Widget to add
        """
        self.add_widget_to_column(0, widget)
    
    def add_to_right(self, widget: BaseWidget) -> None:
        """
        Add a widget to the right column.
        
        Args:
            widget: Widget to add
        """
        self.add_widget_to_column(1, widget)
    
    def add_to_both(self, left_widget: BaseWidget, right_widget: BaseWidget) -> None:
        """
        Add widgets to both columns in the same row.
        
        Args:
            left_widget: Widget to add to the left column
            right_widget: Widget to add to the right column
        """
        self.add_to_left(left_widget)
        self.add_to_right(right_widget) 