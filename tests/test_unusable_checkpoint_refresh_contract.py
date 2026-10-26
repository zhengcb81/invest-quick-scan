"""Additive purpose uses original control contract; never grants authority."""

import pytest
from test_refresh_contract import preview
from test_refresh_owner_control_contract import controlled_inputs


def test_checkpoint_unusable_control_retains_original_ready_status_and_plans_next_generation():
    req, state = controlled_inputs()
    for item in state["items"]:
        item["owner_control"].update(purpose="retry_unusable_checkpoint", comparison_controls=None)
        item["existing_work_status"] = "result_ready"
    out = preview(req, state)
    assert out["status"] == "ready" and all(
        i["generation"] == 2 and i["existing_work_status"] == "result_ready" for i in out["items"]
    )


@pytest.mark.parametrize("status", ["failed", "delivered", "leased", "uncertain"])
def test_new_purpose_never_accepts_other_source_status(status):
    req, state = controlled_inputs()
    for item in state["items"]:
        item["owner_control"].update(purpose="retry_unusable_checkpoint", comparison_controls=None)
        item["existing_work_status"] = status
    with pytest.raises(ValueError):
        preview(req, state)
