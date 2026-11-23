# Rent or Buy? (HK)

Should you buy a Hong Kong home, or rent it and invest the difference? An ECON3086 group project.

- `rentorbuy/calc/`: the calculator, pure Python. It runs in the browser through Pyodide.
- `rentorbuy/calc/recommendations.py`: screens Estate-level buy and rent estimates against take-home pay, debts and available cash.
- `rentorbuy/valuation.py`: picks a specific flat and gets HSBC's valuation, live from the visitor's browser.
- `rentorbuy/scrapers/`: daily scrapers (Midland estate prices and rents, with Centaline's asking prices when Midland refuses us; HKMA rates, each bank's prime rate, HKD new-fund time deposit rates), run by GitHub Actions.
- `rentorbuy/etf_returns.py`: past returns of the Tracker Fund (2800.HK) and SPY, worked out with pandas from monthly prices that `rentorbuy/scrapers/etf.py` downloads with yfinance. Run by hand every few months, not daily.
- `data/`: dated snapshots; `data/latest.json` is what the site reads. `data/manual/` holds hand-entered assumptions.
- `tests/`: hand-checked `assert` tests (`test_calc.py`, `test_valuation.py`, `test_daily.py`, `test_scrapers.py`, `test_banks.py`, `test_deposits.py`, `test_etf_returns.py`, `test_centaline.py`).
- `web/`: the website (React, Tailwind, shadcn/ui). It only displays what Python returns.

## How it fits together

```mermaid
flowchart LR
    subgraph gha["GitHub Actions, every morning (scrape.yml)"]
        DAILY["rentorbuy/scrapers/daily.py"]
    end
    SRC["Midland or Centaline, HKMA, bank websites"] --> DAILY
    MAN["data/manual/assumptions.json<br/>data/etf_returns.json, data/hsbc_estates.json"] --> DAILY
    DAILY --> LATEST["data/latest.json<br/>+ dated copy"]
    subgraph browser["Visitor's browser (GitHub Pages)"]
        PAGE["web/: React page"]
        CALC["rentorbuy.compare_scenarios<br/>(Python in Pyodide)"]
        VAL["rentorbuy.valuation<br/>(Python in Pyodide)"]
        PAGE -->|"inputs dict"| CALC
        CALC -->|"results dict"| PAGE
        PAGE -->|"flat picked"| VAL
    end
    LATEST --> PAGE
    VAL <-->|"live, per visitor"| HSBC["HSBC valuation API"]
```

Each folder with rules of its own has a `README.md`: `rentorbuy/calc/`, `rentorbuy/scrapers/`, `data/` and `web/`.

See `CONTEXT.md` for the words we use, `docs/adr/` for why it is built this way, and `CONTRIBUTING.md` for how we work on it.

## Run it

```bash
uv run pytest                               # the tests (each file also runs alone: uv run python tests/test_calc.py)
uv run python -m rentorbuy.scrapers.daily   # scrape today's data
uv run python -m rentorbuy.scrapers.etf     # refresh ETF prices (Yahoo Finance) and returns, every few months
pnpm --dir web install && pnpm --dir web dev   # the site, at http://localhost:5173
```
