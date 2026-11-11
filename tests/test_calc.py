"""Hand-checked tests for the calculator.

Run with `python tests/test_calc.py` (or `pytest`). Each expected number was
worked out by hand; the working is in the comment beside it.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rentorbuy.calc.stamp_duty import stamp_duty
from rentorbuy.calc.mortgage import (
    balance_after,
    effective_rate,
    insurance_premium,
    max_ltv,
    monthly_payment,
)
from rentorbuy.calc.buy_side import upfront_costs, home_equity
from rentorbuy.calc.comparison import compare, compare_scenarios


def close(a, b, tolerance=0.01):
    return abs(a - b) <= tolerance


def test_stamp_duty():
    assert stamp_duty(3_000_000) == 100
    assert stamp_duty(4_000_000) == 100
    assert stamp_duty(4_200_000) == 40_100  # 100 + 20% x 200,000
    assert stamp_duty(4_400_000) == 66_000  # 1.5% x 4.4M
    assert stamp_duty(5_000_000) == 112_500  # 2.25% x 5M
    assert stamp_duty(7_000_000) == 210_000  # 3% x 7M
    assert stamp_duty(9_500_000) == 320_000  # 270,000 + 10% x 500,000
    assert stamp_duty(15_000_000) == 562_500  # 3.75% x 15M
    assert stamp_duty(25_000_000) == 1_062_500  # 4.25% x 25M
    assert stamp_duty(200_000_000) == 13_000_000  # 6.5% x 200M
    # The marginal bands join the flat rates with no jump.
    assert abs(stamp_duty(4_323_780) - 0.015 * 4_323_780) < 1


def test_effective_rate():
    # H + 1.3% = 3.89%, capped at P - 1.75% = 3.25%: the cap wins.
    assert close(effective_rate(2.59452, 1.3, 5.0, 1.75), 3.25)
    # With HIBOR at 1%, H + 1.3% = 2.3% is below the cap.
    assert close(effective_rate(1.0, 1.3, 5.0, 1.75), 2.3)


def test_monthly_payment():
    assert close(monthly_payment(1_200_000, 0, 10), 10_000)  # no interest: 1.2M / 120
    assert close(monthly_payment(1_000_000, 6, 30), 5_995.51)  # textbook value


def test_balance_after():
    assert close(balance_after(1_000_000, 6, 30, 0), 1_000_000)
    assert balance_after(1_000_000, 6, 30, 360) == 0
    assert close(balance_after(1_200_000, 0, 10, 60), 600_000)  # half paid
    # Same answer as paying it off month by month.
    balance = 1_000_000
    payment = monthly_payment(1_000_000, 6, 30)
    for month in range(12):
        balance = balance * (1 + 0.06 / 12) - payment
    assert close(balance_after(1_000_000, 6, 30, 12), balance)


def test_max_ltv():
    assert max_ltv(6_000_000, True) == 0.90
    assert max_ltv(6_000_000, False) == 0.80
    assert close(max_ltv(10_500_000, True), 9 / 10.5)  # $9M loan cap
    assert max_ltv(13_000_000, True) == 0.80
    assert max_ltv(16_000_000, True) == 0.75  # $12M loan cap
    assert max_ltv(20_000_000, True) == 0.70


def test_insurance_premium():
    assert insurance_premium(3_500_000, 0.70) == 0
    assert insurance_premium(4_000_000, 0.80) == 56_000  # 1.4% x 4M


def test_upfront_costs():
    # 5M flat, 70% loan: loan 3.5M, down payment 1.5M, stamp duty 112,500,
    # agent 1% = 50,000, legal 10,000, no insurance. Total 1,672,500.
    costs = upfront_costs(5_000_000, 5_000_000, 0.70, 1.0, 10_000)
    assert costs["loan"] == 3_500_000
    assert costs["down_payment"] == 1_500_000
    assert costs["total_cash"] == 1_672_500
    # If the bank values it at 4.8M, it lends 70% of 4.8M = 3.36M.
    low = upfront_costs(5_000_000, 4_800_000, 0.70, 1.0, 10_000)
    assert low["loan"] == 3_360_000
    assert low["down_payment"] == 1_640_000


def test_home_equity():
    assert home_equity(5_000_000, 1.0, 3_000_000) == 1_950_000  # 4.95M - 3M


def no_frills(**changes):
    """A Comparison with every cost and growth set to zero, easy to check by hand."""
    inputs = {
        "price": 5_000_000,
        "saleable_area": 500,
        "monthly_rent": 15_000,
        "horizon_years": 2,
        "ltv": 0,  # cash purchase: no mortgage
        "mortgage_rate": 0,
        "price_growth": 0,
        "rent_growth": 0,
        "investment_return": 0,
        "management_fee_per_ft": 0,
        "rates_pct": 0,
        "repair_pct": 0,
        "sell_cost_pct": 0,
    }
    inputs.update(changes)
    return compare(inputs)


def test_compare_by_hand():
    # Day one the buyer pays 5M + 112,500 stamp duty + 50,000 agent + 10,000 legal
    # = 5,172,500. The renter invests the same 5,172,500.
    # Each month the owner pays nothing and the renter pays 15,000. Both sides
    # spend the same, so the owner invests the 15,000 the renter pays as rent.
    result = no_frills()
    assert result["upfront"]["total_cash"] == 5_172_500
    assert result["years"] == [0, 1, 2]
    assert close(result["buy_net_worth"][0], 5_000_000)
    assert close(result["rent_net_worth"][0], 5_172_500)
    assert close(result["buy_net_worth"][1], 5_180_000)  # 5M + 12 x 15,000
    assert close(result["rent_net_worth"][1], 5_172_500)  # nothing added, no return
    assert close(result["buy_net_worth"][2], 5_360_000)
    assert close(result["rent_net_worth"][2], 5_172_500)
    assert result["break_even_year"] == 1  # 5,180,000 > 5,172,500
    assert result["verdict"] == "buy"
    assert close(result["rental_yield"], 0.036)  # 180,000 / 5M


def test_compare_rent_wins_with_low_rent():
    # Rent of 1,000 a month saves only 12,000 a year, against 172,500 of buying costs:
    # buying needs about 14.4 years to catch up, so over 10 years renting wins.
    result = no_frills(monthly_rent=1_000, horizon_years=10)
    assert result["verdict"] == "rent"
    assert result["break_even_year"] is None
    result = no_frills(monthly_rent=1_000, horizon_years=15)
    assert result["break_even_year"] == 15


def test_compare_with_mortgage():
    # With a 70% loan at 0% over 10 years, the owner pays 3.5M / 120 = 29,166.67
    # a month. That is 14,166.67 more than rent, which the renter saves.
    result = no_frills(ltv=0.70, mortgage_years=10, mortgage_rate=0, horizon_years=1)
    assert close(result["monthly_payment"], 29_166.67)
    # Owner: 5M home - (3.5M - 12 x 29,166.67) left on the loan = 1,850,000.
    assert close(result["buy_net_worth"][1], 1_850_000)
    # Renter: 1,672,500 + 12 x 14,166.67 = 1,842,500.
    assert close(result["rent_net_worth"][1], 1_842_500)


def test_dsr_warning():
    result = no_frills(ltv=0.70, mortgage_years=10, mortgage_rate=0, monthly_income=50_000)
    assert close(result["debt_servicing_ratio"], 29_166.67 / 50_000)
    assert result["dsr_too_high"] is True
    assert no_frills()["debt_servicing_ratio"] is None


def test_scenarios_order():
    scenarios = {
        "pessimistic": {"price_growth": -2, "rent_growth": 0},
        "optimistic": {"price_growth": 5, "rent_growth": 3},
    }
    inputs = {"price": 6_000_000, "saleable_area": 450, "monthly_rent": 17_000, "mortgage_rate": 3.25}
    results = compare_scenarios(inputs, scenarios)
    assert results["optimistic"]["gap"] > results["pessimistic"]["gap"]


def test_inputs_from_estate_and_plan():
    # 450 sq ft at the Estate's 14,000/ft and 45/ft rent: price 6.3M, rent 20,250.
    # H-plan: min(2.6 + 1.3, 5 - 1.75) = 3.25%, plus a 1-point rise = 4.25%.
    result = compare({
        "saleable_area": 450, "price_per_ft": 14_000, "rent_per_ft": 45,
        "hibor": 2.6, "prime": 5.0, "rate_shift": 1.0,
    })
    used = result["inputs"]
    assert used["price"] == 6_300_000
    assert used["monthly_rent"] == 20_250
    assert close(used["mortgage_rate"], 4.25)
    assert used["ltv"] == 0.90  # first-time buyer, under $10M
    # Asking for more than allowed gives the most allowed: 80% if not a first-time buyer.
    again = compare({"saleable_area": 450, "price_per_ft": 14_000, "rent_per_ft": 45,
                     "mortgage_rate": 3, "first_time": False, "ltv": 0.9})
    assert again["inputs"]["ltv"] == 0.80
    # The user's own price wins over the Estate's typical price.
    assert compare({"saleable_area": 450, "price_per_ft": 14_000, "price": 6_000_000,
                    "monthly_rent": 20_000, "mortgage_rate": 3})["inputs"]["price"] == 6_000_000


def test_price_defaults_to_valuation():
    # A specific Flat valued by the bank at 18.93M: that is the price unless the user types one.
    result = compare({"saleable_area": 1146, "price_per_ft": 16_000, "rent_per_ft": 46,
                      "valuation": 18_930_000, "mortgage_rate": 3})
    assert result["inputs"]["price"] == 18_930_000
    assert result["inputs"]["monthly_rent"] == 52_716  # 46 x 1,146


def test_missing_input():
    try:
        compare({"price": 5_000_000})
        assert False, "should have raised"
    except ValueError:
        pass


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print("ok ", test.__name__)
    print(f"all {len(tests)} tests passed")
