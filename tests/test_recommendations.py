"""Hand-checked Estate recommendation calculations."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rentorbuy.calc.recommendations import recommend_estates


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
        "monthly_debt": 2_000,
        "down_payment": 250_000,
        "savings": 50_000,
        "saleable_area": 500,
        "mortgage_rate": 0,
        "mortgage_years": 10,
        "comfortable_pct": 30,
    })
    rent = next(item for item in results if item["mode"] == "rent")
    buy = next(item for item in results if item["mode"] == "buy")

    assert buy["price"] == 5_000_000  # 500 sq ft x $10,000 purchase average per sq ft
    assert rent["monthly_costs"]["total"] == 15_000  # 500 sq ft x $30 rent per sq ft
    assert rent["housing_pct"] == 30
    assert rent["comfortable_budget"] == 15_000
    assert rent["label"] == "comfortable"

    assert buy["upfront"]["loan"] == 4_500_000  # first-time buyer: 90% of $5M
    assert close(buy["monthly_costs"]["mortgage"], 37_500)  # $4.5M / 120 at 0% over 10 years
    assert close(buy["monthly_costs"]["total"], 41_033.33)  # mortgage + 1,500 + 750 + 450 + 833.33
    assert buy["upfront"]["total_cash"] == 812_000  # 500K + 112.5K + 50K + 10K + 139.5K
    assert buy["cash_available"] == 300_000
    assert buy["cash_shortfall"] == 512_000
    assert buy["label"] == "risky"
    assert buy["stress"]["monthly_cost"] > buy["monthly_costs"]["total"]
    assert buy["stress"]["monthly_income"] == 40_000  # take-home pay reduced by 20%
    assert buy["stress"]["label"] == "risky"


def test_comfort_stretch_and_preferred_payment_boundaries():
    estate = sample_estates()

    stretch = recommend_estates(estate, {
        "monthly_income": 50_000,
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
        "saleable_area": 500,
        "mortgage_rate": 3,
        "bedrooms": "3",
    })
    assert no_three_bedroom_data == []


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print("ok ", test.__name__)
    print(f"all {len(tests)} tests passed")
