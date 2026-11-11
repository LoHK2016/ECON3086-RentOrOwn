"""Tests for reading each bank's prime rate, using pages saved on 2026-11-11. No network calls.

Run with `uv run python tests/test_banks.py` (or `pytest`).
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from rentorbuy.scrapers.banks import number_in, parse_bochk, parse_hang_seng, parse_hsbc


def fixture(name):
    with open(os.path.join(HERE, "fixtures", name), encoding="utf-8") as file:
        return file.read()


def test_number_in():
    assert number_in("5.00%(for reference only)") == 5.0
    assert number_in("  5.00000 % ") == 5.0
    try:
        number_in("n/a")
        assert False, "should have raised"
    except ValueError:
        pass


def test_hsbc():
    assert parse_hsbc(fixture("hsbc_prime.html")) == 5.0


def test_bochk():
    assert parse_bochk(fixture("bochk_prime.html")) == 5.0


def test_hang_seng():
    assert parse_hang_seng(fixture("hang_seng_prime.json")) == 5.0


def test_a_changed_page_fails_loudly():
    # If a bank redesigns its page we want an error, not a wrong number.
    for parse in [parse_hsbc, parse_bochk]:
        try:
            parse("<html><body><p>Page moved</p></body></html>")
            assert False, "should have raised"
        except ValueError:
            pass


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print("ok ", test.__name__)
    print(f"all {len(tests)} tests passed")
