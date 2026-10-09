"""Retain existing test-only actor bytes not reached by failed controllers."""
from pathlib import Path
import hashlib
import json

IQS = Path(__file__).resolve().parents[5]
OWN = IQS / "runs/r13a"
OUT = IQS / "docs/implementation/intake/G3/2026-10-09-jr13"
from freeze_final import owned_bytes

def main():
    index = OUT / "residual-actor-index.json"
    assert not index.exists()
    records = []
    labels = ["joint-" + str(i).zfill(2) for i in range(1, 8)]
    for label in labels:
        for folder in [OWN / "cases" / label, OWN / "logs" / label]:
            if not folder.exists():
                continue
            for source in sorted(folder.rglob("*")):
                if not source.is_file():
                    continue
                if not (source.suffix in {".log", ".jsonl"} or source.name.endswith(
                    (".request.json", ".response.json", ".process.json"))):
                    continue
                raw = owned_bytes(source)
                dest = OUT / label / "actors" / source.relative_to(OWN)
                existed = dest.exists()
                if existed:
                    assert dest.read_bytes() == raw
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(raw)
                records.append(dict(path=dest.relative_to(OUT).as_posix(), bytes=len(raw),
                                    sha256=hashlib.sha256(raw).hexdigest(), already_archived=existed))
    index.write_text(json.dumps(dict(schema="jr13-existing-actor-archive/1", records=records,
        scope="Original actor bytes only; missing historical process metadata is not reconstructed",
        real_API_calls=0), indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(records=len(records), newly_archived=sum(not x["already_archived"] for x in records))))

if __name__ == "__main__":
    main()
