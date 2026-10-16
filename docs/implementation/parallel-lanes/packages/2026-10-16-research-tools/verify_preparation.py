"""Read-only card/snapshot verification; never executes worker commands."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


def strict(path):
    def pairs(rows):
        value = {}
        for key, item in rows:
            if key in value:
                raise ValueError('duplicate JSON key')
            value[key] = item
        return value
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    lock = strict(here / 'inputs.lock.json')
    assert lock['protocol'] == 'iqs.parallel-input-lock/1.0.0'
    root = (args.inputs or Path(lock['default_snapshot_root'])).resolve(strict=True)
    seen = set()
    for row in lock['files']:
        key = row['path']
        rel = PurePosixPath(key)
        assert not rel.is_absolute() and '..' not in rel.parts and ':' not in key and '\\' not in key
        assert key not in seen
        seen.add(key)
        path = root.joinpath(*rel.parts).resolve(strict=True)
        assert path.is_relative_to(root) and path.is_file()
        data = path.read_bytes()
        assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'], key
    roots = []
    for package in lock['packages']:
        worker = Path(package['workspace']).resolve()
        assert all(worker != old and not worker.is_relative_to(old) and not old.is_relative_to(worker)
                   for old in roots)
        roots.append(worker)
        assert not worker.is_relative_to(Path(lock['coordinator_workspace']).resolve())
        assert (here / (package['package_id'] + '.md')).is_file()
        template = strict(here / ('handoff-' + package['package_id'] + '.template.json'))
        assert template['package_id'] == package['package_id']
        assert template['status'] == 'prepared_template'
        assert template['production_ready'] is False
        assert template['financial_qualification_granted'] is False
    for file in ('README.md', 'integration-contract.md'):
        assert (here / file).is_file()
    print(json.dumps({'preparation': 'passed', 'files_verified': len(seen),
                      'packages': len(roots), 'product_tests_run': False,
                      'workers_dispatched': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
