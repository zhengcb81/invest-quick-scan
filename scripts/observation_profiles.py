"""Named execution-envelope extensions anchored to unchanged released resources.

This selects a schema; it does not attest vendor execution or answer accuracy.
Authority and downstream pre-send/receipt verification remain independent.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path
import stat
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
VENDOR_HTTP_IDENTITY='vendor-http-identity-v1'
SUPPORTED_VERSIONS=frozenset({'1.0.0','1.1.0','1.2.0'})
_BASE_RESOURCES=frozenset({'schemas/observation.schema.json','schemas/answer-content.schema.json','questions/metric-registry.json'})
def _canonical_sha(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()
def _unique(pairs):
    result={}
    for k,v in pairs:
        if k in result:raise ValueError('execution_profile_duplicate_json_key')
        result[k]=v
    return result
def _constant(value):raise ValueError('execution_profile_nonfinite_json')
def _finite_float(value):
    result=float(value)
    if not math.isfinite(result):raise ValueError('execution_profile_nonfinite_json')
    return result
def _read(relative):
    p=ROOT/relative
    for component in (p,*p.parents):
        if component==ROOT.parent:break
        s=component.lstat()
        if component.is_symlink() or getattr(s,'st_file_attributes',0)&0x400:raise ValueError('execution_profile_path_redirected')
    s=p.stat()
    if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or s.st_size>1048576:raise ValueError('execution_profile_resource_invalid')
    with p.open('rb') as f:raw=f.read(1048577)
    if len(raw)>1048576:raise ValueError('execution_profile_resource_too_large')
    return json.loads(raw.decode('utf-8'),object_pairs_hook=_unique,parse_constant=_constant,parse_float=_finite_float)
def schema_for(version,resources):
    """Choose only an explicit known profile against the actual archived package."""
    if not isinstance(version,str) or version not in SUPPORTED_VERSIONS:raise ValueError('unsupported_observation_execution_profile')
    if version in ('1.0.0','1.1.0'):return copy.deepcopy(resources['schemas/observation.schema.json'])
    catalog=_read('schemas/observation-execution-profiles.json')
    if not isinstance(catalog,dict) or set(catalog)!={'protocol','profiles'} or catalog['protocol']!='iqs.observation_execution_profiles/1.0.0':raise ValueError('execution_profile_registry_invalid')
    profiles=catalog['profiles']
    if not isinstance(profiles,dict) or set(profiles)!={VENDOR_HTTP_IDENTITY}:raise ValueError('execution_profile_registry_invalid')
    row=profiles[VENDOR_HTTP_IDENTITY]
    if not isinstance(row,dict) or set(row)!={'observation_schema_version','schema_path','schema_sha256','base_resource_sha256'} or row['observation_schema_version']!='1.2.0' or row['schema_path']!='schemas/observation-v1.2.schema.json':raise ValueError('execution_profile_registration_invalid')
    base=row['base_resource_sha256']
    if not isinstance(base,dict) or set(base)!=_BASE_RESOURCES:raise ValueError('execution_profile_base_registration_invalid')
    for path,digest in base.items():
        if path not in resources or _canonical_sha(resources[path])!=digest:raise ValueError('execution_profile_archived_base_mismatch')
    schema=_read(row['schema_path'])
    if _canonical_sha(schema)!=row['schema_sha256']:raise ValueError('execution_profile_schema_hash_mismatch')
    if schema['properties']['schema_version']!={'const':'1.2.0'}:raise ValueError('execution_profile_schema_version_mismatch')
    Draft202012Validator.check_schema(schema)
    return copy.deepcopy(schema)


def profile_descriptor(resources=None):
    """Actual registered descriptor, never fields trusted from a request."""
    resources = ({path: _read(path) for path in _BASE_RESOURCES} if resources is None else resources)
    schema = schema_for('1.2.0', resources)
    return dict(profile_id=VENDOR_HTTP_IDENTITY, observation_schema_version='1.2.0',
                observation_schema_sha256=_canonical_sha(schema))


def validate_profile_descriptor(value):
    expected=profile_descriptor()
    if value != expected:raise ValueError('subject_dispatch_execution_profile_invalid')
    return copy.deepcopy(expected)
