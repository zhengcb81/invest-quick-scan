# CONTEXT-PACK-06：不丢题义的上下文与题包编译器

唯一可写根`C:/Users/郑曾波/Projects/iqs-context-pack-lab`，Python包`iqs_context_pack`。本卡连同[共同契约](integration-contract.md)、[字段接口](interface-spec.md)、[独立审查](independent-review.md)、[交接模板](handoff.template.json)、发布回执/锁/consumer子集一起使用。无需另一新包完成，不读活动实验结果。目标是给后续真实实验提供可选择的薄编译工具，**不自行证明质量、缓存或经济性优胜**。

## 输入与职责

来源均是总控冻结的固定12题、18事实/9来源、原answer schema/metrics/identity、原控制器prefix_text/compile_tools，以及CODEC/CACHE/必要只读依赖。source版本和raw SHA以锁为准；后续CODEC安全反馈或原SDK变化不自动跟随。本包不接新API、不写IQS/旧Lab、不改变当前真实发包。

第一版完整保留证据、指标registry、公司身份和全部原题对象，只裁掉本次未选择的题义文本；控制器的完整验证上下文仍绑定原全集。baseline_full必须与原prefix_text全表输出逐字节相同；selected_questions调用同一个原函数传原题子集。不得自行改写题义、锚点、事实、单位、状态、source ID或unknown行为。必须给出逐组件来源与hash，不能把token减少归因于删掉必要信息。

另外研究evidence_first布局的可行性：仅在锁定原版本可无损拆分时重排相同组件，证明roundtrip和不可信数据边界；未知格式直接unsupported。此mode可明确未实现及原因，必做的两个mode及批计划不能缺。禁做关键词删证据/简化registry、提示“默认5分”、新formatter或新token账本。

## 必须公开的接口

```python
def compile_context(*, questions, evidence_board, answer_schema, metric_registry,
                    identity, selected_question_ids, mode, expected_context) -> dict: ...
def build_schedule(*, questions, evidence_board, answer_schema, metric_registry,
                   identity, ordered_question_ids, pack_size, mode,
                   company_limits, expected_context) -> dict: ...
def analyze_layouts(plans, *, scenarios) -> dict: ...
```

协议见interface-spec。analyze_layouts调用原`iqs_cache_planner.analyze_prefixes`，保留其输出与局限，不重新实现价格/前缀计量，不报真实cache命中。原CACHE每次最多接一个scenario；多个scenario须逐个独立调用并保留对应，或者明确拒绝不支持，不能静默只取第一个。compile_tools仍复用冻结原函数；缺依赖/未知版本不猜兼容。

CLI：`python -B -X utf8 -m iqs_context_pack --version/--help`；`compile`接受公共输入参数+`--question-ids IQS_01,IQS_02,IQS_04 --mode selected_questions --output <新根>`；`schedule`另收`--pack-size 3`及显式公司limits JSON；`analyze`收已经编译的plans和原CACHE scenarios JSON。选参的真实完整argv写进README，不靠终端变量外部状态。

## 工作步骤与必要检查

1. 验锁，在自己根建计划；先写有意义的失败反例，再实现薄编译/适配。
2. 用原12题跑baseline和四个三题包；每个所选原题deep equality、原board/registry/identity hash保持，12题不重不漏，原source metadata不改变。
3. 单元覆盖空/未知/重复ID、错误company/cutoff/context、原锚点变化、未知mode/version、非有限数/重复键、含相似段落标记/HTML/指令的恶意字符串、只改排序的指纹差异、limits不因包数增加。不能只镜像自己的实现写断言。
4. 集成必须真调用冻结prefix_text、compile_tools、CODEC及CACHE；同一合法compact答在full和selected模式下展开的原标准内容一致（不冒充LLM质量比较）。私有model/history/费用不能进prefix。evidence_first若支持要有重排与marker注入实质反例。
5. 公开CLI E2E：新根compile→schedule→analyze，异机/不同cwd输入搬迁稳定摘要一致；缺输入/篡改/路径外跳/既有输出拒绝，无外根写/网络；清理自有temp。
6. 最终提交payload后**实际调用独立agent全面审查、修完所有有效发现并复审通过**，按independent-review.md留完整证据。仅此一个整包审查节点。

交`docs/handoff/CONTEXT-PACK-06/`，含两个必做mode实物、可选mode真实状态、schema/API/CLI、示例schedule及缓存分析、测试/清理/独审闭环。报告明确“字节投影/理论布局，不是实际缓存率/价格/准确率”，所有资格false。不替总控集成或启动真实实验。
