"""One metered external retrieval HTTP operation, never an answer model.

The coordinator owns the shared budget, linked operation journal and outcome
transaction. This adapter consumes its one-shot admitted permit, performs ONE
request, and returns bounded data and truthful transport metadata. It never
retries, dispatches another route, persists raw pages or fabricates native tools.
"""
from __future__ import annotations

import copy
import hashlib
import os
import re
from typing import Any

from src.config.quick_scan_search_policy import SearchPolicy, _admit
from src.providers.external_search_parsers import DEFAULT_MAX_IN_MEMORY_BYTES, parse_route, strict_search_json
from src.utils.http_client import http_client_manager
from src.utils.quick_scan_work_transport import QuickScanSendAttempt

ADAPTER_VERSION = "stockqa.external_retrieval/1.0.0"
ENDPOINTS = {
    "brave": "https://api.search.brave.com/res/v1/web/search",
    "tavily": "https://api.tavily.com/search",
    "zai_rest": "https://api.z.ai/api/paas/v4/web_search",
    "zai_mcp_streamable": "https://api.z.ai/api/mcp/web_search_prime/mcp",
}
_ERROR_CODES = frozenset({"insufficient_quota", "quota_exceeded", "billing_hard_limit_reached", "account_quota_exceeded", "insufficient_funds", "rate_limit_exceeded", "too_many_requests", "rate_limited"})


class ExternalSearchTransportError(RuntimeError):
    """Only safe metadata leaves a failed paid transport; outcome may be unknown."""

    def __init__(self, receipt: dict[str, Any]) -> None:
        self.receipt = receipt
        super().__init__("external retrieval transport failed")


class ExternalSearchProvider:
    def __init__(self, policy: SearchPolicy, route_id: str) -> None:
        if route_id not in policy.admitted:
            raise ValueError("external route is not admitted")
        route = next((item for item in policy.routes if item["route_id"] == route_id), None)
        if route is None:
            raise ValueError("external route is missing")
        self.route = copy.deepcopy(route)
        self.retrieval = copy.deepcopy(policy.retrieval)
        kind = self.route["kind"]
        if self.route["endpoint"] != ENDPOINTS.get(kind):
            raise ValueError("external endpoint does not match the allowlisted protocol")
        cap = self.retrieval["max_in_memory_response_bytes"]
        if type(cap) is not int or not 1024 <= cap <= DEFAULT_MAX_IN_MEMORY_BYTES:
            raise ValueError("external response byte cap must be within 1024..1000000")
        ok, reason = _admit(self.route, require_storage_rights=True)
        if not ok:
            raise ValueError(reason)

    @staticmethod
    def _request_id(headers: Any) -> str | None:
        value = headers.get("x-request-id") or headers.get("X-Request-Id")
        if isinstance(value, str) and 0 < len(value.strip()) <= 300 and not any(ord(c) < 32 for c in value):
            return value.strip()
        return None

    def fetch(self, permit: QuickScanSendAttempt, *, query: str, top_k: int, locale: str) -> dict[str, Any]:
        """Read short search data; caller must durably settle the returned outcome."""
        if not isinstance(permit, QuickScanSendAttempt) or permit.binding is not None or permit.budget_binding is None or permit.budget_attempt_id != permit.attempt_id:
            raise ValueError("external retrieval requires a budget-only durable permit")
        if not isinstance(query, str) or not query.strip() or len(query) > 2000 or type(top_k) is not int or not 1 <= top_k <= 10:
            raise ValueError("external query or result bound is invalid")
        if not isinstance(locale, str) or re.fullmatch(r"[a-z]{2}-[A-Z]{2}", locale) is None:
            raise ValueError("external locale is invalid")
        if self.route["kind"] == "zai_mcp_streamable":
            # MCP initialize/discovery/search are separate metered operations.
            # The forthcoming coordinator must negotiate and journal them; a
            # tools/call without that proof cannot silently stand in for MCP.
            raise ValueError("mcp_handshake_required")
        key = os.environ.get(self.route["credential_env"])
        if not isinstance(key, str) or not key:
            raise ValueError("credential_env_unset")
        headers = {"Accept": "application/json"}
        kind = self.route["kind"]
        if kind == "brave":
            headers["X-Subscription-Token"] = key
            language, country = locale.split("-")
            params = {"q": query, "count": top_k, "country": country, "search_lang": "zh-hans" if locale == "zh-CN" else language}
            method, data = "GET", {"params": params}
        else:
            headers["Authorization"] = "Bearer " + key
            if kind == "tavily":
                body = {"query": query, "max_results": top_k, "search_depth": "basic", "include_answer": False, "include_raw_content": False, "include_images": False, "include_published_date": True, "auto_parameters": False}
            else:
                body = {"search_query": query, "count": top_k, "search_engine": "search-prime", "search_recency_filter": "noLimit"}
            method, data = "POST", {"json": body}
        session = http_client_manager.get_metered_sync_session()
        permit.consume_for_post()
        receipt: dict[str, Any] = {"origin": "external", "adapter_version": ADAPTER_VERSION, "route_id": self.route["route_id"], "route_kind": kind, "attempt_id": permit.attempt_id, "http_request_count": 1, "http_status_code": None, "request_id": None, "outcome": "unknown"}
        response = None
        try:
            response = session.request(method, self.route["endpoint"], headers=headers, timeout=30, stream=True, allow_redirects=False, **data)
            status = response.status_code
            if type(status) is not int:
                raise ValueError("invalid_http_status")
            receipt["http_status_code"] = status
            receipt["request_id"] = self._request_id(response.headers)
            body_parts, size = [], 0
            for part in response.iter_content(chunk_size=8192):
                if not isinstance(part, bytes):
                    raise ValueError("invalid_response_chunk")
                size += len(part)
                if size > self.retrieval["max_in_memory_response_bytes"]:
                    raise ValueError("response_exceeds_in_memory_cap")
                body_parts.append(part)
            raw = b"".join(body_parts)
            receipt["response_body_sha256"] = hashlib.sha256(raw).hexdigest()
            if not 200 <= status < 300:
                try:
                    document = strict_search_json(raw.decode("utf-8"))
                except (UnicodeDecodeError, ValueError):
                    document = None
                error = document.get("error") if isinstance(document, dict) else None
                code = error.get("code") if isinstance(error, dict) else None
                if isinstance(code, str) and code in _ERROR_CODES:
                    receipt["provider_error_code"] = code
                if status in (401, 403, 404) or (status == 429 and receipt.get("provider_error_code") in _ERROR_CODES):
                    receipt["outcome"] = "confirmed_failure"
                raise ExternalSearchTransportError(receipt)
            parsed = parse_route(kind, raw, max_layers=self.retrieval["max_json_unwrap_layers"], max_bytes=self.retrieval["max_in_memory_response_bytes"])
            receipt.update(outcome="response_available", parse_status=parsed["status"], provider_result_count=len(parsed["entries"]))
            # Short data only. Raw HTTP bytes exist in memory only for the
            # bounded parse and digest above; they never enter the journal.
            receipt["entries"] = [dict(entry, title=entry["title"][:500], snippet=entry["snippet"][:500], publisher=(entry["publisher"][:500] if isinstance(entry.get("publisher"), str) else None)) for entry in parsed["entries"][:top_k] if len(entry["url"]) <= 2048]
            return receipt
        except ExternalSearchTransportError:
            raise
        except Exception as error:
            receipt["failure_type"] = type(error).__name__
            raise ExternalSearchTransportError(receipt) from None
        finally:
            if response is not None:
                response.close()
