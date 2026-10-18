"""Independent candidate probes. Internal budget fixtures are not owner approval."""
from pathlib import Path
from contextlib import closing
import sqlite3
import sys
import pytest

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parents[1]
CANDIDATE=BASE/"response-diagnostic-candidate"
sys.path[:0]=[str(ROOT.parent/"StockQAbyLLM"),str(ROOT.parent/"iqs-agent-runtime-lab/src"),str(ROOT.parent/"iqs-company-agent-lab/src")]
import src.utils
src.utils.__path__.insert(0,str(CANDIDATE/"src/utils"))
import src.providers
src.providers.__path__.insert(0,str(CANDIDATE/"src/providers"))
import iqs_agent_runtime_lab
iqs_agent_runtime_lab.__path__.insert(0,str(CANDIDATE/"runtime/iqs_agent_runtime_lab"))
from src.providers.llm_research_client import ResearchChatSession,ResearchResponseValidationError
from src.utils.quick_scan_work_store import _sanitized_receipt,quick_scan_receipt_sha256
from src.utils.quick_scan_work_transport import QuickScanWorkUncertainError
from tests.unit.test_llm_research_client import TOOLS,budget,client,deny_network,response,transport

def test_arbitrary_validation_exception_message_never_reaches_native_receipt(tmp_path,transport):
    payload=response(tools=True)
    transport[0].payloads=[payload]
    session=ResearchChatSession(client(),system_prefix="rules",tools=TOOLS)
    name=payload["choices"][0]["message"]["tool_calls"][0]["function"]["name"]
    class ExplodingValidator:
        def validate(self,value):
            raise ValueError("PRIVATE_PROVIDER_BODY_SENTINEL_739")
    session._validators[name]=ExplodingValidator()
    with budget(tmp_path) as store:
        with pytest.raises(ResearchResponseValidationError) as err:
            session.step(user_context="strict rejection")
        assert err.value.attempt_receipt["research_validation_code"]=="research_response_validation_failed"
        assert store.get_quick_scan_budget_status("research-test")["spent_micros"]==1000
        with closing(sqlite3.connect(store.path)) as db:
            dump="\n".join(db.iterdump())
        assert "PRIVATE_PROVIDER_BODY_SENTINEL_739" not in dump
        assert store.get_research_visible_output(err.value.attempt_receipt["attempt_id"]) is None

def test_incoherent_reasoning_usage_does_not_gain_price_from_diagnostic(tmp_path,transport):
    payload=response();payload["choices"][0]["message"]["role"]="system"
    payload["usage"]["completion_tokens_details"]["reasoning_tokens"]=-1
    transport[0].payloads=[payload]
    with budget(tmp_path) as store:
        session=ResearchChatSession(client(),system_prefix="rules",tools=TOOLS)
        with pytest.raises(ResearchResponseValidationError) as err:session.step(user_context="negative count")
        receipt=err.value.attempt_receipt
        assert receipt["research_validation_code"]=="research_role_invalid" and "usage" not in receipt
        status=store.get_quick_scan_budget_status("research-test")
        assert status["unreconciled_attempts"]==1 and status["reserved_micros"]>0
        assert store.get_research_visible_output(receipt["attempt_id"]) is None
        with pytest.raises(RuntimeError):session.step(user_context="must not resend")
    assert len(transport[1])==1

@pytest.mark.parametrize("value",[" research_role_invalid","research_role_invalid\x00","RESEARCH_ROLE_INVALID","research_role_invalid\nPRIVATE_PROVIDER_BODY"])
def test_diagnostic_is_an_exact_literal_not_a_text_channel(value):
    assert _sanitized_receipt({"research_validation_code":value})=={}

def test_all_real_historical_receipts_keep_original_hash_without_backfill():
    import json
    source=BASE/"actual-native-alphabet-01/backup/original-ledger.raw.sqlite"
    with closing(sqlite3.connect(source.resolve().as_uri()+"?mode=ro",uri=True)) as db:
        db.execute("PRAGMA query_only=ON")
        receipts=db.execute("SELECT receipt_json,receipt_sha256 FROM quick_scan_attempt_response").fetchall()
    assert len(receipts)==99
    for raw,original_hash in receipts:
        value=json.loads(raw)
        assert "research_validation_code" not in value
        assert quick_scan_receipt_sha256(value)==original_hash

def test_explicit_semantic_subclass_does_not_reclassify_true_uncertainty():
    from iqs_agent_runtime_lab.receiptmap import classify_transport_failure
    received=ResearchResponseValidationError("ValueError",{"http_status_code":200,"research_validation_code":"research_role_invalid"},{"code":"research_role_invalid"})
    assert classify_transport_failure(received)==("rejected","provider_response_semantic_invalid")
    uncertain=QuickScanWorkUncertainError("original-physical",received.attempt_receipt)
    assert classify_transport_failure(uncertain)==("outcome_unknown","transport_outcome_uncertain")
