"""Narrow but meaningful diagnostic contracts, no real keys or HTTP."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import accuracy_pilot as p


class AccuracyPilotTests(unittest.TestCase):
    def setUp(self):
        self.row=dict(question_id='F01',status='answered',value=166.77,unit='CNY_billion',period='2024-H1',scope='consolidated',evidence_refs=['S1'],rationale='已核')
        self.gold=dict(question_id='F01',expected_value=166.77,absolute_tolerance=.005,unit='CNY_billion',period='2024-H1',scope='consolidated')

    def test_true_value_and_source_are_separate(self):
        result=p.evaluate([self.row],[self.gold],{'F01':[]})[0]
        self.assertTrue(result['fact_correct']);self.assertFalse(result['citation_supported'])
        self.assertTrue(p.evaluate([self.row],[self.gold],{'F01':['S1']})[0]['citation_supported'])

    def test_unit_period_and_scope_errors_are_wrong(self):
        for field,bad in [('unit','CNY_million'),('period','2024-FY'),('scope','parent_only'),('value',1667.7)]:
            with self.subTest(field=field):
                row={**self.row,field:bad}
                self.assertFalse(p.evaluate([row],[self.gold],{'F01':['S1']})[0]['fact_correct'])

    def test_wrong_extra_citation_is_not_supported(self):
        row={**self.row,'evidence_refs':['S1','irrelevant']}
        self.assertFalse(p.evaluate([row],[self.gold],{'F01':['S1']})[0]['citation_supported'])

    def test_unknown_is_not_fake_correct_numeric_answer(self):
        row={**self.row,'status':'unknown','value':None,'evidence_refs':[]}
        result=p.evaluate([row],[self.gold],{})[0]
        self.assertFalse(result['fact_correct']);self.assertFalse(result['answered']);self.assertFalse(result['correct_abstention'])
        gold={**self.gold,'expected_value':None}
        self.assertTrue(p.evaluate([row],[gold],{})[0]['correct_abstention'])
        self.assertFalse(p.evaluate([self.row],[gold],{})[0]['fact_correct'])
        self.assertFalse(p.evaluate([{**row,'period':'2025-FY'}],[gold],{})[0]['correct_abstention'])

    def test_frozen_float_boundary_limitation_recorded(self):
        # Frozen pilot v1 slightly exceeds .005 in binary float at this boundary.
        # Keep historical behavior; assessment v2 tests the corrected arithmetic.
        self.assertFalse(p.evaluate([{**self.row,'value':166.765}],[self.gold],{'F01':['S1']})[0]['fact_correct'])

    def test_strict_envelope_no_thought_extraction(self):
        body=json.dumps({'answers':[self.row]})
        self.assertEqual(p.parse(body,['F01'],['S1']),[self.row])
        self.assertEqual(p.parse('```json\n'+body+'\n```',['F01'],['S1']),[self.row])
        for invalid in ['<think>private</think>'+body,body[:-1],body.replace('"F01"','"F02"'),'{"answers":[],"answers":[]}']:
            with self.subTest(invalid=invalid[:25]),self.assertRaises(ValueError):p.parse(invalid,['F01'],['S1'])

    def test_nonfinite_bool_unknown_value_and_missing_refs_reject(self):
        for changes in [{'value':True},{'value':float('nan')},{'status':'unknown'},{'evidence_refs':[]},{'evidence_refs':['foreign']}]:
            with self.subTest(changes=changes),self.assertRaises(ValueError):p.parse(json.dumps({'answers':[{**self.row,**changes}]}),['F01'],['S1'])

    def test_gold_expected_answers_are_not_questions(self):
        reference=p.read(p.REFERENCE)
        self.assertEqual(len(reference['companies']),3)
        for slug in reference['companies']:
            qs=p.questions(reference,slug);self.assertEqual(len(qs),6)
            self.assertEqual([x['question_id'] for x in qs],['F01','F02','F03','F04','F05','F06'])
            self.assertNotIn('expected_value',json.dumps(qs));self.assertNotIn('absolute_tolerance',json.dumps(qs))

    def test_thinking_on_explicit_parameter_policy(self):
        for route in p.MODELS:
            cfg=p.policy(route);self.assertNotIn('temperature',cfg)
            self.assertEqual(cfg['thinking']['type'],'adaptive' if route=='minimax' else 'enabled')
            self.assertEqual(cfg['max_tokens' if route=='deepseek' else 'max_completion_tokens'],10000)
            if route=='minimax':self.assertTrue(cfg['reasoning_split'])

    def test_search_normalization_bounds_and_no_raw_content(self):
        item=p.normalize_source({'url':'https://catl.com/news','title':'t','description':'x'*1400,'extra_snippets':['other']},'brave','q')
        self.assertEqual(len(item['snippet']),1200)
        self.assertIsNone(p.normalize_source({'url':'file:///C:/secret','description':'secret'},'brave','q'))
        self.assertIsNone(p.normalize_source({'link':'https://example.com','content':'Access Denied'},'zai','q'))

    def test_missing_items_stay_missing(self):
        self.assertTrue(p.evaluate([], [self.gold], {})[0]['missing'])

    def test_provider_cooldown_skips_other_companies_zero_key(self):
        own=ROOT/'runs';own.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=own,prefix='accuracy-pilot-unit-') as tmp:
            run=Path(tmp);(run/'evidence').mkdir()
            p.b.write_json(run/'companies.json',{'catl':{},'cncb_h':{},'alphabet':{}})
            for slug in ('catl','cncb_h','alphabet'):
                for provider in ('brave','tavily'):p.b.write_json(run/'evidence'/(slug+'-'+provider+'.json'),[])
            ledger=type('Ledger',(),{'reserved':{'ATT':{'provider':'zai'}},'finished':{'ATT':{'http_status':429}},'summary':lambda self:{'http':0}})()
            module=type('Module',(),{'http_client_manager':type('Manager',(),{'get_sync_session':lambda self:None})()})()
            with patch.object(p.b,'read_key',side_effect=AssertionError('key_read')):
                result=p.retrieve(run,module,ledger)
            self.assertEqual(len(result['search_summary']),3)
            self.assertTrue(all(x['state']=='provider_cooldown' for x in result['search_summary']))

    def test_warm_miss_and_duplicate_send_zero_key_reads(self):
        own=ROOT/'runs';own.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=own,prefix='accuracy-pilot-unit-') as tmp:
            run=Path(tmp);(run/'cache').mkdir();(run/'evidence').mkdir()
            p.b.write_json(run/'companies.json',{'catl':{'entity_id':'synthetic'}})
            p.b.write_json(run/'evidence/catl-curated.json',[])
            ledger=type('Ledger',(),{'reserved':{'ATT':{'arm':'same'}}})()
            with patch.object(p,'freeze',return_value='bound'),patch.object(p.b,'read_key',side_effect=AssertionError('credential_read')):
                with self.assertRaisesRegex(ValueError,'warm_miss_zero_send'):p.request(run,None,None,ledger,'catl','deepseek','curated',[],'new',warm=True)
                with self.assertRaisesRegex(ValueError,'arm_already_sent_no_resend'):p.request(run,None,None,ledger,'catl','deepseek','curated',[],'same')


if __name__=='__main__':unittest.main()
