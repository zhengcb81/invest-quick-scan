# 三家公司参考研究并行包

2026-10-12 编制；**施工卡和输入已准备，未创建工作仓、未派发、未开始研究**。FIN R4软件/来源说明签收（103P），原90参考题仍9completed/9gap/72not_started；每家公司24题未开始。本批拆原剩余研究，不是软件R5返工，不重做已绿校验器。主线仍沿checkpoint31/B01工程，真实金融/G3/F05/owner/UI门保持开放。

| 包 | 工作量与目的 | 唯一写入目录 |
| --- | --- | --- |
| [FIN-ALPHABET-02](FIN-ALPHABET-02.md) | Alphabet30题：补24题，保留并复核6深核，广告/云/AI投入与反证 | C:/Users/郑曾波/Projects/iqs-reference-alphabet-lab |
| [FIN-CATL-02](FIN-CATL-02.md) | 宁德时代30题：补24题＋6深核剩余缺口，电池与储能经营/现金/周期事实 | C:/Users/郑曾波/Projects/iqs-reference-catl-lab |
| [FIN-CSC-02](FIN-CSC-02.md) | 中信建投H30题：补24题＋6深核缺口，证券业收入/风险资本/客户资金与周期 | C:/Users/郑曾波/Projects/iqs-reference-csc-lab |

三个根编制时均不存在，路径互不包含；开工仍要重查writer，存在且归属不明就停止写。可以同时交给三个harness；没有彼此前置，也不依赖B01修完/真实模型回答/StockWiki新golden。总控不自动派发。

每卡含自足上下文、具体优先级与测试；必须同时读[共同规则](common-rules.md)、[接口与合并契约](integration-contract.md)、自身targets、[39文件锁](inputs.lock.json)、[manifest](manifest.json)及同名handoff模板。原 FIN code/data/20题集输入在本机IQS自有 runs/parallel-reference-2026-10-12-01/inputs/fin，绝对路径逐项在锁中；工作harness只读复制到自己的fixtures/fin，依赖不被改写。未来源仓变动使用该冻结快照继续，不能偷换成current。

本批按同一台Windows主机编制。若harness在另一台机器，交付时还须携带39份只读冻结文件及锁并明确新路径映射；只发Markdown或从远端拉IQS不能保证包含本机runs输入。不能因缺输入去复制生产数据库/密钥或用最新源替代固定基线。

交付不是第二公司库或LLM客户端。每包交现有pack1.1.0与ledger1.0.0的完整90行候选，仅自身30行允许改；外公司60行保持，新增source/fact/calc ID各自命名空间。总控提取各自变化、核冲突和反证，再合并回原FIN并做B01盲评；不把三份90简单相加成270题，也不让三个worker改同一共享文件。

人工/可用浏览工具查公开官方网页，允许检索导航；不调用额外LLM API、Brave/Tavily等付费API、不读key、不保存财报/PDF/网页全文。保持冻结cutoff与无法判断/null，不为凑完成率编数字或评分。每题定向尝试充分后真实不可得可gap_terminated，逐条写实际渠道/找什么/结果/停止理由；入口或TLS失败不能推出整公司无资料。

验证节奏：少量业务RED→研究与工具实施→一个稳定候选集中unit/integration/公开CLI E2E＋一次包级事实审查；修复只回归受影响部分，不增加小节点门。`validation.json`只有本批文档/锁/目录/模板预检，不是研究、产品或金融门通过。

交回各自 docs/handoff/<package-id>/handoff.json，内容接口见integration-contract。收到后总控负责实际集中验收与唯一源仓合并；若仍有问题，总控按用户最新要求直接修复，不再发新整改卡。实际不可得/主观评分/owner资格如实开放，不改成假绿。
