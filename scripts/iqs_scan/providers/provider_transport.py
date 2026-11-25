"""Small JSON HTTP transport shared by model and search adapters."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from hashlib import sha256
from http.client import HTTPException
import json
import urllib.error
import urllib.request

from ..foundation.api import record_operation_failure

API_PROTOCOL = "iqs.provider-json-transport-api/1.0.0"
PUBLIC_API_EXPORTS = frozenset({
    "API_PROTOCOL", "PUBLIC_API_EXPORTS", "post_json", "provider_question_scope",
})
_QUESTION = ContextVar("iqs_provider_question", default=None)


@contextmanager
def provider_question_scope(question_id: str):
    """Group same-question retries by a native identifier, without storing its text."""
    reference = "question-" + sha256(str(question_id).encode("utf-8")).hexdigest()
    token = _QUESTION.set(reference)
    try:
        yield
    finally:
        _QUESTION.reset(token)


def _failure(error: BaseException, code: str, marker: str, *, status: int = 0) -> tuple[int, dict]:
    # Each question owns its occurrence. The issue still groups common causes.
    stage = "provider.http/" + code.removeprefix("provider_")
    record_operation_failure(error, stage, code=code, substep=_QUESTION.get())
    return status, {"error": marker}


def post_json(url: str, key: str, body: dict, timeout: float) -> tuple[int, dict]:
    """POST JSON and return a status/payload pair for every transport outcome."""
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    try:
        request = urllib.request.Request(url, data=data, method="POST", headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
        })
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        # The HTTP status is the public failure fact. Do not read or return the
        # provider's error body, which may repeat credentials or request text.
        try:
            error.close()
        except OSError:
            pass  # The original HTTP failure remains authoritative.
        return _failure(error, f"provider_http_{error.code}", "http_error", status=error.code)
    except TimeoutError as error:
        return _failure(error, "provider_transport_timeout", "timeout")
    except urllib.error.URLError as error:
        reason = error.reason
        if isinstance(reason, TimeoutError):
            return _failure(reason, "provider_transport_timeout", "timeout")
        cause = reason if isinstance(reason, BaseException) else error
        return _failure(cause, "provider_transport_error", "transport")
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        return _failure(error, "provider_invalid_response", "transport")
    except (OSError, ValueError, HTTPException) as error:
        return _failure(error, "provider_transport_error", "transport")
