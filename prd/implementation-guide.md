# Implementation Guide

This document provides step-by-step guidance for implementing the Australian Heavy Vehicle TCO Modeller, with particular focus on effective collaboration with AI assistance in Cursor.

## Phase 1: Setup & Core Model Structure

### Step 1: Project Setup

1. **Create Project Structure**
   ```bash
   mkdir -p aus-heavy-vehicle-tco/{tco_model,ui,utils,config/{defaults,scenarios},tests}
   touch aus-heavy-vehicle-tco/{app.py,requirements.txt,README.md}
   ```

2. **Initialize Git Repository**
   ```bash
   cd aus-heavy-vehicle-tco
   git init
   ```

3. **Create Virtual Environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

4. **Install Base Dependencies**
   ```bash
   pip install streamlit pandas numpy plotly pydantic pyyaml pytest
   pip freeze > requirements.txt
   ```

### Step 2: Core Model Implementation

First, create the basic structure and then implement each component iteratively.

#### 1. Create Base Vehicle Classes

**With AI assistance in Cursor**:
1. Create file: `tco_model/vehicles.py`
2. Prompt Cursor with:
   ```
   I need to implement the Vehicle class hierarchy for my TCO model. 
   I need an abstract Vehicle base class with ElectricVehicle and DieselVehicle subclasses. 
   The Vehicle class should have methods for calculating energy consumption, energy cost, and residual value.
   The ElectricVehicle should include battery-specific attributes and methods like battery degradation.
   ```

3. Review and adapt the generated code to match our architecture

**Key implementation details**:
- `Vehicle` as an abstract base class with `@abstractmethod` decorators
- `ElectricVehicle` and `DieselVehicle` inheriting from `Vehicle`
- Implementation of key methods like `calculate_energy_consumption()`, `calculate_energy_cost()`, etc.

#### 2. Create Cost Component Classes

**With AI assistance in Cursor**:
1. Create file: `tco_model/components.py`
2. Prompt Cursor with:
   ```
   I need to implement cost component classes for the TCO model.
   Each component should inherit from an abstract CostComponent base class with a calculate_annual_cost method.
   I need components for: acquisition cost, energy cost, maintenance cost, infrastructure cost, battery replacement cost, insurance cost, registration cost, and residual value.
   ```

3. Review and adapt the generated code

**Key implementation details**:
- `CostComponent` as an abstract base class
- Concrete implementations for each cost category
- Each component handles its specific calculation logic

#### 3. Create Scenario Class

**With AI assistance in Cursor**:
1. Create file: `tco_model/scenarios.py`
2. Prompt Cursor with:
   ```
   I need to implement a Scenario class using Pydantic BaseModel that will store all input parameters for a TCO calculation.
   It should include validation and methods to load/save scenarios from YAML files.
   ```

3. Review and adapt the generated code

**Key implementation details**:
- Use of Pydantic for validation
- Methods for loading/saving to YAML
- Default values and constraints

#### 4. Create TCO Calculator

**With AI assistance in Cursor**:
1. Create file: `tco_model/model.py`
2. Prompt Cursor with:
   ```
   I need to implement the TCOCalculator class that will orchestrate the TCO calculation process.
   It should take a Scenario object and calculate annual costs using the relevant cost components.
   It should produce structured results including total costs, parity year, and levelized cost.
   ```

3. Review and extend the generated code

**Key implementation details**:
- Constructor to initialize components
- Methods for calculating annual costs
- Discounting and aggregation functionality
- Finding parity point and calculating LCOD

### Step 3: Utility Functions

#### 1. Data Handling Utilities

**With AI assistance in Cursor**:
1. Create file: `utils/data_handlers.py`
2. Prompt Cursor with:
   ```
   I need utility functions for loading and manipulating data, including:
   - load_config() to load YAML configuration files
   - load_scenario() and save_scenario() for scenario management
   - export_results_to_excel() for exporting results
   ```

#### 2. Plotting Utilities

**With AI assistance in Cursor**:
1. Create file: `utils/plotting.py`
2. Prompt Cursor with:
   ```
   I need utility functions for creating Plotly charts, including:
   - create_line_chart() for time series data
   - create_stacked_bar_chart() for cost breakdowns
   - create_tornado_chart() for sensitivity analysis
   ```

### Step 4: Configuration Files

Create default configuration files with sample data:

#### 1. Vehicle Specifications

**With AI assistance in Cursor**:
1. Create file: `config/defaults/vehicle_specs.yaml`
2. Prompt Cursor with:
   ```
   Create a YAML configuration file for default vehicle specifications including:
   - Electric rigid and articulated trucks with attributes like purchase price, battery capacity, energy consumption
   - Diesel rigid and articulated trucks with attributes like purchase price, fuel consumption
   ```

#### 2. Energy Price Projections

**With AI assistance in Cursor**:
1. Create file: `config/defaults/energy_prices.yaml`
2. Prompt Cursor with:
   ```
   Create a YAML configuration file for energy price projections from 2025 to 2040 including:
   - Electricity prices for low, medium, and high scenarios
   - Diesel prices for low, medium, and high scenarios
   ```

## Phase 2: Streamlit UI Implementation

### Step 1: Application Entry Point

**With AI assistance in Cursor**:
1. Edit file: `app.py`
2. Prompt Cursor with:
   ```
   Implement the main Streamlit application entry point that:
   - Sets up page configuration
   - Initializes session state
   - Creates the page layout
   - Collects user inputs
   - Calculates TCO results
   - Displays results
   ```

### Step 2: UI Components

#### 1. Layout Module

**With AI assistance in Cursor**:
1. Create file: `ui/layout.py`
2. Prompt Cursor with:
   ```
   Create a module that defines the overall layout of the Streamlit application, including:
   - Title and header
   - Main content area
   - Tab structure for different visualizations
   ```

#### 2. Input Collection

**With AI assistance in Cursor**:
1. Create file: `ui/inputs.py`
2. Prompt Cursor with:
   ```
   Create a module for collecting user inputs through the Streamlit sidebar, organized in expandable sections:
   - General parameters
   - Economic parameters
   - Vehicle parameters (separate for BET and ICE)
   - Energy costs
   - Infrastructure costs
   - Battery replacement options
   - Residual values
   ```

#### 3. Result Display

**With AI assistance in Cursor**:
1. Create file: `ui/outputs.py`
2. Prompt Cursor with:
   ```
   Create a module for displaying TCO results, including:
   - Summary metrics
   - Cumulative TCO chart
   - Cost breakdown chart
   - Sensitivity analysis
   - Detailed data tables
   - Export functionality
   ```

### Step 3: State Management

**With AI assistance in Cursor**:
1. Create file: `ui/state.py`
2. Prompt Cursor with:
   ```
   Create a module for managing Streamlit session state, including:
   - Initialization of state variables
   - Functions for updating state
   - Handling of scenario saving/loading
   ```

## Phase 3: Integration & Testing

### Step 1: Basic Unit Tests

**With AI assistance in Cursor**:
1. Create file: `tests/test_vehicles.py`
2. Prompt Cursor with:
   ```
   Write unit tests for the Vehicle classes, including:
   - Testing energy consumption calculation
   - Testing energy cost calculation
   - Testing residual value calculation
   - Testing battery degradation calculation
   ```

### Step 2: Integration Tests

**With AI assistance in Cursor**:
1. Create file: `tests/test_model.py`
2. Prompt Cursor with:
   ```
   Write integration tests for the TCOCalculator class, including:
   - Testing full calculation flow with a sample scenario
   - Testing parity point calculation
   - Testing sensitivity analysis
   ```

### Step 3: End-to-End Testing

**With AI assistance in Cursor**:
1. Create script: `tests/test_end_to_end.py`
2. Prompt Cursor with:
   ```
   Write an end-to-end test that:
   - Creates a sample scenario
   - Runs the TCO calculation
   - Verifies the results are reasonable
   - Tests exporting to different formats
   ```

## Phase 4: Refinement & Advanced Features

### Step 1: Sensitivity Analysis Implementation

**With AI assistance in Cursor**:
1. Edit file: `tco_model/model.py`
2. Prompt Cursor with:
   ```
   Add a perform_sensitivity_analysis method to the TCOCalculator class that:
   - Takes a baseline scenario
   - Varies key parameters (diesel price, electricity price, etc.) by a specified percentage
   - Calculates the TCO for each variation
   - Returns the impact on TCO difference for each parameter
   ```

### Step 2: Multi-Scenario Comparison

**With AI assistance in Cursor**:
1. Edit files: `ui/inputs.py` and `ui/outputs.py`
2. Prompt Cursor with:
   ```
   Enhance the UI to support multi-scenario comparison:
   - Add a way to save the current scenario
   - Add a dropdown to select saved scenarios for comparison
   - Modify the visualization to show multiple scenarios side by side
   ```

### Step 3: Performance Optimization

**With AI assistance in Cursor**:
1. Review all files for performance bottlenecks
2. Prompt Cursor with:
   ```
   Help me optimize the performance of the application by:
   - Adding appropriate caching decorators (@st.cache_data, @st.cache_resource)
   - Identifying computationally expensive operations
   - Suggesting optimizations for data structures and algorithms
   ```

## Working Effectively with AI Assistance in Cursor

### Tips for Better AI Collaboration

1. **Be Specific in Prompts**:
   Instead of "Help me implement the vehicle class" try "Help me implement the ElectricVehicle class that inherits from Vehicle and includes methods for calculating energy consumption (kWh/km), energy cost, and battery degradation based on age and mileage"

2. **Provide Context**:
   Share relevant parts of your architecture document or requirements when asking for implementation help

3. **Iterative Refinement**:
   Break complex implementations into smaller steps and refine incrementally

4. **Ask for Explanations**:
   When AI generates code you don't fully understand, ask it to explain specific sections

5. **Request Test Cases**:
   Ask AI to generate unit tests for the code it produces

### Example AI Prompts for Key Components

#### Core Model Implementation

```
I'm implementing the TCO model for comparing electric vs. diesel trucks in Australia. 
Here's the code structure I need for the ElectricVehicle class:

1. It should inherit from Vehicle base class
2. Constructor should take: name, purchase_price, annual_mileage, lifespan, battery_capacity, energy_consumption, battery_warranty
3. It needs methods for:
   - calculate_energy_consumption(distance): returns kWh based on energy_consumption attribute
   - calculate_energy_cost(distance, energy_price): returns cost in AUD
   - calculate_battery_degradation(age, total_mileage): returns remaining capacity as fraction (0-1)
   - calculate_residual_value(age): returns value in AUD

Can you implement this class following the design in my architecture document?
```

#### Streamlit UI

```
I'm building the input collection component for my Streamlit TCO calculator.
I need to create sidebar inputs for vehicle parameters with:

1. Expandable sections for "Electric Vehicle Parameters" and "Diesel Vehicle Parameters"
2. In each section, inputs for:
   - Vehicle model name (text input)
   - Purchase price (number input, AUD)
   - For electric: battery capacity (kWh), energy consumption (kWh/km)
   - For diesel: fuel consumption (L/100km)
3. The values should be loaded from defaults but user-adjustable
4. The inputs should be organized logically and include help text

Can you implement the `create_input_sidebar()` function for these sections?
```

#### Data Visualization

```
I need to implement the cumulative TCO comparison chart using Plotly.
It should:

1. Show cumulative costs over time (years) for both electric and diesel
2. Mark the parity point where electric becomes cheaper (if it exists)
3. Have proper formatting (currency, labels, title)
4. Use distinct colors for the two vehicle types
5. Include appropriate hover information

Can you implement the `create_cumulative_tco_chart()` function that takes the results dictionary?
```

### Sample AI Collaboration Workflow

1. **Start with architecture**:
   - Define overall structure
   - Plan class hierarchies and interfaces
   - Document in architecture document

2. **Implement skeleton**:
   - Use AI to generate file/directory structure
   - Create empty class definitions with method signatures

3. **Fill in implementations iteratively**:
   - Focus on one component at a time
   - Ask AI to implement specific methods or classes
   - Review, test, and refine

4. **Integration**:
   - Connect components
   - Test interactions
   - Use AI to identify and fix integration issues

5. **Polish and optimize**:
   - Improve UI/UX
   - Optimize performance
   - Add documentation and comments

By following this guide and leveraging AI effectively, you should be able to implement the Australian Heavy Vehicle TCO Modeller efficiently and with high quality.
