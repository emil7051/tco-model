"""
Constants used throughout the TCO Model application.

This file contains all common constants to avoid magic numbers and strings in the codebase.
"""

# ===== General Constants =====
DEFAULT_DESCRIPTION = ""
DEFAULT_SCENARIO_NAME = "New Scenario"
CURRENT_YEAR = 2023  # Default year for calculations - could be replaced with dynamic datetime.now().year
DEFAULT_CURRENCY = "AUD"  # Default currency for calculations and display

# ===== Economic Constants =====
DEFAULT_DISCOUNT_RATE = 7.0  # %
DEFAULT_INFLATION_RATE = 2.5  # %
DEFAULT_INTEREST_RATE = 7.0  # %
DEFAULT_DOWN_PAYMENT_PCT = 20.0  # %
DEFAULT_CARBON_TAX_RATE = 30.0  # AUD/tonne CO2e
DEFAULT_ROAD_USER_CHARGE = 0.0  # AUD/km

# ===== Loan and Payment Constants =====
DEFAULT_PAYMENT_FREQUENCY = "monthly"
PAYMENTS_PER_YEAR = {
    "monthly": 12,
    "quarterly": 4,
    "annually": 1
}

# ===== Analysis Constants =====
DEFAULT_ANALYSIS_YEARS = 15
MIN_ANALYSIS_YEARS = 1
MAX_ANALYSIS_YEARS = 30
DEFAULT_ANNUAL_MILEAGE = 40000.0  # km

# ===== Vehicle Constants =====
# Electric Vehicle
DEFAULT_EV_NAME = "EV Default"
DEFAULT_EV_PRICE = 400000.0  # AUD
DEFAULT_EV_BATTERY_CAPACITY = 300.0  # kWh
DEFAULT_EV_ENERGY_CONSUMPTION = 0.7  # kWh/km
DEFAULT_EV_BATTERY_WARRANTY = 8  # years

# Diesel Vehicle
DEFAULT_DIESEL_NAME = "Diesel Default"
DEFAULT_DIESEL_PRICE = 200000.0  # AUD
DEFAULT_DIESEL_FUEL_CONSUMPTION = 28.6  # L/100km

# ===== Infrastructure Constants =====
DEFAULT_CHARGER_COST = 50000.0  # AUD
DEFAULT_CHARGER_INSTALLATION_COST = 55000.0  # AUD
DEFAULT_CHARGER_LIFESPAN = 10  # years
DEFAULT_CHARGER_MAINTENANCE_PCT = 1.5  # % of capital cost

# ===== Registration and Insurance =====
DEFAULT_ANNUAL_REGISTRATION_COST = 5000.0  # AUD

# ===== Battery Replacement =====
DEFAULT_BATTERY_REPLACEMENT_YEAR = 8  # Year index when battery replacement occurs
DEFAULT_BATTERY_REPLACEMENT_THRESHOLD = 70.0  # % capacity threshold for replacement

# ===== Cost Increase Rates =====
DEFAULT_COST_INCREASE_RATE = 0.0  # % annual real increase for various costs

# ===== File Paths =====
DEFAULT_CONFIG_DIR = "config"
SCENARIOS_DIR = f"{DEFAULT_CONFIG_DIR}/scenarios"
DEFAULTS_DIR = f"{DEFAULT_CONFIG_DIR}/defaults"

# ===== Calculation Constants =====
DIESEL_CO2_EMISSION_FACTOR = 2.68  # kg CO2e/L of diesel
DIESEL_ENERGY_CONTENT = 10.0  # kWh/L of diesel
KWH_TO_MJ_FACTOR = 3.6  # 1 kWh = 3.6 MJ

# ===== Conversion Constants =====
MJ_TO_KWH_FACTOR = 1 / KWH_TO_MJ_FACTOR  # 1 MJ = 1/3.6 kWh
L_TO_KM_FACTOR = 100  # 1 L/100km = 1 km/L
KM_TO_MILES_FACTOR = 0.621371  # 1 km = 0.621371 miles
MILES_TO_KM_FACTOR = 1 / KM_TO_MILES_FACTOR  # 1 mile = 1/0.621371 km

# ===== UI Constants =====
# Page Configuration
PAGE_TITLE = "Heavy Vehicle TCO Modeller"
PAGE_ICON = "🚚"
PAGE_LAYOUT = "wide"
SIDEBAR_STATE = "expanded"

# Headings and Text
APP_TITLE = "Australian Heavy Vehicle TCO Modeller"
APP_DESCRIPTION = """
Compare the Total Cost of Ownership (TCO) for Battery Electric Trucks (BETs) 
and Internal Combustion Engine (ICE) diesel trucks in Australia.

Adjust parameters in the sidebar to customize your analysis.
"""

# Status Messages
SCENARIO_SUCCESS_MSG = "Scenario parameters loaded successfully."
SCENARIO_CONFIG_ERROR_MSG = "Scenario Configuration Error:"
CALCULATION_ERROR_MSG = "Error during TCO calculation:"
CALCULATION_SPINNER_MSG = "Calculating TCO... Please wait."
