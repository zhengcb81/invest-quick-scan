# OPS-DESK-01：可演进的实操手册与故障诊断桌面

## 范围和职责

唯一写根 `C:/Users/郑曾波/Projects/iqs-operations-lab`，关联 O02/X02/X03/X04/X05/X06/X07/X08/X09 的支撑文档和诊断展示，不接管启动器、执行器或数据owner。读 [共同规则](handoff-rules.md)、[manifest](manifest.json)、[输入锁](inputs.lock.json)。不依赖 VIEW/FIN，也不占正在写的生产仓或现有 Lab。

现在主线真实失败记录充分，后续要一键使用且较弱模型也能维护。需要把“能安全做什么、什么只是设计、何时必须等对账”写成实操手册，保留实际版本边界；不要开发另一套 doctor/调度/恢复/预算程序。

## 实际交付

1. 用户手册：首次配置、用户给名单/手工增减、查看现有结果、开始/续扫、停止派发、额度等待、模型顺位、故障恢复、版本升级/备份。每个动作区分当前已发布入口、拟定入口、owner未就绪；无实际help证据的拟定名称不可抄成可执行命令。
2. 维护手册：源码/安装镜像/运行数据分工、StockWiki identity/query与StockQA任务/预算/outbox唯一职责、轻资产边界、原始观察不改写、版本回退只读、升级保留旧schema和历史。
3. `content/incident-catalog.json`：稳定 incident_id、symptom、需要的最小证据、原owner状态、允许动作说明、禁止误操作、恢复完成应核的原owner回执/状态、能力版本条件、来源引用。状态机/金额由owner提供，不在本包推断结算/批准重试。
4. 合成脱敏诊断 bundles 与只读 validate/render 工具，用来演示手册、测试关联和错误展示。工具不读取生产SQLite/环境变量，不运行探测命令、恢复命令、模型或网络；不是新的 system doctor。

## 最少覆盖的故障场景

| family | 场景和必须保留的区别 |
| --- | --- |
| O01准入 | 缺名单/凭据/route/subject、provisional身份、近名歧义；不自动选公司、合并或造ID |
| O02提供商 | 401密钥、403能力/套餐、429五小时额度、502/503、连接失败；可切顺位与不应误切的情况分别引用原策略 |
| O03已发送不明 | timeout/中断但不能确认vendor未收到；保持uncertain/预算预留，租约过期不是可重发证据 |
| O04已收到无答案 | completed但invalid、length截断、thinking占满、可知费用已settled；只按owner可验证决议进入新generation，不修改旧答案 |
| O05投递 | QA检查点≠StockWiki ACK；request_id缺失≠response_id可冒充；outbox blocked/重复ACK/原包损坏 |
| O06币种预算 | CNY vs旧USD-only能力、未定价/unknown费用、physical请求与题数区别、套餐次数与现金分开；无汇率不转换 |
| O07权限 | owner preview过期、撤销、TTY/真实principal、permission与registered replay差异；hash不是权限 |
| O08查询 | owner读故障、schema不支持、空覆盖、旧水位、不可比较、未知/过期/不适用分开；不能显示全池0家公司或0分 |
| O09运维 | writer冲突、安装版本/hash不一致、SQLite backup/migration未就绪；不删库/改旧账本/force升级 |
| O10隔离 | 实验下载/浏览器cache/进程未终态、路径越界/重parse/硬链接；只清本包ended资源，不动真实live现场 |

每family至少一个正常对照和一个失败/危险误判例。以上不意味着让 worker 执行这些真实动作；操作员命令只作为经过核实的说明，工具永不执行。

## 交接协议、CLI和输入信任

closed `iqs.operations_case_bundle/1.0.0`：`protocol,bundle_id,data_kind,source_inputs,incidents,observed_states,evidence,limitations`。每evidence有相对路径、bytes/raw SHA、角色；observed_states有owner/protocol/version、原状态摘录、observed_at、synthetic标记，不允许API key/vendor思考/公司文档。bundle内部hash只能检测漂移，不能认证owner或授予重试；无独立owner证据一律unqualified。

closed `iqs.operations_render/1.0.0`：bundle hash、明确unqualified或synthetic、incident证据引用/缺口、引用手册章节、API_requests=0、actions_executed=0、warnings。不给动态 next_command，不输出 approve/retry_safe 布尔替代owner判定。未来wire拒绝，不静默修补费用/ID/状态。

```powershell
python -B -X utf8 -m iqs_operations_lab validate --bundle fixtures/incidents/bundle.json
python -B -X utf8 -m iqs_operations_lab render --bundle fixtures/incidents/bundle.json --output runs/desk-01
```

这是本包要实现的离线 CLI。exit0合法、exit2不合法；render只新建自身输出，不覆盖，不拉源URL，不打开任何数据库或自执行bundle中的 argv/path/URL。拒目录穿越、链接、绝对外部引用、坏hash/重复JSON键/未来schema/伪造资格。合法unknown与资料不完整须能渲染且醒目，不假报验证成功。

手册命令清单 `content/command-inventory.json`：owner、operation、status=published_verified/design_only/not_available、精确文档或help fixture来源hash、支持版本、是否读/写/付费、实际owner入口；只读索引，不提供可执行调度。源定义缺真实help时保持design_only，不能根据函数名猜argv。允许对冻结源码文档作静态检查，不在外仓执行或测试。

## 施工步骤、TDD与向后兼容

1. sole-writer/Git/PWF/锁冻结。先整理owner职责和命令发布状态，保留设计与实际差别。
2. RED：uncertain当失败重试、4unknown当正确/0分、费用乘题数、CNY当USD、receipt/hash当owner认证、坏版本、记录缺失当空库、生产清理路径混入；断言工具拒伪造批准并完整呈现缺口，不复制原状态机。
3. 建catalog/schema、十family样例、中文操作手册与离线render。稳定ID不复用别的含义，旧1.0只读，不更新老案例成新现实。
4. 集中unit（引用/状态标签/闭合）、integration（锁/hash/确定渲染）、真实CLI E2E（随机cwd/中文空格、坏bundle失败无正式输出、外部命令不执行、无网络/环境读取）；一次review，并证明合法部分数据不被误拒绝。

交 `content/`、`schemas/`、`src/iqs_operations_lab/`、`tests/`、`docs/handoff/OPS-DESK-01/` 与[模板](OPS-DESK-01.handoff.template.json)。README给清晰入口，手册章节有故障定位导航；交总控 integration-map，列需要发布后再核的真实help/命令，不能把pending写成已运行。

## 总控怎样接入

总控源码发布后统一核真实 CLI/help/版本，把可用手册接一键入口/设置/维护页面。最终doctor/start/resume/迁移仍在原owner实现。该包不关闭X09/G6/预算/恢复/全池门，也不替代现有SW备份、LOAD容量验证或QA-NET故障路由测试。
