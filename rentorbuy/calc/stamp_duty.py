"""Ad valorem stamp duty on a home bought by an individual.

Table in force from 26 Feb 2026 (IRD AVD FAQ Q1). Since 28 Feb 2024 the
duty is the same for every buyer, so it depends only on the price.
See docs/research/hk-property-rules-2026-11.md, section 1.
"""


def stamp_duty(price):
    """Return the stamp duty in HK$ for a home bought at `price` HK$."""
    if price <= 4_000_000:
        duty = 100
    elif price <= 4_323_780:
        duty = 100 + 0.20 * (price - 4_000_000)
    elif price <= 4_500_000:
        duty = 0.015 * price
    elif price <= 4_935_480:
        duty = 67_500 + 0.10 * (price - 4_500_000)
    elif price <= 6_000_000:
        duty = 0.0225 * price
    elif price <= 6_642_860:
        duty = 135_000 + 0.10 * (price - 6_000_000)
    elif price <= 9_000_000:
        duty = 0.03 * price
    elif price <= 10_080_000:
        duty = 270_000 + 0.10 * (price - 9_000_000)
    elif price <= 20_000_000:
        duty = 0.0375 * price
    elif price <= 21_739_120:
        duty = 750_000 + 0.10 * (price - 20_000_000)
    elif price <= 100_000_000:
        duty = 0.0425 * price
    elif price <= 109_574_470:
        duty = 4_250_000 + 0.30 * (price - 100_000_000)
    else:
        duty = 0.065 * price
    return round(duty)
