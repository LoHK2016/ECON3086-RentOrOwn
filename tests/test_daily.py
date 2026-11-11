"""Tests for how the daily snapshot copes when a source fails. No network calls.

Run with `uv run python tests/test_daily.py`.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rentorbuy.scrapers.daily import add_last_known_estates  # needs requests and bs4: `uv run`

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


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print("ok ", test.__name__)
    print(f"all {len(tests)} tests passed")
