import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Type
import logging
from datetime import datetime

# Import necessary classes from sibling modules
from .scenarios import Scenario
from .vehicles import Vehicle, ElectricVehicle, DieselVehicle
from .components import (
    CostComponent, AcquisitionCost, EnergyCost, MaintenanceCost,
    InfrastructureCost, BatteryReplacementCost, InsuranceCost,
    RegistrationCost, ResidualValue, CarbonTaxCost, RoadUserChargeCost # Added new components
)

logger = logging.getLogger(__name__)

class TCOCalculator:
    """Calculates and compares Total Cost of Ownership for electric and diesel vehicles."""

    def __init__(self):
        """Initialize the TCO Calculator with a standard set of cost components."""
        # Define the standard list of component classes to use
        self._component_classes: List[Type[CostComponent]] = [
            AcquisitionCost,
            EnergyCost,
            MaintenanceCost,
            InfrastructureCost,
            BatteryReplacementCost,
            InsuranceCost,
            RegistrationCost,
            CarbonTaxCost,
            RoadUserChargeCost,
            ResidualValue # Keep ResidualValue last as it's often negative
        ]

    def _get_applicable_components(self, vehicle: Vehicle, scenario: Scenario) -> List[CostComponent]:
        """Returns instances of components applicable to the vehicle type and scenario settings."""
        applicable_components = []
        component_instances = {Comp: Comp() for Comp in self._component_classes} # Instantiate all potential components

        for comp_class, instance in component_instances.items():
            # Basic applicability checks
            if isinstance(instance, (InfrastructureCost, BatteryReplacementCost)) and not isinstance(vehicle, ElectricVehicle):
                continue # Skip EV-only costs for Diesel
            if isinstance(instance, CarbonTaxCost):
                 if not isinstance(vehicle, DieselVehicle) or not scenario.include_carbon_tax:
                     continue # Skip carbon tax if not Diesel or not included
            if isinstance(instance, RoadUserChargeCost) and not scenario.include_road_user_charge:
                continue # Skip RUC if not included

            applicable_components.append(instance)

        return applicable_components

    def _calculate_annual_costs_undiscounted(self, vehicle: Vehicle, scenario: Scenario) -> pd.DataFrame:
        """Calculate undiscounted annual costs for each applicable component for a single vehicle."""
        applicable_components = self._get_applicable_components(vehicle, scenario)
        component_names = [comp.__class__.__name__ for comp in applicable_components]
        years = list(range(scenario.analysis_years))
        annual_costs_data = {name: [0.0] * scenario.analysis_years for name in component_names}

        total_mileage_km = 0.0

        for year_index in years:
            current_calendar_year = datetime.now().year + year_index # Approximate calendar year

            for comp_instance in applicable_components:
                comp_name = comp_instance.__class__.__name__
                try:
                    cost = comp_instance.calculate_annual_cost(
                        year=current_calendar_year,
                        vehicle=vehicle,
                        scenario=scenario,
                        calculation_year_index=year_index,
                        total_mileage_km=total_mileage_km
                    )
                    # Ensure cost is numeric, default to 0 if calculation returns None or NaN unexpectedly
                    annual_costs_data[comp_name][year_index] = cost if pd.notna(cost) else 0.0
                except Exception as e:
                    logger.error(f"Error calculating {comp_name} for {vehicle.name} in year index {year_index}: {e}", exc_info=True)
                    annual_costs_data[comp_name][year_index] = np.nan # Mark as NaN on error

            # Update total mileage for the *next* year's calculation
            total_mileage_km += scenario.annual_mileage

        df = pd.DataFrame(annual_costs_data)
        # Add Year column (1-based)
        df['Year'] = [i + 1 for i in years]
        # Calculate Total undiscounted cost
        df['Total'] = df[component_names].sum(axis=1)

        # Set Year as index if preferred, or keep it as a column
        # df = df.set_index('Year')
        return df

    def _apply_discounting(self, undiscounted_df: pd.DataFrame, discount_rate: float) -> pd.DataFrame:
        """Apply discounting to annual costs (excluding the 'Year' column) to get present values."""
        if 'Year' not in undiscounted_df.columns:
             raise ValueError("Undiscounted DataFrame must have a 'Year' column (1-based).")

        discounted_df = undiscounted_df.copy()
        # Year index (0-based) for discounting formula: t = Year - 1
        discount_factors = (1 + discount_rate) ** (discounted_df['Year'] - 1)

        cost_cols = [col for col in discounted_df.columns if col not in ['Year']]

        for col in cost_cols:
            # Apply discounting: cost / (1 + rate)^t
            # Use .astype(float) to handle potential division issues if column is not float
            discounted_df[col] = (discounted_df[col].astype(float) / discount_factors).fillna(0)

        return discounted_df

    def calculate(self, scenario: Scenario) -> Dict:
        """
        Perform the full TCO calculation for the given scenario.

        Args:
            scenario: The Scenario object containing all input parameters.

        Returns:
            A dictionary containing detailed results including undiscounted and discounted
            annual costs, total TCO, LCOD, parity year, and analysis years.
        """
        results = {
            'error': None,
            'analysis_years': scenario.analysis_years,
            'electric_annual_costs_undiscounted': None,
            'diesel_annual_costs_undiscounted': None,
            'electric_annual_costs_discounted': None,
            'diesel_annual_costs_discounted': None,
            'electric_total_tco': None,
            'diesel_total_tco': None,
            'electric_lcod': None,
            'diesel_lcod': None,
            'parity_year': None,
        }
        try:
            # 1. Calculate undiscounted annual costs for each vehicle
            logger.info(f"Calculating undiscounted costs for EV: {scenario.electric_vehicle.name}")
            electric_undisc = self._calculate_annual_costs_undiscounted(scenario.electric_vehicle, scenario)
            logger.info(f"Calculating undiscounted costs for Diesel: {scenario.diesel_vehicle.name}")
            diesel_undisc = self._calculate_annual_costs_undiscounted(scenario.diesel_vehicle, scenario)
            results['electric_annual_costs_undiscounted'] = electric_undisc
            results['diesel_annual_costs_undiscounted'] = diesel_undisc

            # Handle potential NaN values from calculation errors before discounting
            if electric_undisc.isnull().values.any() or diesel_undisc.isnull().values.any():
                 logger.warning("NaN values detected in undiscounted annual costs. Discounting and totals may be affected.")
                 # Fill NaN with 0 before proceeding? Or raise error?
                 # For now, let's fill with 0 for robustness in totals, but log warning.
                 electric_undisc = electric_undisc.fillna(0)
                 diesel_undisc = diesel_undisc.fillna(0)

            # 2. Apply discounting
            logger.info("Applying discounting...")
            electric_disc = self._apply_discounting(electric_undisc, scenario.discount_rate_real)
            diesel_disc = self._apply_discounting(diesel_undisc, scenario.discount_rate_real)
            results['electric_annual_costs_discounted'] = electric_disc
            results['diesel_annual_costs_discounted'] = diesel_disc

            # 3. Calculate total TCO (sum of *discounted* total costs)
            total_tco_ev = electric_disc['Total'].sum() if not electric_disc.empty else 0
            total_tco_diesel = diesel_disc['Total'].sum() if not diesel_disc.empty else 0
            results['electric_total_tco'] = total_tco_ev
            results['diesel_total_tco'] = total_tco_diesel
            logger.info(f"Total Discounted TCO - EV: {total_tco_ev:,.2f}, Diesel: {total_tco_diesel:,.2f}")

            # 4. Calculate Levelized Cost of Driving (LCOD) using discounted TCO
            lcod_ev = self._calculate_lcod(total_tco_ev, scenario)
            lcod_diesel = self._calculate_lcod(total_tco_diesel, scenario)
            results['electric_lcod'] = lcod_ev
            results['diesel_lcod'] = lcod_diesel
            logger.info(f"LCOD - EV: {lcod_ev:.3f} AUD/km, Diesel: {lcod_diesel:.3f} AUD/km")

            # 5. Find parity year using *undiscounted* cumulative costs
            parity_year = self._find_parity_year_undiscounted(
                electric_undisc['Total'].cumsum(),
                diesel_undisc['Total'].cumsum(),
                electric_undisc['Year'] # Pass Year series for mapping index to year number
            )
            results['parity_year'] = parity_year
            logger.info(f"Undiscounted TCO Parity Year: {parity_year if parity_year else 'None'}")

            return results

        except Exception as e:
            logger.error(f"Error during TCO calculation: {e}", exc_info=True)
            results['error'] = f"Calculation failed: {e}"
            return results # Return partial results with error message

    def _calculate_lcod(self, total_discounted_tco: float, scenario: Scenario) -> Optional[float]:
        """Calculate Levelized Cost of Driving (per km).
        
        Uses total discounted TCO divided by total *undiscounted* mileage.
        """
        if total_discounted_tco is None or np.isnan(total_discounted_tco):
            return None

        # Calculate total undiscounted mileage over the analysis period
        total_undiscounted_km = scenario.annual_mileage * scenario.analysis_years

        if total_undiscounted_km == 0:
            logger.warning("Total undiscounted mileage is zero, cannot calculate LCOD.")
            return None

        lcod = total_discounted_tco / total_undiscounted_km
        return lcod

    def _find_parity_year_undiscounted(self, electric_cumulative_undisc: pd.Series, diesel_cumulative_undisc: pd.Series, year_series: pd.Series) -> Optional[int]:
        """Find the first year when undiscounted electric cumulative TCO is <= undiscounted diesel cumulative TCO."""
        try:
            if electric_cumulative_undisc.empty or diesel_cumulative_undisc.empty:
                return None
            # Find indices where electric <= diesel
            parity_indices = electric_cumulative_undisc.index[electric_cumulative_undisc <= diesel_cumulative_undisc]

            if not parity_indices.empty:
                first_parity_index = parity_indices[0]
                # Map the DataFrame index back to the actual analysis year (using the 'Year' column)
                parity_year_number = year_series.iloc[first_parity_index]
                return int(parity_year_number)
            else:
                return None # Parity not reached
        except IndexError:
             logger.warning("Index error while finding parity year, likely due to empty series.")
             return None
        except Exception as e:
            logger.error(f"Error finding undiscounted parity year: {e}", exc_info=True)
            return None
