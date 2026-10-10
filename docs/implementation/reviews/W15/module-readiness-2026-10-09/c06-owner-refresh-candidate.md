# C06 当前主体刷新与主入口接续：私有候选

2026-10-10。总控 `/root`，工作区 `runs/c15a`。本文件是 Phase113 原步骤4的实施记录，不新增审查门。完整 C06 集中审查、真实公司 context2 owner golden、生产发布及金融准确性门仍未关闭。

当前实现及执行 SHA 以 `docs/implementation/intake/W15/c06-query-2026-10-09/producer-checkpoint-03.json` 为准；此前 checkpoint01/02、RED 日志和原始输入保持不变。不直接运行旧 publisher，不把本候选源码或测试复制到生产仓后宣称验收完成。

## 接通了什么

1. StockWiki 公开 `quick-scan-route-refresh --c06-subject-bound` 使用真实 current route、原 issuer/security/listing serializer 和现有只读 QueryReader/IQS 固定离线 CLI，读取已正式导入的原 Observation、PRE-dispatch receipt 与独立主体 sidecar。无外仓 Python 导入，无新答案库、身份主档或费用账本。
2. 原 W06 时效与模块兼容逻辑仍决定逐题复用。新路径拒绝缺库、未知 schema、读取失败和当前主体缺失；旧未绑定历史不获当前主体覆盖。被拒绝或冲突的 owner 记录不复用。
3. QA `OwnerRefreshClient.prepare` 明确选择新路径；`reference` 核对独立主体、身份 revision、原 payload hash、执行 UUID/provider/model/prompt、原 receipt 和当前冻结问题口径。引用原答案，不为它创建新工作、新模型调用或新 C06 包。
4. 持久 owner-refresh binding 1.0 保留原行为；2.0 明确要求 observation context2。沿用原 schema15 的不可变绑定表，不回写或升级旧绑定。新版缺上下文必须在 send-intent 前拒绝，旧版不能被同键重新绑定为新版。
5. QA 公开主运行器支持 authority3，完整标准答案运输同时接受既有 authority2。模型配置名和真正 adapter 名分开保存，复用比较经现有 allowlisted endpoint resolver 得出的实际 provider，不能用 `primary` 等配置别名冒充服务商。
6. IQS 固定离线 CLI 增加显式 `questions` 操作，从经过原冻结发布校验的完整 manifest 导出 `stockqa.identified_questions/1.0.0`。保留旧 `questions.json` 字符串导出；新文件中显式携带 question_id/text。接收方继续对全题 ID、顺序及 prompt SHA 做双向绑定，不从正文猜 ID，也不截短正式问卷。

## 时效和资格的区别

答案期限仍取原 observed_at 与 information_as_of 两个期限中较早者；`now < valid_until` 才能复用，等于期限已过期。导入、复核或查询缓存重放不刷新答案年龄。模型、题义、范围、identity revision 或 perimeter 不同，不能借缓存绕过重扫条件。

查询捕获的一小时 TTL 仅决定能否重放那份捕获，不能证明答案新鲜或当前路由有效。刷新时重新读 current owner，不使用旧 capture 冒充现状。读取仍明确是分库顺序捕获，并通过 owner anchor/revision 及 QA 二次核对保守拒绝变化，不能称跨库原子事务。

当前原回答的 check_level 保持 `unverified_model_output`。发送和导入验证、答案复用许可、金融事实准确性及白名单资格是不同判断。本候选没有把分数自动提升为已审计投资结论。

## 真实软件测试边界

测试走实际 owner SQLite、真实 owner serializer（其身份/receipt/市场注册内容均是合成 fixture）、公开 fixed OS CLI、实际同步 LLM client 和 main、工作账本、完整封包、原 import_package 与 owner ACK。替换供应商 HTTP，不调用真实模型/搜索、不下载公司文档、不触碰真实名单或生产库。

`producer-main4`：完整冻结24题、真实一请求测试预算；只回答一题，其余题明确待续，故首轮是部分扫描而非整家公司成功。实际导入、绑定配置中的 owner、落原 ACK 后，再次运行引用同一 Observation，HTTP 总数仍1，原 package hash 不变。这是主入口接续证明，不是全问卷或真实公司准确性证明。运行耗时111.56秒包含隔离初始化、多个跨进程 owner 校验、故意预算耗尽及重启，不能当作线上 LLM 用时或收费基准。

`producer-rf2`：54项当前主体复用、旧 owner-refresh、模块时效回归通过。`producer-rfinal1`：85项通过，2项仅在自有 SQLite 改名阶段因 fixture 未关闭连接失败；首次关闭末尾连接后，rfinal2为1通过/1失败，发现较早 HTTP 回调也未显式关闭测试连接。已全部明确关闭；剩余证券范围定向结果见 rfinal3。不能拼成一次全87绿或金融准确率。

未知 schema 反例在 `finally` 逐字节恢复原测试库；缺库反例仅对已核对位于自有 tmp_path 的文件改名，并在 `finally` 恢复，拒绝时不自动重建库。所有进程已终态后才修改源码。保留原守卫 SHA、来源执行 SHA、JUnit、stdout/stderr 和失败回执；完整 C06 发布前仍使用 c15a，不能提前清理。

## 下一步与接手约束

- 给统一启动增加明确、受控、可审计的 owner schema3 初始化入口。当前 strict refresh 对未初始化库明确拒绝；测试显式初始化不等于首次用户启动已接通。
- 把私有环境依赖的新增测试整理成生产可运行的测试配置，不能把 `IQS_C06_OWN` 缺失的 collection 错误留给下游。
- 收到或合法生成真实公司的 context2 owner golden 与生成命令后，沿本公开链核验正反例；当前 owner serializer 的合成 G2b fixture 不代替真实公司 golden。
- 同一完整 C06 大节点收尾后一次集中审查，按源当前 SHA 做最小发布，再推进原 G3/L03/B01/F05/事实/UI/TH-IN/全池门。
- Git 向现有 origin 导出跨仓源码的具体问题仍待人类答复。此前问题列34份；checkpoint02已有41份，本次更多。不得将旧允许清单套给新候选，也不得重新运行旧一次性 freeze/publisher。自动审批拒绝的原因是此前泛授权未被识别为覆盖指定跨仓源码及目的地，不能改命令绕过。

两独立内容施工包保持已交付未自动派发；Lab CodeGraph 30文件/611节点/1297边已确认，无重复 init。总控继续唯一拥有 IQS/QA/SW 集成写入，不侵入两内容包源目录。


## 2026-10-10 接续补记

当前新增独立refresh/1.0.0预览契约与原QA预算/待办只读检查，分别25P/8P。StockWiki适配器仍在施工、未验收；原确认/耐久提交/执行器消费未完成。用户已明确许可本文等精确7文档到指定origin；此次不包含源码或真实数据。


## checkpoint06实际接续

**2026-10-10 当前接续（checkpoint06，覆盖下方历史）：** 精确7份第一方文档已正常提交推送a0d283de665f91740190b2371b4722a2af25e557，远端master相同；未导出跨仓源码/真实golden/数据库。独占runs/c15a的StockWiki公共刷新预览已走实际OS账户、当前主体/成员/模块锚、冻结Query2 capture和原Q09/Q13只读账本，并保存不可变owner控制工件。当前63份私有候选，未集中审查/源码发布。最新35纯契约＋1公共CLI为同次36P；受影响账本/工件/公共CLI另批19P。此前128项为126P/2F，坏JSON已拒绝但错误边界未归一，修复后19P；不能拼成128全绿或金融准确率。result_ready只需导入续传时新增HTTP/费用为0，不因模型额度耗尽阻断。动态名单/模块须owner显式current_owner_members/current_manifest配置，身份仍由真实serializer独立验证，不以名称join。全部测试终态、guard原字节不变、0API/生产库/名单写。唯一下一工程动作是已认证owner对精确预览的独立确认、耐久幂等交给原Q13并在原Q09发送时扣账，再其余原C06操作；完成整个节点后一次集中审查，不增小节点审查。实际用户确认/收费提交尚未发生，C06/W15/G3/F05/L03/B01/事实/UI/TH-IN/全池门保持开放。c15a与real-owner-01仍用不清；两个内容包未派发。



## checkpoint07实际接续

**2026-10-10 当前唯一接续（checkpoint07，以下均为历史）：** 独占runs/c15a已有原生owner交互确认入口与不可变幂等工件，公共CLI会拒绝管道/自报确认；确认前后重核精确预览、当前主体/成员/路由/政策/原预算，scope变动要求新预览。另有固定owner只读同意检查入口与原Q13单事务批量登记原语（复用原表/算法、不另建队列）。最新同批实际36P/74.04s、子进程7660/exit0/source_changed为空；保留之前30P/6F的计数fixture表名错误原件。原语本身permission_authenticated=false，公共确认仍handoff_pending/registered_with_executor=false；真实owner读桥正例使用明确合成的同意工件，实际人类确认/收费提交/公开Q13接线尚未发生。67私有候选checkpoint07已固定，未集中审查/源码发布，0API/生产库/名单写，guard不变。唯一下一工程动作：固定QA OS桥读取owner原件，绑定完整authority3/context2及精确question/subject范围，再耐久幂等登记/公开重放/原主执行器消费，Q09仍在实际发送前扣账；之后其余原C06操作并同节点一次集中审查，不增helper审查。7份获明确许可的第一方文档已实际推送a0d283de665f91740190b2371b4722a2af25e557，远端一致；本次后续同7文档的实际Git结果按documentation-publication-02.json核对，代码/数据库/golden不在该导出范围。C06/W15/G3/F05/L03/B01/事实/UI/TH-IN/全池门仍开放，活根不清、内容包未派发、目标active。

