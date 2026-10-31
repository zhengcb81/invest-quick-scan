"""TIME-SEMANTICS-30 lab package: composable, versioned reuse-policy candidates
with an offline interpreter plus frozen-legacy parity.

Candidate-only: nothing here changes StockWiki/StockQA/IQS production schemas,
TTLs, or grants any reuse/verification status. Real clocks are always supplied
explicitly by the caller; this package never reads the wall clock.
"""

from .assess import assess_reuse
from .errors import TimeSemanticsError
from .policy import POLICY_FAMILIES, policy_registry, resolve_policy

PROTOCOL = "iqs.temporal_policy_candidate/1.0.0"
PRODUCTION_READY = False

__all__ = [
    "assess_reuse",
    "policy_registry",
    "resolve_policy",
    "POLICY_FAMILIES",
    "TimeSemanticsError",
    "PROTOCOL",
    "PRODUCTION_READY",
]
