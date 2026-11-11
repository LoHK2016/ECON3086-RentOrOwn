"""Renting, and growing the money a renter (or an owner) does not spend."""


def rent_for_year(start_rent, rent_growth, year_index):
    """Monthly rent in year `year_index` (0 is the first year), rising once a year."""
    return start_rent * (1 + rent_growth / 100) ** year_index


def monthly_rate(annual_return):
    """Monthly rate that compounds to `annual_return` % over a year."""
    return (1 + annual_return / 100) ** (1 / 12) - 1


def grow_one_month(balance, annual_return):
    """Balance after one month of investment return."""
    return balance * (1 + monthly_rate(annual_return))
