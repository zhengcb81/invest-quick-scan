"""New-request citation-copy instructions; never rewrite native answers/URLs."""
import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import question_prompts


@pytest.mark.parametrize("kind", ["score", "fact"])
def test_each_new_typed_rule_requires_exact_original_url_and_small_supported_evidence(kind):
    question = dict(id="SYNTHETIC_URL_RULE", response_kind=kind)
    before = copy.deepcopy(question)
    rule = question_prompts.typed_semantic_rules(question)
    assert "evidence[].url" in rule and "逐字复制" in rule and "query" in rule
    assert "lang/type/trk" in rule and "不得删除" in rule
    assert "通常2个" in rule and "不是硬性" in rule
    assert "不足" in rule and "凑数" in rule
    assert question == before


def test_historical_renderer_fingerprint_remains_original():
    assert question_prompts.renderer_rules_sha256() == "6b221598394f5c23a5f724c0b9bac895bcb44eee87c9189285eb605a6ebf21fe"
