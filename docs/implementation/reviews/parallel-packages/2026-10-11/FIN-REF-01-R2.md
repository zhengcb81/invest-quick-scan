# FIN-REF-01-R2：原四组剩余收口

只交原FIN harness，唯一写根 `C:/Users/郑曾波/Projects/iqs-financial-reference-lab`，不要新开重叠writer。先读 [R1集中续验](FIN-REF-01-R1-acceptance.md)、[独立核源](FIN-REF-01-R1-independent-review.md)、[原R1卡](FIN-REF-01-R1.md)、[原包](../../../parallel-lanes/packages/2026-10-11-wave2/FIN-REF-01.md)与[共同规则](../../../parallel-lanes/packages/2026-10-11-wave2/handoff-rules.md)。本卡自包含，仍为同一个包，不新增小门。

## 接手与保留

验收实际HEAD `655e9069e6bdffef1f5dbcfe243d74a8c100db39`，产品 `601be8b14abc603a51e9558d5928ae6d2679ea36`，分支codex/fin-ref-01，状态仅此前`.codegraph/`；84跟踪/29本机工件/20锁。开工再核当前HEAD/status，不能覆盖后续其他writer工作。5个交接日志/manifest是被ignore的本机原件，非跟踪文件；原交接和旧1.0 schema/锁字节均保留。

58P和原25独立validate/export对已绿，包括错hash/题集/坏JSON/日期/零分子；不要重新实现或为每个修改全套重跑。CATL新增8事实数字和正确货币口径、新NOPAT/债务两口径保留。仅继续原四组剩余；允许partial/不足证据，禁止填分凑完成。

总控只读反例在 `C:/Users/郑曾波/Projects/invest-quick-scan/runs/fin-r1-acceptance-2026-10-11-01/retained-cases`，原记录/控制器在其父目录。不能在那里写/运行产物；在自身owned临时根重建固定小控制。5MiB空白样例已清理，可在自有根再造。所有写仅本Lab既有src/content/schemas/tests/tools/fixtures和新交接，不能改IQS/StockQA/StockWiki/其他Lab/全局环境。

## R1 研究实质与同步：先固定占位和错句RED

- 将78行未研究与真实失败明确区分；没有实际定向尝试的保留not_started/未研究，不计为source_verification_attempts或gap-terminated完成。原6深核/每公司24其他题做真实官方HTML查证或具题义的实际失败记录，再据实更新完成状态；一次查证可支持多题但分别列准确URL/定位/实际支持范围。不能只替换SRC-SKELETON名字或填通用“渠道失败”句。
- Alphabet深核现金流/capex/债务/ROIC等绑定对应真实来源，不统一套营收JSON。中信建投实际访问结果具体记录，不推成所有资料PDF-only；CATL新闻缺某情景只表达该来源范围不足。分析/判断不写入official quote。
- 把OPERATING_01 reference、deep-index、coverage、source-attempts及说明同步为历史FCF仅partial，删错误维护占比推理。ROIC facts/source解释/missing/falsifier/账的债务定义统一为实际选定口径；保留当前与旧两口径说明，不覆盖旧交接。
- 研究完成、事实可判、独立复核、score proposal分别据实。全90/18固定分母不换；允许真实深核以缺口结束，不强求有分。cutoff沿2026-10-11冻结，不用后来公开资料回填。
- 用精确数据断言覆盖78占位分组、错误attempt支持范围和各矛盾句，再附人工官方核源实际日志。不能靠一个“没有skeleton字符串”测试授予研究完成资格。

## R2 冻结输入与issuer/reference绑定：四个补验

- `issuer-link-missing`：supported收入来源保留issuer_matches=true但issuer_company_key/name均null，当前发布。1.1具名可验证关联缺失时须降unverified或拒收；旧材料按明确旧reader只读，不让布尔自己授资格。
- `reference-id-swapped`：交换同公司两题reference_id而question_id/metric各自不变，当前发布。按已公布生成规则绑定ID/公司/题义，不只验证唯一和pattern。
- `locked-other-input-drift`：复制20冻结根与原锁，只改锁内handoff.schema.json；pack摘要和实际3manifest/questions都正确，当前发布。核FIN consumer全部20项的实际path/bytes/raw SHA及安全冻结定位，不能只比较锁文件hash或payload自报的manifesthash。
- `old-published-pack-1-0`：旧1.0虽然文件未动，但当前CLI视为future并拒。保留明确旧版本只读校验/查看通路，版本分派不强行把旧包当1.1或补字段后授资格。原存在的金融局限仍记录；不要求把旧错误材料升级为当前研究完成。
- 原坏日期/唯一30题/截止公开性/unknown分数防线不减。新反例每次正确重算pack_id和账pack_id，区分真正目标规则命中与无关schema/hash错误。

## R3 经济关联与可复算账：六个补验

当前账只检查reference存在、term与fact一致和算术，以下都validate/export exit0。先测RED再最小修复：

1. Alphabet FCF账引用CATL真实OPERATING_01，或引用Alphabet真实IQS_01。核公司、metric、题义/支持范围；若一账服务多个题须登记明确兼容关系，不靠存在性。
2. computed term的source_fact_ids=[]。必须有可核且适配的fact支持，不能取消绑定绕过。
3. 账entry期间改2024，inputs仍2025。账期、流量/余额、所选begin/end/average规则分别校验，不用一个字符串日期或span代替。
4. capex fact和term同时改为91.447 USD_billion，OCF164713 USD_million、算术结果164622 USD_million。局部一致仍是混单位；同尺度转换必须显式且确定，否则拒收。
5. capex fact/term一起改2024，OCF/账期仍2025，年度span都合法。FCF减法需要同一期流量；growth/average_beginning_end合法跨年另按具名method核对应周期，不能一刀切所有跨年。
6. 旧ledger1.0公式阅读与新named-method语法兼容要明确：旧version不能默默改成只支持新语法。可具名profile/新版本分派，不eval任意字符串，不把旧算术错误当合法新结果。

保留现零分子/真零分母、输入/事实值和结果/货币错配的已绿测试；加正确单位换算、合法同比和期初期末平均正例，防误拒。合成控制只是软件验收，不称真实财务gold。

## R4 交接/读取有界：原节点收尾

- `.venv`为持久dev环境可保留，放在明确保留环境说明；temporary_roots只描述实际临时根的创建/清理。不得谎填cleaned=true或删用户dev环境，亦不得改总控公共schema。原公开handoff应exit0，仅形状/声明，不授金融资格。
- changed_paths补实际产品工具 `tools/gen_artifacts_remediation.py`，所有交接新增元数据逐文件据实列出。下一轮工件清单完整闭合，5个被logs/忽略的证据采用精确Git例外或明确可携带归档索引，不能声称它们在当前commit内；旧原件保持历史，禁止改原清单掩盖第一轮漂移。
- 对pack/账/锁及实际读入的短结构资源公布合理大小/总量上限，先文件/path/大小后有界读取，超限稳定exit2、无正式输出；不增下载器。5,583,067-byte空白JSON原CLI实际read(-1)并通过的观测证明没有边界，不是已存在的5MiB协议上限。选定上限后测正好边界/超界及正常90题包，不通过删字段凑大小。
- 保留严格duplicate JSON/NaN/结构坏输入稳定exit2；真实CLI验证/导出用同一路径。错误详情安全，不执行证据；测试环境去key/禁收费/仅自身临时根。

## 集中测试、清理与唯一新交接

上述四组RED→修复→受影响unit/integration/实际CLI正反例，一次稳定候选的包级独审；金融事实先于评分。58已绿测试和原25对不为每个helper重复；共同读取/版本大改时发布前做一次集中兼容回归即可。不得降测试期望或用generic异常代替目标规则通过。

新交接仅本Lab `docs/handoff/FIN-REF-01/remediation-02/`：真实base/product/handoff/terminalHEAD、版本/reader说明、90coverage与18深核逐题索引、真实source-attempts/短facts与反证、可复算账、case-map、review/PWF、原RED/GREEN进程/日志SHA、完整artifacts和20输入核对。原交接/schema/锁不覆写；先正常产品commit再交接commit，无remote不造push。

只清理自己创建且已核绝对范围、文件类型/字节的测试资源，留失败原日志；进程终态/清理列表据实记录。不下载公司文档/正文，不跑LLM或付费搜索/生产DB。最终公共handoff命令使用原wave2 catalog和FIN-REF-01 ID。总控收到后同包集中接续，F05/G3/准确性与生产接线仍待实际证据。
