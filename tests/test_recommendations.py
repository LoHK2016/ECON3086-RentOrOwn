"""Hand-checked Estate recommendation calculations."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rentorbuy.calc.recommendations import loan_to_value_for, recommend_estates
from rentorbuy.calc.affordability import MAX_MORTGAGE_YEARS


def close(a, b, tolerance=0.01):
    return abs(a - b) <= tolerance


def sample_estates():
    return [{
        "id": "E1",
        "name_en": "Harbour Estate",
        "name_zh": "海港屋苑",
        "region_en": "Hong Kong Island",
        "region_zh": "香港島",
        "district_en": "Eastern",
        "district_zh": "東區",
        "price_per_ft": 10_000,
        "rent_per_ft": 30,
        "by_room": {"2": {"price_per_ft": 9_000, "rent_per_ft": 28}},
        "source": "https://example.test/estate",
        "scraped": "2026-11-20",
        "price_source": "midland",
    }]


def test_recommendations_use_snapshot_averages_and_hand_checked_costs():
    results = recommend_estates(sample_estates(), {
        "monthly_income": 50_000,
        "gross_monthly_income": 60_000,
        "monthly_debt": 2_000,
        "down_payment": 250_000,
        "savings": 50_000,
        "saleable_area": 500,
        "mortgage_rate": 0,
        "mortgage_years": 10,
        "comfortable_pct": 30,
        "first_time": True,
    })
    rent = next(item for item in results if item["mode"] == "rent")
    buy = next(item for item in results if item["mode"] == "buy")

    assert buy["price"] == 5_000_000  # 500 sq ft x $10,000 purchase average per sq ft
    assert rent["monthly_costs"]["total"] == 15_000  # 500 sq ft x $30 rent per sq ft
    assert rent["housing_pct"] == 30
    assert rent["comfortable_budget"] == 15_000
    assert rent["label"] == "comfortable"
    assert rent["upfront"]["security_deposit"] == 30_000  # 2 months x $15K monthly rent
    assert rent["upfront"]["agent_fee"] == 7_500  # 50% x one month's rent
    assert rent["upfront"]["total_cash"] == 37_500

    assert buy["upfront"]["loan"] == 4_500_000  # first-time buyer: 90% of $5M
    assert close(buy["monthly_costs"]["mortgage"], 37_500)  # $4.5M / 120 at 0% over 10 years
    assert close(buy["monthly_costs"]["total"], 41_033.33)  # mortgage + 1,500 + 750 + 450 + 833.33
    # The $250K down payment is below the 10% first-time minimum, so the buyer must put in $500K.
    assert buy["upfront"]["insurance_premium"] == 139_500  # 3.1% x $4.5M loan at 90% LTV
    # 500,000 down + 112,500 stamp duty + 50,000 agent + 10,000 legal + 139,500 insurance
    assert buy["upfront"]["total_cash"] == 812_000
    assert buy["cash_available"] == 300_000  # 250,000 down payment + 50,000 savings
    assert buy["cash_shortfall"] == 512_000  # 812,000 - 300,000
    assert buy["label"] == "risky"
    assert buy["stress"]["monthly_cost"] > buy["monthly_costs"]["total"]
    assert buy["stress"]["monthly_income"] == 40_000  # take-home pay reduced by 20%
    assert buy["stress"]["label"] == "risky"


def test_comfort_stretch_and_preferred_payment_boundaries():
    estate = sample_estates()

    stretch = recommend_estates(estate, {
        "monthly_income": 50_000,
        "gross_monthly_income": 60_000,
        "saleable_area": 500,
        "mortgage_rate": 3,
        "comfortable_pct": 25,
    })
    rent = next(item for item in stretch if item["mode"] == "rent")
    assert rent["comfortable_budget"] == 12_500
    assert rent["stretch_budget"] == 15_625
    assert rent["label"] == "stretch"

    preferred = recommend_estates(estate, {
        "monthly_income": 50_000,
        "gross_monthly_income": 60_000,
        "saleable_area": 500,
        "mortgage_rate": 3,
        "preferred_payment": 10_000,
    })
    rent = next(item for item in preferred if item["mode"] == "rent")
    assert rent["comfortable_budget"] == 10_000
    assert rent["stretch_budget"] == 12_500
    assert rent["label"] == "risky"


def test_existing_debt_caps_both_budget_boundaries():
    results = recommend_estates(sample_estates(), {
        "monthly_income": 50_000,
        "gross_monthly_income": 60_000,
        "monthly_debt": 40_000,
        "saleable_area": 500,
        "mortgage_rate": 3,
    })
    rent = next(item for item in results if item["mode"] == "rent")
    assert rent["comfortable_budget"] == 10_000  # income left after $40K debt
    assert rent["stretch_budget"] == 10_000  # Stretch cannot exceed money left after debt
    assert rent["label"] == "risky"


def test_location_and_bedroom_filters_use_only_snapshot_data():
    results = recommend_estates(sample_estates(), {
        "monthly_income": 50_000,
        "gross_monthly_income": 60_000,
        "saleable_area": 500,
        "mortgage_rate": 3,
        "region": "Hong Kong Island",
        "district": "Eastern",
        "bedrooms": "2",
    })
    rent = next(item for item in results if item["mode"] == "rent")
    assert rent["price"] == 4_500_000  # 2-bedroom per-square-foot average x area
    assert rent["monthly_rent"] == 14_000
    assert rent["source_date"] == "2026-11-20"

    no_three_bedroom_data = recommend_estates(sample_estates(), {
        "monthly_income": 50_000,
        "gross_monthly_income": 60_000,
        "saleable_area": 500,
        "mortgage_rate": 3,
        "bedrooms": "3",
    })
    assert no_three_bedroom_data == []


def test_loan_to_value_for_down_payment():
    # $5M flat, first-time buyer: the bank lends up to 90%, so at least $500K down.
    assert close(loan_to_value_for(5_000_000, 0, True), 0.90)  # too little cash: the cap
    assert close(loan_to_value_for(5_000_000, 2_000_000, True), 0.60)  # 1 - 2M / 5M
    assert loan_to_value_for(5_000_000, 6_000_000, True) == 0  # cash buyer: no loan
    # Not first-time: at most 80%, so $500K down still means a 1M down payment.
    assert close(loan_to_value_for(5_000_000, 500_000, False), 0.80)


def six_million_flat(down_payment, savings):
    """A $6M purchase (500 sq ft at $12,000), 3.25% over 30 years, not first-time."""
    estate = sample_estates()
    estate[0]["price_per_ft"] = 12_000
    results = recommend_estates(estate, {
        "monthly_income": 30_000,
        "gross_monthly_income": 40_000,
        "down_payment": down_payment,
        "savings": savings,
        "saleable_area": 500,
        "mortgage_rate": 3.25,
        "first_time": False,
        "comfortable_pct": 90,
    })
    return next(item for item in results if item["mode"] == "buy")


# At 3.25% over 30 years, r = 0.0325 / 12 and each $1 of monthly payment repays
# (1 - (1 + r) ** -360) / r = 229.776 of loan.


def test_purchase_borrows_only_what_the_down_payment_does_not_cover():
    # $3M down on a $6M flat: a $3M loan (50% LTV), not the 80% cap's $4.8M.
    buy = six_million_flat(down_payment=3_000_000, savings=300_000)
    assert buy["upfront"]["loan"] == 3_000_000
    assert close(buy["upfront"]["loan_to_value"], 0.50)
    assert close(buy["monthly_costs"]["mortgage"], 13_056.19)  # 3,000,000 / 229.776
    # Cash: 3,000,000 down + 135,000 stamp duty (2.25% of 6M) + 60,000 agent + 10,000 legal,
    # no insurance at 50% = 3,205,000, within 3,000,000 + 300,000 savings.
    assert buy["upfront"]["total_cash"] == 3_205_000
    assert buy["cash_shortfall"] == 0
    assert close(buy["debt_servicing_ratio"], 0.3264, 0.0001)  # 13,056.19 / 40,000
    # Monthly: 13,056.19 + 1,500 management + 750 rates + 450 government rent + 1,000 repairs
    # = 16,756.19, under the comfort limit of 90% x 30,000 = 27,000.
    assert close(buy["monthly_costs"]["total"], 16_756.19)
    assert buy["label"] == "comfortable"
    # Stress: 4.25% gives 3,000,000 / 203.28 = 14,758.20 a month; DSR on 80% of
    # gross income = 14,758.20 / 32,000 = 46.1%, still under 50%.
    assert close(buy["stress"]["debt_servicing_ratio"], 0.4612, 0.0001)


def test_purchase_is_risky_when_gross_income_dsr_exceeds_fifty_percent():
    # Only the minimum 20% down ($1.2M): the loan is $4.8M, 4,800,000 / 229.776 =
    # 20,889.90 a month, and DSR = 20,889.90 / 40,000 = 52.2%, over the 50% limit.
    # Take-home comfort alone would pass (20,889.90 + 3,700 = 24,589.90 < 27,000).
    buy = six_million_flat(down_payment=1_200_000, savings=2_000_000)
    assert buy["upfront"]["loan"] == 4_800_000
    assert close(buy["debt_servicing_ratio"], 0.5222, 0.0001)
    assert buy["monthly_costs"]["total"] < buy["comfortable_budget"]
    assert buy["label"] == "risky"  # the bank DSR overrides the take-home comfort label


def test_rate_shift_applies_to_a_directly_supplied_mortgage_rate():
    result = recommend_estates(sample_estates(), {
        "monthly_income": 50_000,
        "gross_monthly_income": 60_000,
        "saleable_area": 500,
        "mortgage_rate": 3,
        "rate_shift": 1,
    })
    assert all(item["mortgage_rate"] == 4 for item in result)


def test_rate_shift_applies_after_deriving_the_hibor_rate():
    result = recommend_estates(sample_estates(), {
        "monthly_income": 50_000,
        "gross_monthly_income": 60_000,
        "saleable_area": 500,
        "hibor": 2.6,
        "prime": 5,
        "hibor_spread": 1.3,
        "prime_discount": 1.75,
        "rate_shift": 0.5,
    })
    assert all(item["mortgage_rate"] == 3.75 for item in result)


def test_estates_missing_required_snapshot_fields_are_skipped():
    incomplete = sample_estates()[0]
    del incomplete["rent_per_ft"]
    results = recommend_estates([incomplete, *sample_estates()], {
        "monthly_income": 50_000,
        "gross_monthly_income": 60_000,
        "saleable_area": 500,
        "mortgage_rate": 3,
    })
    assert len(results) == 2  # only the complete Estate contributes rent and buy options


def test_mortgage_term_cannot_exceed_shared_limit():
    try:
        recommend_estates(sample_estates(), {
            "monthly_income": 50_000,
            "gross_monthly_income": 60_000,
            "saleable_area": 500,
            "mortgage_rate": 3,
            "mortgage_years": MAX_MORTGAGE_YEARS + 1,
        })
        assert False, "should have rejected a term above MAX_MORTGAGE_YEARS"
    except ValueError:
        pass


def test_first_time_buyer_default_matches_affordability_calculator():
    # $500K is 10% of $5M: enough for a first-time buyer, but the default (not
    # first-time) caps the loan at 80%, so the buyer must put in 20%.
    result = recommend_estates(sample_estates(), {
        "monthly_income": 50_000,
        "gross_monthly_income": 60_000,
        "down_payment": 500_000,
        "saleable_area": 500,
        "mortgage_rate": 3,
    })
    buy = next(item for item in result if item["mode"] == "buy")
    assert buy["upfront"]["loan_to_value"] == 0.80


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print("ok ", test.__name__)
    print(f"all {len(tests)} tests passed")
