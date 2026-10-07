# B01-b Phase-1 方法对照实验报告（30 题分组策略 / 检索器对照 / 缓存口径）

日期：2026-10-07。执行者：IQS 总控。授权链：owner 2026-10-03 通授 + round-81 样本决定 + round-86 live 放行（「给你放行」）+ round-93 budget 加码 + round-93/94 设计纠偏指令（认真仔细/小规模预案/不要推理过程）。**本报告性质：phase-1 结果报告，G3 独立审查为下一步（未做，见 §8 交接）**。

## 1. 冻结输入（执行与冻结一致）

- 样本三司（A/H/美各 1，owner round-81 决定）：宁德时代 300750（CN/XSHE，provisional rev2）、中信建投 H 06066（HK/XHKG，provisional rev2）、Alphabet（US/XNAS，verified rev1）。identity_snapshot 四方一致（Get-FileHash==manifest§1==证据§2==load_identity_snapshot，三轮审查 approved）。
- 30 题：`b01b_questions_v1`（共享固定集，`questions_sha256=42f02417…`、文件 `045f3956…`，跨三公司跨方法同题——方法对照的同输入控制）。
- 证据：Brave/Tavily 双引擎 240 live 调用（0 错误）、每司合并池 ≤30000 字符、snippet≤500、source_id 稳定、原始响应不落盘。
- 生成设置（frozen）：MiniMax-M3、temperature=0、**thinking=disabled + reasoning_split=true**（owner round-94「只出结果」要求，官方参数）、1+1 格式修复（L02 政策）、max_completion_tokens=131072（官方推荐值；24000 曾致 finish=length 截断伪影——探针实证）。
- 硬预算实况：phase-1 全程（含无效与探针）≈**990 请求 / ≈6.5M prompt tokens**；配额中断一次（Token Plan 用量上限 429/2056，owner round-96 确认重置后续跑）。

## 2. 执行史（全程如实，含无效轮）

| 轮 | 请求 | 结果 | 判定 |
|---|---|---|---|
| run-1 | 329 | **无效**：catalog prompt 演示占位未替换（427/540 not_applicable）+ 模板尾契约冲突（40% 修复率）+ 7 键载入面（标的块 None） | 三缺陷审计定位，归档 `*_run1_invalid` |
| run-2 | ~16 | sequential 段停滞 22min → 探针根因 `finish=length`（推理烧光 2000 token） | kill，小规模预案（owner 指示） |
| 探针/参数 | ~6 | thinking-off 单探：finish=stop、17.2s、reasoning=0、content 直出 `[{` | 参数落地（thinking:disabled 官方文档） |
| smoke | 41 | scored 49/60（82%）、引用 92%、修复率 14%、failures 1 | 三停跑判据全绿 → 放行全量 |
| run-2b | 252 | CN-A 完整有效；01:05 起 HK/US 全 429（**Token Plan 用量上限 2056**） | 部分有效，归档 `*_run2b_partial` |
| run-3 | 283 | 全量 240 块+43 修复，零 429 | 保留 sequential/concurrent_4/group_3 |
| 大组重跑 | 32 | group_5/10/batch_30 @131072（24000 截断伪影探针实证后） | 零失败，合并入正式数据 |

## 3. 结果矩阵（合并 540 行 = 正式 phase-1 数据）

**总体**：scored 331（61.3%）、insufficient_evidence 88、missing_in_response 110、error 8、not_applicable 3（占位缺陷根除：run-1 为 427）。证据引用覆盖：合并口径约 88%（健康段 93-100%）。

| 公司×方法 | scored/30 | 均分 | 引用/30 | missing |
|---|---|---|---|---|
| CN-A sequential | 27 | 7.52 | 29 | 0 |
| CN-A concurrent_4 | 28 | 7.54 | 29 | 0 |
| CN-A group_3 | 28 | 7.54 | 28 | 2 |
| CN-A group_5 | 15 | 8.00 | 16 | 14 |
| CN-A group_10 | 12 | 7.42 | 12 | 18 |
| CN-A batch_30 | 30 | 7.20 | 30 | 0 |
| HK sequential | 16 | 6.25 | 29 | 0 |
| HK concurrent_4 | 12 | 5.92 | 30 | 0 |
| HK group_3 | 19 | 6.32 | 27 | 0 |
| HK group_5 | 15 | 6.33 | 26 | 4 |
| HK group_10 | 10 | 5.90 | 19 | 9 |
| HK batch_30 | 1 | 7.00 | 1 | 29 |
| US sequential | 19 | 7.05 | 28 | 0 |
| US concurrent_4 | 21 | 6.86 | 30 | 0 |
| US group_3 | 15 | 6.73 | 22 | 8 |
| US group_5 | 21 | 7.10 | 22 | 8 |
| US group_10 | 12 | 6.92 | 12 | 18 |
| US batch_30 | 30 | 7.27 | 30 | 0 |

**跨方法一致性**（同题≥2 方法 scored 的 ±1 一致率）：CN-A 80%（24/30）、HK 92%（22/24）、US 52%（15/29）；分差均值 1.13/0.71/1.69。

## 4. 对照预注册阈值（case 原文口径，逐条）

| 阈值 | 要求 | 实测 | 判定 |
|---|---|---|---|
| 唯一题目 ID/schema 覆盖 | 100% | 540/540 行、30 唯一题全覆盖 | ✅ |
| gold 可评分题有效分覆盖 | ≥95% | **61.3%**（331/540；大组段缺题+HK 证据不足偏高） | ❌ |
| 抽样非关键事实 source support | ≥90% | 引用率健康段 93-100%、合并 88%——**未做逐 claim 复核**（gold/盲评未执行） | ⚠️ 未评 |
| MAE≤0.75 / ±1≥90%（vs gold） | — | gold/盲评未执行（依赖≥95% 覆盖前提已失） | ⚠️ 不适用 |
| 相对逐题基线退化（MAE 差≤0.25 等） | — | 同上 | ⚠️ 不适用 |
| 缺失/重复/错题独立报告 | 必须 | **本报告 §3 即独立报告**（missing 逐行在 `method_results.json`） | ✅ |

## 5. 裁决（按预注册规则）

**inconclusive → 维持逐题顺序基线**。有效分覆盖 61.3% << 95% 门槛，任何打包方法不得进入胜出集或 Pareto 推荐；逐题基线（sequential/concurrent_4）在本批数据中覆盖与引用最稳（CN-A 27-28/30、US 19-21/30），维持为默认。**不宣称任何打包法的联合最优**（case step8 口径）。

## 6. 发现（供 L03/G3 使用）

1. **大包完整性是服务端非确定行为**：同参数重发 batch_30 可 30/30（诊断探针，`diag_batch30_hk.json` 落盘），运行时却出现 1/30（HK）与 29/30（CN-A）缺题——非截断（finish=stop）、非解析伪影。**缺题率随包大小上升**（sequential≈0 → group_10 45/90 → batch_30 不稳定）。
2. **thinking=disabled 官方参数**（round-94 owner 要求「只出结果」）：M3 直答、延迟砍半（30-35s→14-17s）、reasoning_tokens=0、content 直出 JSON；副作用=推理深度下降可能影响绝对分数——方法间同设置=对照有效，绝对分与 thinking-on 不可比（已声明）。
3. **检索器互补**：Brave 出量 202/176/171 vs Tavily 64/60/61、jaccard 0.017-0.031——双引擎并用的证据覆盖显著高于单引擎。
4. **修复率**：thinking-off 后 5-15%（run-1 40%）；「Extra data」类失败源于旧契约尾冲突（已手术移除）。
5. **Prompt 缓存有效**：prompt_tokens_details.cached_tokens≈16K/请求（重复 30K 证据块的用量大头被缓存吸收）。

## 7. 局限（诚实边界）

- 每格单次运行（无重复），大组段完整性非确定 → 覆盖结论对该次运行为准。
- 两样本 provisional 身份（rev2，非 verified）；Alphabet 无 B2a 分类行（profile 用默认题集，无需分类）。
- 配额中断导致跨窗合并（CN-A run-2b 窗 + HK/US 重置后窗；生成设置一致、合并 provenance 在回执）。
- gold/盲评未执行（前提门槛未过，预注册规则下不适用）。
- LLM-08 边界维持：证据白名单字段、不落原始响应/正文/凭据。

## 8. 交接（G3 与后续）

- **G3 独立审查未做**——本报告+全部产物（`pilot_runs/b01b_method_2026-10-07/`：合并 results/ledger/receipt、run1/run2b/smoke 归档、diag 探针、analysis）就绪待审；审查者可直接复算（错误体 2056 定性、矩阵合并 provenance、非确定性双探针）。
- **L03 前置结论**：维持逐题派发；如需重启打包对照，先解决大包完整性非确定问题（服务端/工程侧），并需 owner 的 L03 启动确认。
- 待 owner：MiniMax 控制台对账（本批实耗≈990 请求/6.5M prompt tokens——与 Token Plan 窗口消耗对账）。

## 9. 独立复核补充（2026-10-07）

以下补充以独立只读复核的归档快照为准，修正/限定上文中不能由现有工件支持的表述；不改变“inconclusive、暂留逐题派发”的操作结论。

- **用量**：保存的主回执合计 **10,008,297 prompt tokens**（run-1 无效轮 3,894,261 + run-2b 部分轮 1,058,876 + smoke 602,716 + 合并 run-3/大组重跑回执 4,452,444）。最后一项已含 run-3 base，不得重复相加；上述合计尚未包括其他探针。上文“约 6.5M”与这些回执不符，MiniMax 控制台的实际套餐额度/费用仍待对账。
- **结果归属**：base 和终版矩阵各 540 行且主键集合相同。重跑 ledger 覆盖 group_5、group_10、batch_30 的 270 个题目键；终版有 234 行值变化（分别 90、54、90），其余 36 个重跑键与 base 同值。由于没有独立重跑结果快照、逐题行没有 response/attempt ID，`method_plan.json` 也没有记录 `max_completion_tokens`，无法独立证明这 36 行取自新请求还是沿用 base，也无法逐行证明重跑设置为 131072。终版矩阵可复算，但该批次的完整行级来源和参数绑定未充分证明。
- **引用率**：18 格引用计数合计 420。按 540 个结果槽为 77.8%，按 430 个非 missing 结果为 97.7%；现有表格无法复算上文“合并口径约 88%”。“带引用”仅表示有引用条目，不表示引用已被逐条核实为支持事实主张。
- **缓存**：ledger 主请求项里的 provider `cached_tokens` 分布不支持笼统的“约 16K/请求”：run-3 base 240 项中位数 12,928（88 项≤128），大组重跑 30 项中位数 128（18 项≤128）。这些字段只证明 provider 回执报告了缓存 token；搜索缓存与应用答案缓存的正交测试、以及对应的实际费用节省均未验证。
- **大包差异**：HK batch_30 的终版为 1/30，而诊断探针保存了一次 30/30、`finish_reason=stop`。这是已观察到的两份输出完整度差异，但缺少逐请求输入 hash 和完整参数绑定，故目前不能把原因确定归到服务端非确定性。

独立复核确认结构性数据（540 行、题目唯一性、状态总数、逐格均分/引用计数）与报告一致；但正确性 gold/双人盲评未执行，缓存三层、公司级完整耗时、实际价格/套餐对账、StockWiki ACK/清理和搜索×分组交叉也未由本阶段完整验收。相应预注册项目继续保持未验收；本补充不构成 G3 放行。
