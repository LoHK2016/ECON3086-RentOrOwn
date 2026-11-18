"""Estimate a home-buying budget from income, existing repayments and down payment."""

from rentorbuy.calc.mortgage import DSR_LIMIT, max_ltv, monthly_payment

STRESS_RATE_SHIFT = 2.0
MAX_MORTGAGE_YEARS = 30


def loan_for_monthly_payment(payment, annual_rate, years):
    """Largest loan repaid by `payment` each month over `years`."""
    months = years * 12
    monthly_rate = annual_rate / 100 / 12
    if monthly_rate == 0:
        return payment * months
    return payment * (1 - (1 + monthly_rate) ** -months) / monthly_rate


def assess_affordability(monthly_income, monthly_existing_payments, down_payment_funds, mortgage_rate):
    """Estimate a maximum purchase price using the project's documented HK mortgage rules.

    The down-payment funds cover only the deposit, not stamp duty, fees or insurance.
    The stress result is an illustrative +2 percentage-point check, not a bank approval.
    """
    if monthly_income <= 0:
        raise ValueError("monthly income must be greater than zero")
    if monthly_existing_payments < 0:
        raise ValueError("existing monthly payments cannot be negative")
    if down_payment_funds < 0:
        raise ValueError("down-payment funds cannot be negative")
    if mortgage_rate < 0:
        raise ValueError("mortgage rate cannot be negative")

    available_payment = max(0, monthly_income * DSR_LIMIT - monthly_existing_payments)
    income_based_loan = loan_for_monthly_payment(
        available_payment, mortgage_rate, MAX_MORTGAGE_YEARS
    )

    def affordable(price):
        loan = min(income_based_loan, price * max_ltv(price, first_time=False))
        return price - loan <= down_payment_funds

    low = 0.0
    high = income_based_loan + down_payment_funds
    for _ in range(80):
        middle = (low + high) / 2
        if affordable(middle):
            low = middle
        else:
            high = middle

    property_price = low
    ltv = max_ltv(property_price, first_time=False) if property_price else 0
    mortgage = min(income_based_loan, property_price * ltv)
    payment = monthly_payment(mortgage, mortgage_rate, MAX_MORTGAGE_YEARS) if mortgage else 0
    stress_payment = (
        monthly_payment(mortgage, mortgage_rate + STRESS_RATE_SHIFT, MAX_MORTGAGE_YEARS)
        if mortgage
        else 0
    )
    dti = (monthly_existing_payments + payment) / monthly_income
    stress_dti = (monthly_existing_payments + stress_payment) / monthly_income

    return {
        "maximum_mortgage": mortgage,
        "maximum_property_price": property_price,
        "monthly_mortgage_payment": payment,
        "debt_to_income_ratio": dti,
        "stress_rate": mortgage_rate + STRESS_RATE_SHIFT,
        "stress_monthly_mortgage_payment": stress_payment,
        "stress_debt_to_income_ratio": stress_dti,
        "stress_test_passes": stress_dti <= DSR_LIMIT,
        "ltv": ltv,
        "mortgage_years": MAX_MORTGAGE_YEARS,
    }
