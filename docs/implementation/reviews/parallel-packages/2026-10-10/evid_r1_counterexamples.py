"""Discriminating R1 cases. Originals remain immutable; fixtures are synthetic.

Full native CLI controls use a separately labelled relocation lock whose
original input bytes were checked before copying. No guard is monkeypatched.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from iqs_evidence_lab.reference.compare import compare_item, normalize_answer
from iqs_evidence_lab.reference.pack import compute_pack_id

LAB = Path.cwd()
WORK = LAB.parent
IQS = Path(os.environ["IQS_ROOT"])
MIRROR = WORK / "iqs"
CASES = LAB / ".acceptance-cases"
PACK_PATH = CASES / "reference-pack-relocated-1.1.json"
OUTPUTS = LAB / "docs/handoff/EVID-REF-02/remediation-01/generated"
RESULTS = []
CALLS = []


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def call(name, args, *, relocated=True):
    env = dict(os.environ)
    if relocated:
        env.update(IQS_ROOT=str(MIRROR), IQS_EVIDENCE_LAB_IQS_ROOT=str(MIRROR))
    command = [sys.executable, "-B", "-X", "utf8", "tools/reference_entry.py", *args]
    proc = subprocess.run(command, cwd=LAB, env=env, capture_output=True,
                          text=True, encoding="utf-8", timeout=150)
    out = CASES / "cli-logs"
    out.mkdir(exist_ok=True)
    (out / (name + ".stdout.log")).write_text(proc.stdout, encoding="utf-8")
    (out / (name + ".stderr.log")).write_text(proc.stderr, encoding="utf-8")
    result = {"name": name, "command": command, "exit_code": proc.returncode,
              "stderr": proc.stderr, "relocated_input_fixture": relocated}
    put(out / (name + ".result.json"), result)
    CALLS.append(result)
    return result


def record(name, expected, observed, reproduced, *, control=False):
    RESULTS.append({"case_id": name, "expected": expected, "observed": observed,
                    "finding_reproduced": bool(reproduced), "control": control})


def changed_pack(name, mutator):
    p = copy.deepcopy(PACK)
    mutator(p)
    p["pack_id"] = compute_pack_id(p)
    path = CASES / (name + ".pack.json")
    put(path, p)
    return p, path


def dims(r, raw, *, sources=None):
    answer = normalize_answer(raw)
    result, _, _ = compare_item(r, answer, r["company_key"], r["company_key"], sources or SOURCES, [])
    return result


def answer_index(name, doc):
    path = CASES / (name + ".answers.json")
    sha = put(path, doc)
    index = copy.deepcopy(INDEX)
    entry = copy.deepcopy(index["sets"][0])
    entry.update(root="lab", path=path.relative_to(LAB).as_posix(), sha256=sha,
                 source_category="synthetic", set_id=name)
    index["sets"] = [entry]
    target = CASES / (name + ".index.json")
    put(target, index)
    return target


def evaluate(name, doc):
    index = answer_index(name, doc)
    output = OUTPUTS / ("accept-" + name)
    result = call(name, ["evaluate", "--pack", str(PACK_PATH), "--answers", str(index), "--output", str(output)])
    ev = load(output / "evaluation.json") if result["exit_code"] == 0 else None
    return result, ev


PACK = load(PACK_PATH)
RECS = {r["record_id"]: r for r in PACK["records"]}
SOURCES = {s["source_id"]: s for s in PACK["source_refs"]}
INDEX = load(LAB / "fixtures/reference/answers-index.json")
ENTRY = INDEX["sets"][0]
DOCUMENT = load(MIRROR / ENTRY["path"])
REQUESTED = list(DOCUMENT["question_ids"])
FACT = {"question_id": "F01", "status": "answered", "value": 166.77, "unit": "CNY_billion",
        "period": "2024-H1", "scope": "consolidated", "reporting_basis": "as_disclosed",
        "listing": "300750", "rationale": "CATL 2024年半年报披露营收166.77 billion yuan。"}

original = call("original-relocation-control", ["validate", "--pack", str(LAB / "fixtures/reference/reference-pack-1.1.json")], relocated=False)
record("ER-R1-portability", "original public CLI should work in an exact-byte isolated copy, or have an explicit checked relocation mechanism",
       original, original["exit_code"] == 2 and "not covered by the batch lock" in original["stderr"])
control = call("derived-native-control", ["validate", "--pack", str(PACK_PATH)])
record("CONTROL-derived-native", "synthetic relocated lock retains all verified input bytes; native validation exit0",
       control, control["exit_code"] != 0, control=True)
if control["exit_code"]:
    put(CASES / "results.json", {"results": RESULTS, "calls": CALLS, "controller_error": "positive native control failed"})
    raise SystemExit(1)

normal = dims(RECS["REC-catl-F01"], FACT)
record("CONTROL-text-numeric", "real scalar/rationale mechanics still supported", normal,
       normal["numeric"]["accuracy"] != "supported" or normal["text"]["accuracy"] != "supported", control=True)
for name, rationale in (("ER-R1-text-empty-claim", "2024。billion。"),
                        ("ER-R1-text-wrong-metric", "2024年利润为166.77 billion yuan。")):
    x = dims(RECS["REC-catl-F01"], {**FACT, "rationale": rationale})["text"]
    record(name, "no semantic revenue assertion; must not grant text accuracy supported", x, x["accuracy"] == "supported")

unknown = {**FACT, "status": "unknown"}
x = dims(RECS["REC-catl-F01"], unknown)["numeric"]
record("ER-R1-unknown-residual-value", "reject contradictory unknown/value or never count as correct", x, x["accuracy"] == "supported")
score_unknown = dims(RECS["REC-alphabet-IQS_05"], {"question_id": "IQS_05", "status": "insufficient_evidence", "score": 8})["score_basis"]
record("ER-R1-unknown-residual-score", "insufficient_evidence must never grant score accuracy supported", score_unknown, score_unknown["accuracy"] == "supported")
abstain = dims(RECS["REC-catl-F06"], {"question_id": "F06", "status": "unknown", "value": None, "rationale": ""})["numeric"]
record("CONTROL-compliant-abstention", "unknown without a value retains compliant abstention and is not accurate", abstain, abstain["accuracy"] == "supported", control=True)
doc = copy.deepcopy(DOCUMENT)
next(r for r in doc["answers"] if r["question_id"] == "F01").update(unknown)
native, ev = evaluate("unknown-native", doc)
item = next(i for i in ev["items"] if i["question_id"] == "F01") if ev else None
record("ER-R1-unknown-native-denominator", "unknown remains counted, but cannot be counted as numeric correct",
       {"cli": native, "denominator": ev["denominator"] if ev else None, "item": item},
       ev is not None and ev["denominator"]["unknown_total"] >= 1 and item["dimensions"]["numeric"]["accuracy"] == "supported")

def capital(p):
    r = next(r for r in p["records"] if r["record_id"] == "REC-alphabet-IQS_10")
    r["claim"]["definition"] = "Operating performance"
    r["score_support"]["candidate_range"] = {"min": 4, "max": 9}
    r["score_support"]["candidate_range_basis"] = copy.deepcopy(RECS["REC-alphabet-IQS_05"]["score_support"]["candidate_range_basis"])
p, path = changed_pack("capital-definition", capital)
native = call("capital-definition", ["validate", "--pack", str(path)])
r = next(r for r in p["records"] if r["record_id"] == "REC-alphabet-IQS_10")
x = dims(r, {"question_id": "IQS_10", "status": "scored", "score": 8})["score_basis"]
record("ER-R1-capital-definition-bypass", "frozen capital-return question cannot become scoreable by renaming definition; ROIC/WACC gap retained",
       {"cli": native, "missing": r["score_support"]["missing"], "dimension": x}, native["exit_code"] == 0 and x["accuracy"] == "supported")

def endpoint(p):
    r = next(r for r in p["records"] if r["record_id"] == "REC-alphabet-IQS_05")
    for v in r["score_support"]["candidate_range_basis"].values():
        v["source_ids"] = ["SRC-9999"]
p, path = changed_pack("endpoint-unclosed", endpoint)
native = call("endpoint-unclosed", ["validate", "--pack", str(path)])
r = next(r for r in p["records"] if r["record_id"] == "REC-alphabet-IQS_05")
x = dims(r, {"question_id": "IQS_05", "status": "scored", "score": 8})["score_basis"]
record("ER-R1-endpoint-source-closure", "reject nonexistent endpoint source with target constraint exit4, never grant accuracy", {"cli": native, "dimension": x}, native["exit_code"] == 0 and x["accuracy"] == "supported")

def missing_qualification(p):
    r = next(r for r in p["records"] if r["record_id"] == "REC-catl-F01")
    r["qualification"]["source_checked"].update(recorded_at=None, actor=None, ref=None)
p, path = changed_pack("qualification-no-record", missing_qualification)
native = call("qualification-no-record", ["validate", "--pack", str(path)])
r = next(r for r in p["records"] if r["record_id"] == "REC-catl-F01")
x = dims(r, FACT)["numeric"]
record("ER-R1-passed-label-without-record", "source_checked passed requires traceable evidence; string alone cannot grant accuracy", {"cli": native, "dimension": x}, native["exit_code"] == 0 and x["accuracy"] == "supported")

missing = copy.deepcopy(DOCUMENT)
missing["answers"] = [r for r in missing["answers"] if r["question_id"] != "F02"]
native, ev = evaluate("missing-explicit-control", missing)
record("CONTROL-missing-explicit-request", "six requested includes missing F02", {"cli": native, "denominator": ev["denominator"] if ev else None},
       ev is None or ev["denominator"]["requested_total"] != 6 or ev["denominator"]["missing_total"] != 1, control=True)
missing.pop("question_ids")
native, ev = evaluate("missing-fallback", missing)
record("ER-R1-request-fallback-shrinks", "no declared request must not redefine six frozen requested questions as five answers", {"cli": native, "denominator": ev["denominator"] if ev else None},
       ev is not None and ev["denominator"]["requested_total"] == 5 and ev["denominator"]["missing_total"] == 0)

legacy = CASES / "legacy-evaluation.json"
out = OUTPUTS / "accept-legacy-summary"
native = call("legacy-summary", ["summarize", "--evaluation", str(legacy), "--output", str(out)])
summary = load(out / "evaluation-summary.json") if native["exit_code"] == 0 else None
record("ER-R1-legacy-promotes-accuracy", "old mechanical consistency must remain readable without becoming qualified accuracy",
       {"cli": native, "schema": summary["schema"] if summary else None, "denominator": summary["denominator"] if summary else None},
       summary is not None and summary["denominator"]["accuracy_run_counts"]["numeric"]["supported"] == 102)

# A true Windows junction points only at another directory owned by this run.
# The observation records target writes, and removes the junction itself before
# any recursive cleanup. Never descend a junction during enumeration.
staging = LAB / ".temp-roots"
assert staging.is_dir() and not list(staging.iterdir()), "staging root not empty; do not alter it"
staging.rmdir()
target = WORK / "junction-target"
target.mkdir()
sentinel = target / "sentinel.txt"
sentinel.write_text("OWNED_UNCHANGED_SENTINEL\n", encoding="utf-8")
sentinel_sha = hashlib.sha256(sentinel.read_bytes()).hexdigest()
# Pass literal verified owned paths through environment rather than shell code.
env = dict(os.environ, IQS_TEST_JUNCTION=str(staging), IQS_TEST_TARGET=str(target))
command = ["powershell", "-NoProfile", "-Command", "$ErrorActionPreference='Stop'; New-Item -ItemType Junction -Path $env:IQS_TEST_JUNCTION -Target $env:IQS_TEST_TARGET | Out-Null"]
made = subprocess.run(command, env=env, capture_output=True, text=True, timeout=30)
if made.returncode:
    record("ER-R1-staging-junction", "must reject before writing through staging ancestor", {"junction_create_exit": made.returncode, "stderr": made.stderr}, False)
    staging.mkdir()
else:
    assert staging.lstat().st_file_attributes & 0x400 and staging.resolve() == target.resolve()
    try:
        out = OUTPUTS / "accept-staging-junction"
        native = call("staging-junction", ["summarize", "--evaluation", str(legacy), "--output", str(out)])
        names = sorted(p.name for p in target.iterdir())
        record("ER-R1-staging-junction", "exit3 before mkdir/write under staging junction", {"cli": native, "remaining_target_entries": names,
               "sentinel_unchanged": hashlib.sha256(sentinel.read_bytes()).hexdigest() == sentinel_sha, "output_exists": out.exists()},
               native["exit_code"] == 0 and out.exists())
    finally:
        os.rmdir(staging)  # Remove the reparse object only, never its target.
        assert target.is_dir() and hashlib.sha256(sentinel.read_bytes()).hexdigest() == sentinel_sha
        staging.mkdir()

value = {"results": RESULTS, "calls": CALLS, "controller_error": False,
         "synthetic_inputs_only": True, "original_product_written": False,
         "network_calls": 0, "paid_calls": 0}
put(CASES / "results.json", value)
print(json.dumps({"cases": len(RESULTS), "findings_reproduced": [r["case_id"] for r in RESULTS if r["finding_reproduced"] and not r["control"]],
                  "failed_controls": [r["case_id"] for r in RESULTS if r["finding_reproduced"] and r["control"]]}, ensure_ascii=False))
if any(r["finding_reproduced"] for r in RESULTS if r["control"]):
    raise SystemExit(1)
