"""
Input management for the TCO Model application.

This module provides a facade for the input widgets, simplifying the main application code.
"""

import streamlit as st
import logging
from typing import Dict, Any, List

from ui.widgets.input_widgets.sidebar import SidebarManager
from ui.widgets.input_widgets.general import GeneralInputWidget, EconomicInputWidget, OperationalInputWidget
from ui.widgets.input_widgets.vehicle_inputs import ElectricVehicleInputWidget, DieselVehicleInputWidget
from ui.widgets.input_widgets.cost_inputs import (
    InfrastructureInputWidget, OtherCostsInputWidget,
    EnergyPricingInputWidget, BatteryReplacementInputWidget
)

logger = logging.getLogger(__name__)

def create_input_sidebar():
    """
    Creates and renders the sidebar UI for inputting TCO scenario parameters.
    
    This function creates all the necessary widgets and renders them within 
    the Streamlit sidebar inside a form.
    """
    # Ensure scenario_params exists in session state
    if 'scenario_params' not in st.session_state:
        st.sidebar.error("Scenario parameters not initialized. Please run the app main script.")
        st.stop() # Stop execution if state isn't initialized

    with st.sidebar.form(key="scenario_form"):
        # Create all input section widgets
        sections = [
            GeneralInputWidget(expanded=True),
            EconomicInputWidget(expanded=False),
            OperationalInputWidget(expanded=True),
            ElectricVehicleInputWidget(expanded=True),
            DieselVehicleInputWidget(expanded=True),
            InfrastructureInputWidget(expanded=False),
            OtherCostsInputWidget(expanded=False),
            EnergyPricingInputWidget(expanded=False),
            BatteryReplacementInputWidget(expanded=False)
        ]
        
        # Create and render the sidebar manager
        sidebar = SidebarManager(sections)
        sidebar.render(st.session_state['scenario_params']) 
        
        # Add submit button for the form
        st.form_submit_button("Update Scenario") 