"""HSBC's property valuation tool: pick a Flat step by step, then get its Bank Valuation.

The tool is a chain of lookups. Each call says which level was just chosen
(`locate`) and returns the choices for the next level:

    nothing -> zones -> districts -> estates -> blocks -> floors -> flats

HSBC's server answers about 1 call in 4 with a random 404, so every call is
retried with a growing wait (as in the week 6 exercise). A 403, 405 or 429
means we are being refused, so we stop at once (see docs/research/api-access-log.md).

This module uses only the standard library, so it runs both in plain Python
and in the browser (Pyodide). The caller passes in `send`, an async function
that POSTs JSON and returns (status, reply): requests in a script, the
browser's fetch on the website.
"""

import asyncio

API = "https://rbwm-api.hsbc.com.hk/digital-pws-tools-mortgages-eapi-prod-proxy/v1/mortgages"
LOOKUP_URL = API + "/property-valuation-tool"
SEARCH_URL = API + "/property-valuation-address"
VALUATION_URL = API + "/property-valuation"

# Each level, the key that holds the chosen id, and the list the next lookup returns.
LEVELS = [
    ("zone", "zoneId", "districtList"),
    ("district", "districtId", "estateList"),
    ("estate", "estateId", "blockList"),
    ("block", "blockId", "floorList"),
    ("floor", "floor", "flatList"),
]
RETRY_STATUSES = (0, 404)  # 0: the request never got an answer (network error)


class HsbcError(Exception):
    """HSBC did not give an answer we can use."""


def average_valuations(values):
    """Return the average of the supplied bank valuations, rounded to HK dollars."""
    available = [int(value) for value in values if value is not None and int(value) > 0]
    if not available:
        raise ValueError("at least one bank valuation is required")
    return round(sum(available) / len(available))


def lookup_request(chosen, locale):
    """Request body asking for the choices below the deepest level in `chosen`.

    `chosen` maps keys such as "zoneId" to ids. HSBC wants every key present,
    with None for levels not chosen yet.
    """
    body = {"locale": locale, "locate": None}
    for level, key, _ in LEVELS:
        body[key] = chosen.get(key)
        if chosen.get(key) is not None:
            body["locate"] = level
    return body


def list_name(locate):
    """Name of the list in HSBC's reply after choosing `locate`."""
    if locate is None:
        return "zoneList"
    for level, _, next_list in LEVELS:
        if level == locate:
            return next_list
    raise ValueError(f"unknown level: {locate}")


def parse_options(reply, locate):
    """The choices in a lookup reply, as a list of {"id", "name"}."""
    options = []
    for item in reply.get(list_name(locate)) or []:
        options.append({"id": item["id"], "name": item["name"]})
    return options


def valuation_request(chosen, locale):
    """Request body for the valuation of the Flat in `chosen`."""
    body = {"locale": locale}
    for key in ["zoneId", "districtId", "estateId", "blockId", "floor", "flat"]:
        if chosen.get(key) is None:
            raise ValueError(f"choose a {key} first")
        body[key] = chosen[key]
    return body


def to_int(text):
    """HSBC sends numbers as text; '' or None means unknown."""
    if text in (None, ""):
        return None
    return int(float(text))


def parse_valuation(reply):
    """The useful parts of a valuation reply."""
    valuation = to_int(reply.get("valn"))
    if not valuation:
        raise HsbcError("HSBC has no valuation for this flat")
    return {
        "address": reply.get("propAddr"),
        "valuation": valuation,
        "saleable_area": to_int(reply.get("saleableArea")),
        "gross_area": to_int(reply.get("grossFloorArea")),
        "age": reply.get("propAge"),
        "date": (reply.get("valnDt") or "")[:10],
    }


def search_request(zone_id, keyword, locale):
    """Request body for finding estates by name within a zone."""
    return {"locale": locale, "zoneId": zone_id, "estateKeyword": keyword}


def parse_search(reply):
    """Estates found by a keyword search, as ids for the lookup chain."""
    found = []
    for item in reply.get("estateAddressList") or []:
        found.append({
            "zoneId": item["zone"]["id"],
            "districtId": item["district"]["id"],
            "estateId": item["estate"]["id"],
            "name": item["estate"]["name"],
        })
    return found


async def call_with_retry(send, url, body, wait=asyncio.sleep, tries=3):
    """POST `body` to `url`, retrying random failures with a growing wait."""
    status = None
    for attempt in range(tries):
        status, reply = await send(url, body)
        if status == 200 and reply is not None:
            return reply
        if status not in RETRY_STATUSES and status < 500:
            break  # refused or a bad request: trying again will not help
        if attempt < tries - 1:
            await wait(2 ** attempt)
    raise HsbcError(f"HSBC answered {status}")


async def get_options(send, chosen, locale="zh_HK", wait=asyncio.sleep):
    """Choices for the next level below what is in `chosen`."""
    body = lookup_request(chosen, locale)
    reply = await call_with_retry(send, LOOKUP_URL, body, wait)
    return parse_options(reply, body["locate"])


async def get_valuation(send, chosen, locale="zh_HK", wait=asyncio.sleep):
    """Bank Valuation and Saleable Area of the Flat in `chosen`."""
    reply = await call_with_retry(send, VALUATION_URL, valuation_request(chosen, locale), wait)
    return parse_valuation(reply)


async def search_estates(send, zone_id, keyword, locale="zh_HK", wait=asyncio.sleep):
    """Estates in a zone whose name contains `keyword`."""
    reply = await call_with_retry(send, SEARCH_URL, search_request(zone_id, keyword, locale), wait)
    return parse_search(reply)
