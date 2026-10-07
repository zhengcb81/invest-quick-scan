"""Offline boundary regressions. Each fixture owns its root; no key or HTTP."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import accuracy_followup as f


class FollowupTests(unittest.TestCase):
    def test_mcp_json_and_single_sse_decode(self):
        class Reply:
            text='event: message\ndata: {"result":{"ok":true}}\n'
            def json(self):raise ValueError()
        self.assertEqual(f.z.decode(Reply()),{'result':{'ok':True}})
        Reply.text='data: {}\ndata: {}'
        with self.assertRaisesRegex(ValueError,'unexpected_mcp_sse'):f.z.decode(Reply())

    def test_provider_error_redacts_credential(self):
        value=f.z.error_summary({'error':{'code':1113,'message':'x key-secret x'}},'key-secret')
        self.assertEqual(value['error_code'],'1113');self.assertNotIn('key-secret',json.dumps(value))

    def test_summary_headers_preserved_but_bounded(self):
        row={'link':'https://www.hkexnews.hk/a','content':'Fiscal 2024 RMB million '+('x'*4500)}
        item=f.normalize(row,'zai','q')
        self.assertEqual(len(item['snippet']),4000);self.assertTrue(item['snippet'].startswith('Fiscal 2024 RMB million'))
        self.assertNotEqual(item['source_id'],f.p.normalize_source(row,'zai','q')['source_id'])
        self.assertIsNone(f.normalize({**row,'link':'file:///C:/x'},'zai','q'))

    def test_source_and_parent_ledger_drift_stop(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'runs',prefix='accuracy-followup-unit-') as tmp:
            base=Path(tmp);parent=base/'parent';diag=base/'diag';run=base/'run'
            for p in [parent,diag,run,run/'source']:p.mkdir()
            (parent/'input-lock.json').write_text('{}');(parent/'attempts.jsonl').write_text('a');(diag/'attempts.jsonl').write_text('b')
            for name in f.FILES:(run/'source'/Path(name).name).write_bytes((ROOT/name).read_bytes())
            reg=dict(parent_lock=f.p.sha(parent/'input-lock.json'),parent_ledgers={str(p):f.p.sha(p/'attempts.jsonl') for p in [parent,diag]},source_revisions={name:f.p.sha(ROOT/name) for name in f.FILES})
            f.b.write_json(run/'registration.json',reg)
            with patch.object(f,'PARENT',parent),patch.object(f,'DIAG',diag):
                f.source_check(run)
                (parent/'attempts.jsonl').write_text('changed')
                with self.assertRaisesRegex(ValueError,'parent_ledger_drift'):f.source_check(run)
                (parent/'attempts.jsonl').write_text('a')
                (run/'source/accuracy_followup.py').write_text('changed')
                with self.assertRaisesRegex(ValueError,'followup_source_drift'):f.source_check(run)

    def test_score_warm_miss_and_reserved_arm_zero_key(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'runs',prefix='accuracy-followup-unit-') as tmp:
            run=Path(tmp);(run/'evidence').mkdir();(run/'cache').mkdir()
            f.b.write_json(run/'companies.json',{'catl':{'entity_id':'synthetic','canonical_name':'Fixture issuer'}})
            f.b.write_json(run/'score-questions.json',[]);f.b.write_json(run/'evidence/catl-enhanced.json',[])
            ledger=type('Ledger',(),{'reserved':{'ATT':{'arm':'same'}}})()
            with patch.object(f,'freeze',return_value='bound'),patch.object(f.b,'read_key',side_effect=AssertionError('credential_read')):
                with self.assertRaisesRegex(ValueError,'warm_score_miss_zero_send'):f.score_request(run,None,None,ledger,'catl','minimax','new',True)
                with self.assertRaisesRegex(ValueError,'score_already_sent_no_resend'):f.score_request(run,None,None,ledger,'catl','minimax','same')

    def test_invalid_score_thought_not_retained(self):
        class Client:
            def __init__(self,*args,**kwargs):pass
            def send_request(self,prompt,system):
                assert isinstance(prompt,str)
                return '<think>PRIVATE_SENTINEL</think>{"answers":[]}'
        module=type('Module',(),{'LLMClient':Client})()
        with tempfile.TemporaryDirectory(dir=ROOT/'runs',prefix='accuracy-followup-unit-') as tmp:
            run=Path(tmp)
            for d in ['evidence','cache','score-results']:(run/d).mkdir()
            f.b.write_json(run/'companies.json',{'catl':{'entity_id':'synthetic','canonical_name':'Fixture'}})
            f.b.write_json(run/'score-questions.json',[{'question_id':'Q1'}]);f.b.write_json(run/'evidence/catl-enhanced.json',[])
            ledger=type('Ledger',(),{'reserved':{}})()
            with patch.object(f,'freeze',return_value='bound'),patch.object(f.b,'read_key',return_value='dummy'):
                result=f.score_request(run,module,None,ledger,'catl','minimax','bad')
            self.assertEqual(result['state'],'invalid_answer')
            self.assertNotIn('PRIVATE_SENTINEL',(run/'score-results/bad.json').read_text())


if __name__=='__main__':unittest.main()
