# UI-COMPARE-28-R1：公共响应保真、选择/模型维度和安全交接修复

交给原COMPARE harness即可。唯一写根 `C:/Users/郑曾波/Projects/iqs-comparison-view-lab`，继续 `codex/ui-compare-28`。基线HEAD `dd99431d3abda7920cb0a6b0377dae01bc7b53ef`；原handoff指be2ce169、原final review指ab2f486，这正是待修证据问题，不要误选它们当当前HEAD。

先读 [共同规则](handoff-rules.md)、[锁](inputs.lock.json)、[原范围](../2026-10-28-independent-support/UI-COMPARE-28.md)、[总控报告](evidence/compare-final-report.md)。报告/反例是实际独立验收结果，原业务源未改。索引本地元数据两路径属总控授权初始化，不删。只修本卡根因及回归，不实现新生产API/金融评分/第二数据层。

## 必须全部关闭的六组问题

| ID | 位置（基线） | 已复现的问题 | 最小合格行为与回归 |
|---|---|---|---|
| C28-01 | compare_view.js:178–285、323–354；compare_client.js:159–172 | 原history返回reported_score/answer_status、payload.answer/execution；投影把原8分及信息日/版本/coverage等丢成null | 同时支持原entity和history不同形状，按字段实际来源保真；嵌套明确null不能被外层旧5/8覆盖，缺字段保持未知。通过真实交付client链而非只喂理想扁平record |
| C28-02 | compare_client.js:146–147；compare_view.js:1929–1941、2002–2035 | client丢raw groups，view只在raw groups找原理由，展开详情找不到已知summary | 建有界内存原件索引或明确原件resolver，以精确observation/source pointer绑定；实际client→mount→点击cell可看原理由/来源，不能写日志/导出viewstate/新库保存答文 |
| C28-03 | compare_view.js:520–592、1261–1284 | 同qid旧/新package，先按首package过滤，指定OBS_NEW反被变成missing | 显式observation选择优先且可达；保留多版本来源/口径差异，不把新题义混为同尺，不重算分数/静默latest |
| C28-04 | compare_view.js:1221–1240、1283–1284 | 不同provider同model名被合成一列，provider取首条 | 使用声明的完整模型身份区分列/过滤/标签，已知revision也诚实区分，未知revision不补；不同提供商能并列原3/9分 |
| C28-06 | tests/browser/cdp.mjs:301–321；tests/integration/cli.test.mjs:82–101；browser/e2e:27–40 | startsWith(tmpdir)接受兄弟前缀，再cmd/rmdir+rmSync；安全stub已拦截证明越界；第二E2E抢18772 | 一套原生删除API、实际resolved本人拥有根校验、启动失败/超时finally/PID-profile拥有证明；负例无真删除/spawn。浏览器只用本包18771或动态端口，不占另一包默认18772 |
| C28-07 | 原handoff/review/final/invocation与payload清单 | C、reviewer、manifest不一致，evidence SHA=null，reviewed_file_hashes是文字 | 保留旧原件，修复后真实不同agent最终审查，最终新C/input lock/file hashes/实际调用全闭合，新R1元数据M不改C；本Lab校验器须拒绝这些反例 |

C28-01新增可读serializer参考在本批锁内：StockWiki `quick_scan_observations.py:681–697`解码原history；`quick_scan_profiles.py:223–299`输出entity field；`ui_quick_scan.py:144–156`及IQS `dashboard_owner.py:342–356`公开路由。只消费这些冻结源结构做**合成结构fixture**，不是读取真实答案/库或伪造owner golden。

## 反例与必须保持的控制

- [4个产品反例](evidence/compare-product.test.mjs)：当前旧版本4F，原断言保留、只将import变为IQS_R1_COMPONENT_ROOT；需作为本Lab永久回归并修为4P。
- [清理安全stub](evidence/compare-cleanup.test.mjs)：当前1F，原破坏API全被拦截，实际spawn/delete=0；参考共同规则，**不能先运行危险原CLI/E2E来复现**。
- [正确连接生命周期控制](evidence/compare-connection-control.test.mjs)：当前1P，dispose→new mount能拒旧pending。外部直接重新赋值config.connectionIdentity不是已声明可观察更新API，**不作为本轮功能阻断**，不要为它造新状态机；host接入说明补切连接也dispose/remount即可。

保留动态题数、不同entity/ASJ/security/segment不混、qid题义/rubric冲突提示、null/NA与日期模型缺失、pair owner verdict精确绑定且不能从row flags合成true、XSS/窄屏/键盘/分页/dispose的已有断言。新公共fixture要覆盖完整实际client→view链，避免同一个错误投影同时造输入和验输出。

## 运行范围、完成和交回

总控已跑原unit88+安全integration58+perf1，另连接控制1P；原CLI21/browser2未跑，不是它们绿色。清理根因修好并过全拦截边界负例后，在独占副本跑本包完整unit/integration/perf和一次真实浏览器mock E2E；普通用户路径须实际看理由、选择跨版本观察、查看两个同名不同provider列。零真实owner/API/数据库/付费，不跑主工程小时级全套。

只在输入/原红→合并修复回归→最终真实独审三个大节点留证。所有六组和独审发现全部关闭再交；不能用“major已修/还剩minor”写open[]。

新package_id=`UI-COMPARE-28-R1`，新交接位置：
`C:/Users/郑曾波/Projects/iqs-comparison-view-lab/docs/handoff/UI-COMPARE-28/remediation-01/handoff.json`。

使用原handoff1.0.0；配套report/tests/artifacts/cleanup/review全齐，真实C/M和最终独审同共同规则。原旧交付保留。总控之后才合入原UI，production_ready与financial_qualification_granted仍false。
