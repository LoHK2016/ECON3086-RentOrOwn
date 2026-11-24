"""Tests for the RVD price and rent forecast (rentorbuy/market_benchmarks.py).

Run with `python tests/test_market_benchmarks.py` (or `pytest`). The RVD files
in tests/fixtures/ were downloaded once on 2026-11-25, so no test touches RVD.
"""

import os
import random
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rentorbuy.market_benchmarks import (
    annual_growth,
    forecast_benchmarks,
    last_years,
    mean_reverting_forecast,
    parse_monthly_index,
    past_ten_year_growth,
    percentile,
)

FIXTURES = Path(__file__).parent / "fixtures"


def close(a, b, tolerance=0.01):
    return abs(a - b) <= tolerance


def monthly(start_year, months, monthly_growth, noise=0.0):
    """A made-up monthly index starting at 100 in January of `start_year`.

    `noise` adds a repeatable random wobble (in log terms) so a model can be fitted.
    """
    wobble = random.Random(1)
    values = []
    for n in range(months):
        month = datetime(start_year + n // 12, n % 12 + 1, 1)
        index = 100 * (1 + monthly_growth) ** n * (1 + wobble.gauss(0, noise))
        values.append((month, index))
    return values


def read_fixture(name):
    return parse_monthly_index((FIXTURES / name).read_text(encoding="utf-8-sig"))


def test_parse_rvd_file():
    # The file's first data row is "01-1993,...,84.4," and its last "09-2026,...,320.8,P":
    # 1993-01 to 2026-09 is 33 years and 9 months = 405 months.
    price = read_fixture("rvd_1.4M.csv")
    assert len(price) == 405
    assert price[0] == (datetime(1993, 1, 1), 84.4)
    assert price[-1] == (datetime(2026, 9, 1), 320.8)
    rent = read_fixture("rvd_1.3M.csv")
    assert rent[-1] == (datetime(2026, 9, 1), 212.2)


def test_parse_rejects_other_files():
    try:
        parse_monthly_index("Year,Index\n2026,100\n")
        assert False, "a file with no Month / All Classes header should be refused"
    except ValueError:
        pass


def test_annual_growth():
    # 100 -> 121 over 24 months: 1.21 ** (1/2) = 1.10, so 10% a year.
    assert close(annual_growth(100, 121, 24), 10.0)
    # 100 -> 90 over 12 months: -10% a year.
    assert close(annual_growth(100, 90, 12), -10.0)


def test_percentile_is_interpolated():
    assert percentile([0, 10, 20], 0.50) == 10  # the middle value
    # Position (4 - 1) x 0.25 = 0.75, so 0 + 0.75 x (10 - 0) = 7.5.
    assert percentile([0, 10, 20, 30], 0.25) == 7.5


def test_last_years():
    # 1990-01 to 2026-09 is 441 months. 30 years back from 2026-09 is 1996-09,
    # and 1996-09 to 2026-09 inclusive is 30 x 12 + 1 = 361 months.
    values = monthly(1990, 441, 0.0)
    assert values[-1][0] == datetime(2026, 9, 1)
    kept = last_years(values)
    assert kept[0][0] == datetime(1996, 9, 1)
    assert len(kept) == 361


def test_past_ten_year_growth():
    # An index growing 5% every year grows 5% a year over any 10-year stretch.
    yearly = (1.05) ** (1 / 12) - 1
    result = past_ten_year_growth(monthly(1996, 361, yearly))
    assert close(result["low"], 5.0)
    assert close(result["median"], 5.0)
    assert close(result["high"], 5.0)


def test_forecast_follows_the_trend():
    # An index growing 0.4% a month, with a small wobble, for 30 years.
    # The trend is 1.004 ** 12 - 1 = 4.907% a year, so the 10-year point
    # forecast should come back near 4.91%.
    values = monthly(1996, 361, 0.004, noise=0.01)
    result = mean_reverting_forecast(values)
    ten = result["growth_pct"]["10"]
    assert abs(ten["point"] - 4.91) < 0.3
    assert ten["low"] < ten["point"] < ten["high"]
    assert set(result["growth_pct"]) == {str(year) for year in range(1, 31)}
    assert result["history_from"] == "1996-01"
    assert result["history_to"] == "2026-01"  # month 361 is January, 30 years on


def test_band_narrows_with_horizon():
    # A trend model expects prices to return to the trend line, so a 1-year
    # wobble averages out over 30 years and the band in % a year narrows.
    # This is the limit the site states: the long-run band never allows a
    # long fall away from the trend.
    result = mean_reverting_forecast(monthly(1996, 361, 0.004, noise=0.01))
    one = result["growth_pct"]["1"]
    thirty = result["growth_pct"]["30"]
    assert thirty["high"] - thirty["low"] < one["high"] - one["low"]


def test_forecast_on_saved_rvd_files():
    # Real data, so no exact numbers: check the shape and that it is sensible.
    result = forecast_benchmarks(read_fixture("rvd_1.4M.csv"), read_fixture("rvd_1.3M.csv"))
    for series in ("price", "rent"):
        forecast = result[series]
        assert forecast["history_from"] == "1996-09"  # 30 years before 2026-09
        assert forecast["history_to"] == "2026-09"
        for year in ("1", "10", "30"):
            band = forecast["growth_pct"][year]
            assert band["low"] < band["point"] < band["high"]


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print("ok ", test.__name__)
    print(f"all {len(tests)} tests passed")
