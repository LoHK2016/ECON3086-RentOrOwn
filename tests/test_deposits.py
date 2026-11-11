"""Tests for reading and ranking time deposit rates, using pages saved on 2026-11-12. No network calls.

Run with `uv run python tests/test_deposits.py` (or `pytest`).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from rentorbuy.calc.deposits import best_deposit, rank_deposits
from rentorbuy.scrapers.deposits import (
    parse_bochk,
    parse_elebank,
    parse_hsbc,
    parse_mox,
    parse_sc,
    rate_in,
    tenor_months,
)


def fixture(name):
    with open(os.path.join(HERE, "fixtures", name), encoding="utf-8") as file:
        return file.read()


def test_tenor_months():
    assert tenor_months("3 months") == 3
    assert tenor_months("12-month") == 12
    assert tenor_months("2 years") == 24
    assert tenor_months("1 week") is None


def test_rate_in():
    assert rate_in("2.395%") == 2.395
    assert rate_in(" 4% ") == 4.0
    assert rate_in("-") is None


def test_each_bank_page():
    # Read by eye from each saved page: the HKD rows only, not USD or RMB.
    assert parse_hsbc(fixture("hsbc_deposits.html")) == {3: 2.395, 6: 2.195}  # USD table is 3.300%
    assert parse_bochk(fixture("bochk_deposits.html")) == {3: 2.40, 6: 2.40}  # 12-month is "-"
    assert parse_sc(fixture("sc_deposits.html")) == {3: 2.40, 6: 2.40, 12: 3.10}
    assert parse_mox(fixture("mox_deposits.html")) == {3: 2.8, 6: 2.8, 9: 2.75, 12: 2.75, 24: 2.75}
    ele = parse_elebank(fixture("elebank_deposits.json"))
    assert ele[3] == 2.55 and ele[12] == 3.20 and ele[24] == 3.50


DEPOSITS = {
    "HSBC": {"rates": {"3": 2.395, "6": 2.195}, "url": "hsbc"},
    "Standard Chartered": {"rates": {"3": 2.40, "6": 2.40, "12": 3.10}, "url": "sc"},
    "eleBank": {"rates": {"3": 2.55, "6": 2.90, "12": 3.20}, "url": "ele"},
}


def test_best_deposit():
    assert best_deposit(DEPOSITS, "12") == ("eleBank", 3.20)
    assert best_deposit(DEPOSITS, "3") == ("eleBank", 2.55)
    assert best_deposit(DEPOSITS, "24") == (None, None)


def test_rank_deposits():
    ranking = rank_deposits(DEPOSITS, "6")
    assert [offer["bank"] for offer in ranking] == ["eleBank", "Standard Chartered", "HSBC"]
    assert [offer["bank"] for offer in rank_deposits(DEPOSITS, "12")] == ["eleBank", "Standard Chartered"]


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print("ok ", test.__name__)
    print(f"all {len(tests)} tests passed")
