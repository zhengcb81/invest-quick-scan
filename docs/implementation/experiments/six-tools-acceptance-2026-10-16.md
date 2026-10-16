# 六个独立工具包验收 — 2026-10-16

六包**工程签收**，均为 package 1.0.1。原工人交付完整冻结；独立反例发现的问题已直接修复、正常提交。原交付365项测试通过，修复后最终整组426项及跨包7项通过，零失败/错误/跳过。此结论不代表新策略金融准确率提高、成本下降或生产owner已接通；本轮未发收费模型/搜索请求。

| 工具包 | 作用 | 最终测试 | 当前源仓commit（master） |
|---|---|---:|---|
| ANSWER-CODEC-03 | 紧凑传输还原标准答案 | 63 | `fdff607e8bc4401b8a908472761d072c3e0c9ef2` |
| RESEARCH-JUDGE-03 | 全槽盲评、人工判定与解盲比较 | 65 | `4c674ae1b1e054fdfd40a7307c30fd317152c64f` |
| CACHE-PLAN-03 | 已知/未知计量、历史价与缓存假设 | 77 | `245ee603ba9e1a90ff514b996e8ab33d26fecdf7` |
| SESSION-PACK-04 | 共享证据的分段会话与累计资源 | 81 | `fee65997a456cae0cef8fc9a53ebe36ba70f2dd2` |
| CLAIM-GUARD-04 | 上下文、会计口径及critic数据输入 | 77 | `e383e6cb65b72c740a0da9c4e318335de5e819c8` |
| EVID-GAP-04 | 逐题缺口、有界补充与检索计划 | 63 | `af0bdea55b03a41e0a452fef71e68dc00f13eaf0` |

六仓根分别是 Projects/iqs-answer-codec-lab、iqs-research-judge-lab、iqs-cache-planner-lab、iqs-session-packing-lab、iqs-claim-guard-lab、iqs-evidence-gap-lab。六仓均已按用户授权执行CodeGraph初始化，并忽略.codegraph/；各仓未配置remote，未创建新的远端。最新修复说明在各仓 docs/coordinator-acceptance-2026-10-16.md。原 docs/handoff 是历史1.0.0候选记录，不能用其中旧测试数/旧覆盖率替代本报告。

## 修了什么

- CODEC：null指标也必须引用本题已声明来源；HTTP(S) URL须有有效hostname。标准答案、未知score和原引用不被改写。
- SESSION：分段和重启均按原截止时间及累计使用量计算；校验checkpoint完整性、非负计数、在途状态和工具绑定，未知usage不得假成功或获得新额度。
- JUDGE：最终答案与最后revision绑定；解盲map与bundle绑定；result/events回执统一去重。缺缓存/计量和缺财务判定保留未知；参考标量须匹配含义、期间、币种及范围，不把Cloud收入误当利润。
- CACHE：已知小计与完整费用分列，缺usage/time不变成零；限制历史pricecard的模型、日期和窗口；过期/换版前缀不进入可复用收益，不把字符串公共前缀当真实cache hit。
- CLAIM：整题表、单题成员、board、company/cutoff共用可信绑定，复用冻结standard_answers原校验器；critic保留原答及公开证据关系，私有参考/模型元数据不得进入；口径规则不替代金融真值。
- EVID：悬空/错维度引用不覆盖，contradicted保持可见；before整视图不受补充影响；partial仍是缺口，来源不详不能虚构独立性。纠正DOJ提案目录被误写为法院已命令出售Chrome的材料错误。旧author_data现改只读验证，不能重生错误材料或悄悄覆盖篡改现场。

## 真实旧实验的跨包重放

T0原6会话保持72目标槽、4个合法原答和68缺失；codec还原后原答对象逐项相等，真实OCF→FCF错误仍可被检查器发现。T0已知21回执公开价重算小计USD0.100300，现金账单未知。4个无回执SDK失败只表示原carrier无法证明发送阶段，不能称4次真实失联HTTP。

T1只有3个已启动会话输入adapter，因此输出36个输入槽和15答；原登记仍为72槽/57缺。总控显式保留其余未启动会话，不能把已输入3场的统计当原登记全部完成。T1计量保留13个完整usage回执的已知小计USD0.107693、另1个usage未知回执，完整token/费用为null。SDK step、native attempt、收到HTTP响应以及未知发送均非同一数量。

没有导入新真实金融判定时，accuracy/winner仍null。此次串联不重复或改写旧独立盲评结论：T0四答均部分，T1十五答为14部分/1审慎不足，无充分槽。也不能把结构合法答案数当正确答案数。

补证据报告仍保留12题/53维：before为42missing/7proxy/4partial/0direct；after为21missing/16proxy/16partial/0direct。**没有一整维可以据此宣布充分**。新增有限经营机制材料有信息价值，但不证明高留存、ROI或完整单位经济；53维仍需核实，query_plan最多8条且均未执行。见[官方网页核错](../reviews/six-tools-2026-10-16/official-source-check.md)。未下载财报、PDF或全文HTML。

## 独立审查与复现

- [CODEC / SESSION](../reviews/six-tools-2026-10-16/codec-session-review.md)
- [JUDGE / CACHE](../reviews/six-tools-2026-10-16/judge-cache-review.md)
- [CLAIM / EVID](../reviews/six-tools-2026-10-16/claim-evidence-review.md)

总控证据目录：`runs/six-tools-acceptance-2026-10-16-01/`。baseline.json记录交付时六仓HEAD/branch/clean及handoff raw hash；source快照238文件/1658956bytes、199项声明artifact均吻合。原始整组、独立RED/GREEN、最终XML/log、跨包产物、原件保留、CAS文件和提交清单分别保留，不重签工人的tests.json。

本机可复现（显式离线输入，Python C:/Miniconda/python.exe）：

```powershell
C:/Miniconda/python.exe -B -X utf8 runs/six-tools-acceptance-2026-10-16-01/run_suites.py
C:/Miniconda/python.exe -B -X utf8 runs/six-tools-acceptance-2026-10-16-01/run_cross.py
```

测试只在candidate副本和专属temp/cwd运行，移除secret环境、禁止网络和外部写入；含真实冻结SDK注入fake HTTP、公开CLI正反例。新回归已随源仓提交。异机需要复制两轮inputs快照及锁，不能追活动仓latest。共享冻结输入369+395项raw SHA不变，旧work SQLite和其他writer的2026-10-10 README保持，原S1预算SQLite亦未变。清理记录cleanup-history.json保留；初次整包删除被自动审批拒绝后，总控核实并仅删明确pytest/缓存叶目录（433文件/8391607bytes，剩余0），审计报告、RED证据副本及原交付不删。

## 下一步与未关闭边界

下一步由总控沿这些已签收API接入研究driver，先处理原生预算未知请求，再登记新的小规模真实对照。不得直接把旧1.1脚本加大额度当T2，不得静默使用新的证据/工具而沿用旧实验版本。新的模型请求前应固定新题包策略、补充证据hash、工具版本、phase/repeat和计量规则，保留思考但不输出隐藏思考。

原S1累计35attempt、已知公开价估算USD0.207993及USD0.10未知预留不变。未知请求不重发、不伪造0费用、不另建store/policy绕闸。resource profile1.2仍是旧自有候选，未因本验收安装或运行。生产owner多轮/耐久恢复、真实routed Task2全链路、正式评分库和G3/F05等原主线尚未完成；本次只签收工具工程，未新增小节点审批。
