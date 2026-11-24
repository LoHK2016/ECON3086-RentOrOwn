"""Forecast Hong Kong home price and rent growth from 30 years of RVD indices.

The source series are the Rating and Valuation Department's monthly private
domestic "All Classes" price and rent indices. Each series gets a mean-reverting
AR(1) model on its log level, and the model's forecast gives the growth a year
from now up to 30 years from now, with a 95% band.

Offline only: numpy and statsmodels do not run in the browser. The daily job
(rentorbuy/scrapers/daily.py) saves the result in the snapshot as
"market_benchmark", and rentorbuy/calc/market.py turns it into Market Scenarios.
The forecast is a model estimate, not a promise about the future.
"""

import csv
from datetime import datetime
from urllib.request import Request, urlopen

import numpy as np
from statsmodels.tsa.arima.model import ARIMA

from rentorbuy.scrapers import USER_AGENT

PRICE_URL = "https://www.rvd.gov.hk/datagovhk/1.4M.csv"
RENT_URL = "https://www.rvd.gov.hk/datagovhk/1.3M.csv"
HISTORY_YEARS = 30   # fit the model on the last 30 years of months
FORECAST_YEARS = 30  # the longest Horizon the site offers

# statsmodels' names for the deterministic part of each candidate model.
TRENDS = {
    "ct": "a constant and a linear trend",
    "t": "a linear trend",
    "c": "a constant",
}


def parse_monthly_index(text):
    """The (month, All Classes index) pairs in an RVD monthly CSV, oldest first."""
    rows = list(csv.reader(text.splitlines()))
    header = next((row for row in rows if row and row[0] == "Month"), None)
    if header is None or "All Classes" not in header:
        raise ValueError("the RVD file has no 'Month' / 'All Classes' header")
    column = header.index("All Classes")
    values = []
    for row in rows:
        try:
            month = datetime.strptime(row[0].strip(), "%m-%Y")
            index = float(row[column])
        except (ValueError, IndexError):
            continue  # the title, the header and the footnotes
        values.append((month, index))
    values.sort()
    return values


def read_monthly_index(url):
    """Download one RVD monthly CSV and parse it."""
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        return parse_monthly_index(response.read().decode("utf-8-sig"))


def last_years(values, years=HISTORY_YEARS):
    """The months in the last `years` years, counting back from the newest month."""
    latest = values[-1][0]
    cutoff = datetime(latest.year - years, latest.month, 1)
    return [(month, index) for month, index in values if month >= cutoff]


def annual_growth(start, end, months):
    """The steady % a year that turns `start` into `end` over `months` months."""
    return float(((end / start) ** (12 / months) - 1) * 100)


def percentile(values, fraction):
    """Linear-interpolated percentile, e.g. fraction 0.5 for the median."""
    ordered = sorted(values)
    if not ordered:
        raise ValueError("no observations")
    position = (len(ordered) - 1) * fraction
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def past_ten_year_growth(values):
    """How fast the index grew over every 10-year stretch in `values` (% a year).

    Returns the 10th percentile, median and 90th percentile, to set the
    forecast beside what really happened.
    """
    by_month = {(month.year, month.month): index for month, index in values}
    growth = []
    for (year, month), start in sorted(by_month.items()):
        end = by_month.get((year + 10, month))
        if end is not None:
            growth.append(annual_growth(start, end, 120))
    return {
        "low": round(percentile(growth, 0.10), 2),
        "median": round(percentile(growth, 0.50), 2),
        "high": round(percentile(growth, 0.90), 2),
    }


def fit_mean_reverting(log_index):
    """Fit AR(1) models with each trend in TRENDS; return (trend, model) with the lowest AIC."""
    best = None
    for trend in TRENDS:
        try:
            model = ARIMA(log_index, order=(1, 0, 0), trend=trend).fit()
        except (ValueError, np.linalg.LinAlgError):
            continue
        if not model.mle_retvals.get("converged", False):
            continue
        if best is None or model.aic < best[1].aic:
            best = (trend, model)
    if best is None:
        raise ValueError("no AR(1) model converged")
    return best


def mean_reverting_forecast(values, years=FORECAST_YEARS):
    """Forecast growth from the newest month to each of the next `years` years.

    growth_pct["10"] is the steady % a year from now to 10 years from now:
    "point" from the forecast itself, "low" and "high" from its 95% band. The
    band is for this one series under the fitted model; it leaves out the
    chance that the model itself is wrong.
    """
    if len(values) < 36:
        raise ValueError("need at least 36 months to fit the model")
    log_index = np.log([index for _, index in values])
    trend, model = fit_mean_reverting(log_index)
    forecast = model.get_forecast(steps=years * 12)
    point = np.exp(np.asarray(forecast.predicted_mean))
    band = np.exp(np.asarray(forecast.conf_int(alpha=0.05)))
    start = values[-1][1]
    growth = {}
    for year in range(1, years + 1):
        month = year * 12 - 1  # forecast row for the month `year` years ahead
        growth[str(year)] = {
            "low": round(annual_growth(start, band[month, 0], year * 12), 2),
            "point": round(annual_growth(start, point[month], year * 12), 2),
            "high": round(annual_growth(start, band[month, 1], year * 12), 2),
        }
    return {
        "model": "AR(1) on the log index with " + TRENDS[trend],
        "history_from": values[0][0].strftime("%Y-%m"),
        "history_to": values[-1][0].strftime("%Y-%m"),
        "past_ten_year_growth": past_ten_year_growth(values),
        "growth_pct": growth,
    }


def forecast_benchmarks(price_values, rent_values):
    """Price and rent forecasts from the last 30 years of each RVD series."""
    return {
        "source": "Rating and Valuation Department, private domestic All Classes indices",
        "source_urls": [PRICE_URL, RENT_URL],
        "price": mean_reverting_forecast(last_years(price_values)),
        "rent": mean_reverting_forecast(last_years(rent_values)),
    }


def current_benchmarks():
    """Today's forecasts from the live RVD files. Raises OSError or ValueError if they fail."""
    return forecast_benchmarks(read_monthly_index(PRICE_URL), read_monthly_index(RENT_URL))
