"""Load the single IQS model/provider configuration."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/models.json"


def load(path: Path | None = None) -> dict:
    document = json.loads((path or CONFIG).read_text(encoding="utf-8-sig"))
    models = document.get("models")
    search = document.get("search")
    if not isinstance(models, list) or not models:
        raise ValueError("model config has no models")
    if not isinstance(search, list) or not search:
        raise ValueError("model config has no search providers")
    ids = [m["id"] for m in models]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate model id")
    return document


def models() -> list[dict]:
    return sorted(load()["models"], key=lambda m: m.get("priority", 999))


def search() -> list[dict]:
    return sorted(load()["search"], key=lambda s: s.get("priority", 999))


def get(model_id: str) -> dict:
    for item in load()["models"]:
        if item["id"] == model_id:
            return item
    raise KeyError("unknown model id: " + model_id)


def routes() -> dict:
    return {
        item["id"]: {
            "model": item["model"],
            "key_env": item["api_key_env"],
            "endpoint": item["endpoint"],
            "input_rate": item["input_rate"],
            "output_rate": item["output_rate"],
            "cache_rate": item["cache_rate"],
        }
        for item in models()
    }
