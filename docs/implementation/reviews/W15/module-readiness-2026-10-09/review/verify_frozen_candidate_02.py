"""Read-only final candidate/artifact comparison; no product writes or full rerun."""
import hashlib
import json
from pathlib import Path
import sqlite3
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[6]
OWN = ROOT / 'runs/w15a'
INTAKE = ROOT / 'docs/implementation/intake/W15/module-readiness-2026-10-09'
OUT = Path(__file__).resolve().parent
index_raw = (INTAKE / 'candidate-index-02.json').read_bytes()
index = json.loads(index_raw)
roots = {'StockWiki': OWN / 'sw', 'StockQAbyLLM': OWN / 'qa', 'invest-quick-scan': ROOT}
records = []
for owner, rows in index['files'].items():
    for row in rows:
        current_path = roots[owner] / row['path']
        snapshot_path = INTAKE / 'candidate-source-02' / owner / row['path']
        current, snapshot = current_path.read_bytes(), snapshot_path.read_bytes()
        expected = row['execution_sha256']
        facts = dict(owner=owner, path=row['path'], bytes=len(current), expected_sha256=expected,
                     current_sha256=hashlib.sha256(current).hexdigest(),
                     snapshot_sha256=hashlib.sha256(snapshot).hexdigest(),
                     raw_equal=current == snapshot)
        assert facts['current_sha256'] == expected == facts['snapshot_sha256']
        assert len(current) == len(snapshot) == row['bytes']
        records.append(facts)
index_sha = hashlib.sha256(index_raw).hexdigest()
preflight_raw = (INTAKE / 'source-publication/before-publication-01.json').read_bytes()
preflight = json.loads(preflight_raw)
assert preflight['candidate_index_sha256'] == index_sha
checks = []
for label, owner in (
    ('storage-final-09', 'StockWiki'), ('storage-profiles-final-11', 'StockWiki'),
    ('executor-final-affected-04', 'StockQAbyLLM'), ('executor-checkpoint-final-05', 'StockQAbyLLM'),
    ('handoff-final-01', 'invest-quick-scan'),
):
    raw = (INTAKE / (label + '.process.json')).read_bytes()
    process = json.loads(raw)
    prefix = '' if owner == 'invest-quick-scan' else roots[owner].relative_to(ROOT).as_posix() + '/'
    differences = [row['path'] for row in index['files'][owner]
                   if process['execution_sha256'].get(prefix + row['path']) != row['execution_sha256']]
    summary = dict(label=label, pid=process['pid'], returncode=process['returncode'],
                   terminal_confirmed=process['terminal_confirmed'],
                   process_sha256=hashlib.sha256(raw).hexdigest(),
                   candidate_paths_with_different_or_missing_execution_sha= differences)
    if '--junitxml' in process['command']:
        xml_path = Path(process['command'][process['command'].index('--junitxml') + 1])
        xml = ET.fromstring(xml_path.read_bytes())
        interested = []
        for case in xml.iter('testcase'):
            if ('capacity_retry_rechecks_owner' in case.get('name', '')
                    or case.get('name', '').startswith('test_ordinary_network_connect_is_denied')
                    or case.get('name', '') in {'test_windows_stdlib_socketpair_ipc_is_allowed_and_closed',
                                               'test_foreign_sqlite_never_opens'}):
                interested.append(dict(name=case.get('name'), classname=case.get('classname'),
                                       passed=case.find('failure') is None and case.find('error') is None and case.find('skipped') is None))
        summary['capacity_and_guard_cases'] = interested
    checks.append(summary)
with sqlite3.connect((OWN / 'review-owned/capacity-anchor-02/test_current_changed_during_re0/work.sqlite').as_uri() + '?mode=ro', uri=True) as con:
    budgets = con.execute('SELECT budget_attempt_id,work_attempt_id,status,in_flight FROM quick_scan_budget_attempt').fetchall()
    attempts = con.execute('SELECT phase,send_intent_at FROM attempt').fetchall()
assert len(budgets) == 1 and budgets[0][0] == 'DISPATCH_busy' and budgets[0][3] == 0
assert attempts == [('prepared', None)]
static_raw = (INTAKE / 'static-qa-05.process.json').read_bytes()
static = json.loads(static_raw)
assert all(step['returncode'] == 0 and step['terminal_confirmed'] for step in static['steps'])
static_differences = [row['path'] for row in index['files']['StockQAbyLLM']
                      if row['path'].endswith('.py') and static['source_before'].get(row['path']) != row['execution_sha256']]
result = dict(candidate_index_sha256=index_sha,
              candidate_counts={owner: len(rows) for owner, rows in index['files'].items()},
              all_36_current_and_snapshot_bytes_match=True, records=records,
              before_publication_preflight_sha256=hashlib.sha256(preflight_raw).hexdigest(),
              source_preflight_heads={owner: value['head'] for owner, value in preflight['sources'].items()},
              process_checks=checks,
              probe_budget_rows=budgets, probe_attempt_rows=attempts,
              denied_owner_drift_created_new_budget_reservation=False,
              static_qa_05_all_four_terminal_zero=True,
              static_qa_05_candidate_python_paths_with_different_or_missing_sha=static_differences,
              source_product_writes=0, full_reruns=0, HTTP_calls=0)
(OUT / 'frozen-candidate-02-verification.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'records'}, indent=2, ensure_ascii=False))
