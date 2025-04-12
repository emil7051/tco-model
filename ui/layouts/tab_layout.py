"""
Tab-based layout manager for the TCO Model application.

This module provides a layout manager for organizing content into tabs.
"""

import streamlit as st
import logging
from typing import Dict, Any, List, Optional, Callable, Union, Tuple

from ui.widgets.base import BaseWidget

logger = logging.getLogger(__name__)

class TabLayoutManager:
    """
    Layout manager for organizing widgets into tabbed interfaces.
    
    This class provides a simple way to organize multiple widgets
    into a tabbed interface within Streamlit.
    """
    
    def __init__(self, title: Optional[str] = None):
        """
        Initialize a tab layout manager.
        
        Args:
            title: Optional title to display above the tabs
        """
        self.title = title
        self.tabs: List[Tuple[str, List[BaseWidget]]] = []
    
    def add_tab(self, label: str, widgets: List[BaseWidget]) -> None:
        """
        Add a new tab with a list of widgets.
        
        Args:
            label: The label for the tab
            widgets: List of widgets to include in the tab
        """
        self.tabs.append((label, widgets))
    
    def render(self, params: Dict[str, Any]) -> None:
        """
        Render the tabbed interface.
        
        Args:
            params: Parameters to pass to each widget's render method
        """
        if self.title:
            st.header(self.title)
        
        if not self.tabs:
            st.info("No tabs have been added to this layout.")
            return
        
        # Create tab objects
        tab_objects = st.tabs([tab[0] for tab in self.tabs])
        
        # Render widgets in each tab
        for i, (_, widgets) in enumerate(self.tabs):
            with tab_objects[i]:
                for widget in widgets:
                    widget.render(params)


class AccordionLayoutManager:
    """
    Layout manager for organizing widgets into collapsible sections.
    
    This class provides a way to organize multiple widgets into
    expandable/collapsible sections within Streamlit.
    """
    
    def __init__(self, title: Optional[str] = None):
        """
        Initialize an accordion layout manager.
        
        Args:
            title: Optional title to display above the accordion
        """
        self.title = title
        self.sections: List[Tuple[str, List[BaseWidget], bool]] = []
    
    def add_section(self, label: str, widgets: List[BaseWidget], expanded: bool = False) -> None:
        """
        Add a new section with a list of widgets.
        
        Args:
            label: The label for the section
            widgets: List of widgets to include in the section
            expanded: Whether the section should be expanded by default
        """
        self.sections.append((label, widgets, expanded))
    
    def render(self, params: Dict[str, Any]) -> None:
        """
        Render the accordion interface.
        
        Args:
            params: Parameters to pass to each widget's render method
        """
        if self.title:
            st.header(self.title)
        
        if not self.sections:
            st.info("No sections have been added to this layout.")
            return
        
        # Render each section as an expander
        for label, widgets, expanded in self.sections:
            with st.expander(label, expanded=expanded):
                for widget in widgets:
                    widget.render(params) 