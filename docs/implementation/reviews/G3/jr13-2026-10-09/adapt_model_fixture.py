"""A second synthetic run requests its own model before dispatch, no alias waiver."""
from pathlib import Path
import json

IQS=Path(__file__).resolve().parents[5]
OWN=IQS/"runs/r13a"
HERE=Path(__file__).resolve().parent
OUT=IQS/"docs/implementation/intake/G3/2026-10-09-jr13"

def main():
    target=HERE/"qa_actor.py"
    assert not target.exists()
    raw=(IQS/"docs/implementation/reviews/G3/joint-2026-10-09-rebase/qa_actor.py").read_text("utf-8")
    needle='    if request["op"] != "bind-consumer":\n        return legacy.main(request)'
    replacement='''    if request["op"] != "bind-consumer":
        if request["op"] == "produce" and request.get("model_resolved"):
            # Explicit pre-dispatch requested model in this independent fixture.
            # The old driver changed only HTTP returned model, correctly refused
            # by current Q10. Production matching/alias policy is not weakened.
            prepare = legacy.fixture._prepare_root
            def prepared(path):
                files = prepare(path)
                config_path = path / "llm_apis.json"
                config = json.loads(config_path.read_bytes())
                config["providers"]["openai"]["model"] = request["model_resolved"]
                config_path.write_text(json.dumps(config),encoding="utf-8")
                return files
            legacy.fixture._prepare_root = prepared
        return legacy.main(request)'''
    assert raw.count(needle)==1
    target.write_text(raw.replace(needle,replacement),encoding="utf-8")
    (OWN/"qa_actor.py").write_bytes(target.read_bytes())
    for folder in [OWN/"logs/joint-03",OWN/"cases/joint-03"]:
        for item in folder.rglob("*"):
            if item.is_file() and (item.suffix in {".log", ".jsonl"} or item.name.endswith((".request.json",".response.json",".process.json"))):
                destination=OUT/"joint-03-detail"/item.relative_to(OWN)
                assert not destination.exists()
                destination.parent.mkdir(parents=True,exist_ok=True)
                destination.write_bytes(item.read_bytes())
    (OUT/"joint-03"/"invalidation.json").write_text(json.dumps({"qualified":False,
        "pytest_result":"2 passed, 1 failed", "controller_exit":1,
        "cause":"source formatting ran before test process terminated; source hash guard invalidated batch",
        "test_failure":"independent model fixture changed only returned model; Q10 correctly refuses it",
        "resolution":"explicit requested model in second synthetic fixture before HTTP; freeze final sources and rerun"},indent=2)+"\n",encoding="utf-8")
    print('Historical third joint attempt retained; new synthetic model adapter prepared.')

if __name__=='__main__':main()
