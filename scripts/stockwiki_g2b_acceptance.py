"""Coordinator-side G2b acceptance against StockWiki's public owner export.

The fixture values come from StockWiki's own test fixtures. Owner stores seed
isolated roots; the request itself is captured only from the public CLI.
No production database or external repo file is written by this script.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from stockwiki_mapping_contract import MappingContractError, validate_mapping_dto


IQS_ROOT = Path(__file__).resolve().parents[1]
AS_OF = "2026-09-29T00:00:00Z"
EXPECTED_SHA256 = "0efc2c04daa7b6345078410a5df5ae0aa5bec9098b1523d7c25f9f60f53e5d2f"


def _owner_fixture(stockwiki_root: Path, root: Path) -> tuple[str, dict]:
    sys.path.insert(0, str(stockwiki_root))
    sys.path.insert(0, str(stockwiki_root / "tests"))
    from test_identity_g2b_export import _binding, _entity, _provisional_receipt  # type: ignore[import-not-found]
    from stockwiki.identity_receipts import IdentityReceiptStore, binding_projection
    from stockwiki.market_registry import MarketRegistryStore
    from stockwiki.paths import WorkspacePaths
    from stockwiki.quick_scan_store import QuickScanStore

    paths = WorkspacePaths.from_root(root)
    entity = _entity()
    binding = _binding()
    receipt = _provisional_receipt()
    qss = QuickScanStore(paths)
    qss.migrate()
    qss.save_entity(entity, source_bindings=[binding])
    receipts = IdentityReceiptStore(paths)
    receipts.migrate()
    receipts.record_receipt(receipt, identity_store=qss)
    registry = MarketRegistryStore(paths)
    csv_path = stockwiki_root / "tests" / "fixtures" / "market_registry" / "iso10383_sample.csv"
    registry.import_official_csv(csv_path.read_bytes(),
                                 source_url="https://example.invalid/mic.csv",
                                 fetched_at="2026-09-30T00:00:00Z")

    owner_records = {
        "entity": qss.get_entity(entity["entity_id"]),
        "receipt": receipts.get_receipt(receipt["receipt_id"]),
        "registry": registry.read_projection(),
        "binding": binding_projection(qss, binding["binding_ref"]),
    }
    assert owner_records["entity"] is not None
    assert owner_records["receipt"] is not None
    return entity["entity_id"], owner_records


def _export(stockwiki_root: Path, root: Path, entity_id: str) -> bytes:
    result = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", "-m", "stockwiki.cli", "--root", str(root),
         "identity-export-g2b", "--entity-id", entity_id, "--as-of", AS_OF],
        cwd=stockwiki_root, capture_output=True, timeout=120, check=False,
    )
    if result.returncode != 0 or result.stderr or result.stdout.count(b"\n") != 1:
        raise AssertionError(f"StockWiki export failed: exit={result.returncode}; stderr={result.stderr[:300]!r}")
    # Windows text stdout emits CRLF even though the serializer writes "\n".
    return result.stdout.removesuffix(b"\r\n").removesuffix(b"\n")


def _iqs_validate(request_path: Path) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", "scripts/identity_contract_cli.py",
         "--input", str(request_path), "--schema-version", "2.2.0"],
        cwd=IQS_ROOT, capture_output=True, timeout=120, check=False,
    )
    if result.stderr:
        raise AssertionError(f"IQS CLI stderr: {result.stderr[:300]!r}")
    lines = result.stdout.splitlines()
    if len(lines) != 1:
        raise AssertionError(f"IQS CLI line count: {len(lines)}")
    return result.returncode, json.loads(lines[0])


def _check_owner_joins(request: dict, owner: dict) -> None:
    payload = request["payload"]
    context = request["trusted_context"]
    assert request["schema_version"] == "2.2.0" and request["object_type"] == "entity"
    assert payload["identity_schema_version"] == "2.1.0"
    assert payload["identity_state"] == "provisional"
    assert payload["entity_id"] == owner["entity"]["entity_id"]
    assert payload["identity_revision"] == owner["entity"]["identity_revision"]
    receipt_id = payload["scope_attestation_id"]
    receipt = context["identity_receipts"][receipt_id]
    assert receipt == owner["receipt"]
    assert receipt["effective_status"] == "active"
    assert receipt["entity_id"] == payload["entity_id"]
    assert receipt["identity_revision"] == payload["identity_revision"]
    assert context["market_registry"] == owner["registry"]
    assert len(payload["securities"]) == len(payload["listings"]) == 1
    listing = payload["listings"][0]
    security = payload["securities"][0]
    assert listing["security_id"] == security["security_id"] == receipt["security_id"]
    assert listing["listing_id"] == receipt["listing_id"]
    assert listing["entity_id"] == payload["entity_id"]
    assert listing["exchange_mic"] in context["market_registry"][listing["market"]]
    binding = context["source_bindings"][listing["source_binding_ref"]]
    for key in ("binding_ref", "source_namespace", "source_record_id", "entity_id",
                "security_id", "listing_id", "market", "exchange_raw", "exchange_mic",
                "ticker", "status"):
        assert binding[key] == owner["binding"][key], key
    assert binding["source_record_id"] == receipt["source_record_id"]
    assert binding["listing_id"] == listing["listing_id"]
    assert binding["security_id"] == security["security_id"]


def _near_name_mapping_probe(stockwiki_root: Path, root: Path, golden: Path,
                             capture_golden: bool) -> dict:
    """Use owner store/snapshot/mapping APIs; names are synthetic labels."""
    sys.path.insert(0, str(stockwiki_root))
    sys.path.insert(0, str(stockwiki_root / "tests"))
    from test_identity_snapshot import (  # type: ignore[import-not-found]
        _ENTITY_V4, _ENTITY_V4_2, _SECURITY_V4, _SECURITY_V4_2,
        _binding, _entity_v4,
    )
    from stockwiki.identity_mapping import build_mapping_result
    from stockwiki.identity_snapshot import build_identity_snapshot
    from stockwiki.paths import WorkspacePaths
    from stockwiki.quick_scan_store import QuickScanStore

    store = QuickScanStore(WorkspacePaths.from_root(root))
    store.migrate()
    first = _entity_v4(_ENTITY_V4, _SECURITY_V4, binding_ref="BND_fixture_1")
    second = _entity_v4(_ENTITY_V4_2, _SECURITY_V4_2, binding_ref="BND_fixture_2")
    first["canonical_name"] = "中微公司（合成标签）"
    second["canonical_name"] = "中微半导体（合成标签）"
    first["company_wiki_ref"] = "wiki/companies/synthetic-one"
    second["company_wiki_ref"] = "wiki/companies/synthetic-two"
    store.save_entity(first, source_bindings=[_binding("BND_fixture_1", _SECURITY_V4, _ENTITY_V4)])
    store.save_entity(second, source_bindings=[_binding("BND_fixture_2", _SECURITY_V4_2, _ENTITY_V4_2)])
    snapshot = build_identity_snapshot(store, as_of=AS_OF)
    assert {entity["entity_id"] for entity in snapshot["entities"]} == {_ENTITY_V4, _ENTITY_V4_2}
    query = {"ticker": "ACME", "ticker_raw": "ACME", "market": "US",
             "exchange_raw": "NASDAQ", "exchange_mic": "XNAS", "as_of": AS_OF}
    binding = _binding("BND_fixture_1", _SECURITY_V4, _ENTITY_V4)
    exact_query = {**query, "source_binding_expectation": {
        "source_namespace": binding["source_namespace"],
        "source_record_id": binding["source_record_id"],
    }}
    unknown_query = {**query, "ticker": "NOPE", "ticker_raw": "NOPE"}
    mismatch_query = {**query, "source_binding_expectation": {
        "source_namespace": binding["source_namespace"], "source_record_id": "urn:wrong",
    }}
    cases = [
        {"name": "not_attempted", "query": None, "dto": build_mapping_result(snapshot, None)},
        {"name": "unknown", "query": unknown_query,
         "dto": build_mapping_result(snapshot, unknown_query)},
        {"name": "ambiguous", "query": query,
         "dto": build_mapping_result(snapshot, query)},
        {"name": "mapped", "query": exact_query,
         "dto": build_mapping_result(snapshot, exact_query)},
        {"name": "source_mismatch", "query": mismatch_query,
         "dto": build_mapping_result(snapshot, mismatch_query)},
    ]
    for case in cases:
        validate_mapping_dto(case["dto"], snapshot, case["query"])
    by_name = {case["name"]: case["dto"] for case in cases}
    ambiguous = by_name["ambiguous"]
    assert ambiguous["mapping_status"] == "ambiguous" and ambiguous["candidate"] is None
    assert {candidate["entity_id"] for candidate in ambiguous["candidates"]} == {_ENTITY_V4, _ENTITY_V4_2}
    exact = by_name["mapped"]
    assert exact["mapping_status"] == "mapped"
    assert exact["candidate"]["entity_id"] == _ENTITY_V4
    bundle = {"snapshot": snapshot, "cases": cases}
    canonical = json.dumps(bundle, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":"), allow_nan=False).encode("utf-8")
    if not capture_golden:
        assert golden.read_bytes() == canonical, "mapping DTO golden differs from owner API"
    forged = copy.deepcopy(exact)
    forged["candidate"]["entity_id"] = "ENT_forged"
    for changed_dto, changed_query in (
        (forged, exact_query),
        ({**exact, "mapping_status": "unknown"}, exact_query),
        ({**exact, "snapshot_sha256": "0" * 64}, exact_query),
        (exact, {**exact_query, "as_of": "2026-09-30T00:00:00Z"}),
    ):
        try:
            validate_mapping_dto(changed_dto, snapshot, changed_query)
        except MappingContractError:
            pass
        else:
            raise AssertionError("forged mapping DTO was accepted")
    if capture_golden:
        golden.parent.mkdir(parents=True, exist_ok=True)
        golden.write_bytes(canonical)
    return {"duplicate_listing_key_without_source": "ambiguous_unmerged",
            "synthetic_name_labels_only": True,
            "exact_source_key": "mapped_to_one_entity",
            "four_states_and_source_mismatch": "consumer_valid",
            "mapping_golden_sha256": hashlib.sha256(canonical).hexdigest(),
            "mapping_negative_count": 4}


def run(stockwiki_root: Path, golden: Path, capture_golden: bool,
        mapping_golden: Path, capture_mapping_golden: bool) -> dict:
    if not (stockwiki_root / "stockwiki" / "cli.py").is_file():
        raise ValueError("StockWiki root does not contain public CLI")
    if capture_golden and not golden.is_relative_to(IQS_ROOT):
        raise ValueError("captured golden must remain inside the IQS repository")
    if capture_mapping_golden and not mapping_golden.is_relative_to(IQS_ROOT):
        raise ValueError("captured mapping golden must remain inside the IQS repository")
    if golden.exists() and capture_golden:
        raise ValueError("golden already exists; capture must never overwrite")
    if mapping_golden.exists() and capture_mapping_golden:
        raise ValueError("mapping golden already exists; capture must never overwrite")
    with tempfile.TemporaryDirectory(prefix="iqs-g2b-coordinator-") as parent:
        temp_root = Path(parent)
        outputs = []
        first_owner = None
        for index in (1, 2):
            root = temp_root / f"owner-{index}"
            entity_id, owner = _owner_fixture(stockwiki_root, root)
            outputs.append(_export(stockwiki_root, root, entity_id))
            if first_owner is None:
                first_owner = owner
        assert outputs[0] == outputs[1], "owner export must be byte-stable across isolated stores"
        canonical = outputs[0]
        sha = hashlib.sha256(canonical).hexdigest()
        assert sha == EXPECTED_SHA256, f"owner golden SHA drift: {sha}"
        if not capture_golden:
            assert golden.read_bytes() == canonical, "frozen golden differs from owner public export"
        request = json.loads(canonical.decode("utf-8"))
        assert first_owner is not None
        _check_owner_joins(request, first_owner)

        input_path = temp_root / "request.json"
        input_path.write_bytes(canonical)
        code, outcome = _iqs_validate(input_path)
        assert code == 0 and outcome["status"] == "valid" and outcome["errors"] == []

        mutations = {
            "entity_id": lambda r: r["payload"].__setitem__("entity_id", "ENT_1b2a4d3e-0000-4a1b-8c2d-000000000099"),
            "receipt_removed": lambda r: r["trusted_context"]["identity_receipts"].clear(),
            "binding_source": lambda r: r["trusted_context"]["source_bindings"]["BND_fixture_acme_1"].__setitem__("source_record_id", "urn:wrong"),
            "mic_removed": lambda r: r["trusted_context"]["market_registry"]["US"].remove("XNAS"),
            "revision": lambda r: r["payload"].__setitem__("identity_revision", 2),
        }
        negative_codes = {}
        for name, mutate in mutations.items():
            changed = copy.deepcopy(request)
            mutate(changed)
            input_path.write_text(json.dumps(changed, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")
            code, outcome = _iqs_validate(input_path)
            assert code == 2 and outcome["status"] == "invalid" and outcome["errors"], name
            assert "ACME" not in json.dumps(outcome), "consumer diagnostics echoed company payload"
            negative_codes[name] = [error["code"] for error in outcome["errors"]]
        near_name = _near_name_mapping_probe(stockwiki_root, temp_root / "near-name",
                                             mapping_golden, capture_mapping_golden)
        if capture_golden:
            golden.parent.mkdir(parents=True, exist_ok=True)
            golden.write_bytes(canonical)
    assert not temp_root.exists(), "temporary owner stores were not removed"
    return {"status": "passed", "stockwiki_root": str(stockwiki_root),
            "golden": str(golden), "golden_sha256": sha,
            "positive": "IQS exit 0 valid", "negative_codes": negative_codes,
            "owner_mapping_probe": near_name,
            "temporary_roots_cleaned": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stockwiki-root", type=Path, required=True)
    parser.add_argument("--golden", type=Path, required=True)
    parser.add_argument("--capture-golden", action="store_true")
    parser.add_argument("--mapping-golden", type=Path, required=True)
    parser.add_argument("--capture-mapping-golden", action="store_true")
    args = parser.parse_args()
    result = run(args.stockwiki_root.resolve(), args.golden.resolve(), args.capture_golden,
                 args.mapping_golden.resolve(), args.capture_mapping_golden)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
