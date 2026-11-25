"""Replay StockWiki-owned G2b fixtures and optionally verify a fresh public export."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from iqs_scan import REPO_ROOT

from .stockwiki_mapping_contract import MappingContractError, validate_mapping_dto


IQS_ROOT = REPO_ROOT
EXPECTED_SHA256 = "0efc2c04daa7b6345078410a5df5ae0aa5bec9098b1523d7c25f9f60f53e5d2f"
MAPPING_SHA256 = "da3991c0d85ef9a0bce7c9152475b9184942df74c34fab4c5c935fb0e375a96f"


@dataclass(frozen=True)
class OwnerQuery:
    code_root: Path
    data_root: Path
    entity_id: str
    as_of: str


def _read_frozen(path: Path, expected_sha256: str) -> bytes:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError(f"frozen owner export digest changed: {path.name}")
    return raw


def _export(query: OwnerQuery) -> bytes:
    if not (query.code_root / "stockwiki" / "cli.py").is_file():
        raise ValueError("StockWiki code root does not contain the public CLI")
    result = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", "-m", "stockwiki.cli",
         "--root", str(query.data_root), "identity-export-g2b",
         "--entity-id", query.entity_id, "--as-of", query.as_of],
        cwd=query.code_root, capture_output=True, timeout=120, check=False,
    )
    if result.returncode != 0:
        message = f"StockWiki public identity export failed (exit {result.returncode})"
        try:
            diagnostic = json.loads(result.stderr)
        except ValueError:
            diagnostic = None
        code = diagnostic.get("error_code") if isinstance(diagnostic, dict) else None
        if isinstance(code, str) and re.fullmatch(r"[a-z][a-z0-9_]*", code):
            message += f": {code}"
        raise ValueError(message)
    return result.stdout.removesuffix(b"\r\n").removesuffix(b"\n")


def _iqs_validate(request_path: Path) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", "scripts/identity_contract_cli.py",
         "--input", str(request_path), "--schema-version", "2.2.0"],
        cwd=IQS_ROOT, capture_output=True, timeout=120, check=False,
    )
    return result.returncode, json.loads(result.stdout)


def _check_frozen_joins(request: dict) -> None:
    payload = request["payload"]
    context = request["trusted_context"]
    assert request["schema_version"] == "2.2.0" and request["object_type"] == "entity"
    assert payload["identity_schema_version"] == "2.1.0"
    assert payload["identity_state"] == "provisional"
    receipt = context["identity_receipts"][payload["scope_attestation_id"]]
    assert receipt["effective_status"] == "active"
    assert receipt["entity_id"] == payload["entity_id"]
    assert receipt["identity_revision"] == payload["identity_revision"]
    listing, = payload["listings"]
    security, = payload["securities"]
    assert listing["security_id"] == security["security_id"] == receipt["security_id"]
    assert listing["listing_id"] == receipt["listing_id"]
    assert listing["entity_id"] == payload["entity_id"]
    assert listing["exchange_mic"] in context["market_registry"][listing["market"]]
    binding = context["source_bindings"][listing["source_binding_ref"]]
    assert binding["source_record_id"] == receipt["source_record_id"]
    assert binding["listing_id"] == listing["listing_id"]
    assert binding["security_id"] == security["security_id"]


def _verify_mapping_bundle(path: Path) -> dict:
    bundle = json.loads(_read_frozen(path, MAPPING_SHA256))
    snapshot = bundle["snapshot"]
    cases = {case["name"]: case for case in bundle["cases"]}
    expected = {"not_attempted": None, "unknown": "unknown", "ambiguous": "ambiguous",
                "mapped": "mapped", "source_mismatch": "unknown"}
    assert cases.keys() == expected.keys()
    for name, case in cases.items():
        validate_mapping_dto(case["dto"], snapshot, case["query"])
        assert case["dto"]["mapping_status"] == expected[name]
    ambiguous = cases["ambiguous"]["dto"]
    assert ambiguous["candidate"] is None
    assert len({item["entity_id"] for item in ambiguous["candidates"]}) == 2
    scoped = cases["mapped"]
    dto, query = scoped["dto"], scoped["query"]
    assert cases["source_mismatch"]["dto"]["binding_mismatch"] is True

    forged = copy.deepcopy(dto)
    forged["candidate"]["entity_id"] = "ENT_forged"
    for changed, changed_query in (
        (forged, query),
        ({**dto, "mapping_status": "unknown"}, query),
        ({**dto, "snapshot_sha256": "0" * 64}, query),
        (dto, {**query, "as_of": "2026-09-30T00:00:00Z"}),
    ):
        try:
            validate_mapping_dto(changed, snapshot, changed_query)
        except MappingContractError:
            pass
        else:
            raise AssertionError("forged mapping DTO was accepted")
    return {"duplicate_listing_key_without_source": "ambiguous_unmerged",
            "synthetic_name_labels_only": True, "exact_source_key": "mapped_to_one_entity",
            "four_states_and_source_mismatch": "consumer_valid",
            "mapping_golden_sha256": MAPPING_SHA256, "mapping_negative_count": 4}


def _validate_frozen_request(canonical: bytes, input_path: Path) -> dict:
    request = json.loads(canonical)
    _check_frozen_joins(request)
    input_path.write_bytes(canonical)
    code, outcome = _iqs_validate(input_path)
    assert code == 0 and outcome["status"] == "valid" and not outcome["errors"]

    listing = request["payload"]["listings"][0]
    binding_id = listing["source_binding_ref"]
    market, exchange = listing["market"], listing["exchange_mic"]
    mutations = {
        "entity_id": lambda row: row["payload"].__setitem__(
            "entity_id", "ENT_1b2a4d3e-0000-4a1b-8c2d-000000000099"),
        "receipt_removed": lambda row: row["trusted_context"]["identity_receipts"].clear(),
        "binding_source": lambda row: row["trusted_context"]["source_bindings"][binding_id].__setitem__(
            "source_record_id", "urn:wrong"),
        "mic_removed": lambda row: row["trusted_context"]["market_registry"][market].remove(exchange),
        "revision": lambda row: row["payload"].__setitem__("identity_revision", 2),
    }
    negative_codes = {}
    for name, mutate in mutations.items():
        changed = copy.deepcopy(request)
        mutate(changed)
        input_path.write_text(json.dumps(changed, ensure_ascii=False), encoding="utf-8")
        code, outcome = _iqs_validate(input_path)
        assert code == 2 and outcome["status"] == "invalid" and outcome["errors"], name
        assert listing["ticker"] not in json.dumps(outcome), "consumer diagnostics echoed company payload"
        negative_codes[name] = [error["code"] for error in outcome["errors"]]
    return negative_codes


def _verify_live_query(query: OwnerQuery, request_path: Path) -> dict:
    raw = _export(query)
    request = json.loads(raw)
    payload = request.get("payload") if isinstance(request, dict) else None
    if not isinstance(payload, dict) or payload.get("entity_id") != query.entity_id:
        raise ValueError("StockWiki public export did not bind the requested entity")
    request_path.write_bytes(raw)
    code, outcome = _iqs_validate(request_path)
    if code != 0 or outcome.get("status") != "valid" or outcome.get("errors"):
        raise ValueError("fresh StockWiki public export failed IQS validation")
    return {"entity_id": query.entity_id, "as_of": query.as_of,
            "sha256": hashlib.sha256(raw).hexdigest(), "consumer_status": "valid"}


def run(golden: Path, mapping_golden: Path, *, owner: OwnerQuery | None = None) -> dict:
    canonical = _read_frozen(golden, EXPECTED_SHA256)
    mapping = _verify_mapping_bundle(mapping_golden)
    with tempfile.TemporaryDirectory(prefix="iqs-g2b-coordinator-") as parent:
        work = Path(parent)
        negatives = _validate_frozen_request(canonical, work / "request.json")
        fresh = _verify_live_query(owner, work / "live-request.json") if owner is not None else None
    return {"status": "passed", "proof_mode": "frozen_and_live" if fresh else "frozen_owner_exports",
            "golden": str(golden), "golden_sha256": EXPECTED_SHA256,
            "positive": "IQS exit 0 valid", "negative_codes": negatives,
            "owner_mapping_probe": mapping, "live_owner_export": fresh,
            "temporary_roots_cleaned": not work.exists()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", type=Path, required=True)
    parser.add_argument("--mapping-golden", type=Path, required=True)
    parser.add_argument("--stockwiki-root", type=Path, help="StockWiki code root for optional live export")
    parser.add_argument("--owner-root", type=Path, help="explicit StockWiki data root for live export")
    parser.add_argument("--entity-id", help="exact entity id for live export")
    parser.add_argument("--as-of", help="UTC timestamp for live export")
    parser.add_argument("--capture-golden", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--capture-mapping-golden", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.capture_golden or args.capture_mapping_golden:
        parser.error("StockWiki owns golden export; IQS replays the supplied evidence")
    owner = None
    if args.owner_root or args.entity_id or args.as_of:
        if not all((args.stockwiki_root, args.owner_root, args.entity_id, args.as_of)):
            parser.error("live export requires --stockwiki-root, --owner-root, --entity-id and --as-of")
        owner = OwnerQuery(args.stockwiki_root.resolve(), args.owner_root.resolve(), args.entity_id, args.as_of)
    try:
        result = run(args.golden, args.mapping_golden, owner=owner)
    except (AssertionError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        parser.error(str(exc) or "G2b acceptance evidence did not match the expected contract")
    result["stockwiki_root"] = str(args.stockwiki_root.resolve()) if args.stockwiki_root else None
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0
