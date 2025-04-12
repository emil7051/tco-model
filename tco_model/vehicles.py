from abc import ABC, abstractmethod
from typing import Dict, Optional, Union, Literal, Protocol, TYPE_CHECKING, List, NewType
from pydantic import (
    BaseModel, Field, model_validator, ValidationInfo, ConfigDict, field_validator, PrivateAttr
)
import math
import logging

# Import custom types from utils
from utils.financial import AUD, Years, Percentage
from utils.conversions import Kilometres, KWH, LitersPer100KM, KWHPerKM, Decimal

# Prevent circular imports for type hints
if TYPE_CHECKING:
    from tco_model.scenarios import Scenario

logger = logging.getLogger(__name__)

# Define CalendarYear type if not already defined/imported elsewhere
CalendarYear = NewType('CalendarYear', int)
# Define projection dictionary types
ResidualValueProjections = Dict[Years, Percentage] # Year -> Percentage (0.0-1.0)
BatteryCostProjections = Dict[CalendarYear, AUD] # Calendar Year -> AUD/kWh

# --- Strategy Pattern for Energy Consumption ---

class EnergyConsumptionStrategy(Protocol):
    """Protocol defining the interface for energy consumption strategies."""
    def calculate_consumption(self, distance_km: Kilometres) -> float:
        """Calculate energy consumption (in native units) for a given distance."""
        ...

    @property
    def unit(self) -> str:
        """Return the unit of energy consumption (e.g., 'kWh', 'L')."""
        ...


class DieselConsumptionStrategy:
    """Strategy for calculating diesel consumption."""
    # Litres per Kilometre
    l_per_km: float

    def __init__(self, l_per_km: float):
        if l_per_km < 0:
            raise ValueError("Fuel consumption rate (L/km) cannot be negative.")
        self.l_per_km = l_per_km

    def calculate_consumption(self, distance_km: Kilometres) -> float:
        """Returns consumption in Litres."""
        if distance_km < 0:
            raise ValueError("Distance cannot be negative.")
        return float(distance_km) * self.l_per_km

    @property
    def unit(self) -> str:
        return "L"


class ElectricConsumptionStrategy:
    """Strategy for calculating electricity consumption."""
    # KWH per Kilometre
    kwh_per_km: KWHPerKM

    def __init__(self, kwh_per_km: KWHPerKM):
        if kwh_per_km < 0:
            raise ValueError("Energy consumption rate (kWh/km) cannot be negative.")
        self.kwh_per_km = kwh_per_km

    def calculate_consumption(self, distance_km: Kilometres) -> KWH:
        """Returns consumption in KWH."""
        if distance_km < 0:
            raise ValueError("Distance cannot be negative.")
        # Note: Assuming kwh_per_km already accounts for typical driving conditions.
        # Charging efficiency is handled elsewhere (e.g., when calculating grid energy pull or costs).
        consumption_float = float(distance_km) * float(self.kwh_per_km)
        return KWH(consumption_float)

    @property
    def unit(self) -> str:
        return "kWh"

# --- Strategy Pattern for Maintenance Costs ---

class MaintenanceStrategy(Protocol):
    """Protocol defining the interface for maintenance cost strategies."""
    def calculate_base_annual_cost(self, vehicle: 'Vehicle', scenario: 'Scenario') -> AUD:
        """Calculate the base annual maintenance cost (AUD) before applying general increase rates."""
        ...

class DieselMaintenanceStrategy:
    """Strategy for calculating diesel vehicle maintenance costs."""
    def calculate_base_annual_cost(self, vehicle: 'Vehicle', scenario: 'Scenario') -> AUD:
        # Type hint the vehicle explicitly for attribute access
        vehicle_typed: DieselVehicle = vehicle
        class_prefix: str = vehicle_typed.vehicle_type
        detail_key = f"{class_prefix}_diesel"

        # Assuming scenario.maintenance_costs_detailed is Dict[str, Dict[str, Any]]
        if detail_key not in scenario.maintenance_costs_detailed:
            logger.warning(f"MaintenanceCost: Detailed costs for key '{detail_key}' not found in scenario. Falling back to 0.")
            return AUD(0.0)

        maint_details: Dict[str, Any] = scenario.maintenance_costs_detailed[detail_key]
        try:
            min_cost = float(maint_details.get('annual_cost_min_aud', 0))
            max_cost = float(maint_details.get('annual_cost_max_aud', 0))
            base_annual_cost_float = (min_cost + max_cost) / 2.0
            return AUD(base_annual_cost_float)
        except (TypeError, ValueError):
             logger.error(f"MaintenanceCost: Invalid min/max values for '{detail_key}'. {maint_details}. Falling back to 0.")
             return AUD(0.0)

class ElectricMaintenanceStrategy:
    """Strategy for calculating electric vehicle maintenance costs."""
    def calculate_base_annual_cost(self, vehicle: 'Vehicle', scenario: 'Scenario') -> AUD:
        # Type hint the vehicle explicitly for attribute access
        vehicle_typed: ElectricVehicle = vehicle
        class_prefix: str = vehicle_typed.vehicle_type
        detail_key = f"{class_prefix}_bet" # BET = Battery Electric Truck

        # Assuming scenario.maintenance_costs_detailed is Dict[str, Dict[str, Any]]
        if detail_key not in scenario.maintenance_costs_detailed:
            logger.warning(f"MaintenanceCost: Detailed costs for key '{detail_key}' not found in scenario. Falling back to 0.")
            return AUD(0.0)

        maint_details: Dict[str, Any] = scenario.maintenance_costs_detailed[detail_key]
        try:
            min_cost = float(maint_details.get('annual_cost_min_aud', 0))
            max_cost = float(maint_details.get('annual_cost_max_aud', 0))
            base_annual_cost_float = (min_cost + max_cost) / 2.0
            return AUD(base_annual_cost_float)
        except (TypeError, ValueError):
             logger.error(f"MaintenanceCost: Invalid min/max values for '{detail_key}'. {maint_details}. Falling back to 0.")
             return AUD(0.0)


# --- Vehicle Classes ---

class Vehicle(BaseModel, ABC):
    """Abstract base class for all vehicle types, using Pydantic."""

    name: str = Field(..., description="Unique identifier for the vehicle.")
    vehicle_type: Literal["rigid", "articulated"] = Field(..., description="Type of heavy vehicle.")
    base_purchase_price_aud: AUD = Field(..., gt=0, description="Initial purchase price in AUD.")
    lifespan_years: Years = Field(..., gt=0, description="Expected operational lifespan in years.")
    # Use Years as key and Percentage (float 0-1) as value
    residual_value_percent_projections: ResidualValueProjections = Field(
        ...,
        description="Residual value percentage (0.0-1.0) at specific years (e.g., {5: 0.5, 10: 0.3, 15: 0.15})",
        json_schema_extra={"example": {5: 0.5, 10: 0.3, 15: 0.15}}
    )
    # Cost fields common to both or handled by components accessing vehicle data
    base_registration_cost_aud: AUD = Field(..., ge=0, description="Base annual registration cost in AUD.")

    # Allow extra fields passed via kwargs to be stored but not validated strictly here
    model_config = ConfigDict(
        extra = 'allow' # Allow other fields passed in kwargs
    )

    @field_validator('residual_value_percent_projections')
    @classmethod
    def check_residual_percentages(cls, v: ResidualValueProjections) -> ResidualValueProjections:
        """Validate that all residual value percentages are between 0.0 and 1.0."""
        if not v: # Allow empty dict if that's valid, or raise if not
            # raise ValueError("Residual value projections cannot be empty.") # Uncomment if empty is invalid
            return v # Assuming empty is ok for now
        for year, pct in v.items():
            if not (0.0 <= float(pct) <= 1.0):
                raise ValueError(f"Residual value percentage must be between 0.0 and 1.0, got {pct} for year {year}")
        return v

    # Property to access extra fields
    @property
    def additional_params(self) -> Dict[str, Any]:
        """Access extra fields provided during initialization that aren't defined model fields."""
        # In Pydantic v2, extra fields are stored in the __pydantic_extra__ attribute
        try:
            extra = getattr(self, "__pydantic_extra__", None)
            return extra if extra is not None else {}
        except (AttributeError, KeyError):
            return {}

    # Note: Removed __init__; Pydantic handles initialization based on fields.
    # Validation logic previously in __init__ is handled by Field constraints.

    @property
    @abstractmethod
    def energy_consumption_strategy(self) -> EnergyConsumptionStrategy:
        """Return the appropriate energy consumption strategy for this vehicle."""
        pass

    # Removed abstractmethod; calculation now delegates to strategy
    def calculate_energy_consumption(self, distance_km: Kilometres) -> float:
        """
        Calculate energy consumption for a given distance using the assigned strategy.

        Args:
            distance_km: Distance in kilometres

        Returns:
            Energy consumption (in native units determined by the strategy - L or kWh)
        """
        return self.energy_consumption_strategy.calculate_consumption(distance_km)

    # Removed abstractmethod; calculation is now common using the strategy
    def calculate_annual_energy_cost(
        self, annual_mileage_km: Kilometres, energy_price_aud_per_unit: AUD
    ) -> AUD:
        """
        Calculate annual energy cost (AUD) based on consumption and price per unit.

        Args:
            annual_mileage_km: Annual distance in kilometres
            energy_price_aud_per_unit: Price per unit of energy (AUD/L or AUD/kWh, matching the strategy's unit)

        Returns:
            Annual energy cost in AUD
        """
        if annual_mileage_km < 0:
             raise ValueError("Annual mileage cannot be negative.")
        if energy_price_aud_per_unit < 0:
            raise ValueError("Energy price cannot be negative.")

        consumption: float = self.calculate_energy_consumption(annual_mileage_km)
        cost_float = consumption * float(energy_price_aud_per_unit)
        return AUD(cost_float)

    def calculate_residual_value_aud(self, age_years: Years) -> AUD:
        """
        Calculate residual value (AUD) at a given age using interpolation based on projections.

        Args:
            age_years: Vehicle age in years

        Returns:
            Residual value in AUD
        """
        if age_years < 0:
            raise ValueError("Age must be non-negative.")

        # Sort the projection years (which are Years type)
        sorted_years: List[Years] = sorted(self.residual_value_percent_projections.keys())

        if not sorted_years:
            # Fallback to simple linear depreciation to 0 if no projections provided
            # This should ideally be prevented by validation upstream.
            logger.warning(f"Missing residual value projections for {self.name}. Falling back to linear depreciation.")
            effective_lifespan = max(Years(1), self.lifespan_years) # Avoid division by zero
            depreciation_rate = 1.0 / float(effective_lifespan)
            current_value_pct_float = max(0.0, 1.0 - (depreciation_rate * float(age_years)))
            return AUD(self.base_purchase_price_aud * current_value_pct_float)
            # raise ValueError("Residual value percent projections are required but missing.")

        # Find the relevant projection points for interpolation or extrapolation
        year1: Years
        year2: Years
        pct1: Percentage
        pct2: Percentage

        if age_years <= sorted_years[0]:
            # Before the first projection point: Interpolate between purchase price (year 0, 100%) and the first point
            year1, pct1 = Years(0), Percentage(1.0)
            year2, pct2 = sorted_years[0], self.residual_value_percent_projections[sorted_years[0]]
        elif age_years >= sorted_years[-1]:
            # After the last projection point: Use the last point's value
            # Or could extrapolate, but holding the last value is safer.
            return AUD(self.base_purchase_price_aud * float(self.residual_value_percent_projections[sorted_years[-1]]))
        else:
            # Between two projection points: Interpolate
            # Find the two points surrounding the age
            found = False
            for i in range(len(sorted_years) - 1):
                if sorted_years[i] <= age_years < sorted_years[i+1]:
                    year1, pct1 = sorted_years[i], self.residual_value_percent_projections[sorted_years[i]]
                    year2, pct2 = sorted_years[i+1], self.residual_value_percent_projections[sorted_years[i+1]]
                    found = True
                    break
            if not found:
                # Should not happen if age_years is within the overall range and < last point
                 logger.error(f"Logic error in residual value interpolation for age {age_years} and projections {self.residual_value_percent_projections}. Falling back.")
                 return AUD(self.base_purchase_price_aud * float(self.residual_value_percent_projections[sorted_years[-1]])) # Fallback

        # Linear interpolation: pct = pct1 + (age_years - year1) * (pct2 - pct1) / (year2 - year1)
        # Avoid division by zero if years are the same (shouldn't happen with sorted distinct years)
        current_value_pct_float: float
        if year2 == year1:
            current_value_pct_float = float(pct1) # or pct2, they should be the same
        else:
            current_value_pct_float = float(pct1) + (float(age_years) - float(year1)) * (float(pct2) - float(pct1)) / (float(year2) - float(year1))

        # Ensure percentage is within [0, 1] bounds
        current_value_pct_float = max(0.0, min(1.0, current_value_pct_float))

        return AUD(self.base_purchase_price_aud * current_value_pct_float)

    @property
    @abstractmethod
    def maintenance_strategy(self) -> MaintenanceStrategy:
        """Return the appropriate maintenance cost strategy for this vehicle."""
        pass


class ElectricVehicle(Vehicle):
    """Electric vehicle implementation using Pydantic."""

    battery_capacity_kwh: KWH = Field(..., gt=0)
    energy_consumption_kwh_per_km: KWHPerKM = Field(..., gt=0)
    battery_warranty_years: Years = Field(default=Years(8), ge=0)
    # EV Specific Cost/Parameter fields
    # Use CalendarYear as key and AUD as value
    battery_pack_cost_aud_per_kwh_projections: BatteryCostProjections = Field(..., description="Projected battery pack cost per kWh by year (e.g., {2025: 170, 2030: 100})")
    battery_cycle_life: int = Field(default=1500, gt=0) # Typical cycles
    battery_depth_of_discharge_percent: Percentage = Field(default=Percentage(80.0), ge=0, le=100.0)
    charging_efficiency_percent: Percentage = Field(default=Percentage(90.0), gt=0, le=100.0)
    # Use Decimal for rate
    purchase_price_annual_decrease_rate_real: Decimal = Field(default=Decimal(0.0), description="Annual real decrease rate for purchase price (e.g., 0.02 for 2%)", ge=0)

    # Removed __init__, using Pydantic fields and inheriting from Vehicle
    _strategy_instance: Optional[ElectricConsumptionStrategy] = PrivateAttr(default=None) # Cache strategy instance

    @property
    def energy_consumption_strategy(self) -> ElectricConsumptionStrategy:
        """Return the electric consumption strategy."""
        # Create strategy instance on first access after validation
        if self._strategy_instance is None:
            self._strategy_instance = ElectricConsumptionStrategy(self.energy_consumption_kwh_per_km)
        return self._strategy_instance

    # Removed calculate_energy_consumption - handled by base class + strategy
    # Removed calculate_annual_energy_cost - handled by base class + strategy

    def calculate_battery_degradation_factor(self, age_years: Years, total_mileage_km: Kilometres) -> float:
        """
        Estimate battery capacity degradation factor (remaining capacity / original capacity).
        Uses a simplified model combining cycle and calendar aging.

        Args:
            age_years: Battery age in years
            total_mileage_km: Total kilometres driven

        Returns:
            Remaining capacity as a fraction of original (0.0 to 1.0)
        """
        if age_years < 0 or total_mileage_km < 0:
            raise ValueError("Age and mileage must be non-negative.")

        # Use actual cycle life from instance
        equivalent_full_cycles_life: int = self.battery_cycle_life
        # Assume battery calendar life matches vehicle lifespan for simplicity
        calendar_life_years: Years = self.lifespan_years

        # Constants for degradation model (could be refined/made parameters)
        CYCLE_AGING_WEIGHT: float = 0.7         # Weighting for cycle-based degradation
        CALENDAR_AGING_WEIGHT: float = 0.3      # Weighting for time-based degradation
        END_OF_LIFE_THRESHOLD_LOSS_FRACTION: float = 0.2 # Capacity loss representing end-of-life (e.g., 80% remaining -> 0.2 loss)

        # Calculate equivalent full cycles, considering DoD and charging efficiency
        # Energy drawn *from the battery* per km driven
        # Need to account for charging losses when calculating total energy throughput *into* the battery
        charging_efficiency_frac: float = float(self.charging_efficiency_percent) / 100.0
        if charging_efficiency_frac == 0: return 1.0 # Avoid division by zero

        energy_drawn_from_grid_per_km: KWHPerKM = KWHPerKM(self.energy_consumption_kwh_per_km / charging_efficiency_frac)
        total_energy_throughput_kwh: KWH = KWH(float(total_mileage_km) * float(energy_drawn_from_grid_per_km))

        # Usable capacity per cycle depends on DoD
        depth_of_discharge_frac: float = float(self.battery_depth_of_discharge_percent) / 100.0
        usable_capacity_per_cycle_kwh: KWH = KWH(self.battery_capacity_kwh * depth_of_discharge_frac)
        if usable_capacity_per_cycle_kwh == 0: return 1.0 # Avoid division by zero if DoD or capacity is 0

        equivalent_cycles: float = float(total_energy_throughput_kwh) / float(usable_capacity_per_cycle_kwh)

        # Calculate degradation factors (normalized to 1.0 at end-of-life definition)
        # Ensure denominators are not zero
        cycle_degradation: float = min(1.0, equivalent_cycles / equivalent_full_cycles_life) if equivalent_full_cycles_life > 0 else 0.0
        calendar_degradation: float = min(1.0, float(age_years) / float(calendar_life_years)) if calendar_life_years > 0 else 0.0

        # Combine degradations using weights
        total_normalized_degradation: float = (CYCLE_AGING_WEIGHT * cycle_degradation +
                                        CALENDAR_AGING_WEIGHT * calendar_degradation)

        # Calculate remaining capacity fraction (1.0 = new, lower means degraded)
        # Model assumes degradation scales linearly towards the EOL threshold loss
        remaining_capacity_fraction: float = max(0.0, 1.0 - (total_normalized_degradation * END_OF_LIFE_THRESHOLD_LOSS_FRACTION))

        return remaining_capacity_fraction

    _maintenance_strategy_instance: Optional[ElectricMaintenanceStrategy] = PrivateAttr(default=None)

    @property
    def maintenance_strategy(self) -> ElectricMaintenanceStrategy:
        """Return the electric maintenance strategy."""
        if self._maintenance_strategy_instance is None:
            self._maintenance_strategy_instance = ElectricMaintenanceStrategy()
        return self._maintenance_strategy_instance


class DieselVehicle(Vehicle):
    """Diesel vehicle implementation using Pydantic."""

    fuel_consumption_l_per_100km: LitersPer100KM = Field(..., gt=0)
    co2_emission_factor_kg_per_l: float = Field(..., ge=0) # kg CO2e per litre

    # Store L/km for convenience, calculate after validation
    _fuel_consumption_l_per_km: float = PrivateAttr(default=0.0)
    _strategy_instance: Optional[DieselConsumptionStrategy] = PrivateAttr(default=None) # Cache strategy instance

    @model_validator(mode='after') # Use model_validator for Pydantic v2
    def _calculate_l_per_km(self) -> 'DieselVehicle':
        if self.fuel_consumption_l_per_100km is not None: # Should be validated by Field already
            # Convert L/100km to L/km (float)
            self._fuel_consumption_l_per_km = float(self.fuel_consumption_l_per_100km) / 100.0
        return self

    # Getter property for consistency
    @property
    def fuel_consumption_l_per_km(self) -> float:
        # Ensure the value is calculated if accessed before validation (e.g., direct dict init)
        if self._fuel_consumption_l_per_km == 0.0 and self.fuel_consumption_l_per_100km > 0:
            self._fuel_consumption_l_per_km = float(self.fuel_consumption_l_per_100km) / 100.0
        return self._fuel_consumption_l_per_km

    # Removed __init__, using Pydantic fields and inheriting from Vehicle

    @property
    def energy_consumption_strategy(self) -> DieselConsumptionStrategy:
        """Return the diesel consumption strategy."""
        # Create strategy instance on first access after validation
        # Assumes _calculate_l_per_km validator has run and set the private attr
        if self._strategy_instance is None:
             l_per_km = self.fuel_consumption_l_per_km # Use property to ensure calculation
             if l_per_km == 0.0 and self.fuel_consumption_l_per_100km > 0:
                 # Should not happen if validator works, but as fallback
                 l_per_km = float(self.fuel_consumption_l_per_100km) / 100.0
                 self._fuel_consumption_l_per_km = l_per_km # Update private attr

             self._strategy_instance = DieselConsumptionStrategy(l_per_km)
        return self._strategy_instance

    # Removed calculate_energy_consumption - handled by base class + strategy
    # Removed calculate_annual_energy_cost - handled by base class + strategy

    _maintenance_strategy_instance: Optional[DieselMaintenanceStrategy] = PrivateAttr(default=None)

    @property
    def maintenance_strategy(self) -> DieselMaintenanceStrategy:
        """Return the diesel maintenance strategy."""
        if self._maintenance_strategy_instance is None:
            self._maintenance_strategy_instance = DieselMaintenanceStrategy()
        return self._maintenance_strategy_instance
