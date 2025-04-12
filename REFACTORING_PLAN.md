# TCO Model Refactoring Plan

This document outlines the step-by-step plan for improving the Australian Heavy Vehicle TCO Modeller codebase.

## Completed Tasks

### 1.1 Modularize the Preprocessing Logic
- Moved `_preprocess_sidebar_params` from `app.py` to `utils/preprocessing.py`
- Refactored the preprocessing logic into smaller, focused functions
- Added proper error handling and validation
- Updated app.py to use the new module

### 1.2 Clean Up Empty Files
- Implemented proper layout components in `ui/layout.py`
- Implemented unit conversion utilities in `utils/conversions.py`
- Implemented financial calculation utilities in `utils/financial.py`
- Implemented proper validation in `tco_model/validators.py`
- Added common constants to `config/constants.py`
- Implemented `config/scenarios/long_haul.yaml`

### 1.3 Standardize Project Structure
- Create a consistent file naming and organization convention
- Move magic numbers and strings to constants
- Document the project structure in README.md

### 2.1 Centralize Data Handling
- Enhance `utils/data_handlers.py` to handle all data loading
- Implement caching using Streamlit's caching mechanisms
- Create a consistent interface for loading different data types

### 2.3 Improve Data Flow
- Simplify the flow between session state, UI components, and model
- Improve the flattening/unflattening operations
- Use Pydantic models more effectively for validation

#### 3.1 Refactor UI Components
- Split `ui/inputs.py` into multiple focused components (Achieved via deletion and confirmation of existing widget structure)
- Create a component library with reusable UI elements (Implemented via `ui/widgets` structure)
- Implement a more organized layout structure (Implemented via `ui/layouts` and managers)

### 4.1 Refactor Model Calculations
- Simplified the calculation flow in `TCOCalculator` by breaking it into smaller, focused methods
- Split complex methods into smaller functions with clear responsibilities
- Added comprehensive error handling and improved logging
- Created a modular structure for easier maintenance and testing


### 4.3 Optimize Performance
- Implemented NumPy vectorized operations for critical calculation paths
- Created a dedicated optimization module for performance utilities
- Added intelligent caching with parameterized keys
- Implemented batch processing for large datasets to reduce memory pressure
- Optimized memory usage with efficient data structures

## Pending Tasks

### 2. Data Management

#### 2.2 Implement Data Versioning
- [ ] Add versioning for configuration files
- [ ] Create schema validation for YAML configuration files
- [ ] Add documentation on data format specifications

### 3. UI Improvements

#### 3.2 Enhance User Experience
- [x] Add tooltips and help text for complex parameters (Implemented via `help` argument in `st.*` widgets)
- [x] Improve error messages and validation feedback (Improved Pydantic error formatting in sidebar; general errors use `st.error`)
- [x] Implement progressive disclosure for advanced parameters (Implemented via `st.expander`, conditional rendering)

#### 3.3 Optimize UI Rendering
- [x] Cache expensive UI operations (Data loading cached via `@st.cache_data` in `data_handlers`; further UI-specific caching likely not needed)
- [~] Implement responsive design for different screen sizes (Basic responsiveness handled by `st.columns` stacking; advanced layout not implemented)
- [x] Reduce redundant state updates (Addressed by implementing `st.form` for inputs)

### 4. Model Enhancement

#### 4.2 Implement Advanced Features
- [ ] Add sensitivity analysis capabilities
- [ ] Implement scenario comparison feature
- [ ] Add export functionality for results

### 5. Testing and Documentation

#### 5.1 Enhance Test Coverage
- [ ] Implement unit tests for core functionality
- [ ] Add integration tests for UI components
- [ ] Create end-to-end tests for common user flows

#### 5.2 Improve Documentation
- [ ] Add inline documentation for complex functions
- [ ] Create comprehensive user documentation
- [ ] Document the data model and calculation methodology

#### 5.3 Setup CI/CD
- [ ] Implement automated testing
- [ ] Add linting and code quality checks
- [ ] Create a deployment pipeline
