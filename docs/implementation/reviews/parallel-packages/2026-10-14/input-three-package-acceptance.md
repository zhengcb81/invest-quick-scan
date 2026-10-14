# BLIND-INPUT-04 / FIN-PROVENANCE-03 / CHAIN-VERIFY-04 验收收口

日期：2026-10-14。三个包已集中独立审查、真实反例、直接修复，并按实际源HEAD与rawSHA精确回写、正常提交。签收范围为软件及研究候选；**不授予金融准确率gold、真实owner映射或生产执行资格**。COMPANY-AGENT-01已由用户交外包施工，本轮没有进入或修改它的工作目录。

## 实际提交与交接完整性

|包|独占Lab分支|冻结HEAD|总控修复提交|
|---|---|---|---|
|BLIND-INPUT-04|codex/blind-input-04|5611af2f6d48a43cd38e4b54f2ec78461e6bcc1f|281b7a64a01acbdf8184240f5b9005e146086dce|
|FIN-PROVENANCE-03|codex/fin-provenance-03|a6b27e6a0e9d4c0f046f862d267e722fe405c40b|5dc988bdb42f717009ed3dc4822b2e7ece7e2ab7|
|CHAIN-VERIFY-04|codex/chain-verify-04|94c185fff35375314aabf33c48f25f7b7542b63c|f9a47a4732d11c4a8056b6ba1deeb2feff65f844|

源目录分别为C:/Users/郑曾波/Projects/iqs-blind-input-lab、iqs-fin-provenance-lab、iqs-chain-verify-lab。旧handoff/fixture原字节保持，总控报告另在各Lab的docs/coordinator/acceptance-2026-10-14-inputs/，不重签历史清单。三个源tracked业务clean，index空；CodeGraph设施已按用户授权建立，不混入业务提交。

BLIND原artifact1729/1729、FIN131/131 rawSHA匹配；CHAIN943/944匹配，唯一差异是历史manifest自列handoff的旧SHA。原结果commit之后分别还有5/6/4个文件后继变化，接收按实际冻结HEAD，不只按handoff所列commit。五个曾显示missing的深层文件用Windows扩展路径核实确实存在。

## BLIND：输入可以接入，参考资格不再猜补

已修完整Observation1.2 schema与原IQS语义验证、原题/答案/期间/主体冲突、同请求重复/重放与失败分母、思考正文搬运、Observation执行metadata错绑、显式源码根被sys.modules缓存覆盖、validate未读实际字节和公开回执绝对路径泄露。12场景已重建；原历史不合规Observation样例保留并清楚标记，不再冒作正例。

原19个/4个eligible事实缺独立核源依据，现保留全部候选资料但事实oracle与评分oracle资格均为0。运行包0.1.1；公开1.0封套与review_input1.1合同保持，未知格式拒绝，不靠同版加字段绕过。支持显式Observation1.2和单/多题wrapper；原始vendor JSON、自动claims抽取、真人双审及金融正确率未验收。

最终稳定整包91P/1skip；随后仅对公开回执脱敏和12场景复核7P，合计98个唯一通过、1个Windows原生symlink权限skip。不能把两批并集称为一次99项整包。完整原件及资格条件仍需下游独立评审，空claims不能得100%准确率。

## FIN：验证与导出消费同一批字节，搬迁不回源

已修锁项未实读、诊断hash错误不阻断、逐题依赖脱离原锁、公司/原题/ledger绑定缺口、quoted_only被误称闭合、校验显式A却组装B、导出回原Lab补依赖、固定staging名称删除他人目录及非对象JSON崩溃。首次组装依赖根必须显式指定；最终便携副本只读自身deps。

保留原90题/1058facts/62sources及90个null评分，不改金融原题或事实；原88 partial、2 insufficient_evidence和90 needs_revision保持。真实原FIN validate/export已调用；搬迁测试断言实际wrapper及冻结helper的导入位置在移动根、再导出字节一致、缺bank拒绝回源。Windows正常路径与\?\扩展路径仅在比较视图归一，实际IO继续原生扩展路径，祖先链接拒绝保留。

最终冻结完整批次为53P/1skip（54项），code_input_stable=true。此前长路径失败、运行期变动与600秒超时原样保留，未算作最终通过。最终新便携副本为reviews/fin/repaired-portable-bundle-v2，共59文件，bundle-manifest rawSHA a3c89452c688c4268c23bc4bd03387e362f73fbafb3b8c83ed884381874f7021；真实导出受影响复测另1P，未与整包重复相加。公开重建命令由reviews/fin/report.md、summary.json记录；旧v1副本、runs/bundles与旧handoff仍是历史，不误用旧wrapper。

## CHAIN：来源及槽位闭合，弱关系仍保留partial

保留36槽位/59原claim/52原gap及原顺序；当前31partial/4unverified/1N/A，claims为11corroborated/41partial/7unverified，没有新关闭gap。11来源和46按槽位访问处置记录不是46个可核独立HTTP请求，实际请求数未知。

C051降为partial：CATL单方供货声明和买方项目投运新闻不能拼成买方确认供货。C053当前无日期页面不证明旧cutoff已公开。修复跨槽改绑、引用省略、失败/错源访问冒支持、单布尔标志授corroborated、域名后缀伪装和公开CLI KeyError。原RED有些在缺侧车处提前失败或改错deepcopy对象，已修测试使其真正击中语义。

整包72P；之后必要受影响复测最终73个不同用例通过，真实搬迁断言生效。11条URL中本次10条可读，SEC submissions读取失败另记；官方页面人工核证与离线软件测试分开，不能用测试通过率当事实正确率。

## 测试证据、隔离与清理

实际证据根：C:/Users/郑曾波/Projects/invest-quick-scan/runs/input-acceptance-2026-10-14-01/。各reviews/<lane>/report.md、summary.json、repair-manifest.json、logs/<lane>的process/stdout/stderr/XML，以及source-publication.result.json完整保留。只有标准进程收据才用作测试证据；简化rebuild生成记录缺PID/hash字段，未升级为进程测试证明。

父子进程keyless、禁网、仅单lane写入；child PYTHONPATH保留caller已验证的同lane搬迁路径与顺序，不暗回原candidate。隔离探针证实外部/跨lane路径、外库写与联网被拒；它不代替产品自身的安全测试。后期批次记录代码/输入起止SHA，变动批次不视为最终稳定绿。

快照4626文件/73,482,137 bytes。当前与已发布源的fixture/handoff原件逐一核rawSHA，BLIND1632、FIN1635、CHAIN894件保持。Windows MAX_PATH导致的假缺失与真正缺失区分；初次快照因源CHAIN旧test-run-01约29MB合成预算反例超限停止，后续明确排除此历史tmp并保存错误，不删源历史证据。

本轮真实测试PID按创建UTC核闭包，防止Windows复用旧PID误认活进程；三个自有temp根均空。源历史CHAIN临时文件与原cleanup说法不一致，未伪造其历史清理回执。只清本轮自建临时物，失败日志/锁/候选/旧handoff保留。

原真实work.sqlite SHA236e5aa4c4252a37f76c092100c8012c9abff11ee60914edb839bf424b0864e2保持，仍18；原13HTTP/26native搜索/CNY1.268162/30题/0正式评分/ACK0不变。根2026-10-10 README他人修改保持。本轮收费模型/用户key搜索API、公司文档下载、生产DB和名单写均0。Financial/G3/F05/生产UI/一键/全池继续开放。

## 接回主线

COMPANY-AGENT-01由外包继续。ResearchRun目前不是BLIND支持格式；须收到真实交付后显式版本映射，保持原题/答案/失败槽及逻辑样本与物理请求分母。共享检索的逐题search_calls归因、缺失metadata、claims注释和参考资格不能编造，不能把费用逐题重复加总。当前BLIND的search_calls必填非负整数，缺合法归因时保留gap，不能填0或把公司总搜索数逐题复制；真实Company样本与映射尚未验收。

总控回原B01先做真正只读inspector与owner配置核对，不直接把会落库的owner preview叫只读；原真实18库不SQL改状态或用合成确认代替真人。最新只读实证为26条leased（已无有效lease；15 length、11 completed但无已接纳checkpoint）和4条result_ready（均insufficient_evidence；standard_answer=4，delivery_revision=0），旧“4 blocked”只描述入库阻塞，不是当前SQL状态。13次物理请求已占原15次上限，剩2次不足后续至少4次的配对实验；按用户既有预算授权扩展实际策略版本、上限与owner报价，保留原13次，不重置账本。原owner根缺config/quick_scan_refresh.json和控制记录，先恢复真实配置，不能复制namespace/store_id冒真实owner。

具体只读命令、需要核对的当前字节与接线备忘在本轮reviews/next-main-preparation.md及company-agent-blind-integration-notes.md。用户后续实施与预算授权已存在，无须泛泛重问；软件签收不替代产品的实际owner配置、预览和原生TTY确认。具体配置及预览准备后再按公开入口完成真人确认，避免重复已绿长链或伪造确认。共享搜索归因未知不写0，原始attempt/失败槽必须保留，参考资格另行独立核源。
