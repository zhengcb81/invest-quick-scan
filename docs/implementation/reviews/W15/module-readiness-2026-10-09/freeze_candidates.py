"""Immutable W15 code checkpoint, excluding data copies and isolation helpers."""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

ROOT=Path(__file__).resolve().parents[5]
OWN=ROOT/"runs/w15a"
OUT=ROOT/"docs/implementation/intake/W15/module-readiness-2026-10-09"


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    label=sys.argv[1]
    assert label in {"01","02","03"}
    target=OUT/("candidate-source-"+label)
    index=OUT/("candidate-index-"+label+".json")
    assert not target.exists() and not index.exists()
    selections={"StockWiki":[],"StockQAbyLLM":[]}
    baselines={}
    for project,doc,private in (("StockWiki","stockwiki-input-01.json","sw"),("StockQAbyLLM","executor-input-01.json","qa")):
        frozen=json.loads((OUT/doc).read_bytes())
        rows=frozen["nonsecret_files"] if private=="sw" else frozen["artifacts"]
        baseline={r["path"]:r.get("execution_sha256",r.get("sha256")) for r in rows}
        baselines[project]=frozen.get("head",frozen.get("source_head"))
        for path in sorted((OWN/private).rglob("*")):
            if not path.is_file():continue
            name=path.relative_to(OWN/private).as_posix()
            admitted=name.startswith(("stockwiki/","tests/")) if private=="sw" else name.startswith(("src/","tests/")) or name in {"main_with_llm.py",".gitignore"}
            if not admitted:continue
            # Only Python/static wire schemas and exact gitignore are W15 source.
            if not (name.endswith((".py",".schema.json")) or name==".gitignore"):continue
            info=os.lstat(path)
            assert stat.S_ISREG(info.st_mode) and info.st_nlink==1 and not getattr(info,"st_file_attributes",0)&0x400
            raw=path.read_bytes()
            if sha(raw)==baseline.get(name):continue
            destination=target/project/name
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes(raw)
            selections[project].append(dict(path=name,bytes=len(raw),execution_sha256=sha(raw),baseline_execution_sha256=baseline.get(name)))
    selections["invest-quick-scan"]=[]
    for name in ("scripts/route_store_handoff.py","tests/test_route_store_handoff.py",
                 "schemas/quick_scan/route-store-validation.schema.json","schemas/quick_scan/route-store-cli.schema.json","schemas/quick_scan/module-refresh.schema.json"):
        raw=(ROOT/name).read_bytes()
        destination=target/"invest-quick-scan"/name
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(raw)
        selections["invest-quick-scan"].append(dict(path=name,bytes=len(raw),execution_sha256=sha(raw)))
    report=dict(protocol="iqs.w15_candidate_checkpoint/1.0.0",candidate_only=True,source_published=False,
                baselines=baselines,files=selections,real_metadata_archived=False,company_documents_archived=0,
                isolation_support_published=False,API_requests=0)
    index.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for project,rows in selections.items():
        print(json.dumps(dict(project=project,paths=[r["path"] for r in rows]),ensure_ascii=False))


if __name__=="__main__":main()
