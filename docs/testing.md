# Testing Strategy

This document outlines the comprehensive testing approach for the Australian Heavy Vehicle TCO Modeller, ensuring the reliability, accuracy, and performance of both the core calculation model and the Streamlit application.

## 1. Testing Philosophy

Our testing strategy follows these key principles:

1. **Test-Driven Development (TDD)** - Write tests before implementation where feasible
2. **Comprehensive Coverage** - Test across all components and integration points
3. **Validation Against Real Data** - Ensure calculations match expected outcomes
4. **Automated Where Possible** - Use automation to enable frequent testing
5. **Performance Monitoring** - Ensure the application remains responsive

## 2. Testing Levels

### 2.1 Unit Testing

Unit tests verify that individual components work correctly in isolation.

#### Key Areas for Unit Testing

1. **Vehicle Classes**
   - Test energy consumption calculations
   - Test energy cost calculations
   - Test battery degradation models
   - Test residual value calculations

2. **Cost Components**
   - Test individual cost component calculations
   - Verify correct handling of different years/scenarios
   - Test edge cases (zero values, extremes)

3. **Scenario Management**
   - Test validation of input parameters
   - Test loading/saving functionality
   - Test scenario transformations

4. **Financial Calculations**
   - Test discounting functions
   - Test loan/financing calculations
   - Test inflation adjustments

#### Example Unit Tests

```python
# tests/test_vehicles.py
import pytest
from tco_model.vehicles import ElectricVehicle, DieselVehicle

class TestElectricVehicle:
    """Tests for ElectricVehicle class."""
    
    def test_energy_consumption(self):
        """Test energy consumption calculation."""
        ev = ElectricVehicle(
            name="Test EV",
            purchase_price=400000,
            annual_mileage=80000,
            lifespan=15,
            battery_capacity=300,
            energy_consumption=1.5
        )
        
        # Test for 100 km - should consume 150 kWh
        assert ev.calculate_energy_consumption(100) == 150.0
        
        # Test for 500 km - should consume 750 kWh
        assert ev.calculate_energy_consumption(500) == 750.0
    
    def test_energy_cost(self):
        """Test energy cost calculation."""
        ev = ElectricVehicle(
            name="Test EV",
            purchase_price=400000,
            annual_mileage=80000,
            lifespan=15,
            battery_capacity=300,
            energy_consumption=1.5
        )
        
        # Test with electricity price of $0.20/kWh
        # 100 km × 1.5 kWh/km × $0.20/kWh = $30
        assert ev.calculate_energy_cost(100, 0.20) == 30.0

# tests/test_components.py
import pytest
from tco_model.components import AcquisitionCost
from tco_model.vehicles import ElectricVehicle

class TestAcquisitionCost:
    """Tests for AcquisitionCost component."""
    
    def test_cash_purchase(self):
        """Test acquisition cost for cash purchase."""
        # Setup
        vehicle = ElectricVehicle(
            name="Test EV",
            purchase_price=400000,
            annual_mileage=80000,
            lifespan=15,
            battery_capacity=300,
            energy_consumption=1.5
        )
        
        component = AcquisitionCost()
        
        # Test year 0 (purchase year) - should be full price
        cost = component.calculate_annual_cost(
            year=2025,
            vehicle=vehicle,
            params={
                'start_year': 2025,
                'financing_method': 'cash'
            }
        )
        assert cost == 400000
        
        # Test subsequent years - should be zero
        cost = component.calculate_annual_cost(
            year=2026,
            vehicle=vehicle,
            params={
                'start_year': 2025,
                'financing_method': 'cash'
            }
        )
        assert cost == 0
```

### 2.2 Integration Testing

Integration tests verify that components work correctly together.

#### Key Areas for Integration Testing

1. **TCO Calculator**
   - Test end-to-end calculation flow
   - Verify correct aggregation of component costs
   - Test discounting and total cost calculations
   - Test scenario-based calculations

2. **Data Flow**
   - Test data flow from configuration files to model
   - Test transformation of scenario data to calculation inputs
   - Test result formatting and export

#### Example Integration Tests

```python
# tests/test_model.py
import pytest
from tco_model.model import TCOCalculator
from tco_model.scenarios import Scenario

class TestTCOCalculator:
    """Tests for TCOCalculator class."""
    
    def test_simple_scenario(self):
        """Test TCO calculation with a simple scenario."""
        # Create a simplified test scenario
        scenario_data = {
            'name': 'Test Scenario',
            'start_year': 2025,
            'end_year': 2040,
            'discount_rate': 0.07,
            'annual_mileage': 80000,
            # Electric vehicle parameters
            'electric_vehicle_name': 'Test EV',
            'electric_vehicle_price': 400000,
            'electric_vehicle_battery_capacity': 300,
            'electric_vehicle_energy_consumption': 1.5,
            # Diesel vehicle parameters
            'diesel_vehicle_name': 'Test Diesel',
            'diesel_vehicle_price': 200000,
            'diesel_vehicle_fuel_consumption': 50,
            # Energy prices (constant for simplicity)
            'electricity_prices': {str(y): 0.20 for y in range(2025, 2041)},
            'diesel_prices': {str(y): 1.70 for y in range(2025, 2041)},
            # Maintenance costs
            'electric_maintenance_cost_per_km': 0.08,
            'diesel_maintenance_cost_per_km': 0.15,
            # Residual values
            'electric_residual_value_pct': 0.1,
            'diesel_residual_value_pct': 0.1,
        }
        
        scenario = Scenario(**scenario_data)
        
        # Calculate TCO
        calculator = TCOCalculator()
        results = calculator.calculate(scenario)
        
        # Verify results structure
        assert 'electric_annual' in results
        assert 'diesel_annual' in results
        assert 'electric_total' in results
        assert 'diesel_total' in results
        assert 'lcod_electric' in results
        assert 'lcod_diesel' in results
        
        # Basic sanity checks on the results
        # Electric total should include acquisition cost
        assert results['electric_total']['acquisition'][2025] > 0
        
        # Diesel should have higher fuel costs
        assert results['diesel_total']['energy'].sum() > results['electric_total']['energy'].sum()
        
        # Electric should have lower maintenance costs
        assert results['electric_total']['maintenance'].sum() < results['diesel_total']['maintenance'].sum()
    
    def test_parity_calculation(self):
        """Test TCO parity point calculation."""
        # Create a scenario where parity is known (manually calculated)
        # For example, a scenario where parity occurs in year 7 (2031)
        
        # Setup scenario data...
        
        calculator = TCOCalculator()
        results = calculator.calculate(scenario)
        
        # Verify parity year calculation
        assert results['parity_year'] == 2031
```

### 2.3 UI Testing

UI tests verify that the Streamlit interface works correctly.

#### Key Areas for UI Testing

1. **Input Validation**
   - Test form validation
   - Test error handling for invalid inputs
   - Test state preservation between reruns

2. **Visualization**
   - Test chart generation with different data sets
   - Test responsive layout for different screen sizes
   - Test interactive elements (tooltips, legends)

3. **User Flows**
   - Test scenario saving and loading
   - Test result export functionality
   - Test navigation between tabs

#### UI Testing Approach

Since Streamlit applications can be challenging to test in automated fashion, we'll use a combination of manual testing and targeted component tests:

```python
# tests/test_ui_components.py
import pytest
from ui.outputs import create_cumulative_tco_chart
import pandas as pd
import numpy as np

class TestUIComponents:
    """Tests for UI components."""
    
    def test_cumulative_chart_generation(self):
        """Test cumulative TCO chart generation."""
        # Create sample data
        years = range(2025, 2041)
        
        electric_total = pd.DataFrame({
            'total': np.cumsum([50000] + [30000] * 14 + [-30000])
        }, index=years)
        
        diesel_total = pd.DataFrame({
            'total': np.cumsum([30000] + [40000] * 14 + [-20000])
        }, index=years)
        
        results = {
            'electric_total': electric_total,
            'diesel_total': diesel_total,
            'parity_year': 2033
        }
        
        # Generate chart
        fig = create_cumulative_tco_chart(results)
        
        # Verify basic figure properties
        assert fig is not None
        assert len(fig.data) >= 2  # Should have at least two traces
        
        # Check trace names
        trace_names = [trace.name for trace in fig.data]
        assert 'Electric' in trace_names
        assert 'Diesel' in trace_names
```

### 2.4 End-to-End Testing

End-to-end tests verify the entire application workflow.

#### Key Scenarios for E2E Testing

1. **Basic TCO Comparison**
   - Test complete flow from inputs to visualization
   - Verify all components work together correctly

2. **Scenario Management**
   - Test saving, loading, and comparing scenarios
   - Test persistence across application restarts

3. **Export Functionality**
   - Test exporting results to different formats
   - Verify export file content and formatting

#### E2E Testing Implementation

End-to-end testing will primarily be manual using predefined test scripts:

```python
# tests/manual_test_scripts.py

def test_basic_workflow():
    """
    Test script for basic TCO comparison workflow.
    
    Steps:
    1. Launch application
    2. Set vehicle type to 'Articulated'
    3. Set annual kilometers to 100,000
    4. Adjust electric vehicle energy consumption to 1.5 kWh/km
    5. Adjust diesel fuel consumption to 50 L/100km
    6. Set electric vehicle purchase price to $600,000
    7. Set diesel vehicle purchase price to $300,000
    8. Verify results display correctly
    9. Verify cumulative TCO chart displays
    10. Verify cost breakdown chart displays
    11. Verify metrics are calculated correctly
    
    Expected outcome:
    - Application should display TCO comparison results
    - Charts should render correctly
    - Metrics should show reasonable values
    """
    pass
```

### 2.5 Performance Testing

Performance tests ensure the application remains responsive.

#### Key Performance Metrics

1. **Calculation Time**
   - Measure time to calculate TCO for different scenarios
   - Ensure calculation completes within reasonable time (< 1 second)

2. **UI Responsiveness**
   - Measure time from input change to UI update
   - Ensure responsive experience (< 500ms)

3. **Memory Usage**
   - Monitor memory usage during calculation and visualization
   - Identify and address memory leaks

#### Performance Testing Tools

- Profiling: Use Python's built-in profiling tools or Streamlit's performance tracing
- Load Testing: Test with extreme parameters to identify bottlenecks
- Memory Monitoring: Track memory usage over time

```python
# tests/test_performance.py
import pytest
import time
import tracemalloc
from tco_model.model import TCOCalculator
from tco_model.scenarios import Scenario

class TestPerformance:
    """Performance tests for TCO model."""
    
    def test_calculation_time(self):
        """Test calculation time for standard scenario."""
        # Create scenario
        # (Setup standard scenario here)
        
        calculator = TCOCalculator()
        
        # Measure calculation time
        start_time = time.time()
        results = calculator.calculate(scenario)
        end_time = time.time()
        
        calculation_time = end_time - start_time
        
        # Assert calculation completes within reasonable time
        assert calculation_time < 1.0, f"Calculation took {calculation_time:.2f} seconds"
    
    def test_memory_usage(self):
        """Test memory usage during calculation."""
        # Start memory tracing
        tracemalloc.start()
        
        # Create scenario and calculator
        # (Setup scenario here)
        calculator = TCOCalculator()
        
        # Get initial memory snapshot
        snapshot1 = tracemalloc.take_snapshot()
        
        # Perform calculation
        results = calculator.calculate(scenario)
        
        # Get final memory snapshot
        snapshot2 = tracemalloc.take_snapshot()
        
        # Compare memory usage
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        # Check for significant memory increase
        total_diff = sum(stat.size_diff for stat in top_stats)
        assert total_diff < 50 * 1024 * 1024, f"Memory usage increased by {total_diff / (1024 * 1024):.2f} MB"
```

## 3. Test Infrastructure

### 3.1 Test Directory Structure

```
tests/
├── __init__.py
├── conftest.py                 # Shared test fixtures
├── test_model.py               # Core model tests
├── test_vehicles.py            # Vehicle class tests
├── test_components.py          # Cost component tests
├── test_scenarios.py           # Scenario management tests
├── test_ui_components.py       # UI component tests
├── test_performance.py         # Performance tests
├── manual_test_scripts.py      # Manual test scripts
└── data/                       # Test data
    ├── scenarios/              # Test scenarios
    └── expected_results/       # Expected calculation results
```

### 3.2 Testing Tools

1. **Pytest**: Primary testing framework
2. **Pytest-cov**: Coverage reporting
3. **Hypothesis**: Property-based testing (optional)
4. **Streamlit-specific testing**: Custom fixtures for Streamlit components
5. **Profile**: Performance profiling

### 3.3 Test Fixtures

Reusable test fixtures will be defined in `conftest.py`:

```python
# tests/conftest.py
import pytest
import pandas as pd
import numpy as np
from tco_model.vehicles import ElectricVehicle, DieselVehicle
from tco_model.scenarios import Scenario

@pytest.fixture
def sample_electric_vehicle():
    """Fixture providing a sample ElectricVehicle instance."""
    return ElectricVehicle(
        name="Test EV",
        purchase_price=400000,
        annual_mileage=80000,
        lifespan=15,
        battery_capacity=300,
        energy_consumption=1.5
    )

@pytest.fixture
def sample_diesel_vehicle():
    """Fixture providing a sample DieselVehicle instance."""
    return DieselVehicle(
        name="Test Diesel",
        purchase_price=200000,
        annual_mileage=80000,
        lifespan=15,
        fuel_consumption=50
    )

@pytest.fixture
def basic_scenario():
    """Fixture providing a basic test scenario."""
    scenario_data = {
        'name': 'Test Scenario',
        'start_year': 2025,
        'end_year': 2040,
        'discount_rate': 0.07,
        'annual_mileage': 80000,
        # Electric vehicle parameters
        'electric_vehicle_name': 'Test EV',
        'electric_vehicle_price': 400000,
        'electric_vehicle_battery_capacity': 300,
        'electric_vehicle_energy_consumption': 1.5,
        # Diesel vehicle parameters
        'diesel_vehicle_name': 'Test Diesel',
        'diesel_vehicle_price': 200000,
        'diesel_vehicle_fuel_consumption': 50,
        # Energy prices (constant for simplicity)
        'electricity_prices': {str(y): 0.20 for y in range(2025, 2041)},
        'diesel_prices': {str(y): 1.70 for y in range(2025, 2041)},
        # Maintenance costs
        'electric_maintenance_cost_per_km': 0.08,
        'diesel_maintenance_cost_per_km': 0.15,
        # Residual values
        'electric_residual_value_pct': 0.1,
        'diesel_residual_value_pct': 0.1,
    }
    
    return Scenario(**scenario_data)

@pytest.fixture
def sample_tco_results():
    """Fixture providing sample TCO calculation results."""
    years = range(2025, 2041)
    
    # Create sample annual costs for electric
    electric_acquisition = pd.Series([80000]*5 + [0]*10 + [0], index=years)
    electric_energy = pd.Series([24000]*16, index=years)
    electric_maintenance = pd.Series([6400]*16, index=years)
    electric_infrastructure = pd.Series([10000]*10 + [0]*6, index=years)
    electric_insurance = pd.Series([20000]*16, index=years)
    electric_residual = pd.Series([0]*15 + [-40000], index=years)
    
    # Create sample annual costs for diesel
    diesel_acquisition = pd.Series([40000]*5 + [0]*10 + [0], index=years)
    diesel_energy = pd.Series([68000]*16, index=years)
    diesel_maintenance = pd.Series([12000]*16, index=years)
    diesel_insurance = pd.Series([10000]*16, index=years)
    diesel_residual = pd.Series([0]*15 + [-20000], index=years)
    
    # Create DataFrames
    electric_annual = pd.DataFrame({
        'acquisition': electric_acquisition,
        'energy': electric_energy,
        'maintenance': electric_maintenance,
        'infrastructure': electric_infrastructure,
        'insurance': electric_insurance,
        'residual_value': electric_residual
    })
    
    diesel_annual = pd.DataFrame({
        'acquisition': diesel_acquisition,
        'energy': diesel_energy,
        'maintenance': diesel_maintenance,
        'insurance': diesel_insurance,
        'residual_value': diesel_residual
    })
    
    # Add total columns
    electric_annual['total'] = electric_annual.sum(axis=1)
    diesel_annual['total'] = diesel_annual.sum(axis=1)
    
    # Create discounted copies
    discount_factors = pd.Series([(1 / (1 + 0.07)) ** i for i in range(16)], index=years)
    
    electric_total = electric_annual.multiply(discount_factors, axis=0)
    diesel_total = diesel_annual.multiply(discount_factors, axis=0)
    
    return {
        'electric_annual': electric_annual,
        'diesel_annual': diesel_annual,
        'electric_total': electric_total,
        'diesel_total': diesel_total,
        'parity_year': 2033,
        'lcod_electric': 1.04,
        'lcod_diesel': 1.17
    }
```

## 4. Test Data Management

### 4.1 Test Scenarios

Standard test scenarios will be stored in YAML files:

```yaml
# tests/data/scenarios/urban_delivery_test.yaml
name: "Urban Delivery Test"
description: "Test scenario for urban delivery trucks"
start_year: 2025
end_year: 2040
discount_rate: 0.07
annual_mileage: 40000

# Electric vehicle parameters
electric_vehicle_name: "Electric Rigid Truck"
electric_vehicle_price: 400000
electric_vehicle_battery_capacity: 300
electric_vehicle_energy_consumption: 0.9

# Diesel vehicle parameters
diesel_vehicle_name: "Diesel Rigid Truck"
diesel_vehicle_price: 200000
diesel_vehicle_fuel_consumption: 30

# Energy prices (simplified for testing)
electricity_prices:
  "2025": 0.20
  "2030": 0.18
  "2035": 0.16
  "2040": 0.15

diesel_prices:
  "2025": 1.70
  "2030": 1.85
  "2035": 2.10
  "2040": 2.30
```

### 4.2 Expected Results

Expected calculation results will be stored for validation:

```python
# tests/data/expected_results/urban_delivery_test.py
expected_results = {
    'parity_year': 2031,
    'lcod_electric': 0.95,
    'lcod_diesel': 1.08,
    # Further detailed results...
}
```

## 5. Testing Workflow

### 5.1 Development Testing Workflow

1. **Write Tests First**:
   - For new features, write tests before implementation
   - For bug fixes, write tests that reproduce the bug

2. **Run Tests Frequently**:
   - Run unit tests during development
   - Run integration tests after significant changes
   - Run end-to-end tests before commits

3. **Maintain Coverage**:
   - Aim for >80% code coverage on core model
   - Focus on testing critical paths and edge cases

### 5.2 Continuous Integration

The CI pipeline will run tests automatically:

1. **Pull Request Validation**:
   - Run unit and integration tests
   - Report code coverage
   - Run linting and code quality checks

2. **Main Branch Protection**:
   - Require passing tests before merge
   - Require code review
   - Perform automated quality checks

### 5.3 Test Reports

Generate comprehensive test reports:

1. **Coverage Reports**:
   - Line and branch coverage metrics
   - Identification of untested code

2. **Performance Reports**:
   - Calculation time for standard scenarios
   - Memory usage statistics

3. **Regression Analysis**:
   - Comparison of current results with baseline

## 6. Model Validation

### 6.1 Validation Against Known Results

The TCO model will be validated against known results:

1. **Simple Scenarios**:
   - Hand-calculated examples with known outcomes
   - Verification of individual component calculations

2. **Published Case Studies**:
   - Comparison with published TCO analyses
   - Adjustment for methodology differences

3. **Industry Benchmarks**:
   - Validation against industry-standard metrics
   - Consultation with domain experts

### 6.2 Sensitivity Testing

Validate model behavior under different conditions:

1. **Parameter Sweeps**:
   - Systematically vary key parameters
   - Verify expected relationships in results

2. **Edge Cases**:
   - Test with extreme parameter values
   - Verify model stability and reasonableness of results

3. **Sensitivity Analysis**:
   - Validate sensitivity rankings against expectations
   - Ensure small changes produce reasonable effects

## 7. Special Considerations for Streamlit

### 7.1 Streamlit-Specific Testing Challenges

1. **State Management**:
   - Test session state initialization and updates
   - Verify state persistence between reruns

2. **Widget Interaction**:
   - Mock user interactions with widgets
   - Verify callback functions are triggered correctly

3. **Caching**:
   - Test caching decorators work correctly
   - Verify performance improvements from caching

### 7.2 Testing Streamlit Components

Approach for testing Streamlit components:

1. **Component Isolation**:
   - Extract pure functions from UI code for testing
   - Test data transformation and visualization logic separately

2. **Manual Testing Protocol**:
   - Documented manual test procedures
   - Checklist for UI verification

3. **Streamlit Test Utilities**:
   - Use or develop utilities for testing Streamlit components
   - Mock Streamlit context where necessary

## 8. Testing Documentation

### 8.1 Test Documentation Standards

Each test should include:

1. **Purpose**: What aspect of functionality is being tested
2. **Setup**: The necessary preconditions
3. **Action**: The operation being tested
4. **Verification**: The expected outcomes
5. **Cleanup**: Any necessary cleanup

Example:

```python
def test_battery_degradation():
    """
    Test battery degradation calculation.
    
    Purpose:
        Verify that battery degradation is calculated correctly based on
        age and mileage.
    
    Setup:
        Create an ElectricVehicle with known parameters.
    
    Action:
        Calculate degradation for various ages and mileages.
    
    Verification:
        Confirm degradation follows expected patterns and values.
    """
    # Test implementation...
```

### 8.2 Troubleshooting Guide

A guide for diagnosing common test failures:

1. **Calculation Errors**:
   - Check input parameters
   - Verify formulas and constants
   - Review discounting application

2. **Data Consistency Issues**:
   - Check data types and units
   - Verify parameter consistency
   - Review data transformations

3. **UI Testing Issues**:
   - Check for state management problems
   - Verify widget callbacks
   - Review layout changes

## 9. Test Maintenance

### 9.1 Test Refactoring

Guidelines for maintaining tests over time:

1. **DRY Principle**:
   - Extract common test logic to fixtures or helper functions
   - Avoid duplicated assertions

2. **Test Clarity**:
   - Keep tests focused on a single concern
   - Use clear naming and documentation

3. **Test Independence**:
   - Ensure tests do not depend on each other
   - Avoid shared mutable state

### 9.2 Test Debt Management

Strategies for managing test debt:

1. **Regular Review**:
   - Periodically review test coverage
   - Identify areas needing improved testing

2. **Prioritization**:
   - Focus on critical path components
   - Address high-risk areas first

3. **Incremental Improvement**:
   - Add tests with each new feature
   - Improve existing tests during bug fixes

## Conclusion

This comprehensive testing strategy will ensure the reliability, accuracy, and performance of the Australian Heavy Vehicle TCO Modeller. By implementing these testing practices, we can confidently deliver a high-quality tool that provides valuable insights for stakeholders evaluating heavy vehicle electrification options.
