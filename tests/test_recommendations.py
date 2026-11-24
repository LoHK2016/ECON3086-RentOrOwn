"""Hand-checked Estate recommendation calculations."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rentorbuy.calc.recommendations import recommend_estates
from rentorbuy.calc.affordability import MAX_MORTGAGE_YEARS
from rentorbuy.calc.mortgage import DSR_LIMIT, insurance_premium


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
    expected_insurance = insurance_premium(buy["upfront"]["loan"], buy["upfront"]["loan_to_value"])
    expected_upfront = 500_000 + 112_500 + 50_000 + 10_000 + expected_insurance
    assert buy["upfront"]["insurance_premium"] == expected_insurance
    assert buy["upfront"]["total_cash"] == expected_upfront
    assert buy["cash_available"] == 300_000
    assert buy["cash_shortfall"] == expected_upfront - 300_000
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


def test_purchase_is_risky_when_gross_income_dsr_exceeds_fifty_percent():
    estate = sample_estates()
    estate[0]["price_per_ft"] = 12_000  # $6M Purchase Price at 500 sq ft
    result = recommend_estates(estate, {
        "monthly_income": 30_000,
        "gross_monthly_income": 40_000,
        "down_payment": 3_000_000,
        "saleable_area": 500,
        "mortgage_rate": 3.25,
        "first_time": False,
        "comfortable_pct": 90,
    })
    buy = next(item for item in result if item["mode"] == "buy")
    assert buy["monthly_costs"]["total"] < buy["comfortable_budget"]
    assert close(
        buy["debt_servicing_ratio"],
        (buy["monthly_costs"]["mortgage"] + buy["monthly_debt"]) / 40_000,
    )
    assert buy["debt_servicing_ratio"] > DSR_LIMIT
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
    result = recommend_estates(sample_estates(), {
        "monthly_income": 50_000,
        "gross_monthly_income": 60_000,
        "down_payment": 2_000_000,
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
