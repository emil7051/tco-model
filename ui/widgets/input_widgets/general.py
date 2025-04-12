"""
General input widgets for the TCO Model application.

This module provides widgets for general scenario parameters.
"""

import streamlit as st
import datetime
import logging
from typing import Any

from ui.widgets.input_widgets.sidebar import SidebarWidget
from config import constants
from tco_model.scenarios import Scenario

logger = logging.getLogger(__name__)

class GeneralInputWidget(SidebarWidget):
    """Widget for general scenario parameters."""
    
    def __init__(self, expanded: bool = True):
        super().__init__("General", expanded)
        
    def render_content(self, scenario: Scenario) -> None:
        st.text_input(
            "Scenario Name", 
            key="scenario.name"
        )
        
        current_year = datetime.datetime.now().year
        st.number_input(
            "Start Year", 
            min_value=current_year - 10, 
            max_value=current_year + 30,
            step=1, 
            format="%d", 
            key="scenario.analysis_start_year"
        )
        
        st.number_input(
            "Analysis Period (Years)",
            min_value=constants.MIN_ANALYSIS_YEARS, 
            max_value=constants.MAX_ANALYSIS_YEARS,
            step=1, 
            format="%d", 
            key="scenario.analysis_period_years",
            help="Duration of the analysis in years (1-30)."
        )
        
        st.text_area(
            "Description", 
            key="scenario.description"
        )


class EconomicInputWidget(SidebarWidget):
    """Widget for economic parameters."""
    
    def __init__(self, expanded: bool = False):
        super().__init__("Economic", expanded)
        
    def render_content(self, scenario: Scenario) -> None:
        st.number_input(
            "Discount Rate (%)", 
            min_value=0.0, 
            max_value=20.0, 
            step=0.1, 
            format="%.1f", 
            key="scenario.economic_parameters.discount_rate_percent_real",
            help="Real discount rate (0-20%)."
        )
        
        st.number_input(
            "Inflation Rate (%)", 
            min_value=0.0, 
            max_value=10.0, 
            step=0.1, 
            format="%.1f", 
            key="scenario.economic_parameters.inflation_rate_percent",
            help="General inflation rate (0-10%)."
        )
        
        finance_method_key = "scenario.financing_options.financing_method"
        st.selectbox(
            "Financing Method", 
            options=["loan", "cash"], 
            key=finance_method_key
        )
        
        if scenario.financing_options.financing_method == 'loan':
            st.number_input(
                "Loan Term (years)", 
                min_value=1, 
                max_value=15, 
                step=1, 
                key="scenario.financing_options.loan_term_years",
                help="Duration of the vehicle loan financing."
            )
            
            st.number_input(
                "Loan Interest Rate (%)", 
                min_value=0.0, 
                max_value=20.0, 
                step=0.1, 
                format="%.1f", 
                key="scenario.financing_options.loan_interest_rate_percent",
                help="Loan interest rate (0-20%)."
            )
            
            st.number_input(
                "Down Payment (%)", 
                min_value=0.0, 
                max_value=100.0, 
                step=1.0, 
                format="%.1f", 
                key="scenario.financing_options.down_payment_percent",
                help="Down payment percentage (0-100%)."
            )


class OperationalInputWidget(SidebarWidget):
    """Widget for operational parameters."""
    
    def __init__(self, expanded: bool = True):
        super().__init__("Operational", expanded)
        
    def render_content(self, scenario: Scenario) -> None:
        st.number_input(
            "Annual Mileage (km)", 
            min_value=0.0, 
            step=1000.0, 
            format="%.0f", 
            key="scenario.operational_parameters.annual_mileage_km",
            help="Average distance the vehicle is expected to travel per year."
        ) 