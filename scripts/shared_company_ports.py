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
    "stockqa": ("stockqa.company-scan-public-api", 1, 5),
    "company_agent": ("iqs.company-agent-public-api", 2, 3),
    "agent_runtime": ("iqs.agent-runtime-public-api", 1, 4),
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


def current_owner_api_protocols():
    """Read provider-declared versions from public facades only."""
    try:
        from iqs_company_agent_lab.api import PUBLIC_API_PROTOCOL as company_agent
        from iqs_agent_runtime_lab.api import PUBLIC_API_PROTOCOL as agent_runtime
        from src.utils.quick_scan_company_api import PUBLIC_API_PROTOCOL as stockqa
    except ImportError as error:
        raise OwnerApiProtocolError("company_scan_owner_api_unavailable") from error

    return validate_owner_api_protocols({
        "stockqa": stockqa,
        "company_agent": company_agent,
        "agent_runtime": agent_runtime,
    })
