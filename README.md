# Rent or Buy? (HK)

Should you buy a Hong Kong home, or rent it and invest the difference? An ECON3086 group project.

- `rentorbuy/calc/`: the calculator, pure Python. It runs in the browser through Pyodide.
- `rentorbuy/valuation.py`: picks a specific flat and gets HSBC's valuation, live from the visitor's browser.
- `rentorbuy/scrapers/`: daily scrapers (Midland estate prices and rents, HKMA rates), run by GitHub Actions.
- `data/`: dated snapshots; `data/latest.json` is what the site reads. `data/manual/` holds hand-entered assumptions.
- `tests/`: hand-checked `assert` tests (`test_calc.py`, `test_valuation.py`, `test_daily.py`).
- `web/`: the website (React, Tailwind, shadcn/ui). It only displays what Python returns.

See `CONTEXT.md` for the words we use and `docs/adr/` for why it is built this way.

## Run it

```bash
uv run python tests/test_calc.py && uv run python tests/test_valuation.py && uv run python tests/test_daily.py   # the tests
uv run python -m rentorbuy.scrapers.daily   # scrape today's data
pnpm --dir web install && pnpm --dir web dev   # the site, at http://localhost:5173
```
