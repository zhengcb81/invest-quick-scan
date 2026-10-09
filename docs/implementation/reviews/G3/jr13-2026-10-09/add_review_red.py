"""Append independent-review regressions before fixing the product."""
from pathlib import Path

IQS=Path(__file__).resolve().parents[5]
OWN=IQS/"runs/r13a"

def main():
    path=OWN/"sw/tests/test_quick_scan_observations.py"
    tests='''

@pytest.mark.parametrize("field,value", [
    ("item_id", "bad"), ("item_id", None),
    ("observation_id", "obs_short"), ("observation_id", None),
    ("payload_sha256", ""), ("payload_sha256", None),
])
def test_jr13_review_unacknowledgeable_address_zero_writes(tmp_path, monkeypatch, field, value):
    _no_network(monkeypatch)
    store, identity = _workspace(tmp_path)
    package = _package([_jr13_obs("address")])
    package["items"][0][field] = value
    seed = {key:val for key,val in package.items() if key not in {"package_id","package_sha256"}}
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
    seed = {key:val for key,val in package.items() if key not in {"package_id","package_sha256"}}
    package["package_sha256"] = canonical_sha256(seed)
    package["package_id"] = "pkg_" + package["package_sha256"]
    with pytest.raises(ObservationImportError) as error:
        import_package(store, package, frozen_release=_release(), identity_store=identity)
    assert error.value.error_code == "ack_address_invalid"
    assert all(value == 0 for value in store.counts().values())


def test_jr13_review_internal_decision_cannot_create_bad_public_ack(tmp_path, monkeypatch):
    _no_network(monkeypatch)
    store, _ = _workspace(tmp_path)
    bad = {"package_id":"pkg_"+"a"*64,"item_id":"bad","observation_id":"obs_"+"b"*64,
        "payload_sha256":"c"*64,"status":"rejected","error_code":"shape_invalid"}
    with pytest.raises(ObservationImportError) as error:
        store.apply_decisions([bad])
    assert error.value.error_code == "ack_address_invalid"
    assert all(value == 0 for value in store.counts().values())


def test_jr13_review_already_present_references_accepted_import(tmp_path, monkeypatch):
    _no_network(monkeypatch)
    store, identity = _workspace(tmp_path)
    obs = _jr13_obs("reference",entity_id="E99")
    first = import_package(store, _package([obs],producer="First"),frozen_release=_release(),identity_store=identity)
    assert first["acks"][0]["status"] == "rejected"
    entity = _seed_entity("E99")
    bindings = entity.pop("_bindings")
    identity.save_entity(entity,source_bindings=bindings)
    accepted = import_package(store, _package([obs],producer="Second"),frozen_release=_release(),identity_store=identity)
    assert accepted["acks"][0]["status"] == "accepted"
    third = import_package(store, _package([obs],producer="Third"),frozen_release=_release(),identity_store=identity)
    assert third["acks"][0]["status"] == "already_present"
    ack=third["acks"][0]
    audit=store.import_audit_for(ack["package_id"],ack["item_id"])
    assert audit["original_import"]["package_id"] == accepted["package_id"]


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
            cursor = super().execute(sql,*args,**kwargs)
            if sql == "PRAGMA user_version" and not self.in_transaction:
                # Old code reads version before write lock: force both real reads
                # before either CREATE. Correct code reads under BEGIN and bypasses.
                barrier.wait(timeout=5)
            return cursor
    def connect(*args,**kwargs):
        kwargs["factory"] = OrderedConnection
        return original_connect(*args,**kwargs)
    monkeypatch.setattr(sqlite3,"connect",connect)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(store.migrate) for _ in range(2)]
        assert [future.result(timeout=10) for future in futures] == [2,2]
'''
    assert 'def test_jr13_review_unacknowledgeable' not in path.read_text('utf-8')
    with path.open('a',encoding='utf-8') as stream:stream.write(tests)
    print('10 independent-review regression cases appended before product fixes.')

if __name__=='__main__':main()
