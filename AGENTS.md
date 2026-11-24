# AGENTS.md

## Course requirements

This is an ECON3086 (Python Programming for FinTech) group project. Read `docs/course_requirements/project-brief.md` before making design or stack decisions. The constraints that most shape the code:

- Only Python code earns programming marks; any non-Python code earns none.
- Library usage is 40% of the mark, and harder libraries used correctly score higher.
- Code must be simple and readable, with functions tested using `assert`. Every group member must write code and be able to explain every line.
- The app must show its answer is right (checked by hand or against past data) and say what it cannot tell you.

Name domain concepts (Estate, Flat, Saleable Area, Bank Valuation…) with the terms defined in `CONTEXT.md`.

## Where code goes

Before changing anything in `rentorbuy/calc/`, `rentorbuy/scrapers/`, `data/` or `web/`, read that folder's `README.md`: it holds the folder's rules and gotchas. Update it in the same change when a rule, a data flow or a gotcha it describes changes.

`docs/adr/0001-static-site-with-python-in-the-browser.md` explains why; the rules across folders:

- **Every calculation is Python.** The site in `web/` (React, TypeScript) sends inputs to `rentorbuy.compare()` and draws the dict it returns. When the page needs a new number, add it to the Python's return value and display it; the TypeScript only formats and lays out.
- **Browser Python is standard library only.** `rentorbuy/calc/`, `rentorbuy/valuation.py` and `rentorbuy/browser.py` are copied into the site and run in Pyodide (`web/scripts/copy-python.mjs`). `browser.py` may also import `pyodide`. HTTP calls are passed in as an argument (`send`), so tests can use a fake.
- **Third-party libraries live in the offline code.** requests, BeautifulSoup, pandas and yfinance belong in `rentorbuy/scrapers/` and `rentorbuy/etf_returns.py`, which is where the library marks come from.

## Tests

- Each module has a `tests/test_<module>.py` of plain functions using `assert`, runnable on its own (`uv run python tests/test_calc.py`) and all together (`uv run pytest`).
- Expected numbers are worked out by hand, with the working in a comment beside the `assert`. Reading the number off the code's own output proves nothing.
- Scrapers are tested against saved pages in `tests/fixtures/`, so tests never touch a live site.
- Run `uv run pytest` before you finish. A new test file also goes in the "Run the tests" step of `.github/workflows/deploy.yml`.

## Data

The daily GitHub Actions job (`.github/workflows/scrape.yml`) writes `data/<date>/` and `data/latest.json`. To change what is in them, change the scraper and let the job rewrite them. Hand-entered assumptions live in `data/manual/assumptions.json`.

## Live data sources

Before calling HKMA, Midland, a bank site or any other live source by hand, read `docs/research/api-access-log.md`. It says how to work from the saved snapshot, and logs each source's limits (HKMA blocked us on 2026-11-11).

## Group workflow

Before committing or opening a pull request, read `CONTRIBUTING.md`: branch names, commit messages, and what a PR must show.

## Agent skills

### Issue tracker

Issues live in this repo's GitHub Issues (gh CLI). See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary (needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
