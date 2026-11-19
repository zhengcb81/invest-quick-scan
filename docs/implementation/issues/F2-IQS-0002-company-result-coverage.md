# F2-IQS-0002 公司结果读投影不发布逐题覆盖，部分完成与尺度缺组无法辨认

- issue_key: `iqs-company-result-coverage-not-published`
- 状态: verified
- 期望/实际: `claim-matches-refs` / `complete-claimed`；
  `scales-addressable` / `scale-without-group`
  （影响：`GET company/result` 与 `GET company/history` 只把 owner 快照原样
  转发，读者看不到哪一题被观察、哪一组没有任何观察；owner 若声明
  36/36 而只绑定 35 条引用，公开响应与 owner 声明完全一致地"完整"）
- 责任层: 本仓 `scripts/iqs_scan/workbench/dashboard_company_projection.py`
  与 `scripts/iqs_scan/workbench/company_result_coverage.py`
- 修复版本: `invest-quick-scan/company_assessment-1.1.0-obs1`
- 复验: verified @ `invest-quick-scan/company_assessment-1.1.0-obs1`

## 发生引用

| # | run_id | attempt_id | step_id | check_id | evidence_ref |
|---|---|---|---|---|---|
| 1 | `manifest-delivery-01` | `injected-partial-claiming-complete` | `company-result/ENT_99deceb6-f58a-48b1-bd6b-437621015d76` | `coverage-claim` | `iqs:company/ENT_99deceb6…/cas_83694b860296b314daed` |
| 2 | `manifest-delivery-01` | `injected-scale-dropped` | 同上 | `scale-lineage` | `iqs:company/ENT_99deceb6…/cas_0fd4e809aa4a51991b5d` |

两条都是**临时公开响应**：把本工作树 MANIFEST-DELIVERY-01 交付里真实的
36 题 V2 请求（`delivery/register-request-v2.json`）投影成 owner 公开快照形状，
再按施工卡注入一个遗漏题 / 一个整尺度缺失。真实 owner workspace 当前没有
已登记结果（`read-after.json` 的 `company_result_not_registered`），因此这一
缺陷没有"真实已注册快照"可复现——这也是它此前没被发现的原因。

## 最小复现

```bash
python -B -X utf8 scripts/company_result_feedback.py \
  --inject-result tests/fixtures/company_coverage/result-partial-claiming-complete.json \
  --out /tmp/injected.jsonl --run-id replay --attempt-id attempt-1
```

修复前：`project_result()` 的响应里没有 `coverage`，35 条引用与
`completeness.observed_count=36` 一起原样转发；`company/history` 同理只有
`manifest_question_count`/`observed_count` 两个数字，看不出哪一题缺。

## 根因（已证）

`project_result()` / `project_history()` 只校验 `result_id`、`entity_id`、
`aggregate_score` 三项，从不把 owner 的完整性声明与它绑定的引用对账，也不
派生逐题状态；`frozen_release_projection.create_company_assessment_v2()` 一侧
本来就按 `(rubric_version, aggregation_role)` 分区并保留每组原尺度，读侧却
没有把这份结构发布出去。

## RED / GREEN

- RED：`tests/test_company_result_coverage.py` 在收集期失败
  （`ModuleNotFoundError: No module named 'company_result_coverage'`，1 error）；
  同一批的 `tests/test_scan_result_check.py` 5 failed（`KeyError: 'coverage'`）。
- GREEN：`test_company_result_coverage.py` 37 例通过（含 2 例回放入口），
  四文件组合 **126 passed / 0 failed / 0 skipped**；
  `test_dashboard_company_result.py` 61 例、`test_company_assessment_v2_projection.py`
  13 例、`test_scan_result_check.py` 14 例保持通过。

## 同类场景与反例

- 同类：任何 V2 混尺度快照（`scale_version=null` + `scale_versions` 两项）、
  任何 `observed_count` 与引用条数不一致的快照、任何声明的尺度没有任何组承载、
  任何引用指向释放外题号。
- 反例（必须不报错）：36/36 的混尺度完整结果、单尺度完整结果、
  `company_result_not_registered` 这类带名空结果、以及**如实声明**缺项的
  空组（合法部分结果，只披露不归责）。
- 已知边界：若某个组连同它的题目一起从 `lineage_groups` 移除，而同 rubric 的
  另一个组仍在，公开快照无法与"更小的释放"区分（`scale_versions` 是 rubric
  级）。这种情况需要消费方拿 `source_release_sha256` 对冻结释放复核；本卡
  不声称能单独判定。
- 上游责任：owner 声明与引用自相矛盾（`coverage-claim`）或声明的尺度没有组
  （`scale-lineage`）记 `owner=stockwiki`、`origin_owner=invest-quick-scan`，
  因为只有 StockWiki 能改它自己的快照；本仓只保证披露、不转发成完整。
  真实 owner 路径的 `completeness` 由引用算出，结构上不会自相矛盾，因此
  **没有**据此判 StockWiki 缺陷；该行是披露机制，不是已证上游问题。
