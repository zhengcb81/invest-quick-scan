"""Versioned reuse-policy registry.

Two families ship in this lab:

* ``legacy-min-ttl/1.0.0`` — the frozen production rule, restated only as an
  adapter: ``valid_until = min(observed_at+TTL, information_as_of+TTL)``.
  The default path must stay differentially identical to the frozen stockwiki
  implementation (see legacy_oracle.py / parity harness).
* ``semantic-clocks/0.1.0-candidate`` — per-clock candidate rules with
  conservative fallbacks. Candidate-only: never production reuse.

Unknown policy families/versions are named refusals, never silent fallbacks.
"""

from __future__ import annotations

from typing import Any

from .errors import bad
from .timefields import CLOCKS

LEGACY_FAMILY = "legacy-min-ttl"
LEGACY_VERSION = "1.0.0"
CANDIDATE_FAMILY = "semantic-clocks"
CANDIDATE_VERSION = "0.1.0-candidate"

POLICY_FAMILIES = (LEGACY_FAMILY, CANDIDATE_FAMILY)

CLOCK_RULE_KEYS = ("max_age_hours", "on_missing", "rationale")


def _validate_clock_rule(clock: str, rule: dict[str, Any]) -> None:
    if clock not in CLOCKS:
        raise bad("clock_unknown", clock)
    if not isinstance(rule, dict):
        raise bad("policy_clock_rule_invalid", clock)
    extra = set(rule) - set(CLOCK_RULE_KEYS)
    if extra:
        raise bad("policy_clock_rule_extra_keys", f"{clock}:{sorted(extra)}")
    max_age = rule.get("max_age_hours")
    if max_age is not None and (isinstance(max_age, bool) or not isinstance(max_age, int) or max_age < 1):
        raise bad("policy_max_age_invalid", f"{clock}:{max_age!r}")
    if rule.get("on_missing") not in ("refresh", "not_assessable"):
        raise bad("policy_on_missing_invalid", f"{clock}:{rule.get('on_missing')!r}")


def legacy_policy(ttl_hours: int) -> dict[str, Any]:
    """Frozen rule restated as an explicit policy (defaults path)."""
    if isinstance(ttl_hours, bool) or not isinstance(ttl_hours, int) or ttl_hours < 1:
        raise bad("ttl_invalid", repr(ttl_hours))
    return {
        "policy_family": LEGACY_FAMILY,
        "policy_version": LEGACY_VERSION,
        "ttl_hours": ttl_hours,
        "candidate_only": False,
        "clock_rules": {
            "fact_valid_clock": {
                "max_age_hours": ttl_hours,
                "on_missing": "refresh",
                "rationale": "冻结规则：information_as_of+TTL（date-only按T00:00:00Z）",
            },
            "market_clock": {"max_age_hours": None, "on_missing": "not_assessable", "rationale": "legacy不单独评估"},
            "reporting_period_clock": {"max_age_hours": None, "on_missing": "not_assessable", "rationale": "legacy不单独评估"},
            "publication_clock": {"max_age_hours": None, "on_missing": "not_assessable", "rationale": "legacy在导入期校验，复用评估不查"},
            "verification_clock": {"max_age_hours": None, "on_missing": "not_assessable", "rationale": "legacy无核查回执域"},
        },
    }


def candidate_policy(clock_rules: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """Candidate per-clock policy. Defaults are honest nulls (undecided)."""
    rules = {
        "fact_valid_clock": {
            "max_age_hours": 24,
            "on_missing": "refresh",
            "rationale": "有依据提案：答案执行新鲜度沿用原契约24h基线（observed_at腿）；information_as_of不再作TTL续命腿，其自身时点按其他钟评估",
        },
        "market_clock": {
            "max_age_hours": 24,
            "on_missing": "refresh",
            "rationale": "有依据提案：行情逐日更新且原契约已有24h TTL基线；新交易日收盘即过期",
        },
        "reporting_period_clock": {
            "max_age_hours": None,
            "on_missing": "refresh",
            "rationale": "期限取决于披露日历而非固定小时；需owner按指标→下一披露映射实验裁决",
        },
        "publication_clock": {
            "max_age_hours": None,
            "on_missing": "not_assessable",
            "rationale": "逐条约束published_at≤cutoff；无期限语义",
        },
        "verification_clock": {
            "max_age_hours": None,
            "on_missing": "refresh",
            "rationale": "需真实覆盖回执设计；回执期限/格式待owner裁决，缺回执一律保守",
        },
    }
    if clock_rules:
        for clock, patch in clock_rules.items():
            if clock not in rules:
                raise bad("clock_unknown", clock)
            merged = dict(rules[clock])
            merged.update(patch)
            rules[clock] = merged
    for clock, rule in rules.items():
        _validate_clock_rule(clock, rule)
    return {
        "policy_family": CANDIDATE_FAMILY,
        "policy_version": CANDIDATE_VERSION,
        "ttl_hours": None,
        "candidate_only": True,
        "clock_rules": rules,
    }


def _registry() -> dict[str, dict[str, Any]]:
    return {
        f"{LEGACY_FAMILY}/{LEGACY_VERSION}": legacy_policy(24),
        f"{CANDIDATE_FAMILY}/{CANDIDATE_VERSION}": candidate_policy(),
    }


def policy_registry() -> dict[str, dict[str, Any]]:
    return _registry()


def resolve_policy(policy_ref: str, *, ttl_hours: int | None = None) -> dict[str, Any]:
    """Select an explicit policy by ``family/version``; unknown refs are refusals."""
    if not isinstance(policy_ref, str) or not policy_ref.strip():
        raise bad("policy_ref_invalid", repr(policy_ref))
    registry = _registry()
    if policy_ref not in registry:
        raise bad("policy_version_unknown", policy_ref)
    policy = registry[policy_ref]
    if policy["policy_family"] == LEGACY_FAMILY:
        return legacy_policy(ttl_hours if ttl_hours is not None else policy["ttl_hours"])
    return candidate_policy()


def validate_question_policy(entry: dict[str, Any]) -> None:
    """Shape-check one catalog-derived question policy entry (strict)."""
    if not isinstance(entry, dict):
        raise bad("question_policy_invalid", type(entry).__name__)
    required = (
        "question_id",
        "field_id",
        "module_id",
        "question_kind",
        "knowledge_kind",
        "required_clocks",
        "policy_family",
        "max_age_proposal_hours",
        "rationale",
        "legacy_fallback",
        "source_refs",
    )
    missing = [key for key in required if key not in entry]
    if missing:
        raise bad("question_policy_missing_keys", ",".join(missing))
    if entry["question_kind"] not in ("score", "fact"):
        raise bad("question_kind_invalid", repr(entry["question_kind"]))
    if entry["knowledge_kind"] not in ("market_sensitive", "periodic_financial", "structural", "event_sensitive", "mixed"):
        raise bad("knowledge_kind_invalid", repr(entry["knowledge_kind"]))
    clocks = entry["required_clocks"]
    if not isinstance(clocks, list) or not clocks or any(c not in CLOCKS for c in clocks):
        raise bad("required_clocks_invalid", repr(clocks))
    if len(set(clocks)) != len(clocks):
        raise bad("required_clocks_duplicate", repr(clocks))
    if entry["knowledge_kind"] == "mixed" and len(clocks) < 3:
        # A mixed question must split at least two non-fact clocks; a single
        # clock would hide one date behind another (card requirement).
        raise bad("mixed_needs_multiple_clocks", repr(clocks))
    max_age = entry["max_age_proposal_hours"]
    if max_age is not None and (isinstance(max_age, bool) or not isinstance(max_age, int) or max_age < 1):
        raise bad("max_age_proposal_invalid", repr(max_age))
    if not isinstance(entry["rationale"], str) or not entry["rationale"].strip():
        raise bad("rationale_missing", entry.get("question_id", "?"))
    if not isinstance(entry["legacy_fallback"], dict):
        raise bad("legacy_fallback_invalid", entry.get("question_id", "?"))
    if not isinstance(entry["source_refs"], list) or not entry["source_refs"]:
        raise bad("source_refs_missing", entry.get("question_id", "?"))
