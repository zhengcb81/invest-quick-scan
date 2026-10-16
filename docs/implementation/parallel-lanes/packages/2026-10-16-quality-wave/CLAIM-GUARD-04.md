# CLAIM-GUARD-04：数字、口径、来源和评分论据分开查

唯一可写根 `C:/Users/郑曾波/Projects/iqs-claim-guard-lab`。先读共同规范/输入锁；不写其他仓、不发真实模型/搜索。不得重做上一轮JUDGE的盲评打包/解盲比较，不重做CODEC。本包是生成后、入库前的**核查候选**，不改答案或授金融资格。

## 实际问题

T0把正确164713百万美元OCF贴到financial.fcf；T1两答把报告OCF减capex称WC调整前。其他答案用利润率/财务规模替代ROIC、用增长推留存、用账面现金推压力情景履约。JSON和数字摘录可通过，但论据与指标含义仍错。做可确定检查和需要独立复问的检查，不能靠关键词搜索假装理解所有财务语义。

## 公开接口

包名 `iqs_claim_guard`：

```python
def check(answer: dict, *, question: dict, evidence_board: dict,
          context_ref: dict, metric_registry: dict,
          objective_reference: dict | None = None) -> dict: ...
def build_critic_input(answers: list, *, questions: list,
                      evidence_board: dict, context_ref: dict) -> dict: ...
```

check返回新protocol `iqs.answer-claim-findings/1.0.0`：原answer/context规范hash、原题id、findings。每条有稳定rule_id、字段路径、原答短主张、判定层级deterministic_conflict/review_required/unassessable、severity、相关source_id/atom、依据/缺口。没有发现只表示已执行规则未发现，**不能写financial_accuracy=true**。答案原对象不变；不自动改score、不把缺证改5、不让规则暗设主观最高分。

critic输入protocol `iqs.answer-critic-input/1.0.0`，只含公开原题/锚点、完整原答、公开board/截止日、明确待核维度及批判输出schema；不带生成模型/策略/成本/私有参考、review预期标签。它是交给原SDK调用的纯数据，不执行LLM。输出规范要求critic逐题列具体错误/证据缺口/支持或反驳的来源、可核修正建议、是否需要再检索；不输出隐藏思考、不强迫另给1–10黄金分。

CLI `python -m iqs_claim_guard check|critic-input`，显式原件路径/context/指标及可选参考，输出新目录；公开schema与至少两个JSON例子。

## 判定边界

- 复用原validator先验结构。币种/单位/期间/历史与forward/合并vs分部口径均须显式；unknown参考不是0。
- objective_reference只用于十个预锁主标量的离线核查，按主体+指标+期间+单位+币种+口径匹配，不能将复合记录或评分整体合格。未能可靠归一到原子命题的自然语言留review_required/unassessable；数字在来源出现不等于支持整句。
- 必须抓到实际T0 OCF→FCF误标；正常报告FCF=OCF-全部现金capex本身可正确，但未能区分维护/增长capex时不能宣称owner可分配现金。只有报告OCF-capex却明确称“WC调整前”，标口径冲突/需要核对，不能反向猜出真实WC调整额。
- 不把经营利润率当ROIC，净利润当NOPAT，收入增长当已证留存/市场份额，Cloud增长当已证AI股东净价值。若文本明确标为可能推断及列缺口，不能一律当contradicted。压力履约推断需要到期债务、承诺、现金可用性及情景资料；缺失标needs_review，不能武断判公司会破产。
- source存在、同publisher、重复复合fact都不等于独立支持。引用主张只支持数值的一部分时保留partial范围；不能靠多个相同来源票数解决矛盾。
- 周期低谷/困境反转的正常化假设应作为推断/观察触发条件，不把当期低数值判错，也不将未来条件认定已兑现。为投资海选标可信度/缺口，不机械删除暂时困难公司。

## 测试与交接

1. RED反例用独立评审的具体口径错误，记录预期类别及依据；不要写只镜像字符串实现的测试。
2. 单元成对：OCF冒FCF/正确常规FCF/未知维护capex；WC标签正确与错误；经营利润率与ROIC；季度vs年度、美元百万vs十亿、face债务vs账面值、分部vs合并、未来信息、同源复合重复；“可能”推断vs冒充事实；未知数据/冲突引用。
3. 集成只读T0/T1真实标准答案，至少重现两类口径问题和一类不应误杀的合理限定推断。预期来自冻结review，不把测试通过称新模型质量通过。原题/答案原hash保持。
4. 公开CLI E2E产findings及公开critic包；扫描输出树不能带reference/rubric/预期标签/模型策略，错误输入/已存在目录/路径逃逸原子失败，禁网外根写及finally清理。
5. 交 `docs/handoff/CLAIM-GUARD-04/`：规则覆盖/不覆盖、误报风险、如何注入原SDK、版本化新增规则方式、整体测试结果。只在此大节点审查，不加逐规则批准。
