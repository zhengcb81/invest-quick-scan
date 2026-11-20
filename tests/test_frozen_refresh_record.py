"""Offline public validation of historical originals without replaying the planner."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import refresh_contract as refresh
from test_refresh_contract import inputs, preview
from test_refresh_ordered_routes import ordered_inputs


@pytest.mark.parametrize("version", ["1.0.0", "1.1.0", "1.6.0"])
def test_original_frozen_record_uses_its_own_dialect(version):
    request, state = ordered_inputs() if version == "1.6.0" else inputs()
    if version == "1.1.0":
        request["protocol"] = "iqs.refresh_request/1.1.0"
        request["source_query"]["schema_version"] = "2.6.0"
        state["quote"]["currency"] = "CNY"
    frozen = dict(request=request, preview=preview(request, state), owner_state=state)
    cli = Path(__file__).resolve().parents[1] / "scripts/refresh_contract_cli.py"
    command = [sys.executable, "-B", "-X", "utf8", str(cli),
               "--operation", "frozen-record", "--input", "-"]

    def invoke(value):
        run = subprocess.run(command, input=json.dumps(value).encode(),
                             capture_output=True, timeout=25, check=False)
        return run.returncode, json.loads(run.stdout)

    code, reply = invoke(frozen)
    assert code == 0 and reply["status"] == "validated"
    assert reply["input_sha256"] == refresh.digest(frozen)
    assert reply["result"] == {"request_protocol": request["protocol"]}
    assert reply["API_requests"] == reply["database_writes"] == 0
    assert reply["permission_authenticated"] is False
    assert frozen["preview"]["expires_at"] == "2026-10-10T12:13:00Z"

    frozen["owner_state"]["model"] = "another-model"
    code, reply = invoke(frozen)
    assert code == 2 and reply["error_code"] == "refresh_contract_rejected"


def test_frozen_check_does_not_call_the_current_planner(monkeypatch):
    request, state = inputs()
    frozen = dict(request=request, preview=preview(request, state), owner_state=state)

    def unexpected(*args, **kwargs):
        pytest.fail("paid historical read entered the current planner")

    monkeypatch.setattr(refresh, "create_preview", unexpected)
    assert refresh.validate_frozen_record(**frozen) == {"request_protocol": request["protocol"]}



def test_resealed_preview_from_another_dialect_is_rejected():
    request, state = inputs()
    mismatched = preview(request, state)
    mismatched["protocol"] = "stockwiki.refresh_preview/1.1.0"
    mismatched["preview_id"] = "rv1_" + refresh.digest(
        {key: value for key, value in mismatched.items() if key != "preview_id"}
    )
    with pytest.raises(ValueError, match="refresh_document_invalid"):
        refresh.validate_frozen_record(request=request, preview=mismatched, owner_state=state)
