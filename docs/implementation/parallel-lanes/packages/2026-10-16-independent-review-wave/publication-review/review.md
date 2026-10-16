# 三个新包的发布前独立设计审查

审查者：`/root/paired_critic_prepare`；仅审设计，未实施任一 Lab。输入冻结/发布回执正在准备，不以其尚不存在判失败。没有调用模型、搜索或其他网络，没有读取 T4 答案/费用/账本，没有修改卡片、任何 Lab 或 generation 输入。

结论：**一处需在发布前消歧的接口缺口；修正后设计可发布。** 三包的独占根、主线避让、原依赖薄复用、一次整包独审及修复闭环整体合理，无需拆成更多审查节点。

## F01 — REVIEW assignment 与匿名映射缺少明确可执行的 API 绑定（P2）

位置：`REVIEW-CAL-06.md:27–31`；`interface-spec.md` REVIEW 部分。

要求同时写了“私有 map 另存”“judgments 绑定完整 assignment hash”，但公开纯函数是 `score_calibration(casebook, imported_judgments, *, expected_context)`，没有接收 assignment 或私有 map；`make_assignment` 的返回结构也未明确。`expected_context` 在共同契约中是冻结源上下文，不能默认等价于某一次随机分配的 authority。较弱实现容易只检查 judgments 自报的 hash，或以原有含 family/pair 提示的 case_id 当公开 ID，导致跨 assignment 错配/解盲而测试仍能自证通过。

最小修正建议（不引入新评审框架/节点）：

1. 规定 `make_assignment` 返回分开的 `public_assignment` / `private_map`，公开使用不含 family/pair/expected 暗示的 opaque assignment ID；原 case ID 和映射只在私有 map。
2. 将 compare API 明确为 `score_calibration(casebook, imported_judgments, *, assignment, private_map, expected_context)`，或同等明确的一个 assignment bundle 参数。CLI 已有 `--assignment`，再明确私有 map 的文件位置/参数即可。
3. 私有 map 绑定公共 assignment canonical hash、casebook 内容 hash；compare 校验映射一一对应及 case 内容，拒绝 wrong assignment / wrong map；缺失仍计原分母。把这两个反例并入已有整包 tests，不增新 gate。

修正这些字段/接线即可，不需要改变 JUDGE 或另造 semantic scorer。

## C01 — CACHE 多 scenario 调用建议加一句（非阻断）

位置：`CONTEXT-PACK-06.md:24`。

已用 CodeGraph 确认原 `analyze_prefixes(prefixes, *, scenarios)` 会明确拒绝 `len(scenarios)>1`，不会替调用者批处理。卡片写了复数 scenarios 而未说明边界。建议一句确定第一版行为：多场景逐个调用原函数并保留逐场景结果，或首版仅接受 0/1 场景并拒绝更多；不得只取首项。这是文档精确性改进，不需要新增产品范围或测试节点。

## 已确认合理且可独立施工的部分

- `iqs-context-pack-lab` / `iqs-review-calibration-lab` / `iqs-resume-chaos-lab` 三根互不为祖先/后代，本次 `Test-Path` 均为 false；与已开工的 operating-catl / operating-csc / experiment-desk 三根、IQS、StockQA 和既有六工具均不重叠。这里只读检查，不预占/创建这些根。
- 每包都不依赖其他新包结果；全程离线，精确冻结输入为 authority，不追活动 latest。发布时再验证实际 consumer 子集与可搬迁锁；本审查不虚报已完成发布验证。
- CONTEXT 的 selected 文本与完整验证 context 分开；原 board/registry/identity 保持，CODEC 仍用原全集验答。原 prefix 直接复用；可选重排的 unsupported 有明确边界，不需要为了“做完”改造上游。
- REVIEW 合成数据与真实公司参考区分，主观分数不设唯一 gold；格式负例与金融语义错分开。48 个案例及 12 对反例、逐 case 的独立审查是有限且可实施的工作量。
- CHAOS 使用原 HTTP 注入边界/临时原 store/原 SDK/SESSION/CODEC/Sink，观察与预期分离。真实故障点不支持时诚实报告，不伪装原能力；源缺陷则 blocked，而不是改冻结源、发 fake observed 或换库解闸。
- 独审必须是真实不同 agent、绑定最终 payload commit、有效发现清零后复审；无 agent 能力或 upstream defect 则 blocked。只保留一个整包节点，没有要求逐 helper/逐 case 独审审批。
- temp/secret/禁网/进程和原输入保持要求具体，未要求实网或付费调用。新工具均不授予金融真值、生产 owner 或评分资格。

审查范围是施工设计；未运行任一尚未实现的产品测试，未把模板/锁结构通过当成施工验收。
