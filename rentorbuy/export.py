"""Write a Comparison's results as a CSV or an Excel (.xlsx) file.

Standard library only (csv, zipfile), so it runs in the browser through Pyodide
like rentorbuy/calc. The page passes in what rentorbuy.compare_forecast
returned; this file only lays those numbers out in tables and calculates
nothing new.
"""

import base64
import csv
import io
import zipfile
from xml.sax.saxutils import escape

SCENARIOS = ["pessimistic", "neutral", "optimistic"]

LABELS = {
    "en": {
        "summary": "Summary", "scenarios": "Market scenarios", "inputs": "Inputs",
        "net_worth": "Net worth by year", "day_one": "Day-one costs", "monthly": "Monthly costs by year",
        "item": "Item", "value": "Value", "year": "Year",
        "estate": "Estate", "flat": "Flat address", "snapshot_date": "Data snapshot date",
        "export_date": "Export date", "source": "Market scenarios from",
        "forecast": "RVD price and rent forecast", "assumptions": "Hand-entered scenarios (provisional)",
        "verdict": "Who ends ahead", "buy": "Buying", "rent": "Renting", "depends": "Depends on market",
        "low_gap": "Smallest gap (buying minus renting)", "high_gap": "Largest gap (buying minus renting)",
        "pessimistic": "Pessimistic", "neutral": "Neutral", "optimistic": "Optimistic",
        "scenario": "Scenario", "price_growth": "Price growth (% a year)", "rent_growth": "Rent growth (% a year)",
        "ahead": "Ahead at the end", "gap": "Gap at the end (buying minus renting)", "break_even": "Break-even year",
        "price": "Purchase price", "monthly_rent": "Monthly rent", "area": "Saleable area (sq ft)",
        "mortgage_rate": "Mortgage rate (%)", "ltv": "Loan-to-value (%)", "mortgage_years": "Mortgage term (years)",
        "horizon": "Horizon (years)", "investment_return": "Investment return (% a year)",
        "down_payment": "Down payment", "stamp_duty": "Stamp duty", "agent_fee": "Agent fee",
        "legal_fee": "Legal fee", "insurance": "Mortgage insurance", "cash_rebate": "Cash rebate",
        "total_cash": "Cash needed", "loan": "Mortgage loan", "monthly_payment": "Monthly mortgage payment",
        "mortgage": "Mortgage", "management_fee": "Management fee", "rates": "Rates",
        "government_rent": "Government rent", "repairs": "Repairs", "owner_monthly": "Owner pays",
        "rent_monthly": "Tenant pays", "buy_worth": "Buying", "rent_worth": "Renting",
    },
    "zh-Hant": {
        "summary": "摘要", "scenarios": "市況情景", "inputs": "輸入",
        "net_worth": "每年淨資產", "day_one": "上會當日開支", "monthly": "每年每月開支",
        "item": "項目", "value": "數值", "year": "年",
        "estate": "屋苑", "flat": "單位地址", "snapshot_date": "數據日期",
        "export_date": "匯出日期", "source": "市況情景來源",
        "forecast": "差估署樓價及租金預測", "assumptions": "人手設定情景（暫定）",
        "verdict": "最後邊個較著數", "buy": "買樓", "rent": "租樓", "depends": "視乎市況",
        "low_gap": "最小差距（買樓減租樓）", "high_gap": "最大差距（買樓減租樓）",
        "pessimistic": "悲觀", "neutral": "中性", "optimistic": "樂觀",
        "scenario": "情景", "price_growth": "樓價升幅（每年 %）", "rent_growth": "租金升幅（每年 %）",
        "ahead": "最後領先", "gap": "最後差距（買樓減租樓）", "break_even": "打和年期",
        "price": "成交價", "monthly_rent": "月租", "area": "實用面積（平方呎）",
        "mortgage_rate": "按揭利率（%）", "ltv": "按揭成數（%）", "mortgage_years": "按揭年期（年）",
        "horizon": "持有年期（年）", "investment_return": "投資回報率（每年 %）",
        "down_payment": "首期", "stamp_duty": "印花稅", "agent_fee": "代理佣金",
        "legal_fee": "律師費", "insurance": "按揭保險", "cash_rebate": "現金回贈",
        "total_cash": "合共要預備", "loan": "貸款額", "monthly_payment": "每月供款",
        "mortgage": "供款", "management_fee": "管理費", "rates": "差餉",
        "government_rent": "地租", "repairs": "維修", "owner_monthly": "業主每月俾",
        "rent_monthly": "租客每月俾", "buy_worth": "買樓", "rent_worth": "租樓",
    },
}


def tables(reply, context, lang):
    """The export as a list of (title, rows) tables; the first row of each is its header.

    `reply` is what compare_forecast returned. `context` has "estate",
    "flat_address" (or None), "snapshot_date" and "today". Money is rounded to
    whole dollars; rates stay in % as the Comparison used them.
    """
    t = LABELS[lang]
    results = reply["results"]
    middle = results["neutral"]
    used = middle["inputs"]
    upfront = middle["upfront"]

    summary = [[t["item"], t["value"]], [t["estate"], context["estate"]]]
    if context.get("flat_address"):
        summary.append([t["flat"], context["flat_address"]])
    summary += [
        [t["snapshot_date"], context["snapshot_date"]],
        [t["export_date"], context["today"]],
        [t["source"], t[reply["source"]]],
        [t["verdict"], t[reply["range"]["verdict"]]],
        [t["low_gap"], round(reply["range"]["low_gap"])],
        [t["high_gap"], round(reply["range"]["high_gap"])],
    ]

    scenarios = [[t["scenario"], t["price_growth"], t["rent_growth"], t["ahead"], t["gap"], t["break_even"]]]
    for name in SCENARIOS:
        result = results[name]
        growth = reply["scenarios"][name]
        scenarios.append([
            t[name], growth["price_growth"], growth["rent_growth"],
            t[result["verdict"]], round(result["gap"]), result["break_even_year"],
        ])

    inputs = [
        [t["item"], t["value"]],
        [t["price"], round(used["price"])],
        [t["monthly_rent"], round(used["monthly_rent"])],
        [t["area"], used["saleable_area"]],
        [t["mortgage_rate"], round(used["mortgage_rate"], 2)],
        [t["ltv"], round(used["ltv"] * 100, 2)],
        [t["mortgage_years"], used["mortgage_years"]],
        [t["horizon"], used["horizon_years"]],
        [t["investment_return"], round(used["investment_return"], 2)],
    ]

    net_worth = [[t["year"]] + [f"{t[side]} · {t[name]}" for name in SCENARIOS for side in ("buy_worth", "rent_worth")]]
    for i, year in enumerate(middle["years"]):
        row = [year]
        for name in SCENARIOS:
            row += [round(results[name]["buy_net_worth"][i]), round(results[name]["rent_net_worth"][i])]
        net_worth.append(row)

    day_one = [[t["item"], t["value"]]]
    for key, label in [("down_payment", "down_payment"), ("stamp_duty", "stamp_duty"), ("agent_fee", "agent_fee"),
                       ("legal_fee", "legal_fee"), ("insurance_premium", "insurance"), ("cash_rebate", "cash_rebate"),
                       ("total_cash", "total_cash"), ("loan", "loan")]:
        day_one.append([t[label], round(upfront[key])])
    day_one.append([t["monthly_payment"], round(middle["monthly_payment"])])

    cost_keys = ["mortgage", "management_fee", "rates", "government_rent", "repairs", "owner_monthly", "rent_monthly"]
    monthly = [[t["year"]] + [t[key] for key in cost_keys]]
    for cost in middle["yearly_costs"]:
        monthly.append([cost["year"]] + [round(cost[key]) for key in cost_keys])

    return [
        (t["summary"], summary),
        (t["scenarios"], scenarios),
        (t["inputs"], inputs),
        (t["net_worth"], net_worth),
        (t["day_one"], day_one),
        (t["monthly"], monthly),
    ]


def safe_text(value):
    """Stop a spreadsheet reading text such as "=HYPERLINK(...)" as a formula.

    Only text is changed (a leading ' is added); numbers, negative ones
    included, are left as numbers.
    """
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def to_csv(all_tables):
    """All tables one after another in one CSV, each under its title.

    Starts with a byte-order mark so Excel reads the Chinese text as UTF-8.
    """
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\r\n")
    for title, rows in all_tables:
        writer.writerow([safe_text(title)])
        for row in rows:
            writer.writerow(["" if value is None else safe_text(value) for value in row])
        writer.writerow([])
    return "﻿" + out.getvalue()


def column_letter(index):
    """Spreadsheet column name for a 0-based index: 0 -> A, 25 -> Z, 26 -> AA."""
    letters = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def sheet_xml(rows):
    """One worksheet's XML: numbers as numbers, text as inline strings, None left empty."""
    lines = []
    for r, row in enumerate(rows, start=1):
        cells = []
        for c, value in enumerate(row):
            ref = f"{column_letter(c)}{r}"
            if value is None:
                continue
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                cells.append(f'<c r="{ref}"><v>{value}</v></c>')
            else:
                text = escape(str(value))
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{text}</t></is></c>')
        lines.append(f'<row r="{r}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(lines)}</sheetData></worksheet>'
    )


def to_xlsx(all_tables):
    """An Excel workbook with one sheet per table, as bytes.

    An .xlsx file is a zip of XML files; these are the smallest set Excel,
    Numbers and LibreOffice open.
    """
    count = len(all_tables)
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        + "".join(
            f'<Override PartName="/xl/worksheets/sheet{n}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for n in range(1, count + 1)
        )
        + "</Types>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/></Relationships>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
        + "".join(
            f'<sheet name="{escape(title[:31])}" sheetId="{n}" r:id="rId{n}"/>'
            for n, (title, _) in enumerate(all_tables, start=1)
        )
        + "</sheets></workbook>"
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(
            f'<Relationship Id="rId{n}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{n}.xml"/>'
            for n in range(1, count + 1)
        )
        + "</Relationships>"
    )
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as book:
        book.writestr("[Content_Types].xml", content_types)
        book.writestr("_rels/.rels", root_rels)
        book.writestr("xl/workbook.xml", workbook)
        book.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        for n, (_, rows) in enumerate(all_tables, start=1):
            book.writestr(f"xl/worksheets/sheet{n}.xml", sheet_xml(rows))
    return out.getvalue()


def export_file(reply, context, lang, kind):
    """The file for the page to download: {"filename", "mime", "base64"}.

    `kind` is "csv" or "xlsx". The contents are base64 text, since JSON
    (how the page and Python talk) cannot carry raw bytes.
    """
    all_tables = tables(reply, context, lang)
    if kind == "csv":
        data = to_csv(all_tables).encode("utf-8")
        mime = "text/csv;charset=utf-8"
    elif kind == "xlsx":
        data = to_xlsx(all_tables)
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        raise ValueError(f"unknown export kind {kind!r}")
    return {
        "filename": f"rent-or-buy-hk-{context['today']}.{kind}",
        "mime": mime,
        "base64": base64.b64encode(data).decode("ascii"),
    }
