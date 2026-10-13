"""Export selected score contracts from verified archives, without answers or IDs."""
import module_registry
import question_manifest
import standard_answers


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
        if question.get('response_kind', 'score') != 'score':
            raise ValueError('score release projection does not support facts')
        questions[question['id']] = {
            'field_id': standard_answers.question_field_id(question),
            'scope': question['scope'], 'response_kind': 'score',
            'definition_sha256': question['definition_sha256'],
            'semantic_sha256': question['semantic_sha256'],
            'rubric_version': question['rubric_version'],
            'construct_id': question['construct_id'],
        }
    return {'module_package_id': package['package_id'], 'release_id': release['release_id'],
        'catalog_version': release['catalog_version'],
        'semantic_fingerprint_version': package.get('semantic_fingerprint_version', '1.0.0'),
        'questions': questions}


def create_execution_profile(manifest,*,root,observation_schema_version):
    if observation_schema_version!='1.2.0':raise ValueError('subject_dispatch_execution_profile_unavailable')
    create_projection(manifest,root=root)
    package,_,_,_=module_registry.load_package(manifest['module_package_id'],root=root)
    from observation_profiles import profile_descriptor
    return profile_descriptor(package['format_resources'])
