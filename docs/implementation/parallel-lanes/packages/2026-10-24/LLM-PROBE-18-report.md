# LLM-PROBE-18 报告 — 用你的 12 条裁定检验四个模型（对照快照）

- 日期：2026-10-24
- 问题（所有者提出）：像「宁德时代是不是 industrial」这类语义判断，问 LLM 是否比程序逻辑更准？
- 方法：把 **48 个模块的 id/轴/中文名/适用条件** 全量给模型，要求严格 JSON 逐模块回答 yes/no/unsure；只抽取**你裁定过的 12 行**做对照（不告诉模型哪些是争议行，避免引导）。
- 数据：`applicsnap_d296902c…`（pred_6ffa4a71 × attr_897fecae）；裁定基准 = 复核页导出的 `decisions.json`（12 行）
- 复跑：`scripts/applic_llm_compare.py`（prompt/answer 全存档于 `runs/applic-llm-probe-2026-10-24/`）

## 1. 结果总表（✓ = 与你一致）

| 公司 | 模块 | 你的裁定 | 快照 | deepseek-flash | mimo-v2.6-pro | MiniMax-M3.1 | mimo-v2.6-flash |
|---|---|---|---|---|---|---|---|
| Alphabet | acquisitive | 采纳快照 | yes | ✓ | ✗否 | ✓ | ✗缺失 |
| Alphabet | cross_border | 采纳快照 | yes | ✓ | ✓ | ✓ | ✗缺失 |
| Alphabet | dupont | 采纳快照 | yes | ✓ | ✗否 | ✗否 | ✗缺失 |
| Alphabet | listing_structure | 采纳快照 | yes | ✓ | ✓ | ✓ | ✗缺失 |
| Alphabet | mature | 采纳快照 | yes | ✓ | ✓ | ✓ | ✗缺失 |
| Alphabet | porter | 采纳快照 | yes | ✓ | ✓ | ✓ | ✗缺失 |
| Alphabet | software | 保留人工 | unsure | ✓ | ✓ | ✓ | ✗缺失 |
| 宁德时代 | cross_border | 采纳快照 | yes | ✓ | ✓ | ✓ | ✓ |
| 宁德时代 | dupont | 采纳快照 | yes | ✓ | ✗否 | ✗否 | ✗否 |
| 宁德时代 | industrial | 保留人工 | unsure | ✗否 | ✗否 | ✗否 | ✗否 |
| 宁德时代 | porter | 采纳快照 | yes | ✓ | ✗否 | ✓ | ✓ |
| 宁德时代 | scaling | 采纳快照 | yes | ✓ | ✓ | ✓ | ✓ |

| 判定源 | 与你一致 | 说明 |
|---|---|---|
| **deepseek-flash** | **11/12** | 只错 CATL/industrial |
| 快照（规则引擎） | 10/12 | 错 CATL/industrial、Alphabet/software |
| MiniMax-M3.1-Flash | 9/12 | 错 dupont×2、CATL/industrial |
| mimo-v2.6-pro | 7/12 | 错 dupont×2、porter、CATL/industrial |
| mimo-v2.6-flash | 3/12 | Alphabet 整块 `model_not_json`（结构化输出不可靠） |

## 2. 差异逐条归因（重点）

### 2.1 CATL / industrial —— 四个模型**全都说 no**，错因是规则文本

四个模型的理由高度一致：

- deepseek：「电池属汽车和储能环节，非专业设备」
- mimo_pro：「非资本品机械或自动化装备企业」
- minimax：「不属于资本品或专业设备行业」
- mimo：「已有专属能源与汽车模块覆盖」

模块的 `applies_when` 写的是「**资本品、机械、自动化、航空航天和国防装备等**」—— 按字面，电池电芯是**流程制造**，确实不属于资本品/装备。而模块中文名叫「工业制造、自动化与专业设备」，你的判断是「电池制造业当然是制造业（工业）」。

**结论：这不是模型能力问题，是规则文本过窄/名实不符**。任何人（包括模型）按字面读都会判 no。修法只有两条：把 `applies_when` 扩为「资本品、机械、流程制造（化工/材料/电池等）、自动化、航空航天」之类；或把该模块拆成「装备制造」与「流程制造」两个模块。**在这条上 LLM 与规则引擎同错，谁也救不了错误的规则。**

### 2.2 dupont（两公司）—— 规则写成「触发条件」，与你的裁定冲突

规则原文：「ROE变动或质量**无法由核心题解释时选用**」—— 这是**条件触发**语义。你在 G2-1 裁定的是「杜邦分析对所有公司都适用，不用选装」。

于是模型按字面执行触发条件：
- minimax（GOOGL）：「核心业务可解释回报来源，无需单独诊断」→ no
- mimo_pro（GOOGL）：「回报可由核心问题解释，无需杜邦」→ no
- mimo_pro/minimax（CATL）：同理由 → no

**结论：你的裁定没有进入规则文本**。快照之所以判 yes，是因为它把这条模块记为 `owner_ruled_always_applicable`（所有者裁定恒适用）；而 LLM 只看到散文规则。要让 LLM 与你的裁定一致，必须把「所有者裁定」作为提示词的一部分传达（例如规则行标注「本模块经所有者裁定对所有公司恒适用」），或者直接改 `applies_when` 措辞。

### 2.3 porter —— 同类触发规则，但模型分歧更大

「竞争结构或价值链利润归属**不清时**选用」—— deepseek/minimax 认为「不清」（判适用），mimo_pro 认为「相对清晰」（判不适用）。同一规则、不同模型对「清不清」的阈值不同。

### 2.4 同一模型的稳定性问题（重要）

**deepseek 在 CATL/dupont 上因提问方式不同而翻转**：

| 运行 | 提问方式 | 答案 |
|---|---|---|
| 首次 | 一次问 48 个模块 | **no**（理由：ROE 可由核心题解释） |
| 跨模型 | 分两块各问 24 个 | **yes**（理由：ROE 受净利率、周转杠杆驱动，可诊断） |

温度已设 0，但**提示词结构变化仍会改变答案** —— 触发类规则的边界本来就模糊，模型在长列表里更容易「顺带」判 no，在短列表里更容易独立判断。

**含义**：LLM 判定不能当成可复现的确定性函数；若要入库，必须固定提示词模板、固定分块大小，并对结果做抽检复核。

### 2.5 mimo-v2.6-flash 不适配

Alphabet 整块返回非法 JSON（`model_not_json`），CATL 正常 —— 输出较长时结构化不可靠。不宜用于此任务。

## 3. 结论与建议

1. **LLM 在 11/12 上复现了你的判断，优于快照的 10/12** —— 你的直觉是对的：语义类判定（行业归属、是否「不清」）问 LLM 比写死的谓词更准。
2. **但两个错点（CATL/industrial、dupont）根本不是模型错，是规则文本错**：
   - industrial 的 `applies_when` 把「工业制造」窄化成「资本品/机械/装备」；
   - dupont/porter 的 `applies_when` 写成触发条件，未体现你「恒适用」的裁定。
   **先修规则文本，再谈谁判得更准** —— 否则换任何模型、写任何代码都会得到同样的错。
3. **推荐的混合架构**：
   - 机械轴（type/stage/industry 枚举匹配）继续用确定性谓词 —— 便宜、可复现；
   - 语义/触发类（industrial 边界、dupont/porter 是否需要、recovery「是否下滑过」）交给 LLM 判定；
   - 你的裁定（owner_ruled_*）必须显式注入提示词，而不是只存在快照里；
   - LLM 结果固定模板 + 固定分块 + 抽检，并保留每次的 prompt/answer 存档（本报告的做法）。
4. **待你决定**：
   - 是否先修 industrial / dupont / porter 三条 `applies_when` 的措辞（这属于谓词规则变更，会 bump predicate_version 并重建快照）；
   - 是否在适用性层正式引入「LLM 判定通道」（需要新卡：固定模板、成本、抽检、与快照的关系）。
