"""W15: public IQS bundle validation over real offline producer artifacts.

Companies/evidence are synthetic; no identity or financial golden claim.
"""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from unittest.mock import patch

import pytest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import module_contract as mc
import question_sets as qs
import routing
import route_store_handoff as handoff

NOW = "2026-10-09T12:00:00Z"


@pytest.fixture
def bundle(tmp_path):
    root = tmp_path / "iqs"
    shutil.copytree(ROOT / "questions", root / "questions", ignore=shutil.ignore_patterns("releases"))
    for ref in ("schemas/answer-content.schema.json", "schemas/quick_scan/metric.schema.json",
                "schemas/quick_scan/score.schema.json", "schemas/observation.schema.json",
                "schemas/quick_scan/module-legacy-baseline.json"):
        dest = root / ref
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / ref, dest)
    package = routing.publish_routing_package(root=root, renderer_version=qs.RENDERER_VERSION,
                                            renderer_rules_sha256=qs.renderer_rules_sha256())
    identity = dict(entity_id="ENT_W15_SYNTHETIC", identity_ref="fixture:w15:identity",
                    company="Fictional W15 company", ticker="TEST", exchange="TEST",
                    security_id=None, as_of="2026-10-08", verified_facts=[])
    route = routing.resolve_route_decision(identity, package_id=package["package_id"],
                                          now_utc=NOW, root=root)
    run = root / "run"
    with patch.object(qs, "ROOT", root):
        qs.compose_from_route(route, run, now_utc=NOW, expected_route_decision_id=route["decision_id"])
    route_file = run / "route.json"
    route_file.write_bytes(json.dumps(route, ensure_ascii=False, indent=2).encode("utf-8") + b"\r\n")
    return root, route_file, run / "manifest.json", route


def validate(bundle, **kwargs):
    root, route_file, manifest_file, route = bundle
    return handoff.validate_route_bundle(route_file, manifest_file, root=root,
                                        expected_decision_id=kwargs.pop("expected_decision_id", route["decision_id"]),
                                        **kwargs)


def test_actual_producer_bundle_binds_raw_bytes_without_company_score(bundle):
    root, route_file, manifest_file, route = bundle
    before = route_file.read_bytes(), manifest_file.read_bytes()
    result = validate(bundle)
    assert result["protocol"] == "iqs.route_store_validation/1.0.0"
    assert result["validation_mode"] == "history"
    assert result["expected_decision_id"] == route["decision_id"]
    assert result["route_raw_sha256"] == hashlib.sha256(before[0]).hexdigest()
    assert result["manifest_raw_sha256"] == hashlib.sha256(before[1]).hexdigest()
    assert result["question_count"] == 24
    assert result["new_execution_authorized"] is False
    assert result["source_authentication"] == "caller_owned_anchor_and_trusted_validator_transport_required"
    assert "score" not in result
    assert (route_file.read_bytes(), manifest_file.read_bytes()) == before
    assert result["classification_confidence"] == route["classification_confidence"]
    Draft202012Validator(handoff.DTO_SCHEMA, format_checker=FormatChecker()).validate(result)


def test_current_execution_is_explicit_and_requires_trusted_time(bundle):
    with pytest.raises(handoff.RouteBundleError) as err:
        validate(bundle, validation_mode="execution")
    assert err.value.code == "execution_time_required"
    result = validate(bundle, validation_mode="execution", now_utc=NOW)
    assert result["new_execution_authorized"] is True
    assert result["execution_checked_at"] == NOW


def test_resealed_route_cannot_supply_its_own_expected_anchor(bundle):
    _, route_file, _, route = bundle
    changed = copy.deepcopy(route)
    changed["profile_context"]["company"] = "Different fictional company"
    route_file.write_bytes(mc.canonical_bytes(mc.seal_route_decision(changed)))
    with pytest.raises(handoff.RouteBundleError) as err:
        validate(bundle)
    assert err.value.code == "route_anchor_mismatch"


def test_missing_anchor_does_not_default_from_input(bundle):
    with pytest.raises(handoff.RouteBundleError) as err:
        validate(bundle, expected_decision_id=None)
    assert err.value.code == "independent_anchor_required"


def test_legacy_route_schema_is_explicitly_unsupported(bundle):
    _, route_file, _, route = bundle
    route["schema_version"] = "1.0.0"
    route_file.write_bytes(mc.canonical_bytes(route))
    with pytest.raises(handoff.RouteBundleError) as err:
        validate(bundle)
    assert err.value.code == "route_schema_unsupported"


def test_manifest_cannot_hide_absence_of_released_metric_validation(bundle):
    _, _, manifest_file, _ = bundle
    document = json.loads(manifest_file.read_bytes())
    del document["metric_contract_version"]
    manifest_file.write_bytes(mc.canonical_bytes(document))
    with pytest.raises(handoff.RouteBundleError) as err:
        validate(bundle)
    assert err.value.code == "published_manifest_required"


def test_manifest_cannot_rebind_to_another_route(bundle):
    _, _, manifest_file, _ = bundle
    document = json.loads(manifest_file.read_bytes())
    document["route_decision"]["profile_context"]["company"] = "Another fictional company"
    manifest_file.write_bytes(mc.canonical_bytes(document))
    with pytest.raises(handoff.RouteBundleError) as err:
        validate(bundle)
    assert err.value.code == "route_manifest_binding_mismatch"


def test_corrupt_release_is_not_replaced_by_current_catalog(bundle):
    root, _, _, _ = bundle
    document = json.loads(bundle[2].read_bytes())
    archive = root / document["module_locks"][0]["artifact_ref"]
    archive.write_bytes(archive.read_bytes() + b" ")
    with pytest.raises(handoff.RouteBundleError) as err:
        validate(bundle)
    assert err.value.code == "route_invalid"


def test_execution_time_before_decision_is_named_refusal(bundle):
    with pytest.raises(handoff.RouteBundleError) as err:
        validate(bundle, validation_mode="execution", now_utc="2026-10-08T12:00:00Z")
    assert err.value.code == "route_execution_invalid"


def test_route_manifest_binding_and_prompt_resealing_fail_closed(bundle):
    _, _, manifest_file, _ = bundle
    document = json.loads(manifest_file.read_bytes())
    document["questions"][0]["prompt"] += " Changed economics."
    document["questions"][0]["prompt_sha256"] = hashlib.sha256(document["questions"][0]["prompt"].encode()).hexdigest()
    manifest_file.write_bytes(mc.canonical_bytes(document))
    with pytest.raises(handoff.RouteBundleError) as err:
        validate(bundle)
    assert err.value.code == "manifest_invalid"


def test_edited_current_catalog_does_not_reinterpret_frozen_release(bundle):
    root, _, _, _ = bundle
    catalog_path = root / "questions/catalog.json"
    catalog = json.loads(catalog_path.read_bytes())
    catalog["version"] = "99.0.0"
    catalog_path.write_bytes(mc.canonical_bytes(catalog))
    assert validate(bundle)["question_count"] == 24


@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}', b'{"a":{"b":1,"b":2}}',
                                   b'{"a":NaN}', b'{"a":1e400}', b'[]', b'not json'])
def test_malformed_raw_route_is_rejected_before_persistence(bundle, raw):
    bundle[1].write_bytes(raw)
    with pytest.raises(handoff.RouteBundleError) as err:
        validate(bundle)
    assert err.value.code == "route_json_invalid"


def test_real_cli_produces_json_and_named_refusal(bundle):
    root, route_file, manifest_file, route = bundle
    command = [sys.executable, "-B", "-X", "utf8", str(ROOT / "scripts/route_store_handoff.py"),
               "--root", str(root), "--route", str(route_file), "--manifest", str(manifest_file),
               "--expected-decision-id", route["decision_id"]]
    success = subprocess.run(command, capture_output=True, timeout=30)
    (root / "cli-success.stdout.json").write_bytes(success.stdout)
    (root / "cli-success.stderr.log").write_bytes(success.stderr)
    assert success.returncode == 0, success.stderr.decode("utf-8", errors="replace")
    assert json.loads(success.stdout)["status"] == "validated"
    rejected = subprocess.run(command[:-1] + ["route_" + "f" * 64], capture_output=True, timeout=30)
    (root / "cli-rejected.stdout.json").write_bytes(rejected.stdout)
    (root / "cli-rejected.stderr.log").write_bytes(rejected.stderr)
    assert rejected.returncode == 2
    assert json.loads(rejected.stdout)["error_code"] == "route_anchor_mismatch"
    assert b"Traceback" not in rejected.stderr
