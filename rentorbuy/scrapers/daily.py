"""Run every scraper and save today's snapshot.

Writes data/<today>/snapshot.json and copies it to data/latest.json, which
the website reads. Run it with:  python -m rentorbuy.scrapers.daily
"""

import json

import requests
from datetime import date
from pathlib import Path

from rentorbuy.scrapers import hkma, midland

DATA = Path(__file__).resolve().parents[2] / "data"


def last_snapshot():
    """The snapshot saved last time, or {} if there is none."""
    latest = DATA / "latest.json"
    if latest.exists():
        return json.loads(latest.read_text(encoding="utf-8"))
    return {}


def get_rates_or_last_known(assumptions, last):
    """Today's rates, or the last ones we saved (marked stale) if the HKMA API fails."""
    try:
        return hkma.get_rates()
    except (requests.RequestException, KeyError, IndexError, ValueError) as error:
        print("HKMA failed, using last known rates:", error)
        rates = dict(last.get("rates") or assumptions["fallback_rates"])
        rates["stale"] = True
        return rates


def add_last_known_estates(scraped, last, today):
    """Today's Estates, plus the last saved figures for any Estate not scraped today.

    Each Estate's "scraped" date says how old its figures are.
    """
    estates = []
    done = set()
    for estate in scraped:
        estate["scraped"] = today
        estates.append(estate)
        done.add(estate["id"])
    for estate in last.get("estates", []):
        if estate["id"] not in done:
            estate.setdefault("scraped", last["date"])
            estates.append(estate)
    return estates


def attach_hsbc_ids(estates):
    """Copy each Estate's HSBC ids (found by hsbc_estates.py) into it, for the flat picker."""
    path = DATA / "hsbc_estates.json"
    ids = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    for estate in estates:
        estate["hsbc"] = ids.get(estate["id"])
    return estates


def build_snapshot():
    """Scrape everything and combine it with the hand-entered assumptions."""
    assumptions = json.loads((DATA / "manual" / "assumptions.json").read_text(encoding="utf-8"))
    last = last_snapshot()
    today = date.today().isoformat()
    scraped = midland.scrape_all()
    return {
        "date": today,
        "rates": get_rates_or_last_known(assumptions, last),
        "estates": attach_hsbc_ids(add_last_known_estates(scraped, last, today)),
        "bank_plans": assumptions["bank_plans"],
        "scenarios": {k: v for k, v in assumptions["scenarios"].items() if not k.startswith("_")},
        "investment_return": assumptions["investment_return"],
    }


def save(snapshot):
    text = json.dumps(snapshot, ensure_ascii=False, indent=2)
    folder = DATA / snapshot["date"]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "snapshot.json").write_text(text, encoding="utf-8")
    (DATA / "latest.json").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    snapshot = build_snapshot()
    if len(snapshot["estates"]) == 0:
        raise SystemExit("no estate data at all; nothing saved")
    save(snapshot)
    fresh = [e for e in snapshot["estates"] if e["scraped"] == snapshot["date"]]
    print(f"saved {len(snapshot['estates'])} estates for {snapshot['date']} ({len(fresh)} scraped today)")
