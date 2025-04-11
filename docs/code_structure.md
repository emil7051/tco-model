# Code Structure Plan

This document outlines the directory structure and file organization for the Australian Heavy Vehicle TCO Modeller, providing a clear roadmap for implementation.

## Directory Structure

```
aus-heavy-vehicle-tco/
├── app.py                     # Main Streamlit application entry point
├── requirements.txt           # Project dependencies
├── setup.py                   # Package setup for installation
├── README.md                  # Project overview and documentation
├── tco_model/                 # Core TCO calculation package
│   ├── __init__.py           
│   ├── model.py               # TCO calculator implementation
│   ├── vehicles.py            # Vehicle classes (abstract & concrete)
│   ├── components.py          # Cost component implementations
│   ├── scenarios.py           # Scenario management
│   └── validators.py          # Input validation utilities
├── config/                    # Configuration and default data
│   ├── constants.py           # System-wide constants
│   ├── defaults/
│   │   ├── vehicle_specs.yaml # Default vehicle specifications
│   │   ├── energy_prices.yaml # Energy price projections
│   │   ├── battery_costs.yaml # Battery cost projections
│   │   └── incentives.yaml    # Policy incentives data
│   └── scenarios/
│       ├── urban_delivery.yaml # Predefined scenario
│       └── long_haul.yaml      # Predefined scenario
├── ui/                         # UI-related modules
│   ├── __init__.py
│   ├── layout.py              # Page layout functions
│   ├── inputs.py              # Input collection components
│   ├── outputs.py             # Result display components
│   └── state.py               # Session state management
├── utils/                     # Utility functions
│   ├── __init__.py
│   ├── plotting.py            # Chart generation functions
│   ├── financial.py           # Financial calculation utilities
│   ├── data_handlers.py       # Data loading/parsing
│   └── conversions.py         # Unit conversion utilities
├── docs/                      # Documentation
│   ├── architecture.md        # System architecture
│   ├── model_design.md        # Model design details
│   ├── ui_design.md           # UI design guidelines
│   └── development.md         # Development guidelines
└── tests/                     # Test suite
    ├── __init__.py
    ├── test_model.py          # Tests for TCO calculator
    ├── test_vehicles.py       # Tests for vehicle classes
    ├── test_components.py     # Tests for cost components
    └── test_scenarios.py      # Tests for scenarios
```

## File Responsibilities

### Core Application Files

#### `app.py`
- Main entry point for Streamlit application
- Orchestrates the overall application flow
- Integrates UI components and model calculations

```python
# app.py
import streamlit as st
from ui.layout import create_layout
from ui.inputs import create_input_sidebar
from ui.outputs import display_results
from ui.state import initialize_session_state
from tco_model.model import TCOCalculator
from tco_model.scenarios import Scenario

def main():
    # Setup page configuration
    st.set_page_config(
        page_title="Australian Heavy Vehicle TCO Modeller",
        page_icon="🚚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Create page layout
    create_layout()
    
    # Create input sidebar and collect user inputs
    scenario_params = create_input_sidebar()
    
    # Create scenario from inputs
    scenario = Scenario(**scenario_params)
    
    # Calculate TCO
    calculator = TCOCalculator()
    results = calculator.calculate(scenario)
    
    # Display results
    display_results(results)

if __name__ == "__main__":
    main()
```

#### `requirements.txt`
- Lists all project dependencies with version constraints

```
# requirements.txt
streamlit>=1.24.0
pandas>=1.5.3
numpy>=1.24.3
plotly>=5.14.1
pydantic>=2.0.0
pyyaml>=6.0
openpyxl>=3.1.2
pytest>=7.3.1
```

### TCO Model Package

#### `tco_model/model.py`
- Implements the `TCOCalculator` class
- Orchestrates the TCO calculation process
- Manages time-series calculations and discounting

```python
# tco_model/model.py
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple

from .vehicles import Vehicle, ElectricVehicle, DieselVehicle
from .components import (
    AcquisitionCost, EnergyCost, MaintenanceCost, 
    InfrastructureCost, BatteryReplacementCost, 
    InsuranceCost, RegistrationCost, ResidualValue
)
from .scenarios import Scenario

class TCOCalculator:
    """Calculates Total Cost of Ownership for vehicles over a specified period."""
    
    def __init__(self):
        """Initialize the TCO Calculator."""
        self.components = {
            'acquisition': AcquisitionCost(),
            'energy': EnergyCost(),
            'maintenance': MaintenanceCost(),
            'infrastructure': InfrastructureCost(),
            'battery_replacement': BatteryReplacementCost(),
            'insurance': InsuranceCost(),
            'registration': RegistrationCost(),
            'residual_value': ResidualValue()
        }
    
    def calculate(self, scenario: Scenario) -> Dict:
        """
        Calculate TCO for the given scenario.
        
        Args:
            scenario: The scenario containing all input parameters
            
        Returns:
            Dictionary containing all TCO results and metrics
        """
        # Create appropriate vehicle instances
        electric_vehicle = ElectricVehicle(
            name=scenario.electric_vehicle_name,
            purchase_price=scenario.electric_vehicle_price,
            # ... other parameters
        )
        
        diesel_vehicle = DieselVehicle(
            name=scenario.diesel_vehicle_name,
            purchase_price=scenario.diesel_vehicle_price,
            # ... other parameters
        )
        
        # Calculate annual costs for each vehicle
        electric_annual_costs = self._calculate_annual_costs(
            electric_vehicle, scenario, is_electric=True
        )
        
        diesel_annual_costs = self._calculate_annual_costs(
            diesel_vehicle, scenario, is_electric=False
        )
        
        # Calculate total costs
        electric_total = self._calculate_total_costs(electric_annual_costs, scenario)
        diesel_total = self._calculate_total_costs(diesel_annual_costs, scenario)
        
        # Calculate comparative metrics
        parity_year = self._find_parity_year(electric_total, diesel_total)
        lcod_electric = self._calculate_lcod(electric_total, scenario.annual_mileage)
        lcod_diesel = self._calculate_lcod(diesel_total, scenario.annual_mileage)
        
        # Compile and return results
        return {
            'electric_annual': electric_annual_costs,
            'diesel_annual': diesel_annual_costs,
            'electric_total': electric_total,
            'diesel_total': diesel_total,
            'parity_year': parity_year,
            'lcod_electric': lcod_electric,
            'lcod_diesel': lcod_diesel,
            # Additional metrics and analysis results
        }
    
    def _calculate_annual_costs(
        self, vehicle: Vehicle, scenario: Scenario, is_electric: bool
    ) -> pd.DataFrame:
        """Calculate annual costs for a vehicle."""
        # Implementation details...
        pass
    
    def _calculate_total_costs(
        self, annual_costs: pd.DataFrame, scenario: Scenario
    ) -> pd.DataFrame:
        """Apply discounting and calculate total costs."""
        # Implementation details...
        pass
    
    def _find_parity_year(
        self, electric_costs: pd.DataFrame, diesel_costs: pd.DataFrame
    ) -> Optional[int]:
        """Find the year when electric TCO becomes lower than diesel TCO."""
        # Implementation details...
        pass
    
    def _calculate_lcod(
        self, total_costs: pd.DataFrame, annual_mileage: float
    ) -> float:
        """Calculate Levelized Cost of Driving (per km)."""
        # Implementation details...
        pass
    
    # Additional helper methods
```

#### `tco_model/vehicles.py`
- Defines vehicle class hierarchy
- Implements vehicle-specific calculations

```python
# tco_model/vehicles.py
from abc import ABC, abstractmethod
from typing import Dict, Optional, Union

class Vehicle(ABC):
    """Abstract base class for all vehicle types."""
    
    def __init__(
        self, 
        name: str,
        purchase_price: float,
        annual_mileage: float,
        lifespan: int,
        **kwargs
    ):
        """
        Initialize a vehicle.
        
        Args:
            name: Vehicle name/model
            purchase_price: Purchase price (AUD)
            annual_mileage: Annual kilometres driven
            lifespan: Expected vehicle lifespan (years)
        """
        self.name = name
        self.purchase_price = purchase_price
        self.annual_mileage = annual_mileage
        self.lifespan = lifespan
        
        # Store additional parameters
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @abstractmethod
    def calculate_energy_consumption(self, distance: float) -> float:
        """
        Calculate energy consumption for a given distance.
        
        Args:
            distance: Distance in kilometres
            
        Returns:
            Energy consumption (in native units - L for diesel, kWh for electric)
        """
        pass
    
    @abstractmethod
    def calculate_energy_cost(self, distance: float, energy_price: float) -> float:
        """
        Calculate energy cost for a given distance.
        
        Args:
            distance: Distance in kilometres
            energy_price: Price per unit of energy (AUD/L or AUD/kWh)
            
        Returns:
            Energy cost in AUD
        """
        pass
    
    def calculate_residual_value(self, age: int) -> float:
        """
        Calculate residual value at a given age.
        
        Args:
            age: Vehicle age in years
            
        Returns:
            Residual value in AUD
        """
        # Default implementation - override in subclasses if needed
        residual_percentage = max(0, 1.0 - (age / self.lifespan) * 0.9)
        return self.purchase_price * residual_percentage


class ElectricVehicle(Vehicle):
    """Electric vehicle implementation."""
    
    def __init__(
        self,
        name: str,
        purchase_price: float,
        annual_mileage: float,
        lifespan: int,
        battery_capacity: float,
        energy_consumption: float,
        battery_warranty: int = 8,
        **kwargs
    ):
        """
        Initialize an electric vehicle.
        
        Args:
            name: Vehicle name/model
            purchase_price: Purchase price (AUD)
            annual_mileage: Annual kilometres driven
            lifespan: Expected vehicle lifespan (years)
            battery_capacity: Battery capacity (kWh)
            energy_consumption: Energy consumption (kWh/km)
            battery_warranty: Battery warranty period (years)
        """
        super().__init__(
            name=name,
            purchase_price=purchase_price,
            annual_mileage=annual_mileage,
            lifespan=lifespan,
            **kwargs
        )
        self.battery_capacity = battery_capacity
        self.energy_consumption = energy_consumption
        self.battery_warranty = battery_warranty
    
    def calculate_energy_consumption(self, distance: float) -> float:
        """Calculate electricity consumption in kWh."""
        return distance * self.energy_consumption
    
    def calculate_energy_cost(self, distance: float, energy_price: float) -> float:
        """Calculate electricity cost in AUD."""
        consumption = self.calculate_energy_consumption(distance)
        return consumption * energy_price
    
    def calculate_battery_degradation(self, age: int, total_mileage: float) -> float:
        """
        Calculate battery capacity degradation factor.
        
        Args:
            age: Battery age in years
            total_mileage: Total kilometres driven
            
        Returns:
            Remaining capacity as a fraction of original (0-1)
        """
        # Simplified degradation model - can be refined based on real-world data
        cycle_degradation = min(1.0, total_mileage / (self.battery_capacity * 500))
        calendar_degradation = min(1.0, age / 20)
        
        # Combined degradation (typically 80% after 8 years or 160,000 km)
        remaining_capacity = 1.0 - (0.7 * cycle_degradation + 0.3 * calendar_degradation)
        return max(0.0, remaining_capacity)


class DieselVehicle(Vehicle):
    """Diesel vehicle implementation."""
    
    def __init__(
        self,
        name: str,
        purchase_price: float,
        annual_mileage: float,
        lifespan: int,
        fuel_consumption: float,
        **kwargs
    ):
        """
        Initialize a diesel vehicle.
        
        Args:
            name: Vehicle name/model
            purchase_price: Purchase price (AUD)
            annual_mileage: Annual kilometres driven
            lifespan: Expected vehicle lifespan (years)
            fuel_consumption: Fuel consumption (L/100km)
        """
        super().__init__(
            name=name,
            purchase_price=purchase_price,
            annual_mileage=annual_mileage,
            lifespan=lifespan,
            **kwargs
        )
        self.fuel_consumption = fuel_consumption
    
    def calculate_energy_consumption(self, distance: float) -> float:
        """Calculate diesel consumption in litres."""
        return distance * (self.fuel_consumption / 100.0)
    
    def calculate_energy_cost(self, distance: float, energy_price: float) -> float:
        """Calculate diesel cost in AUD."""
        consumption = self.calculate_energy_consumption(distance)
        return consumption * energy_price
```

#### `tco_model/components.py`
- Implements cost component classes
- Each component handles a specific cost category

```python
# tco_model/components.py
from abc import ABC, abstractmethod
from typing import Dict, Any

from .vehicles import Vehicle

class CostComponent(ABC):
    """Abstract base class for all cost components."""
    
    @abstractmethod
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, params: Dict[str, Any]
    ) -> float:
        """
        Calculate annual cost for a specific year.
        
        Args:
            year: Year of analysis (e.g., 2025, 2026, etc.)
            vehicle: Vehicle instance
            params: Additional parameters needed for calculation
            
        Returns:
            Annual cost for this component
        """
        pass


class AcquisitionCost(CostComponent):
    """Handles vehicle acquisition costs."""
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, params: Dict[str, Any]
    ) -> float:
        """Calculate acquisition cost for a specific year."""
        start_year = params.get('start_year', 2025)
        loan_term = params.get('loan_term', 5)
        down_payment_pct = params.get('down_payment_pct', 0.2)
        interest_rate = params.get('interest_rate', 0.07)
        
        # Only apply in first year if paying cash
        if params.get('financing_method') == 'cash':
            return vehicle.purchase_price if year == start_year else 0.0
        
        # For loan financing, calculate annual payments
        # Only apply during the loan term
        if year < start_year or year >= start_year + loan_term:
            return 0.0
            
        # Calculate loan amount
        down_payment = vehicle.purchase_price * down_payment_pct
        loan_amount = vehicle.purchase_price - down_payment
        
        # Apply first year down payment
        if year == start_year:
            return down_payment
        
        # Calculate annual loan payment (simplified)
        r = interest_rate
        n = loan_term
        annual_payment = loan_amount * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
        
        return annual_payment


class EnergyCost(CostComponent):
    """Handles energy costs (fuel/electricity)."""
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, params: Dict[str, Any]
    ) -> float:
        """Calculate energy cost for a specific year."""
        annual_mileage = params.get('annual_mileage', vehicle.annual_mileage)
        
        # Get energy price for the year
        if isinstance(vehicle, ElectricVehicle):
            energy_prices = params.get('electricity_prices', {})
            energy_price = energy_prices.get(str(year), 0.20)  # Default: $0.20/kWh
        else:  # Diesel
            energy_prices = params.get('diesel_prices', {})
            energy_price = energy_prices.get(str(year), 1.70)  # Default: $1.70/L
        
        # Calculate energy cost
        return vehicle.calculate_energy_cost(annual_mileage, energy_price)


# Additional cost component implementations
class MaintenanceCost(CostComponent):
    """Handles maintenance and repair costs."""
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, params: Dict[str, Any]
    ) -> float:
        """Calculate maintenance cost for a specific year."""
        # Implementation details...
        pass


class InfrastructureCost(CostComponent):
    """Handles charging infrastructure costs for electric vehicles."""
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, params: Dict[str, Any]
    ) -> float:
        """Calculate infrastructure cost for a specific year."""
        # Only applies to electric vehicles
        if not isinstance(vehicle, ElectricVehicle):
            return 0.0
            
        # Implementation details...
        pass


class BatteryReplacementCost(CostComponent):
    """Handles battery replacement costs for electric vehicles."""
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, params: Dict[str, Any]
    ) -> float:
        """Calculate battery replacement cost for a specific year."""
        # Only applies to electric vehicles
        if not isinstance(vehicle, ElectricVehicle):
            return 0.0
            
        # Implementation details...
        pass


class InsuranceCost(CostComponent):
    """Handles insurance costs."""
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, params: Dict[str, Any]
    ) -> float:
        """Calculate insurance cost for a specific year."""
        # Implementation details...
        pass


class RegistrationCost(CostComponent):
    """Handles registration and road user charges."""
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, params: Dict[str, Any]
    ) -> float:
        """Calculate registration cost for a specific year."""
        # Implementation details...
        pass


class ResidualValue(CostComponent):
    """Handles residual value calculation (negative cost)."""
    
    def calculate_annual_cost(
        self, year: int, vehicle: Vehicle, params: Dict[str, Any]
    ) -> float:
        """Calculate residual value for a specific year."""
        # Only apply in the final year
        end_year = params.get('end_year', 2040)
        if year != end_year:
            return 0.0
            
        # Calculate vehicle age
        start_year = params.get('start_year', 2025)
        age = year - start_year
        
        # Calculate residual value (as a negative cost)
        residual_value = vehicle.calculate_residual_value(age)
        return -residual_value  # Negative because it reduces total cost
```

#### `tco_model/scenarios.py`
- Implements scenario management
- Handles scenario creation, validation, and comparison

```python
# tco_model/scenarios.py
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
import yaml
import os
from datetime import datetime

class Scenario(BaseModel):
    """Represents a TCO calculation scenario with all input parameters."""
    
    # General parameters
    name: str = Field(..., description="Scenario name")
    description: Optional[str] = Field(None, description="Scenario description")
    start_year: int = Field(2025, description="Analysis start year")
    end_year: int = Field(2040, description="Analysis end year")
    
    # Economic parameters
    discount_rate: float = Field(0.07, description="Real discount rate", ge=0, le=0.2)
    inflation_rate: float = Field(0.025, description="Inflation rate", ge=0, le=0.1)
    financing_method: str = Field("loan", description="Financing method (cash or loan)")
    loan_term: int = Field(5, description="Loan term in years", ge=1, le=15)
    interest_rate: float = Field(0.07, description="Loan interest rate", ge=0, le=0.2)
    down_payment_pct: float = Field(0.2, description="Down payment percentage", ge=0, le=1.0)
    
    # Operational parameters
    annual_mileage: float = Field(80000, description="Annual kilometres driven", ge=0)
    
    # Electric vehicle parameters
    electric_vehicle_name: str = Field(..., description="Electric vehicle name/model")
    electric_vehicle_price: float = Field(..., description="Electric vehicle purchase price (AUD)", gt=0)
    electric_vehicle_battery_capacity: float = Field(..., description="Battery capacity (kWh)", gt=0)
    electric_vehicle_energy_consumption: float = Field(..., description="Energy consumption (kWh/km)", gt=0)
    electric_vehicle_battery_warranty: int = Field(8, description="Battery warranty period (years)", ge=0)
    
    # Diesel vehicle parameters
    diesel_vehicle_name: str = Field(..., description="Diesel vehicle name/model")
    diesel_vehicle_price: float = Field(..., description="Diesel vehicle purchase price (AUD)", gt=0)
    diesel_vehicle_fuel_consumption: float = Field(..., description="Fuel consumption (L/100km)", gt=0)
    
    # Energy prices
    electricity_prices: Dict[str, float] = Field({}, description="Electricity prices by year (AUD/kWh)")
    diesel_prices: Dict[str, float] = Field({}, description="Diesel prices by year (AUD/L)")
    
    # Infrastructure costs
    charger_cost: float = Field(0.0, description="Charger hardware cost (AUD)", ge=0)
    charger_installation_cost: float = Field(0.0, description="Charger installation cost (AUD)", ge=0)
    charger_lifespan: int = Field(10, description="Charger lifespan (years)", ge=1)
    
    # Maintenance costs
    electric_maintenance_cost_per_km: float = Field(0.08, description="Electric maintenance cost (AUD/km)", ge=0)
    diesel_maintenance_cost_per_km: float = Field(0.15, description="Diesel maintenance cost (AUD/km)", ge=0)
    
    # Insurance costs
    electric_insurance_cost_factor: float = Field(1.0, description="Electric insurance cost factor", ge=0)
    diesel_insurance_cost_factor: float = Field(1.0, description="Diesel insurance cost factor", ge=0)
    
    # Registration costs
    annual_registration_cost: float = Field(5000, description="Annual registration cost (AUD)", ge=0)
    
    # Battery replacement
    enable_battery_replacement: bool = Field(False, description="Enable battery replacement")
    battery_replacement_year: Optional[int] = Field(None, description="Fixed battery replacement year")
    battery_replacement_threshold: float = Field(0.7, description="Battery capacity threshold for replacement", ge=0, le=1.0)
    
    # Residual values
    electric_residual_value_pct: float = Field(0.1, description="Electric residual value percentage", ge=0, le=1.0)
    diesel_residual_value_pct: float = Field(0.1, description="Diesel residual value percentage", ge=0, le=1.0)
    
    # Validation and helper methods
    @validator('end_year')
    def end_year_must_be_after_start_year(cls, v, values):
        if 'start_year' in values and v <= values['start_year']:
            raise ValueError('end_year must be after start_year')
        return v
    
    @validator('electricity_prices', 'diesel_prices', pre=True)
    def validate_price_years(cls, v, values):
        if isinstance(v, dict) and 'start_year' in values and 'end_year' in values:
            start_year = values['start_year']
            end_year = values['end_year']
            
            # Ensure all years in the range have prices
            for year in range(start_year, end_year + 1):
                year_str = str(year)
                if year_str not in v:
                    # Use default values if missing
                    if 'electricity_prices' in values and v == values['electricity_prices']:
                        v[year_str] = 0.20  # Default electricity price (AUD/kWh)
                    else:
                        v[year_str] = 1.70  # Default diesel price (AUD/L)
        
        return v
    
    @classmethod
    def from_file(cls, filepath: str) -> 'Scenario':
        """Load scenario from a YAML file."""
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    def to_file(self, filepath: str) -> None:
        """Save scenario to a YAML file."""
        data = self.dict()
        with open(filepath, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
    
    def with_modifications(self, **kwargs) -> 'Scenario':
        """Create a new scenario with modified parameters."""
        data = self.dict()
        data.update(kwargs)
        return Scenario(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario to a dictionary."""
        return self.dict()
```

### UI Package

#### `ui/layout.py`
- Defines the overall layout of the Streamlit application
- Organizes the application into sections and pages

```python
# ui/layout.py
import streamlit as st

def create_layout():
    """Create the overall page layout."""
    # Title and header
    st.title("Australian Heavy Vehicle TCO Modeller")
    
    st.markdown("""
    Compare the 15-year Total Cost of Ownership (TCO) for Battery Electric Trucks (BETs) 
    and Internal Combustion Engine (ICE) diesel trucks in Australia (2025-2040).
    
    Adjust parameters in the sidebar to customize your analysis.
    """)
    
    # Create page division using columns for potential multi-column layout
    # This can be used for side-by-side comparison
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("TCO Analysis Results")
        # Main content area - will be populated by outputs.py
        st.empty()  # Placeholder for results
    
    with col2:
        st.subheader("Summary Metrics")
        # Summary metrics area
        st.empty()  # Placeholder for summary metrics
    
    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs([
        "Cumulative TCO", 
        "Cost Breakdown", 
        "Sensitivity Analysis",
        "Detailed Data"
    ])
    
    # Return tab references for use in outputs.py
    return {
        'main_column': col1,
        'summary_column': col2,
        'tabs': {
            'cumulative_tco': tab1,
            'cost_breakdown': tab2,
            'sensitivity': tab3,
            'detailed_data': tab4
        }
    }
```

#### `ui/inputs.py`
- Implements input collection components
- Organizes inputs into logical groups

```python
# ui/inputs.py
import streamlit as st
from datetime import datetime
import yaml
import os
from typing import Dict, Any

from tco_model.scenarios import Scenario
from utils.data_handlers import load_config

def create_input_sidebar() -> Dict[str, Any]:
    """Create the sidebar input panel and collect user inputs."""
    st.sidebar.title("Input Parameters")
    
    # Load default configuration
    defaults = load_config()
    
    # Scenario selection
    scenario_name = st.sidebar.text_input(
        "Scenario Name", 
        value=f"Scenario_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    
    # Create expandable sections for input groups
    with st.sidebar.expander("General Parameters", expanded=True):
        start_year = st.number_input(
            "Start Year", 
            min_value=2025, 
            max_value=2035, 
            value=2025,
            step=1
        )
        
        end_year = st.number_input(
            "End Year", 
            min_value=start_year + 5, 
            max_value=2050, 
            value=2040,
            step=1
        )
        
        vehicle_type = st.selectbox(
            "Vehicle Type",
            options=["Rigid", "Articulated"],
            index=0
        )
    
    # Economic parameters
    with st.sidebar.expander("Economic Parameters", expanded=False):
        discount_rate = st.slider(
            "Discount Rate (%)", 
            min_value=0.0, 
            max_value=15.0, 
            value=7.0,
            step=0.1,
            format="%.1f"
        ) / 100.0
        
        inflation_rate = st.slider(
            "Inflation Rate (%)", 
            min_value=0.0, 
            max_value=10.0, 
            value=2.5,
            step=0.1,
            format="%.1f"
        ) / 100.0
        
        financing_method = st.selectbox(
            "Financing Method",
            options=["Loan", "Cash"],
            index=0
        ).lower()
        
        if financing_method == "loan":
            loan_term = st.slider(
                "Loan Term (years)", 
                min_value=1, 
                max_value=10, 
                value=5,
                step=1
            )
            
            interest_rate = st.slider(
                "Interest Rate (%)", 
                min_value=0.0, 
                max_value=15.0, 
                value=7.0,
                step=0.1,
                format="%.1f"
            ) / 100.0
            
            down_payment_pct = st.slider(
                "Down Payment (%)", 
                min_value=0.0, 
                max_value=100.0, 
                value=20.0,
                step=5.0,
                format="%.1f"
            ) / 100.0
        else:
            loan_term = 0
            interest_rate = 0.0
            down_payment_pct = 1.0
    
    # Operational parameters
    with st.sidebar.expander("Operational Parameters", expanded=True):
        # Default annual mileage based on vehicle type
        default_mileage = 40000 if vehicle_type == "Rigid" else 80000
        
        annual_mileage = st.number_input(
            "Annual Kilometres", 
            min_value=10000, 
            max_value=200000, 
            value=default_mileage,
            step=5000
        )
    
    # Vehicle parameters (separate sections for BET and ICE)
    with st.sidebar.expander("Electric Vehicle Parameters", expanded=True):
        # Load default vehicle specs based on selected type
        default_ev_specs = defaults["vehicle_specs"]["electric"][vehicle_type.lower()]
        
        electric_vehicle_name = st.text_input(
            "Electric Vehicle Model",
            value=default_ev_specs["name"]
        )
        
        electric_vehicle_price = st.number_input(
            "Purchase Price (AUD)",
            min_value=100000,
            max_value=1000000,
            value=default_ev_specs["purchase_price"],
            step=10000
        )
        
        electric_vehicle_battery_capacity = st.number_input(
            "Battery Capacity (kWh)",
            min_value=50,
            max_value=1000,
            value=default_ev_specs["battery_capacity"],
            step=10
        )
        
        electric_vehicle_energy_consumption = st.number_input(
            "Energy Consumption (kWh/km)",
            min_value=0.5,
            max_value=3.0,
            value=default_ev_specs["energy_consumption"],
            step=0.1,
            format="%.2f"
        )
        
        electric_maintenance_cost_per_km = st.number_input(
            "Maintenance Cost (AUD/km)",
            min_value=0.01,
            max_value=0.5,
            value=0.08,
            step=0.01,
            format="%.2f"
        )
    
    with st.sidebar.expander("Diesel Vehicle Parameters", expanded=True):
        # Load default vehicle specs based on selected type
        default_ice_specs = defaults["vehicle_specs"]["diesel"][vehicle_type.lower()]
        
        diesel_vehicle_name = st.text_input(
            "Diesel Vehicle Model",
            value=default_ice_specs["name"]
        )
        
        diesel_vehicle_price = st.number_input(
            "Purchase Price (AUD)",
            min_value=50000,
            max_value=500000,
            value=default_ice_specs["purchase_price"],
            step=10000
        )
        
        diesel_vehicle_fuel_consumption = st.number_input(
            "Fuel Consumption (L/100km)",
            min_value=10.0,
            max_value=100.0,
            value=default_ice_specs["fuel_consumption"],
            step=1.0,
            format="%.1f"
        )
        
        diesel_maintenance_cost_per_km = st.number_input(
            "Maintenance Cost (AUD/km)",
            min_value=0.05,
            max_value=0.5,
            value=0.15,
            step=0.01,
            format="%.2f"
        )
    
    # Energy costs
    with st.sidebar.expander("Energy Costs", expanded=True):
        # Load energy price projections
        energy_price_projections = defaults["projections"]["energy_prices"]
        
        electricity_price_start = st.number_input(
            "Electricity Price 2025 (AUD/kWh)",
            min_value=0.05,
            max_value=0.5,
            value=0.20,
            step=0.01,
            format="%.2f"
        )
        
        electricity_price_end = st.number_input(
            "Electricity Price 2040 (AUD/kWh)",
            min_value=0.05,
            max_value=0.5,
            value=0.18,  # Default: slight decrease due to renewables
            step=0.01,
            format="%.2f"
        )
        
        diesel_price_start = st.number_input(
            "Diesel Price 2025 (AUD/L)",
            min_value=1.0,
            max_value=3.0,
            value=1.70,
            step=0.05,
            format="%.2f"
        )
        
        diesel_price_end = st.number_input(
            "Diesel Price 2040 (AUD/L)",
            min_value=1.0,
            max_value=5.0,
            value=2.30,  # Default: increasing trend
            step=0.05,
            format="%.2f"
        )
    
    # Infrastructure costs
    with st.sidebar.expander("Infrastructure Costs", expanded=False):
        charger_cost = st.number_input(
            "Charger Hardware Cost (AUD)",
            min_value=0,
            max_value=200000,
            value=50000,
            step=5000
        )
        
        charger_installation_cost = st.number_input(
            "Charger Installation Cost (AUD)",
            min_value=0,
            max_value=200000,
            value=50000,
            step=5000
        )
        
        charger_lifespan = st.slider(
            "Charger Lifespan (years)",
            min_value=5,
            max_value=20,
            value=10,
            step=1
        )
    
    # Battery replacement
    with st.sidebar.expander("Battery Replacement", expanded=False):
        enable_battery_replacement = st.checkbox(
            "Enable Battery Replacement",
            value=False
        )
        
        if enable_battery_replacement:
            replacement_method = st.radio(
                "Replacement Method",
                options=["Fixed Year", "Capacity Threshold"],
                index=0
            )
            
            if replacement_method == "Fixed Year":
                battery_replacement_year = st.slider(
                    "Replacement Year",
                    min_value=start_year + 5,
                    max_value=end_year - 1,
                    value=start_year + 8,
                    step=1
                )
                battery_replacement_threshold = 0.7  # Default
            else:
                battery_replacement_year = None
                battery_replacement_threshold = st.slider(
                    "Capacity Threshold (%)",
                    min_value=50,
                    max_value=90,
                    value=70,
                    step=5
                ) / 100.0
        else:
            battery_replacement_year = None
            battery_replacement_threshold = 0.7  # Default
    
    # Residual values
    with st.sidebar.expander("Residual Values", expanded=False):
        electric_residual_value_pct = st.slider(
            "Electric Residual Value (%)",
            min_value=0,
            max_value=30,
            value=10,
            step=1
        ) / 100.0
        
        diesel_residual_value_pct = st.slider(
            "Diesel Residual Value (%)",
            min_value=0,
            max_value=30,
            value=10,
            step=1
        ) / 100.0
    
    # Generate electricity and diesel price projections based on inputs
    years = list(range(start_year, end_year + 1))
    
    electricity_prices = {}
    diesel_prices = {}
    
    for i, year in enumerate(years):
        year_str = str(year)
        # Linear interpolation between start and end prices
        progress = i / (len(years) - 1) if len(years) > 1 else 0
        
        electricity_prices[year_str] = electricity_price_start + progress * (electricity_price_end - electricity_price_start)
        diesel_prices[year_str] = diesel_price_start + progress * (diesel_price_end - diesel_price_start)
    
    # Compile all parameters
    params = {
        "name": scenario_name,
        "description": f"{vehicle_type} TCO Analysis",
        "start_year": start_year,
        "end_year": end_year,
        
        # Economic parameters
        "discount_rate": discount_rate,
        "inflation_rate": inflation_rate,
        "financing_method": financing_method,
        "loan_term": loan_term,
        "interest_rate": interest_rate,
        "down_payment_pct": down_payment_pct,
        
        # Operational parameters
        "annual_mileage": annual_mileage,
        
        # Electric vehicle parameters
        "electric_vehicle_name": electric_vehicle_name,
        "electric_vehicle_price": electric_vehicle_price,
        "electric_vehicle_battery_capacity": electric_vehicle_battery_capacity,
        "electric_vehicle_energy_consumption": electric_vehicle_energy_consumption,
        "electric_vehicle_battery_warranty": 8,  # Default
        
        # Diesel vehicle parameters
        "diesel_vehicle_name": diesel_vehicle_name,
        "diesel_vehicle_price": diesel_vehicle_price,
        "diesel_vehicle_fuel_consumption": diesel_vehicle_fuel_consumption,
        
        # Energy prices
        "electricity_prices": electricity_prices,
        "diesel_prices": diesel_prices,
        
        # Infrastructure costs
        "charger_cost": charger_cost,
        "charger_installation_cost": charger_installation_cost,
        "charger_lifespan": charger_lifespan,
        
        # Maintenance costs
        "electric_maintenance_cost_per_km": electric_maintenance_cost_per_km,
        "diesel_maintenance_cost_per_km": diesel_maintenance_cost_per_km,
        
        # Insurance costs (defaults)
        "electric_insurance_cost_factor": 1.0,
        "diesel_insurance_cost_factor": 1.0,
        
        # Registration costs (default)
        "annual_registration_cost": 5000,
        
        # Battery replacement
        "enable_battery_replacement": enable_battery_replacement,
        "battery_replacement_year": battery_replacement_year,
        "battery_replacement_threshold": battery_replacement_threshold,
        
        # Residual values
        "electric_residual_value_pct": electric_residual_value_pct,
        "diesel_residual_value_pct": diesel_residual_value_pct
    }
    
    # Add a save button to save the scenario to a file
    if st.sidebar.button("Save Scenario"):
        scenario = Scenario(**params)
        scenario_dir = os.path.join("config", "scenarios")
        os.makedirs(scenario_dir, exist_ok=True)
        
        filepath = os.path.join(scenario_dir, f"{scenario_name}.yaml")
        scenario.to_file(filepath)
        st.sidebar.success(f"Scenario saved to {filepath}")
    
    return params
```

#### `ui/outputs.py`
- Implements result display components
- Utilizes plotly for visualization

```python
# ui/outputs.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List

def display_results(results: Dict[str, Any]) -> None:
    """Display TCO results in the main panel."""
    # Extract key metrics for summary display
    electric_total = results['electric_total']
    diesel_total = results['diesel_total']
    parity_year = results.get('parity_year')
    lcod_electric = results['lcod_electric']
    lcod_diesel = results['lcod_diesel']
    
    # Display summary metrics
    st.subheader("Key Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="15-Year Electric TCO",
            value=f"${electric_total['total'].sum():,.0f}",
            delta=f"{(1 - electric_total['total'].sum() / diesel_total['total'].sum()) * 100:.1f}% vs Diesel",
            delta_color="inverse"
        )
    
    with col2:
        st.metric(
            label="15-Year Diesel TCO",
            value=f"${diesel_total['total'].sum():,.0f}"
        )
    
    with col3:
        if parity_year:
            parity_text = f"Year {parity_year}"
        else:
            parity_text = "Not reached"
            
        st.metric(
            label="TCO Parity Point",
            value=parity_text
        )
    
    st.metric(
        label="Levelized Cost per Kilometre",
        value=f"Electric: ${lcod_electric:.2f}/km | Diesel: ${lcod_diesel:.2f}/km",
        delta=f"{(1 - lcod_electric / lcod_diesel) * 100:.1f}%",
        delta_color="inverse"
    )
    
    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs([
        "Cumulative TCO", 
        "Cost Breakdown", 
        "Sensitivity Analysis",
        "Detailed Data"
    ])
    
    # Cumulative TCO Chart
    with tab1:
        fig = create_cumulative_tco_chart(results)
        st.plotly_chart(fig, use_container_width=True)
    
    # Cost Breakdown Chart
    with tab2:
        fig = create_cost_breakdown_chart(results)
        st.plotly_chart(fig, use_container_width=True)
    
    # Sensitivity Analysis
    with tab3:
        if 'sensitivity' in results:
            fig = create_sensitivity_chart(results['sensitivity'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Run sensitivity analysis to see results here.")
            if st.button("Run Sensitivity Analysis"):
                st.warning("Sensitivity analysis feature not yet implemented.")
    
    # Detailed Data
    with tab4:
        st.subheader("Detailed Annual Costs")
        
        sub_tab1, sub_tab2 = st.tabs(["Electric Vehicle", "Diesel Vehicle"])
        
        with sub_tab1:
            st.dataframe(electric_total, use_container_width=True)
        
        with sub_tab2:
            st.dataframe(diesel_total, use_container_width=True)
        
        # Download buttons
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = pd.concat(
                [electric_total, diesel_total], 
                keys=['Electric', 'Diesel'], 
                axis=1
            ).to_csv(index=True).encode('utf-8')
            
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name="tco_results.csv",
                mime="text/csv",
            )
        
        with col2:
            # This would use a utility function to create an Excel file
            st.button("Download Excel", disabled=True)


def create_cumulative_tco_chart(results: Dict[str, Any]) -> go.Figure:
    """Create a cumulative TCO comparison chart."""
    electric_total = results['electric_total']
    diesel_total = results['diesel_total']
    
    # Calculate cumulative sums
    electric_cumulative = electric_total['total'].cumsum()
    diesel_cumulative = diesel_total['total'].cumsum()
    
    # Create figure
    fig = go.Figure()
    
    # Add traces
    fig.add_trace(go.Scatter(
        x=electric_total.index,
        y=electric_cumulative,
        mode='lines',
        name='Electric',
        line=dict(color='#00CC96', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=diesel_total.index,
        y=diesel_cumulative,
        mode='lines',
        name='Diesel',
        line=dict(color='#EF553B', width=3)
    ))
    
    # Add parity point if it exists
    parity_year = results.get('parity_year')
    if parity_year:
        parity_value = diesel_cumulative.loc[parity_year]
        
        fig.add_trace(go.Scatter(
            x=[parity_year],
            y=[parity_value],
            mode='markers',
            name='Parity Point',
            marker=dict(size=12, color='yellow', line=dict(width=2, color='black')),
            hoverinfo='text',
            text=f'Parity at Year {parity_year}: ${parity_value:,.0f}'
        ))
    
    # Update layout
    fig.update_layout(
        title='Cumulative TCO Comparison (2025-2040)',
        xaxis_title='Year',
        yaxis_title='Cumulative Cost (AUD)',
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='rgba(0, 0, 0, 0.2)',
            borderwidth=1
        ),
        hovermode='x unified',
        yaxis=dict(tickprefix='$', tickformat=','),
        template='plotly_white'
    )
    
    return fig


def create_cost_breakdown_chart(results: Dict[str, Any]) -> go.Figure:
    """Create a stacked bar chart showing cost breakdown by component."""
    electric_total = results['electric_total']
    diesel_total = results['diesel_total']
    
    # Drop the 'total' column as we'll show components
    electric_components = electric_total.drop(columns=['total'])
    diesel_components = diesel_total.drop(columns=['total'])
    
    # Sum costs by component
    electric_breakdown = electric_components.sum()
    diesel_breakdown = diesel_components.sum()
    
    # Create a DataFrame for plotting
    breakdown_df = pd.DataFrame({
        'Electric': electric_breakdown,
        'Diesel': diesel_breakdown
    }).T
    
    # Ensure residual value (negative) is at the bottom of the stack
    columns = list(breakdown_df.columns)
    if 'residual_value' in columns:
        columns.remove('residual_value')
        columns.append('residual_value')
        breakdown_df = breakdown_df[columns]
    
    # Create figure
    fig = px.bar(
        breakdown_df,
        barmode='relative',
        title='15-Year Cost Breakdown by Component',
        labels={'value': 'Cost (AUD)', 'index': 'Vehicle Type', 'variable': 'Cost Component'},
        color_discrete_sequence=px.colors.qualitative.Plotly,
        template='plotly_white'
    )
    
    # Update layout
    fig.update_layout(
        yaxis=dict(tickprefix='$', tickformat=','),
        legend=dict(
            title='Cost Component',
            orientation='h',
            xanchor='center',
            x=0.5,
            y=-0.2
        )
    )
    
    return fig


def create_sensitivity_chart(sensitivity_data: Dict[str, Any]) -> go.Figure:
    """Create a tornado chart for sensitivity analysis."""
    # This is a placeholder. In a real implementation, this would use actual sensitivity data.
    
    # Create sample data for demonstration
    parameters = [
        'Diesel Price', 
        'Electric Price', 
        'Annual Mileage', 
        'Discount Rate', 
        'Battery Cost'
    ]
    
    low_values = [-75000, 50000, -40000, 25000, 30000]
    high_values = [120000, -40000, 80000, -30000, -25000]
    
    # Create figure
    fig = go.Figure()
    
    # Add bars for low values
    fig.add_trace(go.Bar(
        y=parameters,
        x=low_values,
        name='Low Case',
        orientation='h',
        marker=dict(color='rgba(55, 128, 191, 0.8)'),
        hovertemplate='%{y}: %{x:$,.0f}<extra></extra>'
    ))
    
    # Add bars for high values
    fig.add_trace(go.Bar(
        y=parameters,
        x=high_values,
        name='High Case',
        orientation='h',
        marker=dict(color='rgba(219, 64, 82, 0.8)'),
        hovertemplate='%{y}: %{x:$,.0f}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title='Sensitivity Analysis: Impact on TCO Difference (Electric - Diesel)',
        xaxis=dict(
            title='Change in TCO Difference (AUD)',
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='black',
            tickprefix='$',
            tickformat=','
        ),
        yaxis=dict(
            title='Parameter',
            autorange='reversed'  # To put largest values at the top
        ),
        barmode='relative',
        bargap=0.2,
        bargroupgap=0.1,
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='rgba(0, 0, 0, 0.2)',
            borderwidth=1
        ),
        template='plotly_white'
    )
    
    # Add a vertical line at 0
    fig.add_shape(
        type='line',
        x0=0, y0=-0.5,
        x1=0, y1=len(parameters) - 0.5,
        line=dict(color='black', width=2, dash='dot')
    )
    
    return fig
```

### Utils Package

#### `utils/plotting.py`
- Implements reusable chart generation functions

```python
# utils/plotting.py
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple

def create_line_chart(
    data: pd.DataFrame,
    x_column: str,
    y_columns: List[str],
    title: str,
    x_title: str,
    y_title: str,
    colors: Optional[List[str]] = None,
    line_modes: Optional[List[str]] = None,
    annotations: Optional[List[Dict]] = None
) -> go.Figure:
    """
    Create a line chart with multiple traces.
    
    Args:
        data: DataFrame containing the data
        x_column: Column name for x-axis
        y_columns: List of column names for y-axis traces
        title: Chart title
        x_title: X-axis title
        y_title: Y-axis title
        colors: Optional list of colors for traces
        line_modes: Optional list of line modes (lines, markers, etc.)
        annotations: Optional list of annotation dictionaries
    
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    # Default colors and line modes if not provided
    if not colors:
        colors = px.colors.qualitative.Plotly
    
    if not line_modes:
        line_modes = ['lines'] * len(y_columns)
    
    # Add a trace for each y-column
    for i, y_column in enumerate(y_columns):
        color = colors[i % len(colors)]
        mode = line_modes[i % len(line_modes)]
        
        fig.add_trace(go.Scatter(
            x=data[x_column],
            y=data[y_column],
            mode=mode,
            name=y_column,
            line=dict(color=color, width=2)
        ))
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='rgba(0, 0, 0, 0.2)',
            borderwidth=1
        ),
        hovermode='x unified',
        template='plotly_white'
    )
    
    # Add annotations if provided
    if annotations:
        fig.update_layout(annotations=annotations)
    
    return fig


def create_stacked_bar_chart(
    data: pd.DataFrame,
    x_column: str,
    y_columns: List[str],
    title: str,
    x_title: str,
    y_title: str,
    colors: Optional[List[str]] = None,
    hover_template: Optional[str] = None
) -> go.Figure:
    """
    Create a stacked bar chart.
    
    Args:
        data: DataFrame containing the data
        x_column: Column name for x-axis (categories)
        y_columns: List of column names for the stacked bars
        title: Chart title
        x_title: X-axis title
        y_title: Y-axis title
        colors: Optional list of colors for traces
        hover_template: Optional custom hover template
    
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    # Default colors if not provided
    if not colors:
        colors = px.colors.qualitative.Plotly
    
    # Add a bar trace for each y-column
    for i, y_column in enumerate(y_columns):
        color = colors[i % len(colors)]
        
        fig.add_trace(go.Bar(
            x=data[x_column],
            y=data[y_column],
            name=y_column,
            marker=dict(color=color),
            hovertemplate=hover_template if hover_template else None
        ))
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        barmode='stack',
        legend=dict(
            orientation='h',
            xanchor='center',
            x=0.5,
            y=-0.2
        ),
        template='plotly_white'
    )
    
    return fig


def create_tornado_chart(
    parameters: List[str],
    low_values: List[float],
    high_values: List[float],
    title: str,
    x_title: str,
    y_title: str,
    low_color: str = 'rgba(55, 128, 191, 0.8)',
    high_color: str = 'rgba(219, 64, 82, 0.8)',
    zero_line: bool = True
) -> go.Figure:
    """
    Create a tornado chart for sensitivity analysis.
    
    Args:
        parameters: List of parameter names
        low_values: List of low case values
        high_values: List of high case values
        title: Chart title
        x_title: X-axis title
        y_title: Y-axis title
        low_color: Color for low case bars
        high_color: Color for high case bars
        zero_line: Whether to include a vertical line at 0
    
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    # Add bars for low values
    fig.add_trace(go.Bar(
        y=parameters,
        x=low_values,
        name='Low Case',
        orientation='h',
        marker=dict(color=low_color),
        hovertemplate='%{y}: %{x:,.0f}<extra></extra>'
    ))
    
    # Add bars for high values
    fig.add_trace(go.Bar(
        y=parameters,
        x=high_values,
        name='High Case',
        orientation='h',
        marker=dict(color=high_color),
        hovertemplate='%{y}: %{x:,.0f}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis=dict(
            title=x_title,
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='black'
        ),
        yaxis=dict(
            title=y_title,
            autorange='reversed'  # To put largest values at the top
        ),
        barmode='relative',
        bargap=0.2,
        bargroupgap=0.1,
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='rgba(0, 0, 0, 0.2)',
            borderwidth=1
        ),
        template='plotly_white'
    )
    
    # Add a vertical line at 0 if requested
    if zero_line:
        fig.add_shape(
            type='line',
            x0=0, y0=-0.5,
            x1=0, y1=len(parameters) - 0.5,
            line=dict(color='black', width=2, dash='dot')
        )
    
    return fig
```

#### `utils/data_handlers.py`
- Implements data loading and manipulation utilities

```python
# utils/data_handlers.py
import yaml
import pandas as pd
import os
from typing import Dict, Any, Optional, List

def load_config(config_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration data from YAML files.
    
    Args:
        config_name: Optional specific configuration to load
        
    Returns:
        Dictionary containing configuration data
    """
    config_dir = 'config'
    
    # Load specific configuration if provided
    if config_name:
        config_path = os.path.join(config_dir, f"{config_name}.yaml")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    # Load all configuration files if no specific one is requested
    config = {}
    
    # Load constants
    constants_path = os.path.join(config_dir, 'constants.py')
    if os.path.exists(constants_path):
        with open(constants_path, 'r') as f:
            # Execute the constants file and capture its variables
            constants_dict = {}
            exec(f.read(), None, constants_dict)
            config['constants'] = constants_dict
    
    # Load default vehicle specifications
    vehicle_specs_path = os.path.join(config_dir, 'defaults', 'vehicle_specs.yaml')
    if os.path.exists(vehicle_specs_path):
        with open(vehicle_specs_path, 'r') as f:
            config['vehicle_specs'] = yaml.safe_load(f)
    
    # Load projections
    projections_dir = os.path.join(config_dir, 'defaults')
    config['projections'] = {}
    
    projection_files = {
        'energy_prices': 'energy_prices.yaml',
        'battery_costs': 'battery_costs.yaml',
        'incentives': 'incentives.yaml'
    }
    
    for key, filename in projection_files.items():
        file_path = os.path.join(projections_dir, filename)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                config['projections'][key] = yaml.safe_load(f)
    
    return config


def load_scenario(scenario_name: str) -> Dict[str, Any]:
    """
    Load a scenario from a file.
    
    Args:
        scenario_name: Name of the scenario to load
        
    Returns:
        Dictionary containing scenario parameters
    """
    scenario_dir = os.path.join('config', 'scenarios')
    
    # Try with and without .yaml extension
    for filename in [f"{scenario_name}.yaml", scenario_name]:
        filepath = os.path.join(scenario_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return yaml.safe_load(f)
    
    raise FileNotFoundError(f"Scenario file not found: {scenario_name}")


def get_available_scenarios() -> List[str]:
    """
    Get a list of available predefined scenarios.
    
    Returns:
        List of scenario names (without extension)
    """
    scenario_dir = os.path.join('config', 'scenarios')
    
    if not os.path.exists(scenario_dir):
        return []
    
    # Get YAML files and strip extension
    scenario_files = [
        os.path.splitext(f)[0] for f in os.listdir(scenario_dir) 
        if f.endswith('.yaml')
    ]
    
    return scenario_files


def save_scenario(scenario_name: str, scenario_data: Dict[str, Any]) -> str:
    """
    Save a scenario to a file.
    
    Args:
        scenario_name: Name for the scenario
        scenario_data: Dictionary containing scenario parameters
        
    Returns:
        Path to the saved file
    """
    scenario_dir = os.path.join('config', 'scenarios')
    os.makedirs(scenario_dir, exist_ok=True)
    
    filepath = os.path.join(scenario_dir, f"{scenario_name}.yaml")
    
    with open(filepath, 'w') as f:
        yaml.dump(scenario_data, f, default_flow_style=False)
    
    return filepath


def export_results_to_excel(
    results: Dict[str, Any], 
    filepath: str
) -> None:
    """
    Export TCO results to an Excel file.
    
    Args:
        results: Dictionary containing TCO results
        filepath: Path for the output Excel file
    """
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        # Extract key components
        electric_total = results['electric_total']
        diesel_total = results['diesel_total']
        
        # Write summary sheet
        summary_data = {
            'Metric': [
                'Total TCO (15-Year)',
                'Levelized Cost per Kilometre (LCOD)',
                'TCO Parity Year',
                'Annual Kilometres',
                'Discount Rate',
                'Analysis Period'
            ],
            'Electric': [
                f"${electric_total['total'].sum():,.0f}",
                f"${results['lcod_electric']:.2f}/km",
                results.get('parity_year', 'Not reached'),
                f"{results.get('annual_mileage', 'N/A'):,.0f} km",
                f"{results.get('discount_rate', 0.07) * 100:.1f}%",
                f"{results.get('start_year', 2025)}–{results.get('end_year', 2040)}"
            ],
            'Diesel': [
                f"${diesel_total['total'].sum():,.0f}",
                f"${results['lcod_diesel']:.2f}/km",
                'Baseline',
                f"{results.get('annual_mileage', 'N/A'):,.0f} km",
                f"{results.get('discount_rate', 0.07) * 100:.1f}%",
                f"{results.get('start_year', 2025)}–{results.get('end_year', 2040)}"
            ]
        }
        
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        # Write detailed results
        electric_total.to_excel(writer, sheet_name='Electric Vehicle')
        diesel_total.to_excel(writer, sheet_name='Diesel Vehicle')
        
        # Write combined results for comparison
        combined = pd.concat(
            [electric_total, diesel_total], 
            keys=['Electric', 'Diesel'], 
            axis=1
        )
        combined.to_excel(writer, sheet_name='Comparison')
        
        # Write scenario parameters if available
        if 'scenario' in results:
            scenario_df = pd.DataFrame([results['scenario']]).T
            scenario_df.columns = ['Value']
            scenario_df.index.name = 'Parameter'
            scenario_df.to_excel(writer, sheet_name='Scenario Parameters')
```

### Sample Configuration Files

#### `config/defaults/vehicle_specs.yaml`
- Defines default vehicle specifications

```yaml
# Default vehicle specifications
electric:
  rigid:
    name: "Electric Rigid Truck"
    purchase_price: 400000
    battery_capacity: 300
    energy_consumption: 0.9
    battery_warranty: 8
  articulated:
    name: "Electric Articulated Truck"
    purchase_price: 600000
    battery_capacity: 500
    energy_consumption: 1.5
    battery_warranty: 8

diesel:
  rigid:
    name: "Diesel Rigid Truck"
    purchase_price: 200000
    fuel_consumption: 30
  articulated:
    name: "Diesel Articulated Truck"
    purchase_price: 300000
    fuel_consumption: 50
```

#### `config/defaults/energy_prices.yaml`
- Defines energy price projections

```yaml
# Energy price projections
electricity:
  base_2025: 0.20
  low_scenario:
    2025: 0.20
    2030: 0.18
    2035: 0.16
    2040: 0.15
  medium_scenario:
    2025: 0.20
    2030: 0.20
    2035: 0.19
    2040: 0.18
  high_scenario:
    2025: 0.20
    2030: 0.22
    2035: 0.24
    2040: 0.25

diesel:
  base_2025: 1.70
  low_scenario:
    2025: 1.70
    2030: 1.70
    2035: 1.70
    2040: 1.70
  medium_scenario:
    2025: 1.70
    2030: 1.85
    2035: 2.10
    2040: 2.30
  high_scenario:
    2025: 1.70
    2030: 2.10
    2035: 2.50
    2040: 3.00
```

## Testing Structure

```
tests/
├── __init__.py
├── test_model.py
├── test_vehicles.py
├── test_components.py
└── test_scenarios.py
```

### Sample Test File

```python
# tests/test_vehicles.py
import pytest
from tco_model.vehicles import Vehicle, ElectricVehicle, DieselVehicle

class TestVehicles:
    """Tests for vehicle classes."""
    
    def test_electric_vehicle_energy_consumption(self):
        """Test energy consumption calculation for electric vehicles."""
        ev = ElectricVehicle(
            name="Test EV",
            purchase_price=400000,
            annual_mileage=80000,
            lifespan=15,
            battery_capacity=300,
            energy_consumption=1.5
        )
        
        # Test for 100 km
        assert ev.calculate_energy_consumption(100) == 150.0
        
        # Test for 1000 km
        assert ev.calculate_energy_consumption(1000) == 1500.0
    
    def test_diesel_vehicle_energy_consumption(self):
        """Test energy consumption calculation for diesel vehicles."""
        dv = DieselVehicle(
            name="Test Diesel",
            purchase_price=200000,
            annual_mileage=80000,
            lifespan=15,
            fuel_consumption=40
        )
        
        # Test for 100 km (40 L/100km = 0.4 L/km)
        assert dv.calculate_energy_consumption(100) == 40.0
        
        # Test for 1000 km
        assert dv.calculate_energy_consumption(1000) == 400.0
    
    def test_electric_vehicle_energy_cost(self):
        """Test energy cost calculation for electric vehicles."""
        ev = ElectricVehicle(
            name="Test EV",
            purchase_price=400000,
            annual_mileage=80000,
            lifespan=15,
            battery_capacity=300,
            energy_consumption=1.5
        )
        
        # Test for 100 km at $0.20/kWh
        assert ev.calculate_energy_cost(100, 0.20) == 30.0
        
        # Test for 1000 km at $0.15/kWh
        assert ev.calculate_energy_cost(1000, 0.15) == 225.0
    
    def test_diesel_vehicle_energy_cost(self):
        """Test energy cost calculation for diesel vehicles."""
        dv = DieselVehicle(
            name="Test Diesel",
            purchase_price=200000,
            annual_mileage=80000,
            lifespan=15,
            fuel_consumption=40
        )
        
        # Test for 100 km at $1.70/L
        assert dv.calculate_energy_cost(100, 1.70) == 68.0
        
        # Test for 1000 km at $2.00/L
        assert dv.calculate_energy_cost(1000, 2.00) == 800.0
    
    def test_residual_value(self):
        """Test residual value calculation."""
        ev = ElectricVehicle(
            name="Test EV",
            purchase_price=400000,
            annual_mileage=80000,
            lifespan=15,
            battery_capacity=300,
            energy_consumption=1.5
        )
        
        # Test at year 0 (should be 100%)
        assert ev.calculate_residual_value(0) == 400000
        
        # Test at year 15 (should be 10%)
        assert ev.calculate_residual_value(15) == 40000
        
        # Test at year 8 (should be ~47%)
        expected = 400000 * (1.0 - (8 / 15) * 0.9)
        assert abs(ev.calculate_residual_value(8) - expected) < 0.01
    
    def test_battery_degradation(self):
        """Test battery degradation calculation."""
        ev = ElectricVehicle(
            name="Test EV",
            purchase_price=400000,
            annual_mileage=80000,
            lifespan=15,
            battery_capacity=300,
            energy_consumption=1.5
        )
        
        # Test at year 0, 0 km (should be 100%)
        assert ev.calculate_battery_degradation(0, 0) == 1.0
        
        # Test reasonable degradation at year 8 with expected mileage
        degradation = ev.calculate_battery_degradation(8, 8 * 80000)
        assert 0.7 <= degradation <= 0.9
