"""Derive market-growth benchmarks from Hong Kong RVD historical indices.

Uses monthly private-domestic "All Classes" indices from the Rating and
Valuation Department. The scenarios are percentile bands of rolling
10-year annualized changes over the latest 30 years of available data.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen


PRICE_URL = "https://www.rvd.gov.hk/datagovhk/1.4M.csv"
RENT_URL = "https://www.rvd.gov.hk/datagovhk/1.3M.csv"
DATA = Path(__file__).resolve().parents[1] / "data"


def read_monthly_index(url):
    """Read the All Classes column from an RVD monthly CSV URL."""
    with urlopen(url, timeout=30) as response:
        text = response.read().decode("utf-8-sig")
    rows = list(csv.reader(text.splitlines()))
    header = next(row for row in rows if "Month" in row)
    all_classes = header.index("All Classes")
    values = []
    for row in rows:
        if len(row) <= all_classes or row[0] == "Month":
            continue
        try:
            month = datetime.strptime(row[0].strip(), "%m-%Y")
            index = float(row[all_classes].replace("Z", "").strip())
        except (ValueError, TypeError):
            continue
        values.append((month, index))
    values.sort()
    return values


def percentile(values, fraction):
    """Linear-interpolated percentile, with no external library needed."""
    ordered = sorted(values)
    if not ordered:
        raise ValueError("no benchmark observations")
    position = (len(ordered) - 1) * fraction
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def rolling_ten_year_cagrs(values, latest_month):
    """Annualized changes between month pairs exactly 10 years apart."""
    cutoff = datetime(latest_month.year - 30, latest_month.month, 1)
    recent = [(month, index) for month, index in values
              if cutoff <= month <= latest_month]
    by_year = {}
    for month, index in recent:
        by_year.setdefault((month.year, month.month), index)
    observations = []
    ordered = sorted(by_year)
    for month_key in ordered:
        start_year, start_month = month_key
        end_key = (start_year + 10, start_month)
        if end_key in by_year:
            start = by_year[month_key]
            end = by_year[end_key]
            cagr = (end / start) ** (1 / 10) - 1
            observations.append(cagr * 100)
    return observations


def derive_benchmarks(price_values, rent_values):
    """Derive 10th, median and 90th growth bands from 30 years of RVD data."""
    latest = max(price_values[-1][0], rent_values[-1][0])
    price_cagrs = rolling_ten_year_cagrs(price_values, latest)
    rent_cagrs = rolling_ten_year_cagrs(rent_values, latest)
    cutoff = datetime(latest.year - 30, latest.month, 1)
    from_date = cutoff.strftime("%Y-%m")

    def band(cagrs):
        return {
            "pessimistic": round(percentile(cagrs, 0.10), 2),
            "neutral": round(percentile(cagrs, 0.50), 2),
            "optimistic": round(percentile(cagrs, 0.90), 2),
        }

    price = band(price_cagrs)
    rent = band(rent_cagrs)
    return {
        "source": "Hong Kong Rating and Valuation Department",
        "source_urls": [PRICE_URL, RENT_URL],
        "history_from": from_date,
        "history_to": latest.strftime("%Y-%m"),
        "method": "Rolling 10-year annualized changes; 10th/50th/90th percentiles",
        "observations": len(price_cagrs),
        "price_growth": price,
        "rent_growth": rent,
        "scenarios": {
            name: {
                "price_growth": price[name],
                "rent_growth": rent[name],
            }
            for name in ("pessimistic", "neutral", "optimistic")
        },
    }


def fetch_benchmarks():
    """Fetch both official RVD files and derive the benchmark."""
    return derive_benchmarks(read_monthly_index(PRICE_URL), read_monthly_index(RENT_URL))


def saved_benchmarks():
    """Read the last saved benchmark snapshot."""
    path = DATA / "market_benchmarks.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    raise ValueError("no saved market benchmarks")


def current_benchmarks():
    """Use today's RVD data, with the saved benchmark as a network fallback."""
    try:
        return fetch_benchmarks()
    except (OSError, ValueError, csv.Error):
        return saved_benchmarks()
