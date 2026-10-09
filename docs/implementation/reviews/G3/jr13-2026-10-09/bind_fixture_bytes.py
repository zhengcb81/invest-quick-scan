"""Restore the fixture's independently frozen file-byte domain, no hash waiver."""
from pathlib import Path
import hashlib
import json

IQS=Path(__file__).resolve().parents[5]
OWN=IQS/"runs/r13a"
OUT=IQS/"docs/implementation/intake/G3/2026-10-09-jr13"

def main():
    output=OUT/"joint-dependency-03.json"
    assert not output.exists()
    fixtures=OWN/"qa/tests/fixtures"
    path=fixtures/"quick_scan_c06_manifest_v2_fixture.json"
    authority=json.loads((fixtures/"quick_scan_c06_authority_v2_fixture.json").read_bytes())
    raw=path.read_bytes()
    bound=raw.replace(b"\r\n",b"\n").replace(b"\n",b"\r\n")
    expected=authority["observation_context"]["manifest_file_sha256"]
    assert hashlib.sha256(bound).hexdigest()==expected
    assert json.loads(raw)==json.loads(bound)
    path.write_bytes(bound)
    record={"path":path.relative_to(OWN).as_posix(),"Git_blob_sha256":hashlib.sha256(raw).hexdigest(),
        "execution_file_sha256":expected,"basis":"existing independent fixture authority freezes the CRLF worktree bytes",
        "JSON_content_changed":False,"authority_changed":False,"product_changed":False,"real_API_calls":0}
    output.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    for folder in [OWN/"logs/joint-02",OWN/"cases/joint-02/a-selected"]:
        for item in folder.rglob("*"):
            if item.is_file() and (item.suffix in {".log", ".jsonl"} or item.name.endswith((".response.json",".process.json"))):
                target=OUT/"joint-02-detail"/item.relative_to(OWN)
                assert not target.exists()
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(item.read_bytes())
    print(json.dumps(record))

if __name__=='__main__':main()
