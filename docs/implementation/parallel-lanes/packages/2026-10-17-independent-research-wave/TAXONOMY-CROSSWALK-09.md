# TAXONOMY-CROSSWALK-09｜三市场官方行业分类的版本化交叉映射

**目的**：为未来跨A股、港股、美股检索行业和产业链主题准备一个有版本、可追溯的行业分类映射样机。只映射“分类体系中的类别”，不把代码自动贴到任何上市公司，也不把官方产业类别冒充投资主题。

**唯一可写根**：`C:/Users/郑曾波/Projects/iqs-taxonomy-crosswalk-lab/`。不得改 IQS 题库/路由、StockWiki 主档/公司池、行业研究或主题技能。没有本卡与共同契约锁定的文件不可读；所有实现/测试/handoff只在该Lab。

本包锁必须把四个官方分类来源的准确版本/允许用途列入 `external_sources`；只锁本波次文档，不需读取 StockWiki 公司清单。访问/许可限制导致某体系无法形成足量映射时，精确报告 `blocked`/覆盖缺口，不把非官方分类补进去。

## 指定范围与可信来源

以当前可公开核对的官方分类为输入，开工时重新确认修订状态与使用条款：

- 中国：证监会《上市公司行业分类指引》（2012年修订），[证监会原文](https://www.csrc.gov.cn/csrc/c101864/c1024632/content.shtml)。如官方已发布取代版本，使用实际现行版本并把旧版留作历史，不自行猜测。
- 香港：政府统计处 HSIC Version 2.0，[官方分类页面](https://www.censtatd.gov.hk/en/page_698.html)。此分类针对经济单位/主要经济活动，不等于港交所或恒生公司逐户分类。若研究者希望使用HSICS/CSIC上市公司分类，先核实许可；没有明确可复用授权时不得抓取或重新发布该商业分类，报告缺口即可。
- 美国：SEC EDGAR SIC代码表 [SEC官方表](https://www.sec.gov/search-filings/standard-industrial-classification-sic-code-list) 和 Census NAICS [Census官方目录](https://www.census.gov/naics/)。截至2026-10-17，该目录提供2022版并列有2027更新提案的征求意见公告；提案不是生效分类。开工时再查当前状态，记录适用日期并保留历史版本。SIC与NAICS用于不同目的，不假定一一等价。

官方网站可以用于查阅；完整手册/证券文件不得下载或复制进Lab。产物仅含必要的代码、类别名称、版本、短定义/自写释义和出处定位。记录许可/可复用限制。不要使用付费GICS、未经许可的数据库导出或搜索引擎结果页当正式taxonomy。

## 具体交付与数据接口

在`releases/<semver>/`下交付四件不可变版本文件：`canonical-industry-tree.json`、`source-taxonomies.jsonl`、`crosswalk.jsonl`、`coverage-report.json`，加一个可运行只读CLI和`manifest.json`。必须逐文件遵循本卡包的[`canonical-industry-tree.schema.json`](schemas/canonical-industry-tree.schema.json)、[`source-taxonomy-row.schema.json`](schemas/source-taxonomy-row.schema.json)、[`crosswalk-row.schema.json`](schemas/crosswalk-row.schema.json)、[`coverage-report.schema.json`](schemas/coverage-report.schema.json)；`validate`与`map`成功输出遵循[`taxonomy-cli-success.schema.json`](schemas/taxonomy-cli-success.schema.json)，manifest遵循[`taxonomy-release-manifest.schema.json`](schemas/taxonomy-release-manifest.schema.json)。Manifest恰好登记四个release文件，路径和role固定配对；每项的`bytes`是实际文件字节数，`sha256`是写入release后的原始字节SHA-256。Manifest本身不登记在`files`里；CLI返回的`manifest_sha256`是`manifest.json`原始字节SHA-256。JSON文件UTF-8无BOM，JSONL为UTF-8无BOM、每行单个JSON对象、LF换行；文件hash不做换行规范化。

`canonical-industry-tree.json` 至少提供二至三级中性行业节点，中文/英文名称、稳定 `industry_id`、`parent_id`、有效起止日和定义。`level=1`明确定义为广义行业门类，至少30个一级门类；每个非根节点必须有同一版本中有效的上级，且至少存在一个二级节点。门类应能够容纳金融、消费、医疗、软件/IT、半导体/电子、材料/化工、机械、能源、运输、地产、公用事业及其他/未归类。别名必须是同义分类标签，不混入关键词集合或公司名。所有JSON/JSONL行均须通过随卡 schema（`additionalProperties:false`）；跨行唯一性、父子关系、无环和日期一致性由CLI做语义校验。release使用不可变semver快照，版本升级新增文件，不原地覆盖旧release。

`source-taxonomies.jsonl` 每行包含schema所列字段。仅当该最小分类代码项可合法留存/复用时，才能写入一行，此时`reuse_status`固定为`public_reuse_allowed`；许可未知、view-only或不允许复用的内容不得抄入行，改在coverage gap记录官方来源、限制和缺项。至少覆盖CSRC、HSIC、SEC SIC和NAICS；不得把中国行业分类规则和统计分类语义说成相同。`source_sha256`必须是该代码项所据官方发布物/官方网页表格行的最小可复取源字节单元SHA-256；`source_locator`指明页码/表名/行或官方代码URL。若无法定义合法、稳定的原始字节单元，该代码不得进入映射样本，须记入coverage gap；不得对自行转录行做哈希冒称来源hash。

`crosswalk.jsonl` 每条包含schema所列字段。`mapping_relation`方向固定以source相对canonical target描述：`source_broader_than_target`表示source类别范围更宽、target只覆盖其中一部分；`source_narrower_than_target`表示source类别范围更窄、target为其上位类；`partial`表示边界或语义只部分重合；`ambiguous`表示依据不足以选定可靠关系，targets可列候选或为空；`unmapped`表示无合适target且targets必须为空；`exact`表示含义和粒度一致。`mapping_confidence`为0至1的主观映射置信度，不是统计概率；`reviewer_status`只能为`unreviewed|reviewed_supported|disputed`，不得在缺独立逐行复核时标`reviewed_supported`。允许一对多、未映射和需要人工复核。严禁强迫一一对应或给含糊代码高置信度。

`coverage-report.json`至少各含一项`CSRC_LISTED_COMPANY`、`HK_HSIC`、`US_SEC_SIC`和`US_NAICS`；保留历史版本时允许同一体系有多个version row。`sampled_fraction_of_official`是抽样代码数/该版官方代码总数（官方分母不可得时为null）；`mapped_fraction_of_sample`是样本内mapped代码数/抽样代码数（样本数为0时为null）。`coverage_state`表示官方分类目录能否完整核对：`complete`需全量目录及分母可用；`partial`必须说明缺口；`not_available`表示无法合法取得/核对，此时official总数和sampled比例为null。该报告不代表上市公司市场覆盖率，也不能从类别抽样推断公司归类准确率。

Schema只验证单个JSON对象的形状；CLI `validate`必须再对整个release执行下列跨文件语义校验，并在单元/集成/E2E测试中用故意矛盾的真实结构反例验证拒绝：

- 每个源代码样本的唯一键为`(source_taxonomy_id, source_version, source_code)`，`source-taxonomies.jsonl`和`crosswalk.jsonl`中均不得重复。每个源样本在同一不可变release内必须恰有一条crosswalk记录；未映射或证据不足也要显式记录`unmapped`/`ambiguous`。同一源代码映射改变须发布新semver或新来源版本，不在一个release内用重叠/多条期间记录表达。
- 每条crosswalk顶层的`source_taxonomy_id/source_version/source_code`必须逐字段等于`evidence_ref`中的同名字段；该完整三元组必须解析到唯一source-taxonomy样本，且`evidence_ref.source_sha256`必须逐字节等于该样本的`source_sha256`。孤儿、跨体系、错版本、错代码或错hash均拒绝。
- 每个`coverage-report.sources`中的`(source_taxonomy_id, source_version)`必须唯一，并对应source-taxonomy样本集合。`sampled_codes`等于该集合的唯一source_code数量；`mapped_codes`、`ambiguous_codes`、`unmapped_codes`按上述每个样本的唯一crosswalk行分类精确重算，三者之和必须等于`sampled_codes`。不能只校验每个计数字段都非负。
- `mapped_fraction_of_sample`必须等于`mapped_codes / sampled_codes`；样本为0时必须为null。已知`official_total_codes > 0`时`sampled_codes`不得超过分母，`sampled_fraction_of_official`必须等于`sampled_codes / official_total_codes`；分母未知或为0时比例必须为null。`coverage_state=complete`还要求分母已知且`sampled_codes=official_total_codes`、抽样比例为1；其他不完整状态不得伪报complete。浮点输出与重算值的绝对误差至多`1e-9`。

CLI入口及行为固定如下，测试和交接命令必须原样包含：

```text
python -m iqs_taxonomy_crosswalk validate --release <release-dir>
python -m iqs_taxonomy_crosswalk map --release <release-dir> --taxonomy <id> --version <version> --code <code> --as-of YYYY-MM-DD
python -m iqs_taxonomy_crosswalk coverage --release <release-dir>
```

三条命令成功时stdout只输出单个UTF-8 JSON对象并以LF结尾，诊断写stderr；成功exit 0。`validate`输出固定字段`status:"valid", release_id, files_checked[], manifest_sha256`。`map`输出固定字段`status, taxonomy_id, source_version, source_code, as_of, mappings[]`；每条mapping仅含schema指定字段。status只能为`mapped|ambiguous|unmapped`；只有该版本确有source code但无映射时返回`unmapped`并exit 0。未知source code、taxonomy/version、日期或参数格式错误、schema/引用完整性失败均写stderr且exit 2，不写stdout；意外内部错误exit 3。`coverage`直接输出符合`coverage-report.schema.json`的对象，不联网且只读release内冻结文件。所有命令只读，不自动修复或改写release。

项目自定义主题标签必须与官方行业树分开，不能从“半导体/电子行业”自动推断“AI受益”“AI硬件”“中国替代”等投资主题。主题标签的未来实现由单独版本化本体和事实证据驱动，本包不新增主题标签表。

## 样本、测试与完成条件

做不小于每套体系20个有效代码的可追溯小样本，并覆盖至少30个canonical节点；这只是映射样机，不宣称覆盖全市场。对完整代码总量能合法取得时，记录官方覆盖分母和本次纳入比例；受许可或接口限制的代码不伪造缺失数据。用固定人工review员核对每个mapping的来源定位、父子关系、日期和多对多合理性。

必须覆盖以下反例：相同标签/不同含义；一个源代码覆盖多个本体节点；多个细分代码折叠到同一宽类；没有对应项；分类版本升级/代码退役；同名公司（本包不应出现任何公司归属）；公司多业务不能靠主要行业分类推断每个业务分部；行业标签不能推出主题标签；许可未知/不允许复用；有效日期边界。

单元测试验证schema closure、至少30个`level=1`门类、至少一个有效二级节点、跨行稳定ID、父子无环、有效期采用`[valid_from, valid_to)`半开区间、映射两端版本存在、confidence/reviewer状态一致、未映射必须说明、主题/issuer assignment字段拒绝、CLI exit/output契约。必须含跨记录负例：coverage计数不守恒、`mapped_codes > sampled_codes`、mapped比例错误、已知official分母下sampled超过总量、`complete`但抽样不到全量、孤立coverage体系/版本；crosswalk根字段与evidence_ref三元组任一字段不同、source hash不同、证据指向另一体系/版本/代码、缺source记录、source样本无crosswalk行、重复源键。覆盖率必须从唯一源样本及唯一crosswalk状态重算，不能只验证声明值通过JSON Schema。coverage validator必须覆盖四个指定体系，可增加历史版本但不能漏掉当期体系。集成测试使用真实纳入的分类代码。端到端测试从冻结源记录运行公开CLI并得到字节稳定的输出；脏版本/未知代码必须非零退出或明确`unmapped`，不能静默放入`other`。

验收交付：覆盖/缺口报告、逐条映射出处、可复跑命令与固定随机性、许可证/来源说明、schema/测试、SHA manifest、隔离清理、独立审查证据。任何无法核证的条目明确 `ambiguous`/`unmapped`，不为达到覆盖率改答案。
