import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import batching_benchmark as b
import batching_benchmark_report as report


class ReportTests(unittest.TestCase):
    def test_usage_cache_and_missing_usage_are_not_zero_cost_proof(self):
        x=report.token_cost({'usage':{'prompt_tokens':1000,'completion_tokens':100,'prompt_cache_hit_tokens':800}},'deepseek')
        self.assertEqual(x['cached_tokens'],800)
        self.assertAlmostEqual(x['reference_usd'],.0001848)
        self.assertIsNone(report.token_cost({},'deepseek')['reference_usd'])
        self.assertIsNone(report.token_cost({'usage':{'prompt_tokens':-1,'completion_tokens':10}},'deepseek')['reference_usd'])

    def test_repair_counts_only_new_valid_qids_and_rejects_repeat(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            run=Path(tmp);(run/'results').mkdir();(run/'blocks').mkdir()
            usage={'usage':{'prompt_tokens':100,'completion_tokens':10}}
            row=lambda q:dict(question_id=q,status='unknown',score=None)
            b.write_json(run/'results/first.json',{'answers':[row('Q1')],'item_inspection':{'answers':[row('Q2')]},'receipt':usage})
            b.write_json(run/'results/follow.json',{'answers':[row('Q3')],'receipt':usage})
            base=dict(company='C',route='minimax',group_size=5,requested=3,valid_rows=1,scored=0,wall_s=10,question_ids=['Q1','Q2','Q3'])
            b.write_json(run/'blocks/first.json',{**base,'arm':'first','stage':'minimax-small5','chunks':['first']})
            b.write_json(run/'blocks/follow.json',{**base,'arm':'follow','stage':'minimax-repair','group_size':1,'requested':1,'chunks':['follow']})
            (run/'attempts.jsonl').write_text('',encoding='utf-8')
            chain=report.summarize(run)['repair_chains'][0]
            self.assertEqual(chain['final_valid_rows'],3)
            self.assertEqual(chain['initial_rows_with_item_validation'],2)
            self.assertEqual(chain['remaining_invalid'],0)
            b.write_json(run/'results/follow.json',{'answers':[row('Q2')],'receipt':usage})
            with self.assertRaisesRegex(ValueError,'repeated_valid_item'):report.summarize(run)

    def test_same_baseline_survives_multiple_pairings_and_unknown_excluded(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            run=Path(tmp);(run/'results').mkdir();(run/'blocks').mkdir()
            for group,score in [(1,7),(5,8),(30,None)]:
                row=dict(question_id='Q1',status='scored' if score else 'unknown',score=score)
                key='CHK_'+str(group)
                b.write_json(run/'results'/(key+'.json'),{'answers':[row],'receipt':{'usage':{'prompt_tokens':100,'completion_tokens':10}}})
                block=dict(arm='g'+str(group),stage='core',company='C',route='deepseek',group_size=group,
                           requested=1,valid_rows=1,scored=int(bool(score)),wall_s=10/group,chunks=[key])
                b.write_json(run/'blocks'/('g'+str(group)+'.json'),block)
            (run/'attempts.jsonl').write_text('',encoding='utf-8')
            out=report.summarize(run);rows={x['group_size']:x for x in out['blocks']}
            self.assertEqual(rows[5]['scored_mae'],1)
            self.assertEqual(rows[30]['scored_pair_n'],0)
            self.assertIsNone(rows[30]['scored_mae'])
            self.assertEqual(rows[30]['status_agreement'],0)

    def test_search_baseline_never_crosses_context_or_question_set(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            run=Path(tmp);(run/'results').mkdir();(run/'blocks').mkdir()
            for name,group,variant,sha,wall in [('a-brave',1,'brave','a',20),('b-tavily',1,'tavily','b',10),('c-tavily',5,'tavily','b',5),('d-drift',5,'tavily','changed',4)]:
                b.write_json(run/'results'/(name+'.json'),{'answers':[{'question_id':'Q1','status':'scored','score':7}],'receipt':{'usage':{'prompt_tokens':100,'completion_tokens':10}}})
                b.write_json(run/'blocks'/(name+'.json'),dict(arm=name,stage='search-cross',company='C',route='deepseek',group_size=group,requested=1,valid_rows=1,scored=1,wall_s=wall,chunks=[name],evidence_variant=variant,evidence_sha256=sha,question_ids=['Q1'],prompt_profile='v5'))
            (run/'attempts.jsonl').write_text('',encoding='utf-8')
            rows={x['arm']:x for x in report.summarize(run)['blocks']}
            self.assertEqual(rows['c-tavily']['speedup_vs_baseline'],2)
            self.assertNotIn('speedup_vs_baseline',rows['d-drift'])


if __name__=='__main__':unittest.main()
