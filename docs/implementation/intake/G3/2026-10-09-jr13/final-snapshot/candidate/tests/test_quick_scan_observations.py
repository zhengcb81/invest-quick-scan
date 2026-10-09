"""W05 observation import tests.

Binds acceptance cases DB-02, DB-03, DB-06, SC-05, SC-06, STORE-01,
STORE-02, ID-17 and ID-23 (IQS tasks.json W05). Producer-side package bytes
are simulated only at the external boundary (test helper computes the
C06 canonical hashes); the frozen official fixture under
``tests/fixtures/`` provides an independent hash vector so verification is
not self-certified. No test reaches the network or an LLM — static source
checks enforce that both modules stay offline and append-only.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import socket
import sqlite3
from pathlib import Path

import pytest

from stockwiki.cli_registry import build_parser
from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_import import (
    ImportValidationError,
    canonical_sha256,
    import_package,
    parse_package,
    verify_package_integrity,
)
from stockwiki.quick_scan_observations import (
    ObservationImportError,
    QuickScanObservationStore,
)
from stockwiki.quick_scan_store import QuickScanStore


def test_jr13_audit_insert_failure_rolls_back_observation_and_ack(tmp_path, monkeypatch):
    _no_network(monkeypatch)
    store, identity = _workspace(tmp_path)
    with sqlite3.connect(store.database_path) as con:
        con.execute("""CREATE TRIGGER reject_audit BEFORE INSERT ON quick_scan_import_audit
            BEGIN SELECT RAISE(ABORT, 'synthetic audit write failure'); END""")
    obs = _jr13_obs()
    package = _package([obs])
    with pytest.raises(ObservationImportError) as error:
        import_package(store, package, frozen_release=_release(), identity_store=identity)
    assert error.value.error_code == "observation_integrity_error"
    assert store.get_observation(obs["observation_id"]) is None
    assert store.ack_for(package["package_id"], package["items"][0]["item_id"]) is None
    assert store.import_audit_for(package["package_id"], package["items"][0]["item_id"]) is None
    assert all(value == 0 for value in store.counts().values())


FIXTURE_PACKAGE = Path(__file__).parent / "fixtures" / "quick_scan_exchange_example.json"
SEMANTIC = "a" * 64
DEFINITION = "d" * 64


def _no_network(monkeypatch) -> None:
    def _bomb(*args, **kwargs):
        raise AssertionError("network call attempted from observation import")

    monkeypatch.setattr(socket, "socket", _bomb)
    monkeypatch.setattr(socket, "create_connection", _bomb)


def _release() -> dict:
    return {
        "module_package_id": "modpkg_fixture_0001",
        "release_id": "rel_fixture_1",
        "catalog_version": "3.0.0",
        "semantic_fingerprint_version": "2.0.0",
        "questions": {
            "IQS_LEG": {
                "field_id": "score.iqs_01",
                "scope": "entity",
                "response_kind": "score",
            },
            "IQS_PUB": {
                "field_id": "score.iqs_05",
                "scope": "entity",
                "response_kind": "score",
                "rubric_version": "1.0.0",
                "construct_id": "IQS_05",
                "definition_sha256": DEFINITION,
                "semantic_sha256": SEMANTIC,
            },
            "FACT_10": {
                "field_id": "facts.customers",
                "scope": "entity",
                "response_kind": "fact",
            },
            "SEC_Q": {
                "field_id": "quote.price",
                "scope": "security",
                "response_kind": "score",
            },
        },
    }


def _seed_entity(entity_id: str, *, tickers: list[str] | None = None) -> dict:
    tickers = tickers or ["600000"]
    securities = []
    bindings = []
    for index, ticker in enumerate(tickers):
        market = "CN-A" if index == 0 else "HK"
        security_id = f"SEC_{entity_id}_{index}"
        binding_ref = f"BIND_{entity_id}_{index}"
        securities.append(
            {
                "security_id": security_id,
                "entity_id": entity_id,
                "market": market,
                "exchange_raw": "",
                "exchange": "",
                "ticker": ticker,
                "currency": "CNY" if market == "CN-A" else "HKD",
                "security_type": "ordinary",
                "listing_status": "active",
                "source_binding_ref": binding_ref,
                "adr_ratio": None,
                "ordinary_security_ref": None,
            }
        )
        bindings.append(
            {
                "binding_ref": binding_ref,
                "source_namespace": "fixture-master",
                "source_record_id": f"row:{entity_id}:{index}",
                "source_canonical_name": f"Fixture {entity_id}",
                "security_id": security_id,
                "entity_id": entity_id,
                "market": market,
                "exchange_raw": "",
                "ticker": ticker,
                "status": "active",
            }
        )
    return {
        "identity_schema_version": "2.0.0",
        "identity_state": "provisional",
        "identity_revision": 1,
        "entity_id": entity_id,
        "canonical_name": f"Fixture {entity_id}",
        "incorporation_country": None,
        "scope_attestation_id": f"SCOPE_{entity_id}",
        "verified_issuer_receipt_id": None,
        "company_wiki_ref": None,
        "formal_stockwiki_profile": None,
        "securities": securities,
        "segments": [],
        "_bindings": bindings,
    }


def _observation(
    observation_id: str,
    *,
    entity_id: str = "E01",
    question_id: str = "IQS_LEG",
    request_id: str = "REQ_1",
    attempt_id: str = "ATT_1",
    score: int | None = 8,
    status: str = "scored",
    response_kind: str = "score",
    field_id: str = "score.iqs_01",
    security_id: str | None = None,
    listing_id: str | None = None,
    extra: dict | None = None,
    answer_extra: dict | None = None,
    published: bool = False,
) -> dict:
    # This shared helper is also consumed by backup tests with old labels.
    # Normalize synthetic fixture addresses, never product/company identity.
    if not re.fullmatch(r"obs_[a-f0-9]{64}", observation_id):
        observation_id = "obs_" + hashlib.sha256(observation_id.encode()).hexdigest()
    observation = {
        "schema_version": "1.1.0" if published else "1.0.0",
        "entity_id": entity_id,
        "security_id": security_id,
        "segment_id": None,
        "field_id": field_id,
        "construct_id": "IQS_05" if published else None,
        "question_id": question_id,
        "question_version": "1.0.0" if not published else "1.0.0",
        "template_version": "3.0.0",
        "method_id": (
            f"module-locked-v1/core-constructs-v1/{DEFINITION[:16]}/{SEMANTIC[:16]}"
            if published
            else "core-constructs-v1/context-1/fixture"
        ),
        "scope": "security" if security_id else "entity",
        "cohort": {
            "company_type": "operating",
            "industries": ["industrial"],
            "stage": "mature",
            "subtype": None,
        },
        "information_cutoff": "2026-09-30",
        "run_id": f"RUN_{request_id}",
        "scan_id": f"SCAN_{request_id}",
        "inputset_id": "INPUT_V1",
        "task_mode": "single",
        "comparison_group_id": None,
        "observed_at": "2026-10-01T09:01:00Z",
        "execution": {
            "provider": "fixture_provider",
            "model_requested": "fixture-model",
            "model_resolved": "fixture-model",
            "model_revision": "fixture-1",
            "request_id": request_id,
            "attempt_id": attempt_id,
            "started_at": "2026-10-01T09:00:00Z",
            "answered_at": "2026-10-01T09:01:00Z",
            "search_status": "executed",
            "search_receipt_id": "FIXTURE_NOT_SEARCH_PROOF",
            "prompt_sha256": "b" * 64,
        },
        "answer": {
            "question_id": question_id,
            "response_kind": response_kind,
            "status": status,
            "score": score,
            "summary": "fixture summary",
        },
        "evidence_review_status": "unreviewed",
        "observation_id": observation_id,
    }
    if listing_id:
        observation["listing_id"] = listing_id
    if published:
        observation["module_package_id"] = "modpkg_fixture_0001"
        observation["module_release_id"] = "rel_fixture_1"
        observation["question_definition_sha256"] = DEFINITION
        observation["question_semantic_sha256"] = SEMANTIC
        observation["cycle_sensitive"] = False
    if extra:
        observation.update(extra)
    if answer_extra:
        observation["answer"].update(answer_extra)
    return observation


def _package(observations: list[dict], *, producer: str = "StockQAbyLLM") -> dict:
    items = []
    for observation in observations:
        payload_hash = canonical_sha256(observation)
        item_id = "itm_" + canonical_sha256(
            {"observation_id": observation["observation_id"], "payload_sha256": payload_hash}
        )
        items.append(
            {
                "item_id": item_id,
                "observation_id": observation["observation_id"],
                "payload_sha256": payload_hash,
                "observation": observation,
            }
        )
    package = {
        "schema_version": "1.0.0",
        "producer": {
            "component": producer,
            "component_version": "fixture",
            "build_id": "FIXTURE",
        },
        "consumer": {
            "component": "StockWiki",
            "namespace": "quick_scan",
            "minimum_schema_version": "1.0.0",
        },
        "created_at": "2026-10-01T10:00:00Z",
        "data_class": "lightweight_screening",
        "required_capabilities": ["entity_security_identity_v1", "standard_observation_v1"],
        "contract_versions": {
            "identity_schema": "1.0.0",
            "answer_schema": "standard-1",
            "observation_schema": "1.0.0",
            "question_catalog": "3.0.0",
            "model_policy_schema": "2.0.0",
        },
        "document_payloads_included": False,
        "items": items,
        "extensions": [],
    }
    package_hash = canonical_sha256(package)
    package["package_sha256"] = package_hash
    package["package_id"] = "pkg_" + package_hash
    return package


def _workspace(tmp_path: Path) -> tuple[QuickScanObservationStore, QuickScanStore]:
    paths = WorkspacePaths.from_root(tmp_path)
    obs_store = QuickScanObservationStore(paths)
    obs_store.migrate()
    identity = QuickScanStore(paths)
    identity.migrate()
    for entity in (_seed_entity("E01"), _seed_entity("E10", tickers=["600519", "0700"])):
        bindings = entity.pop("_bindings")
        identity.save_entity(entity, source_bindings=bindings)
    return obs_store, identity


def test_official_fixture_vector_verifies(monkeypatch) -> None:
    _no_network(monkeypatch)
    package = parse_package(FIXTURE_PACKAGE.read_text(encoding="utf-8"))
    verify_package_integrity(package)
    item = package["items"][0]
    assert item["payload_sha256"] == canonical_sha256(item["observation"])
    tampered = copy.deepcopy(package)
    tampered["items"][0]["observation"]["answer"]["score"] = 9
    with pytest.raises(ImportValidationError) as exc:
        verify_package_integrity(tampered)
    assert exc.value.error_code == "package_hash_mismatch"


def test_db_02_same_package_twice_is_idempotent(tmp_path, monkeypatch) -> None:
    _no_network(monkeypatch)
    obs_store, identity = _workspace(tmp_path)
    package = _package(
        [
            _observation(
                "obs_596428cb7cb4c1a8f3baaa88801c571cc3626d546f27e5b7433d6a8d1ff7787d",
                request_id="REQ_A",
                attempt_id="ATT_A",
            ),
            _observation(
                "obs_f0af320642c5d4a4270cf11dca07727e6d8f43fcad7c6afd9c478993bb42a3ac",
                request_id="REQ_B",
                attempt_id="ATT_B",
                score=7,
            ),
        ]
    )
    raw = json.dumps(package, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    first = import_package(obs_store, raw, frozen_release=_release(), identity_store=identity)
    assert first["summary"] == {"accepted": 2}
    second = import_package(obs_store, raw, frozen_release=_release(), identity_store=identity)
    assert second["acks"][0]["ack_id"] == first["acks"][0]["ack_id"]
    assert (
        obs_store.import_audit_for(second["acks"][0]["package_id"], second["acks"][0]["item_id"])[
            "ack_sequence"
        ]
        == obs_store.import_audit_for(first["acks"][0]["package_id"], first["acks"][0]["item_id"])[
            "ack_sequence"
        ]
    )
    counts = obs_store.counts()
    assert counts["observations"] == 2
    assert counts["acked_items"] == 2
    stored = obs_store.get_observation(
        "obs_596428cb7cb4c1a8f3baaa88801c571cc3626d546f27e5b7433d6a8d1ff7787d"
    )
    assert stored["observed_at"] == "2026-10-01T09:01:00Z"
    assert stored["reported_score"] == 8

    replay = _package(
        [
            _observation(
                "obs_596428cb7cb4c1a8f3baaa88801c571cc3626d546f27e5b7433d6a8d1ff7787d",
                request_id="REQ_A",
                attempt_id="ATT_A",
            ),
        ]
    )
    replay["created_at"] = "2026-10-01T11:00:00Z"
    replay_hash = canonical_sha256(
        {k: v for k, v in replay.items() if k not in {"package_id", "package_sha256"}}
    )
    replay["package_sha256"] = replay_hash
    replay["package_id"] = "pkg_" + replay_hash
    third = import_package(obs_store, replay, frozen_release=_release(), identity_store=identity)
    assert third["summary"] == {"already_present": 1}
    ack = third["acks"][0]
    assert (
        obs_store.import_audit_for(ack["package_id"], ack["item_id"])["original_import"][
            "package_id"
        ]
        == package["package_id"]
    )
    assert obs_store.counts()["observations"] == 2


def test_db_03_conflicts_rejected_and_execution_key_isolation(tmp_path, monkeypatch) -> None:
    _no_network(monkeypatch)
    obs_store, identity = _workspace(tmp_path)
    original = _observation(
        "obs_7f914d4679f16717c78f388b47b06a630a10c924ebb6fcf173eb4874e040b311",
        request_id="REQ_C",
        attempt_id="ATT_C",
    )
    accepted = import_package(
        obs_store, _package([original]), frozen_release=_release(), identity_store=identity
    )
    assert accepted["summary"] == {"accepted": 1}

    forged = copy.deepcopy(original)
    forged["answer"]["score"] = 3
    conflict = import_package(
        obs_store,
        _package([forged]),
        frozen_release=_release(),
        identity_store=identity,
    )
    assert conflict["summary"] == {"conflict": 1}
    assert _jr13_internal_codes(obs_store, conflict)[0] == "immutable_key_hash_conflict"
    stored = obs_store.get_observation(
        "obs_7f914d4679f16717c78f388b47b06a630a10c924ebb6fcf173eb4874e040b311"
    )
    assert stored["reported_score"] == 8
    conflicts = obs_store.list_conflicts()
    assert conflicts[-1]["conflict_kind"] == "immutable_key_hash_conflict"

    missing_entity = _observation(
        "obs_d8c8795aad33efca97a782e6008e3a75ffdc133c9d4e32adcff7ef49f3e2d15e",
        entity_id="E99",
        request_id="REQ_D",
        attempt_id="ATT_D",
    )
    rejected = import_package(
        obs_store,
        _package([missing_entity]),
        frozen_release=_release(),
        identity_store=identity,
    )
    assert rejected["summary"] == {"rejected": 1}
    assert _jr13_internal_codes(obs_store, rejected)[0] == "entity_not_found"
    assert (
        obs_store.get_observation(
            "obs_d8c8795aad33efca97a782e6008e3a75ffdc133c9d4e32adcff7ef49f3e2d15e"
        )
        is None
    )

    unknown_question = _observation(
        "obs_b700e4f5dc775127ddb31f5ccfc13bffcc7d9abc6e621a486564a2d3856e7ee4",
        question_id="IQS_GHOST",
        field_id="score.ghost",
        request_id="REQ_E",
        attempt_id="ATT_E",
    )
    unknown = import_package(
        obs_store,
        _package([unknown_question]),
        frozen_release=_release(),
        identity_store=identity,
    )
    assert _jr13_internal_codes(obs_store, unknown)[0] == "unknown_question"

    forged_published = _observation(
        "obs_f5d723fca4d03dd1285551e3de0983d52ea2658bf5ca6faa7e022681221c850a",
        question_id="IQS_PUB",
        field_id="score.iqs_05",
        request_id="REQ_F",
        attempt_id="ATT_F",
        published=True,
    )
    forged_published["question_semantic_sha256"] = "c" * 64
    forged_pub = import_package(
        obs_store,
        _package([forged_published]),
        frozen_release=_release(),
        identity_store=identity,
    )
    assert _jr13_internal_codes(obs_store, forged_pub)[0] == "question_semantic_mismatch"

    stripped = _observation(
        "obs_c29b63975b9ec8ecfada198909f317f953a898575f14ed161a01df7f98223b37",
        question_id="IQS_PUB",
        field_id="score.iqs_05",
        request_id="REQ_G",
        attempt_id="ATT_G",
        published=True,
    )
    for key in (
        "module_package_id",
        "module_release_id",
        "question_definition_sha256",
        "question_semantic_sha256",
        "cycle_sensitive",
    ):
        stripped.pop(key, None)
    stripped["schema_version"] = "1.0.0"
    stripped_result = import_package(
        obs_store,
        _package([stripped]),
        frozen_release=_release(),
        identity_store=identity,
    )
    assert _jr13_internal_codes(obs_store, stripped_result)[0] in {
        "partial_module_binding",
        "published_binding_missing",
    }

    exec_twin = _observation(
        "obs_93c1cc86163cea867e8a4ed05f1357c9bb0f8c0bb90ca32342b3dda0ba5f750a",
        request_id="REQ_C",
        attempt_id="ATT_C",
        score=5,
    )
    twin = import_package(
        obs_store,
        _package([exec_twin]),
        frozen_release=_release(),
        identity_store=identity,
    )
    assert twin["summary"] == {"conflict": 1}
    assert _jr13_internal_codes(obs_store, twin)[0] == "execution_key_id_mismatch"
    assert (
        obs_store.get_observation(
            "obs_93c1cc86163cea867e8a4ed05f1357c9bb0f8c0bb90ca32342b3dda0ba5f750a"
        )
        is None
    )
    kinds = {row["conflict_kind"] for row in obs_store.list_conflicts()}
    assert "execution_key_id_mismatch" in kinds


def test_db_06_forbidden_artifacts_rejected_and_no_document_tree(tmp_path, monkeypatch) -> None:
    _no_network(monkeypatch)
    before = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*") if p.is_file())
    obs_store, identity = _workspace(tmp_path)
    carrier = _observation(
        "obs_6f23f137308da1f2c95d9acc4be1af05d9c110cd7c3ca88cf6023366388715d0",
        request_id="REQ_H",
        attempt_id="ATT_H",
        extra={"source_manifest": {"spans": ["fake"]}},
    )
    result = import_package(
        obs_store, _package([carrier]), frozen_release=_release(), identity_store=identity
    )
    assert _jr13_internal_codes(obs_store, result)[0] == "forbidden_field"
    assert (
        obs_store.get_observation(
            "obs_6f23f137308da1f2c95d9acc4be1af05d9c110cd7c3ca88cf6023366388715d0"
        )
        is None
    )
    after = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*") if p.is_file())
    created = [p for p in after if p not in before]
    assert created, "import must persist its own store under data/quick_scan"
    assert all(part.replace("\\", "/").startswith("data/quick_scan/") for part in created), created
    assert not any("compan" in part.lower() and "wiki" in part.lower() for part in created)
    accepted = import_package(
        obs_store,
        _package(
            [
                _observation(
                    "obs_53d9c820a4932e7ae8db65f811335ab1948d6b0ed167fd84af037838aba7c6b2",
                    request_id="REQ_I",
                    attempt_id="ATT_I",
                )
            ]
        ),
        frozen_release=_release(),
        identity_store=identity,
    )
    assert accepted["summary"] == {"accepted": 1}
    row = obs_store.get_observation(
        "obs_53d9c820a4932e7ae8db65f811335ab1948d6b0ed167fd84af037838aba7c6b2"
    )
    assert row["qualification_status"] == "review_pending"


def test_sc_05_self_granted_qualification_rejects_both_paths(tmp_path, monkeypatch) -> None:
    _no_network(monkeypatch)
    obs_store, identity = _workspace(tmp_path)
    legacy = _observation(
        "obs_b62145f03b6a4f3c8d547de9a8f993fb3ad62da2cfb1b6efbbf3c03d4d3c896c",
        request_id="REQ_J",
        attempt_id="ATT_J",
        answer_extra={"accepted_ids": ["c01"]},
    )
    screening = _observation(
        "obs_6e93d808f0091d98f1049ec89cb707ed6ec99dc2761b2ad5da8e75bb66ac39b5",
        question_id="IQS_PUB",
        field_id="score.iqs_05",
        request_id="REQ_K",
        attempt_id="ATT_K",
        published=True,
        answer_extra={"search_verified": True},
    )
    elevated = _observation(
        "obs_f080d2f8e650ce8a8a04817b6aaf190a53f805742ee93eff885f2e4e3515f203",
        request_id="REQ_L",
        attempt_id="ATT_L",
        answer_extra={"check_level": "independently_checked"},
    )
    result = import_package(
        obs_store,
        _package([legacy, screening, elevated]),
        frozen_release=_release(),
        identity_store=identity,
    )
    assert result["summary"] == {"rejected": 3}
    codes = set(_jr13_internal_codes(obs_store, result))
    assert codes == {"self_granted_qualification"}
    assert obs_store.counts()["observations"] == 0

    kept_score = import_package(
        obs_store,
        _package(
            [
                _observation(
                    "obs_8948deb0cc5314627abb6c304ac91dbaa5ab1a6effd7a8bee9cbb69203de9a3f",
                    request_id="REQ_M",
                    attempt_id="ATT_M",
                    score=6,
                )
            ]
        ),
        frozen_release=_release(),
        identity_store=identity,
    )
    assert kept_score["summary"] == {"accepted": 1}
    row = obs_store.get_observation(
        "obs_8948deb0cc5314627abb6c304ac91dbaa5ab1a6effd7a8bee9cbb69203de9a3f"
    )
    assert row["reported_score"] == 6
    assert row["qualification_status"] == "review_pending"


def test_sc_06_legacy_strict_stays_review_pending(tmp_path, monkeypatch) -> None:
    _no_network(monkeypatch)
    obs_store, identity = _workspace(tmp_path)
    legacy_strict = _observation(
        "obs_248a5b9ac0513f314e9883f4fa8a0399407d047d1723d4f3369a83679fd341e5",
        request_id="REQ_N",
        attempt_id="ATT_N",
        score=9,
    )
    screening = _observation(
        "obs_0b5ce0997fffb6278d5ad010c1115c5d7c400847ed89ec8534a7c69925df9d30",
        question_id="IQS_PUB",
        field_id="score.iqs_05",
        request_id="REQ_O",
        attempt_id="ATT_O",
        published=True,
        score=7,
    )
    result = import_package(
        obs_store,
        _package([legacy_strict, screening]),
        frozen_release=_release(),
        identity_store=identity,
    )
    assert result["summary"] == {"accepted": 2}
    for observation_id in (
        "obs_248a5b9ac0513f314e9883f4fa8a0399407d047d1723d4f3369a83679fd341e5",
        "obs_0b5ce0997fffb6278d5ad010c1115c5d7c400847ed89ec8534a7c69925df9d30",
    ):
        row = obs_store.get_observation(observation_id)
        assert row["qualification_status"] == "review_pending"
    source = (Path(__file__).parent.parent / "stockwiki" / "quick_scan_observations.py").read_text(
        encoding="utf-8"
    )
    assert source.count('"qualification_status"') >= 1
    assert '"qualification_status": "review_pending"' in source
    assert "formal_accepted" not in source


def test_store_01_two_run_dirs_one_authority(tmp_path, monkeypatch) -> None:
    """Single-authority store + ACK verified here.

    Residual gap (blocked on later tasks): no UI/theme/industry consumer
    reads QuickScanObservationStore yet — those readers arrive with
    W09/W14/W15; this test pins the only read API (observations_for_entity/
    get_observation) those consumers must share.
    """
    _no_network(monkeypatch)
    run_a = tmp_path / "runs" / "run_a"
    run_b = tmp_path / "runs" / "run_b"
    run_a.mkdir(parents=True)
    run_b.mkdir(parents=True)
    pkg_a = _package(
        [
            _observation(
                "obs_f04e58bc3dfccee277821fecc59b0f54d82da9203b956b2745ed3b8465c1e81a",
                request_id="REQ_SA",
                attempt_id="ATT_SA",
            )
        ]
    )
    pkg_b = _package(
        [
            _observation(
                "obs_54e0ffca49a91f80ed81012708d864ec63562376ec9db6855194741667fed220",
                question_id="FACT_10",
                field_id="facts.customers",
                response_kind="fact",
                status="answered",
                score=None,
                request_id="REQ_SB",
                attempt_id="ATT_SB",
            )
        ],
        producer="StockQAbyLLM",
    )
    (run_a / "outbox.json").write_text(
        json.dumps({"state": "sent", "package_id": pkg_a["package_id"]}),
        encoding="utf-8",
    )
    (run_b / "outbox.json").write_text(
        json.dumps({"state": "sent", "package_id": pkg_b["package_id"]}),
        encoding="utf-8",
    )
    (run_a / "package.json").write_text(
        json.dumps(pkg_a, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )
    (run_b / "package.json").write_text(
        json.dumps(pkg_b, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )
    producer_state_before = {
        str(p): p.read_bytes() for p in (run_a / "outbox.json", run_b / "outbox.json")
    }

    obs_store, identity = _workspace(tmp_path)
    ack_a = import_package(
        obs_store,
        (run_a / "package.json").read_bytes(),
        frozen_release=_release(),
        identity_store=identity,
    )
    ack_b = import_package(
        obs_store,
        (run_b / "package.json").read_bytes(),
        frozen_release=_release(),
        identity_store=identity,
    )
    assert ack_a["summary"] == {"accepted": 1}
    assert ack_b["summary"] == {"accepted": 1}
    for ack in (ack_a["acks"][0], ack_b["acks"][0]):
        assert ack["consumer"]["component"] == "StockWiki"
        assert ack["consumer"]["store_id"] == obs_store.store_id
        assert ack["payload_sha256"]
    view = obs_store.observations_for_entity("E01")
    assert {row["observation_id"] for row in view} == {
        "obs_f04e58bc3dfccee277821fecc59b0f54d82da9203b956b2745ed3b8465c1e81a",
        "obs_54e0ffca49a91f80ed81012708d864ec63562376ec9db6855194741667fed220",
    }
    for path, content in producer_state_before.items():
        assert Path(path).read_bytes() == content
    assert obs_store.counts()["observations"] == 2


def test_store_02_lost_ack_replay_and_conflicting_copy(tmp_path, monkeypatch) -> None:
    _no_network(monkeypatch)
    obs_store, identity = _workspace(tmp_path)
    package = _package(
        [
            _observation(
                "obs_5521958b749f22cf172ca359d969e4e49b34d6675ed75f201b1547db27d8c496",
                request_id="REQ_X",
                attempt_id="ATT_X",
            )
        ]
    )
    raw = json.dumps(package, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    first = import_package(obs_store, raw, frozen_release=_release(), identity_store=identity)
    assert first["summary"] == {"accepted": 1}
    lost = import_package(obs_store, raw, frozen_release=_release(), identity_store=identity)
    assert lost["acks"][0]["ack_id"] == first["acks"][0]["ack_id"]

    copy_package = _package(
        [
            _observation(
                "obs_5521958b749f22cf172ca359d969e4e49b34d6675ed75f201b1547db27d8c496",
                request_id="REQ_X",
                attempt_id="ATT_X",
                score=2,
            )
        ]
    )
    conflicting = import_package(
        obs_store,
        json.dumps(copy_package, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        frozen_release=_release(),
        identity_store=identity,
    )
    assert conflicting["acks"][0]["status"] == "conflict"
    assert _jr13_internal_codes(obs_store, conflicting)[0] == "immutable_key_hash_conflict"
    stored = obs_store.get_observation(
        "obs_5521958b749f22cf172ca359d969e4e49b34d6675ed75f201b1547db27d8c496"
    )
    assert stored["reported_score"] == 8
    assert obs_store.counts()["observations"] == 1


def test_id_17_history_is_immutable_across_identity_generations(tmp_path, monkeypatch) -> None:
    """Old payload/identity fields stay byte-identical across later imports.

    Residual gap (blocked on C01/W01-owned identity merge/split machinery):
    issuer succession "new generations start clean with no inherited score"
    is identity-side; here we pin the observation-side obligation — originals
    never rewritten and no UPDATE/DELETE SQL exists in the store.
    """
    _no_network(monkeypatch)
    obs_store, identity = _workspace(tmp_path)
    first = import_package(
        obs_store,
        _package(
            [
                _observation(
                    "obs_01171ed0221aa1d120df250e285c63d639d73fae6d9106de504398805fc6b8fd",
                    entity_id="E01",
                    request_id="REQ_1G",
                    attempt_id="ATT_1G",
                )
            ]
        ),
        frozen_release=_release(),
        identity_store=identity,
    )
    assert first["summary"] == {"accepted": 1}
    before = obs_store.get_observation(
        "obs_01171ed0221aa1d120df250e285c63d639d73fae6d9106de504398805fc6b8fd"
    )
    before_bytes = json.dumps(before["payload"], sort_keys=True, ensure_ascii=False)

    successor = _observation(
        "obs_04f6cd61472ac1734266393c8cea997afe9059805e7f9c43a4f6b5b8e6601b83",
        entity_id="E10",
        request_id="REQ_2G",
        attempt_id="ATT_2G",
    )
    second = import_package(
        obs_store, _package([successor]), frozen_release=_release(), identity_store=identity
    )
    assert second["summary"] == {"accepted": 1}
    after = obs_store.get_observation(
        "obs_01171ed0221aa1d120df250e285c63d639d73fae6d9106de504398805fc6b8fd"
    )
    after_bytes = json.dumps(after["payload"], sort_keys=True, ensure_ascii=False)
    assert before_bytes == after_bytes
    assert after["payload_sha256"] == before["payload_sha256"]
    assert after["model_resolved"] == before["model_resolved"]
    assert after["observed_at"] == before["observed_at"]
    source = (
        (Path(__file__).parent.parent / "stockwiki" / "quick_scan_observations.py")
        .read_text(encoding="utf-8")
        .upper()
    )
    assert "UPDATE " not in source
    assert "DELETE FROM" not in source


def test_id_23_subject_revision_binding_and_legacy_null(tmp_path, monkeypatch) -> None:
    _no_network(monkeypatch)
    obs_store, identity = _workspace(tmp_path)
    old = _observation(
        "obs_ef4ed0e39cceb5fd636b582cb977039e97772439bc8e11daf8b8189809c0df29",
        request_id="REQ_S1",
        attempt_id="ATT_S1",
        extra={
            "analysis_subject": {
                "analysis_subject_id": "ASJ_1",
                "analysis_subject_revision": 1,
                "entity_id": "E01",
                "primary_issuer_id": "ISS_1",
            }
        },
    )
    new = _observation(
        "obs_3b55a20d2cb13c221416bc98cac94f5ebbd3393613d387a95316cd0b1fe775b7",
        request_id="REQ_S2",
        attempt_id="ATT_S2",
        extra={
            "analysis_subject": {
                "analysis_subject_id": "ASJ_1",
                "analysis_subject_revision": 2,
                "entity_id": "E01",
                "primary_issuer_id": "ISS_1",
            }
        },
    )
    legacy = _observation(
        "obs_a05cdcbd2f8c8b90b70280e939ed90192e8cbdd1f4b94740e791ca0b3ca6df4d",
        request_id="REQ_S3",
        attempt_id="ATT_S3",
    )
    mismatched = _observation(
        "obs_5d00115c6723df86ce70f5e5c09302df19ca1f0f9a9ad302d1bb361010481408",
        request_id="REQ_S4",
        attempt_id="ATT_S4",
        extra={
            "analysis_subject": {
                "analysis_subject_id": "ASJ_9",
                "analysis_subject_revision": 1,
                "entity_id": "E10",
            }
        },
    )
    result = import_package(
        obs_store,
        _package([old, new, legacy, mismatched]),
        frozen_release=_release(),
        identity_store=identity,
    )
    statuses = {ack["observation_id"]: ack["status"] for ack in result["acks"]}
    assert (
        statuses["obs_ef4ed0e39cceb5fd636b582cb977039e97772439bc8e11daf8b8189809c0df29"]
        == "accepted"
    )
    assert (
        statuses["obs_3b55a20d2cb13c221416bc98cac94f5ebbd3393613d387a95316cd0b1fe775b7"]
        == "accepted"
    )
    assert (
        statuses["obs_a05cdcbd2f8c8b90b70280e939ed90192e8cbdd1f4b94740e791ca0b3ca6df4d"]
        == "accepted"
    )
    assert (
        statuses["obs_5d00115c6723df86ce70f5e5c09302df19ca1f0f9a9ad302d1bb361010481408"]
        == "rejected"
    )
    assert _jr13_internal_codes(obs_store, result)[3] == "analysis_subject_scope_mismatch"

    old_row = obs_store.get_observation(
        "obs_ef4ed0e39cceb5fd636b582cb977039e97772439bc8e11daf8b8189809c0df29"
    )
    new_row = obs_store.get_observation(
        "obs_3b55a20d2cb13c221416bc98cac94f5ebbd3393613d387a95316cd0b1fe775b7"
    )
    legacy_row = obs_store.get_observation(
        "obs_a05cdcbd2f8c8b90b70280e939ed90192e8cbdd1f4b94740e791ca0b3ca6df4d"
    )
    assert old_row["analysis_subject_revision"] == 1
    assert old_row["analysis_subject_id"] == "ASJ_1"
    assert new_row["analysis_subject_revision"] == 2
    assert legacy_row["analysis_subject_id"] is None
    assert legacy_row["analysis_subject_revision"] is None
    assert old_row["payload_sha256"] != new_row["payload_sha256"]


def test_published_observation_accepts_valid_binding(tmp_path, monkeypatch) -> None:
    _no_network(monkeypatch)
    obs_store, identity = _workspace(tmp_path)
    published = _observation(
        "obs_c6844e4fb995c4f08c759edd1c1e40a03bac128c5688af77d384a35a51a50ea7",
        question_id="IQS_PUB",
        field_id="score.iqs_05",
        request_id="REQ_P",
        attempt_id="ATT_P",
        published=True,
        score=9,
    )
    result = import_package(
        obs_store, _package([published]), frozen_release=_release(), identity_store=identity
    )
    assert result["summary"] == {"accepted": 1}
    row = obs_store.get_observation(
        "obs_c6844e4fb995c4f08c759edd1c1e40a03bac128c5688af77d384a35a51a50ea7"
    )
    assert row["publication_status"] == "published"
    assert row["reported_score"] == 9


def test_security_scope_and_nan_package_refusals(tmp_path, monkeypatch) -> None:
    _no_network(monkeypatch)
    obs_store, identity = _workspace(tmp_path)
    wrong_security = _observation(
        "obs_db099fb3ad261cded6ea6fae37dbb59f6076f71d86a46f21d8866e75fe6af185",
        question_id="SEC_Q",
        field_id="quote.price",
        request_id="REQ_Z",
        attempt_id="ATT_Z",
        security_id="SEC_E10_0",
    )
    result = import_package(
        obs_store, _package([wrong_security]), frozen_release=_release(), identity_store=identity
    )
    assert _jr13_internal_codes(obs_store, result)[0] == "security_scope_invalid"

    good_security = _observation(
        "obs_d41b4680198b01ce0e1c9d6a79cf52dda77ae4fe05acb88dbc78f6f0a5024ef8",
        question_id="SEC_Q",
        field_id="quote.price",
        request_id="REQ_Z2",
        attempt_id="ATT_Z2",
        security_id="SEC_E01_0",
    )
    ok = import_package(
        obs_store, _package([good_security]), frozen_release=_release(), identity_store=identity
    )
    assert ok["summary"] == {"accepted": 1}

    with pytest.raises(ObservationImportError) as exc:
        parse_package('{"schema_version": NaN, "items": []}')
    assert exc.value.error_code == "json_constant_forbidden"

    with pytest.raises(ObservationImportError) as exc:
        import_package(
            obs_store,
            '{"schema_version":"1.0.0","data_class":"full_document",'
            '"document_payloads_included":true,"extensions":[],"created_at":"x",'
            '"package_sha256":"x","package_id":"x","producer":{"component":"p"},'
            '"consumer":{"namespace":"quick_scan"},"contract_versions":'
            '{"identity_schema":"1","answer_schema":"1","observation_schema":"1",'
            '"question_catalog":"1","model_policy_schema":"1"},"items":[{}]}',
            frozen_release=_release(),
            identity_store=identity,
        )
    assert exc.value.error_code in {"document_payloads_forbidden", "data_class_not_lightweight"}


def test_correction_appends_without_touching_original(tmp_path, monkeypatch) -> None:
    _no_network(monkeypatch)
    obs_store, identity = _workspace(tmp_path)
    import_package(
        obs_store,
        _package(
            [
                _observation(
                    "obs_fd8555892671ef436d14f872326e6077a2f4e3725a32653083143167ff1b7b72",
                    request_id="REQ_COR",
                    attempt_id="ATT_COR",
                )
            ]
        ),
        frozen_release=_release(),
        identity_store=identity,
    )
    before = obs_store.get_observation(
        "obs_fd8555892671ef436d14f872326e6077a2f4e3725a32653083143167ff1b7b72"
    )
    correction_id = obs_store.append_correction(
        "obs_fd8555892671ef436d14f872326e6077a2f4e3725a32653083143167ff1b7b72",
        corrected_observation={"note": "typo fix", "score": 8},
        reason="source date corrected",
    )
    assert correction_id >= 1
    after = obs_store.get_observation(
        "obs_fd8555892671ef436d14f872326e6077a2f4e3725a32653083143167ff1b7b72"
    )
    assert json.dumps(before["payload"], sort_keys=True) == json.dumps(
        after["payload"], sort_keys=True
    )
    rows = obs_store.list_corrections(
        "obs_fd8555892671ef436d14f872326e6077a2f4e3725a32653083143167ff1b7b72"
    )
    assert len(rows) == 1
    assert rows[0]["reason"] == "source date corrected"
    with pytest.raises(ObservationImportError) as exc:
        obs_store.append_correction(
            "obs_9685b2fbb8ce920e5bbccaa8130ff4718473905411b7ffb46ce17bf8d62d1b4c",
            corrected_observation={},
            reason="x",
        )
    assert exc.value.error_code == "correction_target_missing"


def test_modules_stay_offline_and_append_only() -> None:
    root = Path(__file__).parent.parent / "stockwiki"
    for name in ("quick_scan_import.py", "quick_scan_observations.py"):
        source = (root / name).read_text(encoding="utf-8")
        for forbidden in (
            "import requests",
            "import urllib",
            "import socket",
            "import openai",
            "http.client",
            "api_key",
        ):
            assert forbidden not in source, f"{name} must stay offline: {forbidden}"
    store_source = (root / "quick_scan_observations.py").read_text(encoding="utf-8")
    assert "UPDATE " not in store_source.upper()
    assert "DELETE FROM" not in store_source.upper()


def test_db_06_reply_level_nested_evidence_keys_rejected(tmp_path, monkeypatch) -> None:
    _no_network(monkeypatch)
    obs_store, identity = _workspace(tmp_path)
    nested_manifest = _observation(
        "obs_789b311a99395dd9004c7d3fce4699c104bd97518165c109167429d7f0c25fa0",
        request_id="REQ_NM",
        attempt_id="ATT_NM",
        answer_extra={"source_manifest": {"spans": ["fake"]}},
    )
    nested_span = _observation(
        "obs_a49d284eb6403aaafe6e09de43e66bb958577ffb54dfcb589fcc41331a80dccd",
        request_id="REQ_NS",
        attempt_id="ATT_NS",
        answer_extra={"evidence_span_ids": ["span_1"]},
    )
    nested_document = _observation(
        "obs_ad494bcc438230fab4859117936ae8fd2158d81704369a2e3120de39c9d5db92",
        question_id="FACT_10",
        field_id="facts.customers",
        response_kind="fact",
        status="answered",
        score=None,
        request_id="REQ_ND",
        attempt_id="ATT_ND",
        extra={
            "execution": {
                "provider": "fixture_provider",
                "model_requested": "fixture-model",
                "model_resolved": "fixture-model",
                "model_revision": "fixture-1",
                "request_id": "REQ_ND",
                "attempt_id": "ATT_ND",
                "started_at": "2026-10-01T09:00:00Z",
                "answered_at": "2026-10-01T09:01:00Z",
                "search_status": "executed",
                "search_receipt_id": "FIXTURE",
                "prompt_sha256": "b" * 64,
                "raw_document": "<html>page body</html>",
            }
        },
    )
    result = import_package(
        obs_store,
        _package([nested_manifest, nested_span, nested_document]),
        frozen_release=_release(),
        identity_store=identity,
    )
    assert result["summary"] == {"rejected": 3}
    codes = set(_jr13_internal_codes(obs_store, result))
    assert codes == {"forbidden_field"}
    assert obs_store.counts()["observations"] == 0


def test_id_23_subject_carried_scope_must_match_observation(tmp_path, monkeypatch) -> None:
    _no_network(monkeypatch)
    obs_store, identity = _workspace(tmp_path)
    unbound_security = _observation(
        "obs_81bc6d8c9128e737b1a10546932fe3da878d72af38108eae6acdfd38682ab774",
        request_id="REQ_US",
        attempt_id="ATT_US",
        extra={
            "analysis_subject": {
                "analysis_subject_id": "ASJ_1",
                "analysis_subject_revision": 1,
                "entity_id": "E01",
                "security_id": "SEC_E01_0",
            }
        },
    )
    unbound_listing = _observation(
        "obs_da8595d7ec0e2d7ca4d582d46522c46e2e46e830d553bb453fffcd1c77cf2ed0",
        request_id="REQ_UL",
        attempt_id="ATT_UL",
        extra={
            "analysis_subject": {
                "analysis_subject_id": "ASJ_1",
                "analysis_subject_revision": 1,
                "entity_id": "E01",
                "listing_id": "L_77",
            }
        },
    )
    result = import_package(
        obs_store,
        _package([unbound_security, unbound_listing]),
        frozen_release=_release(),
        identity_store=identity,
    )
    assert result["summary"] == {"rejected": 2}
    details = set(_jr13_internal_codes(obs_store, result))
    assert details == {"analysis_subject_scope_mismatch"}
    assert obs_store.counts()["observations"] == 0


def test_published_method_core_token_is_pinned(tmp_path, monkeypatch) -> None:
    _no_network(monkeypatch)
    obs_store, identity = _workspace(tmp_path)
    evil = _observation(
        "obs_5cb56a81b457b77e2a28dfb74390452fd94c13f1365653cd03a85064a2c8b418",
        question_id="IQS_PUB",
        field_id="score.iqs_05",
        request_id="REQ_EC",
        attempt_id="ATT_EC",
        published=True,
    )
    evil["method_id"] = f"module-locked-v1/evil-module-x/{DEFINITION[:16]}/{SEMANTIC[:16]}"
    result = import_package(
        obs_store, _package([evil]), frozen_release=_release(), identity_store=identity
    )
    assert _jr13_internal_codes(obs_store, result)[0] == "method_semantic_binding_mismatch"
    assert (
        obs_store.get_observation(
            "obs_5cb56a81b457b77e2a28dfb74390452fd94c13f1365653cd03a85064a2c8b418"
        )
        is None
    )


def test_db_03_failed_transaction_leaves_no_partial_snapshot(tmp_path, monkeypatch) -> None:
    _no_network(monkeypatch)
    obs_store, identity = _workspace(tmp_path)
    package = _package(
        [
            _observation(
                "obs_8aae580b7c2f28a3c7c986e2ab37e5a60823c4aba1cd2a2f14525c5bd9e0655d",
                request_id="REQ_TA",
                attempt_id="ATT_TA",
            ),
            _observation(
                "obs_1a5265ec87277d178f290143a3cc633910ff1cf515e2142bd4403c8ae6c12d64",
                request_id="REQ_TB",
                attempt_id="ATT_TB",
            ),
        ]
    )
    original = QuickScanObservationStore._apply_one
    calls = {"n": 0}

    def _flaky(self, con, decision):
        calls["n"] += 1
        if calls["n"] >= 2:
            raise RuntimeError("simulated mid-transaction crash")
        return original(self, con, decision)

    monkeypatch.setattr(QuickScanObservationStore, "_apply_one", _flaky)
    with pytest.raises(RuntimeError):
        import_package(
            obs_store,
            json.dumps(package, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            frozen_release=_release(),
            identity_store=identity,
        )
    assert obs_store.counts() == {
        "observations": 0,
        "acked_items": 0,
        "conflicts": 0,
        "corrections": 0,
    }


def test_observation_import_cli_registered_and_idempotent(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    """CLI wiring for `observation-import` (W05 entry): single-line receipt, replay-safe."""
    _no_network(monkeypatch)
    _workspace(tmp_path)
    package = _package(
        [
            _observation(
                "obs_f12e6f356185c9aa81f92472d37598b1586bd7b9622cda4788e9b8f3f12be5b2",
                request_id="REQ_CLI1",
                attempt_id="ATT_CLI1",
            )
        ]
    )
    pkg_path = tmp_path / "package.json"
    pkg_path.write_text(json.dumps(package, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    rel_path = tmp_path / "release.json"
    rel_path.write_text(json.dumps(_release(), ensure_ascii=False), encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args(
        [
            "--root",
            str(tmp_path),
            "observation-import",
            "--package",
            str(pkg_path),
            "--release",
            str(rel_path),
        ]
    )
    assert args.func(args) == 0
    out = capsys.readouterr()
    assert out.err == ""
    assert out.out.count(chr(10)) == 1
    receipt = json.loads(out.out.strip())
    assert receipt["action"] == "observation-import"
    assert receipt["summary"] == {"accepted": 1}
    assert receipt["acks"][0]["status"] == "accepted"

    args2 = parser.parse_args(
        [
            "--root",
            str(tmp_path),
            "observation-import",
            "--package",
            str(pkg_path),
            "--release",
            str(rel_path),
        ]
    )
    assert args2.func(args2) == 0
    out2 = capsys.readouterr()
    receipt2 = json.loads(out2.out.strip())
    assert receipt2["acks"][0]["ack_id"] == receipt["acks"][0]["ack_id"]
    assert (
        receipt2["acks"][0]["observation_id"]
        == "obs_f12e6f356185c9aa81f92472d37598b1586bd7b9622cda4788e9b8f3f12be5b2"
    )


def _jr13_internal_codes(store, receipt):
    """Old tests retain exact internal refusals; public errors have separate tests."""
    return [
        store.import_audit_for(ack["package_id"], ack["item_id"])["internal_error_code"]
        for ack in receipt["acks"]
    ]


# JR1/JR3: public wire format and raw ingress, independent of internal ledger.
_JR13_ACK_KEYS = {
    "schema_version",
    "ack_id",
    "package_id",
    "item_id",
    "observation_id",
    "payload_sha256",
    "status",
    "error_code",
    "received_at",
    "consumer",
}


def _jr13_public_ack(ack):
    assert set(ack) == _JR13_ACK_KEYS
    assert ack["schema_version"] == "1.0.0"
    assert set(ack["consumer"]) == {"component", "namespace", "store_id"}
    assert ack["consumer"]["component"] == "StockWiki"
    assert ack["consumer"]["namespace"] == "quick_scan"
    if ack["status"] in {"accepted", "already_present"}:
        assert ack["error_code"] is None
    elif ack["status"] == "conflict":
        assert ack["error_code"] == "immutable_key_hash_conflict"
    else:
        assert ack["status"] == "rejected"
        assert ack["error_code"] in {
            "unsupported_schema",
            "missing_entity",
            "unknown_question",
            "invalid_payload",
            "lineage_violation",
        }
    import os

    if os.environ.get("IQS_JR13_SCHEMA"):
        from jsonschema import Draft202012Validator, FormatChecker

        contract = json.loads(Path(os.environ["IQS_JR13_SCHEMA"]).read_text("utf-8"))
        Draft202012Validator(
            {"$ref": "#/$defs/ImportAck", "$defs": contract["$defs"]},
            format_checker=FormatChecker(),
        ).validate(ack)


def _jr13_obs(tag="a", **kwargs):
    import hashlib

    return _observation("obs_" + hashlib.sha256(tag.encode()).hexdigest(), **kwargs)


def test_jr13_public_ack_all_outcomes_and_audit(tmp_path):
    store, identity = _workspace(tmp_path)
    original = _jr13_obs(request_id="REQ_JR13", attempt_id="ATT_JR13")
    package = _package([original])
    first = import_package(store, package, frozen_release=_release(), identity_store=identity)[
        "acks"
    ][0]
    _jr13_public_ack(first)
    replay = _package([original])
    replay["created_at"] = "2026-10-01T11:00:00Z"
    seed = {k: v for k, v in replay.items() if k not in {"package_id", "package_sha256"}}
    replay["package_sha256"] = canonical_sha256(seed)
    replay["package_id"] = "pkg_" + replay["package_sha256"]
    duplicate = import_package(store, replay, frozen_release=_release(), identity_store=identity)[
        "acks"
    ][0]
    changed = copy.deepcopy(original)
    changed["answer"]["score"] = 3
    collision = import_package(
        store, _package([changed]), frozen_release=_release(), identity_store=identity
    )["acks"][0]
    for ack in (duplicate, collision):
        _jr13_public_ack(ack)
    assert [first["status"], duplicate["status"], collision["status"]] == [
        "accepted",
        "already_present",
        "conflict",
    ]
    missing = import_package(
        store,
        _package([_jr13_obs("missing", entity_id="MISSING")]),
        frozen_release=_release(),
        identity_store=identity,
    )["acks"][0]
    _jr13_public_ack(missing)
    assert missing["error_code"] == "missing_entity"
    audit = store.import_audit_for(duplicate["package_id"], duplicate["item_id"])
    assert audit["original_import"]["package_id"] == package["package_id"]
    rejected_audit = store.import_audit_for(missing["package_id"], missing["item_id"])
    assert rejected_audit["internal_error_code"] == "entity_not_found"
    assert rejected_audit["detail"] == "MISSING"
    reopened = QuickScanObservationStore(store.paths)
    assert reopened.ack_for(first["package_id"], first["item_id"]) == first
    assert (
        import_package(reopened, package, frozen_release=_release(), identity_store=identity)[
            "acks"
        ][0]
        == first
    )


@pytest.mark.parametrize(
    "changes,expected",
    [
        ({"question_id": "UNKNOWN"}, "unknown_question"),
        ({"schema_version": "9.0.0"}, "unsupported_schema"),
        ({"field_id": "score.other"}, "lineage_violation"),
        (
            {
                "answer": {
                    "question_id": "IQS_LEG",
                    "response_kind": "score",
                    "status": "scored",
                    "score": 11,
                }
            },
            "invalid_payload",
        ),
    ],
)
def test_jr13_public_rejection_taxonomy(tmp_path, changes, expected):
    store, identity = _workspace(tmp_path)
    observation = _jr13_obs("reject")
    observation.update(changes)
    if "question_id" in changes:
        observation["answer"]["question_id"] = changes["question_id"]
    ack = import_package(
        store, _package([observation]), frozen_release=_release(), identity_store=identity
    )["acks"][0]
    _jr13_public_ack(ack)
    assert ack["error_code"] == expected
    assert store.counts()["observations"] == 0


@pytest.mark.parametrize(
    "raw,code",
    [
        ('{"x":1,"x":1}', "json_duplicate_key"),
        ('{"a":{"x":1,"x":1}}', "json_duplicate_key"),
        ('{"a":[{"x":1,"x":1}]}', "json_duplicate_key"),
        ('{"x":NaN}', "json_constant_forbidden"),
        ('{"x":Infinity}', "json_constant_forbidden"),
        ('{"x":-Infinity}', "json_constant_forbidden"),
        ('{"x":1e400}', "json_number_nonfinite"),
        ('{"x":-1e400}', "json_number_nonfinite"),
    ],
)
def test_jr13_raw_json_rejects_before_decisions(raw, code):
    with pytest.raises(ImportValidationError) as caught:
        parse_package(raw)
    assert caught.value.error_code == code


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), (1, 2)])
def test_jr13_direct_dict_cannot_bypass_ingress(value, tmp_path):
    store, identity = _workspace(tmp_path)
    before = store.counts()
    with pytest.raises(ImportValidationError) as caught:
        import_package(
            store,
            {"nested": [{"value": value}]},
            frozen_release=_release(),
            identity_store=identity,
        )
    assert caught.value.error_code == (
        "json_number_nonfinite" if isinstance(value, float) else "json_value_invalid"
    )
    assert store.counts() == before


@pytest.mark.parametrize(
    "mutation", ["duplicate_root", "duplicate_nested", "duplicate_array", "overflow"]
)
def test_jr13_real_cli_invalid_raw_json_zero_writes(tmp_path, mutation):
    import os
    import subprocess
    import sys

    store, identity = _workspace(tmp_path)
    package = _package([_jr13_obs("cli")])
    raw = json.dumps(package)
    if mutation == "duplicate_root":
        raw = raw.replace(
            '"schema_version": "1.0.0"', '"schema_version": "1.0.0", "schema_version": "1.0.0"', 1
        )
    elif mutation == "duplicate_nested":
        raw = raw.replace(
            '"summary": "fixture summary"',
            '"summary": "fixture summary", "summary": "fixture summary"',
            1,
        )
    elif mutation == "duplicate_array":
        raw = raw.replace('"items": [', '"items": [', 1).replace(
            '"item_id":', '"item_id": "ignored", "item_id":', 1
        )
    else:
        raw = raw.replace('"summary": "fixture summary"', '"summary": 1e400', 1)
    packet = tmp_path / "packet.json"
    packet.write_text(raw, encoding="utf-8")
    release = tmp_path / "release.json"
    release.write_text(json.dumps(_release()), encoding="utf-8")
    before = store.counts()
    proc = subprocess.run(
        [
            sys.executable,
            "-B",
            "-X",
            "utf8",
            "-m",
            "stockwiki.cli",
            "--root",
            str(tmp_path),
            "observation-import",
            "--package",
            str(packet),
            "--release",
            str(release),
        ],
        cwd=Path(__file__).parent.parent,
        env=dict(os.environ),
        capture_output=True,
        timeout=30,
    )
    assert proc.returncode != 0, proc.stdout.decode()
    assert store.counts() == before


def test_jr13_historical_ack_bytes_are_not_projected_on_replay(tmp_path):
    import hashlib
    import sqlite3

    store, identity = _workspace(tmp_path)
    package = _package([_jr13_obs("legacy")])
    ack = import_package(store, package, frozen_release=_release(), identity_store=identity)[
        "acks"
    ][0]
    historical = {
        **ack,
        "ack_sequence": 1,
        "original_import": {
            "package_id": package["package_id"],
            "ack_sequence": 1,
            "received_at": ack["received_at"],
        },
    }
    raw = json.dumps(historical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    with sqlite3.connect(store.database_path) as con:
        con.execute(
            "UPDATE quick_scan_import_item SET ack_json=? WHERE package_id=? AND item_id=?",
            (raw, ack["package_id"], ack["item_id"]),
        )
    before = hashlib.sha256(raw.encode()).hexdigest()
    assert store.ack_for(ack["package_id"], ack["item_id"]) == historical
    assert (
        import_package(store, package, frozen_release=_release(), identity_store=identity)["acks"][
            0
        ]
        == historical
    )
    with sqlite3.connect(store.database_path) as con:
        actual = con.execute("SELECT ack_json FROM quick_scan_import_item").fetchone()[0]
    assert actual == raw and hashlib.sha256(actual.encode()).hexdigest() == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("item_id", "bad"),
        ("item_id", None),
        ("observation_id", "obs_short"),
        ("observation_id", None),
        ("payload_sha256", ""),
        ("payload_sha256", None),
    ],
)
def test_jr13_review_unacknowledgeable_address_zero_writes(tmp_path, monkeypatch, field, value):
    _no_network(monkeypatch)
    store, identity = _workspace(tmp_path)
    package = _package([_jr13_obs("address")])
    package["items"][0][field] = value
    seed = {key: val for key, val in package.items() if key not in {"package_id", "package_sha256"}}
    package["package_sha256"] = canonical_sha256(seed)
    package["package_id"] = "pkg_" + package["package_sha256"]
    with pytest.raises(ObservationImportError) as error:
        import_package(store, package, frozen_release=_release(), identity_store=identity)
    assert error.value.error_code == "ack_address_invalid"
    assert all(value == 0 for value in store.counts().values())


def test_jr13_review_empty_item_after_valid_item_zero_writes(tmp_path, monkeypatch):
    _no_network(monkeypatch)
    store, identity = _workspace(tmp_path)
    package = _package([_jr13_obs("good")])
    package["items"].append({})
    seed = {key: val for key, val in package.items() if key not in {"package_id", "package_sha256"}}
    package["package_sha256"] = canonical_sha256(seed)
    package["package_id"] = "pkg_" + package["package_sha256"]
    with pytest.raises(ObservationImportError) as error:
        import_package(store, package, frozen_release=_release(), identity_store=identity)
    assert error.value.error_code == "ack_address_invalid"
    assert all(value == 0 for value in store.counts().values())


def test_jr13_review_internal_decision_cannot_create_bad_public_ack(tmp_path, monkeypatch):
    _no_network(monkeypatch)
    store, _ = _workspace(tmp_path)
    bad = {
        "package_id": "pkg_" + "a" * 64,
        "item_id": "bad",
        "observation_id": "obs_" + "b" * 64,
        "payload_sha256": "c" * 64,
        "status": "rejected",
        "error_code": "shape_invalid",
    }
    with pytest.raises(ObservationImportError) as error:
        store.apply_decisions([bad])
    assert error.value.error_code == "ack_address_invalid"
    assert all(value == 0 for value in store.counts().values())


def test_jr13_review_already_present_references_accepted_import(tmp_path, monkeypatch):
    _no_network(monkeypatch)
    store, identity = _workspace(tmp_path)
    obs = _jr13_obs("reference", entity_id="E99")
    first = import_package(
        store, _package([obs], producer="First"), frozen_release=_release(), identity_store=identity
    )
    assert first["acks"][0]["status"] == "rejected"
    entity = _seed_entity("E99")
    bindings = entity.pop("_bindings")
    identity.save_entity(entity, source_bindings=bindings)
    accepted = import_package(
        store,
        _package([obs], producer="Second"),
        frozen_release=_release(),
        identity_store=identity,
    )
    assert accepted["acks"][0]["status"] == "accepted"
    third = import_package(
        store, _package([obs], producer="Third"), frozen_release=_release(), identity_store=identity
    )
    assert third["acks"][0]["status"] == "already_present"
    ack = third["acks"][0]
    audit = store.import_audit_for(ack["package_id"], ack["item_id"])
    assert audit["original_import"]["package_id"] == accepted["package_id"]
    assert audit["original_import"]["item_id"] == accepted["acks"][0]["item_id"]


def test_jr13_review_concurrent_schema1_upgrade_is_serialized(tmp_path, monkeypatch):
    import threading
    from concurrent.futures import ThreadPoolExecutor

    store, _ = _workspace(tmp_path)
    with sqlite3.connect(store.database_path) as con:
        con.execute("DROP TABLE quick_scan_import_audit")
        con.execute("PRAGMA user_version=1")
    barrier = threading.Barrier(2)
    original_connect = sqlite3.connect

    class OrderedConnection(sqlite3.Connection):
        def execute(self, sql, *args, **kwargs):
            cursor = super().execute(sql, *args, **kwargs)
            if sql == "PRAGMA user_version" and not self.in_transaction:
                # Old code reads version before write lock: force both real reads
                # before either CREATE. Correct code reads under BEGIN and bypasses.
                barrier.wait(timeout=5)
            return cursor

    def connect(*args, **kwargs):
        kwargs["factory"] = OrderedConnection
        return original_connect(*args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", connect)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(store.migrate) for _ in range(2)]
        assert [future.result(timeout=10) for future in futures] == [2, 2]


def _jr13_historical_short_fixture(tmp_path):
    """Synthetic schema-1 forensic fixture; not a real issuer/owner golden."""
    store, identity = _workspace(tmp_path)
    obs = _jr13_obs("old-short")
    obs["observation_id"] = "obs_historical_short"
    package = _package([obs])
    item = package["items"][0]
    decision = dict(item, package_id=package["package_id"], exec_key="synthetic-old-exec")
    row, _ = store._observation_row(decision, 1)
    received = "2026-10-01T09:02:00Z"
    ack = dict(
        schema_version="1.0.0",
        ack_id="ack_historical_short_fixture",
        package_id=package["package_id"],
        item_id=item["item_id"],
        observation_id=item["observation_id"],
        payload_sha256=item["payload_sha256"],
        status="accepted",
        error_code=None,
        received_at=received,
        consumer=dict(component="StockWiki", namespace="quick_scan", store_id=store.store_id),
        ack_sequence=1,
        original_import=None,
    )
    raw = json.dumps(ack, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    with sqlite3.connect(store.database_path) as con:
        con.execute("DROP TABLE quick_scan_import_audit")
        con.execute("PRAGMA user_version=1")
        con.execute(
            "INSERT INTO quick_scan_observation ("
            + ",".join(row)
            + ") VALUES ("
            + ",".join("?" for _ in row)
            + ")",
            list(row.values()),
        )
        con.execute(
            """INSERT INTO quick_scan_import_item
            (package_id,item_id,observation_id,payload_sha256,status,error_code,ack_sequence,received_at,store_id,ack_json)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                package["package_id"],
                item["item_id"],
                item["observation_id"],
                item["payload_sha256"],
                "accepted",
                None,
                1,
                received,
                store.store_id,
                raw,
            ),
        )
    return store, identity, package, ack


def test_jr13_review_short_history_exact_replay_is_read_only(tmp_path, monkeypatch):
    _no_network(monkeypatch)
    store, identity, package, ack = _jr13_historical_short_fixture(tmp_path)
    before = hashlib.sha256(store.database_path.read_bytes()).hexdigest()
    result = import_package(store, package, frozen_release=_release(), identity_store=identity)
    assert result["acks"] == [ack] and result["legacy_wire_pending"] is True
    assert store.ack_for(ack["package_id"], ack["item_id"]) == ack
    assert store.import_audit_for(ack["package_id"], ack["item_id"]) is None
    assert hashlib.sha256(store.database_path.read_bytes()).hexdigest() == before
    with sqlite3.connect(store.database_path) as con:
        assert con.execute("PRAGMA user_version").fetchone()[0] == 1
    decision = {
        field: ack[field] for field in ["package_id", "item_id", "observation_id", "payload_sha256"]
    }
    assert store.apply_decisions([decision]) == [ack]
    assert hashlib.sha256(store.database_path.read_bytes()).hexdigest() == before


def test_jr13_review_short_history_binding_conflict_never_replays(tmp_path, monkeypatch):
    _no_network(monkeypatch)
    store, _, _, ack = _jr13_historical_short_fixture(tmp_path)
    decision = {
        field: ack[field] for field in ["package_id", "item_id", "observation_id", "payload_sha256"]
    }
    decision["payload_sha256"] = "f" * 64
    before = hashlib.sha256(store.database_path.read_bytes()).hexdigest()
    with pytest.raises(ObservationImportError) as error:
        store.apply_decisions([decision])
    assert error.value.error_code == "historical_ack_binding_mismatch"
    assert hashlib.sha256(store.database_path.read_bytes()).hexdigest() == before


def test_jr13_review_short_history_does_not_bypass_package_hash(tmp_path, monkeypatch):
    _no_network(monkeypatch)
    store, identity, package, _ = _jr13_historical_short_fixture(tmp_path)
    package["items"][0]["observation"]["answer"]["score"] = 10
    before = hashlib.sha256(store.database_path.read_bytes()).hexdigest()
    with pytest.raises(ObservationImportError) as error:
        import_package(store, package, frozen_release=_release(), identity_store=identity)
    assert error.value.error_code == "package_hash_mismatch"
    assert hashlib.sha256(store.database_path.read_bytes()).hexdigest() == before


@pytest.mark.parametrize("field", ["payload_sha256", "observation_id"])
@pytest.mark.parametrize("old_first", [False, True])
def test_jr13_review_mixed_conflicting_slot_is_atomic(tmp_path, field, old_first):
    store, identity = _workspace(tmp_path)
    old = _package([_jr13_obs("mixed-old")])
    ack = import_package(store, old, frozen_release=_release(), identity_store=identity)["acks"][0]
    wrong = {key: ack[key] for key in ["package_id", "item_id", "observation_id", "payload_sha256"]}
    wrong.update(status="rejected", error_code="unknown_question")
    wrong[field] = "f" * 64 if field == "payload_sha256" else "obs_" + "f" * 64
    new = dict(
        package_id="pkg_" + "c" * 64,
        item_id="itm_" + "b" * 64,
        observation_id="obs_" + "a" * 64,
        payload_sha256="d" * 64,
        status="rejected",
        error_code="unknown_question",
    )
    before = hashlib.sha256(store.database_path.read_bytes()).hexdigest()
    counts = store.counts()
    with pytest.raises(ObservationImportError) as error:
        store.apply_decisions([wrong, new] if old_first else [new, wrong], identity_lookup=identity)
    assert error.value.error_code == "historical_ack_binding_mismatch"
    assert store.counts() == counts
    assert store.ack_for(new["package_id"], new["item_id"]) is None
    assert hashlib.sha256(store.database_path.read_bytes()).hexdigest() == before


@pytest.mark.parametrize("field", ["payload_sha256", "observation_id"])
def test_jr13_review_slot_created_after_read_is_rechecked_in_transaction(
    tmp_path, monkeypatch, field
):
    store, identity = _workspace(tmp_path)
    old = _package([_jr13_obs("race-old")])
    ack = import_package(store, old, frozen_release=_release(), identity_store=identity)["acks"][0]
    wrong = {key: ack[key] for key in ["package_id", "item_id", "observation_id", "payload_sha256"]}
    wrong.update(status="rejected", error_code="unknown_question")
    wrong[field] = "f" * 64 if field == "payload_sha256" else "obs_" + "f" * 64
    new = dict(
        package_id="pkg_" + "c" * 64,
        item_id="itm_" + "b" * 64,
        observation_id="obs_" + "a" * 64,
        payload_sha256="d" * 64,
        status="rejected",
        error_code="unknown_question",
    )
    # Emulate the absence of the old slot in the pre-transaction snapshot.
    # The actual SQLite write transaction must recheck the now-present row.
    monkeypatch.setattr(store, "replay_decisions", lambda decisions: None)
    before = hashlib.sha256(store.database_path.read_bytes()).hexdigest()
    counts = store.counts()
    with pytest.raises(ObservationImportError) as error:
        store.apply_decisions([new, wrong], identity_lookup=identity)
    assert error.value.error_code == "historical_ack_binding_mismatch"
    assert store.counts() == counts
    assert store.ack_for(new["package_id"], new["item_id"]) is None
    assert hashlib.sha256(store.database_path.read_bytes()).hexdigest() == before


def test_jr13_review_mixed_exact_slot_and_new_item_is_supported(tmp_path):
    store, identity = _workspace(tmp_path)
    old = _package([_jr13_obs("mixed-exact")])
    ack = import_package(store, old, frozen_release=_release(), identity_store=identity)["acks"][0]
    replay = {
        key: ack[key] for key in ["package_id", "item_id", "observation_id", "payload_sha256"]
    }
    replay.update(status="rejected", error_code="unknown_question")
    new = dict(
        package_id="pkg_" + "c" * 64,
        item_id="itm_" + "b" * 64,
        observation_id="obs_" + "a" * 64,
        payload_sha256="d" * 64,
        status="rejected",
        error_code="unknown_question",
    )
    result = store.apply_decisions([new, replay], identity_lookup=identity)
    assert result[1] == ack and result[0]["status"] == "rejected"
    assert store.ack_for(new["package_id"], new["item_id"]) == result[0]
