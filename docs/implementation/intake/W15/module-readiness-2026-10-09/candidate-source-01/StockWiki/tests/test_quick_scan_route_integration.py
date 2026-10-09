"""Actual IQS CLI + SQLite + native backup; inputs are synthetic, not owner golden."""

import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from test_quick_scan_routes import _workspace

from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_analysis import receipt_key
from stockwiki.quick_scan_backup import create_backup, restore_backup, verify_backup
from stockwiki.quick_scan_route_validation import IqsRouteValidator
from stockwiki.quick_scan_routes import QuickScanRouteStore
from stockwiki.quick_scan_store import QuickScanStore

NOW = "2026-10-09T12:00:00Z"


@pytest.fixture
def actual_bundle(tmp_path):
    code_root = Path(os.environ["IQS_ROUTE_TEST_CODE_ROOT"])
    helper = (
        code_root / "docs/implementation/reviews/W15/module-readiness-2026-10-09/produce_bundle.py"
    )
    identity, subject = _workspace(tmp_path / "workspace")
    validator = IqsRouteValidator(
        code_root,
        runs_dir=identity.paths.runs_dir,
        release_root=tmp_path / "release",
        process_env=dict(os.environ),
    )
    routes = QuickScanRouteStore(identity, validator=validator)
    binding = routes.identity_binding(receipt_key(subject))
    request = {
        "root": str(tmp_path / "release"),
        "now": NOW,
        "identity": {
            "entity_id": subject["primary_issuer_id"],
            "identity_ref": binding["route_identity_ref"],
            "company": "Synthetic W15 company",
            "ticker": "TEST",
            "exchange": "TEST",
            "security_id": None,
            "as_of": "2026-10-08",
            "verified_facts": [],
        },
    }
    request_file = tmp_path / "request.json"
    request_file.write_text(json.dumps(request), encoding="utf-8")
    producer_env = dict(os.environ, IQS_ROUTE_TEST_OWNED_ROOT=str(tmp_path))
    produced = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", str(helper), str(request_file)],
        capture_output=True,
        timeout=60,
        check=False,
        env=producer_env,
    )
    (tmp_path / "producer.stdout.log").write_bytes(produced.stdout)
    (tmp_path / "producer.stderr.log").write_bytes(produced.stderr)
    assert produced.returncode == 0, produced.stderr.decode("utf-8", errors="replace")
    raw = (tmp_path / "release/run/route.json").read_bytes()
    manifest = (tmp_path / "release/run/manifest.json").read_bytes()
    decision_id = json.loads(raw)["decision_id"]
    return routes, subject, raw, manifest, decision_id, validator


def test_actual_public_cli_validate_store_activate_and_refuse_resealed_route(actual_bundle):
    routes, subject, raw, manifest, decision_id, validator = actual_bundle
    got = routes.record_snapshot(
        raw, manifest, subject_key=receipt_key(subject), expected_decision_id=decision_id
    )
    assert got["status"] == "recorded"
    routes.set_current(
        decision_id,
        subject_key=receipt_key(subject),
        expected_current_decision_id=None,
        now_utc=NOW,
    )
    execution = routes.get_for_execution(
        subject_key=receipt_key(subject),
        scope="entity",
        scope_id=subject["primary_issuer_id"],
        now_utc=NOW,
    )
    assert execution["execution_validation"]["question_count"] == 24
    assert execution["snapshot"]["route_raw"] == raw
    assert list(validator.runs_dir.iterdir()) == []
    changed = copy.deepcopy(json.loads(raw))
    changed["decision_id"] = "route_" + "e" * 64
    with pytest.raises(ValueError, match="route_anchor_mismatch"):
        routes.get_for_execution(
            subject_key=receipt_key(subject),
            scope="entity",
            scope_id=subject["primary_issuer_id"],
            now_utc=NOW,
            candidate_route=json.dumps(changed).encode(),
        )
    with pytest.raises(ValueError, match="manifest_invalid"):
        altered = json.loads(manifest)
        altered["questions"][0]["prompt"] += " tampered"
        validator.validate(raw, json.dumps(altered).encode(), expected_decision_id=decision_id)
    assert list(validator.runs_dir.iterdir()) == []


def test_schema6_native_backup_and_restore_keep_raw_routes_and_anchor(actual_bundle, tmp_path):
    routes, subject, raw, manifest, decision_id, validator = actual_bundle
    routes.record_snapshot(
        raw, manifest, subject_key=receipt_key(subject), expected_decision_id=decision_id
    )
    routes.set_current(
        decision_id,
        subject_key=receipt_key(subject),
        expected_current_decision_id=None,
        now_utc=NOW,
    )
    report = create_backup(routes.identity.paths, name="w15-roundtrip")
    assert verify_backup(routes.identity.paths, "w15-roundtrip")["ok"] is True
    target = WorkspacePaths.from_root(tmp_path / "restored")
    shutil.copytree(report.backup_dir, target.root / "backups/quick_scan/w15-roundtrip")
    restored = restore_backup(target, "w15-roundtrip")
    assert restored["executor_side"]["paid_dispatch_restored"] is False
    owner = QuickScanRouteStore(QuickScanStore(target), validator=validator)
    execution = owner.get_for_execution(
        subject_key=receipt_key(subject),
        scope="entity",
        scope_id=subject["primary_issuer_id"],
        now_utc=NOW,
    )
    assert (
        execution["snapshot"]["route_raw"] == raw
        and execution["snapshot"]["manifest_raw"] == manifest
    )
    assert execution["expected_decision_id"] == decision_id


def test_stockwiki_public_os_cli_binding_import_activate_read_and_refresh(actual_bundle, tmp_path):
    routes, subject, raw, manifest, decision_id, validator = actual_bundle
    common = [
        sys.executable,
        "-B",
        "-X",
        "utf8",
        "-m",
        "stockwiki.cli",
        "--root",
        str(routes.identity.paths.root),
    ]
    flags = [
        "--subject-key",
        receipt_key(subject),
        "--iqs-code-root",
        str(validator.code_root),
        "--iqs-release-root",
        str(validator.release_root),
    ]

    def cli(action, extra, expected=0):
        result = subprocess.run(
            common + ["quick-scan-route-" + action] + flags + extra,
            capture_output=True,
            timeout=90,
            check=False,
        )
        (tmp_path / (action + ".stdout.log")).write_bytes(result.stdout)
        (tmp_path / (action + ".stderr.log")).write_bytes(result.stderr)
        assert result.returncode == expected, result.stderr.decode("utf-8", errors="replace")
        value = json.loads(result.stdout)
        from jsonschema import Draft202012Validator, FormatChecker
        from referencing import Registry, Resource

        resources = []
        for name in (
            "route-store-cli.schema.json",
            "module-refresh.schema.json",
            "route-store-validation.schema.json",
        ):
            schema = json.loads((validator.code_root / "schemas/quick_scan" / name).read_bytes())
            resources.append((schema["$id"], Resource.from_contents(schema)))
        Draft202012Validator(
            resources[0][1].contents,
            registry=Registry().with_resources(resources),
            format_checker=FormatChecker(),
        ).validate(value)
        return value

    binding = cli("binding", [])
    assert binding["payload"]["route_identity_ref"] == json.loads(raw)["identity_ref"]
    route_path, manifest_path = (
        tmp_path / "incoming-route.json",
        tmp_path / "incoming-manifest.json",
    )
    route_path.write_bytes(raw)
    manifest_path.write_bytes(manifest)
    assert (
        cli(
            "record",
            [
                "--route",
                str(route_path),
                "--manifest",
                str(manifest_path),
                "--expected-decision-id",
                decision_id,
            ],
        )["payload"]["status"]
        == "recorded"
    )
    cli(
        "activate", ["--expected-decision-id", decision_id, "--expect-no-current", "--now-utc", NOW]
    )
    key = ["--scope", "entity", "--scope-id", subject["primary_issuer_id"]]
    current = cli("current", key + ["--now-utc", NOW, "--include-raw-bundle"])
    import base64

    assert base64.b64decode(current["payload"]["snapshot"]["route_raw_base64"]) == raw
    assert current["payload"]["expected_decision_id"] == decision_id
    refresh = cli(
        "refresh",
        key + ["--now-utc", NOW, "--provider", "P1", "--model", "M1", "--ttl-hours", "120"],
    )
    assert refresh["payload"]["totals"]["fields"] == 24
    assert refresh["payload"]["totals"]["planned_dispatches"] == 21
    assert refresh["payload"]["totals"]["deferred_scope_unbound"] == 3
    assert {
        row["field_id"]
        for row in refresh["payload"]["fields"]
        if row["decision"] == "deferred_scope_unbound"
    } == {q["id"] for q in json.loads(manifest)["questions"] if q["scope"] == "security"}
    assert refresh["paid_dispatch_started"] is False and refresh["c06_envelope_validated"] is False
    assert (
        cli("history", key)["payload"]["snapshots"][0]["route_raw_sha256"]
        == current["payload"]["snapshot"]["route_raw_sha256"]
    )
    assert (
        cli(
            "activate",
            ["--expected-decision-id", decision_id, "--expect-no-current", "--now-utc", NOW],
            expected=2,
        )["error_code"]
        == "route_current_conflict"
    )
