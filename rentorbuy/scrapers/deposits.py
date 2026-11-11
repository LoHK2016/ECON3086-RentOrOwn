"""HKD time deposit rates for new funds, from each bank's offer page.

We keep only the rate for each tenor (in months). The conditions (minimum
amount, channel, customer tier, how long the offer runs) stay on the bank's
page, which the site links to.
"""

import json
import re
import time

import requests
from bs4 import BeautifulSoup

from rentorbuy.scrapers import USER_AGENT


def tenor_months(text):
    """'3 months', '3-month', '12 months' or '2 years' as a number of months; None for weeks or days."""
    match = re.search(r"(\d+)\s*-?\s*(month|year)", text.lower())
    if match is None:
        return None
    number = int(match.group(1))
    if match.group(2) == "year":
        return number * 12
    return number


def rate_in(text):
    """'2.395%' as 2.395; None for '-' or an empty cell."""
    match = re.search(r"\d+(\.\d+)?(?=\s*%)", text)
    if match is None:
        return None
    return float(match.group())


def cells(row):
    return [cell.get_text(" ", strip=True) for cell in row.find_all(["td", "th"])]


def add_rate(rates, months, rate):
    """Keep the highest rate seen for each tenor (pages repeat tables for each customer tier)."""
    if months is None or rate is None:
        return
    if months not in rates or rate > rates[months]:
        rates[months] = rate


def parse_hsbc(html):
    """HSBC: one table per customer tier and currency.

    HKD tables say 'Minimum deposit amount: HKD...' in their caption. (Every
    caption mentions 'HKD1' when explaining RewardCash, so 'HKD' alone is not enough.)
    """
    rates = {}
    soup = BeautifulSoup(html, "html.parser")
    for table in soup.find_all("table"):
        caption = table.find("caption")
        if caption is None or not re.search(r"Minimum deposit amount:\s*HKD", caption.get_text()):
            continue
        for row in table.find_all("tr"):
            row_cells = cells(row)
            if len(row_cells) == 2:
                add_rate(rates, tenor_months(row_cells[0]), rate_in(row_cells[1]))
    return rates


def parse_bochk(html):
    """BOCHK: one table; the HKD rows for ordinary customers, with a column per tenor."""
    rates = {}
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    rows = table.find_all("tr")
    # Header: Currency | customer type | 3-month | 6-month | 12-month | channel
    tenors = [tenor_months(text) for text in cells(rows[0])][1:]
    currency = None
    for row in rows[1:]:
        row_cells = cells(row)
        # Only the first row of each currency has the currency cell (it spans the rows below).
        if re.fullmatch(r"[A-Z]{3}", row_cells[0]):
            currency = row_cells[0]
            row_cells = row_cells[1:]
        if currency == "HKD" and "Other Personal Banking Customer" in row_cells[0]:
            for months, text in zip(tenors, row_cells):
                add_rate(rates, months, rate_in(text))
    return rates


def parse_sc(html):
    """Standard Chartered: one table per currency, headed 'New funds of HKD10,000 or above'."""
    rates = {}
    soup = BeautifulSoup(html, "html.parser")
    for table in soup.find_all("table"):
        if "New funds of HKD" not in table.get_text():
            continue
        for row in table.find_all("tr"):
            row_cells = cells(row)
            if len(row_cells) >= 2:
                add_rate(rates, tenor_months(row_cells[-2]), rate_in(row_cells[-1]))
    return rates


def parse_mox(html):
    """Mox: the table straight after the 'HKD New Funds Time Deposit' heading."""
    rates = {}
    soup = BeautifulSoup(html, "html.parser")
    heading = soup.find(string=re.compile("HKD New Funds Time Deposit"))
    if heading is None:
        raise ValueError("Mox: HKD heading not found")
    for row in heading.find_next("table").find_all("tr"):
        row_cells = cells(row)
        if len(row_cells) == 2:
            add_rate(rates, tenor_months(row_cells[0]), rate_in(row_cells[1]))
    return rates


def parse_elebank(text):
    """eleBank: a JSON file (used in the week 6 exercise); HKD 'Time Deposit Rate' tenors."""
    rates = {}
    for item in json.loads(text):
        if item.get("rate_type") == "Time Deposit Rate" and item["currency"]["code"] == "HKD":
            for tenor in item["tenors"]:
                add_rate(rates, tenor_months(tenor["en"]), rate_in(tenor["rate"]))
    return rates


SOURCES = [
    ("HSBC", "https://www.hsbc.com.hk/accounts/offers/deposits/", parse_hsbc),
    ("BOCHK", "https://www.bochk.com/en/deposits/promotion/timedeposits.html", parse_bochk),
    ("Standard Chartered", "https://www.sc.com/hk/deposits/online-time-deposit/", parse_sc),
    ("Mox", "https://mox.com/promotions/time-deposit/", parse_mox),
    ("eleBank", "https://www.elebank.com/vendor/json/deposit_rate.json", parse_elebank),
]
PAGES = {  # where people read the offer; eleBank's JSON is not a page
    "eleBank": "https://www.elebank.com/",
}


def get_deposit_rates(pause=1.0):
    """{bank: {"rates": {"months": rate}, "url": offer page}} for every bank we could read."""
    found = {}
    for bank, url, parse in SOURCES:
        try:
            response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
            response.raise_for_status()
            rates = parse(response.text)
            if not rates:
                raise ValueError("no HKD rates found on the page")
            # JSON keys are text, so store tenors as "3", "6", "12".
            found[bank] = {"rates": {str(m): r for m, r in sorted(rates.items())}, "url": PAGES.get(bank, url)}
            print("ok  ", bank, rates)
        except (requests.RequestException, ValueError, KeyError, IndexError, AttributeError) as error:
            print("FAIL", bank, error)
        time.sleep(pause)
    return found
