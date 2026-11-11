"""Run every scraper and save today's snapshot.

Writes data/<today>/snapshot.json and copies it to data/latest.json, which
the website reads. Run it with:  python -m rentorbuy.scrapers.daily
"""

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from rentorbuy.calc.deposits import best_deposit, rank_all
from rentorbuy.scrapers import banks, centaline, deposits, hkma, midland

DATA = Path(__file__).resolve().parents[2] / "data"


def last_snapshot():
    """The snapshot saved last time, or {} if there is none."""
    latest = DATA / "latest.json"
    if latest.exists():
        return json.loads(latest.read_text(encoding="utf-8"))
    return {}


def get_rates_or_last_known(assumptions, last):
    """Today's HIBOR and prime rate. Any that the HKMA API fails to give keeps its
    last saved value, and the rates are then marked stale."""
    rates = dict(last.get("rates") or assumptions["fallback_rates"])
    rates["stale"] = False
    for get in [hkma.get_hibor, hkma.get_prime]:
        try:
            rates.update(get())
        except (requests.RequestException, KeyError, IndexError, ValueError) as error:
            print("HKMA failed, keeping the last known value:", error)
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


def use_centaline(estates, figures, today):
    """Estates Midland did not give today take Centaline's asking prices, when it has enough listings.

    `figures` is {Estate name: Centaline figures}. An Estate with no usable
    Centaline figures keeps its last Midland figures and their date.
    """
    for estate in estates:
        found = figures.get(estate["name_zh"])
        if estate.get("scraped") == today or not found:
            continue
        if found["price_per_ft"] is None or found["rent_per_ft"] is None:
            continue
        estate.update({
            "price_per_ft": found["price_per_ft"],
            "rent_per_ft": found["rent_per_ft"],
            "price_source": "centaline",
            "transactions": None,
            "listings": found["sale_listings"],
            "source": found["source"],
            "scraped": today,
        })
    return estates


def primes_or_last_known(scraped, last, today):
    """Each bank's prime with the date it was read; a bank not read today keeps its last value."""
    primes = dict(last.get("bank_primes") or {})
    for bank, prime in scraped.items():
        primes[bank] = {"prime": prime, "date": today}
    return primes


def deposits_or_last_known(scraped, last, today):
    """Each bank's deposit rates with the date read; a bank not read today keeps its last rates."""
    found = dict(last.get("deposits") or {})
    for bank, info in scraped.items():
        found[bank] = dict(info, date=today)
    return found


def default_investment_return(found, assumptions):
    """The best 12-month new-fund rate, or the hand-entered fallback if no bank offers 12 months."""
    bank, rate = best_deposit(found, "12")
    if bank is None:
        return dict(assumptions["investment_return"])
    return {"value": rate, "bank": bank, "months": "12", "provisional": False}


def etf_returns():
    """Past ETF returns saved by rentorbuy/etf_returns.py (run by hand, not daily)."""
    path = DATA / "etf_returns.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


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
    today = datetime.now(ZoneInfo("Asia/Hong_Kong")).date().isoformat()  # GitHub's clock is UTC
    scraped = midland.scrape_all()
    print(f"{len(scraped)} estates scraped from Midland today")
    estates = add_last_known_estates(scraped, last, today)
    missing = [e["name_zh"] for e in estates if e["scraped"] != today]
    if missing:
        print(f"{len(missing)} estates missing; trying Centaline")
        estates = use_centaline(estates, centaline.scrape_all(missing), today)
    found = deposits_or_last_known(deposits.get_deposit_rates(), last, today)
    return {
        "date": today,
        "rates": get_rates_or_last_known(assumptions, last),
        "bank_primes": primes_or_last_known(banks.get_primes(), last, today),
        "estates": attach_hsbc_ids(estates),
        "bank_plans": assumptions["bank_plans"],
        "scenarios": {k: v for k, v in assumptions["scenarios"].items() if not k.startswith("_")},
        "deposits": found,
        "deposit_ranking": rank_all(found),
        "investment_return": default_investment_return(found, assumptions),
        "etf_returns": etf_returns(),
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
    print(f"saved {len(snapshot['estates'])} estates for {snapshot['date']}")
