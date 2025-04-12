"""
Input management for the TCO Model application.

This module provides a facade for the input widgets, simplifying the main application code.
"""

import streamlit as st
import logging
from typing import Dict, Any, List

# Assuming these widgets might share a common base class or protocol (e.g., BaseWidget)
# For now, we use Any, but defining a protocol would be better.
from ui.widgets.input_widgets.sidebar import SidebarManager
from ui.widgets.input_widgets.general import GeneralInputWidget, EconomicInputWidget, OperationalInputWidget
from ui.widgets.input_widgets.vehicle_inputs import ElectricVehicleInputWidget, DieselVehicleInputWidget
from ui.widgets.input_widgets.cost_inputs import (
    InfrastructureInputWidget, OtherCostsInputWidget,
    EnergyPricingInputWidget, BatteryReplacementInputWidget
)
# Import the Scenario type
from tco_model.scenarios import Scenario

logger = logging.getLogger(__name__)

# Placeholder for a potential base widget class/protocol
BaseWidget = Any

def create_input_sidebar() -> None:
    """
    Creates and renders the sidebar UI for inputting TCO scenario parameters.
    
    This function creates all the necessary widgets and renders them within 
    the Streamlit sidebar inside a form.
    Requires 'scenario' to be present in st.session_state.
    """
    # Ensure scenario object exists in session state
    if 'scenario' not in st.session_state:
        st.sidebar.error("Scenario object not initialized. Please ensure state is initialized.")
        logger.error("create_input_sidebar called but 'scenario' not in session state.")
        st.stop() # Stop execution if state isn't initialized

    # Type hint the scenario object retrieved from session state
    current_scenario: Scenario = st.session_state['scenario']

    with st.sidebar.form(key="scenario_form"):
        # Create all input section widgets
        # Type hint the list of widgets
        sections: List[BaseWidget] = [
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
        
        # Create and render the sidebar manager, passing the Scenario object
        sidebar = SidebarManager(sections)
        # Pass the scenario object directly
        sidebar.render(current_scenario) 
        
        # Add submit button for the form
        # The submit button's action implicitly updates the form's state,
        # which should be handled by the widgets' render methods if they modify the scenario.
        st.form_submit_button("Update Scenario & Recalculate") 