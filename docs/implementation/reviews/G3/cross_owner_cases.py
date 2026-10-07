"""Public CLI cross-owner preflight; synthetic HTTP/identity, real import/store.

These checks are deliberately narrower than G3, X09 and real owner golden.
Only fixture setup and HTTP transport are substitutes, never package/import logic.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path

import pytest

OWN = Path(os.environ["IQS_CROSS_OWNER_ROOT"]).resolve()
QA = OWN / "qa-net01-intake-runtime" / "runtime"
SW = OWN / "sw-ready01-intake-runtime" / "runtime"


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PRODUCER = load("iqs_cross_producer", QA / "tests/integration/test_qa_net01_transport_e2e.py")
CONSUMER_FIXTURE = load("iqs_cross_consumer_fixture", SW / "tests/test_quick_scan_observations.py")


def produce(monkeypatch, root, capsys):
    root.mkdir()
    files = PRODUCER.setup(monkeypatch, root)
    code, session, models = PRODUCER.invoke(monkeypatch, root, files)
    output = capsys.readouterr()
    assert code == 0, output.out
    assert models == ["primary-model", "backup-model"]
    assert session.post.call_count == 2
    from src.utils.quick_scan_work_store import QuickScanWorkStore
    store = QuickScanWorkStore(root / "quick_scan_work.sqlite")
    item = store.find_work_items(entity_id=PRODUCER.CLI.UUID_ENTITY,
                                 question_ids=["IQS_01"])["IQS_01"][0]
    delivery = store.get_result_delivery(item["work_item_id"])
    assert delivery["state"] == "ready", delivery
    (root / "sealed-package.json").write_text(json.dumps(delivery["package"]), encoding="utf-8")
    return delivery["package"], files, store, item


def import_cli(package, root, capsys):
    from stockwiki.cli import main
    from stockwiki.paths import WorkspacePaths
    from stockwiki.quick_scan_store import QuickScanStore
    root.mkdir(exist_ok=True)
    identity = QuickScanStore(WorkspacePaths.from_root(root))
    identity.migrate()
    entity = CONSUMER_FIXTURE._seed_entity(PRODUCER.CLI.UUID_ENTITY)
    bindings = entity.pop("_bindings")
    identity.save_entity(entity, source_bindings=bindings)
    release = CONSUMER_FIXTURE._release()
    release["questions"]["IQS_01"] = {"field_id": "score.iqs_01", "scope": "entity",
                                      "response_kind": "score"}
    raw = root / "package.json"
    frozen = root / "release.json"
    raw.write_text(json.dumps(package), encoding="utf-8")
    frozen.write_text(json.dumps(release), encoding="utf-8")
    code = main(["--root", str(root), "observation-import", "--package", str(raw),
                 "--release", str(frozen)])
    output = capsys.readouterr()
    # The public CLI documents stdout for success, stderr for rejected input.
    lines = [json.loads(line) for line in (output.out + "\n" + output.err).splitlines()
             if line.startswith("{")]
    assert len(lines) == 1, output.out + output.err
    (root / "receipt.json").write_text(json.dumps(lines[0]), encoding="utf-8")
    return code, lines[0]


def test_producer_package_accepted_by_public_consumer(monkeypatch, tmp_path, capsys):
    package, _, _, _ = produce(monkeypatch, tmp_path / "qa", capsys)
    code, receipt = import_cli(package, tmp_path / "sw", capsys)
    assert code == 0, receipt
    assert receipt["summary"] == {"accepted": 1}, receipt


def test_generated_observation_preserves_comparable_metadata(monkeypatch, tmp_path, capsys):
    package, _, _, _ = produce(monkeypatch, tmp_path / "qa", capsys)
    observation = package["items"][0]["observation"]
    required = {"schema_version", "field_id", "question_version", "template_version",
                "method_id", "cohort", "information_cutoff", "run_id", "observed_at"}
    assert required <= set(observation), sorted(required - set(observation))
    assert observation["observed_at"] == observation["execution"]["answered_at"]
    assert observation["execution"]["model_resolved"] == "backup-model"


def test_independent_actual_attempts_do_not_share_observation_id(monkeypatch, tmp_path, capsys):
    first, _, _, _ = produce(monkeypatch, tmp_path / "first", capsys)
    second, _, _, _ = produce(monkeypatch, tmp_path / "second", capsys)
    a, b = first["items"][0]["observation"], second["items"][0]["observation"]
    assert a["execution"]["attempt_id"] != b["execution"]["attempt_id"]
    assert a["observation_id"] != b["observation_id"], "independent scans collide"


def test_rejected_consumer_ack_replays_without_an_observation(monkeypatch, tmp_path, capsys):
    package, _, _, _ = produce(monkeypatch, tmp_path / "qa", capsys)
    code, first = import_cli(package, tmp_path / "sw", capsys)
    again_code, again = import_cli(package, tmp_path / "sw", capsys)
    assert code == again_code == 0
    assert first["summary"] == again["summary"] == {"rejected": 1}
    assert first["acks"][0]["ack_id"] == again["acks"][0]["ack_id"]
    from stockwiki.paths import WorkspacePaths
    from stockwiki.quick_scan_observations import QuickScanObservationStore
    counts = QuickScanObservationStore(WorkspacePaths.from_root(tmp_path / "sw")).counts()
    assert counts["observations"] == 0, counts


def test_tampered_package_rejected_before_observation_write(monkeypatch, tmp_path, capsys):
    package, _, _, _ = produce(monkeypatch, tmp_path / "qa", capsys)
    changed = copy.deepcopy(package)
    changed["items"][0]["observation"]["answer"]["score"] = 9
    code, receipt = import_cli(changed, tmp_path / "sw", capsys)
    assert code == 2, receipt
    assert receipt["error_code"] == "package_hash_mismatch", receipt


def test_public_producer_warm_resume_keeps_package_with_zero_http(monkeypatch, tmp_path, capsys):
    package, files, store, item = produce(monkeypatch, tmp_path / "qa", capsys)
    attempts = store.list_attempts(item["work_item_id"])
    files["output"] = tmp_path / "qa" / "independent-warm-result.json"
    code, session, _ = PRODUCER.invoke(monkeypatch, tmp_path / "qa", files)
    captured = capsys.readouterr()
    assert code == 0, captured.out
    assert session.post.call_count == 0
    assert store.list_attempts(item["work_item_id"]) == attempts
    assert store.get_result_delivery(item["work_item_id"])["package"] == package
