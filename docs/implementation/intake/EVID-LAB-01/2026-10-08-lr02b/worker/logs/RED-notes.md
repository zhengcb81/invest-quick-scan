# EVID-LAB-01 RED 记录（开发会话内真实失败，修复后转 GREEN）

以下失败发生在本包 TDD 过程中，输出为会话内 pytest 原文摘录（已去除颜色码）。
最终全量回归见 `final-regression-GREEN.log`（54 passed，exit 0）。

## RED-1 `tests/test_inputs_verification.py`（2 failed）

```
FAILED tests/test_inputs_verification.py::test_missing_bound_file_fails_closed
  InputDriftError: locked input drift detected (2): iqs_input:gone.json:missing;
  experiment_index:gone-index.json:missing
  （原因：strict=True 在断言 status 之前就抛出；测试先用 non-strict 断言 missing，再断言 strict 抛错）

FAILED tests/test_inputs_verification.py::test_snapshot_input_hashes_covers_lock_and_index
  AssertionError: assert 'inputs.lock.json' in {...full absolute path key...}
  （原因：snapshot 以绝对路径为 key；改为 lock 文件名为 key）
```

修复：调整测试顺序与 snapshot 键；实现改为 `lock_path.name`。→ GREEN

## RED-2 `tests/test_recoverability.py`（1 failed）

```
FAILED tests/test_recoverability.py::test_all_three_archives_report_honestly
  Differing items: {'rejected': 0} != {'rejected': 53}
  （原因：totals 字典键写错，'rejected' 从未累加）
```

修复：改用 `rejected_packages`/`items` 两个键并正确累加。→ GREEN

## RED-3 `tests/test_semantic.py`（4 failed）

```
FAILED test_period_contradiction_located_with_explicit_evidence
FAILED test_same_url_different_window_conflict
FAILED test_every_dimension_contradiction_has_error_code[2026H1-2025全年-period]
FAILED test_unknown_status_claim_contradiction_is_still_diagnosed
  AssertionError: assert ('abstain' == 'fail' ...)
  （原因：normalize_period 不识别“2026全年”，返回 None → 引擎按规则 abstain）
```

修复：`normalize_period` 增加“全年”解析（含年份提取），并删除早期编辑遗留的
不可达重复函数体；窗口冲突用例随期间归一自动修复。→ GREEN

## 说明

- 无失败被跳过或放宽断言；所有修复都是让规则更完整，不是让断言更松。
- 没有为了得到 GREEN 而改动任何 IQS/StockQA/StockWiki 输入。
