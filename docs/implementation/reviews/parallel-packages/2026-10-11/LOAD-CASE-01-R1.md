# LOAD-CASE-01-R1：四类语义集中整改

本卡是总控集中整改交付，**不是自动开工通知**。用户将卡交给指定 harness 后认领；同包只设一个 writer。目标是修复 LOAD 离线分析器，不实施新 scheduler、队列、预算账本、provider/search client 或 owner adapter。

## 唯一写根、当前基线与先读资料

唯一写根：`C:/Users/郑曾波/Projects/iqs-load-case-lab`。保留实际分支 `codex/load-case-01`、现有产品与旧交付，不 reset/clean/stash、不删除未知文件、不恢复别人的仓库。基线 actual HEAD 为 `d232965e48a67aec7d528097ea3ce574c942596e`，产品提交为 `54038475c0a3ce8b6097a11322cf24c5f09b585f`。原 `1496c7545b6e92d4abb151ead432b9f270e4c91a` 是交接树提交，不是产品提交。验收时 status空、无remote。

先读下列文件，外仓均只读：

- [原施工卡](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-11/LOAD-CASE-01.md)
- [共同规则](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-11/handoff-rules.md)
- [输入锁](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-11/inputs.lock.json)与[handoff模板](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-11/LOAD-CASE-01.handoff.template.json)
- [集中报告](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/intake/parallel-acceptance-2026-10-11/load-case/review.md)、[结果/原命令/终态](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/intake/parallel-acceptance-2026-10-11/load-case/result.json)、[冻结清单](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/intake/parallel-acceptance-2026-10-11/load-case/source-freeze.json)

验收锁 raw SHA=`3ce74d8399e2bee7e163a8b1ecc32cf6335f26bb15d23071a367bdc144e0d46c`；15项 LOAD consumer 输入当时与快照/当前源吻合。开工先核实际 HEAD、状态、143文件清单和锁。已有 writer 或锁漂移先报总控；不能重抄最新 owner 字节替换锁。只读清单明确排除 `.git`/索引/个人配置/缓存，不把143说成整仓全部文件。

允许最小修改 `src/iqs_load_case_lab/` 的现有 trace/analysis/case/inputs/CLI/pack/schema加载实现及确需配合的 money/generator/scenario_pack；`schemas/`、`tests/`、有限手算/负例 fixtures、`content/scenarios/`、本包 README/interfaces 和独占运行根。本包 PWF 固定在 `docs/handoff/LOAD-CASE-01/planning/`；新整改交接固定 `docs/handoff/LOAD-CASE-01/remediation-01/`。不得写 IQS/StockQA/StockWiki/其他 Lab、总控 PWF、安装镜像、全局配置、真实名单/数据库。原 `docs/handoff/LOAD-CASE-01/` 的历史交付不可覆盖来制造旧结果。

## 同一张 R1 的四项收口

### LC-R1-01：预算与重复事件

当前位置 `trace.py:85`、`analysis.py:179/233/282`。先从总控 `controls/` 中保留的输入固定反例；不复制分析算法产生 expected。

- 预发送 reservation：原 HB-L06 spent0.23、held0.2、remaining0.57。仅将 G-06 send 改成 `reservation_placed` 后不能把held0.2变成0。缺后续send捕获可标 incomplete，但该已声明承诺及未知暴露必须留下。
- 同 ID、相同内容 settlement 重复：G-01多捕获一次，spent仍0.23；记录 capture行数/重复名单，不重复计费。同 ID、不同内容继续拒绝/exit4。
- 未知单价：model price=null时，保留已知search0.03的小计、未定价费用桶/预留暴露；全量spent/reserved/remaining和完整守恒不能因跳过未知项给出假0/健康剩余额度/true。明确known subtotal与unknown全量，零价0与未知null必须不同。已有合法价格的 Decimal 守恒仍准确，币种/套餐requests/searchcredits不得混算。

只分析原 trace，不建立第二账本、不替实际 owner 结算。若旧 report schema 的 string字段无法表示unknown，用具名新版本和明确版本分派；旧字节仍可按旧版本复验，不将旧错误输出重标为新合格输出，不静默放开未知字段。

### LC-R1-02：约束必须可诊断，五小时配额与并发分开

当前位置 `analysis.py:159/439`。已知total/group/route cap1而同一原HB-L04 peak2，应报告可定位违规、写报告后exit4。route缺映射不能伪称合规，可明确unknown；不能只计算峰值不检查显式上限。

共享五小时按冻结账户桶与 `[from,to)` 计算；requested model不同不能拆桶。独立声明窗口请求限额与 in-flight并发，未声明窗口限额只能报计数/unknown limit，不能取 `max_in_flight_per_group` 代替。

原 HB-L05半开计数1/2是有效算术基准，但三个 send未close导致实际并发3>声明2。新正常 fixture应合理补完成事件或声明真实独立限额，同时保留旧bytes；另固定超并发/超窗口负例。不要通过调宽caps来抹去实际错误或假称原fixture整体正常。

### LC-R1-03：资格分母、等待与新鲜度

当前位置 `analysis.py:405/422/376`。声明arrival不等于已具备派发资格。建立最小、有限、具名 eligibility/window 映射，区分eligible/blocked/unknown及证据理由；未映射detail必须unknown，不可静默当eligible，也不可把任意detail升级为owner证明。

三个blocked arrival没有合格窗口时，已知全阻塞是N/A/not_assessable；不能记3个已证明eligible。前两个blocked、第三个无关热点有send的控制，不得给确定starvation_observed或清空unknowns。等待以同类work第一次合格窗口至第一次服务及显式截点计算；first coverage份额与最大等待使用有效分母，未知窗口单列。工具仍只归约已有事实，不造schedulertrace。

新鲜度不能用TTL是否null充当信息日期是否缺失，或“无freshness_gap”充当fresh。已观察信息日期、TTL、事件失效各有独立映射；证据缺失明确unknown/缺日期。原normal-L06只有TTL、无日期/field观察，不能报fresh1。保持旧新鲜度案例可追溯，新增最小正反例，不造真实公司答案/owner资格。

### LC-R1-04：实际锁、source与成员引用闭合

当前位置 `cli.py:119/134`、`inputs.py:36`、`case.py:176`。实际lock核验通过，不能替代文档内provenance lock相等。case/collection 的 `inputs_lock_sha256` 必须绑定本次实际提供锁rawSHA；只消费consumer包含LOAD的冻结条目，不能由自报source_ref取得资格。

collection的source_refs与每个member都必须核实际内容：限定本包冻结根/相对路径、禁越界与reparse/secret路径、核文件存在、bytes/rawSHA、版本、case_id/scenario_id、重复身份及引用角色。canonical pack_id是内容地址，不证明文件引用真实。替换source SHA、缺失/越界member或锁不一致须按原协议拒绝；不能用数组长度输出“22份已校验”。写正式输出前完成全量验证，失败不留下半份正式文件。

本次 `counter-forged-collection-ref` 是两字段组合变异（sourceSHA与memberpath）且exit0，不能拆称两个已跑单字段测试。整改测试应分别固定单字段控制再保留组合控制。对尚无合法映射的引用明确unsupported/unknown，不能伪造闭合。

## 保留项、测试规模与唯一集中审查

保留原有有界严格schema/JSON、synthetic命名空间、not_owner_qualified、固定seed、小规模默认/显式2000、future版本拒绝、未来事件违规、不同内容duplicate冲突、ACK同hash重投零新问和未知send暴露。2000是声明生成，不是owner压测；不发实际LLM/搜索/API，不读取密钥值。

采用同一轮集中TDD：先固定上述RED及四项手算正常控制，开发期定向跑受影响组；候选稳定后一次相关全回归、一次公开CLI正反例及一次包级review，不为每个helper添加门，不反复重跑不相关组。原基线77P、20次独立CLI和21控制分开记录；新增测试按实际收集分母，不与重叠选择器相加。复用旧有效日志为基线，不把过去pytest controller环境错误判成产品失败。

公开入口继续 `python -B -X utf8 -m iqs_load_case_lab generate/validate/analyze`。用中文/空格/随机cwd，显式 `pytest -c <本Lab pyproject.toml>`，私有TEMP/TMP/TMPDIR/cache/basetemp/logfile；禁网络/真实DB且普通文件write限定独占根。Windows NUL仅可作为精确空设备例外，不借此开放外来路径。输出已有文件拒覆盖；故障也完成严格自有清理。

预期一次集中证据覆盖：四手算算术控制；reservation保留；相同duplicate幂等及不同内容拒绝；unknown与zero不同；各显式并发及独立窗口配额；全blocked N/A/资格未知/有效first wait；无日期unknown与有证据fresh/stale/eventinvalidated；错lock/改单个source/缺失或越界member/组合变异拒；既有future版本、乱序capture、ACK接续和固定seed控制。先验证原正常与每处独立负例，再归并成一次包级结论，不设中间签收关口。

## 交接与回退

新归档 `docs/handoff/LOAD-CASE-01/remediation-01/` 使用原handoff模板及共同规则。包含 summary、interfaces、case-map、artifacts、完整原RED/最终GREEN stdout/stderr/JUnit/process终态、isolation、source/锁前后清单及剩余unknown。本包planning持续记录实际进展。旧handoff/raw工件只读，新版本稳定case_id可关联旧版本，不能篡改历史。

先实际产品/测试commit，再交接commit；`result_commit`填真实产品完整SHA，handoff/head字段分别记真实读取时点/角色，禁止自引用循环。`scope.changed_paths`填实际本包改动，review快照填实际commit或如实pending/null与限制，不能伪造独立批准。当前原artifacts60条均吻合，保留此事实；新版最后完成全部文档再生成相对path/bytes/64位rawSHA/source_class索引（不含自身hash）。Git正常hooks、精确暂存，不force/skip，不创建remote/推送。

清理只自己的Lab独占运行根；先核终态PID、绝对边界、无外来reparse/单链接、精确文件集合及SHA。保留轻量种子/命令/日志，大规模生成副本可重建后删除；不能清共享TEMP、验收intake、其他harness根。所有API/收费请求必须实际0。

交回总控后，由总控一次包级续验决定是否签收。此整改不关闭O02/L03/X09/G3/F05、全池、金融正确性或TH/IN前置；真实owner映射另由既有主线接入。
