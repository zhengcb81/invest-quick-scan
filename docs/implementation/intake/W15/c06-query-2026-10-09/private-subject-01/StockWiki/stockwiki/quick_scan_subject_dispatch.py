"""Private schema3 extension: actual owner pre-dispatch and atomic post-binding.

Existing observation/ACK transactions are inherited, never reimplemented.
The trusted owner adapter supplying expected_dispatch is pending public CLI
integration; this primitive is not an authentication or production claim.
"""
from __future__ import annotations

import copy
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

from stockwiki.quick_scan_observations import QuickScanObservationStore, ObservationImportError

SCHEMA_VERSION=3
DDL=(
    """CREATE TABLE quick_scan_subject_dispatch (
        dispatch_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
        receipt_id TEXT NOT NULL UNIQUE,
        provider TEXT NOT NULL,
        execution_attempt_id TEXT NOT NULL,
        question_id TEXT NOT NULL,
        request_sha256 TEXT NOT NULL,
        receipt_sha256 TEXT NOT NULL,
        receipt_json TEXT NOT NULL,
        registered_at TEXT NOT NULL,
        UNIQUE(execution_attempt_id,question_id))""",
    """CREATE TABLE quick_scan_subject_binding (
        observation_id TEXT PRIMARY KEY REFERENCES quick_scan_observation(observation_id),
        dispatch_receipt_id TEXT NOT NULL UNIQUE REFERENCES quick_scan_subject_dispatch(receipt_id),
        dispatch_receipt_sha256 TEXT NOT NULL,
        binding_sha256 TEXT NOT NULL,
        binding_json TEXT NOT NULL,
        bound_at TEXT NOT NULL)""",
    """CREATE TRIGGER quick_scan_subject_dispatch_no_update BEFORE UPDATE ON quick_scan_subject_dispatch
       BEGIN SELECT RAISE(ABORT,'subject dispatch is immutable'); END""",
    """CREATE TRIGGER quick_scan_subject_dispatch_no_delete BEFORE DELETE ON quick_scan_subject_dispatch
       BEGIN SELECT RAISE(ABORT,'subject dispatch is immutable'); END""",
    """CREATE TRIGGER quick_scan_subject_binding_no_update BEFORE UPDATE ON quick_scan_subject_binding
       BEGIN SELECT RAISE(ABORT,'subject binding is immutable'); END""",
    """CREATE TRIGGER quick_scan_subject_binding_no_delete BEFORE DELETE ON quick_scan_subject_binding
       BEGIN SELECT RAISE(ABORT,'subject binding is immutable'); END""",
)


def _json(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)


class SubjectBoundObservationStore(QuickScanObservationStore):
    READ_SCHEMA_VERSION=SCHEMA_VERSION

    def __init__(self,paths,*,contract,clock=None):
        super().__init__(paths)
        self.contract=contract
        self.clock=clock or (lambda:datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))

    def migrate(self):
        if self.database_path.exists():
            with closing(sqlite3.connect(self.database_path.as_uri()+'?mode=ro',uri=True)) as con:
                version=int(con.execute('PRAGMA user_version').fetchone()[0])
                if version==SCHEMA_VERSION:
                    self._check_extension(con)
                    return version
                if version>SCHEMA_VERSION:
                    raise ObservationImportError('observation_store_newer_schema')
        super().migrate()  # Existing schema0/1 ->2 behavior and audit are reused.
        con=super()._connect()
        try:
            con.execute('BEGIN IMMEDIATE')
            version=int(con.execute('PRAGMA user_version').fetchone()[0])
            if version==SCHEMA_VERSION:
                self._check_extension(con)
                return version
            if version!=2:
                raise ObservationImportError('subject_dispatch_schema_unavailable')
            for statement in DDL:
                con.execute(statement)
            con.execute('PRAGMA user_version=3')
            con.commit()
            return SCHEMA_VERSION
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    @staticmethod
    def _check_extension(con):
        actual={row[0]:row[1] for row in con.execute(
            "SELECT name,sql FROM sqlite_master WHERE name LIKE 'quick_scan_subject_%'")}
        for statement in DDL:
            name=statement.split()[2]
            if name not in actual or ' '.join(actual[name].split())!=' '.join(statement.split()):
                raise ObservationImportError('subject_dispatch_schema_unavailable')

    def _receipt(self,row):
        try:
            receipt=json.loads(row['receipt_json'],object_pairs_hook=self.contract.qc.module_contract._unique_object)
            self.contract.validate_receipt(receipt,store_id=self.store_id)
            if (self.contract.digest(receipt)!=row['receipt_sha256']
                or receipt['receipt_id']!=row['receipt_id']
                or receipt['request_sha256']!=row['request_sha256']
                or receipt['registered_at']!=row['registered_at']
                or any(receipt['dispatch_request'][k]!=row[k] for k in
                       ('provider','execution_attempt_id','question_id'))):
                raise ValueError('subject_dispatch_receipt_columns_mismatch')
            return receipt
        except (ValueError,TypeError,KeyError,RecursionError) as error:
            raise ObservationImportError('subject_dispatch_receipt_invalid') from error

    def register_dispatch(self,dispatch,*,expected_dispatch):
        # This argument belongs to an independently trusted owner adapter.
        # No public request/CLI is allowed to supply its own expected metadata.
        if dispatch!=expected_dispatch:
            raise ObservationImportError('subject_dispatch_authority_mismatch')
        now=self.clock()
        try:
            request=self.contract.validate_dispatch_request(dispatch,registered_at=now)
        except (ValueError,TypeError,KeyError,RecursionError) as error:
            raise ObservationImportError('subject_dispatch_request_invalid') from error
        self.migrate()
        con=self._connect()
        try:
            con.execute('BEGIN IMMEDIATE')
            row=con.execute('SELECT * FROM quick_scan_subject_dispatch '
                'WHERE execution_attempt_id=? AND question_id=?',
                (request['execution_attempt_id'],request['question_id'])).fetchone()
            if row is not None:
                receipt=self._receipt(row)
                if receipt['dispatch_request']!=request:
                    raise ObservationImportError('subject_dispatch_immutable_conflict')
                return receipt
            previous=con.execute('SELECT observation_id FROM quick_scan_observation WHERE '
                "json_extract(payload_json,'$.execution.attempt_id')=? AND question_id=? LIMIT 1",
                (request['execution_attempt_id'],request['question_id'])).fetchone()
            if previous is not None:
                raise ObservationImportError('subject_dispatch_answer_already_exists')
            receipt={'protocol':'stockwiki.subject_dispatch_receipt/1.0.0','store_id':self.store_id,
                'dispatch_request':request,'request_sha256':self.contract.digest(request),'registered_at':now}
            receipt['receipt_id']='sdr_'+self.contract.digest(receipt)
            con.execute('INSERT INTO quick_scan_subject_dispatch '
                '(receipt_id,provider,execution_attempt_id,question_id,request_sha256,receipt_sha256,receipt_json,registered_at) '
                'VALUES (?,?,?,?,?,?,?,?)',(receipt['receipt_id'],request['provider'],request['execution_attempt_id'],
                request['question_id'],receipt['request_sha256'],self.contract.digest(receipt),_json(receipt),now))
            con.commit()
            return copy.deepcopy(receipt)
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def _apply_one(self,con,decision):
        ack=super()._apply_one(con,decision)
        if ack['status']!='accepted':
            return ack  # Never promote an existing legacy record on replay.
        obs=decision['observation']
        row=con.execute('SELECT * FROM quick_scan_subject_dispatch '
            'WHERE execution_attempt_id=? AND question_id=?',
            (obs['execution']['attempt_id'],obs['question_id'])).fetchone()
        if row is None:
            if con.execute('SELECT 1 FROM quick_scan_subject_dispatch WHERE execution_attempt_id=? LIMIT 1',
                           (obs['execution']['attempt_id'],)).fetchone() is not None:
                raise ObservationImportError('subject_dispatch_original_mismatch')
            return ack  # Genuine legacy import remains unbound, no guessed scope.
        receipt=self._receipt(row)
        original=con.execute('SELECT import_sequence FROM quick_scan_observation WHERE observation_id=?',
                             (obs['observation_id'],)).fetchone()
        now=self.clock()
        try:
            if self.contract.qc._utc(now)<self.contract.qc._utc(ack['received_at']):
                raise ValueError('subject_binding_before_import_ack')
            binding=self.contract.bind_original(receipt,obs,payload_sha256=decision['payload_sha256'],
                observation_sequence=original['import_sequence'],ack_sequence=original['import_sequence'],bound_at=now)
        except (ValueError,TypeError,KeyError,RecursionError) as error:
            raise ObservationImportError('subject_dispatch_original_mismatch') from error
        con.execute('INSERT INTO quick_scan_subject_binding '
            '(observation_id,dispatch_receipt_id,dispatch_receipt_sha256,binding_sha256,binding_json,bound_at) '
            'VALUES (?,?,?,?,?,?)',(obs['observation_id'],receipt['receipt_id'],self.contract.digest(receipt),
                                  self.contract.digest(binding),_json(binding),now))
        return ack

    def binding_for_observation(self,observation_id):
        if not self.database_path.exists():
            return None
        with closing(sqlite3.connect(self.database_path.as_uri()+'?mode=ro',uri=True)) as con:
            con.row_factory=sqlite3.Row
            row=con.execute('SELECT * FROM quick_scan_subject_binding WHERE observation_id=?',
                            (observation_id,)).fetchone()
            if row is None:
                return None
            result=dict(row)
            result['binding']=json.loads(result.pop('binding_json'),
                                        object_pairs_hook=self.contract.qc.module_contract._unique_object)
            if self.contract.digest(result['binding'])!=result['binding_sha256']:
                raise ObservationImportError('subject_binding_hash_mismatch')
            return result

    def dispatch_count(self):
        if not self.database_path.exists():
            return 0
        with closing(sqlite3.connect(self.database_path.as_uri()+'?mode=ro',uri=True)) as con:
            return int(con.execute('SELECT COUNT(*) FROM quick_scan_subject_dispatch').fetchone()[0])
