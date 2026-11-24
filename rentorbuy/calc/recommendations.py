"""Estate-level rent and purchase affordability estimates from a data snapshot."""

from rentorbuy.calc.buy_side import monthly_holding_costs, upfront_costs
from rentorbuy.calc.mortgage import max_ltv, monthly_payment

STRETCH_MULTIPLIER = 1.25
STRESS_RATE_INCREASE = 1.0
STRESS_INCOME_REDUCTION = 0.20


def affordability_label(monthly_housing_cost, monthly_income, monthly_debt,
                        comfortable_pct, cash_shortfall=False, preferred_payment=None):
    """Classify estimated housing costs against take-home pay and the user's limits."""
    ratio_pct = monthly_housing_cost / monthly_income * 100
    available_after_debt = max(0, monthly_income - monthly_debt)
    comfortable_limit = min(monthly_income * comfortable_pct / 100, available_after_debt)
    if preferred_payment is not None:
        comfortable_limit = min(comfortable_limit, preferred_payment)
    stretch_limit = min(comfortable_limit * STRETCH_MULTIPLIER, available_after_debt)

    if cash_shortfall or monthly_housing_cost + monthly_debt >= monthly_income:
        label = "risky"
    elif monthly_housing_cost <= comfortable_limit:
        label = "comfortable"
    elif monthly_housing_cost <= stretch_limit:
        label = "stretch"
    else:
        label = "risky"
    return label, ratio_pct, comfortable_limit, stretch_limit


def _buy_costs(price, rent, area, inputs, annual_rate):
    """Return estimated monthly owner costs and upfront cash for an Estate."""
    loan_to_value = max_ltv(price, inputs["first_time"])
    upfront = upfront_costs(
        price,
        price,
        loan_to_value,
        inputs["agent_fee_pct"],
        inputs["legal_fee"],
    )
    payment = monthly_payment(upfront["loan"], annual_rate, inputs["mortgage_years"])
    holding = monthly_holding_costs(
        area,
        inputs["management_fee_per_ft"],
        rent,
        inputs["rates_pct"],
        inputs["government_rent_pct"],
        price,
        inputs["repair_pct"],
    )
    monthly = {"mortgage": payment, **holding}
    monthly["total"] = sum(monthly.values())
    return monthly, upfront, loan_to_value


def recommend_estates(estates, inputs):
    """Rank Estate-average rent and purchase options against a take-home budget.

    `monthly_income` is monthly take-home pay; `saleable_area` is in square feet.
    Down-payment funds and savings both count toward estimated purchase cash needs.
    Filters only use Estate fields present in the supplied snapshot.
    """
    defaults = {
        "monthly_debt": 0,
        "down_payment": 0,
        "savings": 0,
        "comfortable_pct": 30,
        "preferred_payment": None,
        "first_time": True,
        "mortgage_years": 30,
        "management_fee_per_ft": 3,
        "rates_pct": 5,
        "government_rent_pct": 3,
        "repair_pct": 0.2,
        "agent_fee_pct": 1,
        "legal_fee": 10_000,
        "region": "",
        "district": "",
        "bedrooms": "",
        "mortgage_rate": None,
    }
    options = dict(defaults)
    options.update(inputs)
    income = options["monthly_income"]
    area = options["saleable_area"]
    rate = options["mortgage_rate"]

    if income is None or income <= 0:
        raise ValueError("monthly_income must be greater than zero")
    if area is None or area <= 0:
        raise ValueError("saleable_area must be greater than zero")
    if rate is None or rate < 0:
        raise ValueError("mortgage_rate must be zero or greater")
    if options["mortgage_years"] <= 0:
        raise ValueError("mortgage_years must be greater than zero")
    if options["monthly_debt"] < 0 or options["down_payment"] < 0 or options["savings"] < 0:
        raise ValueError("debt and cash budgets cannot be negative")
    if not 0 < options["comfortable_pct"] < 100:
        raise ValueError("comfortable_pct must be between zero and 100")
    if options["preferred_payment"] is not None and options["preferred_payment"] <= 0:
        raise ValueError("preferred_payment must be greater than zero")

    cash_available = options["down_payment"] + options["savings"]
    recommendations = []
    for estate in estates:
        if options["region"] and estate.get("region_en") != options["region"]:
            continue
        if options["district"] and estate.get("district_en") != options["district"]:
            continue

        price_per_ft = estate["price_per_ft"]
        rent_per_ft = estate["rent_per_ft"]
        if options["bedrooms"]:
            room_data = estate.get("by_room", {}).get(str(options["bedrooms"]))
            if room_data is None:
                continue
            price_per_ft = room_data["price_per_ft"]
            rent_per_ft = room_data["rent_per_ft"]

        price = round(price_per_ft * area)
        rent = round(rent_per_ft * area)
        common = {
            "estate_id": estate["id"],
            "estate_name": estate["name_en"],
            "estate_name_zh": estate["name_zh"],
            "region": estate["region_en"],
            "region_zh": estate["region_zh"],
            "district": estate["district_en"],
            "district_zh": estate["district_zh"],
            "bedrooms": str(options["bedrooms"]) if options["bedrooms"] else None,
            "saleable_area": area,
            "monthly_debt": options["monthly_debt"],
            "price": price,
            "monthly_rent": rent,
            "price_per_ft": price_per_ft,
            "rent_per_ft": rent_per_ft,
            "mortgage_rate": rate,
            "source": estate["source"],
            "source_date": estate.get("scraped"),
            "price_source": estate.get("price_source", "midland"),
        }

        stress_income = income * (1 - STRESS_INCOME_REDUCTION)
        rent_label, rent_ratio, rent_comfortable_limit, rent_stretch_limit = affordability_label(
            rent,
            income,
            options["monthly_debt"],
            options["comfortable_pct"],
            preferred_payment=options["preferred_payment"],
        )
        stress_rent_label, stress_rent_ratio, _, _ = affordability_label(
            rent,
            stress_income,
            options["monthly_debt"],
            options["comfortable_pct"],
            preferred_payment=options["preferred_payment"],
        )
        recommendations.append({
            **common,
            "id": f'{estate["id"]}:rent:{options["bedrooms"] or "any"}',
            "mode": "rent",
            "label": rent_label,
            "monthly_costs": {"rent": rent, "total": rent},
            "upfront": None,
            "cash_available": cash_available,
            "cash_shortfall": 0,
            "housing_pct": rent_ratio,
            "comfortable_pct": options["comfortable_pct"],
            "comfortable_budget": rent_comfortable_limit,
            "stretch_budget": rent_stretch_limit,
            "stress": {
                "monthly_cost": rent,
                "monthly_income": stress_income,
                "housing_pct": stress_rent_ratio,
                "label": stress_rent_label,
                "income_reduction_pct": STRESS_INCOME_REDUCTION * 100,
                "rate_increase_pct": STRESS_RATE_INCREASE,
            },
        })

        monthly, upfront, loan_to_value = _buy_costs(price, rent, area, options, rate)
        shortfall = max(0, upfront["total_cash"] - cash_available)
        buy_label, buy_ratio, comfortable_limit, stretch_limit = affordability_label(
            monthly["total"],
            income,
            options["monthly_debt"],
            options["comfortable_pct"],
            cash_shortfall=shortfall > 0,
            preferred_payment=options["preferred_payment"],
        )
        stress_monthly, _, _ = _buy_costs(
            price,
            rent,
            area,
            options,
            rate + STRESS_RATE_INCREASE,
        )
        stress_buy_label, stress_buy_ratio, _, _ = affordability_label(
            stress_monthly["total"],
            stress_income,
            options["monthly_debt"],
            options["comfortable_pct"],
            cash_shortfall=shortfall > 0,
            preferred_payment=options["preferred_payment"],
        )
        recommendations.append({
            **common,
            "id": f'{estate["id"]}:buy:{options["bedrooms"] or "any"}',
            "mode": "buy",
            "label": buy_label,
            "monthly_costs": monthly,
            "upfront": {**upfront, "loan_to_value": loan_to_value},
            "cash_available": cash_available,
            "cash_shortfall": shortfall,
            "housing_pct": buy_ratio,
            "comfortable_pct": options["comfortable_pct"],
            "comfortable_budget": comfortable_limit,
            "stretch_budget": stretch_limit,
            "stress": {
                "monthly_cost": stress_monthly["total"],
                "monthly_income": stress_income,
                "housing_pct": stress_buy_ratio,
                "label": stress_buy_label,
                "income_reduction_pct": STRESS_INCOME_REDUCTION * 100,
                "rate_increase_pct": STRESS_RATE_INCREASE,
            },
        })

    priority = {"comfortable": 0, "stretch": 1, "risky": 2}
    recommendations.sort(key=lambda item: (
        priority[item["label"]],
        item["housing_pct"],
        item["estate_name"],
        item["mode"],
    ))
    counts = {"buy": 0, "rent": 0}
    shortlist = []
    for item in recommendations:
        if counts[item["mode"]] < 6:
            shortlist.append(item)
            counts[item["mode"]] += 1
    return shortlist
