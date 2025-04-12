"""
Vehicle input widgets for the TCO Model application.

This module provides widgets for vehicle parameters.
"""

import streamlit as st
import logging
from typing import Dict, Any
from abc import abstractmethod

from ui.widgets.input_widgets.sidebar import SidebarWidget

logger = logging.getLogger(__name__)

class VehicleInputWidget(SidebarWidget):
    """Base widget for vehicle parameters."""
    
    def __init__(self, vehicle_type: str, expanded: bool = True):
        """
        Initialize a vehicle input widget.
        
        Args:
            vehicle_type: Type of vehicle (e.g., "electric" or "diesel")
            expanded: Whether the section is expanded by default
        """
        super().__init__(f"{vehicle_type.title()} Vehicle", expanded)
        self.vehicle_type = vehicle_type
        self.prefix = f"{vehicle_type}_vehicle_"
        
    def render_content(self, params: Dict[str, Any]) -> None:
        st.text_input(
            f"{self.vehicle_type.title()} Name/Model", 
            key=f"{self.prefix}name", 
            value=params[f"{self.prefix}name"]
        )
        
        st.number_input(
            f"{self.vehicle_type.title()} Purchase Price (AUD)", 
            min_value=0.0, 
            step=1000.0, 
            format="%.0f", 
            key=f"{self.prefix}price", 
            value=params[f"{self.prefix}price"]
        )
        
        # Render vehicle-specific parameters
        self.render_vehicle_specific(params)
        
        # Show residual value info if available in parameters
        if f"{self.prefix}residual_value_projections" in params:
            st.caption(f"{self.vehicle_type.title()} Residual Value: Loaded from scenario")
    
    @abstractmethod
    def render_vehicle_specific(self, params: Dict[str, Any]) -> None:
        """
        Render parameters specific to this vehicle type.
        
        Args:
            params: Current parameters from session state
        """
        pass


class ElectricVehicleInputWidget(VehicleInputWidget):
    """Widget for electric vehicle parameters."""
    
    def __init__(self, expanded: bool = True):
        super().__init__("electric", expanded)
        
    def render_vehicle_specific(self, params: Dict[str, Any]) -> None:
        st.number_input(
            "EV Battery Capacity (kWh)", 
            min_value=0.0, 
            step=1.0, 
            format="%.1f", 
            key=f"{self.prefix}battery_capacity", 
            help="Total energy storage capacity of the electric vehicle's battery.",
            value=params[f"{self.prefix}battery_capacity"]
        )
        
        st.number_input(
            "EV Energy Consumption (kWh/km)", 
            min_value=0.0, 
            step=0.01, 
            format="%.2f", 
            key=f"{self.prefix}energy_consumption", 
            help="Average electrical energy used per kilometer traveled.",
            value=params[f"{self.prefix}energy_consumption"]
        )
        
        st.number_input(
            "EV Battery Warranty (years)", 
            min_value=0, 
            step=1, 
            key=f"{self.prefix}battery_warranty", 
            value=params[f"{self.prefix}battery_warranty"]
        )


class DieselVehicleInputWidget(VehicleInputWidget):
    """Widget for diesel vehicle parameters."""
    
    def __init__(self, expanded: bool = True):
        super().__init__("diesel", expanded)
        
    def render_vehicle_specific(self, params: Dict[str, Any]) -> None:
        st.number_input(
            "Diesel Fuel Consumption (L/100km)", 
            min_value=0.0, 
            step=0.1, 
            format="%.1f", 
            key=f"{self.prefix}fuel_consumption", 
            value=params[f"{self.prefix}fuel_consumption"]
        ) 