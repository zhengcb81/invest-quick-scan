# 批次状态板（2026-10-24 收盘版）

## 一、包状态

| 批次 | 包 | 状态 | 下一步 |
|---|---|---|---|
| 2026-10-19 | QUESTION-BANK-UPGRADE-12 | ✅ 已验收（R2 闭合，CLI valid） | — |
| 2026-10-19 | UI-BANK-EXPLORER-13 | ✅ 已验收（G7 签收 `9ab7a33`） | — |
| 2026-10-21 | APPLIC-RESOLVE-14 | ✅ 已验收（APPROVED，R1 闭合） | — |
| 2026-10-23 | UI-APPLIC-BRIDGE-15 | ✅ **已验收**（R1 落盘 `484db19`：三处声明修正 + 外部绑定 + 审查报告随包；代码零改动；CLI valid；118 OK） | — |
| 2026-10-24 | APPLIC-GAP-CLOSE-16 | ✅ **已验收**：R1（逐对同值）由 worker 完成；R2（空集/缺格/签收文案/UTC/红相/下标语法）由主控直接修完；CLI valid；191 tests | — |
| 2026-10-24 | APPLIC-LLM-JUDGE-20 | ✅ **已验收**（R2 裁定：第一轮多数 yes 即适用；323 tests；快照 1924/8348 与独立复算一致） | — |
| 2026-10-24 | RULE-SCOPE-DECISION-19 | ✅ **已验收**（三仓落地；四包 CLI valid；AC-02 v2 路由路径为已登记边界） | — |
| 2026-10-24 | BASIC-BANK-EXPANSION-21 | ✅ **已验收**（三仓落地 `f606fa9`/`c3feee6`/`c45756e`；硬编码 24 清零；195+54+126 测试全绿） | — |
| 2026-10-25 | APPLIC-REBASELINE-R3 | ✅ **已完成**（policy 2.4.0 新锁；10272 格逐格零差异，仅 inputs 变） | — |

## 二、今日决策记录

1. **industrial 维持狭义**（装备制造），改名「工业装备与专用设备」并写明不含流程制造 —— 依据是 4 道题全部假设设备/项目商业模式。
2. **dupont / porter 改为对所有公司必做**，由 `owner_ruled` 升为契约恒适用，组装默认必含。
3. **复核台账 R003 被取代**：CATL 的 industrial 定为不适用（台账 append-only，未改历史）。
4. **LLM 通道规则**：high + medium 都采纳；LLM 说 no 走**三方互证**（换模型 + 谓词仲裁），仅三方一致才产出 `llm_corroborated_not_applicable` 且强制复核。

## 三、今日实证数据

| 实验 | 结论 |
|---|---|
| 四模型 × 你 12 条裁定 | deepseek 11/12（优于规则引擎 10/12）；两处差异均源于**规则文本**而非模型能力 |
| 4 模块 × 24 家 shadow | 96 格零错误；high 59 / medium 37 / low 0；**「快照适用但 LLM 说 no」= 0 格**，LLM 只补充 13 格 |
| GAP-CLOSE-16 R2 前后 | 空集→no_evidence、缺格→incomplete；真实 RED 日志 4 failed / 16 passed |
| 主仓全量回归 | **1036 passed / 3 skipped / 755 subtests**（14:30 完成，exit 0；较今日早间 1011 增加 25 项——本月新增的管线审计/复核包/LLM 探针测试） |

## 四、未决事项（需所有者）

1. 复核台账 2 行缺理由：**R009 listing_structure**（采纳快照）、**R012 software**（保留人工）—— 各补一句即可入库。
2. RULE-SCOPE-DECISION-19 是否现在派题库 lane。

## 五、主控环境注意

- 主仓 `questions/releases/current.json` 仍为他人会话遗留的未提交改动（10-18 mtime），不动。
- 主仓题库受信任锚管辖：改内容必须补 lifecycle 元数据，否则 29 个路由/发布测试红（已实测并回滚）。
