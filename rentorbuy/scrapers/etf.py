"""Monthly price history of two index ETFs, from Yahoo Finance via yfinance.

Run by hand every few months (`uv run python -m rentorbuy.scrapers.etf`). It
saves each ETF's whole history to data/etf/<ticker>.csv, then
rentorbuy/etf_returns.py works out the returns from those files.
"""

import yfinance as yf

from rentorbuy.etf_returns import ETF_DIR, TICKERS, save_summary


def download(ticker):
    """Month-end prices: 'Close' (price only) and 'Adj Close' (dividends reinvested)."""
    history = yf.Ticker(ticker).history(period="max", interval="1mo", auto_adjust=False)
    if history.empty:
        raise ValueError(f"{ticker}: no prices returned")
    prices = history[["Close", "Adj Close"]]
    prices.index = prices.index.tz_localize(None).date  # keep just the date
    prices.index.name = "Date"
    return prices


if __name__ == "__main__":
    ETF_DIR.mkdir(parents=True, exist_ok=True)
    for ticker in TICKERS:
        prices = download(ticker)
        prices.to_csv(ETF_DIR / f"{ticker}.csv")
        print(ticker, len(prices), "months,", prices.index[0], "to", prices.index[-1])
    print(save_summary())
