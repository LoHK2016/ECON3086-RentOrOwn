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


def get_rates_or_last_known(assumptions):
    """Today's rates, or the last ones we saved (marked stale) if the HKMA API fails."""
    try:
        return hkma.get_rates()
    except (requests.RequestException, KeyError, IndexError, ValueError) as error:
        print("HKMA failed, using last known rates:", error)
        latest = DATA / "latest.json"
        if latest.exists():
            rates = json.loads(latest.read_text(encoding="utf-8"))["rates"]
        else:
            rates = dict(assumptions["fallback_rates"])
        rates["stale"] = True
        return rates


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
    return {
        "date": date.today().isoformat(),
        "rates": get_rates_or_last_known(assumptions),
        "estates": attach_hsbc_ids(midland.scrape_all()),
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
        raise SystemExit("no estates scraped; keeping yesterday's data")
    save(snapshot)
    print(f"saved {len(snapshot['estates'])} estates for {snapshot['date']}")
