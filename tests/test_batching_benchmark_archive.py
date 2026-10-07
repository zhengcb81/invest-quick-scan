"""Offline integration: real ledger -> payload replay -> minimal owned archive."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import batching_benchmark as b
import batching_benchmark_archive as arc
import batching_benchmark_report as report


class ArchiveTests(unittest.TestCase):
    def prepare_fixture(self,root):
        run=root/'runs/owned';run.mkdir(parents=True)
        for folder in ('evidence','results','blocks'):(run/folder).mkdir()
        company={'canonical_name':'C','entity_id':'ENT_test','identity_file_sha256':'a'*64}
        questions=[dict(question_id='Q1',text='q',anchors={'1':'a','5':'b','10':'c'},rubric_version='1')]
        evidence=[dict(source_id='S1',url='https://example.com/report',title='report',snippet='SHORT_CONTEXT_CANARY')]
        b.write_json(run/'companies.json',{'c':company});b.write_json(run/'questions.json',questions)
        b.write_json(run/'evidence/c-balanced.json',evidence)
        system,prompt=b.build_prompt(company,questions,evidence)
        params={'max_tokens':100,'temperature':0}
        body=dict(model='deepseek-flash',messages=[dict(role='system',content=system),dict(role='user',content=prompt)],**params)
        ledger=b.Ledger(run)
        aid=ledger.reserve('model',.1,dict(entity_id='ENT_test',arm='core.c.deepseek.g1.balanced',route='deepseek',
            question_ids=['Q1'],parameters=params,requested_model='deepseek-flash',
            prompt_sha256=b.fingerprint(dict(system=system,prompt=prompt)),request_body_sha256=b.fingerprint(body),
            evidence_sha256=b.fingerprint(evidence),questions_sha256=b.fingerprint(questions)))
        ledger.finish(aid,dict(state='completed',upper_usd=.001,usage={'prompt_tokens':100,'completion_tokens':10}))
        b.write_json(run/'results/CHK_1.json',dict(chunk_id='CHK_1',answers=[{'question_id':'Q1','status':'unknown','score':None}],
            receipt=ledger.finished[aid],parse_excerpt='SHORT_CONTEXT_CANARY'))
        b.write_json(run/'blocks/core.json',dict(arm='core.c.deepseek.g1.balanced',stage='core',company='c',route='deepseek',
            group_size=1,requested=1,valid_rows=1,scored=0,wall_s=1,chunks=['CHK_1']))
        return run

    def test_ledger_replay_archive_no_context_or_parse_excerpt(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp,patch.object(b,'ROOT',Path(tmp)):
            root=Path(tmp);run=self.prepare_fixture(root)
            dest=root/'docs/implementation/experiments/artifacts/owned'
            result=arc.archive(run,dest)
            self.assertEqual(result['verified_model_payloads'],1)
            self.assertFalse(any('SHORT_CONTEXT_CANARY' in p.read_text(encoding='utf-8') for p in dest.iterdir()))
            sources=json.loads((dest/'source-index.json').read_text(encoding='utf-8'))
            self.assertEqual(sources[0]['sources'][0]['snippet_chars'],20)
            with self.assertRaisesRegex(ValueError,'already_exists'):arc.archive(run,dest)

    def test_actual_payload_drift_refused_before_archive_write(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp,patch.object(b,'ROOT',Path(tmp)):
            root=Path(tmp);run=self.prepare_fixture(root)
            b.write_json(run/'evidence/c-balanced.json',[dict(source_id='S1',url='https://example.com/report',snippet='changed')])
            dest=root/'docs/implementation/experiments/artifacts/owned'
            with self.assertRaisesRegex(ValueError,'mismatch'):arc.archive(run,dest)
            self.assertFalse(dest.exists())

    def test_active_run_and_external_dest_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp,patch.object(b,'ROOT',Path(tmp)):
            root=Path(tmp);run=self.prepare_fixture(root)
            with self.assertRaisesRegex(ValueError,'not_owned_archive'):arc.archive(run,root/'other')
            (run/'orchestrator.lock').write_text('running')
            with self.assertRaisesRegex(ValueError,'active_run'):
                arc.archive(run,root/'docs/implementation/experiments/artifacts/owned')

    def test_public_archive_report_recomputes_without_network_or_sources(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp,patch.object(b,'ROOT',Path(tmp)):
            root=Path(tmp);run=self.prepare_fixture(root);dest=root/'docs/implementation/experiments/artifacts/owned'
            arc.archive(run,dest)
            with patch.object(b,'read_key',side_effect=AssertionError('no credentials')):
                recomputed=report.summarize_archive(dest)
            self.assertTrue(recomputed['archive_statistics_verified'])
            (dest/'results.jsonl').write_text('{}\n',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'hash_mismatch'):report.summarize_archive(dest)


if __name__=='__main__':unittest.main()
