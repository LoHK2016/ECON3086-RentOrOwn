"""Market Scenarios from the RVD forecast, and the range of outcomes across them.

The forecast is made offline (rentorbuy/market_benchmarks.py) and saved in the
snapshot as "market_benchmark". This file only reads it, so it runs in the
browser.
"""

from rentorbuy.calc.comparison import compare_scenarios

# Which end of the forecast each Market Scenario takes.
SCENARIO_ENDS = {"pessimistic": "low", "neutral": "point", "optimistic": "high"}


def forecast_scenarios(benchmark, horizon_years, fallback):
    """The Market Scenarios for a Horizon, and where they came from.

    Pessimistic takes the low end of the forecast for both price and rent
    growth, Neutral the middle, Optimistic the high end. If the snapshot has
    no forecast for this Horizon, the hand-entered `fallback` scenarios are
    used. Returns (scenarios, "forecast" or "assumptions").
    """
    year = str(horizon_years)
    try:
        price = benchmark["price"]["growth_pct"][year]
        rent = benchmark["rent"]["growth_pct"][year]
    except (TypeError, KeyError):
        return fallback, "assumptions"
    scenarios = {}
    for name, end in SCENARIO_ENDS.items():
        scenarios[name] = {"price_growth": price[end], "rent_growth": rent[end]}
    return scenarios, "forecast"


def outcome_range(results):
    """The smallest and largest gap across the scenarios, and who leads in all of them.

    The verdict is "buy" if buying ends ahead in every scenario, "rent" if
    renting does in every one, and "depends" if it changes with the market.
    """
    gaps = [result["gap"] for result in results.values()]
    low, high = min(gaps), max(gaps)
    if low > 0:
        verdict = "buy"
    elif high < 0:
        verdict = "rent"
    else:
        verdict = "depends"
    return {"verdict": verdict, "low_gap": low, "high_gap": high}


def compare_forecast(inputs, benchmark, fallback):
    """Run the Comparison under each Market Scenario for the chosen Horizon."""
    scenarios, source = forecast_scenarios(benchmark, inputs["horizon_years"], fallback)
    results = compare_scenarios(inputs, scenarios)
    return {
        "source": source,
        "scenarios": scenarios,
        "results": results,
        "range": outcome_range(results),
    }
