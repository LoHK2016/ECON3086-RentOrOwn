"""Interest rates from the HKMA open API (JSON, no key needed).

HKMA blocked one of our connections after about 20 requests in two hours.
Read docs/research/api-access-log.md before calling it by hand.
"""

import time

import requests

from rentorbuy.scrapers import USER_AGENT

API = "https://api.hkma.gov.hk/public/market-data-and-statistics"
HIBOR_URL = API + "/daily-monetary-statistics/daily-figures-interbank-liquidity"
PRIME_URL = API + "/monthly-statistical-bulletin/er-ir/hkd-ir-effdates"
BLOCKED = (403, 405, 429)  # the server is refusing us, not failing at random


def latest_record(url, tries=3):
    """The newest record from an HKMA endpoint. Retries network errors and 5xx, never a block."""
    for attempt in range(tries):
        try:
            response = requests.get(url, params={"pagesize": 1}, headers={"User-Agent": USER_AGENT}, timeout=30)
        except requests.RequestException:
            if attempt == tries - 1:
                raise
            time.sleep(2 ** attempt)
            continue
        if response.status_code in BLOCKED:
            response.raise_for_status()  # a block: retrying only makes it last longer
        if response.status_code >= 500 and attempt < tries - 1:
            time.sleep(2 ** attempt)
            continue
        response.raise_for_status()
        return response.json()["result"]["records"][0]


def get_hibor():
    """Today's one-month HIBOR, in % a year."""
    record = latest_record(HIBOR_URL)
    return {"hibor_1m": record["hibor_fixing_1m"], "hibor_date": record["end_of_date"]}


def get_prime():
    """The best lending (prime) rate, in % a year, and the date it took effect."""
    record = latest_record(PRIME_URL)
    return {"prime": record["best_lending_rate"], "prime_since": record["effect_date"]}
