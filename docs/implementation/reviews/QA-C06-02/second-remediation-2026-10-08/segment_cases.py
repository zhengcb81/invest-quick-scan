"""Two synthetic same-chain QR1B cases; frozen inputs remain unchanged."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest

QA = Path(os.environ['QA100_QA_ROOT'])
spec = importlib.util.spec_from_file_location(
    'qa107_segment_fixture', QA / 'tests/unit/test_quick_scan_c06_complete_seal.py'
)
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)
from src.utils.quick_scan_c06_authority import AuthorityUnavailable, load_c06_authority
from src.utils.quick_scan_result_outbox import canonical_sha256


@pytest.mark.parametrize('foreign', [False, True])
def test_segment_profile_binding_at_authority_entry(tmp_path, foreign):
    # A distinct declared synthetic scenario, not an edit to owner golden.
    manifest = copy.deepcopy(f.MANIFEST)
    manifest['profile']['segment_id'] = 'SEG_FIXTURE'
    original = {k: v for k, v in manifest.items()
                if k not in {'manifest_sha256', 'manifest_path', 'contract_id'}}
    raw = json.dumps(original, ensure_ascii=False).encode('utf-8')
    (tmp_path / 'synthetic-segment-manifest.json').write_bytes(raw)
    manifest['manifest_sha256'] = hashlib.sha256(raw).hexdigest()
    document = copy.deepcopy(f.AUTHORITY_V2)
    context = document['observation_context']
    context['manifest_file_sha256'] = manifest['manifest_sha256']
    context['manifest_content_sha256'] = canonical_sha256(original)
    segment_ids = []
    for question in manifest['questions']:
        if question['scope'] == 'entity':
            metadata = context['questions'][question['id']]['metadata']
            metadata['scope'] = 'segment'
            metadata['segment_id'] = 'SEG_FIXTURE'
            segment_ids.append(question['id'])
    assert segment_ids
    if foreign:
        context['questions'][segment_ids[0]]['metadata']['segment_id'] = 'SEG_FOREIGN'
    document['observation_context_sha256'] = canonical_sha256(context)
    authority_path = tmp_path / 'synthetic-segment-authority.json'
    authority_path.write_text(json.dumps(document, ensure_ascii=False), encoding='utf-8')
    if foreign:
        with pytest.raises(AuthorityUnavailable, match='segment_id differs'):
            load_c06_authority(authority_path, manifest=manifest)
    else:
        result = load_c06_authority(authority_path, manifest=manifest)
        assert result['observation_context']['questions'][segment_ids[0]][
            'metadata']['segment_id'] == 'SEG_FIXTURE'
