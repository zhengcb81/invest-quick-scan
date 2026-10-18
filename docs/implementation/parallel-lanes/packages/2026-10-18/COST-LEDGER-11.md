# COST-LEDGER-11｜只读预算/成本/未决费用审计

唯一工作根 **C:/Users/郑曾波/Projects/iqs-cost-ledger-lab**（编制时不存在）；分支 `codex/cost-ledger-11`；module `iqs_cost_ledger`。目标存在且非空时按 `writer_conflict` 处理，不覆盖。

先读[本批共同规范](handoff-rules.md)、[输入锁](inputs.lock.json)、[共同契约](../2026-10-18-mainline-support/integration-contract.md)、费用契约 [../../contracts/providers-and-budget.md](../../../contracts/providers-and-budget.md)。

## 目标与真实边界

费用契约已冻结语义：发送前原子预留、结果未知保留预约且不得记零、`max_cost`/`max_requests` 跨 run 硬上限、`reset_on_restart=false`、comparison 有独立子预算、结果以实际回报型号为准、缺用量是 unknown 而不是 0（`providers-and-budget.md` 第 44–56 行）。但"某份导出账本到底自洽吗"没有可执行检查：多少钱 reserved、多少 settled、几笔 `response_unpriced`/`outcome_uncertain`、有没有 attempt 只 finished 不 reserved、费率卡重算与声明估值差多少、按 policy/route 归因后分母是否守恒。

本包交付**只读审计器**：吃一份声明式导出的账本投影（JSON/JSONL 转换后的闭合 JSON），产出可复算的费用与状态报告。不领预算、不结算、不发送、不查单、不连真实 DB、不算现金账单。

明确不做：不代替 StockQA 账本与预算协调器；不判定 provider 是否真扣费；不把费率卡估值当发票；不做故障注入（属 RESUME-CHAOS-06）；不改政策版本、不释放预约、不清未知费用。

## 为什么可独立、不与在跑工作重叠

- 已派发三包处理 release 差异、摘要保真、关系观察，**都不涉及费用账本**。
- 与 RESUME-CHAOS-06 的区别：那是用真实 StockQA 依赖做发送/预约/超时故障注入；本包不跑任何执行器，只对**已导出**的行做算术与守恒核对，且不主张运行时语义。
- 与主线 publication 节点无交集：不读 owner 库、不碰预算协调器、不改 `current.json` 或任何策略。
- 输入是本仓已 tracked 的导出 JSON/JSONL，可离线单独完成；未来真实导出由总控补冻（见下一节占位）。

## 精确写范围

本 Lab 内：`README.md`、`.gitignore`、`pyproject.toml`、`src/iqs_cost_ledger/`、`schemas/`、`content/`、`fixtures/`、`tests/`、`tools/`、`.tmp/`、`docs/handoff/COST-LEDGER-11/`。

## 冻结输入

来自本仓 Git 对象（source_commit `4e001cd18d229a60de54d56ce6ecd23f8bc00cae`），`git cat-file blob <oid>` 读取后复制到 `vendor/iqs/`；`inputs.lock.json` 用 `iqs.support_input_lock/1.0.0`。

| path | blob OID | bytes | sha256 |
|---|---|---:|---|
| docs/implementation/experiments/accuracy-pricing-2026-10-07.json | 43648ed11f3b65dcd6b13d8f87e2711d7e2dfb36 | 2651 | 403b5b9e71588f7bbaf46df4408317e623a67e9148bd2ebbb1d299f80dd5be8c |
| docs/implementation/experiments/accuracy-first-economics-2026-10-07.json | a9a7b839f73b1bbc2d434303c394075018175c45 | 1069 | 9ab7dc66cde0ae17d72b57b5ebf8641bb2af465da63f7b53a4c597dfb5ef9d61 |
| docs/implementation/experiments/artifacts/accuracy-first-2026-10-07/main/budget.json | a0276357e3f317f2b9fa029371733cd4349ed6fc | 78 | fb790886a85349db20476bec6e9949d10be96e734eeeefb79202cc00ebe9431b |
| docs/implementation/experiments/artifacts/accuracy-first-2026-10-07/followup/budget.json | bacff8af8032f05618907f0640d92f8eb968d496 | 84 | dbb8b4d14bf0c32c7a403a5f512107f4010a39392e08c7a1dfb0421219c87b81 |
| docs/implementation/experiments/artifacts/company-agent-s0-2026-10-15/original-attempt-cost-reconciliation.json | 6f3da8705a270aa45fd9d7003d2e61e44c435b97 | 353 | c209af2f8812a72b12ee664b7554835d84a8dfee628ed89e94fc4f30c6a94395 |
| docs/implementation/experiments/artifacts/company-agent-s0-2026-10-15/mimo/ledger-summary.json | 5d2cf8cab204f7ab4d2f67b1361dfef327652617 | 229 | eca00f345500f01c44140ce9aebd2772d02ae943b0595a9ee01f4c0d480dad68 |
| docs/implementation/experiments/artifacts/b01-improved-2026-10-07/ledger.jsonl | b9c67cf7f8a75b495f438be9c83252deb17ec2e9 | 772983 | 7d1e68bbabf53dec32aa2d28abe7c4b3e1dbf200c4b048b570b22d2f0108cc3a |
| docs/implementation/experiments/artifacts/mimo-pro-pilot-2026-10-07-01/ledger.jsonl | c408e11f21d44a688facd165e2488945903e1582 | 259642 | b071099b22236006be9119704002697d4bb8975de0113ff2a19caac2817fd85f |
| docs/implementation/contracts/providers-and-budget.md | 252edb3c6526569f720ace808eb67962fb9732e0 | 10532 | 0a9df0e877a4609496fe2db228203fe22001d4b54f39210af19c028c2a294747 |

**总控补冻占位（本卡不得自行制造）**：`docs/handoff/COST-LEDGER-11-ledger-projection.json`——主线 saved-research publication / schema24→25 节点的真实预算导出（含 `response_unpriced`、`outcome_uncertain`、`reserved_in_flight` 行与 policy_version）。当前不存在应以 tracked 形式存在的该导出；总控有记录后补冻并给 blob OID。**不得以真实 DB 路径替代**，也不得用 `runs/` 下未 tracked 副本冒充。

## 交付物

1. `schemas/ledger-projection-1.0.0.schema.json`（输入，闭合）：`protocol=iqs.cost_ledger_projection/1.0.0`、`projection_id`、`created_at_utc`、`source_note`、`ratecard_ref`(ArtifactRef)、`policy_refs[]`、`attempts[]`。
2. `schemas/cost-ledger-report-1.0.0.schema.json`（输出）。
3. 审计引擎：整数 micros 十进制运算、分类状态机、守恒校验、费率卡重算、归因。
4. `content/casebook.json`（≥24 例，expected 分离）、`fixtures/`（合成投影 + 两个真实 ledger 的转换适配器输出）、`rules/cost-rules.json`（每条 rule_id 绑定 `providers-and-budget.md` 具体行或字段）。
5. CLI、测试、`integration-map.md`、交接文件集。

`attempts[]` 每行闭合：`attempt_id, policy_version, route, model_requested, model_actual|null, kind(reserved|settled|response_unpriced|outcome_uncertain|reserved_in_flight|released), reserved_micros(int), settled_micros(int|null), invoice_micros(int|null), usage{uncached_input_tokens|null,cached_input_tokens|null,output_tokens|null,thinking_tokens|null,requests:int}, observed_at_utc, http_status|null`。`null` 只能表示"导出里没有"，不得用 0 填充。

## 公开接口与输出协议

```powershell
python -B -X utf8 -m iqs_cost_ledger audit --input content/projections/p-01.json --input-root fixtures --source-root vendor/iqs --lock inputs.lock.json --output .tmp/cost-01
python -B -X utf8 -m iqs_cost_ledger convert --ledger vendor/iqs/ledger.jsonl --summary vendor/iqs/ledger-summary.json --budget vendor/iqs/budget.json --ratecard vendor/iqs/pricing.json --output .tmp/proj-01
python -B -X utf8 -m iqs_cost_ledger validate --input ... --lock ...
python -B -X utf8 -m iqs_cost_ledger evaluate --cases content/casebook.json --input-root fixtures --source-root vendor/iqs --lock inputs.lock.json --output .tmp/eval-01
```

报告 `iqs.cost_ledger_report/1.0.0` 顶层用共同字段；payload 闭合：`projection_sha256,ratecard_sha256,policy_refs,attempts_total,classification_counts,findings,conservation,totals,attribution,limitations`。

- `findings` 每项 `finding_id,rule_id,attempt_id|null,severity,reason_code,observed,expected,evidence_pointer`。`reason_code` 固定枚举至少含：`finished_without_reservation`、`duplicate_reservation`、`duplicate_terminal`、`reservation_leaked`、`unpriced_not_counted`、`uncertain_forced_zero`、`ratecard_gap`、`usage_unknown_not_zero`、`invoice_mislabeled_as_estimate`、`cap_exceeded`、`policy_missing`。
- `conservation`：`attempts_total = settled + response_unpriced + outcome_uncertain + reserved_in_flight + released` 且各类互斥；任一不等即 `findings` 报 `denominator_not_conserved` 并保留原数。
- `totals`：`reserved_micros, settled_micros, estimated_micros, invoice_micros|null, unpriced_count, uncertain_count, reserved_in_flight_count`。`estimated_micros` 与 `invoice_micros` **不得相加**、不得互相替代；无发票时 `invoice_micros=null`。
- `attribution`：按 `policy_version` 与 `route` 各一组，每组含行数与 micros 分项，且分组和回到 `attempts_total`。
- `limitations` 固定含 `invoice_verified=false`、`ratecard_is_published_estimate_not_invoice=true`、`runtime_semantics_not_asserted=true`。

费率卡重算规则：`per_1m_tokens` 单价 → micros 用整数运算 `round_half_up(tokens * unit_micros / 1_000_000)`，并在报告中同时给未取整值；`cached_input` 与 `uncached_input`、`output` 分开；thinking 计入 output 若导出声明如此，否则标 unknown；deepseek peak/off-peak 与 minimax 折扣/套餐只作参考列，`package_note` 明确不得当现金。币种不混算，USD/CNY 各自列出。

退出码：0=审计完成（发现缺口是成功诊断）；2=输入/schema/重复键/哈希漂移；3=输出已存在或越界；4=分类/守恒内部不闭合；5=用法；6=网络或凭据访问尝试；1=意外失败并留错。

## 确定性离线验收

| Case | 必须证明 |
|---|---|
| CO-01 | 两个真实 ledger 转换后：`b01` 导出实测 456 reserved / 458 finished / 458 distinct attempt_id，工具必须报 ≥2 条 `finished_without_reservation` 且分母仍为 458，不得删行凑平 |
| CO-02 | `mimo` 导出 150 reserved / 156 finished：同一规则复现，证明不是硬编码单例 |
| CO-03 | `ledger-summary.json` 的 `physical_response_rows=budget_attempts=counted_requests=terminal_rows=6`、`in_flight=0` 与投影一致；不一致即 finding |
| CO-04 | `rounded_ratecard_usd=0.0034` 与 `unrounded=0.003397320` 同时保留；`cash_invoice_usd=null` 必须输出 `invoice_micros=null` 而非 0 |
| CO-05 | `original-attempt-cost-reconciliation.json`：`budget_status=settled`、`ratecard_estimate_usd="0.000464"`、`invoice_cash_usd=null` 被正确分类，且估值与发票列分离 |
| CO-06 | 费率卡重算：给定 usage 与 `accuracy-pricing-2026-10-07.json`，重算值与声明估值差 1 micros 即 `ratecard_gap`；差 0 不报 |
| CO-07 | 缺 `cached_input_tokens`/`output_tokens` 的行必须是 `response_unpriced`+`usage_unknown_not_zero`，不得按 0 计费 |
| CO-08 | `outcome_uncertain` 行保留 `reserved_micros`，不得出现 `uncertain_forced_zero` 之外的静默归零；静默归零必报 |
| CO-09 | 同一 attempt 两条 `finished` → `duplicate_terminal`；两条 `reserved` → `duplicate_reservation`；跨 policy 同名 attempt 不合并 |
| CO-10 | 预算上限：模型/搜索请求数与现金上限（`main` 120/60/25、`followup` 72/36/23.368035）被 `cap_exceeded` 检查；分类与归因不改变原值 |
| CO-11 | per-policy / per-route 归因分组和回到 `attempts_total`；缺 `policy_version` 单独成组并报 `policy_missing` |
| CO-12 | 负例：重复 JSON 键、NaN、布尔冒充数字、未知 protocol、输入 hash 篡改 → exit2 且无输出；越界/已存在 → exit3 |
| CO-13 | 同一投影两次新根运行 payload 字节相同；零网络、零子进程外呼、临时根成功与失败都清理 |
| CO-14 | 真实 `accuracy-first-economics`（`invoice_verified=false`、`unknown_cache_usage_requests`、`formula_per_1m`）复算与原件一致，且报告写 `invoice_verified=false` |

≥24 个单测场景覆盖上述风险；集成用两个真实 ledger 与两个真实摘要/预算文件；E2E 从公开 CLI 读文件到新结果，再用 `validate` 读回，含随机 cwd 与中文空格路径。工具不得读 `fixtures/expected/`。

## 禁止捷径

不得伪造回执、发票、结算或通过数；不得把费率卡估值写成现金账单；不得把 unknown/未计价写成 0 或"已结清"；不得跳过 hooks 或 `--no-verify`；不得读真实 DB/密钥/环境凭据；不得复制真实 namespace 或答案正文；不得写生产库/名单/预算/政策；不得碰他人 Lab；不得 `git add -A`；不得联网或付费补用量。

## 独立审查要求

按[共同契约 §5](../2026-10-18-mainline-support/integration-contract.md)：真正不同的独立 reviewer 全量核规则与 `providers-and-budget.md` 的对应关系、整数 micros 与取整、守恒分母、发票/估值分离、真实 ledger 复现，并**自带 2 个作者未给的反例**（如一条 `reserved_in_flight` 无终态、一条 usage 部分缺失）。`docs/handoff/COST-LEDGER-11/review/` 必含 `invocation-evidence.json`、`round-XX.*`、`fixes.json`、`final.json`（`verdict=passed`、`open_findings=[]`、`reviewed_commit`）；未通过不得交接。

## 交回

本仓 `docs/handoff/COST-LEDGER-11/`：标准八件 + `rules/cost-rules.json`、`report.md`、`tests.json`、`cleanup.json`、`inventory.json`、`review/`。先 payload commit，再 metadata-only commit。

## 风险与已知未知

- **真实导出不足**：现有 tracked ledger 只有 `reserved/finished/budget_revision`，没有 usage/model 字段，因此 CO-01/CO-02 只能证明"预约缺口可检出"，不能证明真实 `response_unpriced`/`outcome_uncertain` 分类；这需要总控补冻投影（已在输入锁占位）。实施者不得自行合成"真实"未决行冒充。
- **取整口径**：`round_half_up` 与 provider 真实计费可能不同；报告只称参考估算，`invoice_verified=false` 不可放松。
- **未知**：`b01`/`mimo` 两个 ledger 中 `budget_revision` 行的完整字段未逐字核对；真实 projection 的 `policy_version` 命名空间未定，实施时按实际导出登记，不猜。
