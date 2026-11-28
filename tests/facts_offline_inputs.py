"""Generate a self-contained facts-pack fixture through the shipped CLI."""

import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def facts_inputs(tmp_path):
    profile = ROOT / 'examples/profile.json'
    company = json.loads(profile.read_text(encoding='utf-8'))['company']
    identity = tmp_path / 'identity.json'
    identity.write_text(json.dumps({
        'payload': {'entity_id': 'ENT_SYNTHETIC_FACTS', 'canonical_name': company},
    }), encoding='utf-8')
    pack = tmp_path / 'facts-pack-quick'
    composed = subprocess.run(
        [sys.executable, '-B', '-X', 'utf8', str(ROOT / 'scripts/facts_compose.py'),
         '--profile', str(profile), '--mode', 'quick', '--output', str(pack)],
        stdin=subprocess.DEVNULL, capture_output=True, encoding='utf-8',
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
    )
    assert composed.returncode == 0, composed.stderr
    return pack, identity, profile
