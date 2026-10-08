"""Reuse the established exact-manifest cleanup with a new private root."""
from pathlib import Path

D=Path(__file__).resolve().parent
OLD=D.parent/'EVID-LAB-01/remediation-2026-10-08'
s=(OLD/'prepare_cleanup.py').read_text('utf-8')
s=s.replace('.parents[5]','.parents[4]').replace('runs/evid-lab-remediation-2026-10-08-01','runs/qa-c06-02-2026-10-08-01')
s=s.replace('docs/implementation/intake/EVID-LAB-01/2026-10-08-remediation','docs/implementation/intake/QA-C06-02/2026-10-08')
s=s.replace('e99_','qa100_').replace("{'88506':0}","{'67027':0,'13502':1,'76942':0}")
(D/'prepare_cleanup.py').write_text(s,encoding='utf-8')
s=(OLD/'cleanup.ps1').read_text('utf-8')
s=s.replace('../../../../..','../../../..').replace('runs/evid-lab-remediation-2026-10-08-01','runs/qa-c06-02-2026-10-08-01')
s=s.replace('docs/implementation/intake/EVID-LAB-01/2026-10-08-remediation','docs/implementation/intake/QA-C06-02/2026-10-08')
s=s.replace('verification/result.json','verification/final-verification.json').replace('e99_','qa100_')
s=s.replace('evid-lab-remediation-2026-10-08-01','qa-c06-02-2026-10-08-01').replace('EVID-LAB-01*remediation-2026-10-08','reviews*QA-C06-02')
s=s.replace('run_boundaries.py','focused.py').replace('original Lab','original StockQA')
s=s.replace('-not $elResult.input_bytes_unchanged -or ',
    '$elResult.source_head_before -ne $elResult.source_head_after -or $elResult.source_status_before -ne $elResult.source_status_after -or @($elResult.source_artifacts | Where-Object {-not $_.matched}).Count -ne 0 -or ')
(D/'cleanup.ps1').write_text(s,encoding='utf-8')
