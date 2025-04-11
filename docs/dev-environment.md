# Development Environment Setup



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
