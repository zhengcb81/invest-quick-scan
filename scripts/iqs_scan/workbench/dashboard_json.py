"""Strict JSON decoding for dashboard owner transports."""

import json
import math
import re


def owner_refusal(stream):
    """Only consume the validated error code from an owner's single JSON reply."""
    try:
        payload = decode_owner_json(stream)
    except (TypeError, ValueError, UnicodeError, RecursionError):
        return None
    if not isinstance(payload, dict):
        return None
    body = payload.get("error")
    if not isinstance(body, dict):
        body = payload
    code = body.get("error_code") or body.get("code")
    return code if isinstance(code, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,79}", code) else None


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _nonfinite(_):
    raise ValueError("nonfinite_json")


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        _nonfinite(value)
    return number


def decode_owner_json(raw):
    """Decode JSON without dropping duplicate keys or producing infinite values."""
    return json.loads(raw, object_pairs_hook=_unique_object,
                      parse_constant=_nonfinite, parse_float=_finite_float)
