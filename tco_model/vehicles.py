from abc import ABC, abstractmethod
from typing import Dict, Optional, Union

class Vehicle(ABC):
    """Abstract base class for all vehicle types."""
    
    def __init__(
        self, 
        name: str,
        purchase_price: float,
        annual_mileage: float, # This might be better handled at the scenario level
        lifespan: int = 15, # Default lifespan, can be scenario-specific
        residual_value_pct: float = 0.1, # Base residual value pct
        **kwargs
    ):
        """
        Initialize a vehicle.
        
        Args:
            name: Vehicle name/model
            purchase_price: Purchase price (AUD)
            annual_mileage: Annual kilometres driven (Consider moving to Scenario)
            lifespan: Expected vehicle lifespan (years)
            residual_value_pct: Residual value percentage at end of life
        """
        if purchase_price <= 0:
            raise ValueError("Purchase price must be positive.")
        if lifespan <= 0:
            raise ValueError("Lifespan must be positive.")
        if not 0 <= residual_value_pct <= 1:
            raise ValueError("Residual value percentage must be between 0 and 1.")
            
        self.name = name
        self.purchase_price = purchase_price
        # self.annual_mileage = annual_mileage # Prefer getting this from scenario
        self.lifespan = lifespan
        self.residual_value_pct = residual_value_pct
        
        # Store additional parameters safely
        self.additional_params = kwargs
    
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
        Calculate residual value at a given age.
        Assumes linear depreciation towards the final residual value percentage.
        
        Args:
            age_years: Vehicle age in years
            
        Returns:
            Residual value in AUD
        """
        if age_years < 0:
            raise ValueError("Age must be non-negative.")
        if age_years >= self.lifespan:
            return self.purchase_price * self.residual_value_pct
            
        # Linear depreciation model for simplicity
        depreciation_rate = (1.0 - self.residual_value_pct) / self.lifespan
        current_value_pct = 1.0 - (depreciation_rate * age_years)
        return self.purchase_price * current_value_pct


class ElectricVehicle(Vehicle):
    """Electric vehicle implementation."""
    
    def __init__(
        self,
        name: str,
        purchase_price: float,
        battery_capacity_kwh: float,
        energy_consumption_kwh_per_km: float,
        battery_warranty_years: int = 8,
        annual_mileage: float = 80000, # Default, should come from scenario
        lifespan: int = 15,
        residual_value_pct: float = 0.1,
        **kwargs
    ):
        """
        Initialize an electric vehicle.
        
        Args:
            name: Vehicle name/model
            purchase_price: Purchase price (AUD)
            battery_capacity_kwh: Battery capacity (kWh)
            energy_consumption_kwh_per_km: Energy consumption (kWh/km)
            battery_warranty_years: Battery warranty period (years)
            annual_mileage: Annual kilometres driven (Consider moving to Scenario)
            lifespan: Expected vehicle lifespan (years)
            residual_value_pct: Residual value percentage at end of life
        """
        super().__init__(
            name=name,
            purchase_price=purchase_price,
            annual_mileage=annual_mileage,
            lifespan=lifespan,
            residual_value_pct=residual_value_pct,
            **kwargs
        )
        if battery_capacity_kwh <= 0:
            raise ValueError("Battery capacity must be positive.")
        if energy_consumption_kwh_per_km <= 0:
            raise ValueError("Energy consumption must be positive.")
        if battery_warranty_years < 0:
            raise ValueError("Battery warranty cannot be negative.")
            
        self.battery_capacity_kwh = battery_capacity_kwh
        self.energy_consumption_kwh_per_km = energy_consumption_kwh_per_km
        self.battery_warranty_years = battery_warranty_years
    
    def calculate_energy_consumption(self, distance_km: float) -> float:
        """Calculate electricity consumption in kWh."""
        if distance_km < 0:
            raise ValueError("Distance cannot be negative.")
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
            
        # Constants for degradation model (can be refined/made parameters)
        EQUIVALENT_FULL_CYCLES_LIFE = 1500 # Typical cycles before significant degradation
        CALENDAR_LIFE_YEARS = 15         # Typical calendar life
        CYCLE_AGING_WEIGHT = 0.7         # Weighting for cycle-based degradation
        CALENDAR_AGING_WEIGHT = 0.3      # Weighting for time-based degradation
        END_OF_LIFE_THRESHOLD = 0.2     # Capacity loss representing end-of-life (e.g., 80% remaining)
        
        # Calculate equivalent full cycles
        total_energy_throughput_kwh = total_mileage_km * self.energy_consumption_kwh_per_km
        equivalent_cycles = total_energy_throughput_kwh / self.battery_capacity_kwh
        
        # Calculate degradation factors (normalized to 1.0 at end-of-life definition)
        cycle_degradation = min(1.0, equivalent_cycles / EQUIVALENT_FULL_CYCLES_LIFE)
        calendar_degradation = min(1.0, age_years / CALENDAR_LIFE_YEARS)
        
        # Combine degradations using weights
        total_degradation = (CYCLE_AGING_WEIGHT * cycle_degradation + 
                             CALENDAR_AGING_WEIGHT * calendar_degradation)
                             
        # Calculate remaining capacity fraction (1.0 = new, lower means degraded)
        # Model assumes degradation scales linearly towards the EOL threshold loss
        remaining_capacity_fraction = max(0.0, 1.0 - (total_degradation * END_OF_LIFE_THRESHOLD))
        
        return remaining_capacity_fraction


class DieselVehicle(Vehicle):
    """Diesel vehicle implementation."""
    
    def __init__(
        self,
        name: str,
        purchase_price: float,
        fuel_consumption_l_per_100km: float,
        co2_emission_factor: float, # kg CO2e per litre
        annual_mileage: float = 80000, # Default, should come from scenario
        lifespan: int = 15,
        residual_value_pct: float = 0.1,
        **kwargs
    ):
        """
        Initialize a diesel vehicle.
        
        Args:
            name: Vehicle name/model
            purchase_price: Purchase price (AUD)
            fuel_consumption_l_per_100km: Fuel consumption (L/100km)
            co2_emission_factor: CO2 emission factor (kg CO2e/L)
            annual_mileage: Annual kilometres driven (Consider moving to Scenario)
            lifespan: Expected vehicle lifespan (years)
            residual_value_pct: Residual value percentage at end of life
        """
        super().__init__(
            name=name,
            purchase_price=purchase_price,
            annual_mileage=annual_mileage,
            lifespan=lifespan,
            residual_value_pct=residual_value_pct,
            **kwargs
        )
        if fuel_consumption_l_per_100km <= 0:
            raise ValueError("Fuel consumption must be positive.")
        if co2_emission_factor < 0:
            raise ValueError("CO2 emission factor cannot be negative.")
            
        self.fuel_consumption_l_per_100km = fuel_consumption_l_per_100km
        self.fuel_consumption_l_per_km = fuel_consumption_l_per_100km / 100.0
        self.co2_emission_factor = co2_emission_factor # Store the value
    
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
