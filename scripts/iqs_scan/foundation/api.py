"""Public Python operations owned by the foundation capability."""

from .feedback_io import (
    FEEDBACK_ATTEMPT_ENV,
    FEEDBACK_OUT_ENV,
    FEEDBACK_RUN_ENV,
    FEEDBACK_SCHEMA,
    append_feedback,
    diagnose_feedback,
    feedback_path,
)
from .json_io import replace_after_readers_close
from .process_logs import decoded_output_lines, read_process_log, register_process_log
from .runtime_feedback import (
    RuntimeArgumentParser,
    exception_diagnostic,
    operation_scope,
    read_operation_failure,
    record_operation_failure,
)


def __getattr__(name):
    # Diagnostics must still work when a registry, schema file or optional
    # schema dependency is the part of the installation that failed.
    if name not in __all__:
        raise AttributeError(name)
    from . import _domain_exports
    value = getattr(_domain_exports, name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))


API_PROTOCOL = "iqs.foundation-api/1.0.0"

__all__ = (
    "API_PROTOCOL",
    "FEEDBACK_ATTEMPT_ENV",
    "FEEDBACK_OUT_ENV",
    "FEEDBACK_RUN_ENV",
    "FEEDBACK_SCHEMA",
    "RuntimeArgumentParser",
    "JsonSchemaValidationError",
    "ROUTE_SCHEMA",
    "append_feedback",
    "diagnose_feedback",
    "feedback_path",
    "decoded_output_lines",
    "exception_diagnostic",
    "read_process_log",
    "register_process_log",
    "operation_scope",
    "read_operation_failure",
    "record_operation_failure",
    "build_search_receipt",
    "canonical_bytes",
    "core_construct_ids",
    "exchange_sha256",
    "freshness_status",
    "identity_schema_for_wire_profile",
    "independent_support",
    "metric_coordinate",
    "module_digest",
    "observation_schema_for",
    "parse_utc",
    "parse_version",
    "profile_descriptor",
    "question_definition_sha256",
    "read_json",
    "replace_after_readers_close",
    "seal_release",
    "seal_route_decision",
    "search_receipt_sha256",
    "search_receipt_utc_now",
    "unique_json_object",
    "validate_analysis_subject",
    "validate_entity",
    "validate_metric_coordinates",
    "validate_module",
    "validate_package_integrity",
    "validate_parsed_answer",
    "validate_profile_descriptor",
    "validate_registry",
    "validate_release",
    "validate_route_decision",
    "validate_schema",
    "validate_search_receipt",
    "validate_upgrade",
    "validate_work_item",
    "write_json",
)
