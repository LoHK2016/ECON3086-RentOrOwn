"""Typical price and rent per square foot for each Estate, from Midland.

Midland's estate page is built by Next.js, which puts all the page's data in
one JSON block: <script id="__NEXT_DATA__">. We read that block instead of
the visible HTML, because the numbers there are already clean.
"""

import json
import time

import requests
from bs4 import BeautifulSoup

from rentorbuy.scrapers import USER_AGENT
from rentorbuy.scrapers.estates import ESTATES

BASE_URL = "https://www.midland.com.hk/zh-hk/estate/"

# Midland's Chinese district names, in English, for the English site.
DISTRICTS_EN = {
    "中西區": "Central and Western", "灣仔": "Wan Chai", "東區": "Eastern", "南區": "Southern",
    "油尖旺": "Yau Tsim Mong", "深水埗": "Sham Shui Po", "九龍城": "Kowloon City",
    "黃大仙": "Wong Tai Sin", "觀塘": "Kwun Tong", "將軍澳": "Tseung Kwan O", "西貢": "Sai Kung",
    "沙田": "Sha Tin", "大埔": "Tai Po", "北區": "North", "荃灣": "Tsuen Wan", "葵青": "Kwai Tsing",
    "屯門": "Tuen Mun", "元朗": "Yuen Long", "離島": "Islands",
}


def get_estate_data(slug):
    """Download one estate page and return Midland's estate data dict."""
    response = requests.get(BASE_URL + slug, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    page = json.loads(script.string)
    return page["props"]["pageProps"]["result"]["estateData"]


def first_number(*values):
    """The first value that is a positive number, or None."""
    for value in values:
        if isinstance(value, (int, float)) and value > 0:
            return value
    return None


def summarise(slug, data):
    """Keep only what the tool needs from Midland's estate data."""
    market = data.get("market_stat") or {}
    listings = data.get("property_stat") or {}
    by_room = {}
    for rooms, stat in (data.get("market_stat_by_room") or {}).items():
        by_room[rooms] = {
            "price_per_ft": first_number(stat.get("avg_net_ft_price")),
            "rent_per_ft": first_number(stat.get("avg_net_ft_rent")),
        }
    return {
        "id": data["id"],
        "slug": slug,
        "name_zh": data["name"]["chi"],
        "name_en": data["name"]["en"],
        "district_zh": data["subregion"]["name"],
        "district_en": DISTRICTS_EN.get(data["subregion"]["name"], data["subregion"]["name"]),
        # Prefer recent transactions; fall back to the asking prices of listings.
        "price_per_ft": first_number(market.get("net_ft_price"), data.get("avg_net_ft_price")),
        "rent_per_ft": first_number(market.get("net_ft_rent"), listings.get("avg_net_ft_rent")),
        "transactions": market.get("tx_count"),
        "for_sale": data.get("sell_count"),
        "for_rent": data.get("rent_count"),
        "min_area": data.get("min_net_area"),
        "max_area": data.get("max_net_area"),
        "by_room": by_room,
        "source": BASE_URL + slug,
    }


def scrape_all(slugs=ESTATES, pause=1.0):
    """Scrape every Estate, waiting `pause` seconds between pages. Skips pages that fail."""
    estates = []
    for slug in slugs:
        try:
            estates.append(summarise(slug, get_estate_data(slug)))
            print("ok  ", slug)
        except (requests.RequestException, KeyError, TypeError, AttributeError, ValueError) as error:
            print("FAIL", slug, error)
        time.sleep(pause)
    return estates
