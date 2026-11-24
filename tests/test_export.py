"""Tests for the CSV and Excel export (rentorbuy/export.py).

Run with `uv run python tests/test_export.py` (or `pytest`). The .xlsx file is
read back with openpyxl, an independent reader, to show Excel-style software
can open it.
"""

import base64
import csv
import io
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openpyxl import load_workbook  # dev dependency: `uv run`

from rentorbuy.calc.market import compare_forecast
from rentorbuy.export import column_letter, export_file, safe_text, tables, to_csv

# The same no-cost, 1-year Comparison as test_compare_forecast_by_hand in test_calc.py:
# a $5M cash purchase against $15,000 rent, with prices -10% / 0 / +10%.
INPUTS = {
    "price": 5_000_000, "saleable_area": 500, "monthly_rent": 15_000, "horizon_years": 1,
    "ltv": 0, "mortgage_rate": 0, "investment_return": 0, "management_fee_per_ft": 0,
    "rates_pct": 0, "government_rent_pct": 0, "repair_pct": 0, "sell_cost_pct": 0,
}
FORECAST = {
    "price": {"growth_pct": {"1": {"low": -10, "point": 0, "high": 10}}},
    "rent": {"growth_pct": {"1": {"low": -1, "point": 0, "high": 2}}},
}
CONTEXT = {"estate": "Taikoo Shing", "flat_address": None, "snapshot_date": "2026-11-25", "today": "2026-11-25"}


def reply():
    return compare_forecast(INPUTS, FORECAST, {})


def table(title, lang="en"):
    return dict(tables(reply(), CONTEXT, lang))[title]


def test_summary_and_scenarios_by_hand():
    # Gaps worked out in test_compare_forecast_by_hand: -492,500, 7,500 and 507,500.
    summary = dict(table("Summary"))
    assert summary["Estate"] == "Taikoo Shing"
    assert summary["Who ends ahead"] == "Depends on market"
    assert summary["Smallest gap (buying minus renting)"] == -492_500
    assert summary["Largest gap (buying minus renting)"] == 507_500
    assert "Flat address" not in summary  # no specific flat chosen
    scenarios = table("Market scenarios")
    assert scenarios[1] == ["Pessimistic", -10, -1, "Renting", -492_500, None]
    assert scenarios[2][:5] == ["Neutral", 0, 0, "Buying", 7_500]


def test_day_one_and_net_worth_by_hand():
    # Day one: stamp duty 2.25% of 5M = 112,500, agent 1% = 50,000, legal 10,000;
    # cash purchase, so 5,000,000 down and 5,172,500 in all, no loan.
    day_one = dict(table("Day-one costs")[1:])
    assert day_one["Down payment"] == 5_000_000
    assert day_one["Stamp duty"] == 112_500
    assert day_one["Cash needed"] == 5_172_500
    assert day_one["Mortgage loan"] == 0
    # Neutral, year 1: owner 5,000,000 + 12 x 15,000 = 5,180,000; renter keeps 5,172,500.
    net_worth = table("Net worth by year")
    assert net_worth[0][3:5] == ["Buying · Neutral", "Renting · Neutral"]
    assert net_worth[2][0] == 1
    assert net_worth[2][3:5] == [5_180_000, 5_172_500]


def test_chinese_labels():
    summary = dict(table("摘要", "zh-Hant"))
    assert summary["最後邊個較著數"] == "視乎市況"


def test_safe_text_keeps_negative_numbers():
    assert safe_text(-492_500) == -492_500  # a number stays a number
    assert safe_text("=HYPERLINK(\"x\")") == "'=HYPERLINK(\"x\")"
    assert safe_text("-1 trick") == "'-1 trick"
    assert safe_text("Taikoo Shing") == "Taikoo Shing"


def test_csv_file():
    text = to_csv(tables(reply(), dict(CONTEXT, estate="=cmd"), "en"))
    assert text.startswith("﻿")  # byte-order mark, so Excel reads UTF-8
    rows = list(csv.reader(io.StringIO(text[1:])))
    assert rows[0] == ["Summary"]
    assert ["Estate", "'=cmd"] in rows  # text that looks like a formula is defused
    assert ["Smallest gap (buying minus renting)", "-492500"] in rows  # but negatives are not


def test_column_letter():
    assert column_letter(0) == "A"
    assert column_letter(25) == "Z"
    assert column_letter(26) == "AA"  # 26 letters, then two-letter names
    assert column_letter(27) == "AB"


def test_xlsx_file_opens_in_openpyxl():
    file = export_file(reply(), CONTEXT, "en", "xlsx")
    assert file["filename"] == "rent-or-buy-hk-2026-11-25.xlsx"
    data = base64.b64decode(file["base64"])
    assert zipfile.is_zipfile(io.BytesIO(data))
    book = load_workbook(io.BytesIO(data))
    assert book.sheetnames == [
        "Summary", "Market scenarios", "Inputs", "Net worth by year", "Day-one costs", "Monthly costs by year",
    ]
    summary = book["Summary"]
    assert summary["A1"].value == "Item"
    assert summary["B2"].value == "Taikoo Shing"
    gaps = {row[0].value: row[1].value for row in summary.iter_rows(min_row=2)}
    assert gaps["Smallest gap (buying minus renting)"] == -492_500  # a real number cell
    assert book["Market scenarios"]["F2"].value is None  # no Break-even Year: an empty cell


def test_unknown_kind_is_refused():
    try:
        export_file(reply(), CONTEXT, "en", "pdf")
        assert False, "should have raised"
    except ValueError:
        pass


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print("ok ", test.__name__)
    print(f"all {len(tests)} tests passed")
