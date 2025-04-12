"""
Sidebar input widgets for the TCO Model application.

This module provides widgets that are rendered in the Streamlit sidebar.
"""

import streamlit as st
import logging
from typing import Any, Optional, List
from abc import abstractmethod

from ui.widgets.base import BaseWidget
from tco_model.scenarios import Scenario

logger = logging.getLogger(__name__)

class SidebarWidget(BaseWidget):
    """Base class for sidebar input sections."""
    
    def __init__(self, section_title: str, expanded: bool = False, key_prefix: str = ""):
        """
        Initialize a sidebar section widget.
        
        Args:
            section_title: Title of the section
            expanded: Whether the section is expanded by default
            key_prefix: Optional prefix for session state keys
        """
        super().__init__(key_prefix)
        self.section_title = section_title
        self.expanded = expanded
        
    def render(self, scenario: Scenario) -> None:
        """
        Render the input section in an expander.
        
        Args:
            scenario: The current Scenario object from session state
        """
        with st.sidebar.expander(self.section_title, expanded=self.expanded):
            self.render_content(scenario)
    
    @abstractmethod
    def render_content(self, scenario: Scenario) -> None:
        """
        Render the content inside the expander.
        
        Args:
            scenario: The current Scenario object from session state
        """
        pass


class SidebarManager(BaseWidget):
    """Manager widget that assembles all sidebar sections."""
    
    def __init__(self, sections: List[SidebarWidget]):
        """
        Initialize with a list of sidebar section widgets.
        
        Args:
            sections: List of sidebar widgets to render
        """
        super().__init__()
        self.sections = sections
    
    def render(self, scenario: Scenario) -> None:
        """
        Render the complete sidebar with all sections.
        
        Args:
            scenario: The current Scenario object from session state
        """
        st.sidebar.title("Scenario Parameters")
        
        # Render each section
        for section in self.sections:
            section.render(scenario) 