# AGENT-EVAL-02：ResearchRun真实输入盲评桥与三策略比较

**开工补充阅读：[实际owner题目投影](owner-alignment-addendum.md)。** 原12逻辑槽与Run实际qid通过显式sidecar映射，raw12与routed12-v1变体分组，不能改原答案题号或混算不同语义。公共Run1.1不改，其他两公司实际投影未提供时保留未决。

状态：准备完成，待用户派发。唯一可写根：`C:/Users/郑曾波/Projects/iqs-agent-evaluation-lab`，准备时不存在，开工重查归属。任何源仓、RUN/REF新根、共享快照、总控PWF及生产数据均只读。

## 先读与已有成果

读[共同接口](integration-contract.md)、[固定目标](AGENT-EVAL-02.targets.json)、[输入锁](inputs.lock.json)、[handoff模板](AGENT-EVAL-02.handoff.template.json)、[manifest](manifest.json)。完整3公司/12题、时间截止和交接约束都已冻结。

原BLIND-INPUT桥支持Observation1.2和显式wrapper，不支持ResearchRun；不要猜成现有格式或重造盲评系统。原Company0.2.0输出ResearchRun1.1，原FIN90分数null/事实资格0保持。S0已真实跑通信与缓存，它的合成记录题不是公司答案，不能塞进公司准确率。

本包默认keyless/禁网，不发真实LLM/搜索、不看未来RUN/REF私有目录。用冻结真实S0安全回执检验计量边界时只作技术数据；实际公司完整输入尚未提供则用明确合成fixture测试。真正公司准确率由总控接收真实Run与核源参考后计算，不能伪造真实正例。

## 交付目标

1. `iqs_agent_evaluation_lab` 显式读取ResearchRun1.1及其原题、原answer_content、evidence board、events/metrics file_refs，生成既有盲评原生公开输入和私有映射。公共盲评字段严格复用冻结blind-review schema，不私加模型/策略/费用泄露身份。
2. 支持共同接口 `iqs.agent_reference_slice/1.0.0` 的**候选参考导入**；事实核源状态与总控资格分开，未签收时不能升成oracle。不能把REF的候选标记当已通过金融审查。
3. `content/evaluation-bundle.json`，protocol=`iqs.agent_evaluation_bundle/1.0.0`：原件refs、每原slot的适配与失败ledger、盲评产物refs、合格/未资格参考计量、费用/时间/cache与限制。
4. 三策略配对报告：质量→合格回答成本→墙钟，保留失败与样本依赖。不强选赢家、不用完整率/一致率替代准确率，不凭三家公司证明总体不劣。

## 分步实施

1. 初始化自己PWF/仓，按锁复制Company schemas/样例、BLIND原公开代码及依赖。先列真实ResearchRun1.1全部slot状态→既有blind状态桶映射；未知未来/未声明格式拒绝，不能写一个“任意JSON都能读”的万能adapter。
2. 先做失败用例：原题hash不符、answer_sidecar漂移、company/cutoff不符、回答缺题/重复题、失败请求没有answer、原件缺失。通过原原件/副本校验把合法值映射进去，不重写原答案理由/分数。
3. 实现ResearchRun适配，保存原题/答案/证据/修订链的安全hash/ref。私有映射可记录模型/策略/attempt关联，但不保存hidden reasoning正文；公开6字段盲评输入复用原校验入口。
4. 参考桥只接明确声明的reference-slice1.0。每fact是否可计入客观准确率要有独立资格来源；caller纯填true不授资格。资格缺失时输出not_qualified/null与明确分母，不把软件契约通过当金融gold。rubric判断另列人工/独立审查，不设唯一分数oracle。
5. 实现配对汇总：S1同证据和S2自主检索分开；同公司/同题/同模型/同阶段/重复/策略键明确，不把相关重问当新独立样本。新模型分支单列，已拒绝模型仍保留原槽和费用。
6. 成本从实际first-party物理attempt计一次；失败/补问/预热/复核/搜索都保留。现金、套餐消耗、公开价估算、未知预留分列，币种不硬加总。cache缺失null、本地cache与供应商KV分列。wall采用实际run/segment记录，不能相加请求时长冒并行墙钟，修复/排队等待按真实时间显式呈现。
7. 一次集中测试、搬迁和公开CLI全链，产出最小replay-pack；它不依赖另两个新包文件存在。收到未来真实Run时只换显式输入，不改算法/过滤规则去挑好结果。

## 实质测试包

|类别|必须证明|
|---|---|
|真实代码复用|Company原ResearchRun1.1验证→本桥→原BLIND公开validator/report，不能mock三个步骤都成功；合法partial能导出完整适配ledger|
|答案状态|answered/insufficient/refusal/unparsed/missing/no-send/search-failure/timeout/unknown等按实际schema映射；任何失败不能变answered，36槽/单公司12槽保持|
|原件|漂移hash、重复JSON key、陌生question、错误period/company、缺board/events、移动根后读回源；均拒绝或按原协议明确partial，不悄悄修答案|
|模型盲化|公共输入不含model/strategy/provider/cost；私有映射含正确绑定但无思考；同answer_id不同attempt不会碰撞，冲突同attempt不算独立样本|
|参考资格|已核源候选但无总控资格→not_qualified/null；unknown不记0；主观rubric不进事实准确率；合成正例明确synthetic不当金融证明|
|物理计量|一个响应答3题只计一次费；同ref重放不双计、相同内容不同真实attempt都计；reasoning已在output不双算；缺cache/报价/套餐费用保持unknown|
|速度|两并行请求、串行补问、跨segment暂停、UTC不一致；wall/请求和分列，无法可靠重建wall保持unknown而非负数或0|
|实验比较|2合成公司×12题×3策略，严重错误优先于便宜/快；固定包可胜/无胜者/证据不足均合法；失败公司不从分母剔除|
|轻资产与便携|无网络/key读取、无新预算库、无文档下载；路径/链接/已有输出拒绝；公开CLI搬迁可复现，清理自己临时文件|

若需要新增ResearchRun识别分支，优先自己包装既有BLIND接口；上游patch只能在本根的候选副本中给出baseSHA/afterSHA，不改原Lab，更不改RUN的Company schema。新增载体显式新版本，历史例不重签。

## 待实现公开命令

```powershell
python -B -X utf8 -m iqs_agent_evaluation_lab adapt --run fixtures/scenarios/research-run-v1.1.json --input-root fixtures --output runs/new-adapt
python -B -X utf8 -m iqs_agent_evaluation_lab compare --matrix fixtures/scenarios/three-strategy-matrix.json --input-root fixtures --output runs/new-compare
python -B -X utf8 -m iqs_agent_evaluation_lab validate --input content/evaluation-bundle.json --input-root .
python -B -X utf8 -m pytest -q
```

入口需实现并给免安装/显式src调用方式。0=工件合法/比较可读，可以含合法partial；2=格式/锁/版本错；3=输出冲突/路径错。报告必须显式标准确性是否有资格；exit0绝不表示准确率通过。

## 交接重点

`docs/handoff/AGENT-EVAL-02/` 按共同接口交真实commit、命令/PID/日志、artifact refs、cleanup，另附：

- 全状态映射表、原Company schema与原BLIND入口对应、每原slot去向。
- 公共盲评与私有关联样例，两者边界及反例；原答案保持证明。
- 质量/费用/速度/cache公式、未知处理、实际分母、数据资格来源；对单公司与三公司同一口径。
- 能由总控直接传真实Run1.1/已核参考的最短命令；研究格式或资格不足应清楚拒绝，不需继续改工程才可运行。

正常本地提交，不推新远端、不写其他包，不把本卡变成新LLM裁判系统或自己的金融评分模型。公开交接形状校验见共同接口。
