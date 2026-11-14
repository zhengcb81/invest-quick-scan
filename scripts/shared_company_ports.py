"""Version negotiation for the cross-repository company-scan public APIs.

Each provider owns its implementation. IQS coordinates only the stable facade
versions below and does not discover peer modules through implementation paths.
"""
from __future__ import annotations

# Required minimums. A provider may add compatible minor/patch releases without
# forcing all consumers to upgrade in lockstep; changing the major is breaking.
SUPPORTED_OWNER_API_PROTOCOLS = {
    # Pin to the lowest facade versions currently evidenced by the owners'
    # candidate implementations. Older floors are not yet backed by clean
    # compatibility matrices and can admit APIs that the provider rejects.
    "stockqa": ("stockqa.company-scan-public-api", 1, 7),
    "company_agent": ("iqs.company-agent-public-api", 2, 3),
    "agent_runtime": ("iqs.agent-runtime-public-api", 1, 4),
}

# Minimum callable surface needed by ordinary shared-engine execution. These
# operations are reached before/during a normal run, so a version-compatible
# facade that omits one is not actually compatible. Recovery/report-only
# operations remain feature-local and are checked by the paths that use them.
REQUIRED_OWNER_API_OPERATIONS = {
    "stockqa": ("create_native_task", "create_company_scan_task", "create_company_research_runtime"),
    "company_agent": (
        "task_snapshot",
        "task_pack_sizes",
        "validate_scan_task",
        "sha256_hex",
        "native_company_projection",
        "ensure_safe_output_dir",
        "task_bundle",
        "canonical_json",
        "scan_for_secret",
        "create_durable_event_journal",
        "create_runner_port",
        "RunnerPortCrashed",
        "build_runner_checkpoint",
        "write_checkpoint",
        "event_journal_projection",
        "runner_event_projection",
        "check_citation_closure",
        "AnswerRejection",
        "parse_answers_payload",
        "loads",
        "write_runner_export",
    ),
    "agent_runtime": ("validate_session_config", "create_runtime_port"),
}


def required_owner_api_protocols():
    """Return stable minimum facade versions without importing sibling repos.

    Capability discovery must work in a clean process where provider repos are
    not installed. Runtime admission separately verifies providers' actual
    declarations with :func:`current_owner_api_protocols`.
    """
    return {
        owner: f"{family}/{major}.{minor}.0"
        for owner, (family, major, minor) in SUPPORTED_OWNER_API_PROTOCOLS.items()
    }


class OwnerApiProtocolError(ValueError):
    pass


def validate_owner_api_protocols(protocols):
    if not isinstance(protocols, dict) or set(protocols) != set(SUPPORTED_OWNER_API_PROTOCOLS):
        raise OwnerApiProtocolError("company_scan_owner_api_set_mismatch")
    unsupported = {}
    for owner, (family, required_major, required_minor) in SUPPORTED_OWNER_API_PROTOCOLS.items():
        value = protocols[owner]
        try:
            actual_family, version = value.rsplit("/", 1)
            major_text, minor_text, _patch_text = version.split(".")
            major, minor = int(major_text), int(minor_text)
            if any(not part.isdigit() for part in version.split(".")):
                raise ValueError
        except (AttributeError, TypeError, ValueError):
            unsupported[owner] = value
            continue
        if actual_family != family or major != required_major or minor < required_minor:
            unsupported[owner] = value
    if unsupported:
        raise OwnerApiProtocolError("company_scan_owner_api_version_unsupported")
    return dict(protocols)


def validate_owner_api_facades(facades):
    """Validate declared versions and the minimal callable public surface."""
    if not isinstance(facades, dict) or set(facades) != set(SUPPORTED_OWNER_API_PROTOCOLS):
        raise OwnerApiProtocolError("company_scan_owner_api_set_mismatch")
    protocols = {
        owner: getattr(facade, "PUBLIC_API_PROTOCOL", None)
        for owner, facade in facades.items()
    }
    validate_owner_api_protocols(protocols)
    for owner, required in REQUIRED_OWNER_API_OPERATIONS.items():
        facade = facades[owner]
        advertised = getattr(facade, "__all__", None)
        if (not isinstance(advertised, (list, tuple))
                or any(not isinstance(name, str) or not name for name in advertised)):
            raise OwnerApiProtocolError("company_scan_owner_api_operation_unavailable")
        try:
            missing = any(
                name not in advertised or not callable(getattr(facade, name, None))
                for name in required
            )
        except (AttributeError, ImportError):
            missing = True
        if missing:
            raise OwnerApiProtocolError("company_scan_owner_api_operation_unavailable")
    return protocols


def current_owner_api_protocols():
    """Read provider-declared versions from public facades only."""
    from importlib import import_module

    try:
        company_agent = import_module("iqs_company_agent_lab.api")
        agent_runtime = import_module("iqs_agent_runtime_lab.api")
        stockqa = import_module("src.utils.quick_scan_company_api")
    except ImportError as error:
        raise OwnerApiProtocolError("company_scan_owner_api_unavailable") from error

    return validate_owner_api_facades({
        "stockqa": stockqa,
        "company_agent": company_agent,
        "agent_runtime": agent_runtime,
    })
