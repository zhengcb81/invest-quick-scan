# VIEW-01 R2：原五组余项接续

唯一writer：用户原VIEW harness；唯一工作目录`C:/Users/郑曾波/Projects/iqs-viewer-lab`。原[五组R1](VIEW-01-R1.md)及[本次续验](VIEW-01-R1-acceptance.md)为上下文。**不重做G1；只补G2—G5剩余边界，一次集中TDD/unit/integration/真实浏览器/review。** 不增加小节点审查，不代改StockWiki/IQS/其他Lab，不启动真实API/生产库/名单。

## 开工基线与保留

接收HEAD`4d7662b44d34de8ac476621dc59dd09be81df9b6`，`codex/view-01`、无remote、仅`?? .codegraph/`。原产品7069420759d04bf23fcb0e270c7942d7ca18ce6c为祖先，181跟踪/18原锁保护；先核动态HEAD/status，若另一writer改变，记录差异并协调，不reset或覆盖。`.codegraph/`非本包产品，勿触碰/归档它的DB/WAL/SHM。

保留原交接目录和remediation-01全部记录、原固定锁、130分母129P/1Windows skip（unit89/integration20/E2E21）、强制banner/评分状态、恢复不加分、比较demo按ID绑定、原报文片段、正常范围、两挂牌/日期、390卡片/键盘/浏览器Back。新交接追加`docs/handoff/VIEW-01/remediation-02/`，不覆盖旧报告、输入或日志。不因供数缺失发明比较/事实API/身份/总分算法。

## G2：类型、真实报文与有界失败

先加入可失败反例：两端request_id缺失或null；profiles null/5/对象；source_urls=5、comparison.reasons=5、watermark.source_watermarks=5；banner.text非字符串；必要主体/result字段缺失。坏数据必须稳定exit2，无traceback；未知未来wire可明确unsupported且不提取。保持正确未知态、合法null和bool分数的既有展示语义。

明确实际消费字段的必需性及类型；不要仅匹配报文六个头。冻结owner协议与Lab展示扩展分开说明，扩展不冒称owner正式字段，不用“一律套owner schema”破坏既有已明确展示的合法Lab扩展。两端ID必须存在、类型有效、对应；未知版本先降级。cmd_validate/serve共用稳定失败路径，不能只有serve兜底。closed bundle schema与执行体保持一致；默认/可配置单文件、数量和**累计字节**限制在全读前核验，重读/源片段仍服从同一预算。用小可配置阈值测试总量，不为测试制造巨量文件。具体输入可读总控自有cases作只读参考，不依赖它作为长期fixture。

## G3：facts依赖实际能力，比较已关闭

反例：顶层fact_relations available/source exchange:caps-11，raw冻结capabilities1.1 facts_producer_ready=false，带有合成portable关系。不得只因ID存在输出正式available；另测来源owner_reported、不同owner、没有正式关系供数的get_profiles引用、raw能力不覆盖与声明矛盾。

实际消费被引用capabilities的已支持版本、owner、覆盖和供数内容。旧get_profiles2.0/能力1.1没有正式facts供数承诺，诚实unsupported/not_collected/not_provided；展示合成关系可明确独立demo信息，但不授予正式供数资格。available能力也不证明每公司已经采集；来源缺失、冲突、不支持、不可用、未采集须可区分。不可因没有真实owner正例自造新版能力或把全部原portable关系强称owner验证。比较维持已绿演示声明/观察绑定，不回炉、不授予资格。

## G4：完整范围与真分页链

反例至少含：request snapshot S1/response watermark S2；同snapshot/ASJ/revision但不同store；同键不同perimeter/full subject_ref；同universe不同query/operation；distinct合成100+50两页的第二request.cursor接错、缺页、页重复及顺序交换。

连接池→详情→history/facts/risk时核完整身份范围和owner/query/快照；冲突不能覆盖或拼接。key/索引内部实现可自由选择，协议迁移显式说明，URL不能丢范围。没有实际query绑定信息时隔离并标不可比较，不靠同universe推定同query。请求和响应快照必须对应，水位仅同实际owner/query族比较。

分页保存并验证真实request cursor与前页next_cursor、snapshot/query/operation/范围一致性；不能用累计rows>=matched且最后cursor=null自证完成。未知cursor语义诚实未验证/不完整；不能生成owner cursor。合成两页可以复验正确续接，断链/重排缺页不能声明完整；loaded行数、去重主体数、owner计数分别按真实口径。不要把UI本地分页等同owner完整采集。

## G5：缺失态与交接收口

缺同快照profile时采用API missing_detail_note，说明该wire未供数据；不将旧公司一概称新公司。保留双挂牌或明确未提供原因、日期和信息范围、有效键盘路径及窄屏布局。补实际web用到的page_size_limit/meta、snapshot wire_version、新范围定位/分页字段的完整接口映射，区分Lab适配与owner真实字段。null/卡片标签可同批低优先级补，不另加门。

新README/case-map/handoff/review必须用同最终JUnit分母，原124轮计数保留为历史不得当最终130。工件只纳入本包稳定产品，排除动态.codegraph、临时profile/cache；清单bytes/raw SHA以最终字节生成，注明自排除。核实际产品与交接commit祖先关系；真实临时根清理，不虚填cleaned。旧资料原字节保护，源已有个人设施不代删。

## 一次集中交付

公开CLI仍`python -B -X utf8 -m iqs_viewer_lab validate --bundle ...`与本机只读serve；新增行为/version在interfaces说明。先失败反例，再最小修复；稳定候选一次unit+integration+E2E（包括真实browser Back与具名返回按钮）和独立包级审查。只续跑受影响项，原129P/1skip保留准确计数，不能把软件绿当金融准确性或真实owner E2E。

父子去key；复用已安装浏览器，不下载；仅隔离自有TEMP/profile/port，browser route拦外网并记录，不冒称OS级隔离。结束验证owned process0/端口释放，先核绝对路径/文件ID/硬链接闭合再清自有缓存与合成临时输入，保留必要日志/screenshots/trace/反例。不得清总控B01根或其他writer。

remediation-02应含handoff.json（公共1.0）、git-baseline、interfaces/integration-map、case-map、review、isolation、artifacts、原日志/JUnit和本包PWF。总控可用既有wave2 manifest和parallel_handoff_cli结构预检；结构通过不自动签收门。本包做到剩余四组关闭即可，真实StockWiki接线和主线金融/发布门仍由总控负责。
