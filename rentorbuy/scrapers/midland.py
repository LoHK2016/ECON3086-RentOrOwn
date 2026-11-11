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

# Hong Kong's 18 districts, by region, with their English names.
DISTRICTS = {
    "香港島": {"中西區": "Central and Western", "灣仔": "Wan Chai", "東區": "Eastern", "南區": "Southern"},
    "九龍": {"油尖旺": "Yau Tsim Mong", "深水埗": "Sham Shui Po", "九龍城": "Kowloon City",
             "黃大仙": "Wong Tai Sin", "觀塘": "Kwun Tong"},
    "新界": {"葵青": "Kwai Tsing", "荃灣": "Tsuen Wan", "屯門": "Tuen Mun", "元朗": "Yuen Long",
             "北區": "North", "大埔": "Tai Po", "沙田": "Sha Tin", "西貢": "Sai Kung", "離島": "Islands"},
}
REGIONS_EN = {"香港島": "Hong Kong Island", "九龍": "Kowloon", "新界": "New Territories"}

# Midland areas that are not one of the 18 districts, and the district they are in.
AREA_TO_DISTRICT = {"將軍澳": "西貢", "灣仔區": "灣仔", "中西區": "中西區"}


def district_of(midland_area):
    """The official district and region for a Midland area name, in both languages."""
    district = AREA_TO_DISTRICT.get(midland_area, midland_area)
    for region, districts in DISTRICTS.items():
        if district in districts:
            return {
                "region_zh": region,
                "region_en": REGIONS_EN[region],
                "district_zh": district,
                "district_en": districts[district],
            }
    raise ValueError(f"not one of the 18 districts: {midland_area}")


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
        **district_of(data["subregion"]["name"]),
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


BLOCKED = (403, 405, 429)  # Midland is refusing us, e.g. GitHub's servers get 403


def scrape_all(slugs=ESTATES, pause=1.0):
    """Scrape every Estate, waiting `pause` seconds between pages.

    A page that fails is skipped. If Midland refuses us, we stop at once:
    asking for the other pages would only be refused too.
    """
    estates = []
    for slug in slugs:
        try:
            estates.append(summarise(slug, get_estate_data(slug)))
            print("ok  ", slug)
        except requests.HTTPError as error:
            print("FAIL", slug, error)
            if error.response is not None and error.response.status_code in BLOCKED:
                print("Midland is refusing us; stopping. See docs/research/api-access-log.md")
                break
        except (requests.RequestException, KeyError, TypeError, AttributeError, ValueError) as error:
            print("FAIL", slug, error)
        time.sleep(pause)
    return estates
