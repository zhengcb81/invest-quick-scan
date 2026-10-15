# AGENT-REF-02：三公司12题的独立参考事实与评分依据

**开工补充阅读：[实际owner题目投影](owner-alignment-addendum.md)。** 原36逻辑槽保留；区分通用构念与实际类型题，不把不同题/锚点当同义，不按Alphabet的经营企业变体推断证券公司。额外诊断原件仍不授oracle资格。

状态：准备完成，待用户派发。唯一可写根：`C:/Users/郑曾波/Projects/iqs-agent-reference-lab`，准备时不存在。外仓、其他包、冻结输入、总控PWF及真实库均只读；开工重新核唯一writer。

## 先读与任务定位

读[共同接口](integration-contract.md)、[固定36槽目标](AGENT-REF-02.targets.json)、[输入锁](inputs.lock.json)、[handoff模板](AGENT-REF-02.handoff.template.json)、[manifest](manifest.json)。截止、原题、身份限制、每fact/source字段及交接规则都在共同接口，不需要聊天补充。

目标是让总控能独立检查公司 agent 的**事实依据是否正确、评分是否有据**。现有FIN原件/1058事实/90null等保持，先复用核查与目标有关的来源；不重做90题、不把旧资料整理一遍冒新增参考。本包不看未来真实agent答案，不用待评模型写“标准答案”。

可使用harness自带搜索/浏览读取官方HTML或公告网页，记录访问，不读取任何项目API key，不直接调用收费LLM/Brave/Tavily/ZAI API。**不下载/保存财报、PDF、全文HTML或原始网页body。** 找不到可核网页时保留gap，不绕路下载。

## 交付结果

1. `content/reference-slice.json`，严格 `iqs.agent_reference_slice/1.0.0`，覆盖原36槽。原题hash/锚点保持，expected_score不造；所有qualification_granted=false。
2. `evidence-public/`：可供研究agent检索使用的短证据board（无预设分数、标准答案、盲评意见）。每条保留主体、期间、单位、来源/发布日期、短摘录/hash和限制。
3. `reference-private/`：逐槽独立审查依据、可验证子事实、可接受证据/反例、未证实项、评分锚点检查。不能交给模型作为context；与public证据有清楚目录及manifest边界。
4. `content/coverage.json`与`content/gaps.json`：36槽原分母，source_checked_candidate/partial/unverified/contradicted数量；事实资格与评分判断分列。没有证据的槽仍存在。
5. 可执行validate/export CLI、数据校验测试、来源核对原始记录与本包PWF/交接。工人核源不是生产oracle授权。

## 施工步骤

1. 按锁复制自己的fixtures并建立36槽总表。读原完整题干和锚点，逐题拆成少量可观察事实/定性判断/不适用条件；不改变问题意思。原FIN大量null保持不动，相关旧fact可引用原ID并显式记录复核差异。
2. 每家公司先确定研究法律名称/业务主体及ticker提示的对应依据，仍标research-only，不冒成StockWiki owner identity。中信建投A/H合并线索、Alphabet多股类等不能直接当额外公司。
3. 优先复用冻结官方来源线索，访问可核官方网页验证**具体主张**。核准发布日期和period、单位、会计口径；动态页面无可验证历史日期时不得推断截止前就存在。每条区分“发行人披露了X”与“独立证据证实X”，公司自述品牌强不能变成护城河事实。
4. 优先补最影响原12题判断的、可明确核验的子事实，例如收入/业务构成、历史经营趋势、客户/订单/复购证据、资本与负债约束、治理事件或业务变动。目标是每家公司先取得若干高价值事实，不为凑数堆重复宣传或强造每题一个唯一分数。
5. 同时列负面/相反证据及无法排除的解释。周期低谷与永久损害分开，旧经营优势/变化机会与当前低利润分开；不用低谷单项差直接宣布不值得关注。contradicted需要直接相反证据，缺资料不是contradicted。
6. 构建public证据与private参考两个出口，校验跨目录泄漏。每槽明确哪些事实可核、哪些判断有合理区间/不同解释、哪些需要未知，不评投资评级或估值。
7. 一次集中校验+CLI搬迁导出与人工来源抽核，交接真实完成/partial。若36槽多数无证据，要报告主要原因和最短补证方向；不能填模板句子、给来源URL就标supported，或删槽抬覆盖率。

## 验证标准

|类别|必须验证|
|---|---|
|来源实质|每source_checked_candidate指向具体支持句/表项且短摘录可查；相同source可能支持多fact，但不能循环引用自我支持|
|日期|发布日期晚于截止、发布日期unknown、仅访问时间、后更新动态网页均有拒绝/降级例；不能用网页当前版权年份当原公告日期|
|数字口径|亿元/十亿元、FY/自然年/半年、调整后/法定、经营现金/自由现金、存量/新增、计划/实绩，不默默换算；换算写原值/公式/单位|
|主体|同名异公司、中信建投集团/证券实体、A/H/ADR与母子公司/产品品牌混淆；仅ticker不能自授唯一身份|
|参考资格|独立核源候选、主观rubric、未验证和不适用分开；原分数null不补；候选不能进严格准确率oracle|
|分母与关联|36原槽不删，题目hash匹配，fact/source/gap引用完整，重复或陌生题拒绝；相关fact复用不膨胀独立证据数|
|轻资产|导出不含全文/下载文件/secret/模型思考；public证据不含private参考的结论或预期分数|
|便携CLI|从新根validate→export→移目录再次validate；修改源字节拒绝；已有输出/越界拒绝，只清自己临时文件|

单元测试覆盖数据规则，集成测试实际复用冻结原FIN校验/导出时调用其公开入口而不是mock“成功”；若原候选验证通过，只能报告软件结果，不自动授金融内容资格。来源核查要真访问，不能全用mock代替；访问失败记录，保留partial是合法结果。

## 待实现公开命令

```powershell
python -B -X utf8 -m iqs_agent_reference_lab validate --input content/reference-slice.json --targets fixtures/experiment-targets.json --input-root .
python -B -X utf8 -m iqs_agent_reference_lab export --input content/reference-slice.json --mode public-evidence --output runs/new-public
python -B -X utf8 -m iqs_agent_reference_lab export --input content/reference-slice.json --mode private-reference --output runs/new-private
python -B -X utf8 -m pytest -q
```

入口需实现，提供免安装launcher或README显式src路径方法。0=工件合法，可合法含partial；2=输入/hash/协议错；3=输出冲突/路径不安全。合法工件不等于内容全部支持；coverage报告必须显示真缺口。不要为CLI exit0伪造证据。

## 交接重点

按共同接口交 `docs/handoff/AGENT-REF-02/`，另附：

- `source-verification.jsonl`：访问URL、UTC、当时核到的主张/日期依据、成功/失败/未证实与短摘录hash；不存全文，不将source条数冒HTTP次数。
- 36槽覆盖矩阵、与旧fact/来源的复用及新增差异；原FIN原件rawSHA保持证明。
- 可直接给RUN的public短证据包，以及独立保管private参考的明确路径/manifest；不能等待RUN答案才改参考。
- 总控签收时必须复核的有限问题清单，不把每条事实增设审批门。参考资格仍待一次整包实质核验。

只在本新根正常提交；不改正式题库、StockWiki、company-wiki或任何外部Lab，不直接推远端。公开handoff形状校验见共同接口。
