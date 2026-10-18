"""Minimal DeepSeek Search client that returns a verified receipt.

No retries, no fallback provider, no credential logging. Transport is injected so
offline tests never touch the network.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import search_receipt as receipts

ENDPOINT = "https://api.deepseek.com/v1/tools/search"
DEFAULT_COST_MICROS = 5000  # 5 CNY / 1000 successful requests


def _urllib_transport(endpoint, payload, headers, timeout):
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return 0, str(error).encode("utf-8", "replace")


def search(
    query,
    *,
    exposure,
    policy_sha256,
    api_key,
    transport=None,
    endpoint=ENDPOINT,
    count=5,
    ori_question=None,
    need_content=True,
    timeout=30,
    cost_micros=DEFAULT_COST_MICROS,
):
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("deepseek_api_key_required")
    if not isinstance(query, str) or not 1 <= len(query) <= 2000:
        raise ValueError("search_query_invalid")
    if type(count) is not int or not 1 <= count <= 50:
        raise ValueError("search_count_invalid")
    payload = {"query": query, "count": count, "need_content": bool(need_content)}
    if ori_question is not None:
        if not isinstance(ori_question, str) or not 1 <= len(ori_question) <= 128:
            raise ValueError("search_ori_question_invalid")
        payload["ori_question"] = ori_question
    headers = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}
    status, body = (transport or _urllib_transport)(endpoint, payload, headers, timeout)
    requested_at = receipts.utc_now()
    if status != 200:
        return {
            "protocol": "iqs.search_receipt/1.0.0",
            "exposure_sha256": receipts.canonical_sha256(exposure),
            "policy_sha256": policy_sha256,
            "provider": "deepseek",
            "route_id": exposure["routes"][0]["route_id"],
            "query": query,
            "requested_at": requested_at,
            "completed_at": receipts.utc_now(),
            "status": "unavailable",
            "results": [],
            "result_count": 0,
            "cost_micros": 0,
            "currency": exposure["currency"],
            "response_sha256": receipts.hashlib.sha256(body).hexdigest(),
            "error_reason": "http_" + str(status),
        }
    receipt = receipts.from_response(
        body,
        exposure=exposure,
        policy_sha256=policy_sha256,
        provider="deepseek",
        route_id=exposure["routes"][0]["route_id"],
        query=query,
        requested_at=requested_at,
        completed_at=receipts.utc_now(),
        cost_micros=cost_micros,
    )
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--exposure", required=True, type=Path)
    parser.add_argument("--policy-sha256", required=True)
    parser.add_argument("--count", type=int, default=5)
    args = parser.parse_args(argv)
    import os

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    exposure = json.loads(args.exposure.read_text(encoding="utf-8"))
    receipt = search(args.query, exposure=exposure, policy_sha256=args.policy_sha256,
                     api_key=api_key, count=args.count)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0 if receipt["status"] in {"ok", "empty", "unavailable"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
