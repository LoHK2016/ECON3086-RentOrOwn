"""The `send` function for the website: POST JSON with the browser's fetch.

Runs only inside Pyodide (pyodide.http does not exist in plain Python).
rentorbuy.valuation takes it as an argument, so its own code stays testable.
"""

import json

from pyodide.http import pyfetch


async def send(url, body):
    """POST `body` as JSON; return (status, reply), with status 0 if there was no answer."""
    try:
        response = await pyfetch(
            url,
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps(body),
        )
    except Exception:  # pyfetch raises a JavaScript error type on network failure
        return 0, None
    if response.status != 200:
        return response.status, None
    return 200, await response.json()
