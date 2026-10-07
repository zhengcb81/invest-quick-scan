"""Offline invariants for the paid pilot; never reads keys or sends HTTP."""
import json
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import batching_benchmark as b


def answer(qid='Q1', **updates):
    obj = dict(question_id=qid, status='scored', score=7, confidence='medium',
               rationale='已有客户付费记录；留存证据有限。', evidence_refs=['S1'],
               claims=[dict(text='已有客户付费记录', source_ids=['S1'])],
               counterevidence='留存证据有限', sensitivity='客户流失将降低判断')
    obj.update(updates)
    return obj


class BenchmarkTests(unittest.TestCase):
    def test_caps_cannot_expand_human_authorization(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            for caps in ({'model_cap':b.AUTHORIZED_CAPS['model']+1},{'search_cap':201},{'usd_cap':26},
                         {'model_cap':True},{'usd_cap':float('nan')}):
                with self.subTest(caps=caps),self.assertRaises(ValueError):
                    b.Ledger(Path(tmp),**caps)
            self.assertFalse((Path(tmp)/'attempts.jsonl').exists())

    def test_item_recovery_does_not_edit_or_overwrite_answers(self):
        good=answer('Q1');bad=answer('Q2',status='unknown',score=5)
        recovered=b.inspect_items(json.dumps({'answers':[good,bad]}),['Q1','Q2'],['S1'])
        self.assertEqual(recovered['answers'],[good])
        self.assertEqual(recovered['rejected'],[{'question_id':'Q2','reason':'unknown_has_score'}])
        self.assertEqual(recovered['missing'],[])
        missing=b.inspect_items(json.dumps({'answers':[good]}),['Q1','Q2'],['S1'])
        self.assertEqual(missing['answers'],[good]);self.assertEqual(missing['missing'],['Q2'])
        for rows in ([good,good],[good,answer('EXTRA')]):
            with self.assertRaises(ValueError):b.inspect_items(json.dumps({'answers':rows}),['Q1','Q2'],['S1'])
        with self.assertRaises(ValueError):b.inspect_items('{"answers":[],"answers":[]}',[],[])
        with self.assertRaises(ValueError):b.inspect_items(json.dumps({'answers':[good]})+'junk',['Q1'],['S1'])

    def test_targeted_resume_zero_network_and_refuses_changed_pool(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            run=Path(tmp);(run/'evidence').mkdir()
            p=run/'evidence/cncb_h-targeted.json'
            b.write_json(p,[])
            b.write_json(run/'targeted-input-lock.json',
                         {'file_sha256':b.hashlib.sha256(p.read_bytes()).hexdigest()})
            with patch.object(b,'read_key',side_effect=AssertionError('no credentials')):
                self.assertTrue(b.targeted_search(run,None,b.Ledger(run))['resumed'])
                b.write_json(p,[{'changed':1}])
                with self.assertRaisesRegex(ValueError,'drift'):
                    b.targeted_search(run,None,b.Ledger(run))

    def test_scoped_preparation_is_immutable_and_marks_shared_document(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            run=Path(tmp);(run/'evidence').mkdir()
            items=[dict(source_id=s,url='https://www.hkexnews.hk/report.pdf',
                        snippet='中信建投2025年披露事实',title='report',published_at=None)
                   for s in b.SCOPED_SOURCES]
            p=run/'evidence/cncb_h-targeted.json';b.write_json(p,items)
            b.write_json(run/'targeted-input-lock.json',
                         {'file_sha256':b.hashlib.sha256(p.read_bytes()).hexdigest()})
            b.prepare_scoped(run)
            original=(run/'evidence/cncb_h-scoped.json').read_bytes()
            b.prepare_scoped(run)
            self.assertEqual(original,(run/'evidence/cncb_h-scoped.json').read_bytes())
            scoped=json.loads(original)
            self.assertEqual(len({x['document_family'] for x in scoped}),1)
            self.assertTrue(all(x['published_at'] is None for x in scoped))
            (run/'evidence/cncb_h-scoped.json').write_text('[]',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'drift'):b.prepare_scoped(run)

    def test_strict_parser_and_unknown(self):
        self.assertEqual(b.parse_answers(json.dumps({'answers': [answer()]}), ['Q1'], ['S1'])[0]['score'], 7)
        unknown = answer(status='insufficient_evidence', score=None, claims=[], evidence_refs=[])
        self.assertIsNone(b.parse_answers(json.dumps({'answers': [unknown]}), ['Q1'], ['S1'])[0]['score'])
        self.assertEqual(b.parse_answers('```json\n'+json.dumps({'answers':[answer()]})+'\n```',['Q1'],['S1'])[0]['score'],7)
        bad = [answer(score=True), answer(score=11), answer(status='unknown', score=5),
               answer(evidence_refs=['BOGUS']), answer(claims=[dict(text='x', source_ids=['BOGUS'])])]
        for row in bad:
            with self.subTest(row=row), self.assertRaises(ValueError):
                b.parse_answers(json.dumps({'answers': [row]}), ['Q1'], ['S1'])

    def test_duplicate_extra_missing_and_json_keys_rejected(self):
        for rows in ([answer(), answer()], [answer('Q2')], []):
            with self.assertRaises(ValueError):
                b.parse_answers(json.dumps({'answers': rows}), ['Q1'], ['S1'])
        with self.assertRaises(ValueError):
            b.parse_answers('{"answers":[],"answers":[]}', ['Q1'], ['S1'])
        with self.assertRaises(ValueError):
            b.parse_answers(json.dumps({'answers': [answer()]}) + 'more', ['Q1'], ['S1'])

    def test_prompt_no_example_or_forced_cycle_shared_once(self):
        qs = [dict(question_id='Q1', text='客户价值？', anchors={'1':'差','5':'一般','10':'好'}, rubric_version='1')]
        sys_p, p = b.build_prompt({'canonical_name':'宁德时代','entity_id':'ENT_real','ticker':'300750'}, qs, [])
        self.assertNotIn('EXAMPLE', p)
        self.assertNotIn('trough', p)
        self.assertEqual(p.count('客户价值？'), 1)
        self.assertIn('insufficient_evidence', sys_p)
        self.assertNotIn('仅外层兼容', sys_p + p)

    def test_durable_atomic_budget_and_unknown_hold(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            ledger = b.Ledger(Path(tmp), model_cap=5, search_cap=2, usd_cap=1)
            def reserve(_):
                try:
                    return ledger.reserve('model', 0.1, {'chunk_id':str(_)})
                except b.BudgetExceeded:
                    return None
            with ThreadPoolExecutor(max_workers=8) as pool:
                ids = list(pool.map(reserve, range(20)))
            self.assertEqual(sum(x is not None for x in ids), 5)
            self.assertEqual(b.Ledger(Path(tmp), model_cap=5, search_cap=2, usd_cap=1).summary()['model_requests'], 5)
            self.assertEqual(ledger.summary()['unresolved_attempts'], 5)
            with self.assertRaises(b.BudgetExceeded):
                ledger.reserve('model', 0, {})

    def test_cash_cap_and_no_double_settlement(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            ledger = b.Ledger(Path(tmp), model_cap=10, search_cap=10, usd_cap=.15)
            aid = ledger.reserve('model', .1, {})
            with self.assertRaises(b.BudgetExceeded):
                ledger.reserve('search', .1, {})
            ledger.finish(aid, {'attempt_id':aid,'state':'completed','upper_usd':.02})
            with self.assertRaises(ValueError):
                ledger.finish(aid, {'state':'completed','upper_usd':0})
            self.assertIsInstance(ledger.reserve('search', .1, {}), str)

    def test_corrupt_or_duplicate_persisted_ledger_fails_closed(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            run=Path(tmp);ledger=b.Ledger(run);aid=ledger.reserve('model',.1,{})
            original=ledger.path.read_text(encoding='utf-8')
            ledger.path.write_text(original+original,encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'duplicate'):b.Ledger(run)
            ledger.path.write_text(original+json.dumps({'event':'finished','attempt_id':'other'})+'\n',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'unknown'):b.Ledger(run)
            ledger.path.write_text(original.replace('0.1','NaN'),encoding='utf-8')
            with self.assertRaises(ValueError):b.Ledger(run)

    def test_cache_key_includes_route_rubric_cutoff_evidence_and_params(self):
        base = dict(identity={'id':'ENT_a'}, questions=[{'id':'Q1','rubric':'1'}],
                    evidence=[{'id':'S1','snippet':'a'}], route='deepseek', cutoff='2026-10-07', params={'temperature':0})
        old = b.fingerprint(base)
        for key in base:
            changed = dict(base); changed[key] = 'different'
            self.assertNotEqual(old, b.fingerprint(changed))

    def test_application_cache_zero_send_and_model_separation(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            cache = b.AnswerCache(Path(tmp))
            cache.put('a' * 64, {'attempt_id':'ATT_A','answers':[answer()]})
            self.assertEqual(cache.get('a' * 64)['attempt_id'], 'ATT_A')
            self.assertIsNone(cache.get('b' * 64))

    def test_filter_issuer_and_future_source(self):
        identity = dict(canonical_name='中信建投证券', aliases=['中信建投','China Securities','CSC Financial'], issuer_domains=['csc108.com','hkexnews.hk'])
        items = [dict(title='某设备IPO 中信建投证券承销',url='https://example.com/a',snippet='EDA设备业务'),
                 dict(title='中信建投证券 年度业绩',url='https://csc108.com/ir',snippet='本公司证券经纪业务收入',published_at='2026-03-01'),
                 dict(title='中信建投 2027',url='https://example.com/c',snippet='预计利润',published_at='2027-01-01')]
        out, rejects = b.filter_evidence(items, identity, '2026-10-07')
        self.assertEqual(len(out), 1)
        self.assertEqual(len(rejects), 2)

    def test_frozen_runtime_is_explicit_allowlist_only(self):
        self.assertIn('src/providers/llm_client.py', b.RUNTIME_FILES)
        self.assertFalse(any('llm_apis' in f or f.endswith('.json') for f in b.RUNTIME_FILES))

    def test_transport_budget_receipt_and_unknown(self):
        class Response:
            status_code=200
            def json(self):
                return dict(id='RESP_A',model='actual',usage={'prompt_tokens':20,'completion_tokens':10},
                            choices=[{'finish_reason':'stop','message':{'content':'{}'}}])
        class Session:
            sent=0
            def post(self, url, **kwargs):
                self.sent+=1
                self.kwargs=kwargs
                return Response()
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            ledger=b.Ledger(Path(tmp),model_cap=1)
            delegate=Session()
            observer=b.TransportObserver(delegate,ledger,'deepseek',{'arm':'probe'}, {'max_tokens':100,'temperature':0})
            observer.post(b.ROUTES['deepseek']['endpoint'],json={'messages':[{'content':'hi'}],'model':'deepseek-flash'},headers={})
            self.assertEqual(delegate.sent,1)
            self.assertFalse(delegate.kwargs['allow_redirects'])
            self.assertEqual(observer.receipt['response_id'],'RESP_A')
            self.assertEqual(ledger.summary()['unresolved_attempts'],0)
            with self.assertRaises(b.BudgetExceeded):
                observer.post(b.ROUTES['deepseek']['endpoint'],json={'model':'deepseek-flash','messages':[{'content':'hi'}]},headers={})
            self.assertEqual(delegate.sent,1)

    def test_timeout_no_retry_and_reservation_held(self):
        class Session:
            sent=0
            def post(self,*args,**kwargs):
                self.sent+=1
                raise TimeoutError('sensitive outbound body must not be saved')
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            ledger=b.Ledger(Path(tmp));delegate=Session()
            observer=b.TransportObserver(delegate,ledger,'deepseek',{'arm':'probe'},{'max_tokens':100})
            with self.assertRaises(RuntimeError):
                observer.post(b.ROUTES['deepseek']['endpoint'],json={'model':'deepseek-flash','messages':[{'content':'hi'}]},headers={})
            self.assertEqual(delegate.sent,1)
            self.assertEqual(observer.receipt['state'],'outcome_unknown')
            self.assertGreater(ledger.summary()['charged_upper_usd'],0)
            self.assertEqual(ledger.summary()['unresolved_attempts'],1)
            self.assertNotIn('sensitive',ledger.path.read_text(encoding='utf-8'))

    def test_cooldown_blocks_queued_request_before_reserve(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            ledger=b.Ledger(Path(tmp))
            aid=ledger.reserve('model',.1,{'route':'minimax'})
            ledger.finish(aid,{'state':'http_rejected','http_status':429})
            with self.assertRaisesRegex(b.BudgetExceeded,'cooldown'):
                ledger.reserve('model',.1,{'route':'minimax'})
            self.assertIsInstance(ledger.reserve('model',.1,{'route':'deepseek'}),str)
            self.assertEqual(ledger.summary()['model_requests'],2)

    def test_input_drift_and_prepare_after_send_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            run=Path(tmp);(run/'evidence').mkdir()
            for f in ('questions.json','companies.json','runtime-manifest.json'):
                (run/f).write_text('{}',encoding='utf-8')
            b.verify_model_inputs(run)
            (run/'questions.json').write_text('{"changed":1}',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'drift'):
                b.verify_model_inputs(run)
            ledger=b.Ledger(run);ledger.reserve('model',0,{})
            with self.assertRaisesRegex(ValueError,'forbidden'):
                b.prepare(run)

    def test_call_chunk_warm_path_never_constructs_client_or_reads_key(self):
        from unittest.mock import patch
        company=dict(canonical_name='C',entity_id='ENT_a',ticker='A',identity_file_sha256='a'*64)
        qs=[dict(question_id='Q1',text='q',anchors={'1':'a','5':'b','10':'c'},rubric_version='1')]
        params=dict(temperature=0,stream=False,thinking={'type':'disabled'},max_tokens=1624,response_format={'type':'json_object'})
        system,prompt=b.build_prompt(company,qs,[])
        key=b.fingerprint(dict(route=b.ROUTES['deepseek'],system=system,prompt=prompt,parameters=params,parser_version='4',transport_parameter_policy='explicit_only/2'))
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            run=Path(tmp);b.AnswerCache(run/'cache').put(key,{'cache_hit':False,'arm':'first','repeat':0,'answers':[answer()]})
            with patch.object(b,'read_key',side_effect=AssertionError('must not read key')):
                result=b.call_chunk(None,None,b.Ledger(run),run,company,qs,[],'deepseek','warm',warm=True)
            self.assertTrue(result['cache_hit'])
            self.assertEqual(b.Ledger(run).summary()['model_requests'],0)

    def test_projection_normalization_never_invents_or_deduplicates_items(self):
        projected={'answers':[answer('Q1')],**answer('Q2')}
        self.assertEqual(len(b.parse_answers(json.dumps(projected),['Q1','Q2'],['S1'])),2)
        for bad in ({'answers':[answer()],**answer()},
                    {'answers':[],**answer('Q2')},
                    {'answers':[answer()], 'score':7}):
            with self.assertRaises(ValueError):
                b.parse_answers(json.dumps(bad),['Q1','Q2'],['S1'])


if __name__ == '__main__':
    unittest.main()
