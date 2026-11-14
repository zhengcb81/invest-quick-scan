"""Export selected question contracts from verified archives, without answers."""
import re

from iqs_scan.foundation.api import module_digest
from . import module_registry
from . import question_manifest

API_PROTOCOL = "iqs.frozen-question-projection-api/1.1.0"
PUBLIC_API_EXPORTS = frozenset({
    "API_PROTOCOL", "PUBLIC_API_EXPORTS", "create_question_config",
    "create_projection", "create_company_assessment_v2", "create_execution_profile",
})


def create_question_config(manifest, *, root):
    """Explicit identified transport from the SAME valid immutable release.

    Does not parse IDs out of prose or change the legacy questions.json export.
    The receiving runner still checks every ID, order and prompt SHA against
    its independently loaded original manifest before any HTTP.
    """
    create_projection(manifest,root=root)
    return {'question_transport':'stockqa.identified_questions/1.0.0',
        'questions':[{'question_id':q['id'],'text':q['prompt']} for q in manifest['questions']]}


def create_projection(manifest, *, root):
    if (not isinstance(manifest, dict) or manifest.get('answer_format') != 'standard-1'
            or 'module_package_id' not in manifest):
        raise ValueError('released standard-1 manifest required')
    mappings = question_manifest.validate_manifest_metric_contract(manifest, root=root)
    if not isinstance(mappings, dict):
        raise ValueError('released metric contract required')
    package, _, release, _ = module_registry.load_package(manifest['module_package_id'], root=root)
    if not module_registry.observation_ingest_ready(package):
        raise ValueError('historical release cannot accept new observations')
    questions = {}
    for question in manifest['questions']:
        kind = question.get('response_kind', 'score')
        questions[question['id']] = {
            'field_id': question_manifest.question_field_id(question),
            'scope': question['scope'], 'response_kind': kind,
            'definition_sha256': question['definition_sha256'],
            'semantic_sha256': question['semantic_sha256'],
            'rubric_version': question['rubric_version'],
            'construct_id': question['construct_id'],
        }
        if kind == 'fact':
            questions[question['id']]['relations'] = list(question['relations'])
    return {'module_package_id': package['package_id'], 'release_id': release['release_id'],
        'catalog_version': release['catalog_version'],
        'semantic_fingerprint_version': package.get('semantic_fingerprint_version', '1.0.0'),
        'questions': questions}


def create_company_assessment_v2(manifest, observation_refs, *, root):
    """Build the additive owner company-assessment/2 request from frozen sources.

    The original release identity and complete question map are preserved. The
    lineage groups partition that map by the source rubric and aggregation role;
    they never combine scales or produce an aggregate. ``observation_refs`` is
    the set of already persisted observations to include, each represented by
    its original observation ID, payload hash, and question ID. A partial list
    stays partial and is not presented as complete coverage. The owner verifies
    each reference against its stored immutable observation row.
    """
    if not isinstance(observation_refs, list):
        raise ValueError('observation references must be a list')
    source_release = create_projection(manifest, root=root)
    entity_id = (manifest.get('profile', {}).get('entity_id')
                 if isinstance(manifest.get('profile'), dict) else None)
    if not isinstance(entity_id, str) or not entity_id.strip():
        raise ValueError('verified entity_id required for company assessment')

    package, _, release, _ = module_registry.load_package(manifest['module_package_id'], root=root)
    metric_schema = package['format_resources']['schemas/quick_scan/metric.schema.json']
    metric_version = question_manifest.metric_contract_version_for_schema(metric_schema)
    if manifest.get('metric_contract_version') != metric_version:
        raise ValueError('manifest metric contract version differs from source release')
    metric_mappings = question_manifest.validate_manifest_metric_contract(manifest, root=root)
    if not isinstance(metric_mappings, dict):
        raise ValueError('released metric contract required')

    source_questions = source_release['questions']
    manifest_questions = manifest['questions']
    manifest_by_id = {question['id']: question for question in manifest_questions}
    if (len(manifest_by_id) != len(manifest_questions)
            or set(manifest_by_id) != set(source_questions)):
        raise ValueError('source release and manifest question identities differ')

    question_mappings = []
    question_lineage = {}
    questions_by_lineage = {}
    for question_id in sorted(manifest_by_id):
        question = manifest_by_id[question_id]
        source_question = source_questions[question_id]
        response_kind = question.get('response_kind', 'score')
        comparison_role = question.get('comparison_role')
        construct_id = question.get('construct_id')
        rubric_version = question.get('rubric_version')
        definition_sha256 = question.get('definition_sha256')
        semantic_sha256 = question.get('semantic_sha256')
        if not isinstance(rubric_version, str) or not rubric_version.strip():
            raise ValueError(f'question has no rubric version: {question_id}')
        if (definition_sha256 != source_question['definition_sha256']
                or semantic_sha256 != source_question['semantic_sha256']):
            raise ValueError(f'question hashes differ from frozen source: {question_id}')

        if response_kind == 'fact':
            if (comparison_role is not None or construct_id is not None
                    or question.get('metric_contract') is not None):
                raise ValueError(f'information question has score-only metadata: {question_id}')
            aggregation_role = 'information_only'
            metric_contract = None
        elif response_kind == 'score':
            metric_contract = question.get('metric_contract')
            authoritative_mapping = metric_mappings.get(question_id)
            if not isinstance(metric_contract, dict) or metric_contract != authoritative_mapping:
                raise ValueError(f'metric mapping drift: {question_id}')
            aggregation_role = metric_contract.get('aggregation_role')
            if comparison_role == 'context':
                if metric_version != '1.1.0' or aggregation_role != 'context_only':
                    raise ValueError(f'legacy context role cannot be represented: {question_id}')
            elif comparison_role == 'diagnostic':
                if aggregation_role != 'diagnostic_only':
                    raise ValueError(f'diagnostic role differs from metric mapping: {question_id}')
            elif comparison_role == 'core':
                if aggregation_role not in {'quality_core', 'growth_core', 'valuation_core'}:
                    raise ValueError(f'core role differs from metric mapping: {question_id}')
                if not isinstance(construct_id, str) or not construct_id.strip():
                    raise ValueError(f'comparable score question has no construct: {question_id}')
            else:
                raise ValueError(f'unsupported score comparison role: {question_id}')
        else:
            raise ValueError(f'unsupported response kind in company assessment: {question_id}')

        if aggregation_role not in {
            'quality_core', 'growth_core', 'valuation_core', 'diagnostic_only',
            'context_only', 'information_only',
        }:
            raise ValueError(f'unsupported aggregation role: {question_id}')
        if (construct_id is None
                and aggregation_role not in {'diagnostic_only', 'context_only', 'information_only'}):
            raise ValueError(f'comparable score question has no construct: {question_id}')

        question_mapping = {
            'question_id': question_id,
            'metric_contract': metric_contract,
            'comparison_role': comparison_role,
            'construct_id': construct_id,
            'rubric_version': rubric_version,
            'response_kind': response_kind,
            'definition_sha256': definition_sha256,
            'semantic_sha256': semantic_sha256,
        }
        question_mappings.append(question_mapping)
        lineage = (rubric_version, aggregation_role)
        questions_by_lineage.setdefault(lineage, []).append(question_id)
        question_lineage[question_id] = lineage

    source_release_sha256 = module_digest(source_release)
    lineage_provenance = {
        'source_release_sha256': source_release_sha256,
        'module_package_id': package['package_id'],
        'module_release_id': release['release_id'],
        'metric_contract_version': metric_version,
        'metric_schema_sha256': module_digest(metric_schema),
        'question_mappings': question_mappings,
    }
    lineage_provenance_sha256 = module_digest(lineage_provenance)

    lineage_groups = []
    group_by_lineage = {}
    for rubric_version, aggregation_role in sorted(questions_by_lineage):
        question_ids = sorted(questions_by_lineage[(rubric_version, aggregation_role)])
        lineage_group_id = 'lg_' + module_digest({
            'source_release_sha256': source_release_sha256,
            'rubric_version': rubric_version,
            'aggregation_role': aggregation_role,
            'question_ids': question_ids,
        })[:20]
        lineage_groups.append({
            'lineage_group_id': lineage_group_id,
            'rubric_version': rubric_version,
            'aggregation_role': aggregation_role,
            'question_ids': question_ids,
        })
        group_by_lineage[(rubric_version, aggregation_role)] = lineage_group_id

    covered = [question_id for group in lineage_groups for question_id in group['question_ids']]
    if len(covered) != len(set(covered)) or set(covered) != set(source_questions):
        raise ValueError('lineage groups must partition all frozen release questions')

    normalized_refs = []
    seen_observation_ids = set()
    for reference in observation_refs:
        if not isinstance(reference, dict) or set(reference) != {
            'observation_id', 'payload_sha256', 'question_id',
        }:
            raise ValueError('observation reference fields are invalid')
        observation_id = reference['observation_id']
        payload_sha256 = reference['payload_sha256']
        question_id = reference['question_id']
        if (not isinstance(observation_id, str)
                or not re.fullmatch(r'obs_[a-f0-9]{64}', observation_id)):
            raise ValueError('observation ID is invalid')
        if (not isinstance(payload_sha256, str)
                or not re.fullmatch(r'[a-f0-9]{64}', payload_sha256)):
            raise ValueError('observation payload hash is invalid')
        if not isinstance(question_id, str) or question_id not in source_questions:
            raise ValueError('observation references an unknown frozen question')
        if observation_id in seen_observation_ids:
            raise ValueError('duplicate observation ID')
        seen_observation_ids.add(observation_id)
        rubric_version, aggregation_role = question_lineage[question_id]
        normalized_refs.append({
            'observation_id': observation_id,
            'payload_sha256': payload_sha256,
            'question_id': question_id,
            'source_release_sha256': source_release_sha256,
            'lineage_group_id': group_by_lineage[(rubric_version, aggregation_role)],
            'question_definition_sha256': source_questions[question_id]['definition_sha256'],
            'question_semantic_sha256': source_questions[question_id]['semantic_sha256'],
        })
    normalized_refs.sort(key=lambda item: (item['question_id'], item['observation_id']))

    return {
        'entity_id': entity_id,
        'manifest': {
            'protocol': 'stockwiki.company_assessment/2',
            'schema_version': '2.0.0',
            'source_release': source_release,
            'source_release_sha256': source_release_sha256,
            'lineage_provenance': lineage_provenance,
            'lineage_provenance_sha256': lineage_provenance_sha256,
            'lineage_groups': lineage_groups,
        },
        'observations': normalized_refs,
    }


def create_execution_profile(manifest,*,root,observation_schema_version):
    if observation_schema_version!='1.2.0':raise ValueError('subject_dispatch_execution_profile_unavailable')
    create_projection(manifest,root=root)
    package,_,_,_=module_registry.load_package(manifest['module_package_id'],root=root)
    from iqs_scan.foundation.api import profile_descriptor
    return profile_descriptor(package['format_resources'])
