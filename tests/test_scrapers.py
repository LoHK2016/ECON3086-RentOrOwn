"""Tests for the scrapers' parsing, using small saved pieces of Midland's data. No network calls.

Run with `uv run python tests/test_scrapers.py` (or `pytest`).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rentorbuy.scrapers.midland import district_of, first_number, summarise


def test_district_of():
    assert district_of("東區")["region_zh"] == "香港島"
    # Midland's 將軍澳 is not one of the 18 districts: it is in Sai Kung, New Territories.
    assert district_of("將軍澳") == {
        "region_zh": "新界", "region_en": "New Territories", "district_zh": "西貢", "district_en": "Sai Kung",
    }
    try:
        district_of("火星")
        assert False, "should have raised"
    except ValueError:
        pass


def test_first_number():
    assert first_number(None, 0, 14192) == 14192
    assert first_number(None, "n/a") is None


def test_summarise_prefers_transactions():
    # Cut down from Midland's 沙田第一城 page on 2026-11-11.
    data = {
        "id": "E00012",
        "name": {"chi": "沙田第一城", "en": "City One Shatin"},
        "subregion": {"name": "沙田"},
        "avg_net_ft_price": 15261,
        "market_stat": {"net_ft_price": 14192, "net_ft_rent": 48.47, "tx_count": 19},
        "property_stat": {"avg_net_ft_rent": 48},
        "market_stat_by_room": {"2": {"avg_net_ft_price": 14869.0476, "avg_net_ft_rent": 48.3906}},
    }
    estate = summarise("新界-第一城-石門-沙田第一城-E00012", data)
    assert estate["price_per_ft"] == 14192  # transactions, not the 15,261 asking price
    assert estate["rent_per_ft"] == 48.47
    assert estate["region_zh"] == "新界" and estate["district_en"] == "Sha Tin"
    assert estate["by_room"]["2"]["rent_per_ft"] == 48.3906


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print("ok ", test.__name__)
    print(f"all {len(tests)} tests passed")
