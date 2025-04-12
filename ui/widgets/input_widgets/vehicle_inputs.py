"""
Vehicle input widgets for the TCO Model application.

This module provides widgets for vehicle parameters.
"""

import streamlit as st
import logging
from typing import Any
from abc import abstractmethod

from ui.widgets.input_widgets.sidebar import SidebarWidget
from tco_model.scenarios import Scenario

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
        self.key_prefix = f"scenario.{self.vehicle_type}_vehicle."
        
    def render_content(self, scenario: Scenario) -> None:
        vehicle = getattr(scenario, f"{self.vehicle_type}_vehicle", None)
        if not vehicle:
            st.warning(f"Could not find {self.vehicle_type} vehicle data in scenario object.")
            return
            
        st.text_input(
            f"{self.vehicle_type.title()} Name/Model",
            key=f"{self.key_prefix}name"
        )
        
        st.number_input(
            f"{self.vehicle_type.title()} Purchase Price (AUD)",
            min_value=0.0,
            step=1000.0,
            format="%.0f",
            key=f"{self.key_prefix}base_purchase_price_aud"
        )
        
        self.render_vehicle_specific(scenario)
        
        res_val_data = vehicle.residual_value_percent_projections
        if isinstance(res_val_data, dict) and res_val_data:
             st.caption(f"{self.vehicle_type.title()} Residual Value (%): Loaded from scenario ({len(res_val_data)} points)")
        elif res_val_data is None:
             st.caption(f"{self.vehicle_type.title()} Residual Value (%): Not set in scenario")
        else:
             st.caption(f"{self.vehicle_type.title()} Residual Value (%): Invalid data format in scenario")
    
    @abstractmethod
    def render_vehicle_specific(self, scenario: Scenario) -> None:
        """
        Render parameters specific to this vehicle type.
        
        Args:
            scenario: The current Scenario object from session state
        """
        pass


class ElectricVehicleInputWidget(VehicleInputWidget):
    """Widget for electric vehicle parameters."""
    
    def __init__(self, expanded: bool = True):
        super().__init__("electric", expanded)
        
    def render_vehicle_specific(self, scenario: Scenario) -> None:
        st.number_input(
            "EV Battery Capacity (kWh)",
            min_value=0.0,
            step=1.0,
            format="%.1f",
            key=f"{self.key_prefix}battery_capacity_kwh",
            help="Total energy storage capacity of the electric vehicle's battery."
        )
        
        st.number_input(
            "EV Energy Consumption (kWh/km)",
            min_value=0.0,
            step=0.01,
            format="%.2f",
            key=f"{self.key_prefix}energy_consumption_kwh_per_km",
            help="Average electrical energy used per kilometer traveled."
        )
        
        st.number_input(
            "EV Battery Warranty (years)",
            min_value=0,
            step=1,
            key=f"{self.key_prefix}battery_warranty_years"
        )


class DieselVehicleInputWidget(VehicleInputWidget):
    """Widget for diesel vehicle parameters."""
    
    def __init__(self, expanded: bool = True):
        super().__init__("diesel", expanded)
        
    def render_vehicle_specific(self, scenario: Scenario) -> None:
        st.number_input(
            "Diesel Fuel Consumption (L/100km)",
            min_value=0.0,
            step=0.1,
            format="%.1f",
            key=f"{self.key_prefix}fuel_consumption_l_per_100km"
        ) 