# THREE-MARKET-FORMAL-RESULTS-20261121 交回报告

对应 [施工卡](C:/Users/郑曾波/Projects/investment-dashboard/handoffs/owner-requests/invest-quick-scan/THREE-MARKET-FORMAL-RESULTS-20261121.md)（E07/B-04）。IQS 主责结果登记及回跳协议。

**发布 SHA：** IQS 正式服务 `master@296ab84`（8766 快照实例，只读验收面）；操作面为主树临时实例 8767（同一 `config/dashboard.local.json`，revision `10db0cf9…33f0e`；快照实例的 REPO_ROOT 是 `.runtime/iqs-e20-296ab84/`，不含主仓 `runs/`，prepare 在其上被具名拒绝——preparation_not_configured，属快照实例的既定限制而非缺陷）。工作树：IQS 主树、StockQAbyLLM、StockWiki `e8da004+`。本轮代码整改全部在工作树（未提交——StockQA 树内含并行会话 WIP，不混提），清单见根因章节。

## 覆盖总表

| 公司 | 业务工作区实体/挂牌 | IQS r25 实体 | 正式结果 | 观测 | 缺题/具名 | 历史 |
|---|---|---|---|---|---|---|
| 药明 603259 | `ENT_2a41e04d` / `LST_f26e4cea` | `ENT_3ac097b9` / `LST_80ed7414` | **`cas_328435ea4e16928fe203`**（formal，cutoff 2026-11-21，registry seq 3） | 26/36 published | 10 题具名缺失（DUPONT_01/02/03/06/07、IQS_09/10/21/23/24，含 4 题决议具名 failed） | 1 |
| 领先 09988（阿里） | 同实体 `ENT_e4d964f0` / `LST_591474dd` | 同左 | **未登记——`refresh_member_not_scan_enabled`**（universe `UNI_IQS_APPROVED_214_20261025` 非成员；上张卡明确将 membership request 划出范围，本轮不动共享 universe） | 0 | 身份凭据完备（verified rev2），缺 scan-enabled 成员资格这一登记前置 | 0 |
| MongoDB MDB | `ENT_41250504` / `LST_2d86780f` | `ENT_b47ecd1e` / `LST_50d01c61` | **`cas_540ed63741e688f7e5ac`**（formal，cutoff 2026-11-21，registry seq 2） | 33/36 published | 3 题具名缺失（IQS_01/02 导入拒绝=模型答案 schema 越界；IQS_24 invalid_question） | 1 |
| 中微（对照） | `ENT_99deceb6` / `LST_4b1d9b36` | 同左 | `cas_6cab1b94d8f45d42c750`（未动） | 37→47（并行会话交付 +10） | — | 1 |

注：阿里无新实体（与业务端同 ID）；**总分均为空**（`company_aggregate_authority_missing`）——按卡"总分缺权威时继续为空"。逐题质量如实投影（scored / insufficient_evidence / provisional / evidence_limited 计数见验收读回）。

## 施工记录（复用/补跑/待材料）

- **复用**：无既有可登记原生结果（三家 r25 均 0 结果/0 历史/无主体/无绑定）。两家补跑即为本卡施工。
- **药明**：全链补跑。bootstrap standalone_issuer 主体 `ASJ_11acfd11`（perimeter receipt verified）→ prepare（entity 33 + security 3 两包）→ 真实扫描 → 中途撞墙（见根因）→ 决议解卡 → 重扫收官 → 交付 26 观测入库 → 登记。
- **MongoDB**：全链补跑，一次通过：主体引导 → prepare（33+3）→ 35 题真实回答（34 评分 + IQS_24 invalid_question 终态）→ 交付 33 入库（IQS_01/02 交付包被 owner 冻结契约具名拒绝 `vendor_observation_invalid`）→ 登记。
- **阿里**：prepare 在 refresh owner 预览被成员门拒（`refresh_member_not_scan_enabled`），保留具名状态；membership request 是 StockWiki 权威流程，属共享 universe 变更，需 owner 单独决策，本卡未动。
- **药明旧草稿**：`runs/thin-scan-wuxi-2026-10-18` 原样未动（draft:true / verified:false / 24 题，字节级未触碰），具名保留原导出入口与缺原生观测/发布绑定的原因（旧格式无 release/观测绑定，不可经原生链发布；读回方式为同目录静态导出）。阿里与 MongoDB 无草稿（0 条），本次交付即其真实草稿状态。
- **中微对照不动**：正式结果/历史/观测读数与登记时一致；并行会话的 AMEC 重打分交付 +10 条观测不影响其正式结果。

## 根因与整改（用户指令：从根上修、简化门禁；判定=过度门禁）

### 死锁链（全部实证）

1. 模型响应缺可验证搜索回执（`search_unverified`——模型瞬态行为，非系统故障）→ 题包 stage 级失败。
2. 旧代码三处词表/门禁缺陷叠加：
   a. `after_question_failed` 终态白名单缺 stage 原因 → `release_unsent` 拒绝释放已付费题 → item 永久 `leased`；
   b. 级联封锁：一个悬置包阻断同 run 后续所有题包，run 退出后过期租约无清扫器；
   c. IQS precheck 对 `leased/uncertain` 一刀切拒绝启动，不区分活租约（真在途付费工作）与过期残留（可安全回收），而执行器启动自带的 `recover_expired` 本可安全回收——**门把唯一能开锁的钥匙挡在门外**，死锁闭环。
3. 决议链（唯一合法钥匙）当时不可达：决议原因词表（粗类）与 stage 原因不匹配，且部署内无可复用驱动。

### 判定与处置

- **必要门禁（保留）**：租约+TTL（双扣费互斥）、账本原子认领、决议权威、冻结契约导入校验。
- **过度门禁（已修）**：
  - **A. stage 具名失败不落终态 + 级联封锁**（StockQA `qa_engine.py`：具名 stage 失败填 member_failures、清级联继续派发；未识别 stage 仍保守阻塞）——
  - **B. 终态词表缺类**（`llm_runner.py` + `quick_scan_work_store.py`：三个具名传输级原因进 `received_without_answer` 白名单；`known_outcome_journal` 粗类映射同步）；
  - **C. precheck 租约语义**（IQS `dashboard_execution.py`：仅 `uncertain` 与**未过期** leased 阻塞；无到期时间的 leased 保守按活；StockQA projection/inspect DTO 增带 `lease_expires_at`）。
- **保留未动（如实记录，属后续卡）**：owner 导入契约与执行器封存校验的**不对称**——MongoDB IQS_01/02 模型答案 `metrics[0].unit_detail` 写了 130 字符（schema 上限 80），执行器侧校验放行封存、owner 导入侧具名拒绝。对齐两侧是正确修法，但涉及冻结契约，本轮不动。
- **未动**：卡面明示保留的旧草稿、共享 universe（阿里成员门）、中微对照数据、并行会话 WIP（不混提）。

### 解卡实录（全公开 CLI，无手写库；回执 wd/ 目录全套）

三道卡题（药明 IQS_09/10 entity、IQS_23 security）：intent（粗类 `known_response_no_accepted_answer`，证据工件=原响应字节）→ `work_decision_inspect_cli --intent` 从账本推导物理证明 → StockWiki owner CLI `--work-decision-request` preview（单题 permission_request：`subject_refs=[ref]`、`[field_id]`、cutoff 对齐）→ work delegation install（每授权绑定单 preview，agent/authorization 沿用现役部署凭据）→ `--confirm-work-decision-delegated`（--idempotency-key 对齐 action_id）→ `quick_scan_work_decision_apply_cli` → **owd1_ 决议 ×3 落账**。preview 15 分钟 TTL 与幂等键冲突均按公开规则处理（重推导、v2/v3 键）。

## 验收（2026-11-21 晚，正式 8766 服务实读）

**结果+历史双读**（`GET /api/product/company/result?id=…` + `GET /api/product/company/history?id=…`，回执 [acceptance-reads.json](evidence/acceptance-reads.json)）：

- **药明**：`cas_328435ea4e16928fe203` formal，26 scored，10 缺题具名，总分空（authority missing），历史 1 同一 result_id ✓
- **MongoDB**：`cas_540ed63741e688f7e5ac` formal，31 scored + 2 insufficient_evidence，3 缺题具名，总分空，历史 1 同一 result_id ✓
- **阿里**：`company_result_not_registered` 具名可见 ✓（成员门）
- **中微对照**：`cas_6cab1b94d8f45d42c750` 不变 ✓

**卡面规格双读补充核验**（对照回执同文件）：

- 带 `&result_id=<固定正式结果>` 参数的 result 读：两家均 200 且返回**同一**固定 formal 结果 ✓
- history 读含**同一**固定 result_id（status=formal）✓ —— "两次读取都能找到同一固定正式结果" ✓
- 原生尺度组：两家投影 `lineage_groups`=6、`scale_versions=['1.0.0','2.0.0']`、`lineage_provenance_sha256` 在载 ✓
- 原观测引用：`observation_refs` 26/33 条在载 ✓；期间 `information_cutoff=2026-11-21` ✓
- **适用挂牌/公司级范围声明**：registry `listing_id=None`（公司级登记，观测跨 entity+security scope——药明 25+1、MongoDB 31+2；中微先例同形态）。范围声明以三重实证交付：①观测库逐条 scope 分布（上数）；②Dashboard 侧 `workspace_listing_resolved`（跨 ID 挂牌解析成功）；③正式读回的 `analysis_subject` 主体绑定。公司级声明如实成立，无挂牌级误标。
- **固定深链浏览器实读**（IAB 实读，非仅 API）：药明详情页渲染"已存评分与事实记录（26）"，逐题证据/coverage/置信度/暂定评分标记完整；MongoDB 详情页渲染"（33）"；`#/results` 生产结果库列表中两家正式结果可见（最新观测 2026-11-21T18:18Z）。
- **草稿显示真实状态**：工作台草稿段显示 `unavailable`（具名警告"历史薄草稿源尚未明确选择；未将缺少的历史数据表示为零"）——UI 草稿源自始未接线（既有条件），药明草稿本体以静态导出原样留盘、未被混入正式/历史读回（formal/history 读回已验证无草稿行）✓

**Dashboard 组合栈适配读**（真实 adapter 栈 + TestClient，只读；[combo-probe-formal.json](evidence/combo-probe-formal.json)，脚本 [combo-probe-formal.py](evidence/combo-probe-formal.py)）：

- 药明/MongoDB：经**原业务挂牌**（ENT_2a41e04d/LST_f26e4cea、ENT_41250504/LST_2d86780f）读到各自 formal 结果，history 1，`link_status=available`、return_to 可用，`workspace_listing_resolved`（跨 ID 解析成功）✓
- 阿里：`G-IQS-02_company_result_not_registered` 具名保留 ✓
- 中微对照：不变 ✓

**运行凭据**：

- 药明首条原观测：`obs_28866824b9e052fb…`（IQS_01）；MongoDB 首条：`obs_21e791e44fe8f33c…`（IQS_22）。固定结果与首条观测的对应挂牌/发布凭据即上文覆盖总表；两家正式读回的 `iqs_link` 投影 `link_status=available`（return_to 白名单路由可用）。
- 预算：u25-live 账本终值 **$3.79 / $25（159 次请求）**——本轮三市场+并行 AMEC 重打分合计；药明+MongoDB 本卡部分约 $1.1。0 越权、0 手写库、0 未授权 universe 变更。
- 执行包/确认单：prepare_93bbd918（药明）与 prepare_720c098a（MongoDB）双 scope 确认单可重开（gen-2 确认单同样保留）；决议回执 owd1_×3（owd1_d5c91c45、owd1_4f0ad5d1、第一题 owd1_ 见 wd/apply-IQS_09-entity.json）。

## 证据索引

| 文件 | 内容 |
|---|---|
| [evidence/acceptance-reads.json](evidence/acceptance-reads.json) | 正式服务双读回执（含逐题质量计数） |
| [evidence/combo-probe-formal.json](evidence/combo-probe-formal.json) | Dashboard 组合栈四公司适配读回 |
| [evidence/combo-probe-formal.py](evidence/combo-probe-formal.py) | 组合栈探针脚本（只读可复跑） |
| [evidence/wuxi-gen2-delivery-jobs.json](evidence/wuxi-gen2-delivery-jobs.json) | 药明 gen-2 交付 job 引用 |
| `runs/r25-live/three-market-formal-20261121/` | 全过程工作目录：prepare 候选/交付 job/决议链回执（wd/）/监视日志/报告草稿 |
| `runs/r25-live/owner-workspace/runs/state/quick_scan_refresh/work_decisions/` | owner 侧决议 preview/confirmation/grant 存档 |
| `runs/u25-live/work.sqlite` | 预算账本（终值 $3.79/159 请求，无在途） |

## 剩余开口

1. **阿里**：需 owner 单独走 membership request 权威流程把 09988 纳入 `UNI_IQS_APPROVED_214_20261025`（或另立 universe），之后沿本报告同一链路补扫登记。关卡按卡对阿里保持开放，具名状态已可独立验收。
2. **药明 10 缺题 / MongoDB 3 缺题**：全部具名 failed/导入拒绝，证据工件在 wd/evidence/；重扫与重问路径已验证可重开（本轮 gen-2 实证）。搜索气候（模型搜索回执质量）好转后重问即可补齐覆盖。
3. **两侧校验不对称**（执行器封存 vs owner 导入契约）：`metrics[].unit_detail` 类 schema 越界应在封存前拦截——建议后续卡在执行器 checkpoint 校验中加入与 owner 导入契约同源的 schema 校验，避免"封存成功但导入拒绝"的浪费（本轮 2 题即此因）。
4. **代码整改提交**：两仓工作树改动清单见根因章节；因 StockQA 树含并行会话 WIP 未混提，待并行会话协调后按仓提交。
5. **正式 8766 快照服务**运行旧代码（只读面不受影响）；下次 owner 重启时自然载入根修后的代码。
