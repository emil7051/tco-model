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

#### 3.1 Refactor UI Components
- [ ] Split `ui/inputs.py` into multiple focused components
- [ ] Create a component library with reusable UI elements
- [ ] Implement a more organized layout structure

#### 3.2 Enhance User Experience
- [ ] Add tooltips and help text for complex parameters
- [ ] Improve error messages and validation feedback
- [ ] Implement progressive disclosure for advanced parameters

#### 3.3 Optimize UI Rendering
- [ ] Cache expensive UI operations
- [ ] Implement responsive design for different screen sizes
- [ ] Reduce redundant state updates

### 4. Model Enhancement

#### 4.1 Refactor Model Calculations
- [x] Simplify the calculation flow in `TCOCalculator`
- [x] Split complex methods into smaller functions
- [x] Improve error handling and reporting

#### 4.2 Implement Advanced Features
- [ ] Add sensitivity analysis capabilities
- [ ] Implement scenario comparison feature
- [ ] Add export functionality for results

#### 4.3 Optimize Performance
- [x] Profile and optimize calculation bottlenecks
- [x] Implement more effective caching strategies
- [x] Reduce memory usage for large datasets

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

## Implementation Order

The recommended order for implementing these changes is:

### Phase 1: Foundation Improvements 
1. Clean up empty files (Task 1.2)
2. Standardize project structure (Task 1.3)
3. Add constants and basic validation (Tasks 1.2, 1.3) 
4. Improve documentation (Task 5.2 - initial phase)

### Phase 2: Data Layer Improvements
1. Centralize data handling (Task 2.1)
2. Improve data flow (Task 2.3)
3. Implement data versioning (Task 2.2)
4. Add tests for data layer (Task 5.1 - partial)

### Phase 3: Model Layer Improvements
1. Refactor model calculations (Task 4.1)
2. Optimize performance (Task 4.3)
3. Add tests for model layer (Task 5.1 - partial)

### Phase 4: UI Layer Improvements
1. Refactor UI components (Task 3.1)
2. Enhance user experience (Task 3.2)
3. Optimize UI rendering (Task 3.3)
4. Add tests for UI layer (Task 5.1 - partial)

### Phase 5: Advanced Features and Finalization
1. Implement advanced features (Task 4.2)
2. Complete comprehensive documentation (Task 5.2 - final)
3. Set up CI/CD (Task 5.3)

## Best Practices and Guidelines

Throughout implementation, adhere to these guiding principles:

### Clean Code Principles
- Replace magic numbers with named constants
- Use meaningful names for variables, functions, and classes
- Make code self-documenting (with smart comments where necessary)
- Ensure each function does exactly one thing
- Follow DRY (Don't Repeat Yourself) principle
- Keep related code together in a logical structure
- Encapsulate implementation details properly

### Testing Strategy
- Write tests before fixing bugs
- Keep tests readable and maintainable
- Test edge cases and error conditions

### Documentation Guidelines
- Document the "why" not just the "what"
- Keep documentation close to the code
- Use consistent formatting and structure

### Performance Considerations
- Use Streamlit's caching mechanisms appropriately
- Optimize data loading and processing
- Profile code to identify bottlenecks 