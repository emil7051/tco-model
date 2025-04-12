"""
Summary widgets for displaying key TCO metrics in the application.

This module provides widgets for presenting key findings and metrics
from TCO calculations in a concise format.
"""

import streamlit as st
import pandas as pd
import logging
from typing import Dict, Any, List, Optional, Tuple

from ui.widgets.output_widgets.base import OutputWidget, format_currency, is_valid_dataframe
from tco_model.scenarios import Scenario

logger = logging.getLogger(__name__)

class SummaryWidget(OutputWidget):
    """Base class for summary output widgets."""
    
    def __init__(self, title: str = "Summary"):
        """
        Initialize a summary widget.
        
        Args:
            title: Widget title to display
        """
        super().__init__(title)


class TCOSummaryMetrics(SummaryWidget):
    """Widget to display key TCO metrics as streamlit metrics."""
    
    def __init__(self):
        super().__init__("TCO Key Metrics")
    
    def render_content(self, results: Dict[str, Any]) -> None:
        """
        Render the key TCO metrics.
        
        Args:
            results: Current calculation results dictionary
        """
        if 'vehicles' not in results or 'electric' not in results['vehicles'] or 'diesel' not in results['vehicles']:
            st.info("No valid vehicle TCO results available for display.")
            return
        
        ev_results = results['vehicles']['electric']
        diesel_results = results['vehicles']['diesel']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Total TCO")
            st.metric(
                label=f"{ev_results.get('name', 'Electric')}",
                value=format_currency(ev_results.get('total_discounted_tco', 0))
            )
            st.metric(
                label=f"{diesel_results.get('name', 'Diesel')}",
                value=format_currency(diesel_results.get('total_discounted_tco', 0))
            )
        
        with col2:
            st.subheader("Cost per km (LCOD)")
            ev_lcod = ev_results.get('lcod_aud_per_km')
            diesel_lcod = diesel_results.get('lcod_aud_per_km')
            
            if ev_lcod is not None:
                 st.metric(
                     label=f"{ev_results.get('name', 'Electric')}",
                     value=f"${ev_lcod:.3f}/km"
                 )
            else:
                 st.info("EV LCOD not available.")
                 
            if diesel_lcod is not None:
                 st.metric(
                     label=f"{diesel_results.get('name', 'Diesel')}",
                     value=f"${diesel_lcod:.3f}/km"
                 )
            else:
                 st.info("Diesel LCOD not available.")

        with col3:
            st.subheader("Comparison")
            tco_diff = results.get('tco_difference')
            lcod_diff = results.get('lcod_difference')
            parity_info = results.get('parity_info', {})
            parity_year = parity_info.get('parity_year_undiscounted')

            if tco_diff is not None:
                diff_formatted = format_currency(abs(tco_diff))
                savings_label = f"EV vs Diesel TCO Savings"
                if tco_diff > 0:
                    st.metric(label=savings_label, value=diff_formatted, delta="EV Cheaper")
                elif tco_diff < 0:
                    st.metric(label=savings_label, value=diff_formatted, delta="Diesel Cheaper", delta_color="inverse")
                else:
                    st.metric(label=savings_label, value="$0.00", delta="Costs are equal")
            else:
                 st.info("TCO difference not available.")

            if parity_year is not None:
                 st.metric(
                     label="TCO Parity Year (Undiscounted)",
                     value=f"Year {parity_year}"
                 )
            else:
                 st.info("TCO Parity not reached within analysis period.")


class DetailedBreakdownWidget(SummaryWidget):
    """Widget to display detailed cost breakdown with descriptions."""
    
    def __init__(self, vehicle_type: str):
        """
        Initialize a detailed breakdown widget.
        
        Args:
            vehicle_type: Vehicle type to display ("electric" or "diesel")
        """
        super().__init__(f"{vehicle_type.title()} Vehicle Cost Detail")
        self.vehicle_type = vehicle_type
    
    def render_content(self, results: Dict[str, Any]) -> None:
        """
        Render the detailed cost breakdown.
        
        Args:
            results: Current calculation results dictionary
        """
        vehicle_results = results.get('vehicles', {}).get(self.vehicle_type)
        if not vehicle_results:
            st.warning(f"No results found for {self.vehicle_type} vehicle.")
            return

        df_discounted = vehicle_results.get('discounted_annual_costs')
        if not is_valid_dataframe(df_discounted):
            st.info(f"No discounted annual cost breakdown data available for {self.vehicle_type}.")
            return

        component_totals = df_discounted.drop(columns=['Total'], errors='ignore').sum()
        total_tco = vehicle_results.get('total_discounted_tco', 0)

        if total_tco == 0:
             st.info(f"Total TCO for {self.vehicle_type} is zero.")
             return

        st.metric(f"Total Discounted {self.vehicle_type.title()} TCO", format_currency(total_tco))
        st.divider()

        if 'scenario' not in st.session_state:
            st.error("Scenario object not found in session state.")
            return
        scenario: Scenario = st.session_state.scenario

        for component, value in component_totals.items():
            if component == 'YearIndex':
                continue
            if abs(value) < 0.01 and component != 'ResidualValue':
                continue

            percentage = (value / total_tco * 100) if total_tco else 0
            with st.expander(f"{component}: {format_currency(value)} ({percentage:.1f}%) "):
                self._render_component_details(component, scenario)
            
    def _render_component_details(self, component: str, scenario: Scenario) -> None:
        """
        Render detailed information about a cost component based on the scenario object.

        Args:
            component: The cost component name (COLUMN NAME FROM DataFrame)
            scenario: The input Scenario object from session state.
        """
        st.write(f"Details related to the {component} calculation based on scenario inputs.")
        vehicle = getattr(scenario, f"{self.vehicle_type}_vehicle", None)
        if not vehicle:
            st.warning(f"Could not find {self.vehicle_type} vehicle in scenario for details.")
            return

        if component == "AcquisitionCost":
            finance_method = scenario.financing_options.financing_method
            st.caption(f"Based on initial purchase price ({format_currency(vehicle.base_purchase_price_aud)}) and {finance_method} financing.")
            if finance_method == 'loan':
                 st.caption(f"Loan Term: {scenario.financing_options.loan_term_years} years")
                 st.caption(f"Interest Rate: {scenario.financing_options.loan_interest_rate_percent:.1f}%" )
                 st.caption(f"Down Payment: {scenario.financing_options.down_payment_percent:.1f}%" )

        elif component == "EnergyCost":
             st.caption("Based on annual mileage and selected energy price scenario.")
             if self.vehicle_type == "electric":
                 price_scenario_name = scenario.electricity_price_projections.selected_scenario_name
                 st.caption(f"Consumption: {vehicle.energy_consumption_kwh_per_km:.2f} kWh/km")
                 st.caption(f"Price Scenario: {price_scenario_name}")
             else:
                 price_scenario_name = scenario.diesel_price_projections.selected_scenario_name
                 st.caption(f"Consumption: {vehicle.fuel_consumption_l_per_100km:.1f} L/100km")
                 st.caption(f"Price Scenario: {price_scenario_name}")

        elif component == "MaintenanceCost":
             st.caption("Based on vehicle type maintenance schedule and increase rates.")
             rate = scenario.general_cost_increase_rates.maintenance_annual_increase_rate_percent
             st.caption(f"Annual Increase: {rate:.1f}%" )

        elif component == "InfrastructureCost":
            if self.vehicle_type == "electric":
                infra = scenario.infrastructure_costs
                st.caption("Amortized charger hardware, installation, and maintenance costs.")
                st.caption(f"Hardware: {format_currency(infra.selected_charger_cost_aud)}")
                st.caption(f"Installation: {format_currency(infra.selected_installation_cost_aud)}")
                st.caption(f"Maintenance: {infra.charger_maintenance_annual_rate_percent:.1f}% of capital/year")
                st.caption(f"Lifespan: {infra.charger_lifespan_years} years")
            else:
                st.caption("Not applicable for diesel vehicles.")

        elif component == "BatteryReplacementCost":
             if self.vehicle_type == "electric":
                config = scenario.battery_replacement_config
                if config.enable_battery_replacement:
                    st.caption("Cost of battery replacement based on trigger settings.")
                    mode = st.session_state.get("battery_replace_mode", "Fixed Year") 
                    if mode == "Fixed Year":
                        year_idx = config.force_replacement_year_index
                        year_display = f"Year Index {year_idx}" if year_idx is not None else "Not Set"
                        st.caption(f"Trigger: Fixed ({year_display})")
                    else:
                        thresh_val = config.replacement_threshold_fraction
                        st.caption(f"Trigger: Capacity Threshold ({thresh_val:.2f} fraction / {thresh_val*100:.0f}%)")
                else:
                    st.caption("Battery replacement disabled in scenario.")
             else:
                st.caption("Not applicable for diesel vehicles.")

        elif component == "InsuranceCost":
             st.caption("Based on vehicle type base insurance cost and increase rates.")
             rate = scenario.general_cost_increase_rates.insurance_annual_increase_rate_percent
             st.caption(f"Annual Increase: {rate:.1f}%" )

        elif component == "RegistrationCost":
             st.caption("Based on vehicle base registration cost and increase rates.")
             rate = scenario.general_cost_increase_rates.registration_annual_increase_rate_percent
             st.caption(f"Annual Increase: {rate:.1f}%" )

        elif component == "CarbonTaxCost":
             config = scenario.carbon_tax_config
             if config.include_carbon_tax:
                 st.caption("Cost based on vehicle emissions, tax rate, and increase rate.")
                 st.caption(f"Initial Rate: {format_currency(config.initial_rate_aud_per_tonne_co2e)} / tonne CO2e")
                 st.caption(f"Annual Increase: {config.annual_increase_rate_percent:.1f}%" )
             else:
                 st.caption("Carbon tax calculation disabled in scenario.")

        elif component == "RoadUserChargeCost":
             config = scenario.road_user_charge_config
             if config.include_road_user_charge:
                 st.caption("Cost based on annual mileage, RUC rate, and increase rate.")
                 st.caption(f"Initial Rate: ${config.initial_charge_aud_per_km:.3f} / km")
                 st.caption(f"Annual Increase: {config.annual_increase_rate_percent:.1f}%" )
             else:
                 st.caption("Road user charge calculation disabled in scenario.")

        elif component == "ResidualValue":
             st.caption("Negative cost representing the estimated asset value at the end of the analysis period.")
        else:
            st.caption("No specific details available for this component.")

class KeyFindingsWidget(SummaryWidget):
    """Widget to display key findings and insights."""
    
    def __init__(self):
        super().__init__("Key Findings")
    
    def render_content(self, results: Dict[str, Any]) -> None:
        """
        Render the key findings about the TCO analysis.
        
        Args:
            results: Current calculation results dictionary
        """
        if 'vehicles' not in results or 'electric' not in results['vehicles'] or 'diesel' not in results['vehicles']:
            st.info("No valid vehicle TCO results available to generate findings.")
            return

        ev_results = results['vehicles']['electric']
        diesel_results = results['vehicles']['diesel']
        ev_name = ev_results.get('name', 'Electric')
        diesel_name = diesel_results.get('name', 'Diesel')
        ev_tco = ev_results.get('total_discounted_tco')
        diesel_tco = diesel_results.get('total_discounted_tco')

        if ev_tco is None or diesel_tco is None:
            st.warning("TCO values missing, cannot generate findings.")
            return
            
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Overall Cost Comparison")
            tco_diff = results.get('tco_difference', 0)
            
            if tco_diff > 0:
                st.success(f"The **{ev_name}** has a lower TCO by **{format_currency(abs(tco_diff))}**.")
            elif tco_diff < 0:
                st.error(f"The **{diesel_name}** has a lower TCO by **{format_currency(abs(tco_diff))}**.")
            else:
                st.info("Both vehicles have the same total cost of ownership.")
                
            parity_info = results.get('parity_info', {})
            parity_year = parity_info.get('parity_year_undiscounted')
            
            if parity_year is not None:
                st.subheader("Cost Parity (Undiscounted)")
                st.info(f"Cumulative costs become equal around Year **{parity_year}**.")
            else:
                 st.info("Undiscounted TCO parity was not reached within the analysis period.")

        with col2:
            st.subheader("Component Insights")
            
            df_ev_discounted = ev_results.get('discounted_annual_costs')
            df_diesel_discounted = diesel_results.get('discounted_annual_costs')

            if is_valid_dataframe(df_ev_discounted) and is_valid_dataframe(df_diesel_discounted):
                ev_comp_totals = df_ev_discounted.drop(columns=['Total'], errors='ignore').sum()
                diesel_comp_totals = df_diesel_discounted.drop(columns=['Total'], errors='ignore').sum()
                
                common_components = ev_comp_totals.index.intersection(diesel_comp_totals.index)
                component_diffs = []
                for component in common_components:
                    diff = diesel_comp_totals[component] - ev_comp_totals[component]
                    component_diffs.append((component, diff))
                
                for component in ev_comp_totals.index.difference(diesel_comp_totals.index):
                    component_diffs.append((component, -ev_comp_totals[component]))
                    
                for component in diesel_comp_totals.index.difference(ev_comp_totals.index):
                    component_diffs.append((component, diesel_comp_totals[component]))

                if component_diffs:
                    component_diffs.sort(key=lambda x: abs(x[1]), reverse=True)
                    biggest_component, biggest_diff = component_diffs[0]
                    
                    if abs(biggest_diff) > 0.01:
                        if biggest_diff > 0:
                            st.info(f"Largest cost saving for **{ev_name}** (or highest cost for Diesel) is in **{biggest_component}** ({format_currency(abs(biggest_diff))}).")
                        elif biggest_diff < 0:
                            st.info(f"Largest cost saving for **{diesel_name}** (or highest cost for EV) is in **{biggest_component}** ({format_currency(abs(biggest_diff))}).")
                    else:
                        st.info("No significant cost differences found in individual components.")
                else:
                     st.info("Could not compare cost components.")
            else:
                st.info("Detailed component breakdown data not available for comparison.")

            if 'sensitivity_analysis' in results and is_valid_dataframe(results['sensitivity_analysis']):
                st.subheader("Sensitivity Insights (Example)")
                st.info("Sensitivity results processing would go here.")
                # Placeholder: Add logic to parse and display sensitivity findings
                # try:
                #     sensitivity_df = results['sensitivity_analysis'].copy()
                #     sensitivity_df['abs_impact'] = sensitivity_df['Impact'].apply(lambda x: abs(float(str(x).replace('$', '').replace(',', '').replace('+', ''))))
                #     sensitivity_df = sensitivity_df.sort_values('abs_impact', ascending=False)
                #     if not sensitivity_df.empty:
                #         most_sensitive = sensitivity_df.iloc[0]
                #         st.info(f"The TCO difference is most sensitive to changes in **{most_sensitive['Parameter']}**.")
                #     else:
                #         st.info("No sensitivity analysis results to process.")
                # except Exception as e:
                #     logger.warning(f"Could not process sensitivity impact column: {e}")
                #     st.info("Could not determine most sensitive parameter from sensitivity data.") 