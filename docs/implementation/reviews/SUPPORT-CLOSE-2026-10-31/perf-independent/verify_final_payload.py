"""Read-only source/blob verification; writes only this review's thin receipt."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path('C:/Users/郑曾波/Projects/iqs-import-performance-lab')
WORK = ROOT / 'runs/close-support31/perf/work'
C = 'd4679a1c22bad1590b40db7c7c6300f306148e81'
EXPECTED_MANIFEST = '890ff0d4c5e52531dde9d404dd8f601af2917f2dd8c7258c14ea457ca1e051fe'
env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', PYTHONDONTWRITEBYTECODE='1')

def git(*args):
    return subprocess.check_output(['git', '-C', str(SOURCE), *args], env=env)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    head = git('rev-parse', 'HEAD').decode().strip()
    dirty = git('status', '--porcelain=v1').decode('utf8')
    raw = git('show', C + ':docs/payload-manifest.json')
    manifest = json.loads(raw)
    entries = manifest['artifacts']
    refs = [C + ':' + row['path'] for row in entries]
    process = subprocess.run(['git', '-C', str(SOURCE), 'cat-file', '--batch'],
                             input=('\n'.join(refs) + '\n').encode('utf8'),
                             capture_output=True, check=True, env=env)
    cursor = 0
    mismatches = []
    worktree_eol_only = []
    rows = []
    for entry in entries:
        end = process.stdout.index(b'\n', cursor)
        header = process.stdout[cursor:end].split()
        assert len(header) == 3 and header[1] == b'blob', header
        count = int(header[2]); start = end + 1
        content = process.stdout[start:start+count]; cursor = start + count + 1
        valid = sha(content) == entry['sha256'] and len(content) == entry['bytes']
        if not valid: mismatches.append(entry['path'])
        local = WORK / entry['path']
        if local.exists() and local.read_bytes() != content:
            if local.read_bytes().replace(b'\r\n', b'\n') == content.replace(b'\r\n', b'\n'):
                worktree_eol_only.append(entry['path'])
            else: mismatches.append('review_work_copy:' + entry['path'])
        elif not local.exists(): mismatches.append('missing_review_work_copy:' + entry['path'])
        rows.append({'path':entry['path'], 'blob_oid':header[0].decode(), 'sha256':sha(content), 'matches':valid})
    consumed = json.loads((WORK/'docs/consumed-inputs.json').read_bytes())
    vendor_mismatches = []
    vendor_eol_changes = []
    for row in consumed['consumed_inputs']:
        file = WORK / row['vendored_to']
        raw = file.read_bytes()
        if sha(raw) != row['written_raw_sha256'] or len(raw) != row['written_bytes']:
            if sha(raw.replace(b'\r\n',b'\n')) == row['git_blob_raw_sha256']:
                vendor_eol_changes.append(row['vendored_to'])
            else:
                vendor_mismatches.append(row['vendored_to'])
    result = {
        'protocol':'iqs.independent_perf_payload_verify/1.0',
        'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
        'payload_commit':C, 'source_head':head, 'source_dirty_porcelain':dirty,
        'manifest_sha256':sha(git('show', C+':docs/payload-manifest.json')),
        'manifest_sha256_matches':sha(git('show', C+':docs/payload-manifest.json'))==EXPECTED_MANIFEST,
        'artifact_count':len(entries), 'all_manifest_git_blobs_valid':not mismatches,
        'mismatches':mismatches, 'review_work_copy_eol_only_paths':worktree_eol_only,
        'consumed_input_count':len(consumed['consumed_inputs']),
        'vendor_byte_mismatches':vendor_mismatches,
        'vendor_checkout_eol_changes_from_original_vendoring':vendor_eol_changes,
        'vendor_hash_semantics':'written_* are original vendoring receipts, not current Windows checkout byte claims; every checkout difference above independently equals the locked source blob after CRLF-to-LF normalization',
        'input_lock_sha256':consumed['input_lock_sha256'],
        'candidate_patch_sha256':sha((WORK/'integration/candidate.patch').read_bytes()),
        'artifacts':rows,
    }
    (Path(__file__).parent/'final-payload-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    summary={k:v for k,v in result.items() if k not in {'artifacts','review_work_copy_eol_only_paths','vendor_checkout_eol_changes_from_original_vendoring'}}
    summary.update(work_copy_eol_only_count=len(worktree_eol_only),vendor_checkout_eol_change_count=len(vendor_eol_changes))
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    assert head==C and not dirty and result['manifest_sha256_matches'] and not mismatches and not vendor_mismatches

if __name__=='__main__': main()
