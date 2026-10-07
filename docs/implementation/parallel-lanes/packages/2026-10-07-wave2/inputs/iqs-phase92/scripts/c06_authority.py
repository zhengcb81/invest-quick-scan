"""IQS-owned frozen metadata export for the StockQA authority v2 consumer.

This module does not create answers, attest identities, or make network calls.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

import module_registry
import question_manifest
import standard_answers as answers


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_SCHEMA = 'stockqa.quick_scan_observation_context/1.0.0'
_HASH = re.compile(r'^[a-f0-9]{64}$')
_RUN_FIELDS = {'run_id', 'scan_id', 'inputset_id', 'task_mode', 'comparison_group_id'}
_VERSION_FIELDS = {'identity_schema', 'answer_schema', 'observation_schema',
                   'question_catalog', 'model_policy_schema'}


def _text(value, label, maximum):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f'invalid {label}')
    return value


def _run(context):
    if not isinstance(context, dict) or set(context) != _RUN_FIELDS:
        raise ValueError('run context requires the exact five fields')
    for key in ('run_id', 'scan_id', 'inputset_id'):
        _text(context[key], key, 160)
    if context['task_mode'] not in ('primary', 'comparison'):
        raise ValueError('invalid task_mode')
    if context['task_mode'] == 'comparison':
        _text(context['comparison_group_id'], 'comparison_group_id', 160)
    elif context['comparison_group_id'] is not None:
        raise ValueError('primary scan cannot claim a comparison group')
    return copy.deepcopy(context)


def create_authority(manifest, *, manifest_file_sha256, identity_snapshot_sha256,
                     run_context, contract_versions, producer):
    """Export IQS-owned metadata; the receiver independently checks both file hashes.

    Identity hash is a binding, never a verified identity attestation. No answer
    fields, model names, execution timestamps or observation IDs are invented.
    Current support is the released scoring standard-1 path; facts stay F05.
    """
    if not isinstance(manifest, dict) or manifest.get('answer_format') != 'standard-1':
        raise ValueError('standard-1 frozen manifest required')
    if 'module_package_id' not in manifest:
        raise ValueError('released scoring module package required')
    question_manifest.validate_manifest_metric_contract(manifest, root=ROOT)
    package, _, _, _ = module_registry.load_package(manifest['module_package_id'], root=ROOT)
    if not module_registry.observation_ingest_ready(package):
        raise ValueError('historical release cannot issue new observations')
    for value, label in ((manifest_file_sha256, 'manifest file hash'),
                         (identity_snapshot_sha256, 'identity snapshot hash')):
        if not isinstance(value, str) or not _HASH.fullmatch(value):
            raise ValueError(f'invalid {label}')
    run = _run(run_context)
    if not isinstance(contract_versions, dict) or set(contract_versions) != _VERSION_FIELDS:
        raise ValueError('exact contract version set required')
    for key, value in contract_versions.items():
        _text(value, key, 80)
    if (contract_versions['question_catalog'] != manifest['template_version']
            or contract_versions['observation_schema'] != '1.1.0'
            or contract_versions['answer_schema'] != '1.0.0'):
        raise ValueError('contract versions disagree with released observation/answer/catalog')
    if not isinstance(producer, dict) or set(producer) != {'component_version', 'build_id'}:
        raise ValueError('exact producer fields required')
    _text(producer['component_version'], 'component_version', 80)
    _text(producer['build_id'], 'build_id', 160)

    resources = package['format_resources']
    observation_schema = resources['schemas/observation.schema.json']
    # Validate metadata against the SAME archived observation schema, minus the
    # fields only an actual answer/HTTP execution can supply.
    unavailable = {'observation_id', 'observed_at', 'execution', 'answer'}
    metadata_schema = {**observation_schema,
                       'required': [key for key in observation_schema['required'] if key not in unavailable]}
    validator = Draft202012Validator(metadata_schema, format_checker=FormatChecker())
    questions = {}
    for question in manifest['questions']:
        metadata = answers.observation_metadata(manifest, question, run)
        if metadata['scope'] == 'security' and not metadata['security_id']:
            raise ValueError('security scope requires an authoritative security ID')
        if metadata['scope'] == 'segment' and not metadata['segment_id']:
            raise ValueError('segment scope requires an authoritative segment ID')
        if metadata['scope'] == 'entity' and metadata['segment_id'] is not None:
            raise ValueError('entity scope cannot carry a segment ID')
        try:
            validator.validate(metadata)
        except ValidationError as error:
            raise ValueError('metadata differs from released observation schema') from error
        questions[question['id']] = {
            'metadata': metadata,
            'frozen_prompt_sha256': question['prompt_sha256'],
            'work_prompt_sha256': hashlib.sha256(question['prompt'].strip().encode('utf-8')).hexdigest(),
        }
    context = {
        'schema': CONTEXT_SCHEMA,
        'manifest_content_sha256': answers.digest(manifest),
        'manifest_file_sha256': manifest_file_sha256,
        'identity_snapshot_sha256': identity_snapshot_sha256,
        'observation_schema_sha256': answers.digest(observation_schema),
        'answer_schema_sha256': answers.digest(resources['schemas/answer-content.schema.json']),
        'metric_registry_sha256': answers.digest(resources['questions/metric-registry.json']),
        'questions': questions,
    }
    return {
        'schema_version': '2.0.0',
        'contract_versions': copy.deepcopy(contract_versions),
        'capabilities': ['entity_security_identity_v1', 'standard_observation_v1', 'score_v1'],
        'producer': copy.deepcopy(producer),
        'observation_context': copy.deepcopy(context),
        'observation_context_sha256': answers.digest(context),
    }


def _read(path):
    raw = Path(path).read_bytes()
    return json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_object), hashlib.sha256(raw).hexdigest()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def _publish(path, value):
    """Publish complete bytes atomically without replacing an existing target."""
    path = Path(path)
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode('utf-8') + b'\n'
    # Keep the temporary file on the target filesystem. link() publishes an
    # existing complete inode exclusively on Windows and POSIX; it fails if
    # another writer already published. Removing the staging link leaves one
    # ordinary final file. Failure never deletes or truncates the target.
    descriptor, staging_name = tempfile.mkstemp(prefix='.iqs-c06-', dir=path.parent)
    staging = Path(staging_name)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(staging, path)
    finally:
        staging.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Export IQS frozen context for StockQA authority v2; no identity attestation/HTTP.')
    for name in ('manifest', 'identity', 'run', 'versions', 'producer', 'output'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args(argv)
    try:
        manifest, manifest_hash = _read(args.manifest)
        # Bind opaque owner bytes without relabelling synthetic/provisional
        # identity as verified. StockQA must use its public identity loader.
        identity_hash = hashlib.sha256(Path(args.identity).read_bytes()).hexdigest()
        run, _ = _read(args.run)
        versions, _ = _read(args.versions)
        producer, _ = _read(args.producer)
        document = create_authority(manifest, manifest_file_sha256=manifest_hash,
                                    identity_snapshot_sha256=identity_hash,
                                    run_context=run, contract_versions=versions, producer=producer)
        _publish(args.output, document)
    except (OSError, ValueError) as error:
        # No source bodies, company answers or credential bytes in diagnostics.
        print(f'c06_authority_export_refused: {type(error).__name__}', file=sys.stderr)
        return 2
    print(json.dumps({'status': 'exported', 'schema_version': '2.0.0',
                      'observation_context_sha256': document['observation_context_sha256'],
                      'network_calls': 0, 'identity_attested': False}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
