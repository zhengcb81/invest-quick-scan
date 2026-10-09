"""Verify the exact hardened controller validator on owned dummy fixtures."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path

REVIEW_ROOT = Path(os.environ["E97_OWNED_ROOT"]).resolve()
IQS = REVIEW_ROOT.parents[2]
source_path = IQS / "docs/implementation/reviews/G3/jr13-2026-10-09/run_batch.py"
raw = source_path.read_bytes()
(REVIEW_ROOT / "run_batch-frozen-02.py").write_bytes(raw)
module = ast.parse(raw.decode("utf-8"), filename=str(source_path))
node = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "validate_synthetic_config")
function = compile(ast.Module(body=[node], type_ignores=[]), str(source_path), "exec")
base = {"default_provider": "openai", "providers": {"openai": {"enabled": True,
        "api_key": "offline-fixture-key", "model": "actual-fixture-model-B",
        "base_url": "https://api.openai.com/v1/chat/completions", "max_retries": 1, "format_repair_budget": 0}}}
configs = {name: copy.deepcopy(base) for name in ["exact_offline_fixture", "extra_provider_dummy_key", "unregistered_model", "nonfixture_dummy_key", "foreign_base_url", "unexpected_root_field", "bool_retry"]}
configs["extra_provider_dummy_key"]["providers"]["other"] = {"api_key": "dummy-nonfixture-sentinel"}
configs["unregistered_model"]["providers"]["openai"]["model"] = "dummy-unregistered-model"
configs["nonfixture_dummy_key"]["providers"]["openai"]["api_key"] = "dummy-nonfixture-sentinel"
configs["foreign_base_url"]["providers"]["openai"]["base_url"] = "https://dummy.invalid/no-request"
configs["unexpected_root_field"]["extra"] = "dummy"
configs["bool_retry"]["providers"]["openai"]["max_retries"] = True
outcomes = {}
for name, value in configs.items():
    own = REVIEW_ROOT / "controller-recheck-02" / name
    config = own / "fixture" / "llm_apis.json"
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps(value), encoding="utf-8")
    scope = {"OWN": own, "Path": Path, "json": json, "hashlib": hashlib}
    exec(function, scope)
    try:
        receipt = scope["validate_synthetic_config"](str(config))
        outcomes[name] = {"accepted_as_synthetic": True, "receipt": receipt}
    except AssertionError:
        outcomes[name] = {"accepted_as_synthetic": False}
    assert outcomes[name]["accepted_as_synthetic"] == (name == "exact_offline_fixture"), name
record = {"controller_sha256": hashlib.sha256(raw).hexdigest(), "exact_frozen_validator_AST_executed": True,
          "outcomes": outcomes, "only_dummy_offline_credentials_created": True, "real_API_calls": 0,
          "network_attempts": 0, "rejects_extra_provider_and_nonfixture_key": True}
network = REVIEW_ROOT / "network-attempts.jsonl"
assert not network.exists() or not network.read_bytes()
(REVIEW_ROOT / "controller-results-02.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record, ensure_ascii=False))
