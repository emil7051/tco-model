"""
Base classes for UI widgets in the TCO Model application.

This module provides base classes that define the common interface
and behavior for all UI widgets in the application.
"""

from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class BaseWidget(ABC):
    """Base class for all UI widgets."""
    
    def __init__(self, key_prefix: str = ""):
        """
        Initialize the widget.
        
        Args:
            key_prefix: Optional prefix for session state keys to avoid collisions
        """
        self.key_prefix = key_prefix
        
    def get_key(self, key: str) -> str:
        """
        Get a unique session state key for this widget.
        
        Args:
            key: Base key name
            
        Returns:
            Prefixed key name
        """
        return f"{self.key_prefix}_{key}" if self.key_prefix else key
    
    @abstractmethod
    def render(self, params: Dict[str, Any]) -> None:
        """
        Render the widget in the Streamlit UI.
        
        Args:
            params: Current parameters from session state
        """
        pass 