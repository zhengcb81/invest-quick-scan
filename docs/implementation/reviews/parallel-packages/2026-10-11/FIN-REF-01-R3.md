# FIN-REF-01-R3：只续原四组剩余

交原FIN harness，唯一写根 **`C:/Users/郑曾波/Projects/iqs-financial-reference-lab`**。这是原包接续，不是新包或新增逐题审查。先读[R2续验](FIN-REF-01-R2-acceptance.md)、[独立核源](FIN-REF-01-R2-independent-review.md)、[原R2](FIN-REF-01-R2.md)及[共同交接规则](../../../parallel-lanes/packages/2026-10-11-wave2/handoff-rules.md)。其他Lab、IQS、StockQA、StockWiki和生产库禁止写；不启动第二writer。

## 接手基线与保留

验收 branch `codex/fin-ref-01`，base `655e9069e6bdffef1f5dbcfe243d74a8c100db39` → 产品 `c35485981f9b72c82acb7adfe5dbe04e288c741b` → 实际HEAD `775b6a84729e36decb742b0c25eb5c84772d074b`；源仅未跟踪`.codegraph/`，无remote。开工先核最新HEAD/status，有新writer变化就保留并报告，不能reset覆盖。不重复CodeGraph初始化，不清 `.venv`。

保留73P/0skip和37组既有独立CLI对；20锁/issuer/reference ID/零分子/真零分母/空fact/单位混用/同一期FCF防线不返工。保留90行、三公司各30题、18深核、cutoff 2026-10-11、CATL短事实和Alphabet局部正确计算。旧交接/schema/锁/原日志字节不覆写；原1.0只读通路、当前pack单文件5MiB读取前检查、开发环境声明已绿。

总控只读证据根 `C:/Users/郑曾波/Projects/invest-quick-scan/runs/fin-r2-acceptance-2026-10-11-01/`：冻结source、retained-cases、boundary_cases.py、overflow_cases.py、read_boundary_observer.py和对应结果JSON。**只读参考，不在其中运行或写文件**。复制必要的小seed/控制到自己owned临时根；controller含原绝对路径，必须改成自己的OWN，不能直接运行。两个旧实际版本分别在总控 `runs/fin-acceptance-2026-10-11-01/source/content/reference-pack.json`（1.0）和 `runs/fin-r1-acceptance-2026-10-11-01/source/content/reference-pack.json`（前版1.1），或自身已保留历史commit；不要造legacy正例。

## R1 研究实质与来源同步

先固定72not_started分母、实际访问和矛盾句的数据RED；再继续原官方HTML定向查证范围。一次真实查证可支撑多题，不要求90次网络请求、不填分凑完成。逐题引用明确支持范围；访问失败记录时间、真实URL、状态/定位和缺口，仅“未研究”不能改成“失败查证”。不能把唯一source ID计数冒充实际访问次数。

重点纠正：Alphabet可访问SEC HTML的业务/风险/分部/债务部分，不能因不下载PDF一概跳过；CSC06066定位真实HKEX结果，入口/TLS失败只表达实际尝试；CATL新闻缺第二曲线不能泛化成全站无HTML。SRC-SEC-DEBT face/current/noncurrent carrying定义与账/事实/缺口一致；CATL旧PDF-only和无HTML断言、CSC作者概括quote、summary/method“其余gap完成”与72未研究同步。原短摘录可留，不保存全文/公司文档。

完成、缺口结束、未研究、独立查证、评分提案分开。允许真实研究后仍不足证据/分数null；若无法做完原研究范围，明确deferred/原因，不把partial称四组全done。金融值与来源同时核对，不能只做“无skeleton字符串”测试。

## R2 历史只读兼容与完整性

1. `legacy-digest-tampered`：真实旧1.0仅pack_id改全零、**不重算**，当前validate/export均0。reader至少守住该版本原完整性，稳定exit2、不产生正式输出；只读不能略过hash。无需强制旧数据满足新研究字段，旧局限继续保留。
2. `previous-published-1-1`：实际上一轮1.1，正确hash，不传账，当前2/schema_invalid+research_summary_mismatch。同1.1新增必填状态计数不能破坏已发布版本读取。选明确版本/profile/历史只读reader，保留原字节及资格差异；不得拿“future”拒掉自己以前发布的1.1，也不得自动补字段授新资格。
3. 验证与导出都携带真实reader/legacy限制和qualification标记。旧包导出不能丢reader，误显示当前完整验证。ledger1.0旧自由式公式同样明确可读与不可授新computed资格，禁止eval任意表达式。若修改协议，文档说明分派/迁移，原schemas保持兼容通路。

正例：实际旧1.0和旧1.1只读可查看；当前包当前校验仍通过。反例：旧hash错仍拒，未来协议仍明确拒。不得为通过测试将历史材料重新拼造/升级事实。

## R3 绑定与具名期间规则

先重放这五个小控制，正确重算pack_id和账pack_id；validate/export用相同路径，预期exit2、无正式输出，错误命中实际目标规则：

- `metric-binding-omitted`：Alphabet FCF entry引用真实 `FR-ALPHABET-IQS_01`，删除served_question_ids；当前0/0。
- `metric-binding-self-rewritten`：同错引用，并自填served_question_ids=[IQS_01]；当前0/0。兼容关系必须由具名method/metric/题义注册契约决定，不能自声明字段取消校验。可选旧字段缺失进入明确只读限制，不略过当前computed规则。
- `entry-start-only-shifted`：2025 inputs、entry period_start=2024-01-01；当前0/0。核流量期间，不能只比结束日。
- `entry-start-after-end`：start=2026-01-01/end=2025-12-31；当前0/0。首先拒倒序，不需要财务判断。
- `growth-wrong-comparison-year`：原2025同比2024的prior fact和term同时改成2023，原同比说明/指标不改；当前0/0。具名growth按所声明annual同比核比较周期；另合法多期growth用明确参数/定义，不能全面禁跨年。

补合法FCF、同比、期初期末平均和明确单位换算正例，避免只检查错误case。保留原单位混用/同一期减法/值币种反例。兼容及method规则集中设计，不为每个helper加门。

## R4 严格数字、读取前预算、交接闭合

- `current-overflow-literal`、`legacy-overflow-literal`：用实际包复制，仅数值改成JSON合法字面 **1e999**，按实际canonical解析规则正确算pack_id；输入没有NaN/Infinity token。当前0/0，导出Infinity。加载时有限数检查（parse_constant之外还需float溢出/实际数值检查）和导出strict JSON共同兜底；无正式输出/稳定exit2、不带traceback。不要误把现已绿Infinity token case当本反例。
- 单文件5MiB pack检查已绿。过限锁case：合法锁尾补空白到5,258,485 bytes，复制20冻结root，正确重算lock_sha/pack_id；当前虽exit2，hash先read(-1)读完整锁。所有hash和parse路径先类型/path/大小再有界读取；对确实读入的结构文件公布合理累计预算、读前扣额。正好上限与超界都有真实读次数/字节证据，不靠最后exit2。
- 当前base→HEAD39实际路径、声明28：遗漏12（原5日志新跟踪＋新7交接文件），另多声明未改research_catl.py。下一轮按实际product/handoff/terminal commit分段列全变化，原5日志注明新增跟踪但bytes不变；不用把只读路径写changed或覆写原清单。已有31工件/20输入匹配保留，元数据自引用处理遵共同规则。

## 一次集中收尾和交接

四组先固定RED→最小修复→受影响unit/integration/公开CLI正反例；同一稳定候选发布前一次完整兼容回归和包级独审，禁止逐题/helper全套重复。源码共同reader/版本改动才扩回归。软件测试结果与真实官方核源分别记录，不用测试通过推断财务准确率。

命令模板在Lab自有隔离副本内，去keys/禁收费，冻结20输入：

```powershell
# 从副本根，PYTHONPATH指向该副本src；输出仅自有临时根
python -B -X utf8 -m pytest tests/ -q
python -B -X utf8 -m iqs_financial_reference_lab validate --input content/reference-pack.json --inputs-lock fixtures/inputs.lock.json --ledger content/calculation-ledger.json
python -B -X utf8 -m iqs_financial_reference_lab export --input content/reference-pack.json --inputs-lock fixtures/inputs.lock.json --ledger content/calculation-ledger.json --output <owned-fresh-output>
```

新交接仅本Lab `docs/handoff/FIN-REF-01/remediation-03/`：完整base/product/交接/HEAD与dirty状态、reader/profile版本、90coverage/18深核、真实定向尝试与短facts/反证、账、逐项case-map、PWF/review、RED/GREEN PID/起止/exit/日志SHA、完整工件索引和20冻结输入核对。金融研究不足诚实partial。产品先正常commit，再交接commit；无remote不造push。原wave2 manifest/inputs.lock/validation不改。

只清已确认绝对范围/普通文件/单硬链接/bytes/SHA的自身临时资源，留原失败记录/小输入；终态进程和清理据实，`.venv/.codegraph`非临时根。公共handoff用原catalog与FIN-REF-01 ID，exit0只验声明，不关闭F05/G3/主线/生产门。总控收到完整交接后统一续验，不自动派发或改其他Lab。
