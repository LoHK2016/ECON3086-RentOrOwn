"""Mortgage rules: the interest rate, the monthly payment, the loan cap and mortgage insurance.

Rules come from docs/research/hk-property-rules-2026-11.md, sections 2 to 4.
Rates are percentages per year, e.g. 3.25 means 3.25% a year.
"""

DSR_LIMIT = 0.50  # Banks cap the debt servicing ratio at 50%.


def effective_rate(hibor, spread, prime, prime_discount):
    """Rate of an H-plan: HIBOR plus a spread, but never above prime minus a discount (the cap)."""
    hibor_rate = hibor + spread
    capped_rate = prime - prime_discount
    return min(hibor_rate, capped_rate)


def monthly_payment(loan, annual_rate, years):
    """Fixed monthly payment that pays off `loan` in `years` at `annual_rate` %."""
    months = years * 12
    r = annual_rate / 100 / 12
    if r == 0:
        return loan / months
    return loan * r / (1 - (1 + r) ** -months)


def balance_after(loan, annual_rate, years, months_paid):
    """Loan still owed after `months_paid` monthly payments."""
    months = years * 12
    if months_paid >= months:
        return 0.0
    r = annual_rate / 100 / 12
    if r == 0:
        return loan * (1 - months_paid / months)
    payment = monthly_payment(loan, annual_rate, years)
    grown = (1 + r) ** months_paid
    return loan * grown - payment * (grown - 1) / r


def max_ltv(price, first_time):
    """Highest loan-to-value with HKMC mortgage insurance (70% without it).

    90% needs every buyer to own no other HK home and be salaried; we treat
    that as `first_time`.
    """
    if price <= 10_000_000:
        if first_time:
            return 0.90
        return 0.80
    if price < 11_250_000:
        if first_time:
            return min(0.90, 9_000_000 / price)  # loan capped at $9M
        return 0.80
    if price <= 15_000_000:
        return 0.80
    if price <= 17_150_000:
        return min(0.80, 12_000_000 / price)  # loan capped at $12M
    return 0.70


# PROVISIONAL: one-off premium as a share of the loan, by loan-to-value.
# Finance teammates will replace this with the HKMC premium table.
INSURANCE_PREMIUM_RATES = [
    (0.70, 0.000),  # up to 70%: no insurance needed
    (0.80, 0.014),
    (0.85, 0.020),
    (0.90, 0.031),
]


def insurance_premium(loan, ltv):
    """One-off mortgage insurance premium in HK$ for a loan at `ltv`."""
    for top_ltv, rate in INSURANCE_PREMIUM_RATES:
        if ltv <= top_ltv + 1e-9:
            return round(loan * rate)
    raise ValueError(f"loan-to-value {ltv:.0%} is above the 90% limit")


def debt_servicing_ratio(payment, monthly_income):
    """Monthly payment as a share of monthly income, or None if income is not given."""
    if not monthly_income:
        return None
    return payment / monthly_income
