"""Fixed offline query validator; file paths are trusted process configuration."""
import argparse
import json
from pathlib import Path

import query_contract as contract
import module_contract

PROTOCOL='iqs.query_validation/1.0.0'
MAX_BYTES=80*1024*1024


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True)
    parser.add_argument('--operation',required=True,
        choices=('request','originals','bindings','seal','response','query-hash',
            'pool-request','pool-query-hash','pool-index','pool-response','field-assessment',
            'pool-field-assessment','qualified-pool-index','qualified-pool-response',
            'review-lead-request','review-lead-response','research-request','research-query-hash',
            'research-build','research-response','scoped-pool-index','scoped-pool-response',
            'capabilities-request','capabilities-build','capabilities-response'))
    args=parser.parse_args(argv)
    try:
        with Path(args.input).open('rb') as handle:raw=handle.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:raise ValueError('query_input_too_large')
        value=json.loads(raw.decode('utf-8'),object_pairs_hook=module_contract._unique_object)
        module_contract.canonical_bytes(value)
        if not isinstance(value,dict):raise ValueError('query_object_required')
        if args.operation.startswith('capabilities-'):
            import query_capabilities_contract as capabilities
            if isinstance(value.get('request'),dict) and value['request'].get('schema_version')=='1.2.0':
                import query_capabilities_vendor_contract as capabilities
            if args.operation=='capabilities-request':
                if set(value)!={'request'}:raise ValueError('query_contract_input_fields')
                result=capabilities.validate_request(value['request'])
            elif args.operation=='capabilities-build':
                if set(value)!={'request','source_context','index','scope_context'}:raise ValueError('query_contract_input_fields')
                result=capabilities.build_response(**value)
            else:
                if set(value)!={'response','request','source_context','index','scope_context'}:
                    raise ValueError('query_contract_input_fields')
                result=capabilities.validate_response(**value)
        elif args.operation.startswith('research-'):
            import query_research_contract as research
            if args.operation in {'research-request','research-query-hash'}:
                if set(value)!={'request'}:raise ValueError('query_contract_input_fields')
                result=(research.validate_request(value['request']) if args.operation=='research-request'
                    else research.query_sha256(value['request']))
            elif args.operation=='research-build':
                if set(value)!={'profile_response','request','owner'}:raise ValueError('query_contract_input_fields')
                result=research.build_response(**value)
            else:
                if set(value)!={'response','request','owner'}:raise ValueError('query_contract_input_fields')
                result=research.validate_response(**value)
        elif args.operation in {'review-lead-request','review-lead-response'}:
            import query_review_lead_contract as leads
            if args.operation=='review-lead-request':
                if set(value)!={'request'}:raise ValueError('query_contract_input_fields')
                result=leads.validate_request(value['request'])
            else:
                if set(value)!={'response','request','owner'}:raise ValueError('query_contract_input_fields')
                result=leads.validate_response(**value)
        elif args.operation=='pool-field-assessment':
            if set(value)!={'inputs','store_id','at_utc','trusted_check_level_receipts','field_policy'}:
                raise ValueError('query_contract_input_fields')
            from query_field_assessment import assess_pool_inputs
            result=assess_pool_inputs(**value)
        elif args.operation.startswith('scoped-pool-'):
            import query_pool_scope_contract as scoped
            if args.operation=='scoped-pool-index':
                if set(value)!={'index','store_id','assessment_context','scope_context'}:raise ValueError('query_contract_input_fields')
                scoped.validate_index(**value)
                result={'index_sha256':value['index']['content_sha256'],'validated':True}
            else:
                if set(value)!={'response','request','index','selected_rows','store_id','assessment_context','scope_context'}:
                    raise ValueError('query_contract_input_fields')
                result=scoped.validate_response(**value)
        elif args.operation.startswith('qualified-pool-'):
            import query_pool_assessment_contract as qualified
            if args.operation=='qualified-pool-index':
                if set(value)!={'index','store_id','assessment_context'}:raise ValueError('query_contract_input_fields')
                qualified.validate_index(**value)
                result={'index_sha256':value['index']['content_sha256'],'validated':True}
            else:
                if set(value)!={'response','request','index','selected_rows','store_id','assessment_context'}:
                    raise ValueError('query_contract_input_fields')
                result=qualified.validate_response(**value)
        elif args.operation=='field-assessment':
            selector=value.get('query_schema_version')
            expected={'rows','store_id','at_utc','trusted_check_level_receipts','field_policy'}
            if selector is None:
                if set(value)!=expected:raise ValueError('query_contract_input_fields')
                from query_field_assessment import assess_originals as selected_assessment
            elif selector=='2.6.0':
                if set(value)!=expected|{'query_schema_version'}:raise ValueError('query_contract_input_fields')
                from query_field_assessment import assess_vendor_originals as selected_assessment
            else:raise ValueError('query_contract_input_fields')
            result=selected_assessment(**{k:v for k,v in value.items() if k!='query_schema_version'})
        elif args.operation.startswith('pool-'):
            import query_pool_contract as pool
            if args.operation in {'pool-request','pool-query-hash'}:
                if set(value)!={'request'}:raise ValueError('query_contract_input_fields')
                if value['request'].get('schema_version')=='2.2.0':
                    import query_pool_assessment_contract as pool
                elif value['request'].get('schema_version')=='2.5.0':
                    import query_pool_scope_contract as pool
                validated=pool.validate_request(value['request'])
                result=validated if args.operation=='pool-request' else pool.query_sha256(validated)
            elif args.operation=='pool-index':
                if set(value)!={'index','store_id'}:raise ValueError('query_contract_input_fields')
                pool.validate_index(value['index'],store_id=value['store_id'])
                result={'index_sha256':value['index']['content_sha256'],'validated':True}
            else:
                if set(value)!={'response','request','index','selected_rows','store_id'}:
                    raise ValueError('query_contract_input_fields')
                result=pool.validate_response(**value)
        elif args.operation in ('request','query-hash'):
            if set(value)!={'request'}:raise ValueError('query_contract_input_fields')
            selected=contract
            if value['request'].get('schema_version')=='2.6.0':
                import query_vendor_contract as selected
            selected.validate_request(value['request'])
            result=(value['request'] if args.operation=='request' else selected.query_sha256(value['request']))
        elif args.operation=='originals':
            selected=contract
            if value.get('query_schema_version')=='2.6.0':
                if set(value)!={'rows','query_schema_version'}:raise ValueError('query_contract_input_fields')
                import query_vendor_contract as selected
            elif set(value)!={'rows'}:raise ValueError('query_contract_input_fields')
            if not isinstance(value['rows'],list):raise ValueError('query_contract_input_fields')
            result=[]
            for row in value['rows']:
                original=selected._original(row)
                result.append({'row_sha256':contract._digest(row),'original':original,
                    'variant_key':contract.observation_variant_key(original)})
        elif args.operation=='bindings':
            if set(value)!={'items'} or not isinstance(value['items'],list):raise ValueError('query_contract_input_fields')
            import subject_dispatch_contract as subjects
            result=[]
            for item in value['items']:
                if set(item)!={'receipt','observation','payload_sha256','observation_sequence',
                    'ack_sequence','bound_at','store_id'}:raise ValueError('query_contract_input_fields')
                receipt=subjects.validate_receipt(item['receipt'],store_id=item['store_id'])
                binding_input={key:val for key,val in item.items() if key!='store_id'}
                binding=subjects.bind_original(**binding_input)
                result.append({'receipt_input_sha256':contract._digest({'receipt':item['receipt'],'store_id':item['store_id']}),
                    'receipt':receipt,'binding_input_sha256':contract._digest(binding_input),'binding':binding})
        else:
            if set(value)!={'response','request','owner'}:raise ValueError('query_contract_input_fields')
            selected=contract
            if value['request'].get('schema_version')=='2.6.0':
                import query_vendor_contract as selected
            response=(selected.seal_response(value['response'],request=value['request'])
                if args.operation=='seal' else value['response'])
            selected.validate_response(response,expected_request=value['request'],expected_owner=value['owner'])
            result=response
        output={'protocol':PROTOCOL,'operation':args.operation,'status':'validated',
            'input_sha256':contract._digest(value),'result':result,
            'API_requests':0,'database_writes':0,'identity_attested':False}
        encoded=module_contract.canonical_bytes(output)
        if len(encoded)>MAX_BYTES:raise ValueError('query_output_too_large')
        print(encoded.decode('utf-8'));return 0
    except (ValueError,TypeError,KeyError,OSError,UnicodeError,RecursionError):
        print(json.dumps({'protocol':PROTOCOL,'operation':args.operation,'status':'rejected',
            'error_code':'query_contract_rejected','API_requests':0,'database_writes':0,'identity_attested':False}))
        return 2


if __name__=='__main__':raise SystemExit(main())
