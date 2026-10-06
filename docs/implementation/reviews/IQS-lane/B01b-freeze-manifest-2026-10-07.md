# B01-b 冻结 manifest + 成本声明（记录式 — owner round-86 已放行）

日期：2026-10-07。性质：live 执行前冻结记录（BENCH-01 step1 的 manifest 要求）。owner 已于 round-86 放行（「给你放行」）——本档为**跑前落档**，不再等待二次确认；任何本档字段在首请求发出后不得更改（变更=作废本轮、新 run id 重冻）。

## 1. 样本冻结（BENCH-01 given.sample，A/H/美各 1 家，owner round-81 决定）

| 市场 | entity_id | 名称 | 身份态 | identity_snapshot（冻结输入） |
|---|---|---|---|---|
| US | `ENT_97bf6a65-a9e6-43f0-8409-c5695e2f6e1e` | Alphabet Inc. | verified rev1 | `alphabet_snapshot.json` 8690B **`a4c6eeef2b132ca9…`** |
| CN-A | `ENT_99ebb735-f072-41e4-8545-823bc012614f` | 宁德时代（300750/XSHE） | provisional rev2 | `catl_snapshot.json` 2977B **`9960b7e0a682f19f…`** |
| HK | `ENT_1af6804e-40c1-4c35-b190-ea691dba2c85` | 中信建投 H（06066/XHKG） | provisional rev2 | `cncb_h_snapshot.json` 2948B **`4d30c311296161cd…`** |

快照目录：`StockQAbyLLM/pilot_runs/b01_prereq_2026-10-07/`（已入库 `c282c80`）。样本不进大股票池（`不导入或改变大股票池`——三实体为隔离样本，B01 结束后不自动入池）。

## 2. 题面与规则冻结（BENCH-01 given.fixed_inputs）

- **30 道评分题/公司**：程序=冻结题库 `L02-freeze-2026-10-04.json` 的 `question_sets`（mechanism=`IQS select_questions(make_manifest) per frozen profile`、cycle_position=trough）→ 执行期为三样本各生成一个 per-company 文件（keyed by profile_key）并记录 SHA-256；**首请求前完成，冻结后不改**。
- **冻结对象（哈希一并记录于执行回执）**：题目文本/题面 prompt 模板、评分尺 rubric、身份 revision（见 §1）、信息截止时间（as-of=**2026-10-07T00:00:00Z**，与快照一致）、provider/model revision（见 §4）、搜索配置（见 §3）、方法执行顺序（seed 见 §5）、答案 gold、盲评抽样 seed、预注册阈值（见 §6）、硬预算（见 §7）。

## 3. 检索器冻结（step2）

- 两路=**Brave Search API** 与 **Tavily**（owner round-86 已供键：BRAVE_API_KEY 31 字符 / TAVILY_API_KEY 41 字符，用户级 env，运行时注入、不落盘不入库）。
- 结果规整为带稳定 `source_id` 的短证据：**单 snippet ≤500 字符、单公司累计 ≤30,000 字符**；仅 URL/发布或检索时间/长度元数据落盘；原始 response 与完整网页/财报**不落盘**（run 专属临时工件，G3 复核后按 manifest 清理）。
- 证据作为**不可信 context** 随题发送，逐 claim 引用 source_id。

## 4. 模型与两阶段冻结（step4）

- **第一阶段**（全部请求粒度）：**MiniMax-M3**（当前可验证套餐/计费模式；键=MINIMAX_API_KEY 用户级）。
- **第二阶段**（逐题基线 + 第一阶段过门槛的候选打包）：**MiniMax-M3 / mimo-v2.6-flash / deepseek-flash** 各跑独立匹配区组——provider 与 model revision 固定于 `llm_apis.json` 的 run-dir 冻结副本（与 L02 同法），区组内同输入同配置。
- 拒绝/不支持=保留为失败，**不换模型补齐**；失败不在同配对组静默换模型（换模型=用户顺位触发时另开匹配组）。

## 5. 随机化与盲评（step1/step7）

- 方法执行顺序随机化 seed = **20261007**（manifest 记录；配对顺序随机化同源）。
- 盲评抽样 seed = **20261008**；非关键 claim 分层抽样按 case 原文（每公司×方法 max(10题,每入选模块2题)；跨三公司每方法 ≥30 条，不足=inconclusive）。
- gold：解盲前由**两名独立评审者**基于冻结 rubric/来源建立、分歧裁决记录（评审身份在执行回执登记；本档只定规则与 seed）。

## 6. 预注册阈值（step7 — case 原文口径）

- 唯一题目 ID/schema 覆盖 **100%**；gold 可评分题有效分覆盖 **≥95%**（gold unknown 不强填）；
- 抽样非关键事实 source support **≥90%**；critical claims 逐条复核零未解决重大错误；
- 与裁决 gold 比 **MAE ≤0.75** 且 **≥90% 在 ±1**；相对逐题顺序基线 **MAE 差 ≤0.25、source support 降 ≤5pp、可评分覆盖降 ≤5pp**；
- 三家公司单轮只报原始值/中位数/范围（**不报 run 级 p90/显著性**；≥20 个同口径完整 run 才报 p50/p90）。

## 7. 硬预算冻结（step1 budget — 运行前冻结，执行期不放宽）

| 项 | 上限 | 推导 |
|---|---|---|
| 模型请求（第一阶段，3家×30题×6 方法=540 实答 + 修复预算 1.05×） | **primary_request_cap=800**、http 尝试天花板（含重试）**1200** | L02 同法（一次一题+repair_budget=1、5% 修复余量）+ 30% headroom |
| 模型请求（第二阶段区组：基线+候选 ×3 模型 ×30×3） | 第二区组另设 **800/1200**（与一阶段分账） | 同上推导 |
| 检索请求（Brave+Tavily；检索器对照 2×30=60 题次 + 冷缓存与失效子实验重跑） | **search_request_cap=500** | 对照60 + 三个缓存子实验各 ≤120 + 溢出 100 |
| 时间 | 第一/第二阶段各 **≤3h 墙钟**（Q09 deadline 门执行） | 分窗止损 |
| 费用/套餐 | MiniMax **套餐 quota 单列**（窗口消耗+拒绝记录，不虚构单价）；额外现金支出 **≤ USD 25**；Brave/Tavily 记实际 credits 与账单（执行日官方价格快照随回执） | BUD-04：不给虚构精确费用 |
| 止损 | 任一 cap 触达=停新派发（已运行回执继续结算——Q09 语义）；失败尝试逐项对账、不因结果删样本 | LIVE-04 同口径 |

## 8. 执行入口与隔离

- 执行入口=StockQA 公共 `main_with_llm --require-search`（Q06/Q09/Q10 已验证链 + `--identity-snapshot` §1 快照 + B01-a `--spend-authorization` 本档 §7 即授权快照来源：hard_cap=25USD、pricing_snapshot_ref=本档）。
- 所有答案/ACK 落 run 专属临时库与工件；snippet 快照暂存至 G3 复核后按 manifest 清理；执行前后正式名单/配置/DB/工作树无漂移（BENCH-02 语义）。

## 9. 未决与限制（诚实边界）

- 盲评 gold 的两名评审身份与裁决流程在执行回执首段登记（本档定规则不定人）。
- 30 题文件的 SHA 于冻结生成时记录（生成=首请求前的独立步骤，回执携带）。
- MiniMax-M3 套餐的当日 quota 状态在执行开始时读取并记档（不可用=按 BENCH-02 口径 blocked）。
