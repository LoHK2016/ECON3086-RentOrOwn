"""Compare buying with renting, month by month, over the Horizon.

Both sides start with the same cash: what the buyer pays on day one. Each
month, whichever side spends less invests the difference, so both sides
always spend the same amount. At the end of each year we record each side's
Net Worth Outcome. The words used here are defined in CONTEXT.md.
"""

from rentorbuy.calc.mortgage import (
    DSR_LIMIT,
    balance_after,
    debt_servicing_ratio,
    effective_rate,
    max_ltv,
    monthly_payment,
)
from rentorbuy.calc.buy_side import upfront_costs, monthly_holding_cost, home_equity
from rentorbuy.calc.rent_side import rent_for_year, grow_one_month

DEFAULTS = {
    "saleable_area": None,  # square feet (required)
    "price": None,  # Purchase Price, HK$; None means the valuation, else price_per_ft x saleable_area
    "monthly_rent": None,  # HK$ for the same flat; None means rent_per_ft x saleable_area
    "price_per_ft": None,  # the Estate's typical price per sq ft
    "rent_per_ft": None,  # the Estate's typical monthly rent per sq ft
    "valuation": None,  # Bank Valuation, HK$; None means same as the price
    "horizon_years": 10,
    "first_time": True,  # owns no other HK home and is salaried
    "ltv": None,  # loan-to-value, e.g. 0.8; None (or too high) means the highest allowed
    "mortgage_years": 30,
    "mortgage_rate": None,  # % a year; None means work it out from the H-plan below
    "hibor": None,  # one-month HIBOR, % a year
    "prime": None,  # the bank's prime rate, % a year
    "hibor_spread": 1.3,  # H-plan: HIBOR + this
    "prime_discount": 1.75,  # H-plan cap: prime - this
    "rate_shift": 0.0,  # what if rates rise (+) or fall (-), in % points
    "price_growth": 2.0,  # % a year
    "rent_growth": 2.0,  # % a year
    "investment_return": 2.0,  # % a year
    "monthly_income": None,  # HK$, only used for the debt servicing ratio
    "management_fee_per_ft": 3.0,  # HK$ per sq ft per month
    "rates_pct": 8.0,  # rates (5%) + government rent (3%) of a year's rent
    "repair_pct": 0.2,  # % of the home's value a year
    "agent_fee_pct": 1.0,  # paid when buying
    "legal_fee": 10_000,
    "sell_cost_pct": 1.0,  # agent fee when selling at the end
}

REQUIRED = ["saleable_area", "price", "monthly_rent", "mortgage_rate"]


def fill_defaults(inputs):
    """Return a copy of `inputs` with every missing value taken from DEFAULTS."""
    filled = dict(DEFAULTS)
    for key, value in inputs.items():
        if value is not None:
            filled[key] = value
    area = filled["saleable_area"]
    if filled["price"] is None and filled["valuation"]:
        filled["price"] = filled["valuation"]  # a specific Flat: expect to pay what the bank says
    if filled["price"] is None and filled["price_per_ft"] and area:
        filled["price"] = round(filled["price_per_ft"] * area)
    if filled["monthly_rent"] is None and filled["rent_per_ft"] and area:
        filled["monthly_rent"] = round(filled["rent_per_ft"] * area)
    if filled["mortgage_rate"] is None and filled["hibor"] is not None and filled["prime"] is not None:
        filled["mortgage_rate"] = effective_rate(
            filled["hibor"], filled["hibor_spread"], filled["prime"], filled["prime_discount"]
        )
    for key in REQUIRED:
        if filled[key] is None:
            raise ValueError(f"missing input: {key}")
    if filled["valuation"] is None:
        filled["valuation"] = filled["price"]
    filled["mortgage_rate"] = filled["mortgage_rate"] + filled["rate_shift"]
    filled["max_ltv"] = max_ltv(filled["price"], filled["first_time"])
    if filled["ltv"] is None or filled["ltv"] > filled["max_ltv"]:
        filled["ltv"] = filled["max_ltv"]
    return filled


def first_year_buying_wins(years, buy, rent):
    """First year in which buying is ahead of renting, or None if it never is."""
    for i in range(len(years)):
        if buy[i] > rent[i]:
            return years[i]
    return None


def compare(inputs):
    """Run one Comparison. Takes a dict of inputs and returns a dict of results."""
    x = fill_defaults(inputs)
    price = x["price"]
    rate = x["mortgage_rate"]

    upfront = upfront_costs(price, x["valuation"], x["ltv"], x["agent_fee_pct"], x["legal_fee"])
    loan = upfront["loan"]
    payment = monthly_payment(loan, rate, x["mortgage_years"])

    # Both sides start with the buyer's day-one cash. The buyer turns it into a home;
    # the renter invests it. The buyer's own investments start at zero.
    renter_savings = upfront["total_cash"]
    owner_savings = 0.0

    years = [0]
    buy_worth = [home_equity(price, x["sell_cost_pct"], loan)]
    rent_worth = [renter_savings]
    yearly_costs = []

    for month in range(1, x["horizon_years"] * 12 + 1):
        year_index = (month - 1) // 12
        home_value = price * (1 + x["price_growth"] / 100) ** (month / 12)
        rent = rent_for_year(x["monthly_rent"], x["rent_growth"], year_index)

        mortgage = payment if month <= x["mortgage_years"] * 12 else 0
        holding = monthly_holding_cost(
            x["saleable_area"], x["management_fee_per_ft"], rent, x["rates_pct"], home_value, x["repair_pct"]
        )
        owner_cost = mortgage + holding

        # Last month's savings earn a return, then whoever spent less saves the difference.
        renter_savings = grow_one_month(renter_savings, x["investment_return"])
        owner_savings = grow_one_month(owner_savings, x["investment_return"])
        if owner_cost > rent:
            renter_savings += owner_cost - rent
        else:
            owner_savings += rent - owner_cost

        if month % 12 == 1:
            yearly_costs.append({"year": year_index + 1, "owner_monthly": owner_cost, "rent_monthly": rent})

        if month % 12 == 0:
            mortgage_left = balance_after(loan, rate, x["mortgage_years"], month)
            years.append(month // 12)
            buy_worth.append(home_equity(home_value, x["sell_cost_pct"], mortgage_left) + owner_savings)
            rent_worth.append(renter_savings)

    dsr = debt_servicing_ratio(payment, x["monthly_income"])
    gap = buy_worth[-1] - rent_worth[-1]
    return {
        "inputs": x,
        "verdict": "buy" if gap > 0 else "rent",
        "gap": gap,
        "break_even_year": first_year_buying_wins(years, buy_worth, rent_worth),
        "years": years,
        "buy_net_worth": buy_worth,
        "rent_net_worth": rent_worth,
        "upfront": upfront,
        "monthly_payment": payment,
        "yearly_costs": yearly_costs,
        "rental_yield": x["monthly_rent"] * 12 / price,
        "debt_servicing_ratio": dsr,
        "dsr_too_high": dsr is not None and dsr > DSR_LIMIT,
    }


def compare_scenarios(inputs, scenarios):
    """Run the Comparison once per Market Scenario.

    `scenarios` maps a name to {"price_growth": ..., "rent_growth": ...}.
    """
    results = {}
    for name, growth in scenarios.items():
        one = dict(inputs)
        one["price_growth"] = growth["price_growth"]
        one["rent_growth"] = growth["rent_growth"]
        results[name] = compare(one)
    return results
