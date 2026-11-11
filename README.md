# Rent or Buy? (HK)

Should you buy a Hong Kong home, or rent it and invest the difference? An ECON3086 group project.

- `rentorbuy/calc/`: the calculator, pure Python. It runs in the browser through Pyodide.
- `rentorbuy/valuation.py`: picks a specific flat and gets HSBC's valuation, live from the visitor's browser.
- `rentorbuy/scrapers/`: daily scrapers (Midland estate prices and rents, with Centaline's asking prices when Midland refuses us; HKMA rates, each bank's prime rate, HKD new-fund time deposit rates), run by GitHub Actions.
- `rentorbuy/etf_returns.py`: past returns of the Tracker Fund (2800.HK) and SPY, worked out with pandas from monthly prices that `rentorbuy/scrapers/etf.py` downloads with yfinance. Run by hand every few months, not daily.
- `data/`: dated snapshots; `data/latest.json` is what the site reads. `data/manual/` holds hand-entered assumptions.
- `tests/`: hand-checked `assert` tests (`test_calc.py`, `test_valuation.py`, `test_daily.py`, `test_scrapers.py`, `test_banks.py`, `test_deposits.py`, `test_etf_returns.py`, `test_centaline.py`).
- `web/`: the website (React, Tailwind, shadcn/ui). It only displays what Python returns.

See `CONTEXT.md` for the words we use and `docs/adr/` for why it is built this way.

## Run it

```bash
uv run python tests/test_calc.py && uv run python tests/test_valuation.py && uv run python tests/test_daily.py   # the tests
uv run python -m rentorbuy.scrapers.daily   # scrape today's data
uv run python -m rentorbuy.scrapers.etf     # refresh ETF prices (Yahoo Finance) and returns, every few months
pnpm --dir web install && pnpm --dir web dev   # the site, at http://localhost:5173
```
