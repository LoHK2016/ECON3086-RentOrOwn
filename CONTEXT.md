# Rent or Buy (HK)

A tool for ordinary Hong Kong residents to judge whether buying or renting a home is the better financial choice, using listing data from HK property platforms and mortgage data from HK banks.

## Language

### What is being compared

**Estate** (屋苑):
A named residential development (e.g. 太古城, 沙田第一城) that is the basic unit a comparison is about. Sale and rental listings are grouped by Estate. Only Estates on a fixed, curated list of large developments are covered.
_Avoid_: Building, project, development, district

**Flat** (單位):
One specific home in an Estate, picked by block, floor and flat letter through a bank's valuation tool, which also gives its Saleable Area.
_Avoid_: Unit (ambiguous with units of measure), property, apartment

**Saleable Area** (實用面積):
The floor area of a Flat in square feet, excluding common areas. All per-square-foot prices and rents use it.
_Avoid_: Gross area, size (when the measure matters)

**Comparison** (比較):
One buy-vs-rent evaluation for a Flat, or, as a fallback, for an Estate and a Saleable Area. It uses the Estate's typical price and rent per square foot unless the user overrides them.
_Avoid_: Calculation, analysis, query

### Prices

**Purchase Price** (成交價):
The price the user expects to pay for the Flat. Defaults to the Bank Valuation, or to the Estate's typical price per square foot times the Saleable Area.
_Avoid_: Asking price, market value

**Bank Valuation** (銀行估價):
The value a bank's valuation tool assigns to one specific Flat. A mortgage is sized on the lower of the Bank Valuation and the Purchase Price.
_Avoid_: Estimate, appraisal, market value

### The mortgage

**Mortgage Insurance** (按揭保險):
The HKMC Mortgage Insurance Programme, which lets a buyer borrow above the 70% loan-to-value cap. Its one-off premium is a buying cost.
_Avoid_: MIP (in user-facing text), insurance (alone)

**Debt Servicing Ratio** (供款與入息比率):
The monthly mortgage payment divided by the buyer's monthly income. Banks cap it at 50%; the tool warns above that but does not stop the Comparison.
_Avoid_: DTI, affordability

**Home Affordability** (置業負擔能力):
An estimate of the highest home price allowed by monthly repayments and down-payment funds. Existing loan repayments count toward the 50% debt-servicing cap. The down-payment input excludes stamp duty, fees and mortgage-insurance premiums; the estimate is not a bank approval.
_Avoid_: Guaranteed budget

**Debt-to-income Ratio** (債務與收入比率):
For the affordability estimate, existing monthly loan repayments plus the estimated mortgage payment, divided by gross monthly income.
_Avoid_: Loan balance divided by annual income

### How "worth it" is judged

**Horizon** (持有年期):
The number of years N over which buying and renting are compared.
_Avoid_: Period, term (term means the mortgage tenor)

**Net Worth Outcome** (淨資產結果):
Each side's net worth at the end of the Horizon. On the buy side: property value minus selling costs and the outstanding mortgage, plus any money the buyer invested, after all buying and holding costs. On the rent side: the invested down payment plus the invested monthly cost differences. The side with the higher Net Worth Outcome is the better choice.
_Avoid_: Total cost, savings, profit

**Break-even Year** (打和年期):
The first year in which the buy side's Net Worth Outcome exceeds the rent side's.
_Avoid_: Payback period

**Investment Return** (投資回報率):
The annual return assumed on money the renter does not spend on buying (the down payment and any monthly savings). Defaults to the best 12-month bank time-deposit rate. The user may instead pick an index ETF's past average return (Tracker Fund 2800.HK, or SPY after 30% US dividend tax) or enter their own.
_Avoid_: Opportunity cost rate, discount rate

**Market Scenario** (市況情景):
One of three named sets of assumptions for annual property price growth and rent growth over the Horizon: Pessimistic, Neutral and Optimistic. They are the low end, middle and high end of a model fitted to the last 30 years of the Rating and Valuation Department's price and rent indices (hand-entered values if that is missing).
_Avoid_: Forecast, prediction, appreciation rate

**Rental Yield** (租金回報率):
Annual rent divided by property price. Shown for reference only and never used as the verdict.
_Avoid_: Price-to-rent ratio (when presented as the answer)
