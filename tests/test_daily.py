"""Tests for how the daily snapshot copes when a source fails. No network calls.

Run with `uv run python tests/test_daily.py`.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rentorbuy.scrapers.daily import (
    add_last_known_estates,
    default_investment_return,
    deposits_or_last_known,
    primes_or_last_known,
    use_centaline,
)  # needs requests and bs4: `uv run`

LAST = {"date": "2026-11-11", "estates": [{"id": "E1", "price_per_ft": 100}, {"id": "E2", "price_per_ft": 200}]}


def test_failed_estate_keeps_last_figures():
    # E1 scraped today at a new price; E2 failed, so it keeps yesterday's price and date.
    estates = add_last_known_estates([{"id": "E1", "price_per_ft": 110}], LAST, "2026-11-12")
    by_id = {e["id"]: e for e in estates}
    assert by_id["E1"] == {"id": "E1", "price_per_ft": 110, "scraped": "2026-11-12"}
    assert by_id["E2"] == {"id": "E2", "price_per_ft": 200, "scraped": "2026-11-11"}


def test_everything_failed():
    estates = add_last_known_estates([], LAST, "2026-11-12")
    assert [e["scraped"] for e in estates] == ["2026-11-11", "2026-11-11"]
    assert add_last_known_estates([], {}, "2026-11-12") == []


def test_centaline_fills_in_when_midland_fails():
    estates = add_last_known_estates([{"id": "E1", "name_zh": "甲", "price_per_ft": 110}],
                                     {"date": "2026-11-11", "estates": [
                                         {"id": "E2", "name_zh": "乙", "price_per_ft": 200, "rent_per_ft": 5},
                                         {"id": "E3", "name_zh": "丙", "price_per_ft": 300, "rent_per_ft": 6}]},
                                     "2026-11-12")
    figures = {
        "甲": {"price_per_ft": 999, "rent_per_ft": 9, "sale_listings": 24, "source": "c/甲"},
        "乙": {"price_per_ft": 210, "rent_per_ft": 5.5, "sale_listings": 24, "source": "c/乙"},
        "丙": {"price_per_ft": None, "rent_per_ft": 6.5, "sale_listings": 2, "source": "c/丙"},
    }
    by_id = {e["id"]: e for e in use_centaline(estates, figures, "2026-11-12")}
    assert by_id["E1"]["price_per_ft"] == 110  # Midland worked today: Centaline is not used
    assert by_id["E2"]["price_per_ft"] == 210 and by_id["E2"]["price_source"] == "centaline"
    assert by_id["E2"]["scraped"] == "2026-11-12"
    assert by_id["E3"]["price_per_ft"] == 300  # too few listings: keeps Midland's old figure
    assert by_id["E3"]["scraped"] == "2026-11-11"


def test_bank_primes():
    last = {"bank_primes": {"HSBC": {"prime": 5.25, "date": "2026-11-11"},
                            "BOCHK": {"prime": 5.25, "date": "2026-11-11"}}}
    # HSBC read today at 5.0; BOCHK failed, so it keeps yesterday's 5.25 and date.
    primes = primes_or_last_known({"HSBC": 5.0}, last, "2026-11-12")
    assert primes["HSBC"] == {"prime": 5.0, "date": "2026-11-12"}
    assert primes["BOCHK"] == {"prime": 5.25, "date": "2026-11-11"}


def test_deposits_and_default_return():
    last = {"deposits": {"Mox": {"rates": {"12": 2.75}, "url": "mox", "date": "2026-11-11"}}}
    today = {"eleBank": {"rates": {"3": 2.55, "12": 3.20}, "url": "ele"}}
    found = deposits_or_last_known(today, last, "2026-11-12")
    assert found["eleBank"]["date"] == "2026-11-12"
    assert found["Mox"]["date"] == "2026-11-11"  # not read today: kept, with its old date
    assert default_investment_return(found, {}) == {"value": 3.20, "bank": "eleBank", "months": "12", "provisional": False}
    # No bank offers 12 months: fall back to the hand-entered value.
    fallback = {"investment_return": {"value": 2.0, "provisional": True}}
    assert default_investment_return({}, fallback)["value"] == 2.0


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print("ok ", test.__name__)
    print(f"all {len(tests)} tests passed")
