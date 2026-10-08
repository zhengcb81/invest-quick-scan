"""Test-only adapter: public SW seed/import/query APIs, separate process."""
import contextlib
import importlib.util
import io
import os
import json
from pathlib import Path
import sys

from stockwiki.cli import main as cli
from stockwiki.paths import WorkspacePaths
from stockwiki.quick_scan_store import QuickScanStore
from stockwiki.quick_scan_observations import QuickScanObservationStore
_spec = importlib.util.spec_from_file_location('sw108_identity_fixture',
    Path(os.environ['E97_OWNED_ROOT']) / 'sw/tests/test_quick_scan_observations.py')
_fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixture)
_seed_entity = _fixture._seed_entity


def main(request):
    root = Path(request['root'])
    paths = WorkspacePaths.from_root(root)
    op = request['op']
    if op == 'empty':
        store = QuickScanStore(paths)
        store.migrate()
        return dict(empty_identity_store=True, synthetic_only=True)
    if op == 'seed':
        store = QuickScanStore(paths)
        store.migrate()
        entity = _seed_entity('ENT_CONTEXT_FIXTURE')
        entity['canonical_name'] = 'Synthetic joint protocol fixture; never owner golden'
        entity['securities'][0]['security_id'] = 'SEC_CONTEXT_FIXTURE'
        bindings = entity.pop('_bindings')
        bindings[0]['security_id'] = 'SEC_CONTEXT_FIXTURE'
        store.save_entity(entity, source_bindings=bindings)
        return dict(identity_state=store.get_entity('ENT_CONTEXT_FIXTURE')['identity_state'],
                    synthetic_only=True)
    if op == 'import':
        stdout, stderr = io.StringIO(), io.StringIO()
        argv = ['--root', str(root), 'observation-import', '--package', request['package'],
                '--release', request['release']]
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = cli(argv)
        parsed = [json.loads(line) for line in (stdout.getvalue() + '\n' + stderr.getvalue()).splitlines()
                  if line.startswith('{')]
        return dict(cli_exit=code, argv=argv, stdout=stdout.getvalue(), stderr=stderr.getvalue(),
                    receipt=parsed[-1] if parsed else None)
    store = QuickScanObservationStore(paths)
    if op == 'observations':
        return dict(counts=store.counts(), observations=store.observations_for_entity('ENT_CONTEXT_FIXTURE'))
    if op == 'ack':
        return store.ack_for(request['package_id'], request['item_id'])
    if op == 'query':
        from stockwiki.ui_quick_scan import (build_quick_scan_capabilities,
            build_quick_scan_search, build_quick_scan_entity, build_quick_scan_coverage)
        return dict(capabilities=build_quick_scan_capabilities(paths),
                    search=build_quick_scan_search(paths, request.get('query', {})),
                    entity=build_quick_scan_entity(paths, 'ENT_CONTEXT_FIXTURE'),
                    coverage=build_quick_scan_coverage(paths))
    if op == 'backup':
        stdout, stderr = io.StringIO(), io.StringIO()
        argv = ['--root', str(root), 'quick-scan-backup', request['action'], '--name', request['name']]
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = cli(argv)
        return dict(cli_exit=code, argv=argv, stdout=stdout.getvalue(), stderr=stderr.getvalue())
    raise ValueError('Unsupported test adapter op: ' + op)


if __name__ == '__main__':
    request = json.loads(Path(sys.argv[1]).read_text('utf-8'))
    result = main(request)
    Path(sys.argv[2]).write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
