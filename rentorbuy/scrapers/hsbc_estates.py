"""Find each curated Estate's ids in HSBC's valuation tool.

Run by hand when the estate list changes (the ids rarely do):
    python -m rentorbuy.scrapers.hsbc_estates
It makes one keyword search per Estate and saves data/hsbc_estates.json,
which the daily snapshot copies into each Estate as "hsbc".
"""

import asyncio
import json
import time
from pathlib import Path

import requests

from rentorbuy.scrapers import USER_AGENT
from rentorbuy.scrapers.estates import ESTATES
from rentorbuy.valuation import HsbcError, search_estates

OUT = Path(__file__).resolve().parents[2] / "data" / "hsbc_estates.json"
ZONES = {"港島": "1", "九龍": "2", "新界": "3"}  # Midland region -> HSBC zone
calls = []


async def send(url, body):
    """POST with requests. Blocking is fine in a one-off script."""
    try:
        response = requests.post(url, json=body, headers={"User-Agent": USER_AGENT}, timeout=30)
    except requests.RequestException:
        calls.append(0)
        return 0, None
    calls.append(response.status_code)
    if response.status_code != 200:
        return response.status_code, None
    return 200, response.json()


def best_match(name, found):
    """The search result whose name is exactly `name`, else the only result, else None."""
    for estate in found:
        if estate["name"] == name:
            return estate
    if len(found) == 1:
        return found[0]
    return None


def find_estate(name, region):
    """Search Midland's region first, then the other zones (HSBC puts Tseung Kwan O in the New Territories)."""
    zones = [ZONES[region]] + [z for z in ZONES.values() if z != ZONES[region]]
    for zone in zones:
        match = best_match(name, asyncio.run(search_estates(send, zone, name)))
        time.sleep(1)
        if match:
            return match
    return None


def main():
    mapping = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    for slug in ESTATES:
        region, name, midland_id = slug.split("-")[0], slug.split("-")[-2], slug.split("-")[-1]
        if midland_id in mapping:
            continue  # already found; no need to ask HSBC again
        try:
            match = find_estate(name, region)
        except HsbcError as error:
            print("FAIL", name, error)
            break  # stop rather than keep asking, see docs/research/api-access-log.md
        print("ok  " if match else "??? ", name, "->", match)
        if match:
            mapping[midland_id] = match
    OUT.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {len(mapping)} of {len(ESTATES)}; HTTP statuses: {calls}")


if __name__ == "__main__":
    main()
