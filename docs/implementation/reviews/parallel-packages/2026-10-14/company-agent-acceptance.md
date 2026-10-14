# COMPANY-AGENT-01：总控验收与直接修复

2026-10-14；结论为**离线工程交付通过**，不是公司评分准确性或真实实验结论。

## 交付与实际提交

工作目录：`C:/Users/郑曾波/Projects/iqs-company-agent-lab`，分支`master`。收到的HEAD为`366001f8c451a6df08ee02c3ba33a68c8599d64f`，原业务结果提交`a12cfc7e1ed8e399957a03ebb0d485761e11fe18`。原交付冻结268文件、3,487,627 bytes，179项artifact逐条校验无差异。源仓原有一个未跟踪测试生成board，已记录并保留。

总控修复代码已正常提交为`94b2d181c349b831c46d02740b09d9adc5ae40d9`；发布及清理文档提交为`51b5b3e18ef3d30c1f240b988d64a0b28fc001b1`。源码与候选逐文件HEAD/rawSHA校验后写回，48个精确文件；追加两个清理/发布文档。没有重签或覆盖原harness交接、旧fixtures、旧schema、历史replay-pack；源仓tracked业务clean，原未跟踪board原状保留。Lab只做本地提交，没有另建或猜测远端。

当前软件版本`0.2.0`，默认执行`execution_revision=2`；新增model/search request均为独立`1.0.0`协议，新ResearchRun及checkpoint为`1.1.0`。原问题对象和answer-content保持不变，原1.0输出与事件按rev1回放。原行为用例作为兼容性测试，不能算新版闸门或金融准确性证明。

## 实质发现与修复

|环节|交付中的反例|修复后的行为|
|---|---|---|
|模型真正读到的信息|只有问题文字、证据ID；read工具不返回正文；短directive可能截断题目|独立版本请求携带完整原题/锚点/answer schema/tool schemas、公司、截止日、证据摘录与工具结果；稳定与动态hash入事件并在回放时核对|
|自主策略|free_agent固定按4题切片，未实现预注册“先拿12题”|新版本拿到全部12题，可读证据、自选题目子集、保留逐题最终槽位；模型私有上下文只通过opaque handle续接|
|计量|同一物理ref的tokens/时长重复；query=0变1；reasoning在output内仍双计预算|物理ref去重，0和unknown分开；未知变已保存响应可补一次观测；未知usage停止后续模型派发；包含关系明确时reasoning不重复累计|
|恢复与隐私|checkpoint丢压缩状态、URL冲突索引；原pending receipt/tool args可能保存思考|checkpoint1.1保存必要状态并重建冲突索引；泄露仅留安全摘要；重启新segment、不恢复隐藏思考；检查点核心状态与原事件history交叉校验|
|完成与修订|单位冲突先记完成；声明题号不符、重复JSON/patch、null抬分、length终态可能被接收|完成前执行schema及绑定闸门；严格JSON/题号集合；修订须expected hash与新证据，拒绝重复项和无新证据抬分；截断不算完成|
|证据变化|替代证据后，原关联答案仍是completed|只重开引用旧证据的题目，保留不相关已答及历史revision|
|公开CLI及路径|内存通过不能证明文件schema接受新事件；输出journal名可越界；深路径搬迁失败|新事件/schema显式版本化，公开CLI核实际文件；输出前拒绝越界/重名；Windows长路径验证及搬迁可复现|
|报告|报告缺实际证据板，且未验证metrics引用|新封套带证据板rawSHA引用，report校验文件hash和引用/绑定；篡改metrics或重签篡改checkpoint均拒绝|

验证先新增会失败的反例，再实施修复。中间红批、Windows权限失败及隔离guard长路径比较错误均保留，不计作最终通过。顶层两个免安装launcher已由总控按原公开CLI要求纳入范围；这是修正原manifest漏申报，不扩大其他仓库的写入范围。

## 最终验证与清理

- 发布字节闭包：**113 passed、2 skipped**，17.19秒pytest耗时，父进程18.04秒。代码输入hash稳定；没有边测边改。
- 独立真实Windows junction：**1 passed**，实际链接存在，拒绝经链接导出且目标未写入。两个整包skip分别是symlink创建权限和guard不允shell构造junction；后者由此真实案例补证。共114个不同用例通过，不把重复回归次数相加。
- 新版本覆盖两家虚构公司×三策略。测试运行时只从真正收到的context生成合成回答，不能旁路读取公司板或gold；另覆盖read→自选尾题→继续完成、跨公司隔离、稳定前缀、费用未知、依赖失效、公开CLI replay/resume/report正反例及原版本搬迁/漂移。
- 无密钥环境、禁网、仅允许Python子进程、写入只限本轮候选/temp/log/review。真实模型HTTP **0**，搜索HTTP **0**，真实费用 **0**；没有读API key或下载财报/整页文档。
- 本轮专用临时根已清空：删除3,261个文件/59,173,570 bytes；先验证并移除唯一指向同根空target的junction，再检查其余无链接后清理。冻结原件、候选、失败及最终日志保留；不删除源仓原有测试残留。沙箱外CIM只读核实匹配本轮路径的Python/Node/cmd进程为0，没有终止其他进程。

本机原始证据：`runs/company-agent-acceptance-2026-10-14-01/`。其中`intake.json`、`delivery-plan.json`、`logs/company/delivery-byte-closure.*`、`source-delivery.json`、`source-closeout.json`、`cleanup.json`可关联实际HEAD、原/新字节、PID、UTC、退出码及清理结果。源仓自包含接收记录在`docs/handoff/COMPANY-AGENT-01/coordinator-acceptance-2026-10-14/`，附原始测试日志和当前版本synthetic公开CLI示例。

复核命令（Lab仓根，无需安装）：

```powershell
python -B -X utf8 -m pytest -o addopts= -q tests
python -B -X utf8 -m iqs_company_agent_lab replay --task docs/handoff/COMPANY-AGENT-01/coordinator-acceptance-2026-10-14/examples/rev2-free-agent/task.json --events docs/handoff/COMPANY-AGENT-01/coordinator-acceptance-2026-10-14/examples/rev2-free-agent/events.jsonl --strategy free_agent --output runs/rev2-free-agent-fresh
```

输出目录须为全新路径。旧`handoff/replay-pack`保留原交付版本；当前实现与便携测试以仓根为准。CodeGraph未初始化，已经按AGENTS提出询问，尚未擅自建索引；不阻塞已完成的隔离验收。

## 没有关闭的门与下一步

该交付实现并验证的是**公司agent研究执行的离线机制**。没有运行真实S0–S2；不能给出A/B/C金融准确率、价格、速度或KV缓存收益的赢家。`qualification_granted=false`，FIN参考资格仍0，原90个null保持；不能把合成分数、格式完整或多模型一致当正确答案。

接入StockQA时必须消费完整model/search request，实际搜索要使用公司身份与截止日，不能只取旧短directive。原owner运行时仍须负责发送前精确token/费用预留、超时/取消、真实模型参数、每次物理attempt原收据、顺位冷却和unknown结果判定；Lab不另造HTTP、重试队列或预算库。BLIND桥须显式支持ResearchRun1.1、多attempt及共享搜索归因；unknown不填0，不能编一个provider request ID代表整个公司会话。新版真实执行前补独立预注册addendum与新输入锁，原冻结v1不原地改写。

本轮没有改StockQA/StockWiki、真实名单或生产数据库。原work19 SHA仍`a5e77ef5aa427b630a0a463e2cb9088a38ab7619f38b0a0d27eadbe572dafb05`，25leased+1failed+4result_ready；13次历史请求/CNY1.268162/0正式评分/ACK0保持。原IQS01结案不重跑，既有单项原生确认不扩权到新12题研究。Financial/G3/F05/生产UI/一键/全池继续开放。

主线下一步仍是[B01剩余25项有界原生批量恢复](../../../plans/b01-native-batch-recovery-2026-10-14.md)，之后将本次版本化研究端口接入原StockQA并按预注册跑小样本。只在包级/主线大节点集中TDD、集成与E2E验收，不新增helper复核门，也不重派已签收的包。
