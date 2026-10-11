# VIEW-01-R1：同包集中整改

状态：待原 writer 接续。唯一写根 **`C:/Users/郑曾波/Projects/iqs-viewer-lab`**，沿用 `codex/view-01`；总控不代写、不自动派发。先读[集中验收](VIEW-01-acceptance.md)、[原卡](../../../parallel-lanes/packages/2026-10-11-wave2/VIEW-01.md)、[共同规则](../../../parallel-lanes/packages/2026-10-11-wave2/handoff-rules.md)和原锁。本卡是原卡的边界补充，不新设生产门。

起点 HEAD `dff410526ef4475845db885994f2eee5c9805cd6`，产品 `dcf5305791bc440b1334256fddf7e1abb0c6e5a4`。124业务原件/122工件/18锁输入已核实。用户授权的 `.codegraph/` 是总控随后新增设施，不当业务漂移，不删、不提交索引。开工重查 HEAD/dirty/writer；若有新的业务变化，说明具体差异再在新基线上保留修复，不能 reset 或清他人文件。

保留原组件、71P/1skip、原 handoff/截图/测试日志及输入锁。修复下述**五组根因**，先写实际 RED，再实现；同一稳定候选一次集中 unit/integration/真实浏览器/独立review，失败仅重跑受影响部分。不要每个 helper/小步骤加审查，不重新做预研，也不造真实 owner 正例。

## 1. 不可覆盖的演示、未核实及评分语义

banner必须从data_kind强制生成不可弱化的演示/未核实提示；annotations只能补充，不能none/空文案覆盖。状态必须保留原词义和原始值，labels.unknown="已评分"不能使主要显示变成已评分。unknown/insufficient_evidence/not_applicable/error即使原值1–10，也不能渲染为有效分；保留异常原值及明确冲突说明，不填0/5、不自行升格。正常scored1/10、null/bool11、expired8可读但非当前资格的旧行为保持。

recovery原始contributes_score=true可作为异常原值展示，但对外展示资格必须始终不加分，清楚说明冲突；不要改写原观察或隐藏真实低分。非评分状态/异常与owner筛选结果分开，UI不能重算白名单或总分。

RED至少：合法闭包bannernone/空、unknown重标签、unknown5与不足证据8、恢复声明true；DOM证明强制提示和状态/分数一致，而非只测内部函数。

## 2. 原 request/response 支持边界及稳定拒绝

已声明支持的exchange要校对原request/response实际schema_version、operation、request_id对应和必要形状。不能仅靠外壳wire/version当supported。冻结schema版本以实际18输入为准（pool scoped2.5、review-lead2.3），不照原卡错误简写反改。

未来/未知wire先降级，不能在skip前解析未知watermark/projection；对象、null、数组、坏枚举类型、重复JSON键、NaN/Infinity按界面协议明确拒绝或安全显示unsupported，不泄漏traceback，坏输入CLI exit2；合法未知版本允许安全保留为unsupported，不强求全部exit2。bundle schema严格JSON可解析，closed定义与执行校验一致。为bundle/artifact总字节/文件数及原始内容显示制定有界读取，不能任意大文件先全读再检查。

来源页能安全查看原request/response或受限片段，并标明是否截断/不支持，保留原bytes/hash供核对；不要仅用路径/hash冒充原报文可读。未知字段不得静默有损变成空值，不能复制owner模块另造身份/评分引擎。

RED至少：外壳2.0、raw9.0及operation不同；request_id不同；未来wire watermark=null/response非空数组；data_kind=[]；schema重复键与非有限值；边界大小。重算artifactSHA避免只测摘要不匹配。

## 3. 比较与事实供数不得自签

任意portable.owner_comparison.source=self/owner字符串均不是独立证据。冻结get_profiles2.0未承诺比较/入库/事实扩展，缺正式已支持owner结果就显示“未提供/未支持”，历史仍可并排。不能新增本地比较算法或给整题组统一资格。若做明确合成比较演示，要标“演示声明，非owner验证”，绝不作真实可比资格。

只有已支持且可核对的独立owner结果、明确的观察ID集合/两端身份范围/版本与引用对应时才显示具名结论；三条A/B/C只对B/C有结论，不能扩到A。不要改StockWiki或假定未交付的owner CLI；若当前契约不供数，把总控接线缺口写清即可。

facts capabilities需消费支持的实际capabilities exchange；顶层自述source=exchange:...须确实存在且匹配。声称available不代表该公司已采集关系；无来源/不支持/尚未采集要区分。纯演示关系保留演示等级，不用名称推断供应商客户。

RED至少：两条只有self可比、三条仅B/C可比、顺序交换不改变资格、事实顶层available但缺/冲突/unsupported来源。通过判据是诚实缺失态或精确消费，不要求伪造完整owner正例。

## 4. 快照与范围不可串读；分页诚实呈现已加载范围

详情/历史/事实/风险请求和索引键保留owner store/query、snapshot/read watermark、完整subject_ref（revision/perimeter/scope）与对应观察范围。旧池详情只能来自同一具名快照，缺相应profile显示未提供，不能用最后一次sid覆盖。不同scope/revision不拼接；不能仅以名称/entity去重代替subject范围隔离。

pool只加载100但owner matched150且next_cursor非空，必须区分已加载行/owner匹配总数/是否完整和continuation；无需本包调用真实owner或做通用proxy。演示可以用同一快照的多个已提供分页交换证明游标续接，或准确显示“仅本页/后续未提供”，不能谎称100完整。水位比较仅在同owner同query/snapshot族内，并区分owner声明与UI显示顺序；不同store/query时间不能推出陈旧，candidate_set也不能无依据恒判当前。

RED至少：同ASJ不同revision两个快照，旧池→详情→历史→返回全程；不同subject scope同entity；partial100/150游标不丢；异store/query同日期/不同日期无误标。合成重复行的总控反例只是字段丢失控制；正式分页测试请自造合法且不同subject的synthetic fixture，勿声称真实golden。

## 5. 实际详情、简洁布局与交接接口

正式profile不提供listings/scope_as_of时，从同快照明确owner pool供数连接，或逐项显示“该wire未提供”，不能有两挂牌列表却详情静默空表。保留全部挂牌、revision/perimeter及信息时点；不生成入库时点或按名字合并。field_id已在原portable存在，不应无故显示null；coverage未知字段不能渲染undefined。

桌面把常用名称/分数/依据放清楚，长ID/hash可折叠；窄屏390×844用卡片或局部可访问横向表格，避免六列压成逐字竖排。保持页面不溢出只是必要条件。键盘进入详情移到标题/主内容、返回恢复原行或合适fallback；浏览器返回无参数#/pool恢复空筛选，不保留隐藏筛选。保留普通返回按钮的筛选状态及清晰空/错态，不做装饰图。

integration-map/接口文档必须列web实际依赖全部字段，例如page_size_limit与meta形状、快照参数、各页面缺失态；区分Lab适配字段和冻结owner已有字段。不可仅说“替换API”便承诺接线可用。没有owner供数的功能明确not_run/pending，保留disabled入口。

RED至少：同公司A/H详情两挂牌或具名缺失原因；无field_id/coverage的诚实显示；Enter/Space、焦点返回、浏览器Back、桌面/窄屏真实截图与DOM布局；合成2000行仍有界且不推金融/全池容量。

## 一次交回

在 `docs/handoff/VIEW-01/remediation-01/` 留新 handoff/实际Git基线/工件清单/五组case-map/一次review/隔离前后资源记录/PWF。原报告不覆盖；输入与schema版本不静默漂移；product_commit须实际祖先，最终artifacts按最后字节生成，self排除规则明确。正常提交自有代码和文档，不push无remote Lab；不碰IQS、StockWiki、StockQA、其他Labs或全局依赖。

测试环境限自有runs，父子含Playwright driver不继承API key；现有浏览器用独占profile，所有自动请求限loopback，来源不下载。结束关闭自有进程/端口，删除profile/TEMP/合成性能产物，仅保留日志/截图/trace/反例；不把声明cleaned当实际清理。重跑原suite及五组受影响反例，明确P/F/skip分母，软件通过不当金融准确率。

供复现的总控私有纯合成输入和实际日志在 `C:/Users/郑曾波/Projects/invest-quick-scan/runs/view-acceptance-2026-10-11-01/`（cases、logs、screenshots）。可只读参考，重新生成到自己的runs，不在总控目录改测试。本卡不授权读生产DB、真实LLM报文/思考过程，也不授权收费请求或签收生产门。
