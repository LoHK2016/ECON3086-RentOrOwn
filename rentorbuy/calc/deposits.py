"""Which bank pays the most on a HKD time deposit, for each tenor.

`deposits` looks like {"HSBC": {"rates": {"3": 2.395, "6": 2.195}, "url": ...}, ...},
with tenors in months as text (that is how they come back from JSON).
"""

TENORS = ["3", "6", "12"]  # the tenors the site compares


def best_deposit(deposits, months):
    """(bank, rate) with the highest rate for `months`, or (None, None) if no bank offers it."""
    best_bank = None
    best_rate = None
    for bank, info in deposits.items():
        rate = info["rates"].get(months)
        if rate is not None and (best_rate is None or rate > best_rate):
            best_bank = bank
            best_rate = rate
    return best_bank, best_rate


def rank_deposits(deposits, months):
    """Every bank offering `months`, highest rate first: [{"bank", "rate", "url"}]."""
    offers = []
    for bank, info in deposits.items():
        rate = info["rates"].get(months)
        if rate is not None:
            offers.append({"bank": bank, "rate": rate, "url": info["url"]})
    offers.sort(key=lambda offer: offer["rate"], reverse=True)
    return offers


def rank_all(deposits):
    """The ranking for each tenor the site compares."""
    ranking = {}
    for months in TENORS:
        ranking[months] = rank_deposits(deposits, months)
    return ranking
