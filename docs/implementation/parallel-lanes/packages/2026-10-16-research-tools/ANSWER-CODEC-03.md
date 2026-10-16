# ANSWER-CODEC-03：紧凑答案传输与无损标准化

唯一可写根：`C:/Users/郑曾波/Projects/iqs-answer-codec-lab`。先读本卡、同目录 integration-contract.md、inputs.lock.json；所需输入域 iqs/company/trial/rules。其他仓及新 Lab 全部只读。不改模型 SDK、研究调度、预算、题库或最终标准答案 schema，不发任何模型/搜索请求。

## 要解决的问题

T0 真实运行中，完整标准 JSON 的逐题重复元数据使输出庞大，Free 首次输出达到 16384 token 后协议失败。不要简单删理由或关思考。设计**可选的新传输协议**，让 LLM 主要输出判断、依据、反证和必要数字，确定性程序补回已知来源元数据；最终仍通过原标准答案校验。是否真的提升准确率/费用只能由总控真实对照验证，本包不能宣布赢家。

## 已锁接口

Python 包 `iqs_answer_codec`：

```python
def expand(payload: dict, *, questions: list, evidence_board: dict,
           company_key: str, cutoff: str, context_ref: dict,
           answer_schema: dict, metric_registry: dict) -> dict: ...
def render_instructions(*, questions: list, evidence_board: dict) -> dict: ...
```

`expand` 为纯函数，无网络、无外部写、无环境读取；接收 `iqs.compact-answer-batch/1.0.0`，返回 `iqs.expanded-answer-batch/1.0.0`：`answers` 为标准答案 list，另有逐字段 `expansion_manifest`（输入字段/冻结 source_id→输出字段及明确标为 canonical-object 的内容哈希）。对象函数不能恢复原文件raw SHA；CLI在读原件时另附每项原文件raw SHA/bytes的provenance封套，两种哈希不能混称。`render_instructions` 返回该传输的 JSON schema、简短规则、版本；不得混入私有参考或改变原题锚点。不生成 LLM 请求、不代写模型会话。

CLI：`python -m iqs_answer_codec expand --payload P --questions Q --evidence E --company-key alphabet --cutoff YYYY-MM-DD --context-ref C --answer-schema A --metrics M --out NEWDIR`；另提供 `instructions` 子命令，文档给完整 argv。参数均为显式本地路径；错误批次不得部分落盘。

`context_ref` 由调用方从**原请求的可信绑定**传入，字段恰为 `company_key`、`cutoff`、`question_canonical_sha256`、`evidence_board_canonical_sha256`。hash统一为 UTF-8 的 `json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)` 的 SHA256，questions使用完整列表和原顺序。函数核对实参和两份内容hash，CLI另核文件rawhash封套；不能临时从错误board生成expected值再声称核过原任务。codec只保证匹配所提供可信context，不认证StockWiki身份或来源资格。测试中构造两个公司复用source_id、错board传入但原context保持的反例，必须拒绝。

## 传输字段：保持明确，不能补造

顶层固定 protocol、company_key、answers，company_key 必须与调用方显式期望值及 evidence_board.company_key 一致，board.cutoff 必须与本次cutoff一致；answers 1–3 条，每题除 `evidence` 换成 `source_claims` 外仍显式带原标准答案所有字段：question_id、response_kind、status、score、summary、information_as_of、period_start、period_end、basis、trend、confidence、metrics、items、counterevidence、watch_triggers、missing_fields、coverage。保留数字的币种/单位/期间/basis/definition 等原结构，不能用数组位置省略含义。

`source_claims` 每项严格为 `{source_id, claim}`。source_id 必须存在于当前公司/截止日已冻结公开板；只能从同条 source 复制 title/official_url/publication_date 成为原 evidence 的 id/title/url/published_at，claim 原样保留。counterevidence 等原标准结构不随意缩写。claim 仍是模型的主张，引用存在不等于事实已核。metrics/items 的 evidence_ids 必须绑定本题 source_claims，不能程序偷偷补引用。

**无损的可表示域必须说清**：只有原 evidence 元数据与冻结来源完全一致的标准答案，才能删去重复字段后逐字段无损 roundtrip。旧 AnswerSink 未强制 title 等于板title，因此“旧合法答案”不必然在这个域内。若提供反向压缩辅助函数，遇到不同title等必须明确拒绝/标为不可无损表示，不静默重写原件。新紧凑生成的输出明确标注哪些元数据由程序复制，不冒称模型自己核实了这些字段。

不默认 status/score/confidence/趋势/期间/口径；不将缺失 score 设 5；unknown 必须 null 且遵守原未知态约束。日期可显式 null，但不能默用 cutoff 代缺失历史期间。原字段缺失应拒绝。不要把一家公司 source_id 自动补成另一家的同名来源；重复冲突来源拒绝。保留 1.0 载体未来演进空间，未知版本拒绝。

第一版只优化来源重复字段和 schema 发送方式，**不承诺必定大幅节省 token**。若离线测量节省有限，如实报告，并在自己根 proposal 讨论更激进的后续版本，不临时改已锁接口。原标准直接输出继续可用，codec 不改原 AnswerSink。

## 实施与测试

1. schema/函数/CLI 和有效、unknown、部分证据三类样例先落地；构造完整标准答案→只替换 evidence 的紧凑输入→展开与原内容逐字段相等，原 validator 真通过。
2. 实现原子转换及 provenance；相同 source 被多题引用时允许正确复用，同批题重复拒绝。不能依赖外部当前ROOT；测试验证所有导入来自输入快照。
3. 单元反例集中覆盖：未知/冲突 source、错公司/未来 source、同题重复、未请求题、score/status 冲突、缺理由、空成功证据、指标单位/币种/期间错误、丢失 evidence 绑定、未知版本/字段、重复键/非有限数、超上限与中途失败不部分输出。引用的“语义支持”仍明确不在 codec 保证范围。
4. 集成用冻结12题及域内真实 T0 合法答案做 roundtrip，不修改其分数/理由或来源title；若4条真实答案均不在可表示域，应输出具体不可无损原因，保留原件，以明确synthetic的域内标准答案完成正例，不能改真答案凑成功。未知态不得被正常化成 scored。用固定 synthetic 非评分 fact 题另测 items/relations（明确 synthetic，不冒充真实 owner）。
5. E2E 通过真实公开 CLI 成功展开并重新原生校验；损坏输入/已有输出目录/路径逃逸均非零且原输入及外根保持；断网运行，临时根清理。
6. 报原始答案与紧凑 payload 的 UTF-8 字节/字符差异、例子范围。没有真实 tokenizer 时不得把字符数叫 token，也不把压缩率当准确率/模型成本结论。整包一个审查节点。

交接：`docs/handoff/ANSWER-CODEC-03/`，按同目录 handoff-ANSWER-CODEC-03.template.json 和共同规范。交付应可在没有另外两包时测试完成。总控之后把可选 codec 接到新实验 cohort，原 T0/T1 输入和账本不改。
