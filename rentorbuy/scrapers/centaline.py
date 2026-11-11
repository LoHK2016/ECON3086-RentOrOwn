"""Asking prices and rents per saleable sq ft from Centaline's listing pages.

Used when Midland refuses us (it refuses GitHub's servers). Centaline's
search page for an estate shows 24 listings, each with the saleable area and
the price per saleable sq ft. We take the median of the listings in that
Estate. These are asking prices, not transactions, so they usually sit a bit
above what flats really sell for.

robots.txt asks for 1 second between pages (crawl-delay: 1) and disallows
/centanetapi/api/; we only read the public list pages.
"""

import re
import statistics
import time
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from rentorbuy.scrapers import USER_AGENT

LIST_URL = "https://hk.centanet.com/findproperty/list/{kind}/{name}"  # kind: "buy" or "rent"
BLOCKED = (403, 405, 429)
MIN_LISTINGS = 5  # fewer listings than this is too few for a fair median


def per_ft_in(text):
    """'實用 實 702 呎 702呎 @ $21,082 /呎' -> 21082; None if there is no '@ $... /呎'."""
    match = re.search(r"@\s*\$\s*([\d,]+(\.\d+)?)\s*/呎", text)
    if match is None:
        return None
    return float(match.group(1).replace(",", ""))


def parse_listings(html, estate_name):
    """Price (or rent) per saleable sq ft of each listing whose title starts with the Estate's name.

    The search also returns flats nearby or with a similar name, so we keep
    only those in the Estate itself.
    """
    soup = BeautifulSoup(html, "html.parser")
    prices = []
    for card in soup.select(".list"):
        title = card.select_one(".title-lg")
        area = card.select_one(".usable-area")
        if title is None or area is None:
            continue
        if not title.get_text(" ", strip=True).startswith(estate_name):
            continue
        per_ft = per_ft_in(area.get_text(" ", strip=True))
        if per_ft is not None:
            prices.append(per_ft)
    return prices


def median_or_none(prices):
    if len(prices) < MIN_LISTINGS:
        return None
    return round(statistics.median(prices), 1)


def get_page(kind, estate_name):
    response = requests.get(LIST_URL.format(kind=kind, name=quote(estate_name)),
                            headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    return response.text


def get_estate(estate_name, pause=2.0):
    """Median asking price and rent per saleable sq ft for one Estate."""
    sale = parse_listings(get_page("buy", estate_name), estate_name)
    time.sleep(pause)
    rent = parse_listings(get_page("rent", estate_name), estate_name)
    return {
        "price_per_ft": median_or_none(sale),
        "rent_per_ft": median_or_none(rent),
        "sale_listings": len(sale),
        "rent_listings": len(rent),
        "source": LIST_URL.format(kind="buy", name=estate_name),
    }


def scrape_all(estate_names, pause=2.0):
    """{name: figures} for every Estate we could read. Stops at once if Centaline refuses us."""
    found = {}
    for name in estate_names:
        try:
            found[name] = get_estate(name, pause)
            print("ok  ", name, found[name]["price_per_ft"], found[name]["rent_per_ft"])
        except requests.HTTPError as error:
            print("FAIL", name, error)
            if error.response is not None and error.response.status_code in BLOCKED:
                print("Centaline is refusing us; stopping. See docs/research/api-access-log.md")
                break
        except requests.RequestException as error:
            print("FAIL", name, error)
        time.sleep(pause)
    return found
