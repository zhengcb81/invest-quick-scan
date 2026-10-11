"""Add independently issued owner subject facts to new context2, never old originals."""
import copy
import query_contract as qc
import subject_dispatch_contract as dc

def attach_subject_context(context,manifest,binding,*,listing_bindings=None):
    if context.get('schema')!='stockqa.quick_scan_observation_context/1.0.0':
        raise ValueError('subject_context_requires_original_context1')
    if binding.get('binding_version')!='stockwiki.route_subject/1.0.0':
        raise ValueError('subject_context_owner_binding_version')
    subject=binding['subject']
    receipt=binding['perimeter_receipt']
    if (binding['subject_key']!=subject['analysis_subject_id']+'@'+str(subject['analysis_subject_revision'])
        or binding['analysis_subject_id']!=subject['analysis_subject_id']
        or binding['analysis_subject_revision']!=subject['analysis_subject_revision']
        or binding['entity_id']!=manifest['profile']['entity_id']
        or binding['entity_id']!=subject['primary_issuer_id']
        or binding['perimeter_sha256']!=receipt['perimeter_sha256']
        or any(receipt[k]!=subject[k] for k in ('analysis_subject_id','analysis_subject_revision','primary_issuer_id'))):
        raise ValueError('subject_context_owner_binding_mismatch')
    value=copy.deepcopy(context)
    questions={q['id']:q for q in manifest['questions']}
    if set(questions)!=set(value['questions']):raise ValueError('subject_context_question_set_mismatch')
    for qid,row in value['questions'].items():
        meta=row['metadata']
        scope=meta['scope']
        sid=meta['entity_id'] if scope=='entity' else meta['security_id'] if scope=='security' else meta['segment_id']
        listing_id=None
        if scope=='security':
            material=(listing_bindings or {}).get(meta['security_id'])
            if (not isinstance(material,dict)
                or material.get('schema_version')!='stockwiki.listing_binding/1.0.0'
                or material.get('entity_id')!=binding['entity_id']
                or type(material.get('identity_revision')) is not int
                or material['identity_revision']!=binding['identity_revision']):
                raise ValueError('subject_context_listing_owner_material_required')
            listing=material['listing']
            source=material['source_binding']
            if (listing['entity_id']!=binding['entity_id'] or listing['security_id']!=sid
                or source['entity_id']!=binding['entity_id'] or source['security_id']!=sid
                or source['listing_id']!=listing['listing_id']
                or source['binding_ref']!=listing['source_binding_ref'] or source['status']!='active'):
                raise ValueError('subject_context_listing_owner_material_mismatch')
            listing_id=listing['listing_id']
            if manifest['profile'].get('listing_id') not in (None,listing_id):
                raise ValueError('subject_context_listing_profile_mismatch')
        ref={'entity_id':binding['entity_id'],'analysis_subject_id':subject['analysis_subject_id'],
            'analysis_subject_revision':subject['analysis_subject_revision'],
            'primary_issuer_id':subject['primary_issuer_id'],'perimeter_sha256':binding['perimeter_sha256'],
            'scope':scope,'scope_id':sid,'security_id':meta['security_id'],
            'segment_id':meta['segment_id'],'listing_id':listing_id}
        # Existing public query shape is reused; source authentication remains
        # owner-refresh's independent current-store check before any key/HTTP.
        request={'message_type':'request','schema_version':'2.0.0','request_id':'context-'+qid,
            # Internal shape-check envelope; no query/time event is emitted.
            'consumer_id':'invest-quick-scan','operation':'get_profiles',
            'requested_at':meta['information_cutoff']+'T00:00:00Z',
            'payload':{'subject_refs':[ref],'field_ids':[meta['field_id']],
                'information_cutoff':meta['information_cutoff'],'include_history':True,'model_filter':None,'snapshot_id':None}}
        qc.validate_request(request)
        row['subject_binding']={'protocol':'stockqa.subject_context/1.0.0','subject_ref':ref,
            'identity_revision':binding['identity_revision'],'question_contract':copy.deepcopy(questions[qid])}
    value['schema']='stockqa.quick_scan_observation_context/2.0.0'
    return value
