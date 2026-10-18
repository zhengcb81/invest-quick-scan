"""Independent public-write boundary cases; all credentials are fake markers."""
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE.parents[2] / "iqs-company-agent-lab/src"))
import iqs_company_agent_lab

iqs_company_agent_lab.__path__.insert(0, str(BASE / "secret-boundary-candidate/src/iqs_company_agent_lab"))
from iqs_company_agent_lab.events import scan_for_secret
from iqs_company_agent_lab.receipts import check_no_secret, credential_marker
from iqs_company_agent_lab.errors import SecretDetectedError, ProtocolIllegalError


@pytest.mark.parametrize("text", ["ask-price spread", "brisk-demand recovery", "desk-research findings",
                                  "风险评估使用risk-weighted assets", "任务task-summary remains visible"])
def test_unseen_financial_and_operational_prose_survives_both_write_guards(text):
    assert credential_marker(text) is None
    scan_for_secret(text)
    check_no_secret(text, "independent ordinary narrative")


@pytest.mark.parametrize("prefix", ["", " ", "\n", "\t", "'", '"', "=", ":", "(", "[", "_", "-", "密钥", "é"])
def test_boundary_after_punctuation_unicode_and_start_still_refuses(prefix):
    text = prefix + "sk-FAKE-DO-NOT-USE"
    assert credential_marker(text) == "sk-"
    with pytest.raises(SecretDetectedError):
        scan_for_secret(text)
    with pytest.raises(ProtocolIllegalError):
        check_no_secret(text, "independent fake marker")


@pytest.mark.parametrize("marker", ["Authorization", "Bearer ", "api_key", "apikey", "eyJ"])
def test_other_families_keep_original_substring_refusal(marker):
    text = "ordinary-prefix" + marker + "FAKE"
    assert credential_marker(text) == marker
    with pytest.raises(SecretDetectedError):
        scan_for_secret(text)
    with pytest.raises(ProtocolIllegalError):
        check_no_secret(text, "independent fake marker")
