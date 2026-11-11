# 工作树、PWF、整合与交接

本文件配合每包范围使用；不是新的运行准入系统。

## 开工与不相互覆盖

1. 读取该源仓AGENTS、当前PWF和本包。用`GIT_OPTIONAL_LOCKS=0`读取HEAD、tracked diff与本包相关untracked清单；不打印环境密钥。不凭旧文档判断树干净。
2. 在`C:/Users/郑曾波/Projects/iqs-modularity-worktrees-20261111/<包ID>`建该仓独立worktree，分支`codex/modularity-<owner>-20261111`。路径若已被别的作者占用，换唯一后缀并记录；不要覆盖。**这些路径当前只是规划，尚未创建。**
3. QA和RT先比较本包指定canonical/临时候选；IQS/Theme承接已有WIP。用已选路径的patch加明确新文件移入独立树，不复制整个仓库、不丢未跟踪API、不带密钥/DB/运行回答。仅从HEAD新建会丢候选，禁止静默这样开工。
4. 如同一文件同时有未归属修改，先保留并记录双方diff，在隔离树合并；只对有冲突的块协调，不再为整个仓重复问权限。不得`reset --hard`、`clean -fd`、整文件覆盖canonical或`git add -A`。
5. 实现阶段每仓单作者；包外依赖只读。发现跨仓问题发给其owner/总控，不进入对方仓“顺手修”。

候选归拢是一次工程工作，不需要新的hash账本/签发机制。一份短的来源及保留项列表足够。对于不相关文件变化，不重新创建任务或使整个包失效。

## 每仓自己的 PWF

普通owner在自己的工作树下使用`.planning/modularity-closeout-20261111/`，三文件：`task_plan.md`、`progress.md`、`findings.md`；设置该harness的`PWF_PLAN_ROOT=<工作树绝对根>`、`PLAN_ID=modularity-closeout-20261111`。不要覆盖仓库原有其它根计划。

task_plan只需从本包填入：本域目标/非目标、输入HEAD与候选、公开依赖、RED/GREEN步骤、当前状态、单一Next Step。progress记录真实命令和结果；findings记录根因/接口差异。不要抄几百行IQS历史。

IQS总控继续使用根三份PWF；MC-IQS不另建竞争主计划。Dashboard遵守既有D00：包作者只写D00分配的子计划/交接，由D00更新`unified-dashboard-2026-10-26`主计划；不能由IQS强行设置/覆盖其主计划。D00协调是避免写冲突，不是再申请用户授权。

## 测试和独立审查节奏

- 实现一组行为：相关RED→GREEN及相邻回归。新测试进入已有fast/default/对应专项入口；Runtime的历史交付核查与legacy回放明确分开。
- 包完成：运行本包短组及受影响的owner常规检查；调用**不同agent**读最终完整diff、亲跑关键反例/公开替身测试。实质缺陷由作者修完，再请其复核变化。不是每个小commit独审。
- 不以手写用例总数或审查报告hash决定能否运行产品。记录实际结果，不复刻旧receipt/freeze体系。
- 测试使用自有短临时根（Windows避免深路径），可注入时钟；清除测试进程中的API key并禁止外网，允许literal loopback。只清理本次创建的根、PID和端口，finally恢复；不删用户下载/原回答。

## 一份短交接即可

统一位置：各自工作树`docs/handoff/<包ID>/handoff.md`；Dashboard可依D00既有位置，在交回消息给出绝对路径。内容：

```text
包ID / 工作树 / 分支 / 输入HEAD / 最终实现commit
实际修改路径与保留的并行修改
公开入口、protocol、兼容范围（无变化也明确）
已验证TDD行：命令、结果、运行的源码来源；未跑项及原因
独立agent：身份、审过的实现commit、结果、修复事项、剩余实质问题
测试清理与生产数据/API是否触及（简短事实）
总控如何复现 / 依赖哪个owner尚未交付
```

一包可以包含多个源码commit。最终实现commit不要求包含审查自己产生的文档；后续仅加文档的提交无需循环重审，若改代码则针对变化复核。无需handoff JSON、逐assertion回执、源码副本或精确用例计数签名。

## 总控组合验收

Owner包完成后，IQS记录一张简表：`repo → 实现commit → public protocol → 契约结果 → 合并状态`。这只是复现实验来源，不成为产品运行时的全局release-set许可。

从每仓自包含提交导出到短临时根/独立worktree，安装其已声明依赖；新进程没有`.tmp-*`、历史fixture或机器PYTHONPATH兜底。组合根统一选择代码根/entry point。消费者测试可以屏蔽提供者内部模块；**真实集成不能屏蔽提供者自己的内部依赖**，否则是在制造假失败。

|组合场景|实际运行与断言|负责人|
|---|---|---|
|I1 公开互换|IQS/CA/RT/QA公开接口；替身与真实adapter分别运行；版本/缺必需操作的反例|IQS总控，owner定位失败|
|I2 正常与共享共用持久化|原SDK、脚本化provider wire、隔离QA库；普通和共享各跑代表题组，保存逐题结果|QA + IQS，不能只测imports|
|I3 付费窗口恢复|在响应落盘/逐题保存/封包/ACK前后中断；混合成功/待处理/已交付分清response_available与never_sent：已付和已完成分支API增量0，never_sent仅按原授权首次发，unknown先查回执；ACK不重复入库|QA/SW公开入口，IQS编排|
|I4 缓存与时钟|fresh复用0请求；expiry后正常刷新；只读查询/导出不续期；旧答在无新key时仍保存|QA/SW拥有规则，IQS展示|
|I5 查询到研究消费|同一隔离SW的事实query、分页、导出、重开；TH和IN从公开命令生成各自结果|SW/TH/IN；包含错身份、错operation反例|
|I6 原工作台|IQS启动内部export到自有运行根，单次完整snapshot HTTP读接口；bank available/roster unavailable/answers partial仍显示可用内容与原因，正式结果不受影响；名单/任务/恢复走原HTTP，页面重开不重发/不续期|IQS/MC-UI；新进程/隔离配置|
|I7 Dashboard|m6结果与m8任务从真实IQS HTTP/CLI到UI，超时未知只查状态；未安装owner源码的fake路径另测|D00/MC-DASH与IQS|

至少包含三个市场的**有效测试身份向量**、同名/ticker冲突和动态题集；可使用已有去敏真实公开DTO与合成分支注入，不能把合成结果称真实模型/金融验收。原三市场真实扫描成果保留，本专项不重新付费问一遍。一次场景覆盖多条断言即可，不必构造数百套组合。

当前源码组合入口必须与Runtime根conftest/locked fixtures隔离；在报告里列实际加载owner源码根和提交。真实源进程成功到ACK/查询，才叫集成通过。旧实验回放有价值，单独标legacy，不能冒名当前链。

## 并线、发布和退出

1. 各owner先形成自包含提交；无远端的仓记录本地提交，不创建新远端。独立工作树分支可推既有origin，不能强推。
2. 总控合并依赖owner，再合消费端和IQS；源仓有并行改动时合并精确commit，不覆盖WIP。Dashboard由D00合并其m0/m6/m8改动。
3. P3通过后按上述组合切一次部署、跑轻量只读/恢复smoke；不要求每个无关提交都重跑昂贵E2E。
4. 有远端的核对实际SHA及相关CI结论；未跑/待运行如实记录，不能用push成功代替CI。
5. 所有列明边界和上述场景通过、最终独审无未解实质问题，关闭模块化专项。根PWF回到F05/W11真实业务覆盖与TH/IN产品使用，再按原计划推进G3/G4—G6。**不把金融准确率或2000家公司全部扫描另加成架构收尾条件。**
