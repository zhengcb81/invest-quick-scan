"""Frozen controller counterexamples against the delivered Lab snapshot."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

from iqs_evidence_lab import cli
from iqs_evidence_lab.fixtures import archive_provenance_verifier
from iqs_evidence_lab.hashing import read_json
from iqs_evidence_lab.semantic import check_dimension, check_sources

LAB = Path(os.environ['E97_LAB_ROOT'])
CASES = LAB / '.controller-cases-r2'
CASES.mkdir(exist_ok=False)


def public(args):
    return subprocess.run([sys.executable, '-B', '-X', 'utf8', '-m', 'iqs_evidence_lab', *args],
        cwd=LAB, env=dict(os.environ), capture_output=True, timeout=180)


class AcceptanceCases(unittest.TestCase):
    def test_quarter_dictionary_conflict(self):
        result = check_dimension('period', {'kind':'quarter','year':2026,'quarter':1}, {'kind':'quarter','year':2026,'quarter':4})
        self.assertEqual(result.outcome, 'fail', result)

    def test_half_dictionary_conflict(self):
        result = check_dimension('period', {'kind':'half_year','year':2026,'half':1}, {'kind':'half_year','year':2026,'half':2})
        self.assertEqual(result.outcome, 'fail', result)

    def test_missing_year_abstains(self):
        result = check_dimension('period', '2026H1', 'H1')
        self.assertEqual(result.outcome, 'abstain', result)

    def test_missing_source_window_abstains(self):
        rows = check_sources({'sources':[{'url':'https://example.com/report'}]})
        result = next(r for r in rows if r.check=='source.url_window')
        self.assertEqual(result.outcome, 'abstain', result)

    def test_same_report_comparison_columns_not_conflict(self):
        rows = check_sources({'sources':[{'url':'https://example.com/report','period':'2026'}, {'url':'https://example.com/report','period':'2025'}]})
        result = next(r for r in rows if r.check=='source.url_window')
        self.assertNotEqual(result.outcome, 'fail', result)

    def test_wrong_locked_file_rejected_by_public_cli(self):
        wrong = Path(os.environ['IQS_EVIDENCE_LAB_IQS_ROOT']) / 'docs/implementation/experiments/mimo-pilot-pricing-2026-10-07.json'
        out = CASES / 'wrong-index-out'
        result = public(['replay','--input',str(wrong),'--output',str(out)])
        (CASES/'wrong-index.stdout.log').write_bytes(result.stdout)
        (CASES/'wrong-index.stderr.log').write_bytes(result.stderr)
        self.assertIn(result.returncode, (2,5), 'A locked pricing file must not be labeled a result index')
        self.assertFalse(out.exists())

    def test_duplicate_fixture_source_category_rejected(self):
        raw = (LAB/'fixtures/synthetic/FX-001.json').read_text('utf-8')
        raw = raw.replace('"source_category": "synthetic"', '"source_category": "historical_model_output", "source_category": "synthetic"')
        fixture = CASES/'duplicate-category.json'; fixture.write_text(raw,encoding='utf-8')
        out = CASES/'duplicate-out'
        result = public(['replay','--input',str(fixture),'--output',str(out)])
        (CASES/'duplicate.stdout.log').write_bytes(result.stdout)
        (CASES/'duplicate.stderr.log').write_bytes(result.stderr)
        self.assertEqual(result.returncode, 4, 'Conflicting provenance keys must not silently use the last value')
        self.assertFalse(out.exists())

    def test_io_failure_does_not_leave_partial_output(self):
        out = CASES/'write-failed-out'
        original = Path.write_text
        def write(path, *args, **kwargs):
            if path.name == 'metrics.json' and path.parent.name.startswith('staging-'):
                raise OSError('controller injected disk write failure')
            return original(path,*args,**kwargs)
        with patch.object(Path, 'write_text', write):
            code = cli.main(['replay','--input','index','--output',str(out)])
        self.assertEqual(code,1)
        self.assertFalse(out.exists(), 'Failed publication must not poison an exclusive output path')
        self.assertFalse(list(cli.STAGING_ROOT.glob('staging-*')), 'Failed run staging remains')
        self.assertEqual(cli.main(['replay','--input','index','--output',str(out)]),0, 'Same path retry fails')

    def test_historical_chunk_answer_tampering_rejected(self):
        fixture = read_json(LAB/'fixtures/historical/FX-031.json')
        answer = fixture['case']['chunk']['answers'][0]
        answer['score'] = 1 if answer.get('score') != 1 else 9
        answer['rationale'] = 'controller changed retained answer'
        self.assertTrue(archive_provenance_verifier(fixture), 'Historical full copied answers must be bound to the archive')


if __name__ == '__main__':
    unittest.main(verbosity=2)
