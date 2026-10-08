"""Archive bounded software evidence and prove the fixed snapshot/input bytes stayed intact."""
import hashlib
import json
import re
from pathlib import Path

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/sw-repair-remediation-2026-10-08-01"
INTAKE = IQS / "docs/implementation/intake/SW-REPAIR-02/2026-10-08-remediation"
OUT = INTAKE / "verification"


def read(path):
    return json.loads(path.read_text("utf-8-sig"))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, body):
    path.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    commands = read(OUT / "commands.json")
    tests = {}
    for mode in ("core", "extra", "utf8", "browser"):
        text = (OUT / (mode + ".stdout.log")).read_text("utf-8")
        tail = re.findall(r"(\d+) (passed|failed|skipped)", text.split("short test summary info")[-1])
        tests[mode] = {state: int(count) for count, state in tail}
    browser = (OUT / "browser.stdout.log").read_text("utf-8")
    local = re.findall(r"loopback HTTP only: (\d+) requests to \['127\.0\.0\.1:(\d+)'\]", browser)
    tests["browser"].update(requests=sum(int(count) for count, _ in local), ports=[int(port) for _, port in local])
    for mode, filename in (("extra", "boundary-result.json"), ("utf8", "corrupt-manifest-result.json")):
        for path in (OWN / ("pytest-" + mode)).rglob(filename):
            body = read(path)
            name = body.get("dimension") or body["operation"]
            target = INTAKE / "counterexamples" / (name + ".json")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
    for kind in ("root", "parent"):
        origin = OWN / "junction-fixtures" / kind / "result.json"
        (INTAKE / "counterexamples" / ("junction-" + kind + ".json")).write_bytes(origin.read_bytes())
    (INTAKE / "counterexamples/junction-creation.json").write_bytes((OWN / "junction-fixtures.json").read_bytes())
    screenshots = OUT / "screenshots"
    screenshots.mkdir(exist_ok=True)
    wanted = {"e2e-01-list-2000.png", "e2e-05-multi-condition.png", "e2e-07-variants.png"}
    for path in (OWN / "pytest-browser").rglob("*.png"):
        if path.name in wanted:
            (screenshots / path.name).write_bytes(path.read_bytes())
    snapshot = read(OWN / "export-manifest.json")
    changed = [row["path"] for row in snapshot
               if len((OWN / "runtime" / row["path"]).read_bytes()) != row["bytes"]
               or sha((OWN / "runtime" / row["path"]).read_bytes()) != row["sha256"]]
    before = read(OUT / "iqs-input-before.json")
    after = {relative: sha((IQS / relative).read_bytes()) for relative in before}
    assert before == after and not changed
    assert tests["core"].get("passed") == 96 and tests["extra"].get("passed") == 12
    assert tests["utf8"].get("failed") == 2 and tests["browser"].get("passed") == 11 and len(local) == 11
    save(OUT / "result.json", {"schema": "iqs_sw_remediation_acceptance/1", "status": "partial_verified_changes_requested",
         "result_commit": "c83c148af35407a5ae01072314ba9bd17e59b3d9",
         "received_head": "1831a73b37a3ed1b67d3556f6425ed2b52594a24", "checks": commands["checks"],
         "core": tests["core"], "original_12_boundaries": tests["extra"], "additional_utf8": tests["utf8"],
         "browser": tests["browser"], "snapshot_files": len(snapshot), "snapshot_changes_after_tests": changed,
         "iqs_input_files": len(before), "iqs_inputs_unchanged": before == after, "iqs_inputs_after": after,
         "remaining_code_findings": [{"id": "SR02-4B", "priority": "P2", "cases": 2,
             "summary": "Non-UTF8 foreign manifest interrupts public list/prune instead of being reported invalid/skipped"}],
         "paid_api_requests": 0, "keys_provided": 0, "source_repository_writes": 0,
         "production_database_reads_or_writes": 0, "cleanup_pending": True,
         "guard_limits": ["Python write and network audit; exact read-only Git and Playwright driver allowlist",
             "Browser routes abort external requests; disabled background networking and external DNS; not OS packet capture or full native-child isolation"],
         "open_items": ["R2 worker cleanup omitted per-file SHA/hardlink/strict-port audit; cannot reconstruct after deletion",
             "Old shared TEMP deletion attribution unproved; retention is possible explanation, not verified cause",
             "Artifact index note says all git hashes are result_commit, but 16 paths are absent and 11 differ there; all69 match received HEAD",
             "Existing multi-variant query-time selection unavailable; explicit single-variant positives seed separate workspaces",
             "Real owner identity/facts golden and QA joint flow missing/not_run; G3/F05/TH/IN/L03 stay open"]})
    print(json.dumps({"core_passed": 96, "old_boundaries_passed": 12, "new_failed": 2,
                      "browser_passed": 11, "loopback_requests": tests["browser"]["requests"],
                      "snapshot_unchanged": len(snapshot), "iqs_inputs_unchanged": len(before), "cleanup_pending": True}))


if __name__ == "__main__":
    main()
