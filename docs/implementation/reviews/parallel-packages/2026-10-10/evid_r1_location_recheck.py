"""Read-only intake of the user-supplied delivery location; no Lab execution."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[5]
LAB = ROOT.parent / 'iqs-evidence-lab'
INTAKE = ROOT / 'docs/implementation/intake/parallel-packages/2026-10-10/evid-remediation-01'
TARGET = INTAKE / 'user-location-recheck-2026-10-11.json'
assert not TARGET.exists(), 'once-only intake; inspect the existing receipt'
HANDOFF = LAB / 'docs/handoff/EVID-REF-02/remediation-01/handoff.json'
prior = json.loads((INTAKE / 'source-freeze.json').read_bytes())
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def git(*args):
    result = subprocess.run(['git', *args], cwd=LAB, capture_output=True, timeout=45)
    assert result.returncode == 0, result.stderr.decode('utf-8', errors='replace')
    return result.stdout.decode('utf-8').strip()


def state():
    return dict(head=git('rev-parse', 'HEAD'), branch=git('branch', '--show-current'),
        status=git('status', '--porcelain=v1', '--untracked-files=all').splitlines())


before = state()
handoff_raw = HANDOFF.read_bytes()
handoff = json.loads(handoff_raw)
artifacts_raw = (HANDOFF.parent / 'artifacts.json').read_bytes()
artifacts = json.loads(artifacts_raw)['artifacts']


def compare(entries):
    mismatches = []
    for entry in entries:
        file = LAB / entry['path']
        assert file.resolve().is_relative_to(LAB.resolve())
        if not file.is_file():
            mismatches.append(dict(path=entry['path'], reason='missing'))
            continue
        raw = file.read_bytes()
        if len(raw) != entry['bytes'] or sha(raw) != entry['sha256']:
            mismatches.append(dict(path=entry['path'], reason='size_or_sha_changed'))
    return mismatches


source_changes = compare(prior['files'])
artifact_changes = compare(artifacts)
after = state()
same_delivery = (before == after and not source_changes and not artifact_changes
    and before['head'] == prior['head']
    and handoff['snapshot']['result_commit'] == prior['product_commit'])
receipt = dict(schema='iqs.evid_delivery_location_recheck/1.0.0',
    at=datetime.now(timezone.utc).isoformat(), user_supplied_location='docs/handoff/EVID-REF-02/remediation-01/',
    handoff=str(HANDOFF), handoff_sha256=sha(handoff_raw), artifacts_sha256=sha(artifacts_raw),
    prior_freeze='source-freeze.json', prior_freeze_sha256=sha((INTAKE / 'source-freeze.json').read_bytes()),
    source_files_checked=len(prior['files']), artifact_files_checked=len(artifacts),
    source_changes=source_changes, artifact_changes=artifact_changes,
    git_before=before, git_after=after, source_read_only_unchanged=before == after,
    product_commit=handoff['snapshot']['result_commit'], identical_previous_R1=same_delivery,
    declared_R2_directory_exists=(LAB / 'docs/handoff/EVID-REF-02/remediation-02').exists(),
    acceptance='prior_changes_requested_retained' if same_delivery else 'new_delta_requires_intake',
    original_acceptance_report='docs/implementation/reviews/parallel-packages/2026-10-10/EVID-REF-02-R1-acceptance.md',
    original_acceptance_report_sha256=sha((ROOT / 'docs/implementation/reviews/parallel-packages/2026-10-10/EVID-REF-02-R1-acceptance.md').read_bytes()),
    tests_rerun=0, lab_programs_executed=0, lab_writes=0, paid_calls=0,
    next_action='receive actual R2 product/handoff before continuing the same package acceptance',
    financial_accuracy_proven=False, global_gates_closed=False)
with TARGET.open('x', encoding='utf-8', newline='\n') as handle:
    json.dump(receipt, handle, ensure_ascii=False, indent=2)
    handle.write('\n')
print(json.dumps({key: receipt[key] for key in ('source_files_checked','artifact_files_checked',
    'source_changes','artifact_changes','identical_previous_R1','acceptance','declared_R2_directory_exists')}, ensure_ascii=False))
