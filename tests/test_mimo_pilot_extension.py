"""Fixed paired-input and artifact regression tests; no keys or HTTP."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import batching_benchmark as b
import batching_benchmark_archive as a
import batching_benchmark_report as r
import mimo_pilot_extension as e


class ExtensionTests(unittest.TestCase):
    def test_archived_run_prepare_and_warm_miss_never_send_or_read_keys(self):
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='iqs-mimo-ext-test-') as tmp:
            root=Path(tmp);run=root/'runs/completed';run.mkdir(parents=True)
            (root/'docs/implementation/experiments/artifacts/completed').mkdir(parents=True)
            with patch.object(b,'ROOT',root),patch.object(b,'git_bytes',side_effect=AssertionError('git export')), \
                 patch.object(b,'read_key',side_effect=AssertionError('key')):
                with self.assertRaisesRegex(ValueError,'already_archived'):b.prepare(run)
                with self.assertRaisesRegex(ValueError,'already_archived'):e.prepare(run,'thinking')
                company=dict(entity_id='synthetic',canonical_name='synthetic',identity_file_sha256='a'*64)
                with self.assertRaisesRegex(ValueError,'warm_cache_miss_zero_send'):
                    b.call_chunk(None,None,b.Ledger(run),run,company,[{'question_id':'Q'}],[],'mimo_pro','warm',warm=True)
            self.assertEqual(b.Ledger(run).summary()['model_requests'],0)

    def test_observer_does_not_leak_inherited_temperature_into_actual_payload(self):
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='iqs-mimo-ext-test-') as tmp:
            sent=[]
            response=SimpleNamespace(status_code=200,json=lambda:{'id':'synthetic','model':'mimo-v2.6-pro',
                 'usage':{'prompt_tokens':1,'completion_tokens':1},'choices':[{'finish_reason':'stop','message':{'content':'{}'}}]})
            def post(*args,**kwargs):sent.append(kwargs['json']);return response
            params={'thinking':{'type':'enabled'},'max_completion_tokens':10000,'stream':False}
            observer=b.TransportObserver(SimpleNamespace(post=post),b.Ledger(Path(tmp)),'mimo_pro',{'arm':'synthetic'},params)
            observer.post(b.ROUTES['mimo_pro']['endpoint'],json={'model':'mimo-v2.6-pro',
                 'messages':[{'role':'user','content':'synthetic'}],'temperature':0.7,'max_tokens':4096})
            self.assertNotIn('temperature',sent[0])
            self.assertEqual(set(sent[0]),{'model','messages'}|set(params))

    def test_resigned_child_copy_still_must_match_parent_and_terminal_ledger(self):
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='iqs-mimo-ext-test-') as tmp:
            parent=Path(tmp)/'parent';parent.mkdir();run=Path(tmp)/'child';run.mkdir();(run/'source').mkdir()
            b.write_json(parent/'questions.json',[]);(parent/'attempts.jsonl').write_text('')
            lock=dict(files={'questions.json':e.digest(parent/'questions.json')},system_sha256=b.hashlib.sha256(b.SYSTEM.encode()).hexdigest())
            b.write_json(parent/'pilot-input-lock.json',lock);b.write_json(run/'questions.json',[])
            reg=dict(kind='thinking',parent_input_fingerprint=b.fingerprint(lock),
                     parent_ledgers={str(parent):e.digest(parent/'attempts.jsonl')},
                     parent_file_hashes={'questions.json':e.digest(parent/'questions.json')})
            b.write_json(run/'registration.json',reg)
            for source in e.SOURCES:(run/'source'/Path(source).name).write_bytes((ROOT/source).read_bytes())
            with patch.object(e,'PARENT',parent),patch.object(b,'read_key',side_effect=AssertionError('key')):
                e.freeze_files(run,['questions.json','registration.json']);e.verify(run,'thinking')
                b.write_json(run/'questions.json',[{'wrong':'re-signed'}]);e.freeze_files(run,['questions.json','registration.json'])
                with self.assertRaisesRegex(ValueError,'paired_copy_drift'):e.verify(run,'thinking')
                b.write_json(run/'questions.json',[]);e.freeze_files(run,['questions.json','registration.json'])
                (parent/'attempts.jsonl').write_text('changed')
                with self.assertRaisesRegex(ValueError,'parent_ledger_drift'):e.verify(run,'thinking')

    def test_equal_cap_maps_deepseek_without_conflicting_token_limits(self):
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='iqs-mimo-ext-test-') as tmp:
            run=Path(tmp);(run/'results').mkdir();configs=[]
            rows={'answers':[dict(question_id='Q',status='unknown',score=None,confidence='low',rationale='缺口',
                          evidence_refs=[],claims=[],counterevidence='不足',sensitivity='补充')]}
            class Client:
                def __init__(self,*args,**kwargs):configs.append(dict(b._thread_context.observer.params))
                def send_request(self,*args):
                    b._thread_context.observer.receipt={'finish_reason':'stop'}
                    return json.dumps(rows)
            company=dict(entity_id='synthetic',canonical_name='synthetic',identity_file_sha256='a'*64)
            with patch.object(b,'read_key',return_value='synthetic'):
                for route in ('deepseek','minimax'):
                    for mode in ('off','on'):
                        b.call_chunk(SimpleNamespace(LLMClient=Client),None,b.Ledger(run),run,company,
                                     [{'question_id':'Q'}],[],route,'synthetic',generation_overrides=e.policy(route,mode))
            for cfg in configs:self.assertNotIn('temperature',cfg)
            for cfg in configs[:2]:
                self.assertEqual(cfg['max_tokens'],10000);self.assertNotIn('max_completion_tokens',cfg)
            for cfg in configs[2:]:self.assertTrue(cfg['reasoning_split'])

    def test_archive_owns_lock_and_indexes_every_appended_execution_source(self):
        sys.path.insert(0,str(ROOT/'tests'))
        import test_batching_benchmark_archive as cases
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='iqs-mimo-ext-test-') as tmp,patch.object(b,'ROOT',Path(tmp)):
            root=Path(tmp);run=cases.ArchiveTests().prepare_fixture(root)
            (run/'source').mkdir();(run/'source/runner.py').write_text('synthetic = 1')
            b.write_json(run/'pilot-registration.json',{'synthetic':True})
            lock=run/'orchestrator.lock';lock.write_text(str(os.getpid()))
            dest=root/'docs/implementation/experiments/artifacts/owned'
            with self.assertRaisesRegex(ValueError,'active_run_owner_mismatch'):
                a.archive(run,dest,lock_owner_pid=-1)
            a.archive(run,dest,lock_owner_pid=os.getpid())
            self.assertTrue(lock.exists())
            manifest=json.loads((dest/'archive-manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(set(manifest['retained_files']),{p.name for p in dest.iterdir()}-{'archive-manifest.json'})
            self.assertIn('source-runner.py',manifest['retained_files'])
            self.assertTrue(r.summarize_archive(dest)['archive_statistics_verified'])

    def test_prior_real_archive_still_recomputes_after_new_model_added(self):
        path=ROOT/'docs/implementation/experiments/artifacts/b01-improved-2026-10-07'
        before={p.name:b.hashlib.sha256(p.read_bytes()).hexdigest() for p in path.iterdir()}
        with patch.object(b,'read_key',side_effect=AssertionError('key')):
            result=r.summarize_archive(path)
        self.assertTrue(result['archive_statistics_verified'])
        self.assertNotIn('mimo_pro',result['by_model'])
        self.assertEqual(before,{p.name:b.hashlib.sha256(p.read_bytes()).hexdigest() for p in path.iterdir()})

    def test_thinking_equal_cap_and_provider_specific_policy(self):
        self.assertEqual(e.policy('deepseek','on')['max_completion_tokens'],10000)
        self.assertEqual(e.policy('deepseek','off')['max_completion_tokens'],10000)
        self.assertEqual(e.policy('minimax','on')['thinking'],{'type':'adaptive'})
        self.assertTrue(e.policy('minimax','on')['omit_temperature'])
        self.assertEqual(len(e.blocks_for('thinking')),21)

    def test_parent_drift_refuses_before_key_or_http(self):
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='iqs-mimo-ext-test-') as tmp:
            parent=Path(tmp)
            (parent/'questions.json').write_text('[]',encoding='utf-8')
            lock={'files':{'questions.json':b.hashlib.sha256(b'[]').hexdigest()},'system_sha256':b.hashlib.sha256(b.SYSTEM.encode()).hexdigest()}
            b.write_json(parent/'pilot-input-lock.json',lock)
            e.check_parent(parent)
            (parent/'questions.json').write_text('[1]',encoding='utf-8')
            with patch.object(b,'read_key',side_effect=AssertionError('key')),self.assertRaisesRegex(ValueError,'parent_input_drift'):
                e.check_parent(parent)

    def test_copied_evidence_source_and_budget_lock_all_fail_closed(self):
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='iqs-mimo-ext-test-') as tmp:
            run=Path(tmp);(run/'source').mkdir()
            for name in ('questions.json','budget.json','registration.json'):
                b.write_json(run/name,{'test':'original'})
            for source in e.SOURCES:
                (run/'source'/Path(source).name).write_bytes((ROOT/source).read_bytes())
            e.freeze_files(run,['questions.json','budget.json','registration.json'])
            e.verify_files(run)
            for name in ('questions.json','budget.json','registration.json','source/mimo_pilot_extension.py'):
                path=run/name;old=path.read_bytes();path.write_bytes(old+b' ')
                with self.assertRaisesRegex(ValueError,'extension_input_drift'):
                    e.verify_files(run)
                path.write_bytes(old)


if __name__=='__main__':unittest.main()
