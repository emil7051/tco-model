"""
Financial utility functions for the TCO Model.

This module includes functions for:
- Loan calculations
- Net Present Value (NPV) calculations
- Depreciation calculations
- Other financial utility functions
"""
# Standard library imports
from typing import Dict, List, Optional, Tuple

# Third-party imports
import numpy as np

# Application-specific imports
from config.constants import DEFAULT_PAYMENT_FREQUENCY, PAYMENTS_PER_YEAR
from utils.conversions import percentage_to_decimal


def calculate_loan_payment(
    principal: float,
    interest_rate: float,
    loan_term_years: int,
    payment_frequency: str = DEFAULT_PAYMENT_FREQUENCY
) -> float:
    """
    Calculate regular loan payment using the PMT formula.
    
    Args:
        principal: Loan principal amount
        interest_rate: Annual interest rate as a percentage (e.g., 7.0 for 7%)
        loan_term_years: Loan term in years
        payment_frequency: Frequency of payments ('monthly', 'quarterly', 'annually')
        
    Returns:
        Regular payment amount
    """
    # Convert annual interest rate to decimal
    r = percentage_to_decimal(interest_rate)
    
    # Determine number of payments based on frequency
    payments_per_year = PAYMENTS_PER_YEAR.get(payment_frequency.lower(), 12)  # Default to monthly
    
    # Convert annual rate to rate per payment period
    rate_per_period = r / payments_per_year
    
    # Total number of payments
    n_payments = loan_term_years * payments_per_year
    
    # PMT formula: PMT = P * r * (1 + r)^n / ((1 + r)^n - 1)
    if rate_per_period == 0:
        return principal / n_payments  # Simple division if rate is 0
    
    numerator = rate_per_period * (1 + rate_per_period)**n_payments
    denominator = (1 + rate_per_period)**n_payments - 1
    payment = principal * (numerator / denominator)
    
    return payment


def calculate_loan_schedule(
    principal: float,
    interest_rate: float,
    loan_term_years: int,
    payment_frequency: str = DEFAULT_PAYMENT_FREQUENCY
) -> List[Dict]:
    """
    Generate a complete loan amortization schedule.
    
    Args:
        principal: Loan principal amount
        interest_rate: Annual interest rate as a percentage
        loan_term_years: Loan term in years
        payment_frequency: Frequency of payments ('monthly', 'quarterly', 'annually')
        
    Returns:
        List of dictionaries with payment details for each period
    """
    # Calculate the regular payment amount
    payment = calculate_loan_payment(principal, interest_rate, loan_term_years, payment_frequency)
    
    # Convert annual interest rate to decimal
    r = percentage_to_decimal(interest_rate)
    
    # Determine number of payments based on frequency
    payments_per_year = PAYMENTS_PER_YEAR.get(payment_frequency.lower(), 12)  # Default to monthly
    
    # Convert annual rate to rate per payment period
    rate_per_period = r / payments_per_year
    
    # Total number of payments
    n_payments = loan_term_years * payments_per_year
    
    # Initialize variables
    remaining_principal = principal
    schedule = []
    
    # Generate the schedule
    for period in range(1, n_payments + 1):
        # Calculate interest for this period
        interest_payment = remaining_principal * rate_per_period
        
        # Calculate principal portion of payment
        principal_payment = payment - interest_payment
        
        # Adjust for final payment rounding issues
        if period == n_payments:
            principal_payment = remaining_principal
            payment = principal_payment + interest_payment
        
        # Update remaining principal
        remaining_principal -= principal_payment
        if remaining_principal < 0:
            remaining_principal = 0
        
        # Add to schedule
        schedule.append({
            'period': period,
            'payment': payment,
            'principal': principal_payment,
            'interest': interest_payment,
            'remaining_principal': remaining_principal
        })
    
    return schedule


def calculate_npv(cash_flows: List[float], discount_rate: float) -> float:
    """
    Calculate Net Present Value (NPV) of a series of cash flows.
    
    Args:
        cash_flows: List of cash flows, starting with initial investment (negative)
        discount_rate: Discount rate as a percentage (e.g., 7.0 for 7%)
        
    Returns:
        Net Present Value
    """
    # Convert discount rate to decimal
    r = percentage_to_decimal(discount_rate)
    
    # Calculate NPV
    npv = 0
    for i, cf in enumerate(cash_flows):
        npv += cf / (1 + r) ** i
    
    return npv


def calculate_irr(cash_flows: List[float]) -> Optional[float]:
    """
    Calculate Internal Rate of Return (IRR) of a series of cash flows.
    
    Args:
        cash_flows: List of cash flows, starting with initial investment (negative)
        
    Returns:
        IRR as a percentage, or None if IRR cannot be calculated
    """
    try:
        # Use numpy's IRR function
        irr = np.irr(cash_flows)
        
        # Convert to percentage
        return irr * 100
    except:
        return None


def calculate_straight_line_depreciation(
    cost: float,
    salvage_value: float,
    useful_life_years: int
) -> Tuple[float, List[float]]:
    """
    Calculate straight-line depreciation.
    
    Args:
        cost: Initial cost of the asset
        salvage_value: Expected salvage value at the end of useful life
        useful_life_years: Useful life in years
        
    Returns:
        Tuple of (annual_depreciation, list_of_book_values)
    """
    # Calculate annual depreciation
    annual_depreciation = (cost - salvage_value) / useful_life_years
    
    # Calculate book value for each year
    book_values = []
    remaining_value = cost
    
    for _ in range(useful_life_years + 1):
        book_values.append(remaining_value)
        remaining_value -= annual_depreciation
        # Ensure we don't depreciate below salvage value
        if remaining_value < salvage_value:
            remaining_value = salvage_value
    
    return annual_depreciation, book_values


def calculate_residual_value(
    initial_value: float,
    age_years: int,
    depreciation_rate: float
) -> float:
    """
    Calculate residual value using exponential depreciation.
    
    Args:
        initial_value: Initial value of the asset
        age_years: Age of the asset in years
        depreciation_rate: Annual depreciation rate as a percentage
        
    Returns:
        Residual value
    """
    # Convert depreciation rate to decimal
    r = percentage_to_decimal(depreciation_rate)
    
    # Calculate residual value: V = V₀ * (1 - r)^t
    residual_value = initial_value * (1 - r) ** age_years
    
    return residual_value


def calculate_levelized_cost(
    total_costs: float,
    total_output: float
) -> float:
    """
    Calculate the levelized cost (e.g., per km, per kWh).
    
    Args:
        total_costs: Total discounted costs over the analysis period
        total_output: Total undiscounted output (e.g., km traveled, kWh produced)
        
    Returns:
        Levelized cost per unit of output
    """
    if total_output == 0:
        return float('inf')  # Avoid division by zero
    
    return total_costs / total_output
