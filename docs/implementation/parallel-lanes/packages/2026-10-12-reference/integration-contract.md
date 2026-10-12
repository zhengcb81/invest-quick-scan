# 接口和总控合并契约

## 唯一数据格式

各包交原FIN协议iqs.financial_reference_pack/1.1.0与iqs.calculation_ledger/1.0.0，schema来自冻结commit1e7d617。CLI修复声明1.4.1，pyproject包版本1.0.0，两者不要混写。**不发明新的Observation/身份/评分协议，也不复制一套FIN校验器。** 各候选仍90行，自己公司30行允许变化，另一60行按canonical JSON摘要与原件逐行相等，不把三个候选270行相加。

Canonical row hash：UTF-8 json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)的SHA256。targets.json已给每行baseline hash和绑定字段；pack_id按原compute_pack_id算法，不用此row算法替换。固定reference_id/question_id/text SHA/manifest SHA/metric_id/rubric/scope要求/公司清单/原inputs不得改变；不重新路由/改题/自行补owner ID。top-level允许pack_id、created_at、research_summary与明确追加的研究limitations更新；inputs/companies/protocol保留，review_status仍按实际未独立金融认证记录。

来源：baseline全部Source记录和其ID保持对象内容不变，不给旧source换URL/发行人/日期。新增ID使用包专属命名空间：Alphabet SRC-RFA-* / FACT-RFA-* / CALC-RFA-*；CATL RFC，CSC RFS。旧目标行事实若需要纠错，在changes.md列旧事实/row hash、证据、替代事实；用新ID记录新事实版本并更新本公司引用，不静默覆盖旧fact ID含义。新增source只绑定本company_key；官方网页同源可一题或多题引用，实际contains哪条claim须逐条说明。保留冲突与旧事实撤销原因，不删除坏消息。别包新增IDs不能引用。

账：原calculation-ledger所有非本公司Entry保持canonical摘要；Entry.reference_ids按base reference→company映射判断范围，含混合公司拒。本公司旧Entry如受纠错影响，可在本公司候选替换同calc_id的内容，但changes.md记录expected旧entry hash、原因/新值/证据；不得改别公司。新Entry使用专属CALC前缀，不跨公司绑定。期初/期末/币种/单位/economic_role受原公开validator约束；CURATED角色不是金融真值。metric只用已登记且题义适用的方法，不新增公式注册或用金融业ROE冒充工业ROIC。未登记方法的独立手工复算写calc-notes.md并附官方fact，不包装成computed ledger entry；不可算则合法insufficient_evidence/not_applicable，不造分母。

research_summary必须按原compute_research_summary从完整90行重算；仅统计本地候选真实研究，另外60不凭自己的工作改成done。19旧访问摘要单独baseline retained；追加本公司实际访问短记录，不声称writer日志是独立已验证访问。created_at记录候选实际生成UTC；总控合并时用自己的merge UTC。所有未评分维持null；proposed区间必须实际证据充分，不自签accepted。

冻结函数的actual_source_consultations是被attempt引用的唯一Source ID数，不是HTTP访问次数；source_verification_attempts是逐题attempt条数。保留这两个旧字段的算法，实际网页访问次数/去重页数/复用题数另附访问摘要，不改schema字段口径或编次数。

## 工作者公开校验路径

工作根W，冻结依赖在W/fixtures/fin。设置PYTHONPATH=W/fixtures/fin/src和去key测试环境/TEMP=W/runs/<isolated>。不能pip install到原FIN或直接从外仓私有sys.path导入。

```powershell
$workerRoot = '本卡唯一新根绝对路径'
$env:PYTHONPATH = Join-Path $workerRoot 'fixtures/fin/src'
python -B -X utf8 -m iqs_financial_reference_lab validate --input "$workerRoot/content/reference-pack.json" --inputs-lock "$workerRoot/fixtures/fin/fixtures/inputs.lock.json" --ledger "$workerRoot/content/calculation-ledger.json"
python -B -X utf8 -m iqs_financial_reference_lab export --input "$workerRoot/content/reference-pack.json" --inputs-lock "$workerRoot/fixtures/fin/fixtures/inputs.lock.json" --ledger "$workerRoot/content/calculation-ledger.json" --output "$workerRoot/runs/export-one-shot"
```

上述环境示意不是完整去key控制器；真正测试用allowlist child env并在退出还原自己的环境。validate 0合法/2坏输入；export 0新输出/2拒发布/3已有目录。从随机cwd和中文空格目录复跑；拒坏输入不留正式输出，已有目录不覆盖。每文件5MiB及32MiB累计限保持。依赖文件39份SHA始终不变，工具只产生自己的content/runs/reports。

## 总控合并（ worker不能代写原FIN）

1. 三包可任意顺序交回，无互相等待。核实际Git/基线39hash/30题绑定/另外60hash、source与calc命名空间及证据范围/费用与cleanup，不用handoff shape自签事实。
2. 提取每包**自身30行**及其专属新Source/本公司ledger替换与新增；不给外公司候选覆盖权。若原FIN在编制后前进，按base row/source/entry hash做三方冲突检查；已变记录转人工比对，禁止last-writer-wins或回滚新源仓。
3. 无冲突输入与基线合并：reference顺序沿原90位置，Source/Entry用稳定ID顺序；最终pack_id/research_summary按owner算法重算，created_at统一总控本次merge时点。以固定merge时点检验A+B/C+B+A得到同样canonical内容；不同真实时间不能拿字节差异误判逻辑不交换。
4. 对完整候选只做一个集中public validate/export＋包级事实/反证核查；需修复由总控直接做。软件通过仍不是金融事实全对或评级可用。独立事实→评分后才接B01比较，保持原30分母/难题/弃答及成本。
5. 原FIN的schema/历史handoff/冻结锁不被worker改写；只有总控正常精确源码/数据提交可更新它。不写StockWiki/company-wiki、生产库、名单或再造永久公司存储。各工作根是可归档研究材料，不是第二数据权威。

## 交接预检

使用同名handoff.template.json，公开handoff1.0.0。将package-id与自己文件替换：

```powershell
python -B -X utf8 C:/Users/郑曾波/Projects/invest-quick-scan/scripts/parallel_handoff_cli.py --catalog C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-12-reference/manifest.json --package-id FIN-ALPHABET-02 --input C:/Users/郑曾波/Projects/iqs-reference-alphabet-lab/docs/handoff/FIN-ALPHABET-02/handoff.json
```

该预检只证明shape与声明范围；它不检查网页真伪、真实owner或金融准确性，也不授权发布。真实commit/hash/逐题coverage、原测试日志、研究/软件两种review和未完成项必须随交接供总控复核。
