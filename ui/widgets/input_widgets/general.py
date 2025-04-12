"""
General input widgets for the TCO Model application.

This module provides widgets for general scenario parameters.
"""

import streamlit as st
import datetime
import logging
from typing import Dict, Any

from ui.widgets.input_widgets.sidebar import SidebarWidget
from config import constants

logger = logging.getLogger(__name__)

class GeneralInputWidget(SidebarWidget):
    """Widget for general scenario parameters."""
    
    def __init__(self, expanded: bool = True):
        super().__init__("General", expanded)
        
    def render_content(self, params: Dict[str, Any]) -> None:
        st.text_input("Scenario Name", key="name", value=params['name'])
        
        current_year = params['start_year']
        st.number_input(
            "Start Year", 
            min_value=current_year - 10, 
            max_value=current_year + 30,
            step=1, 
            format="%d", 
            key="start_year",
            value=current_year
        )
        
        st.number_input(
            "Life Cycle (Years)", 
            min_value=constants.MIN_ANALYSIS_YEARS, 
            max_value=constants.MAX_ANALYSIS_YEARS,
            step=1, 
            format="%d", 
            key="analysis_years", 
            help="Duration of the analysis in years (1-30).",
            value=params['analysis_years']
        )
        
        st.text_area("Description", key="description", value=params['description'])


class EconomicInputWidget(SidebarWidget):
    """Widget for economic parameters."""
    
    def __init__(self, expanded: bool = False):
        super().__init__("Economic", expanded)
        
    def render_content(self, params: Dict[str, Any]) -> None:
        st.number_input(
            "Discount Rate (%)", 
            min_value=0.0, 
            max_value=20.0, 
            step=0.1, 
            format="%.1f", 
            key="discount_rate", 
            help="Real discount rate (0-20%).",
            value=params['discount_rate']
        )
        
        st.number_input(
            "Inflation Rate (%)", 
            min_value=0.0, 
            max_value=10.0, 
            step=0.1, 
            format="%.1f", 
            key="inflation_rate", 
            help="General inflation rate (0-10%).",
            value=params['inflation_rate']
        )
        
        st.selectbox(
            "Financing Method", 
            options=["loan", "cash"], 
            key="financing_method", 
            index=0 if params['financing_method'] == 'loan' else 1
        )
        
        # Only show loan parameters if financing method is "loan"
        if st.session_state.get('financing_method') == 'loan':
            st.number_input(
                "Loan Term (years)", 
                min_value=1, 
                max_value=15, 
                step=1, 
                key="loan_term", 
                help="Duration of the vehicle loan financing.",
                value=params['loan_term']
            )
            
            st.number_input(
                "Loan Interest Rate (%)", 
                min_value=0.0, 
                max_value=20.0, 
                step=0.1, 
                format="%.1f", 
                key="interest_rate", 
                help="Loan interest rate (0-20%).",
                value=params['interest_rate']
            )
            
            st.number_input(
                "Down Payment (%)", 
                min_value=0.0, 
                max_value=100.0, 
                step=1.0, 
                format="%.1f", 
                key="down_payment_pct", 
                help="Down payment percentage (0-100%).",
                value=params['down_payment_pct']
            )


class OperationalInputWidget(SidebarWidget):
    """Widget for operational parameters."""
    
    def __init__(self, expanded: bool = True):
        super().__init__("Operational", expanded)
        
    def render_content(self, params: Dict[str, Any]) -> None:
        st.number_input(
            "Annual Mileage (km)", 
            min_value=0.0, 
            step=1000.0, 
            format="%.0f", 
            key="annual_mileage", 
            help="Average distance the vehicle is expected to travel per year.",
            value=params['annual_mileage']
        ) 