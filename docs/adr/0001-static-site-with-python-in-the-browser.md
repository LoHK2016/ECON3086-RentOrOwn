# Static site, with the Python calculator running in the browser

Only Python earns programming marks, but we want an Apple-style interface (React, Tailwind and shadcn/ui) and free public hosting. So the site is a static build on GitHub Pages, and every calculation is done by our own pure-standard-library Python package, `rentorbuy`, run in the visitor's browser with Pyodide. The page sends a dict of inputs to `rentorbuy.compare()` and draws the dict it returns; the JavaScript only displays results and never calculates them.

Scraping does not happen in the browser. A GitHub Actions job runs the Python scrapers every day and commits a dated JSON snapshot (`data/<date>/…` plus `data/latest.json`), which the site reads.

The one live call from the browser is the flat picker: when a visitor picks a block, floor and flat, our Python (`rentorbuy.valuation`, run by Pyodide) asks HSBC's valuation tool directly. HSBC allows this: its API answers any website's browser (CORS `*`). Each visitor makes a handful of calls for their own flat, as they would on HSBC's own page, so there is no crawling of every flat.

## Considered options

- **Streamlit or NiceGUI.** More Python and more library marks, but the look cannot follow Apple's Human Interface Guidelines, and they need a running server.
- **Calculating in JavaScript.** Simplest for the web, but that code earns no marks.
- **A Python backend (FastAPI on a host).** Works, but adds a server to run and pay for, with no gain for a calculator whose inputs fit in one page.

## Consequences

- Pyodide is loaded by JavaScript, so it earns no library marks. Library marks come from the scrapers, the backtest and the charts for the slides (requests, BeautifulSoup, pandas, matplotlib).
- `rentorbuy.calc` must stay standard-library only, so it loads fast in Pyodide and can be tested with `assert` in plain Python.
- Data is at most a day old, except a specific flat's HSBC valuation, which is live.
- The flat picker depends on HSBC keeping its API open to browsers. If HSBC closes it, "Typical flat" (estate averages) still works.
- `rentorbuy.valuation` takes the HTTP call as an argument (`send`), so the same code runs with `requests` in scripts, with the browser's fetch on the site, and with a fake in the tests.
