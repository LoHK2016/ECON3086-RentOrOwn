"""Tests for the HSBC valuation lookups, using replies saved from real calls on 2026-11-11.

No test calls HSBC: `send` is replaced by a fake that plays back saved replies.
Run with `python tests/test_valuation.py` (or `pytest`).
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rentorbuy.valuation import (
    HsbcError,
    LOOKUP_URL,
    call_with_retry,
    get_options,
    get_valuation,
    lookup_request,
    parse_search,
    parse_valuation,
    valuation_request,
)

TAIKOO = {"zoneId": "1", "districtId": "3", "estateId": "210"}
SAVED_VALUATION = {
    "propAddr": "香港鰂魚涌太古城海景花園 第33 座青松閣4樓A室",
    "valn": "18930000",
    "grossFloorArea": "1232",
    "saleableArea": "1146",
    "propAge": 45,
    "valnDt": "2026-11-11 23:59:50 +0800",
}


def fake_sender(replies):
    """An async `send` that returns each (status, reply) in turn and records the bodies."""
    sent = []

    async def send(url, body):
        sent.append(body)
        return replies[len(sent) - 1]

    return send, sent


async def no_wait(seconds):
    pass


def run(coroutine):
    return asyncio.run(coroutine)


def test_lookup_request():
    # Nothing chosen: ask for zones, with every key present.
    assert lookup_request({}, "en_HK") == {
        "locale": "en_HK", "locate": None, "zoneId": None, "districtId": None,
        "estateId": None, "blockId": None, "floor": None,
    }
    # An estate chosen: ask for its blocks.
    body = lookup_request(TAIKOO, "zh_HK")
    assert body["locate"] == "estate"
    assert body["estateId"] == "210" and body["blockId"] is None


def test_valuation_request_needs_every_level():
    try:
        valuation_request(TAIKOO, "zh_HK")
        assert False, "should have raised"
    except ValueError:
        pass
    full = dict(TAIKOO, blockId="229,2919,nil", floor="4", flat="A")
    assert valuation_request(full, "zh_HK")["flat"] == "A"


def test_parse_valuation():
    flat = parse_valuation(SAVED_VALUATION)
    assert flat["valuation"] == 18_930_000
    assert flat["saleable_area"] == 1146
    assert flat["gross_area"] == 1232
    assert flat["date"] == "2026-11-11"
    try:
        parse_valuation({"valn": ""})
        assert False, "should have raised"
    except HsbcError:
        pass


def test_parse_search():
    reply = {"code": "00", "estateAddressList": [
        {"zone": {"id": "1", "name": "香港"}, "district": {"id": "3", "name": "鰂魚涌"},
         "estate": {"id": "210", "name": "太古城"}}]}
    assert parse_search(reply) == [dict(TAIKOO, name="太古城")]
    assert parse_search({"code": "00"}) == []


def test_get_options_reads_the_right_list():
    blocks = {"blockList": [{"id": "229,2919,nil", "name": "海景花園 第33 座青松閣"}]}
    send, sent = fake_sender([(200, blocks)])
    options = run(get_options(send, TAIKOO, wait=no_wait))
    assert options == [{"id": "229,2919,nil", "name": "海景花園 第33 座青松閣"}]
    assert sent[0]["locate"] == "estate"


def test_retry_after_random_404():
    # HSBC's random 404 twice, then an answer: we get the answer on the third try.
    send, sent = fake_sender([(404, None), (404, None), (200, SAVED_VALUATION)])
    full = dict(TAIKOO, blockId="229,2919,nil", floor="4", flat="A")
    flat = run(get_valuation(send, full, wait=no_wait))
    assert flat["valuation"] == 18_930_000
    assert len(sent) == 3


def test_gives_up_after_three_tries():
    send, sent = fake_sender([(404, None)] * 3)
    try:
        run(call_with_retry(send, LOOKUP_URL, {}, wait=no_wait))
        assert False, "should have raised"
    except HsbcError:
        pass
    assert len(sent) == 3


def test_stops_at_once_when_refused():
    # 405 means HSBC is refusing us: asking again would only make it worse.
    send, sent = fake_sender([(405, None), (200, {})])
    try:
        run(call_with_retry(send, LOOKUP_URL, {}, wait=no_wait))
        assert False, "should have raised"
    except HsbcError:
        pass
    assert len(sent) == 1


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print("ok ", test.__name__)
    print(f"all {len(tests)} tests passed")
