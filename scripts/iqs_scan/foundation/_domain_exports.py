"""Domain-facing foundation operations whose schemas load only on use."""

from .json_io import (
    read_json,
    write_json,
)
from .module_contract import (
    ROUTE_SCHEMA,
    canonical_bytes,
    digest as module_digest,
    core_construct_ids,
    parse_version,
    question_definition_sha256,
    seal_release,
    seal_route_decision,
    unique_json_object,
    validate_module,
    validate_registry,
    validate_release,
    validate_route_decision,
    validate_schema,
    validate_upgrade,
)
from .contract_validation import (
    JsonSchemaValidationError,
    identity_schema_for_wire_profile,
    validate_analysis_subject,
    validate_entity,
    validate_parsed_answer,
    validate_work_item,
)
from .observation_profiles import (
    schema_for as observation_schema_for,
    profile_descriptor,
    validate_profile_descriptor,
)
from .exchange_contract import (
    canonical_sha256 as exchange_sha256,
    independent_support,
    validate_package_integrity,
)
from .search_receipt import (
    canonical_sha256 as search_receipt_sha256,
    utc_now as search_receipt_utc_now,
    from_response as build_search_receipt,
    validate as validate_search_receipt,
)
from .work_contract import (
    parse_utc,
    freshness_status,
)
from .metric_coordinates import (
    metric_coordinate,
    validate_metric_coordinates,
)
