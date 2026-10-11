"""Fixed offline preview validator. Never authenticates a supplied owner JSON."""
import argparse
import json
from pathlib import Path
import module_contract
import refresh_contract as contract

PROTOCOL='iqs.refresh_validation/1.0.0'


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--operation',choices=('request','policy','preview','validate-preview'),required=True)
    args=parser.parse_args(argv)
    try:
        with args.input.open('rb') as handle:raw=handle.read(contract.MAX_BYTES+1)
        if len(raw)>contract.MAX_BYTES:raise ValueError('refresh_input_too_large')
        value=json.loads(raw.decode('utf-8-sig'),object_pairs_hook=module_contract._unique_object)
        if not isinstance(value,dict):raise ValueError('refresh_object_required')
        if args.operation=='policy':
            if set(value)!={'policy'}:raise ValueError('refresh_input_fields')
            result=contract.validate_policy(value['policy'])
        elif args.operation=='request':
            if set(value)!={'request'}:raise ValueError('refresh_input_fields')
            contract.validate_request(value['request']);result=value['request']
        elif args.operation=='preview':
            if set(value)!={'request','owner_state','created_at','expires_at'}:raise ValueError('refresh_input_fields')
            result=contract.create_preview(**value)
        else:
            if set(value)!={'preview','request','owner_state','now'}:raise ValueError('refresh_input_fields')
            result=contract.validate_preview(**value)
        print(module_contract.canonical_bytes(dict(protocol=PROTOCOL,status='validated',
            operation=args.operation,input_sha256=contract.digest(value),result=result,
            API_requests=0,database_writes=0,permission_authenticated=False)).decode('utf-8'))
        return 0
    except (ValueError,TypeError,KeyError,OSError,UnicodeError,RecursionError):
        print(json.dumps(dict(protocol=PROTOCOL,status='rejected',operation=args.operation,
            error_code='refresh_contract_rejected',API_requests=0,database_writes=0,
            permission_authenticated=False)))
        return 2


if __name__=='__main__':raise SystemExit(main())
