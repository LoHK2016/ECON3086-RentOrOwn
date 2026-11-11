"""Costs of buying and owning a home."""

from rentorbuy.calc.stamp_duty import stamp_duty
from rentorbuy.calc.mortgage import insurance_premium


def upfront_costs(price, valuation, ltv, agent_fee_pct, legal_fee):
    """Cash the buyer pays on day one, item by item.

    The bank lends `ltv` of the lower of the price and its valuation, so a
    valuation below the price makes the down payment bigger.
    """
    loan = round(min(price, valuation) * ltv)
    costs = {
        "loan": loan,
        "down_payment": price - loan,
        "stamp_duty": stamp_duty(price),
        "agent_fee": round(price * agent_fee_pct / 100),
        "legal_fee": legal_fee,
        "insurance_premium": insurance_premium(loan, ltv),
    }
    costs["total_cash"] = (
        costs["down_payment"]
        + costs["stamp_duty"]
        + costs["agent_fee"]
        + costs["legal_fee"]
        + costs["insurance_premium"]
    )
    return costs


def monthly_holding_cost(saleable_area, management_fee_per_ft, monthly_rent, rates_pct, home_value, repair_pct):
    """Owner's monthly costs other than the mortgage.

    - management fee: HK$ per square foot of saleable area
    - rates and government rent: about `rates_pct` % of a year's rent (the rateable value)
    - repairs: `repair_pct` % of the home's value a year
    """
    management = saleable_area * management_fee_per_ft
    rates = monthly_rent * 12 * rates_pct / 100 / 12
    repairs = home_value * repair_pct / 100 / 12
    return management + rates + repairs


def home_equity(home_value, sell_cost_pct, mortgage_left):
    """What the owner would keep after selling and paying off the mortgage."""
    return home_value * (1 - sell_cost_pct / 100) - mortgage_left
