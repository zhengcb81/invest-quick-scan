"""Public Python operations owned by the questions capability."""

from .question_bank import (
    load_manifest as load_bank_manifest,
    summarize as summarize_bank,
)
from .question_library import (
    ALWAYS_APPLICABLE_DIAGNOSTICS,
    load_library,
    validate_profile,
    valid_url,
)
from .question_manifest import (
    fact_questions,
    metric_contract_version_for_schema,
    validate_manifest_metric_contract,
    question_field_id,
    select_fact_questions,
)
from .question_prompts import (
    standard_prompt,
    typed_semantic_rules,
    legacy_typed_semantic_rules,
)
from .question_fingerprints import (
    question_fingerprint,
)
from .module_registry import (
    load_package,
    FACT_BANK_RESOURCE,
    observation_ingest_ready,
    validate_fact_bank,
)
from .routing import (
    resolve_route_decision,
    validate_route_snapshot,
    validate_route_for_execution,
)
from .question_sets import (
    compose_from_route,
    compose as compose_questions,
    basic_questions,
    load_library as load_active_bank,
)
from .frozen_release_projection import (
    create_execution_profile,
    create_company_assessment_v2,
    create_projection,
    create_question_config,
)

API_PROTOCOL = "iqs.questions-api/1.1.0"

__all__ = (
    "ALWAYS_APPLICABLE_DIAGNOSTICS",
    "API_PROTOCOL",
    "FACT_BANK_RESOURCE",
    "basic_questions",
    "compose_from_route",
    "compose_questions",
    "create_company_assessment_v2",
    "create_execution_profile",
    "create_projection",
    "create_question_config",
    "fact_questions",
    "legacy_typed_semantic_rules",
    "load_active_bank",
    "load_bank_manifest",
    "load_library",
    "load_package",
    "metric_contract_version_for_schema",
    "observation_ingest_ready",
    "question_field_id",
    "question_fingerprint",
    "resolve_route_decision",
    "select_fact_questions",
    "standard_prompt",
    "summarize_bank",
    "typed_semantic_rules",
    "validate_profile",
    "valid_url",
    "validate_fact_bank",
    "validate_manifest_metric_contract",
    "validate_route_for_execution",
    "validate_route_snapshot",
)
