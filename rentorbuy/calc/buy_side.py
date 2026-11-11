"""Costs of buying and owning a home."""

from rentorbuy.calc.stamp_duty import stamp_duty
from rentorbuy.calc.mortgage import insurance_premium


def upfront_costs(price, valuation, ltv, agent_fee_pct, legal_fee, cash_rebate_pct=0):
    """Cash the buyer pays on day one, item by item.

    The bank lends `ltv` of the lower of the price and its valuation, so a
    valuation below the price makes the down payment bigger. Banks give back
    a cash rebate of `cash_rebate_pct` % of the loan, which lowers the cash needed.
    """
    loan = round(min(price, valuation) * ltv)
    costs = {
        "loan": loan,
        "down_payment": price - loan,
        "stamp_duty": stamp_duty(price),
        "agent_fee": round(price * agent_fee_pct / 100),
        "legal_fee": legal_fee,
        "insurance_premium": insurance_premium(loan, ltv),
        "cash_rebate": round(loan * cash_rebate_pct / 100),
    }
    costs["total_cash"] = (
        costs["down_payment"]
        + costs["stamp_duty"]
        + costs["agent_fee"]
        + costs["legal_fee"]
        + costs["insurance_premium"]
        - costs["cash_rebate"]
    )
    return costs


def monthly_holding_costs(saleable_area, management_fee_per_ft, monthly_rent, rates_pct,
                          government_rent_pct, home_value, repair_pct):
    """Owner's monthly costs other than the mortgage, item by item, in HK$.

    Rates (差餉) and government rent (地租) are charged on the rateable value,
    which is about a year's rent for the flat.
    """
    rateable_value = monthly_rent * 12
    return {
        "management_fee": saleable_area * management_fee_per_ft,
        "rates": rateable_value * rates_pct / 100 / 12,
        "government_rent": rateable_value * government_rent_pct / 100 / 12,
        "repairs": home_value * repair_pct / 100 / 12,
    }


def home_equity(home_value, sell_cost_pct, mortgage_left):
    """What the owner would keep after selling and paying off the mortgage."""
    return home_value * (1 - sell_cost_pct / 100) - mortgage_left
