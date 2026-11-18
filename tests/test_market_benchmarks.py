"""Tests for the RVD 30-year market benchmark."""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rentorbuy.market_benchmarks import derive_benchmarks, percentile


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
    assert result["scenarios"]["pessimistic"]["price_growth"] == 5.0
    assert result["scenarios"]["neutral"]["price_growth"] == 5.0
    assert result["scenarios"]["optimistic"]["price_growth"] == 5.0
    assert result["scenarios"]["neutral"]["rent_growth"] == 3.0


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print("ok ", test.__name__)
    print(f"all {len(tests)} tests passed")
