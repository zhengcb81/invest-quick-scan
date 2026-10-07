"""Offline tests for the small Pro experiment; no real keys or network."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import batching_benchmark as b
import batching_benchmark_report as report
import mimo_pro_pilot as p


class PilotTests(unittest.TestCase):
    def test_mixed_thinking_and_json_is_rejected_instead_of_substring_repair(self):
        row=dict(question_id='Q',status='unknown',score=None,confidence='low',rationale='不足',
                 evidence_refs=[],claims=[],counterevidence='不足',sensitivity='补充')
        content=json.dumps({'answers':[row]})
        self.assertEqual(len(b.parse_answers(content,['Q'],[])),1)
        for contaminated in ('<think>synthetic reasoning</think>'+content,'analysis: synthetic\n'+content):
            with self.assertRaises(ValueError):b.parse_answers(contaminated,['Q'],[])

    def test_hidden_reasoning_body_never_enters_saved_receipt(self):
        with tempfile.TemporaryDirectory(dir=ROOT,prefix='iqs-mimo-pro-test-') as tmp:
            ledger=b.Ledger(Path(tmp))
            secret='REASONING_CANARY_MUST_NOT_PERSIST'
            body={'id':'synthetic_response','model':'mimo-v2.6-pro','usage':{
                'prompt_tokens':1,'completion_tokens':2,'completion_tokens_details':{'reasoning_tokens':1}},
                'choices':[{'finish_reason':'stop','message':{'content':'{"answers":[]}','reasoning_content':secret}}]}
            response=SimpleNamespace(status_code=200,json=lambda:body)
            delegate=SimpleNamespace(post=lambda *args,**kwargs:response)
            observer=b.TransportObserver(delegate,ledger,'mimo_pro',{'arm':'synthetic'},
                        {'thinking':{'type':'enabled'},'max_completion_tokens':10000})
            observer.post(b.ROUTES['mimo_pro']['endpoint'],json={'model':'mimo-v2.6-pro',
                          'messages':[{'role':'user','content':'synthetic'}]})
            self.assertNotIn(secret,json.dumps(observer.receipt))
            self.assertNotIn(secret,(Path(tmp)/'attempts.jsonl').read_text(encoding='utf-8'))
            self.assertEqual(observer.receipt['usage']['completion_tokens_details']['reasoning_tokens'],1)

    def test_model_price_and_same_key(self):
        self.assertEqual(b.ROUTES['mimo_pro']['key_env'],b.ROUTES['mimo']['key_env'])
        cost=report.token_cost({'usage':{'prompt_tokens':1000,'completion_tokens':100,
             'prompt_tokens_details':{'cached_tokens':800}}},'mimo_pro')
        self.assertAlmostEqual(cost['reference_usd'],.00017688)

    def test_question_set_and_budget_count(self):
        self.assertEqual(len(set(p.QIDS)),10)
        self.assertEqual(3*3*(10+2+1)+3*3+3*2,132)
        self.assertEqual(len(p.TOPICS)*2*len(p.TOPICS['catl']),24)

    def test_source_and_evidence_lock_refuses_drift(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='iqs-mimo-pro-test-') as tmp:
            run=Path(tmp);(run/'source').mkdir();(run/'evidence').mkdir()
            for name in ['questions.json','companies.json','runtime-manifest.json','budget.json','pilot-registration.json']:
                b.write_json(run/name,{})
            for slug in p.TOPICS:
                b.write_json(run/'evidence'/(slug+'-targeted.json'),[])
            for source in p.SOURCES:
                (run/'source'/Path(source).name).write_bytes((ROOT/source).read_bytes())
            with patch.object(b,'verify_model_inputs',return_value='synthetic'):
                first=p.freeze(run)
                self.assertEqual(p.freeze(run,True),first)
            b.write_json(run/'evidence/catl-targeted.json',[{'different':1}])
            with self.assertRaisesRegex(ValueError,'drift'):
                p.freeze(run,True)

    def test_generic_targeted_resume_zero_transport_and_keys(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='iqs-mimo-pro-test-') as tmp:
            run=Path(tmp);(run/'evidence').mkdir()
            path=run/'evidence/catl-targeted.json';b.write_json(path,[])
            b.write_json(run/'catl-targeted-input-lock.json',{'file_sha256':b.hashlib.sha256(path.read_bytes()).hexdigest()})
            with patch.object(b,'read_key',side_effect=AssertionError('key read')):
                self.assertTrue(b.targeted_search(run,None,b.Ledger(run),'catl',p.TOPICS['catl'],p.DOMAINS['catl'])['resumed'])
            path.write_text('[1]',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'drift'):
                b.targeted_search(run,None,b.Ledger(run),'catl')

    def test_completed_block_resume_zero_model_and_keys(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='iqs-mimo-pro-test-') as tmp:
            run=Path(tmp);(run/'blocks').mkdir()
            b.write_json(run/'companies.json',{})
            b.write_json(run/'questions.json',[])
            for s in p.TOPICS:
                for r in p.MODELS:
                    arm=f'pilot-repeat.{s}.{r}.g10.targeted'
                    b.write_json(run/'blocks'/(arm+'.json'),{'run_fingerprint':'frozen','arm':arm})
            with patch.object(p,'freeze',return_value='frozen'),patch.object(b,'install_observer'), \
                 patch.object(b,'call_chunk',side_effect=AssertionError('network')), \
                 patch.object(b,'read_key',side_effect=AssertionError('key')):
                self.assertEqual(p.execute(run,None,b.Ledger(run),'repeat')['model_requests'],0)

    def test_pro_parameters_json_mode_and_thinking_separate_cache(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix='iqs-mimo-pro-test-') as tmp:
            run=Path(tmp);(run/'results').mkdir()
            rows={'answers':[dict(question_id='Q',status='unknown',score=None,confidence='low',rationale='未知',
                  evidence_refs=[],claims=[],counterevidence='不足',sensitivity='补充') ]}
            configs=[]
            class FakeClient:
                def __init__(self,*args,**kwargs):
                    configs.append(b._thread_context.observer.params.copy())
                def send_request(self,*args):
                    b._thread_context.observer.receipt={'finish_reason':'stop'}
                    return json.dumps(rows)
            module=SimpleNamespace(LLMClient=FakeClient)
            company={'canonical_name':'fixture','entity_id':'ENT_fixture','identity_file_sha256':'a'*64}
            questions=[{'question_id':'Q'}]
            with patch.object(b,'read_key',return_value='synthetic-key-not-real'):
                cold=b.call_chunk(module,None,b.Ledger(run),run,company,questions,[],'mimo_pro','pilot.matrix')
                thinking=b.call_chunk(module,None,b.Ledger(run),run,company,questions,[],'mimo_pro','pilot.thinking',
                     generation_overrides={'thinking':{'type':'enabled'},'max_completion_tokens':10000})
            self.assertEqual(configs[0]['response_format'],{'type':'json_object'})
            self.assertEqual(configs[0]['temperature'],0)
            self.assertNotIn('temperature',configs[1])
            self.assertNotEqual(cold['cache_key'],thinking['cache_key'])
            with patch.object(b,'read_key',side_effect=AssertionError('key')):
                cached=b.call_chunk(None,None,b.Ledger(run),run,company,questions,[],'mimo_pro','warm',warm=True)
                self.assertTrue(cached['cache_hit'])


if __name__=='__main__':
    unittest.main()
