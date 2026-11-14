"""Public model invocation service, independent of the thin-scan CLI."""
from __future__ import annotations

import json
import os

from .provider_transport import post_json

API_PROTOCOL = "iqs.model-invocation-api/1.0.0"
PUBLIC_API_EXPORTS = frozenset({
    "API_PROTOCOL", "PUBLIC_API_EXPORTS", "ask_model",
})


def ask_model(provider: dict, prompt: str, max_tokens: int = 1200, *, transport=None) -> dict:
    key = os.environ.get(provider["key_env"], "")
    body = {"model": provider["model"], "messages": [{"role": "user", "content": prompt}],
            "temperature": 0, "max_tokens": max_tokens}
    status, payload = (transport or post_json)(provider["endpoint"], key, body, 90)
    if status == 0:
        marker = (payload or {}).get("error") if isinstance(payload, dict) else None
        return {"error": "model_timeout" if marker == "timeout" else "model_transport_error"}
    if status != 200 or not isinstance(payload, dict):
        return {"error": f"model_http_{status}"}
    choices = payload.get("choices") or []
    if not choices:
        return {"error": "model_no_choice"}
    choice = choices[0] or {}
    text = ((choice.get("message") or {}).get("content")) or ""
    if not text.strip() and choice.get("finish_reason") == "length":
        return {"error": "model_truncated_no_content"}
    try:
        answer, _ = json.JSONDecoder().raw_decode(text.strip())
    except ValueError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            return {"error": "model_not_json"}
        try:
            answer = json.loads(text[start:end + 1])
        except ValueError:
            return {"error": "model_not_json"}
    usage = payload.get("usage") or {}
    answer["_usage"] = {
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
    }
    return answer
