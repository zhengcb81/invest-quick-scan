"""Read-only independent binding of frozen engineering payload and native evidence."""
from contextlib import closing
from pathlib import Path
import hashlib
import json
import sqlite3
import xml.etree.ElementTree as ET

OWN = Path(__file__).resolve().parent
C = OWN.parent / "native-continuation-candidate"
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):
    return json.loads(path.read_text(encoding="utf8"))
cas = read(C / "candidate-cas.json")
assert len(cas["files"]) == 21
for item in cas["files"]:
    assert sha(Path(item["candidate_path"])) == item["candidate_sha256"], item["path"]
for item in cas["test_and_harness_files"]:
    assert sha(C / item["path"]) == item["sha256"], item["path"]
bindings = read(C / "evidence/p06-source-bindings.json")
counts = {}
for component, entries in bindings["components"].items():
    prefix = C / "runtime" / component
    if component in {"qa", "company", "bridge"}:
        prefix /= "src"
    elif component == "sw":
        prefix /= "stockwiki"
    counts[component] = len(entries)
    for entry in entries:
        assert entry["matches"] is True
        assert sha(prefix / entry["path"]) == entry["sha256"], (component, entry["path"])
assert sum(counts.values()) == 348
dbpath = C / "p06/test_native14_actual0_0/executor.sqlite"
before = sha(dbpath)
with closing(sqlite3.connect(dbpath.resolve().as_uri() + "?mode=ro", uri=True)) as db:
    db.execute("PRAGMA query_only=ON")
    assert db.execute("PRAGMA user_version").fetchone()[0] == 24
    tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    requested = ["work_item", "attempt", "quick_scan_budget_attempt", "quick_scan_owner_continuation_cell", "quick_scan_question_pack_send", "quick_scan_research_intent", "quick_scan_research_visible_output", "answer_checkpoint"]
    row_counts = {name: db.execute('SELECT COUNT(*) FROM "' + name + '"').fetchone()[0] for name in requested if name in tables}
    assert row_counts["work_item"] == 12
    assert row_counts["quick_scan_budget_attempt"] == 101
    assert row_counts["quick_scan_owner_continuation_cell"] == 1
    assert row_counts["quick_scan_question_pack_send"] == 1
    assert row_counts["quick_scan_research_intent"] == 1
    old = db.execute("SELECT status,actual_cost_micros,reconciled_at,reserved_cost_micros,in_flight FROM quick_scan_budget_attempt WHERE budget_attempt_id IN ('DISPATCH_legacy_unknown','DISPATCH_legacy_response') ORDER BY budget_attempt_id").fetchall()
    assert len(old) == 2 and all(x[1:4] == (None, None, 100000) for x in old)
    assert {x[0] for x in old} == {"outcome_uncertain", "response_unpriced"}
    assert sum(x[4] for x in old) == 1
assert sha(dbpath) == before
legacy = C.parents[2] / "runs/company-agent-owner-2026-10-15-01/execution/quick_scan_work.sqlite"
assert sha(legacy) == "79ae4b84e293a63c762025e326753d78d998e6a5a2d54b5d83245923f03ae85e"
results = {}
for name in ["u16.xml", "r12-0.xml", "r12-1.xml", "r12-2.xml", "p06.xml"]:
    suites = ET.parse(C / "evidence" / name).getroot()
    values = [suites] if suites.tag == "testsuite" else list(suites)
    results[name] = {key: sum(float(s.get(key, "0")) for s in values) for key in ["tests", "errors", "failures", "skipped", "time"]}
    assert results[name]["errors"] == results[name]["failures"] == 0
out = dict(protocol="iqs.independent_native_continuation_evidence/1.0.0", candidate_cas_sha256=sha(C / "candidate-cas.json"), exact_source_paths=21, source_binding_counts=counts, synthetic_native_row_counts=row_counts, original_two_unresolved_rows_preserved=True, synthetic_database_sha256=before, actual_legacy_source_sha256=sha(legacy), tests=results, all_reads_readonly=True, paid_calls=0, qualification="real original software with synthetic public fixture; separate actual legacy read-only migration evidence; not paid model/financial accuracy")
(OWN / "evidence-binding.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf8")
print(json.dumps({"source_paths":21,"original_source_bindings":348,"database_checks_passed":True,"tests":results}))
