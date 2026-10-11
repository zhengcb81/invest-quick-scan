# FIN-REF-01 remediation-03 集中续验

**结论：接收partial有效交付，changes_requested；R2历史兼容组关闭，R1/R3/R4仅续剩余。** 这次不是四组全部完成，但上一轮10组边界全部修复。保留有效内容，不再回炉它们；同包一次集中审查，不新增helper门。原研究范围不静默缩减，F05/G3/准确性和生产接线仍开放。

## 实际交接与通过项

源 `C:/Users/郑曾波/Projects/iqs-financial-reference-lab`，branch `codex/fin-ref-01`；base `775b6a84729e36decb742b0c25eb5c84772d074b`，产品 `b86b25feff0b71d97f845bf0dab9eddb8d34c5c2`，交接 `2b9b993dc7683b61a93840386659238f536785ba`，终态HEAD `04633a7cb4151f6413d64874efe6743bc8d4a262`。无remote，源仅既有 `?? .codegraph/`。pack1.1.0、ledger1.0.0、CLI声明1.3.0。

131跟踪、33工件、20冻结输入bytes/raw SHA匹配，产品为实际祖先。公开handoff PID50628/exit0，仅shape/声明范围。旧交接、1.0 schema与锁字节保持；源开发`.venv/.codegraph`不是测试临时根。

完整原suite PID62548/exit0：**81P/0skip**，进程14.10秒（pytest自身13.20秒）。旧25与上一轮12独立validate/export对37/37符合；再前轮10组全部符合，包括：

- 删除或自改served字段的原错题引用拒；倒序/错start日期和2023冒充同比2024拒。
- 实际旧1.0错pack_id拒；实际上一轮1.1正确hash可经historical reader读取，导出保留reader与资格限制；当前正常包仍通过。**R2关闭**。
- current/legacy的合法JSON字面1e999溢出均稳定exit2、无正式输出；原Infinity常量拒绝保持。
- pack正好5,242,880 bytes可读；+1 byte在读取前拒；5,258,485-byte锁现在在hash读取前拒，reads=[]。原锁先无限读取实例关闭。

前47组对共94次公开CLI全部期望一致；额外两组见下，各validate/export均确认，合计98次。测试数量仅软件覆盖，不是金融准确率。

## 原组剩余

| 原组 | 当前结论 | 只需接续的内容 |
| --- | --- | --- |
| R1 研究 | partial接收，原研究仍开放 | 72not_started如实deferred，未查证；访问范围与少量旧说明仍矛盾 |
| R2 历史兼容 | **关闭** | 不重做旧reader/hash/导出标记；后续变更只回归保护 |
| R3 账关联 | 原五实例关闭，语义注册仍缺 | FCF改标ROIC可发布；合法同比输入列表换序被误拒 |
| R4 读取/交接 | 原溢出和超限锁读取关闭 | 累计读取预算未公布/实施；实际路径声明遗漏8项 |

**R3错误发布**：复制实际正确FCF entry，仅改metric=`financial.roic`、reference_ids=[FR-ALPHABET-IQS_10]、served_question_ids=[IQS_10]。OCF/capex、`sub(OCF,capex)`、73,266 USD_million和其facts/期间不改；pack及账hash保持正确。`fcf-method-relabelled-as-roic` validate PID31920/exit0，export PID57588/exit0并正式导出。现在registry只核作者给的metric→题ID，未核metric↔method/经济量/结果单位，所以改两个自声明字段仍能绕过。应拒发布，把ROIC百分比与美元金额的FCF区分；不是新评分规则。

**R3合法输入误拒**：实际同比entry只reverse inputs数组，公式仍`growth(REV_2025,REV_2024)`、按symbol值和期间完全相同、结果正确。`valid-yoy-input-array-reordered` validate PID63216/exit2，export PID26300/exit2，命中growth_wrong_comparison_year。公式是具名symbol调用，inputs数组没有声明经济角色顺序；期别检查却取inputs[0]/[1]。应依据formula operands绑定cur/prior，合法输入顺序无关；保留真正跨错年反例。

**R4声明**：base→实际HEAD37路径，handoff29，遗漏8：gen_artifacts_remediation.py、artifacts.json、handoff-commit.txt、新5日志/manifest；没有多声明未变路径。缺的是闭合metadata，不是越权仓写。两阶段产品/交接列表都要如实，不能说“16产品＋交接已全部闭合”。单文件5MiB已经实现，累计预算仍无明确文档/扣额；这是原卡余项，不伪称已有16/100MiB协议，不另造大文件压测证明。

## 研究与清理

独立核源见[R3独立记录](FIN-REF-01-R3-independent-review.md)：90行、三公司各30、18深核、26 fact记录、9已研究/9缺口/72未研究、18attempt映射均保持；19新增访问摘要能区分ID数和访问记录，但不能只凭作者“Proves actual access”就称独立验证19次执行。72deferred不是伪装完成，可以保留partial；总控维持原研究范围pending，不批准自动缩题。全分数/区间null，不以此本身判失败。

自有隔离 `runs/fin-r3-acceptance-2026-10-11-01/` 留snapshot、source、guard、原PID/stdout/stderr/JUnit、小输入retained-cases与结果JSON。`boundary-cases.json`、`overflow-cases.json`、`read-boundary-cases.json`、`named-contract-cases.json`保存实际正反例；`scope-check.json`、`handoff-check.json`、`closeout.json`记录范围/终态。先核绝对路径/文件ID/单链接/raw SHA，再清理cases/temp的223文件153目录；超限合成输入、复制锁根、导出和pytest临时产物已删。131源/副本SHA及HEAD/status未变，CIM owned Python0。

原测试去密钥/禁外网/只写owned；模型、付费搜索、下载公司文档、生产DB和外仓源码写入0。独立agent只看官方HTML、不存正文/PDF。只交[同包三组余项R4](FIN-REF-01-R4.md)，原R2关闭、81已绿防线保留，原Lab仍由原writer独占。
