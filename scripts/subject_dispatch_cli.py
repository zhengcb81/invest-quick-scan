"""Fixed offline contract adapter. Validated content does not attest its source."""
import argparse
import json
import sys
from pathlib import Path
import subject_dispatch_contract as contract
import query_contract as qc

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--operation',choices=('request','receipt','bind','release','questions'),required=True)
    parser.add_argument('--input',required=True)
    parser.add_argument('--release-root',default=str(Path(__file__).resolve().parents[1]))
    args=parser.parse_args(argv)
    try:
        value=qc.load_document(args.input)
        if args.operation=='request':
            if set(value)!={'dispatch','registered_at'}:raise ValueError('subject_contract_input_fields')
            result=contract.validate_dispatch_request(value['dispatch'],registered_at=value['registered_at'])
        elif args.operation=='receipt':
            if set(value)!={'receipt','store_id'}:raise ValueError('subject_contract_input_fields')
            result=contract.validate_receipt(value['receipt'],store_id=value['store_id'])
        elif args.operation=='bind':
            if set(value)!={'receipt','observation','payload_sha256','observation_sequence','ack_sequence','bound_at'}:
                raise ValueError('subject_contract_input_fields')
            result=contract.bind_original(**value)
        else:
            if set(value)!={'manifest'}:raise ValueError('subject_contract_input_fields')
            from frozen_release_projection import create_projection,create_question_config
            project=create_projection if args.operation=='release' else create_question_config
            result=project(value['manifest'],root=Path(args.release_root))
        output={'protocol':'iqs.subject_dispatch_validation/1.0.0','operation':args.operation,
            'status':'validated','input_sha256':contract.digest(value),'result':result,
            'API_requests':0,'database_writes':0,'identity_attested':False}
        print(json.dumps(output,ensure_ascii=False,allow_nan=False));return 0
    except (ValueError,TypeError,KeyError,OSError,RecursionError):
        print(json.dumps({'protocol':'iqs.subject_dispatch_validation/1.0.0','operation':args.operation,
            'status':'rejected','error_code':'subject_dispatch_contract_rejected','API_requests':0,
            'database_writes':0,'identity_attested':False}));return 2

if __name__=='__main__':raise SystemExit(main())
