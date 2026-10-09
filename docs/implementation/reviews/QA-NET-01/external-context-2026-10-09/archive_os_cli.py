"""Retain actual child logs/PIDs before final owned-root cleanup, no reruns."""
import hashlib
import json
from pathlib import Path

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/n111a"
OUT = IQS / "docs/implementation/intake/QA-NET-01/2026-10-09-external-context/verification"
LABELS = (
    "os-public-cold-first-01", "os-public-cold-red-02", "os-public-cold-green-01",
    "os-public-interruption-first-01", "os-public-recovery-affected-green-01",
)
# Config files, keys, provider bodies, databases and arbitrary temp files are
# deliberately absent. All allowed logs contain only this synthetic fixture.
NAMES = {
    "cold-stdout.log", "cold-stderr.log", "warm-stdout.log", "warm-stderr.log",
    "killed-stdout.log", "killed-stderr.log", "resumed-stdout.log", "resumed-stderr.log",
    "unknown-reopen-stdout.log", "unknown-reopen-stderr.log", "missing-key-stdout.log",
    "missing-key-stderr.log", "rejected-stdout.log", "rejected-stderr.log",
    "external-child-http.jsonl", "child-barrier.json", "termination.json", "key-opens.jsonl",
    "network-attempts.jsonl", "store-clock.txt", "result.json", "guard/sitecustomize.py",
}


def main():
    for label in LABELS:
        batch = OUT / label
        process = json.loads((batch / "process.json").read_text("utf-8"))
        assert not process["timeout"] and process["executed_source_unchanged"], label
        source = (OWN / "tmp" / label).resolve()
        assert source.is_relative_to(OWN.resolve()) and source.is_dir() and not source.is_symlink()
        target = batch / "subprocess"
        target.mkdir(exist_ok=False)
        cases = []
        for directory in sorted(source.iterdir()):
            if not directory.is_dir() or directory.is_symlink() or directory.name.endswith("current"):
                continue
            present = [(name, directory / name) for name in sorted(NAMES) if (directory / name).is_file()]
            if not present:
                continue
            number = len(cases)
            records = []
            for name, path in present:
                assert not path.is_symlink() and path.resolve().is_relative_to(source)
                raw = path.read_bytes()
                copied = target / f"{number:02d}" / name
                copied.parent.mkdir(parents=True, exist_ok=True)
                copied.write_bytes(raw)
                assert copied.read_bytes() == raw
                records.append({"path": copied.relative_to(batch).as_posix(), "source_name": name,
                    "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
            cases.append({"case_directory": directory.name, "records": records,
                "real_network_audit_file_present": "network-attempts.jsonl" in {name for name, _ in present}})
        index = {"schema_version": "1.0.0", "label": label, "synthetic_only": True,
            "not_financial_or_provider_interoperability_evidence": True,
            "process_sha256": hashlib.sha256((batch / "process.json").read_bytes()).hexdigest(), "cases": cases}
        (target / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"label": label, "case_logs": len(cases),
            "artifacts": sum(len(case["records"]) for case in cases)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
