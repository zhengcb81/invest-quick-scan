"""Preserve old diagnostic assertions through the new internal audit API."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[5]/"runs/r13a/sw"

def main():
    path=ROOT/"tests/test_quick_scan_observations.py"
    old=path.read_text("utf-8")
    marker="# JR1/JR3: public wire format and raw ingress, independent of internal ledger."
    original,addition=old.split(marker,1)
    original=original.replace('assert second["acks"][0]["ack_sequence"] == first["acks"][0]["ack_sequence"]',
        'assert obs_store.import_audit_for(second["acks"][0]["package_id"], second["acks"][0]["item_id"])["ack_sequence"] == obs_store.import_audit_for(first["acks"][0]["package_id"], first["acks"][0]["item_id"])["ack_sequence"]')
    original=original.replace('ack["original_import"]["package_id"]', 'obs_store.import_audit_for(ack["package_id"], ack["item_id"])["original_import"]["package_id"]')
    original=re.sub(r'(\w+)\["acks"\]\[0\]\["error_code"\]',r'_jr13_internal_codes(obs_store, \1)[0]',original)
    original=re.sub(r'\{ack\["error_code"\] for ack in (\w+)\["acks"\]\}',r'set(_jr13_internal_codes(obs_store, \1))',original)
    helper='''\ndef _jr13_internal_codes(store, receipt):
    """Old tests retain exact internal refusals; public errors have separate tests."""
    return [store.import_audit_for(ack["package_id"], ack["item_id"])["internal_error_code"] for ack in receipt["acks"]]

'''
    assert 'def _jr13_internal_codes' not in old
    path.write_text(original+helper+marker+addition,encoding="utf-8",newline="\n")
    path=ROOT/"tests/test_quick_scan_delivery.py"
    assert 'test_jr13_schema2_backup' not in path.read_text('utf-8')
    with path.open('a',encoding='utf-8',newline='\n') as stream: stream.write(r'''

def test_jr13_schema2_backup_and_restore_preserves_original_ack(tmp_path):
    from stockwiki.quick_scan_backup import create_backup, verify_backup, restore_backup
    paths=WorkspacePaths.from_root(tmp_path)
    store=QuickScanObservationStore(paths); store.migrate()
    decision=_decision("itm_backup","obs_backup","b"*64)
    ack=store.apply_decisions([decision])[0]
    snapshot=create_backup(paths,name="jr13-schema2")
    assert snapshot is not None
    verify_backup(paths,"jr13-schema2")
    import shutil
    # Only this synthetic pytest workspace is removed, never the source repo.
    shutil.rmtree(paths.data_dir/"quick_scan")
    restore_backup(paths,"jr13-schema2")
    restored=QuickScanObservationStore(paths)
    assert restored.ack_for(decision["package_id"],decision["item_id"])==ack
    assert restored.import_audit_for(decision["package_id"],decision["item_id"])["internal_error_code"] is None

def test_jr13_schema1_migration_preserves_legacy_ack_and_does_not_backfill(tmp_path):
    import json
    import sqlite3
    store=_store(tmp_path)
    decision=_decision("itm_legacy","obs_legacy","c"*64)
    ack=store.apply_decisions([decision])[0]
    legacy={**ack,"ack_sequence":1}
    raw=json.dumps(legacy,sort_keys=True,separators=(",",":"))
    with sqlite3.connect(store.database_path) as con:
        con.execute("UPDATE quick_scan_import_item SET ack_json=?",(raw,))
        con.execute("DROP TABLE quick_scan_import_audit")
        con.execute("PRAGMA user_version=1")
    assert store.ack_for(decision["package_id"],decision["item_id"])==legacy
    assert store.import_audit_for(decision["package_id"],decision["item_id"]) is None
    assert store.migrate()==2
    assert store.apply_decisions([decision])[0]==legacy
    assert store.import_audit_for(decision["package_id"],decision["item_id"]) is None
    with sqlite3.connect(store.database_path) as con:
        assert con.execute("SELECT ack_json FROM quick_scan_import_item").fetchone()[0]==raw

def test_jr13_newer_schema_and_failed_upgrade_are_atomic(tmp_path,monkeypatch):
    import sqlite3
    import pytest
    from stockwiki.quick_scan_observations import ObservationImportError
    store=_store(tmp_path)
    decision=_decision("itm_atomic","obs_atomic","d"*64)
    ack=store.apply_decisions([decision])[0]
    with sqlite3.connect(store.database_path) as con:
        con.execute("DROP TABLE quick_scan_import_audit"); con.execute("PRAGMA user_version=1")
    def fail(con):
        con.execute("CREATE TABLE rollback_probe (value TEXT)")
        raise RuntimeError("injected migration interruption")
    with monkeypatch.context() as patch:
        patch.setattr(store,"_create_import_audit",fail)
        with pytest.raises(ObservationImportError,match="observation_migration_failed"): store.migrate()
    with sqlite3.connect(store.database_path) as con:
        assert con.execute("PRAGMA user_version").fetchone()[0]==1
        assert con.execute("SELECT 1 FROM sqlite_master WHERE name='rollback_probe'").fetchone() is None
        con.execute("PRAGMA user_version=99")
    with pytest.raises(ObservationImportError,match="observation_store_newer_schema"): store.migrate()
    assert store.ack_for(decision["package_id"],decision["item_id"])==ack
''')
    print('Preserved old diagnostic assertions; added three migration/backup cases')

if __name__=='__main__':main()
