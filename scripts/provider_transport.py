"""Small JSON HTTP transport shared by model and search adapters."""
from __future__ import annotations

import json
import urllib.error
import urllib.request

API_PROTOCOL = "iqs.provider-json-transport-api/1.0.0"
PUBLIC_API_EXPORTS = frozenset({
    "API_PROTOCOL", "PUBLIC_API_EXPORTS", "post_json",
})


def post_json(url: str, key: str, body: dict, timeout: float) -> tuple[int, dict]:
    """POST JSON and return a status/payload pair for every transport outcome."""
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST", headers={
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raw = error.read()
        try:
            payload = json.loads(raw.decode("utf-8"))
        except ValueError:
            payload = {"error": raw.decode("utf-8", "replace")[:500]}
        return error.code, payload
    except TimeoutError:
        return 0, {"error": "timeout"}
    except urllib.error.URLError as error:
        reason = getattr(error, "reason", error)
        if isinstance(reason, TimeoutError):
            return 0, {"error": "timeout"}
        return 0, {"error": "transport", "detail": str(reason)[:200]}
    except (OSError, ValueError) as error:
        return 0, {"error": "transport", "detail": str(error)[:200]}
