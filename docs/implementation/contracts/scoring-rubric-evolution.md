# V02：独立评分尺候选与兼容边界

2026-10-01。实现状态为 `local_candidate_implemented`；不激活生产评分尺，不关闭G3、V02任务依赖门或StockWiki历史重算验收。没有数据库、提供商调用或下载依赖。

## 发布与输入

候选归档：`questions/scoring-rubrics/rubrel_1ae5bfbf4c63bb197bde53d9058ca50ff631aae1a9525e0ec8578f4495379d02.json`。
文件字节SHA-256：`88af96451741a8fcdd1b69d07d4de21c665c549c2d077aa6866f2d74fa9909ae`。
候选来自已发布模块包 `pkg_24f07923f23cf0a2be5d7fb4b36a11925c779a8f4a68bdc9c81457084ded080f` / `modrel_18c097b26b82746d3b48d9f2da4858a15ce216bce39c2572d10c2dcef23d32b9` 的common模块；24题定义逐题按共享canonical JSON散列绑定。`calibration_sample_refs=[]`，没有真实公司校准，不承诺跨行业排序有效。

`schemas/quick_scan/scoring-rubric.schema.json`定义Release、Snapshot、Row。Release独立记录method、版本、cohort、有效区间、权重、覆盖阈值、核心替代篮子、附加关键风险和校准引用。默认经营类候选继承原六维质量权重20/20/15/20/15/10，维度覆盖率至少0.7、质量覆盖率至少0.8，质量18项；成长/估值各3项单列。银行等必须另发绑定其替代问题及cohort的评分尺，不能套用经营类候选。

Snapshot是**调用方已认证、已校验观察的投影**，不是新的C03答案格式。每条投影带原observation ID/hash、定义/实际题义hash、主体/挂牌作用层、期间、信息截止日、provider/model/config、状态、置信度、check level与其receipt、freshness。调用方负责查验真实StockWiki观察内容hash、check receipt及身份；本模块不凭自声明字段授予等级。来源hash与派生hash只证明一致性，不证明来源可信。V08/StockWiki接线之前不可把CLI自述数据直接用于生产白名单。

## 公开API

`scripts/scoring_rubrics.py`复用`module_contract.canonical_bytes/digest`，不导入数据库/模型/上层调度器。

- `seal_rubric(body)`：确定性候选内容寻址；不维护active指针。核心构念严格IQS_01—24、每项唯一且原维度不变，权重总和100、严格整数。附加关键项不增加核心分母。
- `validate_upgrade(old,new)`：显式supersedes；同method只允许不改变评分含义的递增版本。权重、篮子、阈值、cohort或等级门槛改变须使用新method。实际发布者仍需验升级关系，不以seal代替验升级。
- `load_rubric(path,expected_sha256,expected_release_id)`：读取不超过1MiB的精确字节；拒绝重复JSON key、非有限值、hash/ID不符；历史读取不受当前有效期限制。
- `aggregate(rubric,snapshot,expected_snapshot_sha256,at)`：API使用canonical Snapshot hash，`at`显式UTC且在评分尺半开有效区间内。生成新的derived ID、原观察引用、分母、覆盖率、不可用理由和关键风险。无写入、无LLM请求，不改变原始回答或旧白名单。历史评分尺若过期可读取，重放须明确选择当时有效的派生时间；生产活动发布资格由V16另管。
- `compare(...,axis='time'|'company'|'model')`：重新生成两边派生值并检查评分含义、题义、作用层、期间、模型配置和已答篮子。company轴允许不同issuer/scope ID，但作用层口径和截止日仍须相同；time轴允许截止日递进，但期间仍要求一致。model轴保留两边带模型标记的输出；不同模型配置报incomparable，不自动生成数值趋势。变化8分与原8分不能因此生成伪零变化。未知、关键风险缺题或低覆盖时quality为null，不把null作0。
- `rule_input(derived,expected_method_id,expected_release_id)`：验证派生hash及精确method/release绑定，返回usable或unavailable；不是规则引擎或信任认证器。新method分数不能自动输入旧规则。

只有status=scored、严格1—10整数、足够check level/receipt、非低置信度、fresh且比较轴完整的回答可计分。unknown/search_unavailable/insufficient_evidence中的原8分被忽略；诊断题10分不能抬高核心。N/A需`screening_audited`或更高且经审计才可从适用分母排除；关键风险N/A仍阻断质量分。固定IQS_12/13/16、评分尺附加关键项及输入追加critical都不能平均掉或取消。混合主体口径和重复构念/观察直接拒绝。

## CLI与测试

CLI读两个外部文件，要求**文件字节**SHA；API的Snapshot参数要求**canonical内容**SHA，两种口径不能混用。stdout是派生JSON；输入失败输出固定`scoring_rubric_input_invalid`并退出2。CLI不写结果文件。

```powershell
python -B -X utf8 scripts/scoring_rubrics.py aggregate --rubric <release.json> --rubric-sha256 <byte-sha256> --release-id <rubrel_id> --snapshot <caller-validated-projection.json> --snapshot-sha256 <byte-sha256> --at 2026-10-01T12:00:00Z
python -B -X utf8 -m pytest -q -p no:cacheprovider -o addopts= tests/test_scoring_rubrics.py tests/test_scoring_and_rules_contract.py tests/test_metrics_contract.py tests/test_implementation_plan.py tests/test_parallel_lane_plan.py
```

EVO-05—07本地正反例涵盖权重并列派生、来源不变、未知8/诊断10、题义/期间/作用层/模型不齐、关键风险、NA门槛、严格类型、替代构念、真实归档和隔离公开CLI。CLI subprocess清除API/live环境变量，在临时目录执行，退出后验证目录被删除；没有真实公司扫描或付费请求。RED/GREEN日志和独立审查报告同目录留档。G3校准、生产caller认证、StockWiki不可变持久化/CAS/历史重算和V16活动资格仍需后续owner实施验收。
