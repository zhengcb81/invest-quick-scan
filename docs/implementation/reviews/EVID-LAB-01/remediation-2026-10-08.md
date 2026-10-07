# EVID-LAB-01整改：保留现有实现，完成一批修复

给原Lab harness的自包含接续卡。唯一写仓仍是`C:/Users/郑曾波/Projects/iqs-evidence-lab`，沿用原[施工卡](../../parallel-lanes/packages/2026-10-07-wave2/EVID-LAB-01.md)及授权/共同规范。IQS/其他仓只读，不重建仓、不reset/clean、不收费、不抓新来源、不扩大样本。总控[验收](acceptance-2026-10-08.md)基于HEAD d87cf718a0fa90f2d0929e902ad2faa70c39580a；开工先核新HEAD和活动writer，相关差异不能按旧hash覆盖。

## 一批修复范围

1. `semantic.py`和相关测试/fixture：期间dict保留year/quarter/half等明确子期间；Q1/Q4、H1/H2不得pass。目标period有year而claim没有时abstain。字典/字符串互相比较、半年/全年/年化及缺字段留具体理由；不靠关键词补年。
2. URL窗口与诊断来源：无期间窗口abstain；同报告比较列/同URL不同内容片段可以互补。只有明确claim目标与所引用期间冲突才fail。来源URL去重与片段内容hash分开，不增加独立来源数。保留synthetic、historical_model_output、agent_review_only来源类别，不伪造真实来源正例。
3. `hashing.py`/`fixtures.py`/CLI与schema/test：所有公共JSON入口用严格重复键/非有限值检查。historical fixture完整复制的chunk/answer须绑定原归档全部投影或canonical hash，改score/rationale也必须被发现；不能只核state/parse_error/question_ids。输出fixture原字节input SHA、存在的答案canonical SHA，以及expected/observed字段定位。没有字段/正文就abstain，不反推来源。
4. `cli.py`真实写入发布：第二文件写盘失败不得留一个看似可用却无法重试的exclusive输出目录。先完整验证/计算，在Lab自有受管临时目录写齐并校验，再以不会覆盖旧输出的方式发布；失败清本次临时产物，已存在目标不变。若采用明确失败标记/恢复机制，须提供公开重试行为和等价测试，不能只catch异常返回1。
5. 提案仍`execution_enabled=false/live_not_run=true`。逐题主分母冻结300计划槽（同时报告实际发出、未发送、失败包内、unknown、结构有效、带claim和给分子集）；answered-only只能是条件指标。给具体mixed/themed两组各五题、题面/锚点/身份/截止日hash、query/参数/24搜索共享规则、context选择与单位/表头约束、逐模型token上界×冻结价、检索缓存key/version/有效期与实际模型revision缺口。纠正crash_resume不能自动重发未知预约。对Phase96既有结果说明差异，不复制新网络/预算/缓存实现，不把草案直接翻开关。
6. 交接可复现：修正37项工作树/Git EOL hash口径。可以同时声明Git blob/工作树原字节及准确导出/恢复方法；或在实际授权覆盖下采用精确-text后重冻结。不要随意全仓改行尾，也不要把Git hash不符叫内容篡改。fixture数量是34、expectation42、诊断记录350；锁是224次校验而非224不同文件。`pyproject`正确声明真实运行依赖jsonschema，或明确只在预安装环境运行及入口限制。

## 固定RED和最终验证

总控[counterexamples](acceptance_cases.py)可只读复制到Lab自有测试根并适配fixture路径；不要直接在IQS ROOT运行带输出的脚本。用卡中同样真实函数/CLI和持久文件，磁盘失败可在文件IO边界注入，不stub owner计算。九方法已有8个真实失败、另一个Windows锁定非index拒绝已通过，保留该负例。新增source category/agent标签、fixture input/answer SHA/定位及300槽分母案例。

开发先固定这些RED、最小GREEN；最终一次相关54原方法+新例集中回归、公开CLI三历史归档/34fixture重放、明确失败路径和不同新根稳定重放。原IQS输入hash前后不变；历史396/186/24/326/48、不可测264项等分母保持原义。没有新源码行为不重复收费实验或旧审查，不给小helper另加审查门。

测试全部在自己独占临时根、环境无密钥、guard每个子进程继承；清理前绝对路径/owner/逐文件hash、无link/junction、进程终态核实。不能只写ignore_errors=true和目录为空就自称恢复；严格检查不支持时报告具体缺口。

## 交回总控

更新原`docs/handoff/EVID-LAB-01/`，保留历史原日志；新结果commit、HEAD、before/after、准确命令、版本、artifact bytes/SHA、case-map六组整改与RED/GREEN/清理证据。代码先commit再写交接，允许后续交接commit；交接清楚区分源码结果commit与证据HEAD。只提交本仓获授权路径，不创建remote，不写IQS PWF，不自关L02/G3/F05。

标准：既有重算/来源分层不退化；8固定错误改正，元数据可追溯；提案要么实质冻结且非执行，要么明确draft并列缺口，不冒称预注册已签。总控随后一次集中回验，不自动发新live。
