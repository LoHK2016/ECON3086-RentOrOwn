"""Estimate a home-buying budget from income, existing repayments and down payment."""

from rentorbuy.calc.mortgage import DSR_LIMIT, effective_rate, max_ltv, monthly_payment

# HKMA's stress test assumed rates 2 points (200 basis points) higher. It has been
# suspended since 28 Feb 2024 (docs/research/hk-property-rules-2026-11.md), so the
# page shows it only as a what-if.
STRESS_RATE_SHIFT = 2.0
MAX_MORTGAGE_YEARS = 30


def loan_for_monthly_payment(payment, annual_rate, years):
    """Largest loan repaid by `payment` each month over `years`."""
    months = years * 12
    monthly_rate = annual_rate / 100 / 12
    if monthly_rate == 0:
        return payment * months
    return payment * (1 - (1 + monthly_rate) ** -months) / monthly_rate


def maximum_price(available_payment, down_payment_funds, mortgage_rate):
    """The dearest home the payment and the cash allow: (price, loan).

    The loan is the smaller of what `available_payment` repays over 30 years and
    the loan-to-value cap for that price (non-first-time tiers); the cash covers
    the rest of the price. Found by halving the search range 80 times.
    """
    income_loan = loan_for_monthly_payment(available_payment, mortgage_rate, MAX_MORTGAGE_YEARS)

    def loan(price):
        return min(income_loan, price * max_ltv(price, first_time=False))

    low = 0.0
    high = income_loan + down_payment_funds
    for _ in range(80):
        middle = (low + high) / 2
        if middle - loan(middle) <= down_payment_funds:
            low = middle
        else:
            high = middle
    return low, loan(low)


def assess_affordability(monthly_income, monthly_existing_payments, down_payment_funds, mortgage_rate):
    """Estimate a maximum purchase price using the project's documented HK mortgage rules.

    The down-payment funds cover only the deposit, not stamp duty, fees or insurance.
    The stress figures show the same budget if rates were STRESS_RATE_SHIFT points
    higher: the payment on today's loan, and the lower price that would then fit.
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
    price, mortgage = maximum_price(available_payment, down_payment_funds, mortgage_rate)
    payment = monthly_payment(mortgage, mortgage_rate, MAX_MORTGAGE_YEARS) if mortgage else 0

    stress_rate = mortgage_rate + STRESS_RATE_SHIFT
    stress_payment = monthly_payment(mortgage, stress_rate, MAX_MORTGAGE_YEARS) if mortgage else 0
    stress_price, _ = maximum_price(available_payment, down_payment_funds, stress_rate)

    return {
        "mortgage_rate": mortgage_rate,
        "maximum_mortgage": mortgage,
        "maximum_property_price": price,
        "monthly_mortgage_payment": payment,
        "debt_to_income_ratio": (monthly_existing_payments + payment) / monthly_income,
        "ltv": mortgage / price if price else 0,
        "mortgage_years": MAX_MORTGAGE_YEARS,
        "stress_rate": stress_rate,
        "stress_monthly_mortgage_payment": stress_payment,
        "stress_debt_to_income_ratio": (monthly_existing_payments + stress_payment) / monthly_income,
        "stress_maximum_property_price": stress_price,
    }


def plan_rate(rates):
    """The mortgage rate of the chosen plan.

    `rates` has hibor, hibor_spread, prime and prime_discount. If it also has a
    "p_rate" (a Small P or Big P plan), that rate is used as it is; otherwise the
    H-plan rate: HIBOR plus the spread, capped at prime minus the discount.
    """
    if rates.get("p_rate") is not None:
        return rates["p_rate"]
    return effective_rate(rates["hibor"], rates["hibor_spread"], rates["prime"], rates["prime_discount"])


def affordability_for_plan(monthly_income, monthly_existing_payments, down_payment_funds, rates):
    """assess_affordability at the chosen plan's rate (see plan_rate). This is what the page calls."""
    return assess_affordability(
        monthly_income, monthly_existing_payments, down_payment_funds, plan_rate(rates)
    )
