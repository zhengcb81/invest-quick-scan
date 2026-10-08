"""Regenerate this package's public quick-scan goldens into logs/golden/.

Everything is built through the PUBLIC entry points (identity save + import +
query layer + backup create) in a private temporary workspace; nothing touches a
production store. The JSON carries ``golden_class`` so a synthetic fixture is
never mistaken for a real identity/owner golden:

* ``synthetic_public_import_fixture`` — search/condition/legacy-snapshot output
* ``synthetic_backup_owner_fixture`` — create/owner-registry output
* real StockWiki identity golden: **missing** (never synthesised)

Usage::

    python -B -X utf8 docs/handoff/SW-REPAIR-02/build_goldens.py \
        --repo C:/Users/郑曾波/Projects/StockWiki \
        --out <repo>/docs/handoff/SW-REPAIR-02/logs/golden
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

LEGACY_QUERY_COMMIT = "9f552a67"
GOLDEN_CLASS_FIXTURE = "synthetic_public_import_fixture"
GOLDEN_CLASS_BACKUP = "synthetic_backup_owner_fixture"


def _dump(out: Path, name: str, payload: dict) -> None:
    path = out / name
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8"
    )
    print(f"wrote {path}")


def _legacy_module(repo: Path, work: Path):
    blob = subprocess.run(
        ["git", "show", f"{LEGACY_QUERY_COMMIT}:stockwiki/quick_scan_query.py"],
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8")
    target = work / "legacy_quick_scan_query.py"
    target.write_text(blob, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("golden_legacy_query", target)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    sys.path[:0] = [str(repo), str(repo / "tests")]

    from test_quick_scan_observations import _observation, _package  # noqa: E402
    from test_quick_scan_profiles import E01, _release, _workspace  # noqa: E402

    from stockwiki.quick_scan_import import import_package  # noqa: E402
    from stockwiki.quick_scan_observations import QuickScanObservationStore  # noqa: E402
    from stockwiki.quick_scan_profiles import build_profiles  # noqa: E402
    from stockwiki.quick_scan_query import query_capabilities, search  # noqa: E402
    from stockwiki.quick_scan_store import QuickScanStore  # noqa: E402

    capabilities = dict(query_capabilities())
    capabilities["golden_class"] = GOLDEN_CLASS_FIXTURE
    capabilities["generated_by"] = (
        "python -B -X utf8 docs/handoff/SW-REPAIR-02/build_goldens.py "
        "--repo <StockWiki> --out <StockWiki>/docs/handoff/SW-REPAIR-02/logs/golden"
    )
    _dump(out, "query_capabilities_ok.json", capabilities)

    with tempfile.TemporaryDirectory(prefix="swr02-golden-") as tmp:
        work = Path(tmp)
        paths = _workspace(work / "ws")

        # Two REAL imported analysis subjects on one field so the ambiguity
        # refusal has something to refuse (public import only, no hand-made rows).
        import_package(
            QuickScanObservationStore(paths),
            _package(
                [
                    _observation(
                        "GOLDEN_OBS_SUBJ_A",
                        entity_id=E01,
                        score=2,
                        request_id="REQ_GOLDEN_A",
                        attempt_id="ATT_GOLDEN_A",
                        extra={
                            "analysis_subject": {
                                "analysis_subject_id": ("ASJ_11111111-1111-4111-8111-111111111111"),
                                "analysis_subject_revision": 1,
                                "entity_id": E01,
                                "primary_issuer_id": E01,
                            }
                        },
                    ),
                    _observation(
                        "GOLDEN_OBS_SUBJ_B",
                        entity_id=E01,
                        score=9,
                        request_id="REQ_GOLDEN_B",
                        attempt_id="ATT_GOLDEN_B",
                        extra={
                            "analysis_subject": {
                                "analysis_subject_id": ("ASJ_22222222-2222-4222-8222-222222222222"),
                                "analysis_subject_revision": 1,
                                "entity_id": E01,
                                "primary_issuer_id": E01,
                            }
                        },
                    ),
                ]
            ),
            frozen_release=_release(),
            identity_store=QuickScanStore(paths),
        )
        legacy = _legacy_module(repo, work)
        profiles = build_profiles(paths)

        # The frozen paging golden needs a set bigger than one page, so it uses
        # an explicit synthetic profile list (labelled as such) rather than the
        # 2-entity fixture workspace.
        synthetic = [
            {"entity_id": "ENT_" + str(i).zfill(6), "canonical_name": f"Fixture {i}"}
            for i in range(101)
        ]
        old = legacy.search(synthetic, page=1, page_size=50)
        page2 = search(synthetic, page=2, page_size=50, snapshot=old["snapshot"])
        _dump(
            out,
            "query_legacy_snapshot_page2_ok.json",
            {
                "golden_class": GOLDEN_CLASS_FIXTURE,
                "legacy_query_commit": LEGACY_QUERY_COMMIT,
                "legacy_snapshot": old["snapshot"],
                "legacy_page1_entity_ids": [r["entity_id"] for r in old["rows"]],
                "current_page2_entity_ids": [r["entity_id"] for r in page2["rows"]],
                "expected_page2_entity_ids": old["snapshot"]["ordered_ids"][50:100],
                "snapshot_identical": page2["snapshot"] == old["snapshot"],
                "rules_version": page2["rules_version"],
                "generation_command": (
                    "python -B -X utf8 docs/handoff/SW-REPAIR-02/build_goldens.py "
                    "--repo <StockWiki> --out <out>"
                ),
            },
        )

        conditioned = search(
            profiles,
            conditions=[{"field": "score.iqs_05", "op": ">=", "value": 1}],
            condition_combine="all",
        )
        ambiguous_condition = search(
            profiles,
            conditions=[{"field": "score.iqs_01", "op": ">=", "value": 8}],
            condition_combine="all",
        )
        _dump(
            out,
            "query_search_condition_ok.json",
            {
                "golden_class": GOLDEN_CLASS_FIXTURE,
                "query": {
                    "conditions": [{"field": "score.iqs_05", "op": ">=", "value": 1}],
                    "condition_combine": "all",
                },
                "entity_ids": [r["entity_id"] for r in conditioned["rows"]],
                "condition_rules": conditioned["condition_rules"],
                "score_condition_outcomes": [
                    {
                        "entity_id": r["entity_id"],
                        "outcome": r.get("score_condition_outcome"),
                        "leaves": r.get("score_conditions"),
                    }
                    for r in conditioned["rows"]
                ],
                "ambiguous_field_probe": {
                    "conditions": [{"field": "score.iqs_01", "op": ">=", "value": 8}],
                    "entity_ids": [r["entity_id"] for r in ambiguous_condition["rows"]],
                    "outcome_counts": ambiguous_condition["condition_rules"]["outcome_counts"],
                    "leaf_reasons": ambiguous_condition["condition_rules"]["leaf_reasons"],
                    "note": (
                        "score.iqs_01 carries incomparable subject variants, so the row "
                        "evaluates to unknown and the imported 9 never satisfies >=8"
                    ),
                },
                "facts_available": conditioned["facts_available"],
                "c06_envelope_validated": conditioned["c06_envelope_validated"],
                "generation_command": (
                    "python -B -X utf8 docs/handoff/SW-REPAIR-02/build_goldens.py "
                    "--repo <StockWiki> --out <out>"
                ),
            },
        )

        ambiguous = next(
            (
                entry
                for entry in (p["score_fields"].get("score.iqs_01") or {} for p in profiles)
                if isinstance(entry, dict) and entry.get("ambiguous")
            ),
            None,
        )
        _dump(
            out,
            "query_variant_ambiguous_ok.json",
            {
                "golden_class": GOLDEN_CLASS_FIXTURE,
                "field_id": "score.iqs_01",
                "entity_id": E01,
                "ambiguous": bool(ambiguous),
                "status": (ambiguous or {}).get("status"),
                "score": (ambiguous or {}).get("score"),
                "variant_count": (ambiguous or {}).get("variant_count"),
                "variants": (ambiguous or {}).get("variants"),
                "generation_command": (
                    "python -B -X utf8 docs/handoff/SW-REPAIR-02/build_goldens.py "
                    "--repo <StockWiki> --out <out>"
                ),
            },
        )

        from stockwiki.quick_scan_backup import create_backup, quick_scan_backup_root  # noqa: E402
        from stockwiki.quick_scan_backup_manifest import OWNER_REGISTRY_NAME  # noqa: E402

        data = paths.root / "data" / "quick_scan"
        if not any(p.is_file() for p in data.rglob("*")):
            (data / "golden_marker.txt").write_text("golden", encoding="utf-8")
        create_backup(paths, name="golden_backup")
        registry = json.loads(
            (quick_scan_backup_root(paths) / OWNER_REGISTRY_NAME).read_text(encoding="utf-8")
        )
        _dump(
            out,
            "backup_owner_registry_ok.json",
            {
                "golden_class": GOLDEN_CLASS_BACKUP,
                "registry": registry,
                "generation_command": (
                    "python -B -X utf8 docs/handoff/SW-REPAIR-02/build_goldens.py "
                    "--repo <StockWiki> --out <out>"
                ),
            },
        )

    _dump(
        out,
        "identity_golden_status.json",
        {
            "golden_class": "real_identity_golden",
            "status": "missing",
            "reason": (
                "This package is not authorised to create or certify a real StockWiki "
                "identity/owner golden; none was synthesised to fill the gap."
            ),
            "generation_command": None,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
