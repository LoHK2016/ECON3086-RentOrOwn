"""Tests for the RVD 30-year market benchmark."""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rentorbuy.market_benchmarks import derive_benchmarks, mean_reverting_forecast, percentile


def test_percentile_is_interpolated():
    assert percentile([0, 10, 20], 0.50) == 10
    assert percentile([0, 10, 20, 30], 0.25) == 7.5


def test_benchmark_has_three_bands():
    price = []
    rent = []
    for year in range(1996, 2027):
        price.append((datetime(year, 1, 1), 100 * (1.05 ** (year - 1996))))
        rent.append((datetime(year, 1, 1), 100 * (1.03 ** (year - 1996))))
    result = derive_benchmarks(price, rent)
    assert result["price_growth"]["pessimistic"] == 5.0
    assert result["price_growth"]["neutral"] == 5.0
    assert result["price_growth"]["optimistic"] == 5.0
    assert result["rent_growth"]["neutral"] == 3.0


def test_mean_reverting_forecast_returns_point_and_intervals():
    values = []
    for year in range(1996, 2027):
        for month in (1, 7):
            age = (year - 1996) * 12 + month - 1
            values.append((datetime(year, month, 1), 100 * (1.002 ** age)))
    result = mean_reverting_forecast(values)
    assert result["horizon_years"] == 10
    assert "80%" in result["intervals_pct"]
    assert "95%" in result["intervals_pct"]
    assert isinstance(result["point_growth_pct"], (int, float))


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print("ok ", test.__name__)
    print(f"all {len(tests)} tests passed")
