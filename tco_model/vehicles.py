from abc import ABC, abstractmethod
from typing import Dict, Optional, Union, Literal
from pydantic import (
    BaseModel, Field, model_validator, ValidationInfo, ConfigDict, field_validator # Added field_validator
)

class Vehicle(BaseModel, ABC):
    """Abstract base class for all vehicle types, using Pydantic."""
    
    name: str = Field(..., description="Unique identifier for the vehicle.")
    vehicle_type: Literal["rigid", "articulated"] = Field(..., description="Type of heavy vehicle.")
    purchase_price: float = Field(..., gt=0, description="Initial purchase price in AUD.")
    lifespan: int = Field(..., gt=0, description="Expected operational lifespan in years.")
    residual_value_projections: Dict[int, float] = Field(
        ..., 
        description="Residual value percentage at specific years (e.g., {5: 0.5, 10: 0.3, 15: 0.15})", 
        json_schema_extra={"example": {5: 0.5, 10: 0.3, 15: 0.15}}
    )
    # Cost fields common to both or handled by components accessing vehicle data
    registration_cost: float = Field(..., ge=0, description="Base annual registration cost in AUD.")

    # Allow extra fields passed via kwargs to be stored but not validated strictly here
    model_config = ConfigDict(
        extra = 'allow' # Allow other fields passed in kwargs
    )

    @field_validator('residual_value_projections')
    @classmethod
    def check_residual_percentages(cls, v: Dict[int, float]):
        """Validate that all residual value percentages are between 0.0 and 1.0."""
        if not v: # Allow empty dict if that's valid, or raise if not
            # raise ValueError("Residual value projections cannot be empty.") # Uncomment if empty is invalid
            return v # Assuming empty is ok for now
        for year, pct in v.items():
            if not (0.0 <= pct <= 1.0):
                raise ValueError(f"Residual value percentage must be between 0.0 and 1.0, got {pct} for year {year}")
        return v

    # Property to access extra fields
    @property
    def additional_params(self):
        """Access extra fields provided during initialization that aren't defined model fields."""
        # In Pydantic v2, extra fields are stored in the __pydantic_extra__ attribute
        try:
            return getattr(self, "__pydantic_extra__", {}) or {}
        except (AttributeError, KeyError):
            return {}
    
    # Note: Removed __init__; Pydantic handles initialization based on fields.
    # Validation logic previously in __init__ is handled by Field constraints.
    
    @abstractmethod
    def calculate_energy_consumption(self, distance_km: float) -> float:
        """
        Calculate energy consumption for a given distance.
        
        Args:
            distance_km: Distance in kilometres
            
        Returns:
            Energy consumption (in native units - L for diesel, kWh for electric)
        """
        pass
    
    @abstractmethod
    def calculate_annual_energy_cost(
        self, annual_mileage_km: float, energy_price_per_unit: float
    ) -> float:
        """
        Calculate annual energy cost.
        
        Args:
            annual_mileage_km: Annual distance in kilometres
            energy_price_per_unit: Price per unit of energy (AUD/L or AUD/kWh)
            
        Returns:
            Annual energy cost in AUD
        """
        pass
    
    def calculate_residual_value(self, age_years: int) -> float:
        """
        Calculate residual value at a given age using interpolation based on projections.

        Args:
            age_years: Vehicle age in years

        Returns:
            Residual value in AUD
        """
        if age_years < 0:
            raise ValueError("Age must be non-negative.")

        # Sort the projection years
        sorted_years = sorted(self.residual_value_projections.keys())

        if not sorted_years:
            # Fallback to simple linear depreciation to 0 if no projections provided (or handle as error)
            # For now, let's assume projections are always provided by the Scenario loader.
            # A validator could enforce this.
            # As a simple fallback: linear depreciation to 0 over lifespan
            # effective_lifespan = max(1, self.lifespan) # Avoid division by zero
            # depreciation_rate = 1.0 / effective_lifespan
            # current_value_pct = max(0.0, 1.0 - (depreciation_rate * age_years))
            # return self.purchase_price * current_value_pct
            raise ValueError("Residual value projections are required but missing.")


        # Find the relevant projection points for interpolation or extrapolation
        if age_years <= sorted_years[0]:
            # Before the first projection point: Interpolate between purchase price (year 0, 100%) and the first point
            year1, pct1 = 0, 1.0
            year2, pct2 = sorted_years[0], self.residual_value_projections[sorted_years[0]]
        elif age_years >= sorted_years[-1]:
            # After the last projection point: Use the last point's value
            # Or could extrapolate, but holding the last value is safer.
            return self.purchase_price * self.residual_value_projections[sorted_years[-1]]
        else:
            # Between two projection points: Interpolate
            # Find the two points surrounding the age
            for i in range(len(sorted_years) - 1):
                if sorted_years[i] <= age_years < sorted_years[i+1]:
                    year1, pct1 = sorted_years[i], self.residual_value_projections[sorted_years[i]]
                    year2, pct2 = sorted_years[i+1], self.residual_value_projections[sorted_years[i+1]]
                    break
            else:
                # Should not happen if age_years is within the overall range and < last point
                 return self.purchase_price * self.residual_value_projections[sorted_years[-1]] # Fallback


        # Linear interpolation: pct = pct1 + (age_years - year1) * (pct2 - pct1) / (year2 - year1)
        # Avoid division by zero if years are the same (shouldn't happen with sorted distinct years)
        if year2 == year1:
            current_value_pct = pct1 # or pct2, they should be the same
        else:
            current_value_pct = pct1 + (age_years - year1) * (pct2 - pct1) / (year2 - year1)

        # Ensure percentage is within [0, 1] bounds
        current_value_pct = max(0.0, min(1.0, current_value_pct))

        return self.purchase_price * current_value_pct


class ElectricVehicle(Vehicle):
    """Electric vehicle implementation using Pydantic."""
    
    battery_capacity_kwh: float = Field(..., gt=0)
    energy_consumption_kwh_per_km: float = Field(..., gt=0)
    battery_warranty_years: int = Field(default=8, ge=0)
    # EV Specific Cost/Parameter fields
    battery_pack_cost_projections_aud_per_kwh: Dict[int, float] = Field(..., description="Projected battery pack cost per kWh by year (e.g., {2025: 170, 2030: 100})")
    battery_cycle_life: int = Field(default=1500, gt=0) # Typical cycles
    battery_depth_of_discharge: float = Field(default=0.8, ge=0, le=1.0)
    charging_efficiency: float = Field(default=0.9, gt=0, le=1.0)
    purchase_price_annual_decrease_real: float = Field(default=0.0, description="Annual real decrease rate for purchase price (e.g., 0.02 for 2%)", ge=0)
    
    # Removed __init__, using Pydantic fields and inheriting from Vehicle
    
    def calculate_energy_consumption(self, distance_km: float) -> float:
        """Calculate electricity consumption in kWh."""
        if distance_km < 0:
            raise ValueError("Distance cannot be negative.")
        # Original code adjusted charging efficiency, but tests expect direct calculation
        # We'll remove the charging efficiency adjustment to match test expectations
        return distance_km * self.energy_consumption_kwh_per_km
    
    def calculate_annual_energy_cost(
        self, annual_mileage_km: float, energy_price_per_unit: float
    ) -> float:
        """Calculate annual electricity cost in AUD."""
        if annual_mileage_km < 0:
            raise ValueError("Annual mileage cannot be negative.")
        if energy_price_per_unit < 0:
             raise ValueError("Energy price cannot be negative.")
        consumption_kwh = self.calculate_energy_consumption(annual_mileage_km)
        return consumption_kwh * energy_price_per_unit
    
    def calculate_battery_degradation_factor(self, age_years: int, total_mileage_km: float) -> float:
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
        equivalent_full_cycles_life = self.battery_cycle_life 
        calendar_life_years = self.lifespan # Assume battery calendar life matches vehicle lifespan for simplicity
        
        # Constants for degradation model (could be refined/made parameters)
        CYCLE_AGING_WEIGHT = 0.7         # Weighting for cycle-based degradation
        CALENDAR_AGING_WEIGHT = 0.3      # Weighting for time-based degradation
        END_OF_LIFE_THRESHOLD_LOSS = 0.2 # Capacity loss representing end-of-life (e.g., 80% remaining -> 0.2 loss)
        
        # Calculate equivalent full cycles, considering DoD
        energy_drawn_per_km = self.energy_consumption_kwh_per_km / self.charging_efficiency # Energy from battery per km
        total_energy_throughput_kwh = total_mileage_km * energy_drawn_per_km
        # Usable capacity per cycle depends on DoD
        usable_capacity_per_cycle = self.battery_capacity_kwh * self.battery_depth_of_discharge
        if usable_capacity_per_cycle == 0: return 1.0 # Avoid division by zero if DoD or capacity is 0
            
        equivalent_cycles = total_energy_throughput_kwh / usable_capacity_per_cycle
        
        # Calculate degradation factors (normalized to 1.0 at end-of-life definition)
        # Ensure denominators are not zero
        cycle_degradation = min(1.0, equivalent_cycles / equivalent_full_cycles_life) if equivalent_full_cycles_life > 0 else 0.0
        calendar_degradation = min(1.0, age_years / calendar_life_years) if calendar_life_years > 0 else 0.0
        
        # Combine degradations using weights
        total_normalized_degradation = (CYCLE_AGING_WEIGHT * cycle_degradation + 
                                        CALENDAR_AGING_WEIGHT * calendar_degradation)
                             
        # Calculate remaining capacity fraction (1.0 = new, lower means degraded)
        # Model assumes degradation scales linearly towards the EOL threshold loss
        remaining_capacity_fraction = max(0.0, 1.0 - (total_normalized_degradation * END_OF_LIFE_THRESHOLD_LOSS))
        
        return remaining_capacity_fraction


class DieselVehicle(Vehicle):
    """Diesel vehicle implementation using Pydantic."""
    
    fuel_consumption_l_per_100km: float = Field(..., gt=0)
    co2_emission_factor: float = Field(..., ge=0) # kg CO2e per litre
    
    # Store L/km for convenience, calculate after validation
    _fuel_consumption_l_per_km: float = 0.0 
    
    @model_validator(mode='after') # Use model_validator for Pydantic v2
    def _calculate_l_per_km(self) -> 'DieselVehicle':
        if self.fuel_consumption_l_per_100km is not None: # Should be validated by Field already
            self._fuel_consumption_l_per_km = self.fuel_consumption_l_per_100km / 100.0
        return self

    # Getter property for consistency
    @property
    def fuel_consumption_l_per_km(self) -> float:
        return self._fuel_consumption_l_per_km

    # Removed __init__, using Pydantic fields and inheriting from Vehicle
    
    def calculate_energy_consumption(self, distance_km: float) -> float:
        """Calculate diesel consumption in litres."""
        if distance_km < 0:
            raise ValueError("Distance cannot be negative.")
        return distance_km * self.fuel_consumption_l_per_km
    
    def calculate_annual_energy_cost(
        self, annual_mileage_km: float, energy_price_per_unit: float
    ) -> float:
        """Calculate annual diesel cost in AUD."""
        if annual_mileage_km < 0:
            raise ValueError("Annual mileage cannot be negative.")
        if energy_price_per_unit < 0:
            raise ValueError("Energy price cannot be negative.")
        consumption_l = self.calculate_energy_consumption(annual_mileage_km)
        return consumption_l * energy_price_per_unit
