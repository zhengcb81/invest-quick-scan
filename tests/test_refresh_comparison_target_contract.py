"""Versioned wire target candidates; no owner authentication or financial gold."""

import copy

import pytest
import refresh_contract as refresh
from test_refresh_contract import preview
from test_refresh_owner_control_contract import controlled_inputs


def targeted():
    request, state = controlled_inputs()
    request["protocol"] = "iqs.refresh_request/1.3.0"
    state.update(provider="minimax", model="MiniMax-M3.1-Flash")
    for item in state["items"]:
        item["owner_control"]["comparison_target"] = dict(
            provider="minimax",
            model="MiniMax-M3.1-Flash",
            route_id="minimax-target",
            provider_config_ref="minimax-config",
            policy_id="shared-budget",
            owner_policy_sha256=state["policy_sha256"],
        )
    return request, state


def test_new_target_wire_binds_target_owner_policy_without_reinterpreting_legacy_controls():
    request, state = targeted()
    result = preview(request, state)
    assert result["protocol"] == "stockwiki.refresh_preview/1.3.0"
    refresh.validate_preview(result, request=request, owner_state=state)
    assert result["items"] == state["items"] and result["API_requests"] == 0


@pytest.mark.parametrize(
    "fault",
    ["provider", "model", "policy_hash", "missing", "old_version", "extra_target"],
)
def test_resealed_consumer_target_cannot_expand_policy_or_old_wire(fault):
    request, state = targeted()
    target = state["items"][0]["owner_control"]["comparison_target"]
    if fault == "provider":
        target["provider"] = "mimo"
    elif fault == "model":
        target["model"] = "other-model"
    elif fault == "policy_hash":
        target["owner_policy_sha256"] = "0" * 64
    elif fault == "missing":
        del state["items"][0]["owner_control"]["comparison_target"]
    elif fault == "old_version":
        request["protocol"] = "iqs.refresh_request/1.2.0"
    else:
        target["approved"] = True
    with pytest.raises(ValueError):
        preview(request, state)


@pytest.mark.parametrize("purpose", ["retry_unknown_answer", "retry_unusable_answer"])
def test_target_dialect_declares_only_independent_comparison(purpose):
    request, state = targeted()
    control = state["items"][0]["owner_control"]
    control.update(purpose=purpose, comparison_controls=None, comparison_target=None)
    with pytest.raises(ValueError):
        preview(request, state)
