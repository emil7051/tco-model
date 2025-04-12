"""
Cost input widgets for the TCO Model application.

This module provides widgets for cost and infrastructure parameters.
"""

import streamlit as st
import logging
from typing import Dict, Any, List

from ui.widgets.input_widgets.sidebar import SidebarWidget

logger = logging.getLogger(__name__)

class InfrastructureInputWidget(SidebarWidget):
    """Widget for infrastructure parameters."""
    
    def __init__(self, expanded: bool = False):
        super().__init__("Infrastructure (EV)", expanded)
        
    def render_content(self, params: Dict[str, Any]) -> None:
        st.number_input(
            "Charger Hardware Cost (AUD)", 
            min_value=0.0, 
            step=100.0, 
            format="%.0f", 
            key="charger_cost", 
            value=float(params['charger_cost'])
        )
        
        st.number_input(
            "Charger Installation Cost (AUD)", 
            min_value=0.0, 
            step=100.0, 
            format="%.0f", 
            key="charger_installation_cost", 
            value=float(params['charger_installation_cost'])
        )
        
        st.number_input(
            "Charger Lifespan (years)", 
            min_value=1, 
            step=1, 
            key="charger_lifespan", 
            help="Expected operational life of the charger hardware before needing replacement.",
            value=params['charger_lifespan']
        )
        
        st.number_input(
            "Charger Maintenance (% of Capital)", 
            min_value=0.0, 
            max_value=10.0, 
            step=0.1, 
            format="%.1f", 
            key="charger_maintenance_percent", 
            help="Annual maintenance cost as % of hardware + install cost (0-10%).",
            value=params['charger_maintenance_percent']
        )


class OtherCostsInputWidget(SidebarWidget):
    """Widget for maintenance and other costs."""
    
    def __init__(self, expanded: bool = False):
        super().__init__("Maintenance & Other Costs", expanded)
        
    def render_content(self, params: Dict[str, Any]) -> None:
        st.caption("Maintenance: Loaded from scenario (based on vehicle type)")
        st.caption("Insurance: Loaded from scenario (based on vehicle type)")
        
        st.number_input(
            "Annual Registration Cost (AUD)", 
            min_value=0.0, 
            step=100.0, 
            format="%.0f", 
            key="annual_registration_cost", 
            value=params['annual_registration_cost']
        )
        
        st.number_input(
            "Carbon Tax Rate (AUD/tonne CO2e)", 
            min_value=0.0, 
            step=1.0, 
            format="%.2f", 
            key="carbon_tax_rate", 
            help="Tax applied per tonne of Carbon Dioxide Equivalent (CO2e) emissions.",
            value=params['carbon_tax_rate']
        )
        
        st.number_input(
            "Road User Charge (AUD/km)", 
            min_value=0.0, 
            step=0.01, 
            format="%.2f", 
            key="road_user_charge", 
            help="Charge applied per kilometer traveled, potentially replacing registration or fuel excise.",
            value=params['road_user_charge']
        )
        
        # Add inputs for the general increase rates
        st.number_input(
            "Maintenance Cost Increase Rate (%/yr)", 
            min_value=0.0, 
            step=0.1, 
            format="%.1f", 
            key="maintenance_increase_rate", 
            help="Annual real increase for maintenance.",
            value=params['maintenance_increase_rate'] * 100
        )
        
        st.number_input(
            "Insurance Cost Increase Rate (%/yr)", 
            min_value=0.0, 
            step=0.1, 
            format="%.1f", 
            key="insurance_increase_rate", 
            help="Annual real increase for insurance.",
            value=params['insurance_increase_rate'] * 100
        )
        
        st.number_input(
            "Registration Cost Increase Rate (%/yr)", 
            min_value=0.0, 
            step=0.1, 
            format="%.1f", 
            key="registration_increase_rate", 
            help="Annual real increase for registration.",
            value=params['registration_increase_rate'] * 100
        )
        
        st.number_input(
            "Carbon Tax Increase Rate (%/yr)", 
            min_value=0.0, 
            step=0.1, 
            format="%.1f", 
            key="carbon_tax_increase_rate", 
            help="Annual real increase for carbon tax.",
            value=params['carbon_tax_increase_rate'] * 100
        )
        
        st.number_input(
            "Road User Charge Increase Rate (%/yr)", 
            min_value=0.0, 
            step=0.1, 
            format="%.1f", 
            key="road_user_charge_increase_rate", 
            help="Annual real increase for RUC.",
            value=params['road_user_charge_increase_rate'] * 100
        )


class EnergyPricingInputWidget(SidebarWidget):
    """Widget for energy pricing parameters."""
    
    def __init__(self, expanded: bool = False):
        super().__init__("Energy Pricing", expanded)
        
    def render_content(self, params: Dict[str, Any]) -> None:
        # Electricity Scenario Selection
        elec_scenarios = list(params['electricity_price_projections'].keys())
        selected_elec = params['selected_electricity_scenario']
        elec_index = elec_scenarios.index(selected_elec) if selected_elec in elec_scenarios else 0
        
        if elec_scenarios:
            st.selectbox(
                "Electricity Price Scenario", 
                options=elec_scenarios, 
                key="selected_electricity_scenario", 
                index=elec_index
            )
        else:
            st.warning("No electricity price projections found in scenario.")
        
        # Diesel Scenario Selection
        diesel_scenarios = list(params['diesel_price_scenarios'].keys())
        selected_diesel = params['selected_diesel_scenario']
        diesel_index = diesel_scenarios.index(selected_diesel) if selected_diesel in diesel_scenarios else 0
        
        if diesel_scenarios:
            st.selectbox(
                "Diesel Price Scenario", 
                options=diesel_scenarios, 
                key="selected_diesel_scenario", 
                index=diesel_index
            )
        else:
            st.warning("No diesel price scenarios found in scenario.")


class BatteryReplacementInputWidget(SidebarWidget):
    """Widget for battery replacement parameters."""
    
    def __init__(self, expanded: bool = False):
        super().__init__("Battery Replacement (EV)", expanded)
        
    def render_content(self, params: Dict[str, Any]) -> None:
        st.checkbox(
            "Enable Battery Replacement", 
            key="enable_battery_replacement", 
            value=params['enable_battery_replacement']
        )
        
        # Only show battery replacement options if enabled
        if st.session_state.get('enable_battery_replacement'):
            replace_mode = st.radio(
                "Replacement Trigger", 
                ["Fixed Year", "Capacity Threshold"], 
                key="battery_replace_mode"
            )
            
            if replace_mode == "Fixed Year":
                # Determine min/max years based on current year and analysis duration
                analysis_years = params['analysis_years']
                min_replace_index = 1
                max_replace_index = analysis_years
                
                st.number_input(
                    "Battery Replacement Year (Index)", 
                    min_value=min_replace_index, 
                    max_value=max_replace_index, 
                    step=1, 
                    key="battery_replacement_year", 
                    help=f"Year index within analysis period (1 to {max_replace_index}).",
                    value=params['battery_replacement_year']
                )
            else:  # Capacity Threshold
                initial_threshold_display = params['battery_replacement_threshold']
                
                st.number_input(
                    "Battery Capacity Threshold (%)", 
                    min_value=0.0, 
                    max_value=100.0, 
                    step=1.0, 
                    format="%.1f", 
                    key="battery_replacement_threshold", 
                    help="Replace when capacity drops below this % (0-100%).", 
                    value=initial_threshold_display
                ) 