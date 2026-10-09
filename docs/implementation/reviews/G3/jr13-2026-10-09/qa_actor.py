"""Thin test-only current binding adapter; never edits the production client.

Run only in a fresh guarded exported runtime. The unchanged historical actor
must be copied to OWN/legacy_qa_actor.py after its frozen hash is checked.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

OWN = Path(os.environ["E97_OWNED_ROOT"]).resolve()
spec = importlib.util.spec_from_file_location("joint108_qa_actor", OWN / "legacy_qa_actor.py")
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)


def inside(value):
    path = Path(value).resolve()
    if not path.is_relative_to(OWN):
        raise ValueError("test actor path outside the owned runtime")
    return path


def main(request):
    root = inside(request["root"])
    if request["op"] not in {"produce", "legacy-upgrade", "snapshot", "begin", "ack", "warm", "seal", "bind-consumer"}:
        raise ValueError("unsupported current QA test actor operation")
    if request["op"] == "ack":
        inside(request["ack"])
    if request["op"] != "bind-consumer":
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
        return legacy.main(request)
    descriptor_path = inside(request["receiver_descriptor"])
    raw = descriptor_path.read_bytes()
    descriptor = json.loads(raw)
    if (
        descriptor.get("schema_version") != "joint_receiver_fixture/1.0.0"
        or descriptor.get("synthetic_only") is not True
        or descriptor.get("basis") != "public QuickScanObservationStore.store_id"
        or set(descriptor.get("consumer", {})) != {"component", "namespace", "store_id"}
        or not inside(descriptor["workspace_root"]).is_dir()
    ):
        raise ValueError("receiver fixture descriptor is not the frozen owner input")
    # The receiving actor's descriptor is obtained BEFORE begin/send/ACK.
    # No incoming ACK is read or projected to learn the expected target.
    if not (root / "quick_scan_work.sqlite").is_file():
        raise ValueError("produce a real current CLI result before binding")
    store = legacy.QuickScanWorkStore(root / "quick_scan_work.sqlite")
    qid = request.get("question_id", "IQS_01")
    values = store.find_work_items(entity_id=legacy.fixture.base.ENTITY_ID, question_ids=[qid])
    if len(values.get(qid, [])) != 1:
        raise ValueError("ambiguous or missing fixture work item")
    item = values[qid][0]
    before = legacy.snapshot(store, item)
    digest = hashlib.sha256(raw).hexdigest()
    source_ref = "joint-receiver-fixture:" + descriptor_path.relative_to(OWN).as_posix() + ":sha256=" + digest
    binding = store.bind_result_delivery_consumer(item["work_item_id"], descriptor["consumer"], source_ref=source_ref)
    return {"binding": binding, "receiver_descriptor_sha256": digest,
            "before": before, "after": legacy.snapshot(store, store.get_item(item["work_item_id"])),
            "synthetic_only": True, "incoming_ack_used_as_authority": False}


if __name__ == "__main__":
    request = json.loads(inside(sys.argv[1]).read_bytes())
    result = main(request)
    inside(sys.argv[2]).write_text(json.dumps(result, ensure_ascii=False, default=lambda value:
        value.decode("utf-8") if isinstance(value, bytes) else str(value)), encoding="utf-8")
