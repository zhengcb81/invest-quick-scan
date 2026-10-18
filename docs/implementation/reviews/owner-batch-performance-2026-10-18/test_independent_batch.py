"""Independent counterexamples. Author fixture constructs synthetic original journal only.
No synthetic authority check is represented as public-native permission proof.
"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import threading,time
import pytest
from src.utils.quick_scan_work_store import QuickScanWorkStore,WorkConflictError
from src.utils.quick_scan_refresh_admission import AdmissionRejected
from src.core.models import Question
from src.utils.quick_scan_work_transport import bind_owner_refresh_guard,_check_owner_refresh_guard,QuickScanWorkPersistenceError
from test_owner_batch_claim import prepare,invoke,rows,sha
from test_owner_batch_adapters import synthetic_adapter,lifecycle


def test_last_frozen_work_identity_drift_is_rejected_inside_original_transaction(tmp_path):
    prepared=prepare(tmp_path,3);store=prepared[0]
    # Drift occurs in the actual original row after admission; inputs/hash remain original.
    with store._transaction() as db:
        db.execute('UPDATE work_item SET identity_snapshot_sha256=? WHERE work_item_id=?',(sha('drift'),prepared[-1][-1]['work_item_id']))
    before=rows(store)
    with pytest.raises(ValueError,match='refresh_admission_work_mismatch'):invoke(prepared)
    assert rows(store)==before


def test_partially_overlapping_independent_stores_have_no_loser_only_claim(tmp_path):
    prepared=prepare(tmp_path,3);ids=[x['work_item_id'] for x in prepared[-1]]
    barrier=threading.Barrier(2)
    def race(args):
        label,members=args
        store=QuickScanWorkStore(prepared[0].path,clock=lambda:prepared[1][0]);local=(store,*prepared[1:])
        barrier.wait()
        try:
            invoke(local,work_item_ids=members,run_id=label,scan_id=label);return label,'claimed',members
        except WorkConflictError:return label,'refused',members
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(race,[('LEFT',ids[:2]),('RIGHT',ids[1:])]))
    assert sorted(r[1] for r in outcomes)==['claimed','refused']
    winner=next(r for r in outcomes if r[1]=='claimed');loser=next(r for r in outcomes if r[1]=='refused')
    assert {x['work_item_id'] for x in map(prepared[0].get_item,ids) if x['status']=='leased'}==set(winner[2])
    with closing(prepared[0]._connect()) as db:
        assert db.execute("SELECT COUNT(*) FROM work_run_ref WHERE run_id=?",(loser[0],)).fetchone()[0]==0
        assert db.execute("SELECT COUNT(*) FROM work_event WHERE event_type='claimed'").fetchone()[0]==2
        assert db.execute('SELECT COUNT(*) FROM attempt').fetchone()[0]==0


def test_waiting_for_original_sqlite_lock_exhausts_deadline_without_claim(tmp_path):
    prepared=prepare(tmp_path,2);store=prepared[0];before=rows(store)
    blocker=store._connect();blocker.execute('BEGIN IMMEDIATE')
    started=threading.Event();deadline=time.monotonic()+0.15
    def queued():
        started.set()
        with pytest.raises(WorkConflictError,match='deadline'):
            invoke(prepared,dispatch_deadline=deadline)
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(queued);assert started.wait(1)
            time.sleep(max(0,deadline-time.monotonic())+0.05)
            blocker.execute('ROLLBACK');future.result(timeout=5)
    finally:blocker.close()
    assert rows(store)==before


def test_claim_permission_is_not_reused_after_revocation(tmp_path):
    prepared=prepare(tmp_path,2);owner,calls=synthetic_adapter(prepared);life=lifecycle(prepared,owner)
    result=life.before_registered_questions([Question(q,question_id=q) for q in owner.entries])
    assert len(result)==2 and len(calls)==1
    before=rows(prepared[0])
    def revoked():raise AdmissionRejected('revoked after original batch claim')
    owner.check=revoked
    with bind_owner_refresh_guard(owner.check):
        with pytest.raises(QuickScanWorkPersistenceError,match='owner_refresh_guard_rejected'):_check_owner_refresh_guard()
    assert rows(prepared[0])==before
    assert all(prepared[0].get_item(x['work_item_id'])['status']=='leased' for x in result)


@pytest.mark.parametrize('bad',[True,0,-1,float('nan'),float('inf')])
def test_invalid_deadline_has_no_db_effect(tmp_path,bad):
    prepared=prepare(tmp_path,2);before=rows(prepared[0])
    with pytest.raises(ValueError,match='deadline'):invoke(prepared,dispatch_deadline=bad)
    assert rows(prepared[0])==before


def test_maximal_thirty_member_action_returns_exact_reversed_order_and_only_one_epoch(tmp_path):
    prepared=prepare(tmp_path,30);store=prepared[0]
    ids=[x['work_item_id'] for x in prepared[-1]][::-1]
    result=invoke(prepared,work_item_ids=ids)
    assert [x['work_item_id'] for x in result]==ids
    assert len({x['lease'].lease_token for x in result})==30
    assert all(store.get_item(x)['lease_expires_at']==1600 for x in ids)
    with closing(store._connect()) as db:
        assert db.execute("SELECT COUNT(*) FROM work_event WHERE event_type='claimed'").fetchone()[0]==30
        assert db.execute('SELECT COUNT(*) FROM attempt').fetchone()[0]==0
        assert db.execute('SELECT COUNT(*) FROM quick_scan_budget_attempt').fetchone()[0]==0
    before=rows(store)
    with pytest.raises(WorkConflictError,match='not_pending'):invoke(prepared,work_item_ids=ids)
    assert rows(store)==before


def test_thirtyone_member_call_rejected_before_any_work_or_run_attachment(tmp_path):
    prepared=prepare(tmp_path,31);before=rows(prepared[0])
    with pytest.raises(ValueError,match='exact_work_ids'):invoke(prepared)
    assert rows(prepared[0])==before
