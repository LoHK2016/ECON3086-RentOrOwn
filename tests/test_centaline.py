"""Tests for reading Centaline's listing pages, using Taikoo Shing's pages saved on
2026-11-12 (listing cards only). No network calls.

Run with `uv run python tests/test_centaline.py` (or `pytest`).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from rentorbuy.scrapers.centaline import median_or_none, parse_listings, per_ft_in


def page(kind):
    with open(os.path.join(HERE, "fixtures", f"centaline_{kind}.html"), encoding="utf-8") as file:
        return file.read()


def test_per_ft_in():
    assert per_ft_in("實用 實 702 呎 702呎 @ $21,082 /呎") == 21082
    assert per_ft_in("實用 實 715 呎 715呎 @ $48 /呎") == 48
    assert per_ft_in("實用 實 702 呎") is None


def test_sale_listings():
    prices = parse_listings(page("buy"), "太古城")
    assert len(prices) == 24
    # The first card on the page: 金殿台, 702 sq ft for $14.8M -> $21,082 per sq ft.
    assert prices[0] == 21082
    assert round(14_800_000 / 702) == 21083  # Centaline rounds down; close enough
    assert median_or_none(prices) == 18804


def test_rent_listings():
    rents = parse_listings(page("rent"), "太古城")
    assert len(rents) == 24
    # 海天花園, 715 sq ft for $35,000 a month -> $48.95, which Centaline shows as $48.
    assert rents[0] == 48
    assert median_or_none(rents) == 48.5


def test_other_estates_are_left_out():
    assert parse_listings(page("buy"), "康怡花園") == []


def test_too_few_listings_gives_no_median():
    assert median_or_none([100, 200, 300]) is None
    assert median_or_none([100, 200, 300, 400, 500]) == 300


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print("ok ", test.__name__)
    print(f"all {len(tests)} tests passed")
