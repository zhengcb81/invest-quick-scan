# FIN-REF-01 remediation-02 集中续验

结论：**changes_requested，接收有效部分，原四组剩余未全部关闭**。本轮为同包集中验收，不增加小节点审批；源码继续归原 FIN harness，总控未改 Lab。软件通过不等于财务事实已独立核实，更不关闭 B01/F05/G3 或生产接线。

## 冻结交付和已保留成果

- 实际仓 `C:/Users/郑曾波/Projects/iqs-financial-reference-lab`，分支 `codex/fin-ref-01`；base `655e9069e6bdffef1f5dbcfe243d74a8c100db39`，产品 `c35485981f9b72c82acb7adfe5dbe04e288c741b`，交接 commit `6d54dc38b58d086eb3eebc580d74170de206ab79`，最终 HEAD `775b6a84729e36decb742b0c25eb5c84772d074b`。产品为实际祖先；无 remote。源状态仅 `?? .codegraph/`。
- 109跟踪文件、31声明工件和20冻结输入的 bytes/raw SHA 全匹配。原交接、原1.0 schema与锁保留；上一轮5个被忽略日志本次进入Git，**原字节不变**，不是重写历史。记录见自有 `runs/fin-r2-acceptance-2026-10-11-01/{snapshot,old-delivery-integrity,scope-check}.json`。
- 包版本1.1.0、账1.0.0、CLI声明1.2.0；1.0新增明确只读 reader。`.venv`明确为保留开发环境，公开 handoff PID40720/exit0，原临时环境声明问题关闭；此命令只验结构/声明。
- 完整原suite PID26440/exit0，73P/0skip，31.46秒；JUnit和原stdout/stderr/进程记录留档。旧25组及上轮12组独立 validate/export 正反例 **37/37符合**，包含20锁实际漂移、issuer/reference ID、空facts、错公司/题义/单位/年份和旧1.0可读。零分子和严格 Infinity 常量拒绝保持。
- CATL事实、Alphabet可复算计算和历史FCF partial修正保留。90行、每公司30题、18深核固定分母，分数及区间仍全部null。

## 剩余问题及实际反例

| 原组 | 本轮进步 | 剩余阻断 |
| --- | --- | --- |
| R1 研究实质 | 9已研究、9真实缺口、72未开始分开；不再把占位都计为失败尝试 | 72行 directed_attempts为空，仍未完成原卡要求的官方HTML定向查证；部分来源说明与当前facts/缺口状态矛盾 |
| R2 版本/身份/冻结 | 20原锁、issuer和ID反例已关，旧1.0不再当future | 旧1.0错pack_id仍发布；已发布旧1.1因同版本新增必填字段不可读；导出丢失legacy reader标记 |
| R3 账经济关联 | 原六类反例已修，named method复算保留 | 可删或自改可选served_question_ids绕过题义；只检查entry结束日，开始日倒序或错年度仍发布；年度增长可把2024比较数换2023 |
| R4 读取/交接 | 正好5MiB pack可读、5MiB+1在读取前拒；临时环境声明已关 | 锁先无限制读完求hash再拒超限；1e999被解析成inf并导出非法Infinity；变更声明不闭合 |

独立CLI控制都正确重算目标pack_id/账pack_id，未用无关hash错制造RED。新增10组 validate/export 对中9组不符合期望，另1组原 Infinity 常量拒绝符合；加上前37组共94次真实公开 validate/export 调用。**这是软件边界结果，不是模型准确率。**

| 控制名 | validate / export | 预期及依据 |
| --- | --- | --- |
| metric-binding-omitted / metric-binding-self-rewritten | 各0/0并产出 | FCF账改挂真实IQS_01；删served字段或自填IQS_01便取消限制，应2/2 |
| entry-start-only-shifted / entry-start-after-end | 各0/0并产出 | 2025输入，entry start改2024，或start2026>end2025，应2/2 |
| growth-wrong-comparison-year | 0/0并产出 | 原年度2025同比2024，fact/term一起改2023，应拒所声明年同比；不禁止合法多期增长 |
| legacy-digest-tampered | 0/0并产出 | 实际旧1.0 pack_id全零，未重算；只读不等于略过原完整性，应2/2 |
| previous-published-1-1 | 2/2 | 实际上一轮已发布1.1正确hash，未提供账；应有明确历史只读通路，不授新研究资格 |
| current-overflow-literal / legacy-overflow-literal | 各0/0，导出含Infinity | 原始JSON数字为1e999而非NaN/Infinity token，应2/2，无正式输出 |

三次真实读观察：pack 5,242,880 bytes退出0；5,242,881 bytes退出2且reads=[]；锁5,258,485 bytes退出2但已 `read(-1)` 返回全部5,258,485 bytes。前者在已核大小范围内完整读取合法；后者因 `_sha256_file` 在有界reader前 `Path.read_bytes()` 而失败。只公布单文件5MiB，没有伪称已有总量阈值。

Git base→HEAD实际39项，handoff声明28项，遗漏12项（旧5日志和新7交接元数据/日志），另声明未变 `tools/research_catl.py`。都是本Lab范围，不是越权写；需要如实闭合声明，不能把原日志新增跟踪写成内容改动。

## 独立核源与隔离证据

[独立核源记录](FIN-REF-01-R2-independent-review.md)确认财务局部改善，但72行未研究、HTML覆盖泛化和债务旧句仍需同步。18attempt记录对应7个source ID，仅可证明这些映射；缺实际访问日志时，不能把7唯一ID当7次已验证真实访问。

自有根 `C:/Users/郑曾波/Projects/invest-quick-scan/runs/fin-r2-acceptance-2026-10-11-01/` 保存冻结source、guard、原process/stdout/stderr/JUnit及小反例。结果分别为 `independent-cases.json`、`extra-cases.json`、`boundary-cases.json`、`overflow-cases.json`、`read-boundary-cases.json`、`handoff-check.json`、`closeout.json`。先核绝对范围/文件ID/单硬链接/raw SHA，再清理cases/temp内258文件154目录；超限合成输入、复制锁根、导出和pytest临时文件已删除，小输入转存retained-cases。109源和109副本raw SHA、HEAD/status未变；CIM自有Python进程0。保留原Lab `.venv/.codegraph`，没有重建索引。

测试进程去密钥、拒外网、只写自有根；模型/付费搜索/文档下载/生产DB/外仓源码写入0。独立agent只读官方HTML，不保存正文/PDF，不调用模型。只交[同包四组余项R3](FIN-REF-01-R3.md)，不返工已绿防线。
