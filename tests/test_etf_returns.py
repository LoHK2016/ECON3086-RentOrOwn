"""Checks for the ETF return calculations: made-up prices we can work out by hand,
then the real prices saved in data/etf/. No network calls.

Run with `uv run python tests/test_etf_returns.py` (or `pytest`).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import pandas as pd

from rentorbuy.etf_returns import (after_tax_growth, annual_return, load_prices,
                                   rolling_annual_returns)


def monthly(values):
    return pd.Series(values, index=pd.date_range("2000-01-31", periods=len(values), freq="ME"))


def test_doubling_in_ten_years_is_about_7_2_percent_a_year():
    # 2 ** (1/10) = 1.0718
    growth = monthly([1.0] * 120 + [2.0])
    assert round(annual_return(growth, 10), 2) == 7.18


def test_annual_return_needs_enough_months():
    try:
        annual_return(monthly([1.0] * 120), 10)
        assert False, "should refuse 120 months for a 10-year return"
    except ValueError:
        pass


def test_only_the_dividend_is_taxed():
    # The price stays at 100; a 2% dividend lifts the reinvested value to 102.
    # 30% withholding leaves 1.4% of the 2%.
    prices = pd.DataFrame({"Close": [100.0, 100.0], "Adj Close": [100.0, 102.0]},
                          index=monthly([0, 0]).index)
    growth = after_tax_growth(prices, 0.30)
    assert round(growth.iloc[-1], 4) == 1.014
    # Untaxed, the whole 2% counts.
    assert round(after_tax_growth(prices, 0).iloc[-1], 4) == 1.02


def test_price_rise_is_not_taxed():
    prices = pd.DataFrame({"Close": [100.0, 110.0], "Adj Close": [100.0, 110.0]},
                          index=monthly([0, 0]).index)
    assert round(after_tax_growth(prices, 0.30).iloc[-1], 4) == 1.1


def test_rolling_returns_find_the_worst_stretch():
    # 1 year of flat prices, then a fall by half, then flat: every 1-year
    # stretch that includes the fall loses 50%.
    growth = monthly([1.0] * 12 + [0.5] * 13)
    windows = rolling_annual_returns(growth, 1)
    assert round(windows.min(), 2) == -50
    assert round(windows.max(), 2) == 0
    assert len(windows) == 25 - 12


def test_spy_after_tax_is_between_price_only_and_all_dividends():
    # Real prices saved from Yahoo Finance. Taxing 30% of the dividend must give
    # a return between the price alone and the price with every dividend kept.
    prices = load_prices("SPY")
    price_only = annual_return(prices["Close"], 20)
    all_dividends = annual_return(prices["Adj Close"], 20)
    after_tax = annual_return(after_tax_growth(prices, 0.30), 20)
    assert price_only < after_tax < all_dividends
    # 30% of the dividend part is lost (roughly; returns compound).
    expected = all_dividends - 0.30 * (all_dividends - price_only)
    assert abs(after_tax - expected) < 0.1


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print("ok ", test.__name__)
    print(f"all {len(tests)} tests passed")
