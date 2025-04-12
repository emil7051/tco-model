# Australian Heavy Vehicle TCO Modeller

A comprehensive Total Cost of Ownership (TCO) model for comparing Battery Electric Trucks (BETs) and Internal Combustion Engine (ICE) diesel trucks in Australia (2025-2040).

## Project Overview

This application provides a robust Python-based TCO modelling tool with an interactive Streamlit web interface that helps fleet operators, policymakers, and investors make data-driven decisions about heavy vehicle electrification in Australia. The model compares the 15-year total cost of ownership between electric and diesel trucks across different operational scenarios.

### Key Features

- **Comprehensive TCO Calculation**: Includes acquisition, energy, maintenance, infrastructure, battery replacement, residual value, and more
- **Multiple Vehicle Types**: Supports rigid and articulated trucks for urban delivery, regional freight, and long-haul applications
- **Customisable Inputs**: Adjust prices, utilisation, economic parameters, and more to reflect specific operational contexts
- **Interactive Visualisations**: Dynamic charts for TCO evolution, cost breakdowns, and parity points
- **Sensitivity Analysis**: Identify which factors have the greatest impact on TCO outcomes
- **Australian Context**: Built specifically with Australian market data, costs, and regulations in mind
- **High Performance**: Optimized calculation engine with vectorized operations and caching for fast analysis
- **Modular Architecture**: Clean separation of concerns for easy extensibility and maintenance

## Installation

### Prerequisites

- Python 3.9 or higher
- Git

### Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/aus-heavy-vehicle-tco.git
   cd aus-heavy-vehicle-tco
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application Locally

Start the Streamlit application:

```bash
streamlit run app.py
```

This will open the application in your default web browser at http://localhost:8501.

### Using the TCO Model

1. **Input Parameters**: Use the sidebar to adjust parameters for your specific scenario:
   - Vehicle specifications (type, powertrain, purchase price, etc.)
   - Operational parameters (annual mileage, utilisation, etc.)
   - Economic factors (discount rate, financing terms, etc.)
   - Energy costs (diesel price, electricity rates, etc.)
   - Incentives and policies

2. **Results**: View the results in the main panel:
   - Comparative TCO over the 15-year period
   - Cost breakdown by component
   - Parity point analysis
   - Sensitivity charts
   - Levelised cost per kilometre

3. **Export**: Download the results as CSV or Excel files for further analysis.

## Project Structure

```
tco-model/
├── app.py                   # Main Streamlit application entry point
├── requirements.txt         # Project dependencies
├── README.md                # This file
├── REFACTORING_PLAN.md      # Documentation of refactoring tasks and progress
├── tco_model/               # Core TCO calculation logic
│   ├── __init__.py
│   ├── model.py             # TCO model core classes
│   ├── components.py        # Cost component classes
│   ├── optimizations.py     # Performance optimization utilities
│   ├── scenarios.py         # Scenario management
│   ├── validators.py        # Data validation logic
│   └── vehicles.py          # Vehicle classes
├── ui/                      # User interface components
│   ├── __init__.py
│   ├── inputs.py            # Input form components
│   ├── layout.py            # Page layout components
│   ├── outputs.py           # Results visualization components
│   └── state.py             # Session state management
├── utils/                   # Utility functions and helpers
│   ├── __init__.py
│   ├── conversions.py       # Unit conversion utilities
│   ├── data_handlers.py     # Data loading/parsing utilities
│   ├── financial.py         # Financial calculation utilities
│   ├── plotting.py          # Chart generation functions
│   └── preprocessing.py     # Parameter preprocessing utilities
├── config/                  # Configuration and constants
│   ├── constants.py         # Application-wide constants
│   ├── defaults/            # Default configuration files
│   └── scenarios/           # Predefined scenario configurations
└── tests/                   # Test suite
    ├── __init__.py
    ├── test_components.py   # Tests for cost components
    ├── test_model.py        # Tests for TCO model
    ├── test_scenarios.py    # Tests for scenario handling
    └── test_vehicles.py     # Tests for vehicle models
```

## Documentation

Additional documentation can be found in the `docs/` directory:

- [Technical Architecture](docs/architecture.md)
- [Model Design Specifications](docs/model_design.md)
- [Implementation Guide](docs/implementation_guide.md)
- [UI Design Plan](docs/ui_design.md)
- [Testing Strategy](docs/testing.md)

## Recent Improvements

As outlined in the [Refactoring Plan](REFACTORING_PLAN.md), the following enhancements have been implemented:

### Model Optimization

- **Modular Calculation Logic**: The TCO calculation flow has been reorganized into smaller, focused methods for better maintainability
- **Vectorized Operations**: Replaced iterative calculations with NumPy vectorized operations for significant performance improvements
- **Batch Processing**: Implemented batch processing for large datasets to reduce memory pressure and improve calculation speed
- **Improved Caching**: Added an intelligent caching system to avoid redundant calculations
- **Enhanced Performance Monitoring**: Added comprehensive performance tracking to identify and address bottlenecks
- **Better Error Handling**: Improved error reporting and recovery mechanisms throughout the calculation pipeline

### Architecture Improvements

- **Dedicated Optimizations Module**: Centralized performance utilities in a reusable module
- **Simplified API**: Streamlined the model interface for easier integration and testing
- **Consistent Naming Conventions**: Standardized naming throughout the codebase for better readability
- **Enhanced Documentation**: Added comprehensive docstrings and code comments

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Data sources include Australian Trucking Association, CSIRO, and ARENA
- Model methodology adapted from established TCO frameworks
