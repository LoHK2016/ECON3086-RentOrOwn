# Calculator

`rentorbuy.calc` is pure standard-library Python. The site passes inputs to it
through Pyodide; JavaScript only displays the returned values. `compare()` works
on one Flat or Estate and `recommend_estates()` ranks Estate-level rent and
purchase estimates from the supplied data snapshot. Recommendations never
create individual Flat listings.

## Estate recommendations

`recommend_estates(estates, inputs)` uses `monthly_income` as monthly take-home
pay, `monthly_debt` as existing repayments, and the sum of `down_payment` and
`savings` as cash available for estimated purchase costs. A comfortable limit is
the lower of the chosen share of take-home pay, income left after debt, and an
optional preferred payment. The Stretch boundary is 125% of that limit, capped
at income left after debt. A purchase with an upfront cash shortfall is Risky.

Prices and rents are the snapshot's per-square-foot Estate averages multiplied
by the entered Saleable Area. A bedroom filter is applied only when that
bedroom's `by_room` average exists in the snapshot. Purchase costs reuse
`upfront_costs()`, `monthly_holding_costs()` and the existing mortgage rules:
30 years, the selected first-time-buyer LTV assumption, 1% agent fee, $10,000
legal fee, $3 per sq ft monthly management fee, 5% rates, 3% government rent,
and 0.2% annual repairs by default. These costs and the +1 percentage-point
rate / -20% income stress scenario are illustrative assumptions, not quotes or
bank tests. The management fee is a flat assumption, not a quoted HOA fee.
The stamp-duty schedule is the project's documented rule; the one-off Mortgage
Insurance premium remains provisional. Ongoing property insurance and actual
insurer costs are not included.

The source URL and source date are carried from each Estate record. The
recommendations cannot identify available Flats, exact fees, commute times,
amenities, or a buyer's tax position.
