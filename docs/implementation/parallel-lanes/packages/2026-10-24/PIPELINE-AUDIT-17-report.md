# PIPELINE-AUDIT-17 差异归因报告

- 工具：`scripts/applic_pipeline_check.py`（7 项测试，`tests/test_applic_pipeline_check.py`）
- 快照：`applicsnap_d296902c…`（pred_6ffa4a71 × attr_897fecae，2026-10-21 评估口径）
- 样本覆盖：**2/214 家**（全库仅 CATL 与 Alphabet 有可复用组装 manifest；其余 212 家无可复用 profile，按卡 R1 如实报 0 覆盖，不硬凑）
- 复跑：本报告每个数字可由工具原命令重现

## 1. 交叉表（摘要）

| 样本 | rows | 一致 | 快照适用而组装未选 | 组装选而快照非 applicable |
|---|---|---|---|---|
| CATL | 48 | 43 | 4 | 1 |
| Alphabet | 48 | 41 | 6 | 1 |

两样本退出码均为 2（有差异）。

## 2. 逐条差异与根因分类

### CATL

| 模块 | 快照判定 | 根因类 | 证据 | 管线建议 |
|---|---|---|---|---|
| industrial | unknown（`negative_evidence_not_verified`：industry=[auto] 不满足 in[industrial]） | **手工 profile 与谓词不同源** | manifest profile `industry_modules:[auto, industrial]`；快照属性 industry=[auto]（assumed，G2-2 裁定口径） | 属实分歧：组装器的行业轴允许多选，谓词按单标签判。属**架构级**——组装器吃 profile 字段、快照吃属性表，两套真源。归所有者裁定（见 §3 Q1） |
| cross_border | applicable（extra.cross_border=true） | **组装器缺 extra 轴通道** | 谓词判真；组装 profile 无 extra.* 概念 | 若要采纳，组装器需新增「extra 旗标 → overlay/主题模块」映射；或裁决 extra 类模块不进 thin_scan（记录为已知偏差） |
| scaling | applicable（stage=[mature,scaling] 双标签） | **组装器阶段轴单选 vs 谓词多标签** | profile `stage:"mature"` 单值；快照 stage=[mature,scaling] | 同 Q1 家族：阶段轴语义差 |
| dupont / porter | applicable（所有者裁定恒适用） | **所有者裁定通道未进组装器** | G2-1 原话「杜邦分析和波特五力是针对所有公司都适用的呀」；组装 profile `diagnostic_modules:[]` | 若采纳：诊断模块默认全开或经路由规则显式触发；当前组装器只能手工开 |

### Alphabet

| 模块 | 快照判定 | 根因类 | 证据 | 管线建议 |
|---|---|---|---|---|
| software | unknown（industry=[internet] 不满足 in[software]） | 同 CATL/industrial：profile 多行业 vs 谓词单标签 | profile `industry_modules:[internet, software]` | 同 Q1 |
| acquisitive / cross_border / listing_structure | applicable（extra.*=true） | 同 CATL：extra 轴无通道 | — | 同 Q2 |
| mature | applicable（stage=[mature,scaling]） | 阶段轴语义差 | profile `stage:"scaling"`？—— 否，实为组装选 scaling 而快照两标签都真 | 同 Q1 家族；注意「组装选 A、快照 A+B 都真」仍计一致（both exclude nothing），差异只在组装未选 mature |
| dupont / porter | applicable | 同 CATL | — | 同 Q3 |

**两样本根因完全同构**（4 类：真源不同、extra 通道缺、阶段轴语义差、诊断通道缺）—— 说明这是**系统性管线断点**，不是 CATL 单例错误。

## 3. 归因汇总与待所有者裁定的架构问题

| # | 问题 | 性质 | 选项 |
|---|---|---|---|
| **Q1** | 组装器的 profile（手写：行业多选、阶段单选）与快照谓词（属性表单标签、stage 多标签）**真源不同** | 架构 | A：组装改为「快照驱动」（读 applicable 模块集组装）；B：保持手工 profile，把快照作为**校验器**（本工具即此形态）；C：双轨并存，差异清单随每次组装输出 |
| **Q2** | extra.* 旗标模块（acquisitive/cross_border/listing_structure）组装器无通道 | 通道缺失 | A：新增映射；B：裁决不进 thin_scan，记已知偏差 |
| **Q3** | dupont/porter 所有者恒适用裁定未进组装器 | 通道缺失 | A：诊断默认全开（对齐 G2-1）；B：维持手工开 |
| **Q4** | industrial 类「组装选了、快照谓词判假」是否要在扫描前阻断 | 流程 | A：组装前跑本工具，差异非空即人工复核；B：仅记录不阻断 |

## 4. 已知边界

1. 快照属性全部 assumed（G2-2 所有者裁定），谓词判假一律降级 unknown 而非 not_applicable —— 本报告的差异不受此影响（差异只看 applicable 与否）。
2. 组装器模板 3.2.0（48 模块时代）vs 题库 4.2.0（62 模块）vs 快照谓词 pred_6ffa4a71 —— 三处版本未对齐是**更大范围的管线议题**，超出本卡（记入 Q1 家族）。
3. 样本 2/214：全量对账需先有 214 家的组装 profile（或按卡 R1 接受现状）。

## 5. 结论

两条管线（题库组装、适用性判定）各自已验收、各自测试绿，但**汇合点从未对齐**。差异不是 bug 而是设计真空：组装器从不知道快照存在。四个架构问题（Q1–Q4）需所有者裁定后，另立实现卡落地 —— 本卡到此为止，不动任何判定语义。
