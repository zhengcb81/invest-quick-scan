"""I5 current-source integration through the StockWiki public CLI.

The owner database is seeded with synthetic facts by StockWiki's existing C06
fixtures. Theme and Industry consume the same isolated database through their
published clients; no consumer imports StockWiki implementation modules.

Run with IQS_C06_RUN_INTEGRATION=1 and IQS_C06_OWN pointing at the owned C06
fixture root. The fixture root supplies the small, approved IQS query contract
copy expected by StockWiki's integration helper.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*") if path.is_file()
    }


def test_theme_and_industry_consume_one_isolated_stockwiki_snapshot(tmp_path, monkeypatch):
    if os.environ.get("IQS_C06_RUN_INTEGRATION") != "1" or not os.environ.get("IQS_C06_OWN"):
        pytest.skip("I5 needs the explicit owned C06 fixture runtime")

    stockwiki_root = Path(os.environ.get("IQS_STOCKWIKI_ROOT", ROOT.parent / "StockWiki")).resolve()
    theme_root = Path(os.environ.get("IQS_THEME_ROOT", ROOT.parent / "analyze-theme-value-chain")).resolve()
    industry_root = Path(os.environ.get("IQS_INDUSTRY_ROOT", ROOT.parent / "industry-research")).resolve()
    fixture_root = Path(os.environ["IQS_C06_OWN"]).resolve()
    fixture_iqs_root = fixture_root / "iqs"
    iqs_code_root = ROOT
    required = (
        stockwiki_root / "stockwiki" / "quick_scan_query_v2_cli.py",
        stockwiki_root / "tests" / "test_c06_facts_query.py",
        fixture_iqs_root / "tests" / "test_query_contract_v2.py",
        theme_root / "scripts" / "quick_scan_client.py",
        industry_root / "tools" / "quick_scan_client.py",
    )
    missing = [str(path) for path in required if not path.is_file()]
    assert not missing, f"I5 source/runtime inputs missing: {missing}"

    # Ensure every spawned owner process is local-only and cannot inherit a
    # provider credential from the interactive shell.
    for name in tuple(os.environ):
        if any(secret_marker in name.upper() for secret_marker in ("API_KEY", "TOKEN", "SECRET", "PASSWORD")):
            monkeypatch.delenv(name, raising=False)

    for path in (
        stockwiki_root,
        stockwiki_root / "tests",
        fixture_iqs_root / "scripts",
        iqs_code_root / "scripts",
        theme_root / "scripts",
        industry_root,
        industry_root / "tools",
    ):
        monkeypatch.syspath_prepend(str(path))
    extra_pythonpath = os.pathsep.join(str(path) for path in (
        stockwiki_root, stockwiki_root / "tests", fixture_iqs_root / "scripts",
        iqs_code_root / "scripts",
        theme_root / "scripts", industry_root, industry_root / "tools",
    ))
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    monkeypatch.setenv("PYTHONPATH", extra_pythonpath + (os.pathsep + existing_pythonpath if existing_pythonpath else ""))

    # Reuse StockWiki's real storage fixture and serializers. Its synthetic
    # positive and review/period edge cases provide enough rows to exercise
    # actual consumer pagination without inventing production-shaped facts.
    owner_fixture = importlib.import_module("test_c06_facts_query")
    paths, _store, _service, _refs, _attempts = owner_fixture.facts_owner(tmp_path / "seed", monkeypatch)
    owner_root = Path(paths.root).resolve()
    owner_before = _tree_hashes(owner_root)

    theme = _load_module("iqs_i5_theme_quick_scan_client", theme_root / "scripts" / "quick_scan_client.py")
    industry = _load_module("iqs_i5_industry_quick_scan_client", industry_root / "tools" / "quick_scan_client.py")
    subjects = {"subjects": [
        {
            "subject_id": f"SYNTHETIC_I5_{key.upper()}",
            "entity_id": entity_id,
            "display_name": display_name,
            "listing_ids": [],
            "markets": [],
        }
        for key, (entity_id, display_name) in owner_fixture.ENTITIES.items()
    ]}
    entity_ids = [entity_id for entity_id, _name in owner_fixture.ENTITIES.values()]
    fields = ["facts.customers"]
    common = {
        "entity_ids": entity_ids,
        "field_ids": fields,
        "mode": "explore",
        "information_cutoff": "2026-10-09",
        "relation_types": ["sells_to"],
        "direction": "outgoing",
        "evidence": "require_resolved",
        "page_size": 1,
    }

    theme_output = tmp_path / "theme-output"
    theme_capture = tmp_path / "theme-capture"
    theme_transport = theme.OwnerCliTransport(
        owner_root,
        iqs_code_root,
        python_executable=sys.executable,
        timeout_seconds=45,
        capture_root=theme_capture,
    )
    theme_capabilities = theme.check_capabilities(theme_transport, "1.2.0")
    assert theme_capabilities["verdict"] == "supported", theme_capabilities
    theme_request = theme.build_request(
        subjects,
        operation="query_facts",
        mode="explore",
        field_ids=fields,
        information_cutoff="2026-10-09",
        relation_types=["sells_to"],
        direction="outgoing",
        page_size=1,
    )
    theme_first = theme.run_query(
        subjects, theme_request, transport=theme_transport, output_dir=theme_output / "page-1"
    )
    assert theme_first["disposition"] == "facts_present", theme_first
    assert theme_first["row_count"] == 1
    theme_first_report = json.loads(Path(theme_first["artifacts"]["report_json"]).read_text(encoding="utf-8"))
    theme_snapshot = theme_first_report["provenance"]["snapshot_id"]
    theme_cursor = theme_first_report["next_cursor"]
    assert theme_snapshot and theme_cursor

    # A newly constructed transport resumes a cursor from the consumer-owned
    # snapshot store, proving re-open/replay across independent client objects.
    theme_reopened = theme.OwnerCliTransport(
        owner_root,
        iqs_code_root,
        python_executable=sys.executable,
        timeout_seconds=45,
        capture_root=theme_capture,
    )
    theme_page_two_request = theme.build_request(
        subjects,
        operation="query_facts",
        mode="explore",
        field_ids=fields,
        information_cutoff="2026-10-09",
        relation_types=["sells_to"],
        direction="outgoing",
        page_size=1,
        cursor=theme_cursor,
        snapshot_id=theme_snapshot,
    )
    theme_page_two = theme.run_query(
        subjects, theme_page_two_request, transport=theme_reopened, output_dir=theme_output / "page-2"
    )
    assert theme_page_two["disposition"] == "facts_present", theme_page_two
    assert theme_page_two["row_count"] == 1
    theme_second_report = json.loads(Path(theme_page_two["artifacts"]["report_json"]).read_text(encoding="utf-8"))
    assert theme_second_report["provenance"]["snapshot_id"] == theme_snapshot

    theme_export_request = theme.build_request(
        subjects,
        operation="export_facts",
        mode="explore",
        field_ids=fields,
        information_cutoff="2026-10-09",
        relation_types=["sells_to"],
        direction="outgoing",
        label="I5 synthetic theme export",
    )
    theme_export = theme.run_query(
        subjects, theme_export_request, transport=theme_reopened, output_dir=theme_output / "export"
    )
    assert theme_export["disposition"] == "facts_present", theme_export
    theme_export_report = json.loads(Path(theme_export["artifacts"]["report_json"]).read_text(encoding="utf-8"))
    assert len(theme_export_report["export"]["candidates"]) >= 2

    industry_config = {
        "owner_root": str(owner_root),
        "iqs_code_root": str(iqs_code_root),
        "capture_root": str(tmp_path / "industry-capture"),
        "python_executable": sys.executable,
        "timeout_seconds": 45,
        # StockWiki's get_profiles profile wire validates this canonical
        # consumer ID; using a test-only suffix here makes the owner's strict
        # request contract reject an otherwise valid Industry Research call.
        "consumer_id": "industry-research",
        "page_size": 1,
        "max_pages": 10,
    }
    industry_client = industry.QuickScanClient(industry_config)
    industry_capabilities = industry_client.capabilities()
    assert industry_capabilities["status"] == "ready", industry_capabilities
    industry_first = industry_client.collect_all_pages(**common)
    assert industry_first["status"] in {"ok", "partial"}, json.dumps(industry_first, ensure_ascii=False, indent=2)
    assert industry_first["total"] >= 2
    assert len(industry_first["pages"]) >= 2
    assert len(industry_first["facts"]) >= 2
    industry_snapshot = industry_first["snapshot_id"]
    assert industry_snapshot
    assert {
        page["response"]["result"]["watermark"]["snapshot_id"]
        for page in industry_first["pages"]
    } == {industry_snapshot}

    # New consumer instance reopens the existing pinned capture and returns
    # the same rows without changing the owner workspace.
    industry_reopened = industry.QuickScanClient(industry_config)
    industry_replay = industry_reopened.collect_all_pages(**common, snapshot_id=industry_snapshot)
    assert industry_replay["status"] == industry_first["status"]
    assert industry_replay["snapshot_id"] == industry_snapshot
    assert [row["fact_id"] for row in industry_replay["facts"]] == [
        row["fact_id"] for row in industry_first["facts"]
    ]

    industry_export = industry_reopened.export_facts(
        entity_ids=entity_ids,
        field_ids=fields,
        mode="explore",
        information_cutoff="2026-10-09",
        relation_types=["sells_to"],
        direction="outgoing",
        evidence="require_resolved",
        label="I5 synthetic industry export",
    )
    assert industry_export["status"] == "ok", industry_export
    industry_export_body = industry_export["response"]["result"]["export"]
    assert len(industry_export_body["candidates"]) >= 2

    # Identity and operation failures must travel through the same public
    # consumer adapter and owner CLI as the successful query above. Neither
    # may be translated into an empty result or leave an owner-side capture.
    wrong_identity_client = industry.QuickScanClient({
        **industry_config,
        "consumer_id": "industry-research-i5-test",
        "capture_root": str(tmp_path / "industry-wrong-identity-capture"),
    })
    wrong_identity = wrong_identity_client.collect_all_pages(**common)
    assert wrong_identity["status"] == "unavailable", wrong_identity
    assert wrong_identity["error_code"] == "subject_contract_output_invalid", wrong_identity
    assert wrong_identity["facts"] == []

    wrong_operation_request = copy.deepcopy(industry_first["pages"][0]["request"])
    wrong_operation_request["operation"] = "delete_facts"
    wrong_operation = industry_reopened.call(wrong_operation_request)
    assert wrong_operation["status"] == "unavailable", wrong_operation
    assert wrong_operation["response"] is None
    assert wrong_operation["rejected"]["status"] == "rejected", wrong_operation
    assert wrong_operation["error_code"] == "subject_contract_output_invalid", wrong_operation

    assert _tree_hashes(owner_root) == owner_before, "read-only consumer calls changed StockWiki owner files"
    assert all(Path(path).is_file() for path in (
        theme_first["artifacts"]["request"], theme_first["artifacts"]["response"],
        theme_first["artifacts"]["report_json"], theme_export["artifacts"]["report_json"],
    ))
    assert theme_output.is_dir() and theme_capture.is_dir()
    assert Path(industry_config["capture_root"]).is_dir()
