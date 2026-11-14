"""Strict JSON decoding for dashboard owner transports."""

import json
import math


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
