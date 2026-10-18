from pathlib import Path
import os,sys,subprocess
r=Path(__file__).resolve().parent
label='original-regression01'
env={k:os.environ[k] for k in ('SystemRoot','SYSTEMROOT','WINDIR','PATH','PATHEXT') if k in os.environ}
env.update(PYTHONPATH=os.pathsep.join([str(r/'runtime/guard'),str(r/'runtime/qa'),str(r/'runtime/sw')]),IQS_CONTINUATION_OWN=str(r),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',TEMP=str(r/'runtime/tmp'),TMP=str(r/'runtime/tmp'))
file=r/'runtime/qa/tests/unit/test_quick_scan_work_store.py'
names=['test_prepared_crash_recovers_as_unsent_but_send_intent_crash_is_uncertain','test_unknown_attempt_never_releases_for_fallback_or_new_claim','test_late_old_lease_receipt_is_retained_without_state_overwrite','test_response_available_without_checkpoint_is_uncertain_after_crash','test_two_processes_race_on_one_lease_and_stale_epoch_is_fenced']
cmd=[sys.executable,'-B','-m','pytest',*[str(file)+'::'+name for name in names],'-q','--tb=short','-p','no:cacheprovider','--basetemp',str(r/label),'--junitxml',str(r/'evidence'/(label+'.xml'))]
raise SystemExit(subprocess.run(cmd,cwd=r,env=env).returncode)
