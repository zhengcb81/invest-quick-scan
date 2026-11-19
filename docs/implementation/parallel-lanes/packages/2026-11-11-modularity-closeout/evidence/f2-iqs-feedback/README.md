# F2-IQS-FEEDBACK 观察样本

2026-11-19。六份 `feedback-observation/1` JSONL，均由本仓公开读入口
（`read_company_assessment` → `project_result` → `dashboard_company_feedback`）
产出，或由同一个投影对**临时公开响应**产出。全部为脱敏投影：不含公司正文、
不含凭据、不含物理路径，`evidence_ref` 是逻辑引用。

| 文件 | 来源 | 结果 |
|---|---|---|
| `real-read-absent.jsonl` | 真实 owner workspace `runs/r25-live/owner-workspace` 的公开读（只读，0 模型调用） | `owner-absence=reason-named` 符合预期；其余五项 `no-result` 记 `unknown` |
| `injected-partial-claiming-complete.jsonl` | 临时公开响应：36 题真实请求投影出的快照，注入 1 道遗漏题且 owner 仍声明 36/36 | `coverage-claim=complete-claimed` 偏差，`owner=stockwiki` |
| `injected-scale-dropped.jsonl` | 临时公开响应：整个 `2.0.0` 尺度（两个组、5 题）连同引用一起消失，`scale_versions` 仍列 2.0.0 | `scale-lineage=scale-without-group` 偏差，`owner=stockwiki` |
| `injected-group-declared-empty.jsonl` | 临时公开响应：整组 `2.0.0/quality_core`（3 题）无观察，但 owner 如实声明缺项 | 全 `expected`——如实声明的缺组是合法部分结果 |
| `injected-modelled-run-states.jsonl` | 临时公开响应：36 题释放 + **建模**的逐题回执（`IQS_01` 已观察；`PORTER_01/02` 内容过滤、`DUPONT_04/05` 截断、`IQS_22` 已结算未保存） | 全 `expected`；四态在 `coverage.questions[].status` 里 |
| `injected-complete-mixed.jsonl` | 临时公开响应：36/36 合法混尺度结果（合法对照） | 全 `expected` |

`injected-modelled-run-states` 是**建模**样本，不是抓取：交付最终把 36 题全部
绑定为观察，公开快照从未长成这样。它只用于证明四态能被区分，来源写在
`tests/fixtures/company_coverage/build_fixtures.py` 的 `_modelled_run_state()`。

复现命令（工作目录为本仓根，`<python>` 需带 `yaml`）：

```bash
# 真实读
python -B -X utf8 scripts/company_result_feedback.py \
  --stockwiki-root <StockWiki checkout> \
  --workspace-root runs/r25-live/owner-workspace \
  --stockwiki-python <python> \
  --entity ENT_99deceb6-f58a-48b1-bd6b-437621015d76 \
  --out real-read-absent.jsonl --run-id manifest-delivery-01 --attempt-id read-absent-2

# 临时公开响应（可加 --receipts）
python -B -X utf8 scripts/company_result_feedback.py \
  --inject-result tests/fixtures/company_coverage/result-partial-claiming-complete.json \
  --out injected-partial-claiming-complete.jsonl \
  --run-id manifest-delivery-01 --attempt-id injected-partial-claiming-complete
```

真实读一次是 1 次 StockWiki 公开命令子进程、0 次模型调用、0 次注册/发布/导入；
`--inject-result` 不读也不写 owner，只把已保存快照放到 owner 读本该返回的位置。
