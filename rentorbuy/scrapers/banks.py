"""Each bank's own prime rate (best lending rate), from its website.

An H-plan's cap is "the bank's prime minus a discount", so two banks with the
same plan can still charge different rates if their primes differ.
Standard Chartered's prime was not found online; the site uses HKMA's for it.
"""

import json
import re
import time

import requests
from bs4 import BeautifulSoup

from rentorbuy.scrapers import USER_AGENT

HSBC_URL = "https://www.hsbc.com.hk/investments/market-information/hk/lending-rate/"
BOCHK_URL = "https://www.bochk.com/whk/rates/hkDollarPrimeRate/hkDollarPrimeRate-enquiry.action?lang=en"
HANG_SENG_URL = "https://rbwm-api.hsbc.com.hk/pws-hk-hase-rates-papi-prod-proxy/v1/hkd-prime-rates"


def number_in(text):
    """The first number in `text`, e.g. 5.0 from 'Rate: 5.00%(for reference only)'."""
    match = re.search(r"\d+(\.\d+)?", text)
    if match is None:
        raise ValueError(f"no number in {text!r}")
    return float(match.group())


def parse_hsbc(html):
    """HSBC puts the current rate in a heading above its table of past changes."""
    soup = BeautifulSoup(html, "html.parser")
    for heading in soup.find_all("h2"):
        text = heading.get_text(" ", strip=True)
        if "Current Hong Kong Dollar Best Lending Rate" in text:
            return number_in(text.split(":")[1])
    raise ValueError("HSBC: rate heading not found")


def parse_bochk(html):
    """BOCHK puts the rate in the second cell of the row with class 'best-rate'."""
    soup = BeautifulSoup(html, "html.parser")
    row = soup.find("tr", class_="best-rate")
    if row is None:
        raise ValueError("BOCHK: rate row not found")
    return number_in(row.find_all("td")[1].get_text())


def parse_hang_seng(text):
    """Hang Seng's page fills itself from a small JSON file."""
    return float(json.loads(text)["rate"])


SOURCES = [
    ("HSBC", HSBC_URL, parse_hsbc),
    ("BOCHK", BOCHK_URL, parse_bochk),
    ("Hang Seng", HANG_SENG_URL, parse_hang_seng),
]


def get_primes(pause=1.0):
    """{bank: prime} for every bank we could read. A bank that fails is left out."""
    primes = {}
    for bank, url, parse in SOURCES:
        try:
            response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
            response.raise_for_status()
            primes[bank] = parse(response.text)
            print("ok  ", bank, primes[bank])
        except (requests.RequestException, ValueError, KeyError, IndexError) as error:
            print("FAIL", bank, error)
        time.sleep(pause)
    return primes
