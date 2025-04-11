# Development Environment Setup

This document provides detailed instructions for setting up a development environment for the Australian Heavy Vehicle TCO Modeller project, ensuring consistent setup across all contributors.

## 1. System Requirements

### 1.1 Hardware Requirements

- **Processor**: Dual-core processor (quad-core recommended)
- **Memory**: 8GB RAM minimum (16GB recommended)
- **Storage**: 1GB free disk space for the project and dependencies

### 1.2 Software Requirements

- **Operating System**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+ recommended)
- **Python**: Version 3.9 to 3.11
- **Git**: Latest stable version
- **Code Editor**: VS Code with Cursor AI integration (recommended)

## 2. Python Environment Setup

### 2.1 Installing Python

#### Windows
1. Download the Python installer from [python.org](https://www.python.org/downloads/)
2. Run the installer, ensuring you check "Add Python to PATH"
3. Verify installation by running `python --version` in Command Prompt

#### macOS
1. Install Homebrew if not already installed:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. Install Python using Homebrew:
   ```bash
   brew install python@3.11
   ```
3. Verify installation by running `python3 --version` in Terminal

#### Linux (Ubuntu)
1. Update package list:
   ```bash
   sudo apt update
   ```
2. Install Python and development tools:
   ```bash
   sudo apt install python3.11 python3.11-venv python3.11-dev
   ```
3. Verify installation by running `python3.11 --version` in Terminal

### 2.2 Installing Git

#### Windows
1. Download Git from [git-scm.com](https://git-scm.com/download/win)
2. Run the installer with default options
3. Verify installation by running `git --version` in Command Prompt

#### macOS
1. Install Git using Homebrew:
   ```bash
   brew install git
   ```
2. Verify installation by running `git --version` in Terminal

#### Linux (Ubuntu)
1. Install Git:
   ```bash
   sudo apt install git
   ```
2. Verify installation by running `git --version` in Terminal

### 2.3 Setting Up Cursor

Cursor is a code editor built on VS Code with integrated AI assistance, which is ideal for this project.

1. Download Cursor from [cursor.sh](https://cursor.sh/)
2. Install following the on-screen instructions
3. Launch Cursor and sign in
4. Install Python and Streamlit extensions:
   - Python extension
   - Pylance
   - Streamlit for VS Code

## 3. Project Setup

### 3.1 Cloning the Repository

1. Open a terminal or command prompt
2. Clone the repository:
   ```bash
   git clone https://github.com/your-username/aus-heavy-vehicle-tco.git
   cd aus-heavy-vehicle-tco
   ```

### 3.2 Creating a Virtual Environment

#### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3.3 Installing Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist yet, create it with these initial dependencies:

```
streamlit>=1.24.0
pandas>=1.5.3
numpy>=1.24.3
plotly>=5.14.1
pydantic>=2.0.0
pyyaml>=6.0
openpyxl>=3.1.2
pytest>=7.3.1
```

Then run the install command above.

### 3.4 Configuring Git

Set up your Git identity:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

If working on a fork, add the upstream repository:

```bash
git remote add upstream https://github.com/original-username/aus-heavy-vehicle-tco.git
```

### 3.5 Setting Up Pre-commit Hooks (Optional)

For code quality enforcement, you can set up pre-commit hooks:

1. Install pre-commit:
   ```bash
   pip install pre-commit
   ```

2. Create a `.pre-commit-config.yaml` file in the project root:
   ```yaml
   repos:
   - repo: https://github.com/pre-commit/pre-commit-hooks
     rev: v4.4.0
     hooks:
     - id: trailing-whitespace
     - id: end-of-file-fixer
     - id: check-yaml
     - id: check-added-large-files

   - repo: https://github.com/pycqa/flake8
     rev: 6.0.0
     hooks:
     - id: flake8
       additional_dependencies: [flake8-docstrings]

   - repo: https://github.com/pycqa/isort
     rev: 5.12.0
     hooks:
     - id: isort

   - repo: https://github.com/psf/black
     rev: 23.3.0
     hooks:
     - id: black
   ```

3. Install the hooks:
   ```bash
   pre-commit install
   ```

## 4. Creating the Project Structure

Create the project directory structure as outlined in the Code Structure Plan:

```bash
# Create main directories
mkdir -p tco_model ui utils config/{defaults,scenarios} tests/data

# Create initial files
touch app.py
touch tco_model/{__init__.py,model.py,vehicles.py,components.py,scenarios.py}
touch ui/{__init__.py,layout.py,inputs.py,outputs.py,state.py}
touch utils/{__init__.py,plotting.py,financial.py,data_handlers.py}
touch tests/{__init__.py,test_model.py,test_vehicles.py,test_components.py}
```

## 5. Testing the Setup

### 5.1 Creating a Simple Test App

Create a simple test app to verify the setup:

```python
# app_test.py
import streamlit as st

st.title("TCO Modeller Setup Test")
st.write("If you can see this, your Streamlit setup is working!")

value = st.slider("Test Slider", 0, 100, 50)
st.write(f"Selected value: {value}")
```

### 5.2 Running the Test App

Run the test app to verify Streamlit is working correctly:

```bash
streamlit run app_test.py
```

This should open a browser window with the test app.

### 5.3 Verifying Package Imports

Create a test script to verify all dependencies are installed correctly:

```python
# test_imports.py
try:
    import streamlit
    import pandas
    import numpy
    import plotly
    import pydantic
    import yaml
    import pytest
    print("All imports successful!")
except ImportError as e:
    print(f"Import error: {e}")
```

Run the script:

```bash
python test_imports.py
```

You should see "All imports successful!" if everything is set up correctly.

## 6. IDE Configuration

### 6.1 Cursor Settings

Configure Cursor for optimal Python and Streamlit development:

1. Open Settings (File > Preferences > Settings)
2. Search for and update these settings:
   - `"python.linting.enabled": true`
   - `"python.linting.pylintEnabled": true`
   - `"python.formatting.provider": "black"`
   - `"editor.formatOnSave": true`
   - `"editor.codeActionsOnSave": {"source.organizeImports": true}`

### 6.2 Cursor Extensions

Install these recommended extensions for Python development in Cursor:

1. Python
2. Pylance
3. Streamlit for VS Code
4. Python Docstring Generator
5. YAML
6. GitLens
7. Better Comments

### 6.3 Cursor AI Configuration

Optimize Cursor AI for the project:

1. Open Cursor AI Settings
2. Add the project's documents to the knowledge base:
   - Technical Architecture Document
   - Model Design Specifications
   - Streamlit UI Design Plan
   - Testing Strategy
   - AI Collaboration Workflow

### 6.4 Debugging Configuration

Set up a debugging configuration for Streamlit:

1. Create a `.vscode/launch.json` file:
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Streamlit Run",
         "type": "python",
         "request": "launch",
         "module": "streamlit",
         "args": ["run", "app.py"],
         "justMyCode": true
       },
       {
         "name": "Python: Current File",
         "type": "python",
         "request": "launch",
         "program": "${file}",
         "console": "integratedTerminal",
         "justMyCode": true
       }
     ]
   }
   ```

2. This allows you to debug the Streamlit app by pressing F5

## 7. Database and External Resources

This project primarily uses file-based storage rather than a database, but here's how to set up the necessary resources:

### 7.1 Configuration Files

Create initial configuration files:

#### Vehicle Specifications
Create `config/defaults/vehicle_specs.yaml`:

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

#### Energy Price Projections
Create `config/defaults/energy_prices.yaml`:

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

#### Battery Cost Projections
Create `config/defaults/battery_costs.yaml`:

```yaml
# Battery cost projections (AUD/kWh)
baseline:
  2025: 170
  2030: 100
  2035: 75
  2040: 60

conservative:
  2025: 200
  2030: 130
  2035: 100
  2040: 80

optimistic:
  2025: 150
  2030: 80
  2035: 60
  2040: 45
```

### 7.2 Sample Scenarios

Create a sample scenario:

Create `config/scenarios/urban_delivery.yaml`:

```yaml
name: "Urban Delivery"
description: "Urban delivery truck with depot charging"
start_year: 2025
end_year: 2040

# Economic parameters
discount_rate: 0.07
inflation_rate: 0.025
financing_method: "loan"
loan_term: 5
interest_rate: 0.07
down_payment_pct: 0.2

# Operational parameters
annual_mileage: 40000

# Electric vehicle parameters
electric_vehicle_name: "Electric Rigid Truck"
electric_vehicle_price: 400000
electric_vehicle_battery_capacity: 300
electric_vehicle_energy_consumption: 0.9
electric_vehicle_battery_warranty: 8

# Diesel vehicle parameters
diesel_vehicle_name: "Diesel Rigid Truck"
diesel_vehicle_price: 200000
diesel_vehicle_fuel_consumption: 30

# Energy prices
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

# Infrastructure costs
charger_cost: 50000
charger_installation_cost: 50000
charger_lifespan: 10

# Maintenance costs
electric_maintenance_cost_per_km: 0.08
diesel_maintenance_cost_per_km: 0.15

# Insurance costs
electric_insurance_cost_factor: 1.0
diesel_insurance_cost_factor: 1.0

# Registration costs
annual_registration_cost: 5000

# Battery replacement
enable_battery_replacement: false
battery_replacement_threshold: 0.7

# Residual values
electric_residual_value_pct: 0.1
diesel_residual_value_pct: 0.1
```

## 8. Environment Variables

If needed, you can set up environment variables for the project:

### 8.1 Creating a .env File

Create a `.env` file in the project root for local development:

```
# Development settings
DEBUG=True
LOG_LEVEL=DEBUG

# Feature flags
ENABLE_SENSITIVITY_ANALYSIS=True
ENABLE_SCENARIO_COMPARISON=True
```

### 8.2 Using Environment Variables

To use environment variables with Streamlit, you can use the `streamlit.secrets` mechanism:

1. Create a `.streamlit/secrets.toml` file:
   ```toml
   [env]
   DEBUG = true
   LOG_LEVEL = "DEBUG"
   ENABLE_SENSITIVITY_ANALYSIS = true
   ENABLE_SCENARIO_COMPARISON = true
   ```

2. Add both `.env` and `.streamlit/secrets.toml` to your `.gitignore` file

## 9. Development Workflow

### 9.1 Starting the Development Server

To start the Streamlit development server:

```bash
streamlit run app.py
```

This will automatically reload when you make changes to the code.

### 9.2 Running Tests

To run the test suite:

```bash
pytest
```

For more detailed output:

```bash
pytest -v
```

For coverage report:

```bash
pytest --cov=tco_model --cov=utils
```

### 9.3 Git Workflow

Follow this workflow for development:

1. Create a new branch for each feature/bugfix:
   ```bash
   git checkout -b feature/new-feature-name
   ```

2. Make changes and commit regularly:
   ```bash
   git add .
   git commit -m "Descriptive commit message"
   ```

3. Push changes to your branch:
   ```bash
   git push origin feature/new-feature-name
   ```

4. Create a pull request when ready for review

5. After approval, merge the pull request

6. Keep your local repository updated:
   ```bash
   git checkout main
   git pull
   ```

## 10. Troubleshooting

### 10.1 Common Issues

#### Virtual Environment Issues

**Problem**: Python can't find installed packages
**Solution**: Ensure your virtual environment is activated:
- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

#### Streamlit Port Conflicts

**Problem**: Address already in use
**Solution**: Change the Streamlit port:
```bash
streamlit run app.py --server.port=8501
```

#### Package Conflicts

**Problem**: Dependency conflicts
**Solution**: Try creating a fresh environment:
```bash
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Git Problems

**Problem**: Merge conflicts
**Solution**: Resolve conflicts and complete the merge:
```bash
git status  # Identify conflicted files
# Edit the files to resolve conflicts
git add .  # Add resolved files
git commit  # Complete the merge
```

### 10.2 Getting Help

If you encounter issues:

1. Check the project documentation first
2. Search for similar issues in the issue tracker
3. Ask for help in the project's communication channels
4. For Streamlit-specific issues, consult the [Streamlit forum](https://discuss.streamlit.io/)

## 11. Performance Optimization

### 11.1 Streamlit Caching

Use Streamlit's caching mechanisms to improve performance:

```python
@st.cache_data
def load_data():
    # Data loading operations
    return data

@st.cache_resource
def create_model():
    # Model initialization
    return model
```

### 11.2 Profiling

For performance bottlenecks, use Python's profiling tools:

```bash
python -m cProfile -o profile.stats app.py
```

Then analyze with:

```bash
pip install snakeviz
snakeviz profile.stats
```

## Conclusion

You now have a fully configured development environment for the Australian Heavy Vehicle TCO Modeller project. This setup ensures consistency across the development team and provides the tools needed for efficient collaboration.

For further assistance, refer to the other project documentation or contact the project maintainers.
