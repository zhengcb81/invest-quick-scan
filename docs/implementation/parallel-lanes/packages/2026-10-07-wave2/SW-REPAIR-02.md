# SW-REPAIR-02｜备份、可比查询与UI六项整改

唯一工作目录：`C:/Users/郑曾波/Projects/StockWiki`。原W12/U01/U02的集中整改；复用已交付代码，不重做身份主档、W05/W09/W11或原SW-READY-01。先读[共同规范](handoff-rules.md)、[接口](interfaces.md)、[锁](inputs.lock.json)和[原整改卡](../../../reviews/SW-READY-01/remediation-card-2026-10-07.md)/[独立报告](../../../reviews/SW-READY-01/intake-review-2026-10-07.md)。本卡不继承新的写授权；由用户实际指定唯一writer、授权下列路径后开工。

## 已知起点与范围

`master@04dfc5190589a8bbe224a47e94b045779c884b80`，2026-10-07T20:58:52Z当时clean。原48工件完整不代表验收；真实7场景为6 fail/1 WAL positive pass，3.83s，UI失败项当时仅静态断言。**这六项可以在本仓独立复现和修复，不等QA-C06-02。**真实双owner流水线/恢复再由总控集中验证。

允许源码：`stockwiki/quick_scan_backup.py`、`quick_scan_backup_manifest.py`、`quick_scan_profiles.py`、`quick_scan_query.py`、`quick_scan_rows.py`、`ui_quick_scan.py`；`stockwiki/ui_static/app.js`、`index.html`、`styles.css`。

允许测试：`tests/test_quick_scan_backup.py`、`test_quick_scan_profiles.py`、`test_quick_scan_query.py`、`test_ui_quick_scan.py`、`test_e2e_quick_scan_ui.py`；必要新增同目录`tests/test_swr_*.py`。文档：`docs/quick-scan-backup-restore.md`、`docs/ui.md`及`docs/handoff/SW-REPAIR-02/`。先核现有路径再报备精确清单；超出需要先说明并获授权。

禁止改StockQA/IQS/CWP/研究技能/安装镜像、生产库/名单/config/凭据、原SW交付和原冻结RED；不得为了对齐QA残缺包放宽Observation/ACK。

## 六项最终行为

| ID | 修复与不可妥协断言 |
|---|---|
| SWR-1 | absent与existing-empty恢复成功；非空、并发新文件、junction/越界拒绝。检查到空不授予删目录权限；失败保留原目标，仅清自己的staging |
| SWR-2 | prune仅处理真实create流程登记的受管完成备份。版本/结构/hash/名称/路径安全与**trusted owner记录**均核验；仅created_by字符串、自算digest、目录名字不算owner。foreign/unknown/partial/损坏/链接全部跳过。旧无owner备份按明示兼容可只读verify/restore，不自动adopt赋予删除权 |
| SWR-3 | finalize rename在错误处理内；注入失败不留可被list/prune当完成的partial。manifest成功字段不能早于真实最终提交；崩溃恢复明确partial状态 |
| SWR-4 | 两个accepted导入的不同subject/scope/模型/语义变体均可见。未唯一选择时ambiguous或全展示；不能取最近/最高/最后一条静默合并，>=8规则不靠错误高分入选。多挂牌同issuer仍一行，不同issuer不并名 |
| SWR-5 | UI可增删至少两条分项条件，AND/OR由W07同一服务器规则执行；query/snapshot绑定完整leaf+combine。真实浏览器“一项过、一项不过”：AND不命中，OR命中，改leaf失效旧snapshot，unknown不补5 |
| SWR-6 | 旧9f552a67公开query产生的实际snapshot在新版本继续读取page2、IDs/顺序不丢不重，或明示版本兼容路径。错查询/错条件snapshot仍拒绝；不放宽匹配换绿 |

trusted owner记录的具体存储方案先用现有backup管理结构设计；不得为prune在投资库外创建第二研究数据库。确需新源码文件或store修改，列精确路径/迁移/证明后向用户确认；卡的禁止范围不能用“需要”绕过。文件系统所有者检查与版本化记录的证据边界写清，不能宣称恶意同权限本地进程无法伪造。

## 实施和测试，一包连续完成

1. 只读复核当前代码和原freeze，保留原RED；将原7场景映射到本仓测试。旧query snapshot必须由旧Git实际producer函数生成，不只手算query_hash。公开import产生synthetic subject观察，不手造profiles替代导入路径。
2. 先做备份恢复/owner/partial三项，用空/非空/并发填入、foreign自洽manifest、损坏/链接、rename异常、WAL已提交与旧备份兼容同批TDD。
3. 做projection/variant和查询兼容，核subject revision、security/listing、scope、口径、model/日期对齐；倒序导入、旧高分/新unknown、不同模型同题、同issuer多挂牌与同名不同issuer都不能混分。未知/过期/缺facts保持原语义。
4. 复用服务器规则改真实UI多条件；页面只能展示存储数据，不调用LLM/下载、不在JS重评分。至少测两条件、增删、AND/OR、刷新/导航分页、变体明确展示、恶意短文本安全呈现。
5. 一批受影响unit/integration，再一次真实浏览器离线E2E；真实StockWiki服务+自有SQLite，HTTP模型边界stub。截图/HTTP200不能代替DOM/实际请求与业务断言。确认无源库读写、外部浏览网络/模型发送0，只允许本包loopback HTTP并留本地请求证据；关闭本包服务/进程/浏览器、核端口与逐路径清理。
6. 交付相关全量/静态门一次及同批集中独审。不要重复原990套件为每小hunk刷次数，也不要因为旧GREEN多而跳过六反例。

原冻结反例导出/guard命令和schema/hash在原整改卡。本包修后必须另记新commit/导出manifest，不替换旧freeze。新测试根在StockWiki自身临时目录，不能按原示例在IQS runs里写；如复用总控guard，先在自己的导出根配置只读固定源与可写根，不能关闭guard或改总控脚本。

## 完成与交接

六项固定反例全闭合、WAL正例保留、真实多条件浏览器通过、旧snapshot和未知状态兼容、环境清理与集中审查完成，才签本卡本地complete。TTL/replacement、W15、真实QA导入/双库恢复及F05/golden未完成项明确列not_run，不能伪造完整query能力。

在`docs/handoff/SW-REPAIR-02/`交[模板](SW-REPAIR-02.handoff.template.json)和共同规范全套。额外包括六项闭合表、原/新版本、旧实际snapshot、owner/旧备份兼容说明、真实浏览器日志/截图和公开query schema/capabilities/golden的**实际现状+生成命令**。真实身份golden缺失标missing，不合成verified填空。回退新UI/规则入口时保留所有观察、备份、水位/ACK与历史；不通过恢复生产库演示回退。
