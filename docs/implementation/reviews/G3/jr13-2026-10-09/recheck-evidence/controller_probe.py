"""Execute the frozen controller's exact config predicate on fake credentials."""
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
(REVIEW_ROOT / "run_batch-before-hardening.py").write_bytes(raw)
module = ast.parse(raw.decode("utf-8"), filename=str(source_path))
main = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "main")
def assigned_name(node):
    return node.targets[0].id if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) else None
start = next(index for index, node in enumerate(main.body) if assigned_name(node) == "synthetic")
end = next(index for index, node in enumerate(main.body) if assigned_name(node) == "network")
block = ast.Module(body=main.body[start:end], type_ignores=[])
predicate = compile(block, str(source_path), "exec")

base = {"default_provider": "openai", "providers": {"openai": {"enabled": True,
        "api_key": "offline-fixture-key", "model": "actual-fixture-model-B",
        "base_url": "https://api.openai.com/v1/chat/completions", "max_retries": 1, "format_repair_budget": 0}}}
configs = {"exact_offline_fixture": copy.deepcopy(base), "extra_provider_dummy_key": copy.deepcopy(base), "unregistered_model": copy.deepcopy(base)}
configs["extra_provider_dummy_key"]["providers"]["other"] = {"api_key": "dummy-nonfixture-sentinel", "model": "dummy-unregistered-model"}
configs["unregistered_model"]["providers"]["openai"]["model"] = "dummy-unregistered-model"
outcomes = {}
for name, value in configs.items():
    own = REVIEW_ROOT / "controller-negative" / name
    config = own / "fixture" / "llm_apis.json"
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps(value), encoding="utf-8")
    (own / "key-opens.jsonl").write_text(str(config) + "\n", encoding="utf-8")
    destination = own / "out"
    destination.mkdir()
    scope = {"OWN": own, "destination": destination, "Path": Path, "json": json, "hashlib": hashlib}
    try:
        exec(predicate, scope)
        outcomes[name] = {"accepted_as_synthetic": True, "synthetic_config_reads": scope["synthetic"]}
    except AssertionError as exc:
        outcomes[name] = {"accepted_as_synthetic": False, "exception": str(exc)}

record = {"source_controller_sha256": hashlib.sha256(raw).hexdigest(), "exact_source_AST_slice_executed": True,
          "only_dummy_offline_credentials_created": True, "real_API_calls": 0, "network_attempts": 0,
          "outcomes": outcomes}
(REVIEW_ROOT / "controller-results.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record, ensure_ascii=False))
