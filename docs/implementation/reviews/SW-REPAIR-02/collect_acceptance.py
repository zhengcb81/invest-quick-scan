"""Preserve bounded, synthetic acceptance evidence before deleting private fixtures."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

IQS = Path(__file__).resolve().parents[4]
OWN = IQS / "runs/sw-repair-2026-10-08-01"
INTAKE = IQS / "docs/implementation/intake/SW-REPAIR-02/2026-10-08"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write(path: Path, body) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())


def main() -> None:
    for source in (OWN / "logs").glob("*.log"):
        copy(source, INTAKE / "verification" / source.name)
    for source in (OWN / "pytest-extra").rglob("boundary-result.json"):
        body = json.loads(source.read_text(encoding="utf-8"))
        copy(source, INTAKE / "counterexamples" / (body["dimension"] + ".json"))
    for source in (OWN / "pytest-aligned").rglob("boundary-result.json"):
        body = json.loads(source.read_text(encoding="utf-8"))
        copy(source, INTAKE / "counterexamples" / (body["dimension"] + ".json"))
    for kind in ("root", "parent"):
        copy(OWN / "junction-fixtures" / kind / "result.json", INTAKE / "counterexamples" / ("junction-" + kind + ".json"))
    copy(OWN / "junction-fixtures.json", INTAKE / "counterexamples/junction-creation.json")
    wanted = {"e2e-01-list-2000.png", "e2e-05-multi-condition.png", "e2e-07-variants.png"}
    for source in (OWN / "pytest-browser").rglob("*.png"):
        if source.name in wanted:
            copy(source, INTAKE / "verification/screenshots" / source.name)
    snapshot = json.loads((OWN / "export-manifest.json").read_text(encoding="utf-8"))
    changed = []
    for item in snapshot:
        data = (OWN / "runtime" / item["path"]).read_bytes()
        if sha(data) != item["sha256"] or len(data) != item["bytes"]:
            changed.append(item["path"])
    inert = (OWN / "runtime/config/llm_providers.yaml").read_bytes()
    write(INTAKE / "verification/environment-fixture.json", {
        "path": "config/llm_providers.yaml", "kind": "generated_inert_environment_not_git_source",
        "bytes": len(inert), "sha256": sha(inert), "providers": [], "keys": 0})
    browser = (OWN / "logs/browser.log").read_bytes()
    encoding = "utf-16" if browser.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8"
    browser_text = browser.decode(encoding)
    local = re.findall(r"loopback HTTP only: (\d+) requests to \['127\.0\.0\.1:(\d+)'\]", browser_text)
    write(INTAKE / "verification/result.json", {
        "status": "changes_requested", "result_commit": "9f9e0afe16a327b475cb7a6e3d40bd1578bb9b0f",
        "core": {"passed": 81, "failed": 0, "skipped": 0, "seconds": 19.48,
                 "includes": "74 worker affected methods plus 7 original frozen intake cases"},
        "browser": {"passed": 11, "failed": 0, "skipped": 0, "seconds": 79.64,
                    "requests": sum(int(n) for n, port in local), "ports": [int(port) for n, port in local],
                    "existing_chromium": True, "browser_downloads": 0},
        "additional": {"methods": 12, "failed": 12, "setup_errors": 0,
                       "batches": [{"failed": 10, "seconds": 2.16, "period_basis_superseded": True},
                                   {"failed": 2, "deselected": 10, "seconds": 0.84, "cases": "junction"},
                                   {"failed": 2, "seconds": 1.13, "cases": "completed_period_and_basis", "supersedes": "initial period/basis; not two additional logical cases"}],
                       "not_counted": "initial junction dataclass serialization failures were controller errors",
                       "period_basis_corrected": "two focused re-runs use completed FY2025 vs 2026H1 and current vs normalized on 2026H1; original forward-end cases retained and superseded"},
        "snapshot_files": len(snapshot), "snapshot_changes_after_tests": changed,
        "network_scope": "Python audit permits loopback and exact read-only legacy Git command; browser page routes abort external requests",
        "paid_api_requests": 0, "keys_provided": 0, "production_database_reads_or_writes": 0,
        "source_repository_writes": 0, "cleanup_pending": True,
        "limits": ["Python audit does not restrict all native child-process reads/writes; installed Chromium is allowed only for the browser test",
                   "browser background networking disabled and external DNS forced to NOTFOUND; page-route assertions are not a system-wide packet capture",
                   "worker 1032/1046 full-suite logs are received evidence, not re-run by coordinator",
                   "real identity/facts golden and QA joint flow remain missing/not_run"]})
    if changed or len(local) != 11:
        raise ValueError("snapshot drift or missing browser request receipts")
    print(json.dumps({"snapshot_files_unchanged": len(snapshot), "browser_requests": sum(int(n) for n, p in local),
                      "browser_ports": len(local), "new_true_failures": 12, "cleanup_pending": True}))


if __name__ == "__main__":
    main()
