"""G-IQS-01: the IQSLink capability declaration for the Dashboard.

This module is deliberately narrow. It publishes only what the live IQS owner
can honour right now, in the frozen Dashboard `IQSLink`/`IQSRoutes` shape, and
it refuses to echo any return target that is not a configured local logical
Dashboard route. It reads no database, calls no model and performs no I/O.

The Dashboard contract is `contracts/openapi.yaml` 0.1.1-b; `IQSLink` and
`IQSRoutes` are `additionalProperties: false`, so this module emits exactly the
eight declared keys and no others.
"""

from __future__ import annotations

from urllib.parse import urlsplit

SERVICE_ID = "invest-quick-scan"
ROUTE_TEMPLATE_VERSION = "iqs.dashboard.owner/1.0.0"

# The logical Dashboard routes this owner may hand a user back to. Absolute
# origins are never accepted here: the Dashboard origin is the Dashboard's own
# business, not the IQS owner's.
RETURN_ROUTE_ALLOWLIST = frozenset(
    {
        "/results",
        "/history",
        "/facts",
        "/dashboard",
        "/operations",
        "/universe",
        "/screener",
        "/companies",
    }
)

RETURN_QUERY_ALLOWLIST = {
    "/results": frozenset(
        {"query", "view", "offset", "limit", "conditions", "condition_combine", "filters", "snapshot_token"}
    ),
    "/history": frozenset({"id"}),
    "/facts": frozenset({"id"}),
    "/dashboard": frozenset(),
    "/operations": frozenset(),
    "/universe": frozenset(),
    "/screener": frozenset(),
    "/companies": frozenset({"q"}),
}

# B03: the Dashboard company workspace routes (its router renders
# `/company/<ENT>/<tab>`; no tab means the overview tab). A company return
# carries the original listing/scope filter, so those two keys are the only
# query keys a company return may bind. Duplicated keys are refused here:
# a repeated `listing_id` is ambiguous and must never survive into a route
# a user is navigated back to.
COMPANY_ROUTE_TABS = frozenset({"overview", "documents", "research", "forecast", "quickscan"})
COMPANY_RETURN_QUERY_ALLOWLIST = frozenset({"listing_id", "analysis_subject_id"})

FALLBACK_RETURN = "#/results"

CONTEXTS = ("entity", "listing", "subject", "observation", "return_to")


class LinkError(Exception):
    """A caller error the transport should report as 400."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def safe_entity_id(value: object) -> str | None:
    """Accept only the bounded identifier shape the owner publishes.

    Whitespace is refused rather than trimmed: an id must match the owner's
    value exactly, the same rule the UI module applies. Used at the link
    boundary so a malformed id is never treated as addressable.
    """
    if not isinstance(value, str):
        return None
    if not value or len(value) > 256:
        return None
    if not value[0].isascii() or not value[0].isalnum():
        return None
    for char in value:
        if char.isascii() and (char.isalnum() or char in "_.:-"):
            continue
        return None
    return value


def _company_route(path: object) -> tuple[str, str | None] | None:
    """Split a `/company/<ENT>[/<tab>]` path; None when it is not one.

    The tabs are the Dashboard company router's real tabs; a missing tab is
    the overview tab. The entity segment must pass the same bounded
    identifier rule as every owner-published id.
    """
    if not isinstance(path, str) or not path.startswith("/company/"):
        return None
    segments = path.split("/")
    if len(segments) == 3:
        entity_id = safe_entity_id(segments[2])
        return (entity_id, None) if entity_id else None
    if len(segments) == 4 and segments[3] in COMPANY_ROUTE_TABS:
        entity_id = safe_entity_id(segments[2])
        return (entity_id, segments[3]) if entity_id else None
    return None


def _query_keys_ok(query: str, allowed: frozenset) -> bool:
    """Bounded query keys with duplicate refusal (a repeated key is ambiguous)."""
    seen: set[str] = set()
    for pair in query.split("&") if query else ():
        if not pair:
            continue
        key = pair.split("=", 1)[0]
        if key not in allowed or key in seen:
            return False
        seen.add(key)
    return True


def _safe_absolute_company_return(raw: str) -> str | None:
    """Validate an absolute trusted-loopback Dashboard company return URL.

    Only a concrete loopback http(s) origin over an explicit company route
    with bounded query keys is accepted; a fragment, foreign host, encoded
    bypass or cross-scope parameter makes the whole value unusable.
    """
    try:
        parsed = urlsplit(raw)
    except ValueError:
        return None
    if parsed.fragment:
        return None
    origin = _base_origin(f"{parsed.scheme}://{parsed.netloc}")
    if origin is None:
        return None
    if _company_route(parsed.path) is None:
        return None
    if not _query_keys_ok(parsed.query, COMPANY_RETURN_QUERY_ALLOWLIST):
        return None
    return raw


def company_return_entity(value: object) -> str | None:
    """The entity named by a validated company return route, else None.

    The Dashboard service uses this to refuse a return that names a DIFFERENT
    company than the link being composed (cross-scope injection), and the UI
    module mirrors the same rule.
    """
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if raw.startswith("#"):
        route = _company_route(raw[1:].partition("?")[0])
        return route[0] if route else None
    lowered = raw.lower()
    if lowered.startswith("http://") or lowered.startswith("https://"):
        try:
            parsed = urlsplit(raw)
        except ValueError:
            return None
        route = _company_route(parsed.path)
        return route[0] if route else None
    return None


def safe_return_to(value: object) -> str:
    """Return a validated logical Dashboard route, or the plain results list.

    Rejects protocol-relative URLs, foreign schemes, extra fragments, control
    characters and any route outside the allowlist. B03 adds two accepted
    forms beside the eight logical routes: the Dashboard company workspace
    route `#/company/<ENT>[/<tab>]`, and — because the IQS UI lives on a
    different loopback origin than the Dashboard — the same company route as
    an absolute trusted-loopback URL, which is the only form a back link can
    actually navigate. Everything else still collapses to the fallback.
    """
    if not isinstance(value, str):
        return FALLBACK_RETURN
    raw = value.strip()
    if not raw or len(raw) > 16000:
        return FALLBACK_RETURN
    if any(ord(char) < 0x20 or ord(char) == 0x7F or char == "\\" for char in raw):
        return FALLBACK_RETURN
    # Percent-encoded control characters are refused too: decoding them later
    # could reintroduce a CR/LF or NUL after this check has already passed.
    lowered = raw.lower()
    if any(f"%{code:02x}" in lowered for code in range(0x00, 0x20)) or "%7f" in lowered:
        return FALLBACK_RETURN
    if lowered.startswith(("http://", "https://")):
        absolute = _safe_absolute_company_return(raw)
        return absolute if absolute is not None else FALLBACK_RETURN
    if not raw.startswith("#"):
        return FALLBACK_RETURN
    body = raw[1:]
    if not body.startswith("/") or body.startswith("//"):
        return FALLBACK_RETURN
    # A second fragment marker could splice a different route into the value.
    if "#" in body:
        return FALLBACK_RETURN
    path, _, query = body.partition("?")
    if path in RETURN_ROUTE_ALLOWLIST:
        allowed = RETURN_QUERY_ALLOWLIST[path]
        for pair in query.split("&") if query else ():
            if not pair:
                continue
            key = pair.split("=", 1)[0]
            if key not in allowed:
                return FALLBACK_RETURN
        return f"#{body}"
    if _company_route(path) is not None:
        if not _query_keys_ok(query, COMPANY_RETURN_QUERY_ALLOWLIST):
            return FALLBACK_RETURN
        return f"#{body}"
    return FALLBACK_RETURN


def _base_origin(value: object) -> str | None:
    """Only a concrete loopback http(s) origin is a usable deeplink base."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text or len(text) > 2048 or any(char.isspace() for char in text):
        return None
    try:
        parsed = urlsplit(text)
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        return None
    # Credentials in an origin would be echoed into every published route, so a
    # userinfo component is refused outright rather than stripped silently.
    if parsed.username is not None or parsed.password is not None or "@" in parsed.netloc:
        return None
    host = parsed.hostname
    if host not in {"127.0.0.1", "localhost", "::1"}:
        return None
    # A port must be a real TCP port; `http://127.0.0.1:99999` and a trailing
    # colon with no digits are both unusable addresses.
    if parsed.netloc.endswith(":"):
        return None
    try:
        port = parsed.port
    except ValueError:
        return None
    if port is not None and not 1 <= port <= 65535:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def capability(
    *,
    base_origin: object = None,
    observation_count: object = None,
    observation_state: object = None,
    has_subject: object = None,
    return_to: object = None,
) -> dict:
    """Build the frozen `IQSLink` object for the current owner state.

    `observation_count` is the number of formal observations the owner can
    address. When it is zero the `observation` context is not advertised,
    because a link that cannot resolve is worse than no link.

    `observation_state` distinguishes WHY the context is missing:

    - ``"counted"``      - a real count was obtained (0 or more)
    - ``"unreadable"``   - the owner could not be read, so the count is unknown
    - ``"unconfigured"`` - no owner read was attempted (no origin configured)

    `has_subject` says whether any formal row actually carries an
    `analysis_subject_id`. A workspace of legacy rows has the column but always
    NULL, so a subject-scoped link there cannot resolve and must not be
    advertised (review REV4-03).

    The frozen `IQSLink` has no free-text reason field (`additionalProperties:
    false`), but its `status` enum includes ``"incompatible"``, whose contract
    meaning is "this owner cannot be used as declared". An unreadable owner is
    reported as ``incompatible`` while a genuine zero stays ``partial``, so the
    two cases are distinguishable inside the frozen schema instead of being
    collapsed. No key is added.
    """
    origin = _base_origin(base_origin)
    if observation_state not in {"counted", "unreadable", "unconfigured"}:
        observation_state = "counted" if isinstance(observation_count, int) else "unreadable"
    has_observations = (
        observation_state == "counted"
        and isinstance(observation_count, int)
        and not isinstance(observation_count, bool)
        and observation_count > 0
    )
    subject_available = has_observations and has_subject is True
    contexts: list[str] = []
    if origin:
        contexts = ["entity", "listing"]
        # `observation` depends only on a formal observation existing.
        if has_observations:
            contexts.append("observation")
        # `subject` additionally needs a formal row that actually carries
        # `analysis_subject_id`; otherwise a subject-scoped link cannot resolve.
        if subject_available:
            contexts.append("subject")
        contexts.append("return_to")
    if not origin:
        status = "unavailable"
    elif has_observations:
        status = "available"
    elif observation_state == "unreadable":
        # "Cannot read" is not "has none": the declaration is unusable as
        # evidence of absence, which is exactly `incompatible`.
        status = "incompatible"
    else:
        status = "partial"
    routes = (
        {
            "results": f"{origin}/#/results",
            "history": f"{origin}/#/history",
            "facts": f"{origin}/#/facts",
            "launch": f"{origin}/",
        }
        if origin
        else {"results": None, "history": None, "facts": None, "launch": None}
    )
    return {
        "service_id": SERVICE_ID,
        "base_origin": origin,
        "route_template_version": ROUTE_TEMPLATE_VERSION,
        "supported_context": contexts,
        "mode": "deeplink" if origin else "unavailable",
        "status": status,
        "routes": routes,
        "return_to": safe_return_to(return_to) if origin else None,
    }


# NOTE (REV2-06/REV3-01): a `result_link()` composer used to live here. It had
# no production caller and produced a second, subtly different query encoding
# from the UI's `URLSearchParams`, so it was removed rather than left as a trap
# for the next author. The exact deep link is composed by the UI
# (`src/app/ui/deep_link.js::formalResultLink`), which is the side that owns the
# logical Dashboard route space.
