# 三条线的明确交付接口

## 共同候选封套（1.0.0）

本批只交候选资料，不输出生产 DTO。每包在自己的 schemas/ 定义封闭 JSON schema：根 required 字段固定为 protocol、package_id、artifact_id、created_at_utc、information_cutoff、input_refs、records、limitations、qualification_granted。protocol 由卡指定；qualification_granted 恒 false。additionalProperties=false；扩展另升版本，保留旧版本样例/读取测试，不原地改同版本含义。

- input_refs：非空数组，严格 {path,sha256,bytes}，path 是冻结 IQS 相对路径，sha256 为 raw 文件 SHA。引用闭合于 inputs.lock.json；不得用 canonical hash冒充原字节摘要。
- artifact_id：`candidate_<包名小写>_<64hex>`，内容寻址，SHA 域为除 artifact_id/created_at_utc 外全部根内容的 JSON：UTF-8、ensure_ascii=False、sort_keys=True、separators=(',', ':')、allow_nan=False；数组顺序保留。这是候选 ID，不是生产 semantic hash。
- records 的 ID 全部使用本包前缀，不引用其他新包的产物。现有 question_ref 严格 {path,module_id,question_id,question_object_sha256}，question_object_sha256 按上述 canonical 算法摘要原问题对象全字段；facts.json 使用原问题自身 module_id。它仅证明引用的冻结对象，没有正式发布或资格含义。
- information_cutoff：CHAIN 固定 2026-10-13，事实公布日晚于该日不能当已知；ROUTE/SCORE 合成情景按各 record 的 as_of 核时点，封套 cutoff 同为 2026-10-13。访问时间与事实公开时间分开。
- 每例带 fixture_class=synthetic|public_source_reference、owner_mapping_status=not_mapped、production_execution=not_run。不能写 qualified/accepted/human_approved=true 或自签真实身份/证据等级。

records 必须有完整卡指定覆盖；多个候选文件可以同协议，但主 content 文件唯一。出错拒绝零正式输出；缺事实是合法 gap record，不能删题缩分母。

## CLI（每包薄工具，不代实现产品）

每包提供 `python -B -X utf8 -m <卡指定 module> validate --input <主content> --inputs-lock <本包复制的锁>`；`export` 同参数另加 `--output <新目录>`，额外只读依赖用明确参数。返回 0=候选有效，2=输入/引用/语义边界非法，3=输出已存在或超写范围；错误不得输出 traceback 中的私人内容或落半份正式文件。report固定 validation_scope=candidate_artifact_only。

工具复用冻结 IQS jsonschema/读写/题库入口和类型定义，引用数据时不复制第二题库。需要原产品运行的测试从自己的 fixtures/iqs 调用原公开 CLI，保留其真实输出；原产品遇到问题登记 known-product-gaps.json，不悄悄实现另一个路由/评分/查询器把它盖过去。

## 总控合入与版本演进

三包文件命名空间分别 RC02、CC02、SA02，各目录不重叠、没有相互依赖。总控收到三个增量以后按各自 baseline question_object_sha256 做 compare-and-swap：源对象变了就分类迁移提案或重核，不按最后写入者覆盖。建议改同一原题时分别保留提案 ID 和理由，由总控统一决策。

ROUTE→已有 C01 路由/模块回归；CHAIN→F03/F04/F05/F06 事实、关系及词表发布；SCORE→C02 评分尺候选及 B01/F05 盲评标准。以上是消费目的，不是由 Lab 发布/签收这些任务。没有真实 owner 接口的 E2E 标 not_run。具体质量与开工边界见各卡。

不把本批 handoff 模板或独立工具 exit0 当模型答案准确率。真实金融基准、评分尺发布、生产数据和用户白名单阈值仍由总控按原大节点完成。
