"""
Sidebar input widgets for the TCO Model application.

This module provides widgets that are rendered in the Streamlit sidebar.
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional, List

from ui.widgets.base import BaseWidget

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
        
    def render(self, params: Dict[str, Any]) -> None:
        """
        Render the input section in an expander.
        
        Args:
            params: Current parameters from session state
        """
        with st.sidebar.expander(self.section_title, expanded=self.expanded):
            self.render_content(params)
    
    @abstractmethod
    def render_content(self, params: Dict[str, Any]) -> None:
        """
        Render the content inside the expander.
        
        Args:
            params: Current parameters from session state
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
    
    def render(self, params: Dict[str, Any]) -> None:
        """
        Render the complete sidebar with all sections.
        
        Args:
            params: Current parameters from session state
        """
        st.sidebar.title("Scenario Parameters")
        
        # Render each section
        for section in self.sections:
            section.render(params) 