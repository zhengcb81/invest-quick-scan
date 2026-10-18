"""Refusal-only native factory probes and descriptive task restore isolation.

No successful owner double, owner grant, model request or work database is
constructed here. Successful restoration is only an in-memory carrier check.
"""
import copy
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

BASE = Path(__file__).resolve().parents[1]
PROJECTS = BASE.parents[2]
sys.path.insert(0, str(PROJECTS / "StockQAbyLLM"))
sys.path.insert(0, str(PROJECTS / "iqs-company-agent-lab/src"))


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


factory = module("independent_native_task3_factory", BASE / "composition-candidate/scripts/shared_company_task.py")
restorer = module("iqs_company_agent_lab.independent_task3_restore",
    BASE / "company-native-task-overlay/src/iqs_company_agent_lab/task.py")


@pytest.mark.parametrize("kind", ["plain_double", "foreign_owner", "foreign_store", "unmetered"])
def test_factory_refuses_before_unauthorized_owner_check(kind):
    from src.runners.llm_runner import QuickScanWorkLifecycle
    from src.utils.quick_scan_refresh_execution import ApprovedRefreshSession
    from src.utils.quick_scan_owner_refresh import OwnerRefreshSession
    if kind == "plain_double":
        lifecycle = SimpleNamespace()
    else:
        lifecycle = QuickScanWorkLifecycle.__new__(QuickScanWorkLifecycle)
        store = object()
        lifecycle._store = store
        lifecycle._transport_managed = kind != "unmetered"
        if kind == "foreign_owner":
            lifecycle._owner_refresh = SimpleNamespace()
        else:
            # Deliberately incomplete actual types test the negative structural
            # guard only. Their real permission method cannot succeed.
            owner = ApprovedRefreshSession.__new__(ApprovedRefreshSession)
            native = OwnerRefreshSession.__new__(OwnerRefreshSession)
            owner.native = native
            owner.service = SimpleNamespace(store=store)
            native.store = object() if kind == "foreign_store" else store
            lifecycle._owner_refresh = owner
    with pytest.raises(factory.NativeTaskRejected, match="original_.*required"):
        factory.create_native_task(lifecycle, experiment_id="reject-only", run_id="reject-only")


def bundle(protocol="iqs.company-agent-task/3.0.0"):
    return dict(raw=dict(protocol=protocol, company_ref={"sha256": "a" * 64}, limits={},
                         owner_binding={"synthetic": False, "subject_ref": {"scope_id": "carrier-only"}}),
                questions=[], company_doc={"origin": "owner_public"}, evidence_board_doc={"records": []},
                runtime_profile={"synthetic": False}, targets={})


def test_known_task3_restores_binding_but_never_aliases_saved_or_raw_binding():
    saved = bundle()
    before = copy.deepcopy(saved)
    task = restorer.task_from_bundle(saved)
    assert task.owner_binding == saved["raw"]["owner_binding"]
    task.owner_binding["subject_ref"]["scope_id"] = "mutated-public-carrier"
    assert task.raw["owner_binding"]["subject_ref"]["scope_id"] == "carrier-only"
    task.raw["owner_binding"]["subject_ref"]["scope_id"] = "mutated-raw-carrier"
    assert saved == before


@pytest.mark.parametrize("protocol", ["iqs.company-agent-task/4.0.0", "iqs.company-agent-research/1.0.0"])
def test_unknown_or_legacy_protocol_never_gains_native_binding(protocol):
    task = restorer.task_from_bundle(bundle(protocol))
    assert not hasattr(task, "owner_binding")


def test_task3_missing_binding_fails_closed_during_restore():
    saved = bundle()
    del saved["raw"]["owner_binding"]
    with pytest.raises(KeyError):
        restorer.task_from_bundle(saved)
