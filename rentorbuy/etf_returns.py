"""Past yearly returns of two index ETFs, worked out with pandas.

The prices come from data/etf/<ticker>.csv (saved by rentorbuy/scrapers/etf.py).
'Close' is the price alone; 'Adj Close' also counts dividends as reinvested.

US funds pay dividends to Hong Kong investors after 30% US withholding tax,
so for SPY we take 30% off the dividend part of each month's return.
"""

import json
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
ETF_DIR = DATA / "etf"
TICKERS = {
    "2800.HK": {"name": "Tracker Fund of Hong Kong (Hang Seng Index)", "dividend_tax": 0.0},
    "SPY": {"name": "SPDR S&P 500 ETF", "dividend_tax": 0.30},
}
YEARS = 20  # the return the comparison uses: the average over the last 20 years, or all we have
WINDOW = 10  # also show the worst 10-year stretch


def load_prices(ticker):
    return pd.read_csv(ETF_DIR / f"{ticker}.csv", index_col="Date", parse_dates=True)


def after_tax_growth(prices, dividend_tax):
    """What $1 invested in the first month is worth each month after, dividends reinvested.

    Each month's total return is the price change plus the dividend. Only the
    dividend part is taxed, at `dividend_tax` (0.30 for 30%).
    """
    total = prices["Adj Close"].pct_change()
    price_only = prices["Close"].pct_change()
    dividend = total - price_only
    after_tax = total - dividend * dividend_tax
    return (1 + after_tax.fillna(0)).cumprod()


def annual_return(growth, years):
    """Average yearly return, compounded, over the last `years` years, in %."""
    months = years * 12
    if len(growth) <= months:
        raise ValueError(f"need more than {months} months of prices")
    ratio = growth.iloc[-1] / growth.iloc[-1 - months]
    return (ratio ** (1 / years) - 1) * 100


def rolling_annual_returns(growth, years):
    """Average yearly return over every `years`-year stretch, in %, labelled by the month it ends."""
    ratio = growth / growth.shift(years * 12)
    return ((ratio ** (1 / years) - 1) * 100).dropna()


def summarise(ticker):
    """The figures the site shows for one ETF."""
    info = TICKERS[ticker]
    prices = load_prices(ticker)
    growth = after_tax_growth(prices, info["dividend_tax"])
    years = min(YEARS, (len(growth) - 1) // 12)  # Yahoo has 2800.HK only from 2008
    windows = rolling_annual_returns(growth, WINDOW)
    worst_end = windows.idxmin()
    return {
        "name": info["name"],
        "value": round(float(annual_return(growth, years)), 2),
        "years": years,
        "dividend_tax": info["dividend_tax"],
        "worst": round(float(windows.min()), 2),
        "worst_from": (worst_end - pd.DateOffset(years=WINDOW)).strftime("%Y-%m"),
        "worst_to": worst_end.strftime("%Y-%m"),
        "losing_share": round(float((windows < 0).mean()) * 100),  # % of 10-year stretches that lost money
        "history_from": prices.index[0].strftime("%Y-%m"),
        "prices_to": prices.index[-1].strftime("%Y-%m"),
    }


def save_summary():
    summary = {ticker: summarise(ticker) for ticker in TICKERS}
    text = json.dumps(summary, ensure_ascii=False, indent=2)
    (DATA / "etf_returns.json").write_text(text, encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(save_summary())
