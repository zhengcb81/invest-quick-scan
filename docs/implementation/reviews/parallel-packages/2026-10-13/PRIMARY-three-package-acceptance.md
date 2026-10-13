# 三个PRIMARY包集中验收与直接修复

2026-10-13。结论：三包的软件交付已修复、签收并正常本地提交；来源研究按partial接收，未授金融资格。有效增量已合并回原FIN，不是新财务引擎或新的股票池。没有下载公司文档、保存网页全文、调用付费API或写生产库。

## 当前交接

| 项目 | 产品commit | 最终交接HEAD | 实际测试 |
| --- | --- | --- | --- |
| Alphabet，codex/primary-alphabet-03 | 3bfb5e6a0c1bd625e09a4d879df2da51cd9476dd | 514e9baee37eaa16e0a222ea4e395a5e57cfebdc | 57P，PID70936；另20/20 CLI，PID35212 |
| 宁德时代，codex/primary-catl-03 | bb4fba90d4ebbccf5d634ed47fefbe85c6761439 | 56860915091e66498d7d916d62d68afae2445576 | 84P，PID40088 |
| 中信建投，codex/primary-csc-03 | 21f191640c45b08b039614406a4b4ddbf2a519e1 | 5a72395d0088caf9050a71bd5d2937c32bbd9f35 | 78P，PID55308 |
| 原FIN，codex/fin-ref-01 | cc91670b874d56ccfa45f3b8c71f7e9d25ef1998 | 212eba64f707d098952a8249fa05bf5be95fa6ea | 合并后121P，PID66724 |

最终工件清单逐bytes/raw SHA匹配205/124/122/348项，排除各自清单本身；源工作树仅既有.codegraph/设施未跟踪。首次缺失的Alphabet5个已删除测试scratch不恢复，新清单如实去掉不存在路径。原交接/自审声明另存intake-handoff.json，不当作当前结果。各仓实际PWF也有当前状态前缀。

各Lab当前入口：

- [Alphabet交接](C:/Users/郑曾波/Projects/iqs-primary-alphabet-lab/docs/handoff/PRIMARY-ALPHABET-03/controller-acceptance-2026-10-13/README.md)
- [宁德时代交接](C:/Users/郑曾波/Projects/iqs-primary-catl-lab/docs/handoff/PRIMARY-CATL-03/controller-acceptance-2026-10-13/README.md)
- [中信建投交接](C:/Users/郑曾波/Projects/iqs-primary-csc-lab/docs/handoff/PRIMARY-CSC-03/controller-acceptance-2026-10-13/README.md)
- [原FIN交接](C:/Users/郑曾波/Projects/iqs-financial-reference-lab/docs/handoff/FIN-REF-01/controller-acceptance-2026-10-13/README.md)

## 具体修复

[一次集中独立核源](PRIMARY-independent-source-review.md)指出真实官方正文也会被绑错事实。Alphabet撤回87条错误绑定，保留9条旧proof和6条修正proof；优先股条件遗漏的旧claim/value保留为contradicted，新增条件事实及前序hash。零回购、June融资、现金加证券合计保留对应证据，不因数值异常而删去。全部30题不再自签confirmed_primary。

宁德时代14条混口径映射撤回，已有短转载证据拆成16条精确proof；现金、资金、债务范围、期间与复合claim不能互相代替。新增文中日期与旧facts不一致时记gap，不伪造新核读。原件不可得的30题limited状态保留。

中信建投撤回16个整题官方确认；普通股ROE10.51的正确pack事实保留，修错proof/自审的永续债解释、分红数量级与截止状态。分部合计的算术纠正，4条claim/value不一致的旧SEGIB事实保持原值并标contradicted；监管决定日与公开日分开，不能从URL推已核公开日。

三个薄CLI补闭合引用、真实日期/截止、scope/主体/币种/单位/期间/短摘录hash、事实逐一处置、未读或转载不能confirmed、严格JSON/非有限值、锁字节和允许变动检查。没有复制财务公式引擎。

源公开CLI又发现两个真实运行问题：CSC依赖测试环境注入FIN模块才能启动；Alphabet验证创建代码根的固定临时目录。新增有效反例后修独立引导和自动清理的独占temp。源续验Alphabet PID78364、CSC PID66612均exit0；CATL PID39692、FIN PID11252也exit0。未把测试环境失败或缺导入当来源错误。

## 财务owner与兼容

冻结FIN1.5.0允许computed ROIC将平均资本标成period_end，真实公共CLI已复现。修原FIN owner至1.5.1，显式period_end/beginning_balance与平均公式冲突时拒绝；不能只靠外层旧账不可变检查遮住缺陷。真实新计算ID同样不能绕过。

初版严格要求所有旧metadata都为average_beginning_end，导致5项既有正例失败。按实际公式含义调整：既有not_applicable/unspecified保持可读，对named平均公式给明确legacy warning；不把它们当期末口径，也不因此授金融资格。公共validate/export输出ledger_warnings。原失败和兼容说明保留，未静默重写旧schema/43冻结依赖。

原FIN新counterexamples先实际RED；初次guard误处理Windows subprocess executable=None保留失败，随后有效6F/1P。兼容回归121P，整合新数据后仍121P/0skip。源公共version确认1.5.1；旧1.1档案读取PID38704 exit0；源export PID46884=0、拒覆盖PID22568=3；正确pack关联的坏平均声明validate PID25596=2、export PID78876=2且不产生正式目录。旧冻结副本仍1.5.0，不能误说已更新或以它替代当前owner校验。

## 合并与仍欠证据

同一基线按各自30题比对，拒外公司行/原Source修改、新ID越界、共享行冲突及重复worker。六种顺序同字节，6P，PID65200。变化回执与账项前序hash受核；新增RPC账项有明确增量，不改原8项。旧62母公司事实与1.0/1.1/20原题锁保持。

合并仍90题，72定向研究完成/18gap/0not_started，1058条包含历史的facts、109 contradicted、62 Sources、9 ledger entries；所有分数和区间null、独审needs_revision、financial gold0。旧research_summary的36事实存在计数不是官方确认；1.2出口使用deep_researched_count，新增proof/访问也不是HTTP计费分母。

| 当前候选 | 全部30题处置 | proof | residual gap条目 |
| --- | --- | --- | --- |
| Alphabet | limited19、unconfirmed9、contradicted1、cutoff1 | 15 | 293 |
| 宁德时代 | limited30 | 16 | 251 |
| 中信建投 | limited10、unconfirmed20 | 24 | 见真实qualification-index |

gap条目可能同题多条，不是公司数或题目数。三包整题confirmed为0不等于所有官方数字均无效；只说明没有覆盖整题全部事实与问题缺口。未来只补具名原件/口径/截止证据，不重做已绿软件；未知继续未知，不填5分。收到较大的补证任务时可按用户最新授权交独立harness，不自动派发或反复给小修卡。

原FIN保留三个完整私有候选及qualification/changes/targets，qualification摘要绑定各自候选文件，不伪造与合并文件相同的raw hash。生产库、身份golden、观察记录和模型准确性资格未从此资料自动生成。

## 隔离、提交与主线

测试使用keyless环境、禁网、受控Python子进程、独占temp；失败/stdout/JUnit/PID/退出码保留。清理只针对自有封闭测试目录，清理统计以自有cleanup receipt为准；源个人设施、B01活动根及其他writer的2026-10-10 README保持。模型HTTP/付费搜索/下载/生产DB/名单写为0。

这次是同一F05资料验收节点，没有新建每题审查门。金融/G3/F05/生产UI/一键/全池仍开放。主线回checkpoint44的B01完整subject-context2/authority3+Observation1.2 pre-send→封存→owner公开导入→inspection与qualified/pool读取，再做已知响应终态/retry/CNY兼容；已绿的旧批次不重做。原live13HTTP/26native搜索/CNY1.268162/0评分/ACK0保持。

四个Lab均正常本地产品与交接提交，没有remote导出。IQS只提交本轮公文，远端仍此前自动审批范围pending；不把私有财务JSON/源码/数据库/真实golden混入，也不覆盖其他writer README。
