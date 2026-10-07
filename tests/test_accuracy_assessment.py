import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from accuracy_assessment import evaluate


class AssessmentTests(unittest.TestCase):
    def test_decimal_rounding_boundary_not_expanded(self):
        gold=dict(question_id='F01',expected_value=166.77,absolute_tolerance=.005,unit='CNY_billion',period='2024-H1',scope='consolidated')
        row=dict(question_id='F01',status='answered',value=166.765,unit=gold['unit'],period=gold['period'],scope=gold['scope'],evidence_refs=['S1'])
        self.assertTrue(evaluate([row],[gold],{'F01':['S1']})[0]['fact_correct'])
        self.assertFalse(evaluate([{**row,'value':166.764999}],[gold],{'F01':['S1']})[0]['fact_correct'])
        self.assertFalse(evaluate([{**row,'unit':'CNY_million'}],[gold],{'F01':['S1']})[0]['fact_correct'])


if __name__=='__main__':unittest.main()
