"""Independent rejection probes; internal transactions are not owner authentication."""
import importlib.util
from contextlib import closing
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

CANDIDATE = Path(__file__).resolve().parents[1] / "native-continuation-candidate"
sys.path[:0] = [str(CANDIDATE / "runtime/qa"), str(CANDIDATE / "runtime/sw")]
import src.utils
src.utils.__path__.insert(0, str(CANDIDATE / "qa/src/utils"))
import tests
tests.__path__.insert(0, str(CANDIDATE / "qa/tests"))
import tests.unit
tests.unit.__path__.insert(0, str(CANDIDATE / "qa/tests/unit"))
spec = importlib.util.spec_from_file_location("native_review_original_units", CANDIDATE / "qa/tests/unit/test_owner_budget_continuation.py")
unit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(unit)
original = unit.original
continuation = unit.continuation
actual_current_session = continuation._current_session


def count(store):
    with closing(store._connect()) as db:
        return db.execute("SELECT COUNT(*) FROM quick_scan_budget_attempt").fetchone()[0]


def test_registered_cell_and_bound_lookalike_are_not_authority(original, monkeypatch):
    from src.utils.quick_scan_work_transport import _OWNER_REFRESH_GUARD
    prepared = unit.synthetic_cell(original, monkeypatch)
    monkeypatch.setattr(continuation, "_current_session", actual_current_session)
    class Lookalike:
        def check(self):
            return None
    token = _OWNER_REFRESH_GUARD.set(Lookalike().check)
    try:
        assert actual_current_session() is None
        with pytest.raises(unit.BudgetAdmissionError, match="reconciliation_required"):
            unit.send_synthetic_cell(original, prepared)
    finally:
        _OWNER_REFRESH_GUARD.reset(token)
    assert count(original[0]) == 2


def test_current_owner_refusal_rolls_back_before_new_budget(original, monkeypatch):
    prepared = unit.synthetic_cell(original, monkeypatch)
    def revoked():
        raise ValueError("independent_current_owner_revoked")
    prepared[3].check = revoked
    with pytest.raises(unit.BudgetAdmissionError, match="independent_current_owner_revoked"):
        unit.send_synthetic_cell(original, prepared)
    assert count(original[0]) == 2


def test_foreign_ledger_cannot_receive_projection(original, monkeypatch, tmp_path):
    prepared = unit.synthetic_cell(original, monkeypatch)
    # Internal test hook is deliberately not a native-approved positive.
    prepared[3].service = SimpleNamespace(store=SimpleNamespace(path=tmp_path / "foreign.sqlite"))
    controlled = prepared[3].proof["owner_policy"]["budget_exposure_acceptance"]["control"]
    controlled["ledger_path"] = str((tmp_path / "foreign.sqlite").resolve())
    with pytest.raises(unit.BudgetAdmissionError, match="original_ledger_mismatch"):
        unit.send_synthetic_cell(original, prepared)
    assert count(original[0]) == 2
    assert not (tmp_path / "foreign.sqlite").exists()


@pytest.mark.parametrize("actual_cost", [1, 200000])
def test_old_exposure_resolution_invalidates_existing_acceptance(original, monkeypatch, actual_cost):
    prepared = unit.synthetic_cell(original, monkeypatch)
    with original[0]._transaction() as db:
        db.execute("UPDATE quick_scan_budget_attempt SET status='settled',actual_cost_micros=?,in_flight=0,reconciled_at='2026-10-18T12:00:00Z' WHERE budget_attempt_id='DISPATCH_unknown'", (actual_cost,))
    with pytest.raises(unit.BudgetAdmissionError, match="source_row_changed"):
        unit.send_synthetic_cell(original, prepared)
    assert count(original[0]) == 2


def test_renewed_control_cannot_reuse_same_original_cell(original, monkeypatch):
    prepared = unit.synthetic_cell(original, monkeypatch)
    prepared[3].proof["owner_policy"]["budget_exposure_acceptance"]["control"]["expires_at"] = "2026-10-20T00:00:00Z"
    with pytest.raises(unit.BudgetAdmissionError, match="registered_action_changed"):
        unit.send_synthetic_cell(original, prepared)
    assert count(original[0]) == 2


def test_registered_cell_confirmation_cannot_be_relabelled(original, monkeypatch):
    prepared = unit.synthetic_cell(original, monkeypatch)
    prepared[3].proof["confirmation"]["confirmation_id"] = "rc2_" + "f" * 64
    with pytest.raises(unit.BudgetAdmissionError, match="registered_action_changed"):
        unit.send_synthetic_cell(original, prepared)
    assert count(original[0]) == 2


def test_non_exact_cell_members_cannot_use_the_accepted_budget(original, monkeypatch):
    prepared = unit.synthetic_cell(original, monkeypatch)
    prepared[3].entries = {}
    with pytest.raises(unit.BudgetAdmissionError, match="original_session_members_mismatch"):
        unit.send_synthetic_cell(original, prepared)
    assert count(original[0]) == 2
