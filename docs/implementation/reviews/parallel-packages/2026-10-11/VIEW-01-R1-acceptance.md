# VIEW-01 remediation-01 集中续验

2026-10-11，结论 **changes_requested**。G1核心关闭；G3比较声明降级和按观察绑定关闭；保留布局、来源片段、键盘及正常分页等改进。余项只续原G2—G5的[唯一R2](VIEW-01-R2.md)，不重做已绿组件，不增加小节点门。本次不接生产StockWiki、不授予金融准确性或owner资格。

## 实际交付与边界

- 源：`C:/Users/郑曾波/Projects/iqs-viewer-lab`，分支`codex/view-01`，HEAD `4d7662b44d34de8ac476621dc59dd09be81df9b6`；产品`7069420759d04bf23fcb0e270c7942d7ca18ce6c`为实际祖先，无remote。实际状态仅`?? .codegraph/`。
- 181跟踪文件只读冻结到IQS自有`runs/view-r1-acceptance-2026-10-11-01/source`。18原锁输入匹配，原`docs/handoff/VIEW-01/`交接文件字节未变。
- 新manifest列183项，其中178非索引工件bytes/raw SHA匹配；另外5项为未跟踪`.codegraph/`动态设施，不复制、不冻结其数据库、不称183项稳定产品全部匹配。下一交接应排除索引设施。
- 公开handoff CLI PID71684/exit0，仅证明交接形状和声明范围。handoff最终130项/129P/1skip与本次实跑一致；README仍写124/85+20+19，是旧轮计数，需统一。

## 集中实跑

完整原suite：PID78052/exit0，64.51秒；JUnit130项，129P/1skip，unit89（88P/1skip）、integration20P、真实Chromium E2E21P。Windows无符号链接权限保留跳过分母，软件测试不算金融准确率。

前两次沙箱运行分别PID33820和76068在Windows asyncio本机socketpair等待；诊断栈、空stdout/stderr和真实终止记录保留，只终止核实父子关系的自有进程。解除本机通信沙箱限制后同套件通过，不把环境等待算产品RED，也不虚称三次全绿。

另20个独立公开validate CLI合成控制（原15＋补5），每次重算实际工件摘要；原始PID/exit/stdout/stderr及小输入保存在自有根。五类形状输入实际exit1/traceback：profiles整数、profiles null、portable source_urls整数、comparison.reasons整数、source_watermarks整数。profiles对象未按数组拒绝，仍supported。没有伪造真实owner正例。

独立浏览器PID33124/exit0，7.26秒，五场景确认：banner.none仍强制演示；unknown原5显示未知及`—`；响应快照冲突仍进入旧快照详情；键盘进入详情聚焦H2；真实browser Back至裸`#/pool`清空筛选并恢复9行。正常返回行焦点由原E2E验证；独立场景点击导航tab后焦点在tab按钮，不当作“返回按钮恢复焦点失败”。390px真实截图显示股票池已经卡片化，不再逐字压碎六列。四个独立服务实际释放，browser route仅允许loopback，记录无外部页面请求；不宣称操作系统级浏览器防火墙。

## 按原五组判断

| 原组 | 结论 | 证据与剩余问题 |
| --- | --- | --- |
| G1 标记/评分 | 核心关闭 | 强制banner、固定状态语义、未知原分冲突、恢复恒不加分均成立；保留原分异常说明 |
| G2 报文/严格读取 | 部分通过，继续R2 | raw版本/operation/不一致ID已降级；但两端同时缺ID仍supported。必要result/profiles/链接等形状仍崩溃或静默空；validate的build_view_model在try之外。banner.text等closed schema类型未落实，独立总字节上限尚缺 |
| G3 比较/facts | 比较关闭，facts继续R2 | 比较仅演示声明、按ID多声明合并可保留。真实caps响应facts_producer_ready=false，顶层available引用该exchange后仍available关系；source=owner_reported也不验证实际供数。不能由来源ID存在性自授能力 |
| G4 快照/范围/分页 | 继续R2 | 正常snapshot/revision分隔和100/150显示可保留。request S1/response S2仍把9题挂S1；异store或异perimeter仍混入同snapshot/ASJ/rev键。合法distinct 100+50合成两页把第二请求cursor改错后仍loaded150/is_complete=true，未验证游标链。水位族缺实际query上下文 |
| G5 详情/布局/接口 | 主体改善，收口R2 | 两挂牌/日期、卡片、焦点和Back保留。API missing_detail_note未被页面采用；新接口清单仍遗漏web所需page_size_limit和snapshot wire_version；交接旧计数/动态索引项需整理 |

独立agent做一次原包只读审查，结论与上述反例合并，见[独立记录](VIEW-01-R1-independent-review.md)。其结构与类型反例不另设逐项审批门；小显示null、卡片空标签等只作同批低优先级完善，不升级主线阻断。

## 资源收尾与接续

按已核绝对自有根、文件ID/大小/hash及闭合硬链接集合清理2079生成文件/200目录，包含TEMP、两浏览器profile、hostile bundle和性能样例。保留小反例、原日志、截图/trace、冻结副本及控制器。181源与副本字节、HEAD/status再次匹配，CIM自有Python/Node/Chrome0，四个独立端口释放。源Lab、既有浏览器安装、其他writer、生产库/名单和B01活动根未改；模型/付费搜索/公司文档下载0。

原writer只在VIEW Lab接续R2；主控保持B01 checkpoint31唯一工程动作，FIN/OPS各自R2。当前只验demo组件，真实owner接线、UI生产门、F05/G3/facts/一键/全池仍开放。文档本地提交；新文档推送仍沿先前自动审批拒绝后的明确范围授权约束，不称远端同步。
