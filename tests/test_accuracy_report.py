import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import accuracy_report as r


class ReportTests(unittest.TestCase):
    def test_not_run_and_correct_abstention_are_separate(self):
        row=dict(arm='matrix.catl.deepseek.zai',route='deepseek',variant='zai',state='not_run_missing_context',receipt=None,wall_s=0,
            assessment=[dict(expected_value=10,answered=False,fact_correct=False,citation_supported=False,missing=True,correct_abstention=False)])
        profile=r.profiles([row])['matrix.deepseek.zai']
        self.assertEqual(profile['known_facts_planned'],1);self.assertEqual(profile['calls_executed'],0);self.assertEqual(profile['correct_roic_abstentions'],0)

    def test_numeric_truth_not_promoted_to_cited_support(self):
        row=dict(arm='pack.catl.g3.i0',route='deepseek',variant='enhanced',state='valid',receipt={'usage':{'prompt_tokens':11,'completion_tokens':7}},wall_s=2,
            assessment=[dict(expected_value=10,answered=True,fact_correct=True,citation_supported=False,missing=False,correct_abstention=False)])
        profile=r.profiles([row])['pack_g3.deepseek.enhanced']
        self.assertEqual(profile['numeric_exact_correct'],1);self.assertEqual(profile['unsupported_exact'],1);self.assertEqual(profile['citation_supported'],0)
        self.assertEqual(profile['prompt_tokens'],11)

    def test_missing_second_model_does_not_create_consensus(self):
        row=dict(company='catl',route='deepseek',variant='enhanced',arm='enhanced.catl.deepseek',answers=[dict(question_id='F01',status='answered',value=1,unit='x',period='y',scope='z')],assessment=[dict(question_id='F01',citation_supported=True)])
        first=r.consensus([row])[0]
        self.assertFalse(first['all_four_exactly_agree']);self.assertFalse(first['all_four_cited_supported'])


if __name__=='__main__':unittest.main()
