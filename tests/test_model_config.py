import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import model_config  # noqa: E402


def test_minimax_model_is_canonical_and_single_sourced():
    assert model_config.get("minimax")["model"] == "MiniMax-M3.1-Flash"
    for path in (
        ROOT / "scripts/thin_scan.py",
        ROOT / "scripts/batching_benchmark.py",
        ROOT / "scripts/batching_benchmark_report.py",
        ROOT / "scripts/accuracy_pilot.py",
    ):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"MiniMax-M3(?!\.1-Flash)", text), path.name


def test_routes_preserve_existing_models_and_rates():
    routes = model_config.routes()
    assert set(routes) == {"minimax", "mimo", "mimo_pro", "deepseek"}
    assert routes["deepseek"]["model"] == "deepseek-flash"
    assert routes["deepseek"]["endpoint"] == "https://api.deepseek.com/chat/completions"
    assert routes["minimax"]["key_env"] == "MINIMAX_API_KEY"
    assert routes["minimax"]["input_rate"] == 0.6
    assert routes["mimo_pro"]["model"] == "mimo-v2.6-pro"


def test_provider_profiles_match_the_model_config():
    profiles = json.loads((ROOT / "examples/provider-connectivity-profiles.json").read_text(encoding="utf-8"))
    minimax = [p for p in profiles["profiles"] if p["provider"] == "minimax"]
    assert minimax
    expected = model_config.get("minimax")["model"]
    assert {p["model"] for p in minimax} == {expected}


def test_unknown_model_id_is_rejected():
    try:
        model_config.get("does-not-exist")
    except KeyError as error:
        assert "unknown model id" in str(error)
    else:
        raise AssertionError("unknown model id was accepted")


def test_batching_routes_are_loaded_from_the_config():
    import batching_benchmark
    assert batching_benchmark.ROUTES == model_config.routes()


def test_search_entries_expose_key_env_like_routes_do():
    """RED regression: config/models.json stores `api_key_env`, but consumers read `key_env`.

    model_config.routes() maps the field; search() must map it too, otherwise
    thin_scan.py's search() raises KeyError('key_env') before any request is made.
    """
    providers = model_config.search()
    assert providers, "config must declare at least one search provider"
    for provider in providers:
        assert "key_env" in provider, f"search provider {provider.get('id')} lacks key_env"
        assert "api_key_env" not in provider, "consumers read key_env; do not leak the raw field"
        assert provider["key_env"], "key_env must not be empty"
        assert provider["endpoint"].startswith("https://")


def test_thin_scan_consumes_the_mapped_search_provider():
    """The real failure: thin_scan took search()[0] and indexed ['key_env']."""
    import thin_scan

    provider = model_config.search()[0]
    # Every key thin_scan reads off the provider must be present.
    for field in ("key_env", "endpoint", "cost_micros"):
        assert field in provider, f"thin_scan needs {field} on the search provider"
    assert hasattr(thin_scan, "search"), "thin_scan must keep its search entrypoint"
    # The scan must not resolve credentials through the raw config field name.
    source = (ROOT / "scripts/thin_scan.py").read_text(encoding="utf-8")
    assert 'provider["api_key_env"]' not in source
