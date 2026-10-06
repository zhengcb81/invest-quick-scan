# Q10 施工卡（写前报告 — owner 通授 2026-10-03 覆盖本批；纯离线无 live 成本）

日期：2026-10-06。任务卡 Q10「实现结果 outbox 与投递回执消费」，deps 全满足（Q07✓ Q09✓ C06✓）。
case：JOB-07 / JOB-08 / DB-07 / LLM-08（owner=Q05）/ PAR-10；不变量：I01 / I12。

## 只读勘察结论（本轮完成，全部实证）
- **store 侧 Q10 API 全部已建、零调用**：`mark_result_delivery_blocked`（durable block ✓ step1/DB-07）、`prepare_result_delivery`（封存 C06：result_ready+checkpoint 前置、`validate_exchange_package`+`validate_checkpoint_binding` 双校验、**封存后不可变**（同字节幂等/异字节冲突）、blocked→ready 通路 ✓）、`begin_result_delivery`（send-intent）、`confirm_result_delivery_not_sent`（证明未发出才重臂 ✓ step3）、`apply_result_delivery_ack`（精确 ACK/幂等 ✓ step4）、`list_result_ready_without_delivery`/`get_result_delivery`/`list_result_delivery_events`；outbox 模块 `quick_scan_result_outbox.py`（C06 信封全量校验 L116-217、**checkpoint 绑定校验 L221-305**、ACK 校验 L307-、delivery_key）。
- **C06 绑定契约（适配器的字段映射依据，全部实证）**：observation 需 identity/question（=work 字段）、answer{question_id、response_kind="score"、score=saved.score、summary=saved.description、status∈{scored,insufficient_evidence,not_applicable}（**unknown 不可打包**）、evidence[]（url ⊆ provenance.source_urls；scored 必须非空）}、execution 九字段（全出自 provenance：actual_provider/model_requested/actual_model/request_id/provider_attempt_id/search_status/search_receipt_id/provider_prompt_sha256/response_completed_at，**全非空字符串**）。envelope 层另有权威输入：producer{component_version,build_id}、consumer{StockWiki/quick_scan/最小版本}、created_at、required_capabilities（含 standard_observation_v1）、contract_versions（精确键集，answer_schema/question_catalog 为文本）——**这些不可从 checkpoint 推造 → 缺失即 block**（step1/DB-07 原文语义）。
- **内容寻址**：payload_sha256=canonical(observation)、item_id=itm_sha({observation_id,payload_sha256})、package_sha256=canonical(body 去双 id)、package_id=pkg_sha——适配器必须按同法构造。

## 设计
1. **C06 适配器（新增 `src/utils/quick_scan_c06_adapter.py`）**：`build_c06_package(checkpoint_payload, *, authority) -> dict`——从 checkpoint payload（answer/work/provenance）+ **authority 输入**（contract_versions、capabilities、producer version/build_id）确定性组装完整 C06 v1 包（内容寻址同法）；**权威字段缺失/答案 status=unknown/execution 字段缺 → 抛 `MissingC06Fields`（分类为 block）**——不推造任何 cohort/版本/cutoff/标准证据字段（step1 原文）。evidence 缺省=provenance.source_urls 的 url 条目（真实来源、不发明标题/引文；更丰富证据由调用方传入）。
2. **执行路径接线（llm_runner 或 adapter 调用方）**：Q07 检查点落定（result_ready）后尝试组装：成功→`prepare_result_delivery` 封存；`MissingC06Fields`/校验缺字段→`mark_result_delivery_blocked(reason)`（work 保持 result_ready、**不重问** ✓ DB-07）。StockWiki 不可用不影响（全离线本地 ✓ DB-07）。
3. **ACK 消费入口**：公共函数包装 `apply_result_delivery_ack`（内部 `validate_import_ack` 精确匹配 package/item/observation/payload+namespace/store；accepted/already_present→delivered；rejected/conflict→终态；重复幂等 ✓ store 已有）。
4. **投递恢复**：`begin_result_delivery`（send-intent）→结果不明保留；`confirm_result_delivery_not_sent`（仅证明未发出才重臂）；PAR-10=send-intent 不明+**假 ACK**（格式对但 hash 不匹配）→拒、保持不确定、不重 POST、不覆盖原观察。
5. **LLM-08（owner=Q05）**：本批引用其边界（`_FORBIDDEN_KEYS` 校验已在 outbox 模块=不落正文/凭据的结构化字段白名单）——不越权执行 Q05 本体。

## 本批执行的 case
- **JOB-07**：result_ready+封存后恢复——已证明未发送→同字节/同 key 重臂；结果不明→先精确 ACK/权威对账；全程 LLM 调用 0；ACK 前不 delivered；重复 ACK 幂等。
- **JOB-08**：错 item/hash 的 ACK、非法状态跳转 → 具名拒；原待办与回执保留。
- **DB-07**：无 StockWiki/缺权威字段 → durable block（reason 持久）、不猜补/不伪装/不重问、适配器可用后 blocked→ready→封存（store 已有该通路，测试贯通）。
- **PAR-10**：send-intent 不明+格式正确但 hash 不匹配的假 ACK → 拒+保持不确定+不自动重 POST+不第二次模型请求+不覆盖原观察。
- **LLM-08**（owner=Q05）：登记边界（outbox 白名单即其结构化字段约束的实现面），不执行 Q05 本体。

## 允许改动（I18 接入不重写）
1. **新增** `src/utils/quick_scan_c06_adapter.py` + `tests/unit/test_q10_delivery.py`
2. `src/runners/llm_runner.py` — 检查点落定后的组装/block 接线（最小）
3. `src/utils/quick_scan_work_store.py` — **仅限**实勘发现的最小缺口（当前勘察=零缺口；若改须具名+先测后改）
4. IQS：本卡、Phase 82、case 执行记录
5. **禁改**：`quick_scan_result_outbox.py`（C06 校验面=Q10 首段已验证产物）、delivery 状态机、Q06/Q07/Q09 已验证面、StockWiki 侧（ACK 消费方在 StockWiki 的对端不在本批）

## 门与证据
- StockQA：定向（Q10 新测 + Q06 15 + Q07 8 + Q09 8 + 回归）→ 全量（基线 897 口径，`-p no:base_url`）→ mypy/ruff/black(100)
- 独立审查两轮 → StockQA 隔离提交 → PWF 记档
- **无 live 成本**（全离线：临时库/假 ACK/不联网）

## 风险与边界
- scored 答案必须有 evidence：缺省 url-only 证据=真实来源绑定（不发明），更丰富证据字段属 StockWiki 侧语义，不由本批捏造。
- unknown 状态检查点不可打包（绑定校验拒）→ 适配器分类为 block（非 error）——与 step1「不再次调用模型」一致。
- 封存不可变：同字节重入幂等返回；跨字节拒绝（防替换/防重放）——JOB-07/DB-07 测试各钉一条。
