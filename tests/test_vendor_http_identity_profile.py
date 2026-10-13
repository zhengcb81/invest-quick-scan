"""Synthetic IQS authority/ingest boundaries, never vendor or financial gold."""
import copy
import json
from pathlib import Path
import sys
import unittest
import tempfile
from unittest.mock import patch
from jsonschema import ValidationError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import c06_authority as exporter
import standard_answers as sa
import observation_profiles as profiles
import test_c06_authority as legacy_fixture
from test_standard_answers import rehash

class VendorIdentityProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        legacy_fixture.C06AuthorityTests.setUpClass()
        cls.fixture=legacy_fixture.C06AuthorityTests()

    def authority(self,version='1.2.0'):
        f=self.fixture
        return f.create(contract_versions={**f.versions,'observation_schema':version},observation_schema_version=version)

    def record(self):
        f=self.fixture
        r=sa.build_observations(f.manifest,f.answers,f.receipts)['observations'][0]
        r['schema_version']='1.2.0'
        r['execution'].update(request_id=None,response_id='SYNTHETIC_completion_id',request_payload_sha256='1'*64,response_sha256='2'*64,receipt_sha256='3'*64)
        return rehash(r)

    def test_explicit_new_export_preserves_question_semantics_and_old_context_shape(self):
        old=self.fixture.create();new=self.authority()
        a=old['observation_context'];b=new['observation_context']
        self.assertEqual(set(a),set(b));self.assertEqual(a['schema'],b['schema'])
        self.assertNotEqual(a['observation_schema_sha256'],b['observation_schema_sha256'])
        for qid,previous in a['questions'].items():
            row=copy.deepcopy(b['questions'][qid]);self.assertEqual(row['metadata'].pop('schema_version'),'1.2.0')
            expected=copy.deepcopy(previous);expected['metadata'].pop('schema_version');self.assertEqual(row,expected)

    def test_new_record_preserves_missing_request_and_real_response_separately(self):
        r=self.record();self.assertIs(sa.validate_observation(r,require_published=True,expected_observation_id=r['observation_id']),r)
        self.assertIsNone(r['execution']['request_id']);self.assertEqual(r['execution']['response_id'],'SYNTHETIC_completion_id')

    def test_new_record_accepts_distinct_nonempty_header(self):
        r=self.record();r['execution']['request_id']='SYNTHETIC_header_id';rehash(r)
        sa.validate_observation(r,require_published=True,expected_observation_id=r['observation_id'])

    def test_new_nullable_header_still_requires_key_and_refuses_bad_types(self):
        for value in ('', True, 42, [], {}):
            r=self.record();r['execution']['request_id']=value;rehash(r)
            with self.subTest(value=value),self.assertRaises((ValueError,ValidationError)):
                sa.validate_observation(r)
        r=self.record();r['execution'].pop('request_id');rehash(r)
        with self.assertRaises((ValueError,ValidationError)):sa.validate_observation(r)

    def test_profile_files_refuse_ambiguous_and_nonfinite_json(self):
        with tempfile.TemporaryDirectory(prefix='iqs-execution-profile-json-') as own:
            root=Path(own);p=root/'probe.json'
            with patch.object(profiles,'ROOT',root):
                p.write_text('{"finite":1.25}',encoding='utf-8')
                self.assertEqual(profiles._read('probe.json'),{'finite':1.25})
                for raw in ('{"key":1,"key":2}','{"nested":{"x":1,"x":2}}',
                            '{"x":NaN}','{"x":Infinity}','{"x":1e400}'):
                    p.write_text(raw,encoding='utf-8')
                    with self.subTest(raw=raw),self.assertRaises(ValueError):profiles._read('probe.json')

    def test_registered_schema_and_archived_base_cannot_drift(self):
        root=profiles.ROOT
        catalog=json.loads((root/'schemas/observation-execution-profiles.json').read_bytes())
        resources={path:json.loads((root/path).read_bytes())
                   for path in catalog['profiles'][profiles.VENDOR_HTTP_IDENTITY]['base_resource_sha256']}
        profiles.schema_for('1.2.0',resources)
        bad=copy.deepcopy(resources);bad['schemas/answer-content.schema.json']['$comment']='changed archived schema'
        with self.assertRaisesRegex(ValueError,'archived_base_mismatch'):profiles.schema_for('1.2.0',bad)
        with tempfile.TemporaryDirectory(prefix='iqs-execution-profile-drift-') as own:
            temporary=Path(own);(temporary/'schemas').mkdir()
            (temporary/'schemas/observation-execution-profiles.json').write_bytes(
                (root/'schemas/observation-execution-profiles.json').read_bytes())
            schema=json.loads((root/'schemas/observation-v1.2.schema.json').read_bytes())
            schema['$comment']='altered deployed bytes'
            (temporary/'schemas/observation-v1.2.schema.json').write_text(json.dumps(schema),encoding='utf-8')
            with patch.object(profiles,'ROOT',temporary),self.assertRaisesRegex(ValueError,'schema_hash_mismatch'):
                profiles.schema_for('1.2.0',resources)

    def test_new_profile_closed_required_identity_and_hashes(self):
        for key in ('response_id','request_payload_sha256','response_sha256','receipt_sha256'):
            for kind in ('missing','empty','boolean'):
                r=self.record()
                if kind=='missing':r['execution'].pop(key)
                else:r['execution'][key]='' if kind=='empty' else True
                rehash(r)
                with self.subTest(key=key,kind=kind),self.assertRaises((ValueError,ValidationError)):
                    sa.validate_observation(r,require_published=True,expected_observation_id=r['observation_id'])

    def test_old_null_remains_refused_and_explicit_legacy_export_is_byte_equal(self):
        old=self.fixture.create();new=self.authority('1.1.0');self.assertEqual(sa.digest(old),sa.digest(new))
        r=sa.build_observations(self.fixture.manifest,self.fixture.answers,self.fixture.receipts)['observations'][0]
        r['execution']['request_id']=None;rehash(r)
        with self.assertRaises((ValueError,ValidationError)):sa.validate_observation(r)

    def test_bad_version_and_mismatched_selection_refused(self):
        for v in ('1.3.0','2.0.0'):
            with self.subTest(version=v),self.assertRaises(ValueError):self.authority(v)
        with self.assertRaises(ValueError):
            self.fixture.create(contract_versions={**self.fixture.versions,'observation_schema':'1.1.0'},observation_schema_version='1.2.0')

    def test_new_version_cannot_drop_frozen_module_cycle_or_semantics(self):
        for key in ('cycle_sensitive','module_package_id','question_semantic_sha256'):
            r=self.record();r.pop(key);rehash(r)
            with self.subTest(key=key),self.assertRaises((ValueError,ValidationError)):sa.validate_observation(r)
        r=self.record();r['question_semantic_sha256']='4'*64;rehash(r)
        with self.assertRaises(ValueError):sa.validate_observation(r)

if __name__=='__main__':unittest.main()
