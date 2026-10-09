"""Initial private v2 get_profiles shape; no public contract is changed yet."""
import copy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
PRIVATE=ROOT/'runs/c15a/iqs'


def obj(properties):
    return dict(type='object',properties=properties,required=list(properties),additionalProperties=False)


def main():
    assert PRIVATE.is_dir()
    target=PRIVATE/'schemas/quick_scan/query-v2.schema.json'
    assert not target.exists()
    original=json.loads((PRIVATE/'schemas/quick_scan/query.schema.json').read_bytes())
    entity=dict(type='string',pattern=r'^ENT_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')
    subject_id=dict(type='string',pattern=r'^ASJ_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')
    text=dict(type='string',minLength=1,maxLength=160)
    nullable=dict(type=['string','null'],minLength=1,maxLength=160)
    subject=obj(dict(entity_id=entity,analysis_subject_id=subject_id,
                    analysis_subject_revision=dict(type='integer',minimum=1),primary_issuer_id=copy.deepcopy(entity),
                    perimeter_sha256=dict(type='string',pattern='^[a-f0-9]{64}$'),
                    scope=dict(enum=['entity','security','segment']),scope_id=text,
                    security_id=nullable,listing_id=nullable,segment_id=nullable))
    refs=dict(type='array',items={'$ref':'#/$defs/SubjectRef'},minItems=1,maxItems=100)
    fields=dict(type='array',items=text,uniqueItems=True,minItems=1,maxItems=200)
    model_filter=dict(anyOf=[{'type':'null'},obj(dict(provider=text,model_resolved=text))])
    payload=obj(dict(subject_refs=refs,field_ids=fields,information_cutoff=dict(type='string',format='date'),
                     include_history=dict(type='boolean'),model_filter=model_filter,snapshot_id=nullable))
    # Nonempty Observation support stays fail-closed until lineage TDD is wired.
    # This is a private implementation stage, not a published capability.
    profile=obj(dict(subject_ref={'$ref':'#/$defs/SubjectRef'},canonical_name=dict(type='string',minLength=1,maxLength=200),
                     observations=dict(type='array',maxItems=0)))
    result=obj(dict(status=dict(enum=['ok','partial','coverage_gap']),
                    profiles=dict(type='array',items=profile,maxItems=100),
                    missing_subject_refs=dict(type='array',items={'$ref':'#/$defs/SubjectRef'},maxItems=100),
                    coverage=copy.deepcopy(original['$defs']['Coverage']),
                    watermark=copy.deepcopy(original['$defs']['Watermark'])))
    common=dict(schema_version=dict(const='2.0.0'),request_id=text,operation=dict(const='get_profiles'))
    request=obj(dict(message_type=dict(const='request'),**common,
                     consumer_id=dict(enum=['user_ui','analyze-theme-value-chain','industry-research','invest-quick-scan']),
                     requested_at=dict(type='string',format='date-time'),payload=payload))
    response=obj(dict(message_type=dict(const='response'),**common,
                      response_at=dict(type='string',format='date-time'),result=result))
    schema={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:iqs:quick-scan:query:2',
            'title':'QuickScanQueryV2 private initial get_profiles stage',
            '$defs':{'SubjectRef':subject,'Request':request,'Response':response},
            'oneOf':[{'$ref':'#/$defs/Request'},{'$ref':'#/$defs/Response'}]}
    target.write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps(dict(private_schema=str(target),public_contract_changed=False,
                         nonempty_observation_supported=False,real_company_golden=False)))


if __name__=='__main__':
    main()
