# FIN-REF-01-R1 集中续验：保留修复，四组仍需收口

2026-10-11，结论 `changes_requested`。本轮有真实进步：CATL官方headline facts、Alphabet部分债务/NOPAT口径、旧25项拒收与零分子控制已修好；但研究完成声明与实际材料不符，绑定/计算仍有边界绕过，公开交接未通过。只续 [原包唯一R2](FIN-REF-01-R2.md)，不重写已绿部分，不另开小节点审查。

## 交付与冻结

- 唯一Lab `C:/Users/郑曾波/Projects/iqs-financial-reference-lab`，分支 `codex/fin-ref-01`。基线 `b5852aac5978a268dc4dd2eb795663c69b3ab9ca`，产品 `601be8b14abc603a51e9558d5928ae6d2679ea36`，交接便笺记录 `304633362c2dc21521b8f9c2889737c3212ba7dd`，实际终态 HEAD `655e9069e6bdffef1f5dbcfe243d74a8c100db39`。产品为实际HEAD祖先，无remote。
- 84个跟踪原件和20个FIN输入锁匹配；旧schema及原交接原字节不变。新交接29工件均在本机按bytes/raw SHA匹配，其中5个日志/输出manifest被 `logs/` 忽略、不在Git，另行只读冻结；不是5个源文件丢失，也不能声称它们可从交接commit恢复。
- 实际Git产品差异多出未列入 changed_paths 的 `tools/gen_artifacts_remediation.py`；artifacts与commit便笺两项交接元数据也未逐项列出。新交接worktree manifest字段为null，不构造不存在的状态hash。
- 新pack协议1.1.0、ledger仍1.0.0；旧1.0schema保留，但当前CLI只有1.1读取路径。新pack raw SHA `abbd7ecae6ffc8d69a3c29ed1ba424d8fda690ffeacef06795f69897b6918525`，pack_id `frpack_d330fa0b09345d25ad21ff0f2945122484a74c3cb24207959804c485a72f83b6`。交接source-attempts raw SHA `420b2f81ce5213e27982b615cdeba824f5b74832600fbd1c905961b7ec6d1697`。

本机验收根 `C:/Users/郑曾波/Projects/invest-quick-scan/runs/fin-r1-acceptance-2026-10-11-01` 保留snapshot、artifact-presence/delivery-content/git-delivery核对、原始进程和日志SHA、控制器、小合成反例与完整冻结副本。总控未写Lab或其PWF。

## 实际测试

| 验证 | 实际结果 |
| --- | --- |
| 原完整pytest | PID46032，exit0，58P，9.6072807秒；stdout SHA `f755ef6a12b4ff24bb454649a5b3118b326c84db77c29c14d273e79683cd80c5`，stderr为空 |
| 旧25独立控制，validate与export均实际执行 | 25/25符合预期；错hash/题集/来源/日期/区间/账值、根array/null/重复JSON/NaN均拒收；一致零分子正例通过。共50次公开CLI，不以原单元测试代替 |
| 同原根因12补验 | 2正常拒收控制符合，10不符合（下表）；24次公开CLI。修改后的pack正确重算内容摘要、账的pack_id同步，不用错误hash制造假阳性 |
| 读取计数观测 | 原CLI对5,583,067-byte合成JSON（只加空白）调用一次 `read(-1)`，exit0；证明无读取边界，不虚构某个已发布大小阈值 |
| IQS公开handoff CLI | PID23892，exit2，`temporary_root_not_cleaned`；stdout SHA `ed3bdfae32c031d1677380563128b878674b601d6bcda86b19b8745b2c3aae0d` |
| 一次独立官方事实审查 | [独立记录](FIN-REF-01-R1-independent-review.md)：研究占位与旧财务推理未同步；保留CATL headline及正确算术，不签金融评分 |

两次早期pytest启动分别因总控Python guard对Windows NUL读取/默认logging设备定位拒绝，在收集前失败。原日志完整保留；仅在验收环境允许标准NUL读并把pytest日志定向自有temp后完成58P，不改产品、不算产品RED、不隐藏失败。没有为每个helper新增review。

## 原四组剩余问题

### R1 研究实质与事实一致性

90行中9行含facts（Alphabet4、CATL5）；空facts本身合法。真正阻断是78行（全部72非深核＋6中信建投深核）仍为 `SRC-SKELETON`、locator `n/a`、sought `skeleton placeholder (no research conducted)`、termination `skeleton_baseline`。却计入source_verification_attempts=90、rows_gap_terminated=81，并在README声称每行真实定向查证。它们没有实际URL/定位/访问结果，不能视作研究完成。

Alphabet6个深核attempt统一引用营收concept `SRC-SEC-REV`，不支持其现金流、capex、偿债或ROIC查证范围；题义映射没有接到对应来源。中信建投通道失败与“全部PDF-only”的判断未收窄；分析句仍列为official quote。CATL风险题从一篇结果新闻未覆盖，推成cutoff内没有官方HTML，超过实际尝试范围。

`FR-ALPHABET-OPERATING_01`仍answerable，且旧falsifier认为维护capex占比高使可持续FCF低于已扣总capex的73266；新ledger的partial说明未同步到reference/deep-index。ROIC新fact已含当期票据面值，旧missing_evidence/falsifier及SRC-SEC-DEBT说明仍称未含当期、IC低估。README/review声称这些全部统一，不符合实际。

可保留：CATL官方新闻确支持4237/722/1332/3925亿元及相应百万元转换，货币资金加交易性金融资产与现金等价物/净债务已区分；销量661GWh和39.2%为公司转述数据。Alphabet Note6支持49085/12000面值含当期，与46547/10883非流动账面债务两口径；未舍入税率计算NOPAT约107382.196，原定义下ROIC28.74%、历史FCF73266、流动性差额77758、收入增15.09%的算术可保留。详见[CATL官方新闻](https://www.catl.com/news/9654.html)与[Alphabet官方10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm)。这些局部事实/算术不证明完整题义或评分可判。

### R2 绑定仍有绕过与旧读取断裂

| 独立案例 | 预期 | 实际validate / export |
| --- | --- | --- |
| issuer-link-missing | supported收入来源无可验证issuer关联须降支持或拒收 | 77808 / 61356，均exit0并导出 |
| reference-id-swapped | ID必须与公司/题目生成规则一致 | 38676 / 21248，均exit0；交换两题reference_id未被发现 |
| locked-other-input-drift | 20项已声明FIN冻结输入均核bytes/hash | 25688 / 1672，均exit0；只改复制根的handoff.schema.json，锁本身原bytes未动，实际SHA已变 |
| old-published-pack-1-0 | 保留旧协议明确读取通路，不升格旧事实 | 66812 / 60320，均exit2，schema/future_protocol；原1.0只有保留文件，没有可用reader |

全部null cutoff的非法公司形状正确拒收，原错公司key控制已正确拒收；这些已绿防线保留。R2问题是supported来源缺具名关联仍被接受，以及按payload实际hash验证3个manifest/questions，未读锁的其余已声明输入。不要把全20个原件恰好未变与程序实现了20项核对混淆。

### R3 计算仍只核局部，不核经济关联

| 独立案例 | 实际validate / export（预期exit2） |
| --- | --- |
| ledger-valid-wrong-company-reference | 9476 / 26820均0；Alphabet FCF账引用真实存在的CATL OPERATING_01 |
| ledger-valid-wrong-metric-reference | 41168 / 66940均0；FCF账改引用Alphabet IQS_01 |
| ledger-empty-source-fact-ids | 47624 / 54716均0；computed输入取消fact关联仍发布 |
| ledger-entry-period-mismatch | 14708 / 31852均0；账期改2024，输入仍2025 |
| ledger-consistent-cross-unit-mix | 64140 / 79884均0；capex fact和term都改为91.447 USD_billion，结果按164713 USD_million减91.447数值并声明164622 USD_million，局部一致但单位混用 |
| ledger-consistent-cross-year-mix | 52460 / 24076均0；capex fact/term同步改2024，OCF及账期仍2025，两个年度跨度都长，绕过仅FY/Q1跨度检查 |

真正一致零分母控制正确 `empty_denominator`/exit2，零分子通过，原数值/结果/term-vs-fact不一致已修；保留这些。上述均为合成软件控制，不是官方财务正例。ledger沿用1.0但公式约定改成新named-method唯一语法，旧材料读取兼容也必须明确处理，不能靠保留schema文件宣称向下兼容。

### R4 交接和读取

保留开发`.venv`可以据实说明，无需删环境或假填cleaned=true；但把它放在temporary_roots并created=true/cleaned=false仍触发既有公共合同失败。应将持久保留环境与已清理临时根按原合同分类，不能改总控公共schema来放过。本机29项工件匹配，但5个忽略文件不能从commit恢复，交接须说明/形成可携带证据；真实逐文件差异补齐遗漏产品工具。

`load_json_strict`依旧fh.read()，锁/冻结文件也无界read_bytes；原卡要求文档化有界短结构读取未实现。观测未把5MiB自行定为协议上限，而证明请求本身是无界的；应先公布合理上限，再测正常边界与超界拒收。原strict JSON及结构稳定exit2改善保留。

## 隔离与后续

去密钥子环境、Python继承audit限定自有读写/网络/子进程；handoff检查仅另允许原IQS script/catalog/schema三个精确只读文件。独立审查在线读官方HTML，未保存页面正文/公司文档。模型/收费搜索/生产DB/外仓业务写入均0。

清理前核全部84源/副本及5补充日志hash、实际HEAD/status和子进程终态；只读CIM确认owned Python进程0。逐文件核自有普通文件/ID/SHA后清理196文件/96目录，5MiB合成输入删除，保留小反例、冻结副本与原日志。源只保留此前未跟踪.codegraph/，无业务改动。

原writer只接 [R2同包四组续卡](FIN-REF-01-R2.md)，旧25/25控制和58P不重做实现；新交接remediation-02，原件不覆盖。F05/G3与真实金融准确性、B01对照、生产UI/一键/全池仍开放。
