"""
Financial utility functions for the TCO Model.

This module includes functions for:
- Loan calculations
- Net Present Value (NPV) calculations
- Depreciation calculations
- Other financial utility functions
"""
# Standard library imports
from typing import Dict, List, Optional, Tuple, NewType, Union, TypedDict

# Third-party imports
import numpy as np

# Application-specific imports
from config.constants import DEFAULT_PAYMENT_FREQUENCY, PAYMENTS_PER_YEAR
from utils.conversions import percentage_to_decimal, Decimal, Percentage # Import custom types

# Custom Types for Financial Domain
AUD = NewType('AUD', float)
Years = NewType('Years', int)
Rate = NewType('Rate', float) # Generic rate, could be interest or discount
PaymentFrequency = NewType('PaymentFrequency', str) # e.g., 'monthly', 'annually'
PeriodNumber = NewType('PeriodNumber', int)

class LoanPaymentDetails(TypedDict):
    period: PeriodNumber
    payment: AUD
    principal: AUD
    interest: AUD
    remaining_principal: AUD

def calculate_loan_payment(
    principal: AUD,
    interest_rate: Percentage,
    loan_term_years: Years,
    payment_frequency: PaymentFrequency = PaymentFrequency(DEFAULT_PAYMENT_FREQUENCY)
) -> AUD:
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
    # Convert annual interest rate percentage to decimal rate
    r_decimal: Decimal = percentage_to_decimal(interest_rate)
    
    # Determine number of payments based on frequency
    payments_per_year: int = PAYMENTS_PER_YEAR.get(payment_frequency.lower(), 12)  # Default to monthly
    
    # Convert annual rate to rate per payment period
    rate_per_period: Rate = Rate(r_decimal / payments_per_year)
    
    # Total number of payments
    n_payments: int = loan_term_years * payments_per_year
    
    # PMT formula: PMT = P * r * (1 + r)^n / ((1 + r)^n - 1)
    if rate_per_period == 0:
        # Simple division if rate is 0
        return AUD(principal / n_payments) 
    
    numerator = rate_per_period * (1 + rate_per_period)**n_payments
    denominator = (1 + rate_per_period)**n_payments - 1
    payment: float = principal * (numerator / denominator)
    
    return AUD(payment)


def calculate_loan_schedule(
    principal: AUD,
    interest_rate: Percentage,
    loan_term_years: Years,
    payment_frequency: PaymentFrequency = PaymentFrequency(DEFAULT_PAYMENT_FREQUENCY)
) -> List[LoanPaymentDetails]:
    """
    Generate a complete loan amortization schedule.
    
    Args:
        principal: Loan principal amount
        interest_rate: Annual interest rate as a percentage
        loan_term_years: Loan term in years
        payment_frequency: Frequency of payments ('monthly', 'quarterly', 'annually')
        
    Returns:
        List of dictionaries (LoanPaymentDetails) with payment details for each period
    """
    # Calculate the regular payment amount
    regular_payment: AUD = calculate_loan_payment(principal, interest_rate, loan_term_years, payment_frequency)
    
    # Convert annual interest rate percentage to decimal rate
    r_decimal: Decimal = percentage_to_decimal(interest_rate)
    
    # Determine number of payments based on frequency
    payments_per_year: int = PAYMENTS_PER_YEAR.get(payment_frequency.lower(), 12)  # Default to monthly
    
    # Convert annual rate to rate per payment period
    rate_per_period: Rate = Rate(r_decimal / payments_per_year)
    
    # Total number of payments
    n_payments: int = loan_term_years * payments_per_year
    
    # Initialize variables
    remaining_principal: AUD = principal
    schedule: List[LoanPaymentDetails] = []
    
    # Generate the schedule
    for period_num in range(1, n_payments + 1):
        # Calculate interest for this period
        interest_payment: AUD = AUD(remaining_principal * rate_per_period)
        
        # Calculate principal portion of payment
        principal_payment: AUD = AUD(regular_payment - interest_payment)
        
        # Adjust for final payment rounding issues
        current_payment = regular_payment
        if period_num == n_payments:
            # Ensure final principal payment clears the balance exactly
            principal_payment = remaining_principal 
            # Adjust final payment amount based on recalculated principal
            current_payment = AUD(principal_payment + interest_payment)
            remaining_principal = AUD(0.0)
        else:
             # Update remaining principal normally
            remaining_principal = AUD(remaining_principal - principal_payment)
            # Ensure principal doesn't go negative due to potential float issues
            if remaining_principal < 0:
                remaining_principal = AUD(0.0)
        
        # Add to schedule
        payment_details: LoanPaymentDetails = {
            'period': PeriodNumber(period_num),
            'payment': current_payment,
            'principal': principal_payment,
            'interest': interest_payment,
            'remaining_principal': remaining_principal
        }
        schedule.append(payment_details)
    
    return schedule


def calculate_npv(cash_flows: List[AUD], discount_rate: Percentage) -> AUD:
    """
    Calculate Net Present Value (NPV) of a series of cash flows.
    
    Args:
        cash_flows: List of cash flows, starting with initial investment (negative)
        discount_rate: Discount rate as a percentage (e.g., 7.0 for 7%)
        
    Returns:
        Net Present Value
    """
    # Convert discount rate percentage to decimal rate
    r_decimal: Decimal = percentage_to_decimal(discount_rate)
    
    # Calculate NPV using list comprehension for conciseness
    npv_float: float = sum(cf / (1 + r_decimal) ** i for i, cf in enumerate(cash_flows))
    
    return AUD(npv_float)


def calculate_irr(cash_flows: List[AUD]) -> Optional[Percentage]:
    """
    Calculate Internal Rate of Return (IRR) of a series of cash flows.
    
    Args:
        cash_flows: List of cash flows, starting with initial investment (negative)
        
    Returns:
        IRR as a percentage, or None if IRR cannot be calculated
    """
    try:
        # Use numpy's IRR function
        # Convert AUD list to simple list of floats for numpy
        cash_flows_float = [float(cf) for cf in cash_flows]
        irr_decimal: float = np.irr(cash_flows_float)
        
        # Check if irr result is valid (numpy might return nan)
        if np.isnan(irr_decimal) or np.isinf(irr_decimal):
             return None
        
        # Convert to percentage
        return Percentage(irr_decimal * 100.0)
    except ValueError: # Catch numpy's specific error for invalid cash flows
        return None
    except Exception: # Catch any other unexpected errors
        # Consider logging the error here
        return None


def calculate_straight_line_depreciation(
    cost: AUD,
    salvage_value: AUD,
    useful_life_years: Years
) -> Tuple[AUD, List[AUD]]:
    """
    Calculate straight-line depreciation.
    
    Args:
        cost: Initial cost of the asset
        salvage_value: Expected salvage value at the end of useful life
        useful_life_years: Useful life in years
        
    Returns:
        Tuple of (annual_depreciation, list_of_book_values for years 0 to useful_life_years)
    """
    if useful_life_years <= 0:
        # Handle invalid useful life
        return AUD(0.0), [cost]
        
    # Calculate annual depreciation
    depreciable_amount: AUD = AUD(cost - salvage_value)
    # Ensure depreciable amount is not negative
    depreciable_amount = max(AUD(0.0), depreciable_amount)
    annual_depreciation: AUD = AUD(depreciable_amount / useful_life_years)
    
    # Calculate book value for each year (including year 0)
    book_values: List[AUD] = []
    current_book_value: AUD = cost
    
    for year in range(useful_life_years + 1):
        book_values.append(current_book_value)
        # Only depreciate if not the last value (which is already appended)
        if year < useful_life_years:
            current_book_value = AUD(current_book_value - annual_depreciation)
            # Ensure we don't depreciate below salvage value
            current_book_value = max(salvage_value, current_book_value)
    
    return annual_depreciation, book_values


def calculate_residual_value(
    initial_value: AUD,
    age_years: Years,
    depreciation_rate: Percentage
) -> AUD:
    """
    Calculate residual value using exponential depreciation.
    
    Args:
        initial_value: Initial value of the asset
        age_years: Age of the asset in years
        depreciation_rate: Annual depreciation rate as a percentage
        
    Returns:
        Residual value
    """
    # Convert depreciation rate percentage to decimal rate
    r_decimal: Decimal = percentage_to_decimal(depreciation_rate)
    
    # Calculate residual value: V = V₀ * (1 - r)^t
    # Ensure the rate is capped at 100% (decimal 1.0)
    effective_rate = min(r_decimal, Decimal(1.0))
    residual_value_float: float = initial_value * (1 - effective_rate) ** age_years
    
    # Ensure residual value is not negative
    return AUD(max(0.0, residual_value_float))


def calculate_levelized_cost(
    total_costs: AUD, # Should be the Net Present Value of all costs
    total_output: float # e.g., total km, total kWh (undiscounted)
) -> float: # Cost per unit of output (e.g., AUD/km, AUD/kWh)
    """
    Calculate the levelized cost (e.g., per km, per kWh).
    
    Args:
        total_costs: Total discounted costs (NPV) over the analysis period
        total_output: Total undiscounted output (e.g., km traveled, kWh produced)
        
    Returns:
        Levelized cost per unit of output (float, as units might vary)
    """
    if total_output == 0:
        return float('inf')  # Avoid division by zero, represent as infinity
    
    # The result is cost per unit, so it's a float, not necessarily AUD
    return float(total_costs / total_output)
