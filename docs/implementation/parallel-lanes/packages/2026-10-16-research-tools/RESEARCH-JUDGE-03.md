# RESEARCH-JUDGE-03：隔离研究输出的完整盲评与比较

唯一可写根：`C:/Users/郑曾波/Projects/iqs-research-judge-lab`。必读 integration-contract.md 和 inputs.lock.json；用 evaluation/company/iqs/trial/rules，reference 只给自己的离线参考计分器。其余仓只读，无收费模型/搜索，不组织生成 LLM 或实际付费判题。

## 任务和兼容性

已签收 EVAL 的 ResearchRun/owner bridge 不能直接接受新的 isolated-research。做**显式新适配器**，复用冻结 EVAL 的 strict JSON、盲化、指标/投影等可用纯工具，公开记录哪些重用、哪些新增。不更改旧 EVAL schema，也不将新输出改名为 owner_runtime 来混过验证。不要重写已签收全套评测框架；新增小型边界和必要 isolated 计量适配即可。

本包完成工程及离线实证，真实金融盲评仍由总控组织。自动评分只能核十个独立主标量的明确结构化断言；不能靠关键词/模型间一致打“金融正确”。无唯一1–10 gold。完整质量规则见冻结 rules。

## 公开接口

Python 包 `iqs_research_judge`，以下均离线：

```python
def adapt_isolated(result: dict, *, events: list, questions: list,
                   evidence_board: dict, projection: dict) -> dict: ...
def build_review_bundle(runs: list, *, seed: str) -> dict: ...
def import_judgments(bundle: dict, judgments: dict) -> dict: ...
def compare(reviewed: dict, *, private_map: dict) -> dict: ...
```

各新中间/评审/判定/比较载体使用分别明确的 `iqs.isolated-evaluation/1.0.0`、`iqs.isolated-review-bundle/1.0.0`、`iqs.isolated-judgments/1.0.0`、`iqs.isolated-comparison/1.0.0`；自行写关闭式 schema、样例。CLI `python -m iqs_research_judge adapt|blind|import-judgments|compare`，文档写每个必需参数和一条全链路实例。

原输入 result 字段见 trial 六份真实结果及冻结 driver：protocol1.0/1.1，answers=list，revisions 为按题 revision/answer/hash，1.1还可有scan/model/native_attempt元数据；两版显式分支接受，不凭删除字段降级。events 的真实 receipt 按 attempt_id 接回，不能只数 sdk_step_invocations 当 HTTP。缺少 receipt 的失败保留“实际发送未知”，不能自动计0。原 1.0 失败草稿只有 hash，正文不可复核。

评测总目标由完整12题和显式 logical→effective projection 定义，不从 answers 自动生成。11原题+OPERATING_01，漏题保留，重复/异题/错公司/哈希冲突拒绝。T0六会话必须是72个目标槽，4个合法答案、68个未交卷槽；不是 accuracy=4/72，也不是 success4/4。生成中间接口自行文档化但保留每槽原题、原执行状态、答案/缺口和溯源。

## 盲化与判定

公开评审只含匿名 session/slot、原题和锚点、完整标准答案、统一公开证据、cutoff/必要公司身份和确定性随机顺序；不含策略、模型、端点、耗时、费用、原始目录名、receipt/request/prefix hash、repeat可识别编号或私有映射。稳定 seed 的解盲映射在单独 private/ 下，不能只是从公开JSON隐去而在文件名/目录/manifest/log泄露。

答案自身若显式自称模型/策略，使用既有冻结盲化规则；不能悄悄删改投资论据。无法无损去除的题标为 blindability failure、保留目标槽，公开包不导出泄漏正文；private 保留原件和失败理由。不能为“保留失败分母”而把敏感原文照发给评审。

判定输入必须逐匿名槽显式标记语义覆盖（充分/部分/审慎不足/缺失未解析）、事实短命题及 supported/contradicted/unsupported/not_assessable、原始 source_id 绑定、推断/事实区别、评分理由合理性和引用支持。验证判定不存在未知槽/重复槽/跨公司引用/错bundlehash；缺判定保留 pending，不补“正确”。任何数值自动核验要匹配主体/指标/期间/币种/单位/口径；未明确结构化匹配的自然语言主张留人工，不猜提取；跨题同 atom 去重。

十个主参考不是复合 fact 全文资格，更不是所有12题评分 gold。reference 数据不能自动注入公开生成输入；实际评审需要的独立参考应作为总控明确的评审私有资料，私有rubric不发生成模型。

## 必做验证

1. 单元 RED：答案缺失却100%成功、unknown score5、OPERATING_01误配IQS11、重复revision/改rawhash、失联receipt被当0、reasoning与output双计、缓存分母错误、未来/错单位参考、评审未完成被当赢家。
2. 集成：六个真实T0结果按72槽展开、初答/修订/失败可追溯；无 financial judgments 时 accuracy/winner必须null。若与原 EVAL 的 status 映射不同，保留原 token 并显式新映射，不能让无法解析的状态消失。
3. 盲包正反例：可重复seed、换seed不丢目标；正文/文件名/引用路径/私有映射泄漏、模型自称、混公司、篡改输入均被正确处理。检查真实公开输出树，不只检查内存对象。
4. E2E：公开 CLI 从冻结 T0→盲包→**标明synthetic的测试判定**→比较，真实结果仍无金融判定；另测试漏判/坏bundle/已有输出目录/路径逃逸。不得把synthetic判定和真实金融验收一起统计。
5. 费用仅沿真实 receipt/usage；配对键含公司、有效题集/证据hash、cutoff、模型/搜索配置、strategy版本、repeat/阶段；跨 treatment 默认拒绝直接排名，输出未配对原因。可以展示原始行，但不能假设 T0与后续新prompt是同因子比较。
6. 全套禁网、临时文件 finally清理。整包一次集中验证/审查；不用另一新包也能完成。

交接：`docs/handoff/RESEARCH-JUDGE-03/`，模板见同目录 handoff-RESEARCH-JUDGE-03.template.json。列出真实T0计量与未知金融状态、哪些旧接口可复用及明确不可支持的版本。生产评测/正式评分库/G3均未获本包资格。
