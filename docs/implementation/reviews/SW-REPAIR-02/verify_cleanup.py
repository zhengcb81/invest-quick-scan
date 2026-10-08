"""Read-only lstat and byte verification; records proof outside the deletion root."""
import hashlib
import json
import os
import stat
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
EVIDENCE = REPO / 'docs/implementation/intake/SW-REPAIR-02/2026-10-08'
ROOT = REPO / 'runs/sw-repair-2026-10-08-01'
baseline_path = EVIDENCE / 'cleanup-baseline.json'
raw = baseline_path.read_bytes()
baseline = json.loads(raw.decode('utf-8-sig'))
assert Path(baseline['absolute_root']) == ROOT, 'wrong root'
actual_files, actual_dirs = set(), set()
for directory, dirs, files in os.walk(ROOT, followlinks=False):
    for name in ['.'] + dirs + files:
        entry = Path(directory) if name == '.' else Path(directory) / name
        info = entry.lstat()
        assert not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400, 'reparse refused'
        assert entry == ROOT or ROOT in entry.parents, 'escaped root'
        if entry != ROOT:
            relative = entry.relative_to(ROOT).as_posix()
            (actual_dirs if stat.S_ISDIR(info.st_mode) else actual_files).add(relative)
        if stat.S_ISREG(info.st_mode):
            assert info.st_nlink == 1, 'hardlink refused'
assert actual_files == {f['path'] for f in baseline['files']}, 'file set drift'
assert actual_dirs == set(baseline['directories']), 'directory set drift'
for item in baseline['files']:
    data = (ROOT / item['path']).read_bytes()
    assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'], 'byte drift'
proof = {'schema': 'swr_cleanup_lstat/1', 'root': str(ROOT), 'baseline_sha256': hashlib.sha256(raw).hexdigest(),
         'files_verified': len(actual_files), 'directories_verified': len(actual_dirs), 'hardlinks': 0, 'reparse_points': 0}
(EVIDENCE / 'cleanup-lstat.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(proof))
