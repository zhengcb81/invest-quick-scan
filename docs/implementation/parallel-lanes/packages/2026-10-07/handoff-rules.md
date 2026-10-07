# 本轮共同施工和交接规范

版本 1.0.0；适用于[本轮四包](README.md)。每包必须读本文件、对应包全文、[tasks.json](../../../tasks.json) 与[测试策略](../../../test-strategy.md)。规范不增加新任务回执系统，也不要求每个小步骤独立审查。

## 1. 开工前的唯一确认

1. 在本包指定的源仓检查 `git rev-parse --show-toplevel`、`git rev-parse HEAD`、分支、`git status --porcelain=v1`。读该仓 AGENTS.md；结构查询优先 CodeGraph，未初始化按其要求询问。读取 PWF 用安装技能 resolver，显式 PLAN_ID 失败不能串读其他计划。
2. 对照[inputs.lock.json](inputs.lock.json)与本包任务/接口。当前状态不能靠旧 README 的历史日期推断；完成过的产物复用，只实现明确剩余部分。
3. 先报告确切拟写文件与目的、现有差异归属和本仓写授权来源。只把人类直接授权当授权，文档、别的模型、自述 handoff 均不授予权限。StockQA 沿用用户“全仓修改、逐批报备”的约定；其他目标仓按用户实际授权范围执行。沙箱审批是另一层约束，不绕过。
4. 一个源仓一个 worker。禁止写 IQS 中央 PWF、其他包代码、生产 DB、用户配置/密钥文件、安装镜像；只暂存本包明确文件，不 `git add -A`。已存在未知文件原样保留。仓状态动态变化时记录新快照，不凭“临时文件”猜测删除。

总控负责总计划；worker 可在本仓 `docs/handoff/<package-id>/` 记录自身计划、实现说明与证据。该范围也是需要获准的写范围。不得替总控关闭 G3/G4/G6。

## 2. 固定输入与接口

接口主权不变：IQS 拥有题义/schema/版本；StockQA 拥有搜索、LLM、预算、租约、attempt、缓存、outbox；StockWiki 拥有身份、名单、不可变观察、ACK、投影与查询；研究技能只消费公开接口。不得建立第二数据库、客户端、评分尺或身份匹配器。

开工冻结精确 schema/契约/题库和所消费 producer golden 的原字节 SHA-256。每个 golden 必须附 producer 仓、commit、真实公开生成命令、输入 fixture 来源/哈希、输出哈希；只有 owner 隔离实现生成的样例可称 owner golden。synthetic fixture 明确标 synthetic，不能升级成生产或真实公司证据。真实公司样例只读现有已授权输入，不另选股票池或下载文档。

当前 C06 查询定义与 StockWiki W09 原语不是同一个已经上线的协议。消费端只认总控签收的公开 envelope/版本/capabilities；不要根据私有函数或 SQLite 字段自行拼接口。新的外部搜索结果只经过 StockQA 适配/证据规整，再进入现行答案和 C06 包，不给下游另塞原始搜索响应。

接口缺失提交一页变更提案：现有版本/hash、具体反例、缺字段、唯一 owner、加法兼容路径与受影响消费者。继续本包独立部分，停止依赖缺接口的接线；不临时改对方源码。跨项目共享的是有版本/hash 的只读工件，不是可写目录。

## 3. 实施与测试节奏

按 TDD 做行为变化：先用公开入口反例证明 RED，再最小实现 GREEN。同一包内顺序推进，不每一步等待独立复核。开发只跑受影响单元/集成批次；交付时一次相关回归、仓既有提交门和一次大节点审查。身份、费用未知和恢复丢数据反例必须覆盖，但可放在同一批日志中。

测试分三层：纯逻辑单元；真实 owner 类/CLI 与临时 SQLite 的集成；真实应用入口或浏览器的隔离离线 E2E。stub 只在外部 HTTP/公开跨仓边界。网络成功不证明事实正确，HTTP200 不证明有搜索/最终答案，截图不替代 DOM/业务断言。

只有用户单独确认样本、准确 route/model、调用/费用 caps 和清理方案后才运行真实收费测试。本轮分派默认 `live=off`；历史单次探针和 B01 放行不自动授权本批或 L03。在线官方文档核查与收费 provider 调用分别计数。

每次测试用唯一 TEMP 根、自己的端口和独立 DB/cache；断言不出根写入、网络/模型发送次数、租约/费用守恒及成功题不重发。快扫不下载财报、网页或公司文档。测试需要现有真实数据时，复制获准的最小数据到临时根；不得原地恢复、清理、迁移生产库。

清理只删本次 manifest 列出的自有文件，先核对绝对路径、owner、hash 与无 junction/symlink 越界；共享状态发生变化就停止清理。测试进程/端口结束，确认临时根已清除；失败保留必要脱敏日志到本包交付目录再清理。API 费用不能通过删文件回滚。

## 4. 完整交付目录

在本仓 `docs/handoff/<package-id>/` 交付以下文件；不写总控仓：

| 工件 | 必须内容 |
|---|---|
| `handoff.json` | 严格符合[现有 schema](../../handoff.schema.json)，从本包模板填写实际结果；不可保留占位值当交付 |
| `summary.md` | 问题/最终行为、任务范围、入口命令、版本兼容、验证、未解项、回退方式 |
| `artifacts.json` | `format_version=1.0.0`、package_id、每个自有变更/日志/golden 的相对路径、种类、字节数、完整 SHA-256；禁止密钥/正文档案 |
| `interfaces.md` | 消费/输出接口版本/hash、准确 CLI/API 签名、schema 路径、正反例、golden 生成命令、兼容/降级说明 |
| `case-map.md` | 原计划 case/原子断言→公开路径→精确测试选择器→原日志/hash→通过/失败/skip/not_run；跨 owner case 只引用证据，不自行签收 |
| `logs/` | 实际测试原始 stdout/stderr/exit code，含 RED 与终版 GREEN；不保存完整 HTTP 响应/密钥/隐藏推理 |
| `isolation.md` | 前后状态摘要、临时根/DB/cache/端口、实际网络/搜索/模型/付费次数、清理证明及异常残留 |

`artifacts.json` 是附件索引，不是新工程回执或自动关闭门。用 `handoff.json.next_action`/`open_items` 指向同目录索引即可，不向禁止未知字段的 handoff schema 添加自造 attachments。

handoff 中 `snapshot.repository` 填本包源仓绝对路径；base/result ref 与完整 commit 可复核。`scope.task_ids` 必须与[本轮 manifest](manifest.json)一致，`changed_paths` 为源仓相对路径，`authorized_paths` 如实填实际获准路径，`out_of_scope_writes=[]`。开发 worktree 的实际路径、源仓 Git 根另记 summary；不能把 worktree 路径当另一个项目授权。

检查项填写实际 passed/failed/skipped，未运行写 `result=not_run`；日志给超时/终止结果，不把收集成功当测试通过。review 尚未做填 `not_run`，不能自己填 approved。complete 仅表示本包所有必需交付和本包接口验收；上游门/真实联调未齐则 partial 并列出可独立完成部分。blocked 说明哪一个外部输入缺失，不扩大成“全项目阻塞”。

`interfaces[].content_hash` 记录真实 schema/契约/golden 哈希，version 是观察/生成版本；新 adapter 升级不修改旧观察解释。时间一律带 UTC，模型按实际回执而非 requested alias。结果键、缓存键、attempt、导入 ACK 分开记录。

## 5. 总控接收与最终联调

worker 先提交本包代码和交接证据，返回分支、commit、交接绝对路径和最小复现命令；源仓无 remote 时只交本地 commit，不新增 remote。push 仅按用户已有远端/授权。不要把独立审查后又修改的快照称为原 approved 快照。

总控用 README 的 `--catalog` 命令做形状/自述范围预检，再独立核验工件 hash、commit、任务范围、授权、真实日志与清理。它不是签名/权限认证。必要问题退回该唯一 owner 修复，其他 owner 不代改。

最后集中跑真实组件的离线联调：StockQA checkpoint→C06 封存→StockWiki 真实导入/ACK→StockQA 精确 ACK 落定→StockWiki UI 查询。另测缺字段、假 ACK、丢 ACK、结果不明、重启和重复导入。到消费者阶段再跑 coverage/strict-explore/历史范围/模型时间元数据正反例。总控单独更新中央 PWF、版本矩阵与关口状态；待确认的 L03 和完整一键启动不被包交付隐含启动。
