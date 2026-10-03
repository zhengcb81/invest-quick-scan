"""G1 offline verification: L01 receipt deep-check, light-asset scan, snapshot facts.

Read-only. Run:
  python -X utf8 g1_verify.py <stockqa_root> <iqs_root>
Emits a deterministic log to stdout. No network.
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

failures = []
checks = []


def check(name, ok, detail=None):
    checks.append((name, ok, detail))
    if not ok:
        failures.append(name)
    print(
        ("PASS" if ok else "FAIL")
        + " | "
        + name
        + (" | " + str(detail) if detail else "")
    )


def finding(name, detail=None):
    checks.append((name, "finding", detail))
    print("FINDING | " + name + (" | " + str(detail) if detail else ""))


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    stockqa = Path(sys.argv[1])
    iqs = Path(sys.argv[2])
    pilot = stockqa / "pilot_runs" / "l01_2026-10-02"

    print("== G1 offline verification ==")
    print("stockqa:", stockqa)
    print("iqs:", iqs)

    files = sorted(pilot.glob("company-*.json"))
    check("A0 pilot company files == 11", len(files) == 11, len(files))

    n_rec = 0
    coherent = 0
    hash_ok = 0
    cite_ok = 0
    executed = 0
    rids = set()
    webs = 0
    srcs = 0
    inv_files = 0
    info_dates = 0
    answers_total = 0
    score_dist = []
    statuses = {}
    max_desc = 0
    html_hits = 0
    cred_hits = 0
    prompt_hits = 0
    src_meta = False
    secret_re = re.compile(
        r"sk-[A-Za-z0-9]{16,}|api[_-]?key[\"']?\s*[:=]\s*[\"'][^\"'\s]{8,}"
    )
    body_re = re.compile(r"<html|<!doctype html|%PDF-|data:image/", re.I)

    for p in files:
        d = json.loads(p.read_text(encoding="utf-8"))
        inv_files += 1
        answers = d["answers"]
        receipts = d["execution_receipts"]
        for qid, r in receipts.items():
            n_rec += 1
            if (
                r.get("search_status") == "executed"
                and r.get("http_status_code") == 200
                and r.get("response_id")
            ):
                executed += 1
            if r.get("response_id"):
                rids.add(r["response_id"])
            w = r.get("web_search_calls") or []
            webs += len(w) if isinstance(w, list) else int(w)
            urls = r.get("source_urls") or []
            srcs += len(urls)
            attempts = r.get("attempts") or []
            attempt_urls = set()
            for a in attempts:
                attempt_urls.update(a.get("source_urls") or [])
                if (
                    a.get("source_titles")
                    or a.get("source_dates")
                    or a.get("published_date")
                ):
                    src_meta = True
            if r.get("source_titles") or r.get("source_dates"):
                src_meta = True
            if r.get("actual_model") == "MiniMax-M3":
                pass
            else:
                check(
                    "A4 model MiniMax-M3:" + p.name + ":" + qid,
                    False,
                    r.get("actual_model"),
                )
            a = answers.get(qid)
            answers_total += 1
            st = a.get("status")
            statuses[st] = statuses.get(st, 0) + 1
            sc = a.get("score")
            if st == "scored" and isinstance(sc, int):
                coherent += 1
                score_dist.append(sc)
            elif st == "unknown" and sc is None:
                coherent += 1
            # canonical binding
            canon = json.dumps(
                a, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            if hashlib.sha256(canon.encode("utf-8")).hexdigest() == r.get(
                "answer_sha256"
            ):
                hash_ok += 1
            # citations trace to executed search attempt urls
            acites = a.get("source_urls") or []
            if attempt_urls and all(u in attempt_urls for u in acites):
                cite_ok += 1
            if a.get("information_as_of") or a.get("published_date"):
                info_dates += 1
            desc = a.get("description") or ""
            max_desc = max(max_desc, len(desc))
            blob = json.dumps(d, ensure_ascii=False)
        blob = json.dumps(d, ensure_ascii=False)
        if body_re.search(blob):
            html_hits += 1
        if secret_re.search(blob):
            cred_hits += 1
        if "mock" in blob.lower() or "monkeypatch" in blob.lower():
            prompt_hits += 1

    check("A1 status<->score coherent 20/20", coherent == 20, coherent)
    check("A2 answer_sha256 canonical replay 20/20", hash_ok == 20, hash_ok)
    check(
        "A3 citations subset of executed attempt urls",
        cite_ok == answers_total,
        "%d/%d" % (cite_ok, answers_total),
    )
    check("A4 receipts executed+http200+response_id 20/20", executed == 20, executed)
    check("A5 distinct response_id == 20", len(rids) == 20, len(rids))
    check("A7 web searches == 41", webs == 41, webs)
    check("A7 source urls == 388", srcs == 388, srcs)
    if info_dates == answers_total:
        check("A8 info date fields populated", True, info_dates)
    else:
        finding(
            "A8 structured information dates unpopulated (information_as_of/published_date null)",
            "%d/%d populated; prose dates only; freshness contract allows null -> not-fresh fail-closed"
            % (info_dates, answers_total),
        )
    if not src_meta:
        finding(
            "A11 receipts persist source URLs but no source title/published_date",
            "stock-pool-design section2 save-set wants title+URL+date; only URLs in attempts/receipts",
        )
    check(
        "A9 status counts scored=18 unknown=2",
        statuses == {"scored": 18, "unknown": 2},
        statuses,
    )
    check(
        "A10 score dist matches report",
        sorted(score_dist) == [4, 5, 6, 7, 7, 7, 8, 8, 8, 8, 8, 9, 9, 9, 9, 9, 9, 9],
        sorted(score_dist),
    )
    check("B1 no html/pdf body patterns in pilot files", html_hits == 0, html_hits)
    check("B2 no credential-like strings in pilot files", cred_hits == 0, cred_hits)
    check(
        "B3 no mock/monkeypatch markers in pilot files", prompt_hits == 0, prompt_hits
    )
    check("B4 description bounded (max len < 4000)", max_desc < 4000, max_desc)

    # budget recount (independent of _fix_budget.py)
    invocations = len(
        json.loads((pilot / "run-log.json").read_text(encoding="utf-8"))["runs"]
    )
    check("A7 invocations == 11", invocations == 11, invocations)
    check("A7 primary requests == 20 == at cap", n_rec == 20 and n_rec <= 20, n_rec)

    # git facts
    def git(repo, *args):
        return subprocess.run(
            ["git", *args],
            cwd=str(repo),
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout

    head_sqa = git(stockqa, "rev-parse", "--short", "HEAD").strip()
    head_iqs = git(iqs, "rev-parse", "--short", "HEAD").strip()
    tracked = git(stockqa, "ls-files")
    tracked_paths = [l for l in tracked.splitlines() if l.strip()]
    root_llm = [l for l in tracked_paths if l == "llm_apis.json"]
    check(
        "C1 root llm_apis.json not tracked (template llm_apis.json.example is)",
        not root_llm,
        root_llm,
    )
    check(
        "C1b no tracked llm_apis.json with live key material (only .example allowed)",
        all(l.endswith(".example") for l in tracked_paths if "llm_apis" in l),
        [l for l in tracked_paths if "llm_apis" in l],
    )
    check(
        "C2 logs/ not tracked",
        not any(l.startswith("logs/") for l in tracked.splitlines()),
    )
    dirty = [l for l in git(stockqa, "status", "--porcelain").splitlines() if l.strip()]
    expected_untracked = {".codegraph/", ".workbuddy-ai/", "nul", "progress_update.txt"}
    actual_un = {l[3:] for l in dirty if l.startswith("??")}
    check(
        "C3 stockqa dirty == 4 expected kept untracked",
        actual_un == expected_untracked,
        sorted(actual_un),
    )

    # recorded review hashes (L01 review approved 2026-10-03)
    expected = {
        pilot
        / "pilot-report.md": "034c9d920967010b0d806c68e988af1bc201cb2b0c80db259689f0c686406a29",
        pilot
        / "run-log.json": "abecd559cc127a42b7714a0a508a3f7cdbbab6540f5eab217d4dd1ea2493e409",
        pilot
        / "_fix_budget.py": "6108cdca734aef230181f31108397cb8513ed1639f475f3b183d4951c9750539",
        iqs
        / "docs/implementation/reviews/L01-pilot-freeze-2026-10-02.json": "7e07998f447b817903a0d9969ad7b1f71dd4164d85d7aad3038e0b37c88fe100",
    }
    for p, h in expected.items():
        got = sha256_file(p)
        check("C4 hash matches L01 approved review: " + p.name, got == h, got[:16])

    # snapshot existence for REV-05 (L01/S02/Q05)
    check(
        "D1 receipt-S02.json exists",
        (iqs / "docs/implementation/contracts/receipt-S02.json").exists(),
    )
    check(
        "D2 Q02 MiniMax live E2E contract exists",
        (
            iqs
            / "docs/implementation/contracts/validation-Q02-MiniMax-live-E2E-2026-10-02.md"
        ).exists(),
    )
    check("D3 S06 closeout not required here (marker only)", True, "info")
    sqa_files = git(
        stockqa,
        "ls-files",
        "tests/unit/test_q05_content_boundary.py",
        "q04_handoff.json",
    )
    check(
        "D4 Q05 artifacts tracked",
        "test_q05_content_boundary.py" in sqa_files,
        repr(sqa_files[:80]),
    )

    print("== summary ==")
    print("checks:", len(checks), "failures:", len(failures))
    if failures:
        print("FAILED:", failures)
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    main()
