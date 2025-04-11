3.3 Installing Dependencies
bashpip install -r requirements.txt
If requirements.txt doesn't exist yet, create it with these initial dependencies:
streamlit>=1.24.0
pandas>=1.5.3
numpy>=1.24.3
plotly>=5.14.1
pydantic>=2.0.0
pyyaml>=6.0
openpyxl>=3.1.2
pytest>=7.3.1
Then run the install command above.
3.4 Configuring Git
Set up your Git identity:
bashgit config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
If working on a fork, add the upstream repository:
bashgit remote add upstream https://github.com/original-username/aus-heavy-vehicle-tco.git
3.5 Setting Up Pre-commit Hooks (Optional)
For code quality enforcement, you can set up pre-commit hooks:

Install pre-commit:
bashpip install pre-commit

Create a .pre-commit-config.yaml file in the project root:
yamlrepos:
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

Install the hooks:
bashpre-commit install


4. Creating the Project Structure
Create the project directory structure as outlined in the Code Structure Plan:
bash# Create main directories
mkdir -p tco_model ui utils config/{defaults,scenarios} tests/data

# Create initial files
touch app.py
touch tco_model/{__init__.py,model.py,vehicles.py,components.py,scenarios.py}
touch ui/{__init__.py,layout.py,inputs.py,outputs.py,state.py}
touch utils/{__init__.py,plotting.py,financial.py,data_handlers.py}
touch tests/{__init__.py,test_model.py,test_vehicles.py,test_components.py}
5. Testing the Setup
5.1 Creating a Simple Test App
Create a simple test app to verify the setup:
python# app_test.py
import streamlit as st

st.title("TCO Modeller Setup Test")
st.write("If you can see this, your Streamlit setup is working!")

value = st.slider("Test Slider", 0, 100, 50)
st.write(f"Selected value: {value}")
5.2 Running the Test App
Run the test app to verify Streamlit is working correctly:
bashstreamlit run app_test.py
This should open a browser window with the test app.
5.3 Verifying Package Imports
Create a test script to verify all dependencies are installed correctly:
python# test_imports.py
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
Run the script:
bashpython test_imports.py
You should see "All imports successful!" if everything is set up correctly.
6. IDE Configuration
6.1 Cursor Settings
Configure Cursor for optimal Python and Streamlit development:

Open Settings (File > Preferences > Settings)
Search for and update these settings:

"python.linting.enabled": true
"python.linting.pylintEnabled": true
"python.formatting.provider": "black"
"editor.formatOnSave": true
"editor.codeActionsOnSave": {"source.organizeImports": true}



6.2 Cursor Extensions
Install these recommended extensions for Python development in Cursor:

Python
Pylance
Streamlit for VS Code
Python Docstring Generator
YAML
GitLens
Better Comments

6.3 Cursor AI Configuration
Optimize Cursor AI for the project:

Open Cursor AI Settings
Add the project's documents to the knowledge base:

Technical Architecture Document
Model Design Specifications
Streamlit UI Design Plan
Testing Strategy
AI Collaboration Workflow



6.4 Debugging Configuration
Set up a debugging configuration for Streamlit:

Create a .vscode/launch.json file:
json{
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

This allows you to debug the Streamlit app by pressing F5

7. Database and External Resources
This project primarily uses file-based storage rather than a database, but here's how to set up the necessary resources:
7.1 Configuration Files
Create initial configuration files:
Vehicle Specifications
Create config/defaults/vehicle_specs.yaml:
yaml# Default vehicle specifications
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
Energy Price Projections
Create config/defaults/energy_prices.yaml:
yaml# Energy price projections
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
Battery Cost Projections
Create config/defaults/battery_costs.yaml:
yaml# Battery cost projections (AUD/kWh)
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
7.2 Sample Scenarios
Create a sample scenario:
Create config/scenarios/urban_delivery.yaml:
yamlname: "Urban Delivery"
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
8. Environment Variables
If needed, you can set up environment variables for the project:
8.1 Creating a .env File
Create a .env file in the project root for local development:
# Development settings
DEBUG=True
LOG_LEVEL=DEBUG

# Feature flags
ENABLE_SENSITIVITY_ANALYSIS=True
ENABLE_SCENARIO_COMPARISON=True
8.2 Using Environment Variables
To use environment variables with Streamlit, you can use the streamlit.secrets mechanism:

Create a .streamlit/secrets.toml file:
toml[env]
DEBUG = true
LOG_LEVEL = "DEBUG"
ENABLE_SENSITIVITY_ANALYSIS = true
ENABLE_SCENARIO_COMPARISON = true

Add both .env and .streamlit/secrets.toml to your .gitignore file

9. Development Workflow
9.1 Starting the Development Server
To start the Streamlit development server:
bashstreamlit run app.py
This will automatically reload when you make changes to the code.
9.2 Running Tests
To run the test suite:
bashpytest
For more detailed output:
bashpytest -v
For coverage report:
bashpytest --cov=tco_model --cov=utils
9.3 Git Workflow
Follow this workflow for development:

Create a new branch for each feature/bugfix:
bashgit checkout -b feature/new-feature-name

Make changes and commit regularly:
bashgit add .
git commit -m "Descriptive commit message"

Push changes to your branch:
bashgit push origin feature/new-feature-name

Create a pull request when ready for review
After approval, merge the pull request
Keep your local repository updated:
bashgit checkout main
git pull

11. Performance Optimization
11.1 Streamlit Caching
Use Streamlit's caching mechanisms to improve performance:
python@st.cache_data
def load_data():
    # Data loading operations
    return data

@st.cache_resource
def create_model():
    # Model initialization
    return model
11.2 Profiling
For performance bottlenecks, use Python's profiling tools:
bashpython -m cProfile -o profile.stats app.py
Then analyze with:
bashpip install snakeviz
snakeviz profile.stats