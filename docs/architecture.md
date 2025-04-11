# Technical Architecture Document

This document details the technical architecture for the Australian Heavy Vehicle TCO Modeller, outlining the system design, components, and interactions to provide a clear blueprint for implementation.

## Architecture Overview

The system uses a layered architecture pattern with clear separation of concerns:

1. **Data Layer**: Manages default data, projections, and user inputs
2. **Model Layer**: Implements the core TCO calculation logic using OOP principles
3. **Presentation Layer**: Streamlit-based web application for interactive visualisation

### Design Principles

1. **Modularity**: System components are designed to be loosely coupled and highly cohesive
2. **Extensibility**: Architecture allows for future extensions (e.g., additional vehicle types, alternative powertrains)
3. **Maintainability**: Clear separation of concerns and well-defined interfaces
4. **Testability**: Components can be tested in isolation with clear boundaries
5. **Performance**: Strategic use of caching and efficient algorithms

## Component Architecture

### 1. Data Layer

#### Configuration Management
- Manages default parameters, projections, and constants
- Implemented using YAML/JSON configuration files for easy maintenance
- Supports loading domain-specific data (vehicle specs, energy prices, etc.)

```python
# Sample configuration structure
config/
  ├── constants.yaml        # System-wide constants
  ├── vehicle_defaults.yaml # Default vehicle specifications
  ├── projections/
  │   ├── energy_prices.yaml  # Energy price projections
  │   ├── battery_costs.yaml  # Battery cost projections
  │   └── residual_values.yaml # Residual value projections
  └── scenarios/
      ├── urban_delivery.yaml # Pre-defined scenario
      └── long_haul.yaml      # Pre-defined scenario
```

#### Input Validation
- Validates user inputs against allowed ranges and constraints
- Implemented using Pydantic models for robust validation
- Provides clear error messages for invalid inputs

### 2. Model Layer

#### Core Abstractions

**Vehicle Classes**
- Base `Vehicle` class with common attributes and methods
- Specialized `ElectricVehicle` and `DieselVehicle` subclasses
- Responsible for vehicle-specific calculations (e.g., energy consumption)

**Cost Component Classes**
- Base `CostComponent` abstract class defining interface
- Specialized components for each cost category (acquisition, energy, maintenance, etc.)
- Each component calculates its annual costs based on scenario parameters

**Scenario Class**
- Contains all input parameters for a specific TCO calculation
- Provides a cohesive way to manage and validate inputs
- Supports scenario comparison and sensitivity analysis

**TCO Calculator**
- Orchestrates the overall TCO calculation process
- Applies time-based factors (discounting, inflation, etc.)
- Aggregates results into structured output formats

#### Key Interactions

1. **Scenario Creation**:
   - User inputs or default configurations populate a `Scenario` object
   - `Scenario` object validates all inputs for consistency

2. **TCO Calculation**:
   - `TCOCalculator` receives a `Scenario` object
   - Creates appropriate `Vehicle` instances based on scenario
   - Initializes required `CostComponent` objects
   - Calculates annual costs for each year in the analysis period
   - Applies discounting and aggregates results

3. **Result Generation**:
   - Structured output generation for visualization and reporting
   - Calculation of key metrics (LCOD, parity points, etc.)
   - Support for sensitivity analysis

### 3. Presentation Layer

#### Streamlit Application
- Main application entry point (`app.py`)
- Organized into logical sections using Streamlit components
- Manages user input collection and display of results

#### UI Components
- Input Section: Sidebar with organized parameter inputs
- Results Section: Main panel with tabs for different visualizations
- Summary Metrics: Key figures displayed prominently

#### Visualization
- Uses Plotly for interactive charts
- Implements reusable chart generation functions
- Provides multiple visualization types (line charts, bar charts, etc.)

#### State Management
- Uses Streamlit session state for maintaining application state
- Implements caching for performance optimization
- Supports scenario saving and comparison

## Data Flow

1. **Input Collection**:
   - User adjusts parameters via Streamlit UI
   - Inputs are collected and validated

2. **Model Processing**:
   - Validated inputs create a `Scenario` object
   - `TCOCalculator` processes the scenario
   - Results are returned as structured data

3. **Output Presentation**:
   - Results are transformed into visualizations
   - Charts and tables are displayed to the user
   - Summary metrics are highlighted

## Technology Stack

- **Backend**: Python 3.9+
- **Web Framework**: Streamlit
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly
- **Data Validation**: Pydantic
- **Configuration**: PyYAML
- **Testing**: Pytest

## Development Considerations

### Performance Optimization
- Use Streamlit caching decorators (`@st.cache_data`, `@st.cache_resource`)
- Perform heavy calculations only when inputs change
- Use efficient data structures for time-series calculations

### Error Handling
- Implement comprehensive input validation
- Provide clear error messages for users
- Use exception handling for graceful error recovery

### Testing Strategy
- Unit tests for individual components
- Integration tests for component interactions
- Scenario-based tests for end-to-end validation

### Security Considerations
- Validate all user inputs
- Avoid executing arbitrary code
- Use secure defaults for all parameters

## Future Extensions

The architecture is designed to accommodate future extensions:

1. **Additional Vehicle Types**
   - Add new vehicle subclasses
   - Extend configuration with new vehicle specifications

2. **Alternative Powertrains**
   - Add new vehicle classes (e.g., `HydrogenVehicle`)
   - Implement appropriate cost components

3. **Enhanced Visualization**
   - Add more advanced chart types
   - Support for comparative visualizations

4. **API Integration**
   - Expose calculator as a REST API
   - Enable integration with other systems

5. **Advanced Scenarios**
   - Support for fleet-level analysis
   - Multi-vehicle comparison
