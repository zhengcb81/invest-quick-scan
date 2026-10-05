# W06 审查跟进批次施工卡（F1/F2/F3，写前报告，2026-10-05）

## 授权与背景
- 来源：W06 独立审查记录的跟进项（task_plan Phase 61）——"F1/F2 落在 W06 case 范围外，**先于 work-item 存储落地前必修**"；owner 通授（2026-10-03）覆盖本批。
- F3 = TIME-03 测试缺口（IQS 侧，行为已被审查探针证实正确，仅补真实输入变化）。
- 纪律：TDD 先红后绿；两仓均在授权范围（StockWiki = 通授+写前报告；IQS = 本仓）。

## 变更范围（仅这些文件）
| 仓 | 文件 | 内容 |
|---|---|---|
| StockWiki | `stockwiki/quick_scan_freshness.py` | F1 代次对齐门（resume 前，C04 work_contract.py:160-162 语义：期望代次≠在途代次必须 dispatch）；F2 兼容门前置到 unknown/冷却分支之前（新身份不继承旧冷却），in-flight resume 保持最先并以 docstring 记录"防重复派发"取舍（审查者明示二选一）；F2b F1/F2 各配固定反例 |
| StockWiki | `tests/test_quick_scan_freshness.py` | +5~6 个 F1/F2 case（RED 先行） |
| IQS | `tests/test_freshness_and_jobs_contract.py` | F3：扩展 test_time_03 真实变更 checked_at/imported_at 并断言不失效续期 |

## 语义边界（不许动的）
- 不改 `freshness_status`/`observation_compatible`/`request_identity_key`/`build_gap_plan` 汇总与 `plan_sha256` 口径；
- 不改已有 10 case 的断言预期（只增不改）；
- 零网络/零写库不变（socket bomb 测试保持）；
- 决策词汇表不新增 decision 名（复用 dispatch_new_work/resume_existing_work/deferred_unknown）。

## 门
- StockWiki：定向 pytest 全绿 → `ruff`+`black(100)` 净 → `check_all.sh` 全绿（上次 907 passed 基线）；
- IQS：定向 `pytest tests/test_freshness_and_jobs_contract.py` 全绿 + `git diff --check`；
- 本批测试结果与 SHA 记入 progress.md；独立审查可并入后续里程碑合并审查（小任务不逐卡开审）。

## 审查轮修订（2026-10-05，r1 needs_revision 之后）
- **F1 范围扩展**：原卡写"resume 前"，r1 审查确认原 finding 字面是"复用/恢复前"（C04 门同时罩 reuse）→ 补 **P2-1 reuse 门**（work_item 存在且代次≠expected + fresh 观察 → dispatch/generation_mismatch + 反例测试）；case ②（无 work_item 不判冲突，C04 字面会 dispatch 的分歧）记入 `_field_decision` docstring 点 4，随 F2 的 resume-first 取舍一并留 owner 签认。
- **LOW 一并整改**：LOW-1（compat 系 reasons 追加 `status_x` 归因，不再替换）、LOW-2（不兼容分支 freshness 防御求值，未来/非法日期不再中止整计划）、LOW-4（单次求值）；LOW-3（结果+SHA 记 progress）已完成。
- 复跑证据：freshness 20/20、ruff/black 净、`check_all` ALL CHECKS PASSED；三文件 SHA 见 progress.md 同批记录。
