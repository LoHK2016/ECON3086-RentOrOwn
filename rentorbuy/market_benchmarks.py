"""Forecast Hong Kong housing price and rent growth with a mean-reverting AR model.

The source series are official monthly private-domestic All Classes indices
from the Rating and Valuation Department. The forecast is a model estimate,
not a claim that future growth is certain.
"""

import csv
import json
import math
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

import numpy as np
from statsmodels.tsa.arima.model import ARIMA


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
    """Linear-interpolated percentile."""
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
    for month_key in sorted(by_year):
        start_year, start_month = month_key
        end_key = (start_year + 10, start_month)
        if end_key in by_year:
            start = by_year[month_key]
            end = by_year[end_key]
            observations.append(((end / start) ** (1 / 10) - 1) * 100)
    return observations


def derive_benchmarks(price_values, rent_values):
    """Keep historical percentile bands for fallback and transparency."""
    latest = max(price_values[-1][0], rent_values[-1][0])
    cutoff = datetime(latest.year - 30, latest.month, 1)

    def band(cagrs):
        return {
            "pessimistic": round(percentile(cagrs, 0.10), 2),
            "neutral": round(percentile(cagrs, 0.50), 2),
            "optimistic": round(percentile(cagrs, 0.90), 2),
        }

    price = band(rolling_ten_year_cagrs(price_values, latest))
    rent = band(rolling_ten_year_cagrs(rent_values, latest))
    return {
        "source": "Hong Kong Rating and Valuation Department",
        "source_urls": [PRICE_URL, RENT_URL],
        "history_from": cutoff.strftime("%Y-%m"),
        "history_to": latest.strftime("%Y-%m"),
        "method": "Rolling 10-year annualized changes; historical fallback",
        "price_growth": price,
        "rent_growth": rent,
    }


def mean_reverting_forecast(values, horizon_months=120):
    """Fit a mean-reverting AR(1) model with a linear trend."""
    latest = datetime.now().year - 30
    recent = [(month, index) for month, index in values if month.year >= latest]
    if len(recent) < 36:
        raise ValueError("not enough observations for a mean-reverting forecast")

    observed = np.array([math.log(index) for _, index in recent], dtype=float)
    candidates = [
        ((1, 0, 0), "ct"),
        ((1, 0, 0), "t"),
        ((1, 0, 0), None),
    ]
    best = None
    for order, trend in candidates:
        try:
            fitted = ARIMA(observed, order=order, trend=trend).fit()
            if not fitted.mle_retvals.get("converged", False):
                continue
            if not fitted.mle_retvals.get("converged", False):
                continue
            if best is None or fitted.aic < best["model"].aic:
                best = {"model": fitted, "order": order, "trend": trend}
        except Exception:
            continue
    if best is None:
        raise ValueError("no mean-reverting candidate could be fitted")

    forecast = best["model"].get_forecast(steps=horizon_months)
    start_index = math.exp(observed[-1])
    point_index = np.exp(np.asarray(forecast.predicted_mean))
    point = (point_index[-1] / start_index) ** (12 / horizon_months) - 1

    intervals = {}
    for confidence, alpha in ((80, 0.20), (95, 0.05)):
        frame = forecast.conf_int(alpha=alpha)
        low_index = np.exp(np.asarray(frame[:, 0]))
        high_index = np.exp(np.asarray(frame[:, 1]))
        low = (low_index[-1] / start_index) ** (12 / horizon_months) - 1
        high = (high_index[-1] / start_index) ** (12 / horizon_months) - 1
        intervals[f"{confidence}%"] = [
            round(low * 100, 2),
            round(high * 100, 2),
        ]

    return {
        "model": "AR1-linear-trend" if best["order"][1:] == (0, 0) else "ARIMA" + str(best["order"]),
        "trend": best["trend"],
        "horizon_years": horizon_months // 12,
        "point_growth_pct": round(point * 100, 2),
        "intervals_pct": intervals,
        "observations": len(observed),
    }


def mean_reverting_forecasts(price_values, rent_values):
    """Return separate 10-, 20- and 30-year mean-reverting forecasts."""
    latest = max(price_values[-1][0], rent_values[-1][0])
    cutoff = datetime(latest.year - 30, latest.month, 1)
    price = [(month, index) for month, index in price_values if month >= cutoff]
    rent = [(month, index) for month, index in rent_values if month >= cutoff]
    horizons = {}
    for years in (10, 20, 30):
        horizons[str(years)] = {
            "price": mean_reverting_forecast(price, years * 12),
            "rent": mean_reverting_forecast(rent, years * 12),
        }
    ten = horizons["10"]
    return {
        "source": "Hong Kong Rating and Valuation Department",
        "source_urls": [PRICE_URL, RENT_URL],
        "history_from": cutoff.strftime("%Y-%m"),
        "history_to": latest.strftime("%Y-%m"),
        "method": "Independent mean-reverting AR(1) models with linear trend; 10-, 20- and 30-year forecasts",
        "horizons": horizons,
        "price": ten["price"],
        "rent": ten["rent"],
    }


def fetch_benchmarks():
    """Fetch both RVD series and derive mean-reverting forecasts plus intervals."""
    price = read_monthly_index(PRICE_URL)
    rent = read_monthly_index(RENT_URL)
    historical = derive_benchmarks(price, rent)
    forecast = mean_reverting_forecasts(price, rent)
    historical["forecast"] = forecast
    historical["arima"] = forecast
    historical["method"] = "Independent mean-reverting AR(1) linear-trend 10-, 20- and 30-year forecasts"
    ten = forecast["horizons"]["10"]
    historical["scenarios"] = {
        "pessimistic": {
            "price_growth": ten["price"]["intervals_pct"]["95%"][0],
            "rent_growth": ten["rent"]["intervals_pct"]["95%"][0],
        },
        "neutral": {
            "price_growth": ten["price"]["point_growth_pct"],
            "rent_growth": ten["rent"]["point_growth_pct"],
        },
        "optimistic": {
            "price_growth": ten["price"]["intervals_pct"]["95%"][1],
            "rent_growth": ten["rent"]["intervals_pct"]["95%"][1],
        },
    }
    return historical


def saved_benchmarks():
    """Read the last saved benchmark snapshot."""
    path = DATA / "market_benchmarks.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    raise ValueError("no saved market benchmarks")


def current_benchmarks():
    """Use live RVD data with a saved snapshot as network fallback."""
    try:
        return fetch_benchmarks()
    except (OSError, ValueError, csv.Error):
        return saved_benchmarks()
