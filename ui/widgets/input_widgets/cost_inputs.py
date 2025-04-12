"""
Cost input widgets for the TCO Model application.

This module provides widgets for cost and infrastructure parameters.
"""

import streamlit as st
import logging
from typing import Any # Removed Dict, List

from ui.widgets.input_widgets.sidebar import SidebarWidget
from tco_model.scenarios import Scenario # Import Scenario

logger = logging.getLogger(__name__)

class InfrastructureInputWidget(SidebarWidget):
    """Widget for infrastructure parameters."""
    
    def __init__(self, expanded: bool = False):
        super().__init__("Infrastructure (EV)", expanded)
        
    def render_content(self, scenario: Scenario) -> None: # Updated signature
        st.number_input(
            "Charger Hardware Cost (AUD)",
            min_value=0.0,
            step=100.0,
            format="%.0f",
            key="scenario.infrastructure_costs.selected_charger_cost_aud" # Updated key
            # value removed
        )

        st.number_input(
            "Charger Installation Cost (AUD)",
            min_value=0.0,
            step=100.0,
            format="%.0f",
            key="scenario.infrastructure_costs.selected_installation_cost_aud" # Updated key
            # value removed
        )

        st.number_input(
            "Charger Lifespan (years)",
            min_value=1,
            step=1,
            key="scenario.infrastructure_costs.charger_lifespan_years", # Updated key
            help="Expected operational life of the charger hardware before needing replacement."
            # value removed
        )

        st.number_input(
            "Charger Maintenance (% of Capital)",
            min_value=0.0,
            max_value=10.0, # Assuming this is correct (0-10%)
            step=0.1,
            format="%.1f",
            key="scenario.infrastructure_costs.charger_maintenance_annual_rate_percent", # Updated key
            help="Annual maintenance cost as % of hardware + install cost (0-10%)."
            # value removed
        )


class OtherCostsInputWidget(SidebarWidget):
    """Widget for maintenance and other costs."""
    
    def __init__(self, expanded: bool = False):
        super().__init__("Other Costs & Increase Rates", expanded)
        
    def render_content(self, scenario: Scenario) -> None: # Updated signature
        st.caption("Vehicle-specific maintenance, insurance, and registration costs are defined per vehicle.")
        # Removed the direct input for registration cost as it's now vehicle-specific

        st.number_input(
            "Carbon Tax Rate (AUD/tonne CO2e)",
            min_value=0.0,
            step=1.0,
            format="%.2f",
            key="scenario.carbon_tax_config.initial_rate_aud_per_tonne_co2e", # Updated key
            help="Initial tax applied per tonne of Carbon Dioxide Equivalent (CO2e) emissions."
            # value removed
        )

        st.number_input(
            "Road User Charge (AUD/km)",
            min_value=0.0,
            step=0.01,
            format="%.2f",
            key="scenario.road_user_charge_config.initial_charge_aud_per_km", # Updated key
            help="Initial charge applied per kilometer traveled, potentially replacing registration or fuel excise."
            # value removed
        )

        st.divider()
        st.subheader("Annual Cost Increase Rates (Real %)")

        st.number_input(
            "Maintenance Cost Increase Rate (%/yr)",
            min_value=0.0,
            step=0.1,
            format="%.1f",
            key="scenario.general_cost_increase_rates.maintenance_annual_increase_rate_percent", # Updated key
            help="Annual real increase for maintenance."
            # value removed
        )

        st.number_input(
            "Insurance Cost Increase Rate (%/yr)",
            min_value=0.0,
            step=0.1,
            format="%.1f",
            key="scenario.general_cost_increase_rates.insurance_annual_increase_rate_percent", # Updated key
            help="Annual real increase for insurance."
            # value removed
        )

        st.number_input(
            "Registration Cost Increase Rate (%/yr)",
            min_value=0.0,
            step=0.1,
            format="%.1f",
            key="scenario.general_cost_increase_rates.registration_annual_increase_rate_percent", # Updated key
            help="Annual real increase for registration."
            # value removed
        )

        st.number_input(
            "Carbon Tax Increase Rate (%/yr)",
            min_value=0.0,
            step=0.1,
            format="%.1f",
            key="scenario.carbon_tax_config.annual_increase_rate_percent", # Updated key
            help="Annual real increase for carbon tax."
            # value removed
        )

        st.number_input(
            "Road User Charge Increase Rate (%/yr)",
            min_value=0.0,
            step=0.1,
            format="%.1f",
            key="scenario.road_user_charge_config.annual_increase_rate_percent", # Updated key
            help="Annual real increase for RUC."
            # value removed
        )


class EnergyPricingInputWidget(SidebarWidget):
    """Widget for energy pricing parameters."""
    
    def __init__(self, expanded: bool = False):
        super().__init__("Energy Pricing", expanded)
        
    def render_content(self, scenario: Scenario) -> None: # Updated signature
        # Access projections directly from the scenario object
        elec_projections = scenario.electricity_price_projections
        diesel_projections = scenario.diesel_price_projections

        # Electricity Scenario Selection
        if elec_projections and elec_projections.scenarios:
            elec_scenario_names = [s.name for s in elec_projections.scenarios]
            selected_elec_key = "scenario.electricity_price_projections.selected_scenario_name"
            st.selectbox(
                "Electricity Price Scenario",
                options=elec_scenario_names,
                key=selected_elec_key
                # index removed, relies on key
            )
        else:
            st.warning("No electricity price projections found in scenario.")

        # Diesel Scenario Selection
        if diesel_projections and diesel_projections.scenarios:
            diesel_scenario_names = [s.name for s in diesel_projections.scenarios]
            selected_diesel_key = "scenario.diesel_price_projections.selected_scenario_name"
            st.selectbox(
                "Diesel Price Scenario",
                options=diesel_scenario_names,
                key=selected_diesel_key
                # index removed, relies on key
            )
        else:
            st.warning("No diesel price scenarios found in scenario.")


class BatteryReplacementInputWidget(SidebarWidget):
    """Widget for battery replacement parameters."""
    
    def __init__(self, expanded: bool = False):
        super().__init__("Battery Replacement (EV)", expanded)
        
    def render_content(self, scenario: Scenario) -> None: # Updated signature
        enable_key = "scenario.battery_replacement_config.enable_battery_replacement"
        st.checkbox(
            "Enable Battery Replacement",
            key=enable_key
            # value removed
        )

        # Read enabled status directly from the scenario object
        if scenario.battery_replacement_config.enable_battery_replacement:
            # UI only key for mode selection - read from session state
            mode_key = "battery_replace_mode"
            replace_mode = st.radio(
                "Replacement Trigger",
                ["Fixed Year", "Capacity Threshold"],
                key=mode_key # Keep reading/writing UI mode to session state
                # index removed
            )

            if replace_mode == "Fixed Year":
                year_key = "scenario.battery_replacement_config.force_replacement_year_index"
                analysis_years = scenario.analysis_period_years
                min_replace_year_idx = 0 # 0-based index
                max_replace_year_idx = analysis_years - 1 # Max 0-based index

                st.number_input(
                    f"Battery Replacement Year Index (0 to {max_replace_year_idx})",
                    min_value=min_replace_year_idx,
                    max_value=max_replace_year_idx,
                    step=1,
                    key=year_key, # Key points to the 0-based index attribute
                    help=f"0-based index for replacement year (0 = start of year 1, {max_replace_year_idx} = start of year {analysis_years})."
                    # value removed
                )
            else:  # Capacity Threshold
                threshold_key = "scenario.battery_replacement_config.replacement_threshold_fraction"
                st.number_input(
                    "Battery Capacity Threshold (Fraction)",
                    min_value=0.0,
                    max_value=1.0,
                    step=0.01,
                    format="%.2f", # Format as fraction
                    key=threshold_key, # Key points to the fraction attribute
                    help="Replace when capacity drops below this fraction (0.0 to 1.0). E.g., 0.7 for 70%."
                    # value removed
                ) 