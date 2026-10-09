"""Versioned manifest format for the W12 quick-scan backup lane.

Owns everything that describes a backup rather than performing one: the format
constants, the refusal codes shared by create/verify/restore, the canonical
manifest digest, the per-file SQLite reports (schema version, integrity, table
counts, ACK/observation/member watermarks, rule-version markers) and the
manifest builder itself. ``quick_scan_backup`` performs the copying and calls
into this module; both are StockWiki-owned and offline.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_delivery import DELIVERY_RULES_VERSION
from stockwiki.quick_scan_freshness import FRESHNESS_RULES_VERSION
from stockwiki.quick_scan_query import QUERY_RULES_VERSION
from stockwiki.quick_scan_recovery import RECOVERY_POLICY_VERSION
from stockwiki.quick_scan_recovery import RULES_VERSION as RECOVERY_RULES_VERSION
from stockwiki.quick_scan_rules import RULES_VERSION as POLICY_RULES_VERSION

BACKUP_FORMAT_VERSION = "1.0.0"
MANIFEST_SCHEMA = "stockwiki.quick_scan_backup_manifest/1.0.0"
MANIFEST_NAME = "quick_scan_backup_manifest.json"

# Frozen manifest reading policy (SWR-02): a directory is only ever treated as a
# StockWiki backup when its ``schema`` is one of these EXACT strings and its
# ``format_version`` is a strict MAJOR.MINOR.PATCH whose major equals ours.
# Adding a schema version here is a deliberate, reviewed protocol change.
SUPPORTED_MANIFEST_SCHEMAS = (MANIFEST_SCHEMA,)
_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")

# Trusted owner record (SWR-02). ``prune_backups`` may only delete a directory
# the real ``create_backup`` flow registered by binding its name to the digest of
# the manifest it published. A self-consistent manifest, a ``created_by`` string
# or a matching directory name alone is NOT ownership.
# Evidence boundary: this is a versioned provenance record inside the existing
# backup area, not a signature — a same-privilege local process that can write
# the backup root can also write this file.
OWNER_REGISTRY_NAME = "owner_registry.json"
OWNER_REGISTRY_SCHEMA = "stockwiki.quick_scan_backup_owner_registry/1.0.0"
OWNER_RECORD_VERSION = "stockwiki.quick_scan_backup_owner_record/1.0.0"
OWNER_MODULE = "stockwiki.quick_scan_backup"
OWNER_READ_EVIDENCE_NOTE = (
    "owner_registry is a versioned provenance record written only by the create "
    "flow inside the existing backup area; it binds a directory name to the "
    "digest of the manifest that flow published. It is NOT a signature and does "
    "NOT claim to stop a same-privilege local process that can write the backup "
    "root from forging both the directory and the record."
)


QUICK_SCAN_DIR = Path("data") / "quick_scan"
EXECUTOR_MESSAGE = "执行侧未核验、禁止恢复收费"

# Highest PRAGMA user_version this build understands per owned store file.
# A backup whose stored schema is newer than this must not be restored.
SUPPORTED_USER_VERSIONS = {
    "scan.sqlite": 6,
    "scan_observations.sqlite": 2,
    "analysis_subjects.sqlite": 1,
    "identity_receipts.sqlite": 1,
    "scan_evidence.sqlite": 1,
    "market_registry.sqlite": 1,
}

RESTORE_PRECONDITIONS = (
    "target data/quick_scan must not exist or must be empty before restore",
    "restore covers StockWiki-owned quick-scan stores only (data/quick_scan)",
    "no cross-file atomicity: reconcile ACK / observation / member watermarks "
    "between owners before resuming any dispatch against the restored store",
    "stop new dispatches or complete in-flight reconciliation before swapping stores",
    "executor (StockQA) database, fee ledger and paid dispatch state are NOT in this "
    "backup: " + EXECUTOR_MESSAGE,
    "store_id is path-derived: ACKs written after a cross-root restore carry the new "
    "path-derived store_id while historical ACK rows keep the original value",
    "verify_backup must pass before restore (enforced automatically)",
)


class QuickScanBackupError(ValueError):
    """A named refusal from the quick-scan backup/restore lane."""

    def __init__(self, error_code: str, detail: str = "") -> None:
        self.error_code = error_code
        self.detail = detail
        super().__init__(f"{error_code}: {detail}" if detail else error_code)


def _bad(code: str, detail: str = "") -> QuickScanBackupError:
    return QuickScanBackupError(code, detail)


def manifest_digest(body: dict[str, Any]) -> str:
    """Canonical SHA-256 over the manifest body (without ``manifest_sha256``)."""
    blob = json.dumps(
        body, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_manifest_shape(manifest: Any, *, expect_name: str) -> None:
    """Frozen structural gate for every manifest that claims to be ours.

    Runs BEFORE any file hash is trusted: version policy, schema marker, the
    ``name`` ↔ directory binding, non-empty/unique/safe file paths, the
    executor-side prohibition block and the non-atomic consistency block. A
    digest is only an integrity check over whatever bytes were hashed — it is
    never proof of structure or of ownership (SWR-02).
    """
    if not isinstance(manifest, dict):
        raise _bad("manifest_invalid", "manifest must be a JSON object")

    fmt = manifest.get("format_version")
    if (
        not isinstance(fmt, str)
        or not _SEMVER.fullmatch(fmt)
        or fmt.split(".")[0] != BACKUP_FORMAT_VERSION.split(".")[0]
    ):
        raise _bad("unsupported_format_version", str(fmt))

    schema = manifest.get("schema")
    if schema not in SUPPORTED_MANIFEST_SCHEMAS:
        raise _bad("unsupported_manifest_schema", str(schema))

    name = manifest.get("name")
    if not isinstance(name, str) or name != expect_name:
        raise _bad("manifest_name_mismatch", f"{name!r} != {expect_name!r}")

    created = manifest.get("created_at_utc")
    if not isinstance(created, str) or not created.endswith("Z"):
        raise _bad("manifest_invalid", "created_at_utc must be a UTC timestamp")

    if not isinstance(manifest.get("workspace_root"), str) or not manifest["workspace_root"]:
        raise _bad("manifest_invalid", "workspace_root required")
    if manifest.get("quick_scan_dir") != QUICK_SCAN_DIR.as_posix():
        raise _bad("manifest_invalid", "quick_scan_dir required")

    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise _bad("manifest_invalid", "files must be a non-empty list")
    seen: set[str] = set()
    for entry in files:
        if not isinstance(entry, dict):
            raise _bad("manifest_invalid", "file entry must be an object")
        rel = entry.get("path")
        if not isinstance(rel, str) or not rel or "\\" in rel:
            raise _bad("manifest_invalid", f"unsafe file path: {rel!r}")
        parsed = Path(rel)
        if parsed.is_absolute() or ".." in parsed.parts or parsed.as_posix() != rel:
            raise _bad("manifest_invalid", f"unsafe file path: {rel!r}")
        if rel in seen:
            raise _bad("manifest_duplicate_path", rel)
        seen.add(rel)
        digest = entry.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise _bad("manifest_invalid", f"missing sha256: {rel}")
        size = entry.get("bytes")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise _bad("manifest_invalid", f"missing byte size: {rel}")

    preconditions = manifest.get("restore_preconditions")
    if not isinstance(preconditions, list) or not preconditions:
        raise _bad("manifest_invalid", "restore_preconditions required")

    executor = manifest.get("executor_side")
    if not isinstance(executor, dict):
        raise _bad("executor_side_invalid", "executor_side must be an object")
    expected_executor = {
        "provided": False,
        "status": "unverified",
        "owned_by": "StockQA",
        "fee_restoration": "prohibited",
        "paid_dispatch_restored": False,
        "fee_ledger_included": False,
        "paid_dispatch_included": False,
        "message": EXECUTOR_MESSAGE,
    }
    for key, expected in expected_executor.items():
        if executor.get(key) != expected:
            raise _bad("executor_side_invalid", f"{key}={executor.get(key)!r}")

    consistency = manifest.get("consistency")
    if not isinstance(consistency, dict) or consistency.get("cross_file_atomic") is not False:
        raise _bad("consistency_invalid", "cross_file_atomic must be false")


def validate_owner_registry(data: Any) -> dict[str, Any]:
    """Frozen reading policy for the owner registry (SR02-3).

    Version policy first: an UNKNOWN ``format_version`` fails closed, because a
    registry this build does not understand can never grant delete authority.
    Same strict ``MAJOR.MINOR.PATCH``/same-major rule as the manifest, then the
    exact schema marker, then ``records`` must be a list. This validates SHAPE
    only — whether an individual record actually OWNS a directory (record
    version, owner module, workspace binding, digest) is decided in
    ``prune_backups`` against the manifest the record is supposed to describe.
    """
    if not isinstance(data, dict):
        raise _bad(
            "owner_registry_invalid",
            f"registry must be a JSON object, got {type(data).__name__}",
        )
    fmt = data.get("format_version")
    if (
        not isinstance(fmt, str)
        or not _SEMVER.fullmatch(fmt)
        or fmt.split(".")[0] != BACKUP_FORMAT_VERSION.split(".")[0]
    ):
        raise _bad("owner_registry_version_unsupported", str(fmt))
    if data.get("schema") != OWNER_REGISTRY_SCHEMA:
        raise _bad("owner_registry_invalid", str(data.get("schema")))
    if not isinstance(data.get("records"), list):
        raise _bad("owner_registry_invalid", "records must be a list")
    return data


def owner_record_grants_deletion(record: Any, *, manifest: dict[str, Any]) -> bool:
    """Does this owner record describe THIS manifest in THIS workspace (SR02-3)?

    Name + digest alone are not ownership: the record must also carry our
    record version, our owner module and the workspace root recorded in the
    manifest itself. A foreign/damaged record simply grants nothing — it is
    never rewritten, adopted or repaired here.
    """
    if not isinstance(record, dict):
        return False
    if record.get("record_version") != OWNER_RECORD_VERSION:
        return False
    if record.get("owner_module") != OWNER_MODULE:
        return False
    if record.get("workspace_root") != manifest.get("workspace_root"):
        return False
    digest = record.get("manifest_sha256")
    return isinstance(digest, str) and digest == manifest.get("manifest_sha256")


def _report_database(db_path: Path) -> dict[str, Any]:
    """Read schema/count facts FROM the snapshot copy, never from the live file."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        con.row_factory = sqlite3.Row
        user_version = int(con.execute("PRAGMA user_version").fetchone()[0])
        journal_mode = str(con.execute("PRAGMA journal_mode").fetchone()[0])
        integrity = str(con.execute("PRAGMA integrity_check").fetchone()[0])
        tables = [
            row["name"]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        counts: dict[str, int] = {}
        for table in tables:
            counts[table] = int(con.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0])
        sample = _sample_queries(con, tables)
    finally:
        con.close()
    if integrity != "ok":
        raise _bad("integrity_check_failed", db_path.name)
    return {
        "user_version": user_version,
        "journal_mode": journal_mode,
        "integrity": integrity,
        "tables": tables,
        "counts": counts,
        **sample,
    }


def _sample_queries(con: sqlite3.Connection, tables: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if "quick_scan_import_item" in tables:
        row = con.execute(
            "SELECT COALESCE(MAX(ack_sequence), 0) AS seq, MAX(received_at) AS at, "
            "COUNT(*) AS n FROM quick_scan_import_item"
        ).fetchone()
        out["ack"] = {
            "max_ack_sequence": int(row["seq"]),
            "max_received_at": row["at"],
            "items": int(row["n"]),
        }
    if "quick_scan_observation" in tables:
        row = con.execute(
            "SELECT COALESCE(MAX(import_sequence), 0) AS seq, MAX(imported_at) AS at, "
            "COUNT(*) AS n FROM quick_scan_observation"
        ).fetchone()
        releases = sorted(
            {
                str(r[0])
                for r in con.execute(
                    "SELECT DISTINCT json_extract(payload_json, '$.module_release_id') "
                    "FROM quick_scan_observation "
                    "WHERE json_extract(payload_json, '$.module_release_id') IS NOT NULL"
                )
            }
        )
        packages = sorted(
            {
                str(r[0])
                for r in con.execute(
                    "SELECT DISTINCT json_extract(payload_json, '$.module_package_id') "
                    "FROM quick_scan_observation "
                    "WHERE json_extract(payload_json, '$.module_package_id') IS NOT NULL"
                )
            }
        )
        question_versions = sorted(
            {
                str(r[0])
                for r in con.execute(
                    "SELECT DISTINCT json_extract(payload_json, '$.question_version') "
                    "FROM quick_scan_observation"
                )
                if r[0] is not None
            }
        )
        template_versions = sorted(
            {
                str(r[0])
                for r in con.execute(
                    "SELECT DISTINCT json_extract(payload_json, '$.template_version') "
                    "FROM quick_scan_observation"
                )
                if r[0] is not None
            }
        )
        publication = {
            str(row_status[0]): int(row_status[1])
            for row_status in con.execute(
                "SELECT publication_status, COUNT(*) FROM quick_scan_observation "
                "GROUP BY publication_status"
            )
        }
        out["observation"] = {
            "max_import_sequence": int(row["seq"]),
            "max_imported_at": row["at"],
            "rows": int(row["n"]),
            "module_release_ids": releases,
            "module_package_ids": packages,
            "question_versions": question_versions,
            "template_versions": template_versions,
            "publication_status": publication,
        }
    if "quick_scan_member" in tables:
        row = con.execute(
            "SELECT COALESCE(MAX(version), 0) AS v, COUNT(*) AS n, "
            "COALESCE(SUM(manual_pin), 0) AS pins FROM quick_scan_member"
        ).fetchone()
        universes = [
            str(r[0])
            for r in con.execute("SELECT universe_id FROM quick_scan_universe ORDER BY universe_id")
        ]
        policies = {
            str(r[0]): str(r[1])
            for r in con.execute(
                "SELECT universe_id, policy FROM quick_scan_maintenance_policy ORDER BY universe_id"
            )
        }
        out["roster"] = {
            "universe_ids": universes,
            "max_member_version": int(row["v"]),
            "members": int(row["n"]),
            "manual_pins": int(row["pins"]),
            "maintenance_policies": policies,
        }
    if "analysis_subject" in tables:
        row = con.execute(
            "SELECT COUNT(*) AS n, COALESCE(MAX(analysis_subject_revision), 0) AS rev "
            "FROM analysis_subject"
        ).fetchone()
        out["subjects"] = {"rows": int(row["n"]), "max_revision": int(row["rev"])}
    if "quick_scan_candidate" in tables:
        row = con.execute(
            "SELECT COUNT(*) AS n, MAX(imported_at) AS at FROM quick_scan_candidate"
        ).fetchone()
        out["candidates"] = {"rows": int(row["n"]), "max_imported_at": row[1]}
    if "quick_scan_alias" in tables:
        out["aliases"] = {
            "rows": int(con.execute("SELECT COUNT(*) FROM quick_scan_alias").fetchone()[0])
        }
    if "identity_receipt" in tables:
        out["identity_receipts"] = {
            "rows": int(con.execute("SELECT COUNT(*) FROM identity_receipt").fetchone()[0])
        }
    if "market_registry_record" in tables:
        out["market_registry"] = {
            "rows": int(con.execute("SELECT COUNT(*) FROM market_registry_record").fetchone()[0])
        }
    return out


def _rules_versions() -> dict[str, str]:
    return {
        "quick_scan_rules": POLICY_RULES_VERSION,
        "quick_scan_recovery": RECOVERY_RULES_VERSION,
        "recovery_policy_version": RECOVERY_POLICY_VERSION,
        "quick_scan_freshness": FRESHNESS_RULES_VERSION,
        "quick_scan_query": QUERY_RULES_VERSION,
        "quick_scan_delivery": DELIVERY_RULES_VERSION,
    }


def build_manifest(
    paths: WorkspacePaths, *, name: str, staging: Path, rel_files: list[Path]
) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    watermarks: dict[str, Any] = {}
    versions: dict[str, Any] = {
        "rules": _rules_versions(),
        "roster": {},
        "observations": {},
        "ack": {},
        "subjects": {},
    }
    for rel in rel_files:
        snapshot = staging / rel
        entry: dict[str, Any] = {
            "path": rel.as_posix(),
            "workspace_path": (QUICK_SCAN_DIR / rel).as_posix(),
            "bytes": snapshot.stat().st_size,
            "sha256": _sha256_file(snapshot),
            "backup_method": "sqlite3_online_backup" if rel.suffix == ".sqlite" else "byte_copy",
        }
        if rel.suffix == ".sqlite":
            report = _report_database(snapshot)
            entry["user_version"] = report["user_version"]
            entry["journal_mode"] = report["journal_mode"]
            entry["integrity"] = report["integrity"]
            for table, count in report["counts"].items():
                counts[f"{rel.name}:{table}"] = counts.get(f"{rel.name}:{table}", 0) + count
            if rel.name == "scan_observations.sqlite" and "ack" in report:
                watermarks["ack"] = report["ack"]
                watermarks["observation"] = report["observation"]
                versions["observations"] = {
                    k: report["observation"][k]
                    for k in (
                        "module_release_ids",
                        "module_package_ids",
                        "question_versions",
                        "template_versions",
                        "publication_status",
                    )
                }
                versions["ack"] = {
                    "max_ack_sequence": report["ack"]["max_ack_sequence"],
                    "max_received_at": report["ack"]["max_received_at"],
                    "user_version": report["user_version"],
                }
            if rel.name == "scan.sqlite" and "roster" in report:
                watermarks["roster"] = {
                    "max_member_version": report["roster"]["max_member_version"],
                    "members": report["roster"]["members"],
                }
                versions["roster"] = report["roster"]
            if rel.name == "analysis_subjects.sqlite" and "subjects" in report:
                watermarks["subjects"] = report["subjects"]
                versions["subjects"] = report["subjects"]
            if rel.name == "scan.sqlite" and "candidates" in report:
                watermarks["candidates"] = report["candidates"]
        files.append(entry)

    return {
        "format_version": BACKUP_FORMAT_VERSION,
        "schema": MANIFEST_SCHEMA,
        "name": name,
        "created_at_utc": _utc_now(),
        "workspace_root": str(paths.root),
        "quick_scan_dir": QUICK_SCAN_DIR.as_posix(),
        "files": files,
        "counts": dict(sorted(counts.items())),
        "watermarks": watermarks,
        "versions": versions,
        "store_identity": [
            {
                "path": entry["workspace_path"],
                "user_version": entry.get("user_version"),
                "sha256": entry["sha256"],
            }
            for entry in files
            if entry["path"].endswith(".sqlite")
        ],
        "consistency": {
            "method": "sqlite3_online_backup_per_file",
            "cross_file_atomic": False,
            "raw_live_copy": False,
            "note": (
                "Each store file is an independent consistent snapshot; the six "
                "stores are not captured in one transaction. Reconcile watermarks "
                "across owners instead of assuming cross-process atomicity."
            ),
        },
        "restore_preconditions": list(RESTORE_PRECONDITIONS),
        "executor_side": {
            "provided": False,
            "status": "unverified",
            "owned_by": "StockQA",
            "fee_ledger_included": False,
            "paid_dispatch_included": False,
            "fee_restoration": "prohibited",
            "paid_dispatch_restored": False,
            "message": EXECUTOR_MESSAGE,
        },
    }
