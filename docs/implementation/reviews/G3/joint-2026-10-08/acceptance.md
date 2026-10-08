# QA／StockWiki 实际联合验收

2026-10-08，Phase108。结论：**partial_verified / changes_requested**。真实生成与导入已连通，ACK闭环尚未连通；三项跨仓阻断见[集中整改卡](remediation.md)。原QA四链、SR02-4B、LR-02B有限签收保持，不重复实现或重开它们。

## 固定输入与实际执行

| Owner | 软件结果 | 收到的HEAD | 前后状态 |
|---|---|---|---|
| StockQA | b6eaa082e6e1df1306fa144bd623aa6de68213a1 | a39d7eafceacfa1114f5e5cb094eadb32030652c | master；原七项未跟踪不动 |
| StockWiki | cc587a8cf76f2c50a0cdfb4693d3767dfa5944fa | d253fea5f4f6e4242d2b91eaf8d89d3dac8b45ff | master；clean |

固定QA136/SW296个源码及测试文件，结束后432/432原SHA不变；源仓HEAD/status也不变。[源快照](../../../intake/G3/2026-10-08-joint/source-snapshot.json)、[最终核验](../../../intake/G3/2026-10-08-joint/verification/final-verification.json)。题义release先于派发，从冻结合成manifest及六个原模块artifact SHA建立，[来源证明](../../../intake/G3/2026-10-08-joint/verification/release-provenance.json)。没有用产出观察反推题义。

实际QA CLI为`main_with_llm.py` OS子进程；仅HTTP响应边界使用合成替身。实际SW CLI为`observation-import --package ... --release ...`。ACK读取为公开`ack_for`，接收为QA公开`apply_result_delivery_ack`，不是虚构ACK CLI。两仓分进程/cwd/PYTHONPATH，库、TEMP与日志都在本次IQS独占根。查询调用公开UI JSON builder，未启动HTTP/browser UI，本批不声称浏览器验收。

初cold=31完整包，全部31由SW公开CLI接受；第二独立同模型B_DIRECT也生成31包，其中一包追加到SW验证不可比变体。三次cold共93次合成HTTP（含31次alias不支持场景）；真实模型/搜索、收费、下载、生产库/名单和外仓写均0。测试身份明确provisional，合成QA fixture中的verified标签不构成真实身份资格或owner golden。

## 集中结果

| 批次 | 实际结果 | 原日志 |
|---|---|---|
| 原集中suite | 17实例：6 passed / 11 failed；68.10s，controller wall69.868s，无timeout | [原日志](../../../intake/G3/2026-10-08-joint/verification/joint-suite.stdout.log) |
| 仅夹具修正及未执行路径补批 | 9实例：7 passed / 2 failed；31.75s，wall32.268s，无timeout | [补批日志](../../../intake/G3/2026-10-08-joint/verification/corrections.stdout.log) |
| 独立unknown恢复、schema与空库计数 | q8 warm/seal各CLI0、HTTP0；两个原ACK公开schema无效；空身份库观察0 | [补充原件](../../../intake/G3/2026-10-08-joint/verification/additional-results.json) |

不能加总成“整套通过”。原失败包括控制器采集/初始化问题和依赖未执行，产品问题按下面三组收敛。所有初版helper/日志保留；未把实际失败输入改为预期接受，也未删原ACK字段制造成功正例。

| 组 | 本批可证明的范围 | 未证明／结果 |
|---|---|---|
| J01 | 31原观察；低2、cycle/watch、18条长证据、insufficient/null及N/A/null原样保留 | partial：ACK受JR1阻断 |
| J02 | 错具体security在key/HTTP/DB前拒绝；消费者拒独立definition错release | partial：不冒充全部semantic/template/scope矩阵 |
| J03 | 两个同模型独立run/scan/attempt/observation不碰撞；同包重放原ACK不变 | 子范围passed；不是第二模型比较 |
| J04 | 重复summary最后值与原包一致，无需重签 | failed JR3：accepted=1、观察1 |
| J05 | 篡改hash包级拒；已迁移空身份库拒绝、观察0 | partial；其ACK内部码entity_not_found属JR1；真实owner身份/全部revision反例缺 |
| J06 | 已提交接收方公开对账取回同一原ACK | failed JR1：原ACK被拒，send_uncertain未落定 |
| J07 | 五种错键拒绝且完整前后快照不变 | failed JR2：wrong store在ready及独立q7 send_intent后均能delivered |
| J08 | compact→完整supersede，2 revision、1 attempt | 子范围passed；非法head/旧ACK保留既有QA证据，未在此组重复跑全矩阵 |
| J09 | 独立q8 ready→begin→warm/seal，各HTTP0、原attempt/包不变，未知交付状态保留 | partial：非模型结果未知/预留/fallback全链 |
| J10 | 实际SW create/verify/restore；非空目标拒绝；新空目标恢复观察/计数，原库不变 | partial：双owner配套恢复及中断missing |
| J11 | 原2/9和不同basis/run完整可追；默认>=8零命中，详情ambiguous | 子范围passed；model/segment/period/rubric全矩阵不扩大 |
| J12 | capabilities诚实为W09，C06/facts/relations=false，查询HTTP/LLM0 | partial：F05/strict-explore/空partial真实gold missing |

## 三个阻断及能力保留

1. **JR1，ACK公共格式与错误码。** SW在schema_version1.0.0里增加ack_sequence/部分original_import，而IQS冻结ImportAck和QA只允许十个根字段；实际accepted与rejected原件均不符合公开schema。实际空库拒绝还返回entity_not_found，公共枚举要求missing_entity。其余内部题义/执行冲突码也不能直接冒充公共码。所有四种状态都需收口，不能只修accepted。原ACK落库不可改写。
2. **JR2，目标库首次绑定缺失。** QA只校验store_id文字，不与事前目标比较；错误qsobs_unrelated_target被实际落定。两个负例明确是旧契约形状的构造反例，不是把SW原ACK投影后当成功正例。须在发送前持久绑定目标，并在ACK事务比较；不能从第一份ACK学习目标。
3. **JR3，歧义JSON接收。** SW json.loads缺重复键hook，矛盾summary被取最后值并落库。全深度严格解码与非有限输入需一起覆盖，包级拒绝零观察写入。

原J03仅将HTTP返回model改B，真实请求仍A，31回答之后checkpoint因execution receipt mismatch被拒。这不能证明真正B模型对比；登记**requested≠resolved当前unsupported**，保留原返回和请求，不伪改actual为requested。后续durable resolved追溯需专门处理，见整改卡附记，不夹带到本批三项修复。

## 控制器与环境

原五个错键断言用了find_work_items摘要作before、get_item完整作after，造成形状差异；补批统一同一get_item后五个拒绝/不变全部通过。原missingentity根未迁移，先CLI2是正确环境拒绝；补批初始化空身份库，暴露真实公共错误码不一致。J11原批因第二产物不存在而未执行，补批才实际验证，不把依赖失败称查询bug。

最初freeze漏LF候选，并非此前推测的混合EOL。结束后逐文件证明432个固定blob都可在LF/CRLF字节域重建，mixed_eol_files=0；[EOL证明](../../../intake/G3/2026-10-08-joint/verification/source-eol-proof.json)。临时snapshot/sourcebaseline归档父路径曾读错，修正后复用已有alias快照，没有重跑模型测试。原工具错误和initial helpers保留，非产品RED。

一次[独立集中审查与补批附记](independent-review.md)确认上述边界。106合成原输入/包/日志另存，原actor流及JUnit均归档；内层owner helper按UTF8解码，外actor stdout/stderr是raw，不声称每层raw。

严格lstat/单硬链/无reparse、精确集合/size/SHA、CIM无匹配运行进程后dry-run→Apply删除**1074本批自有文件、78目录**，仅`runs/joint-2026-10-08-01`；无服务监听端口，仅受控asyncio socketpair。[清理回执](../../../intake/G3/2026-10-08-joint/cleanup-receipt.json)。共享TEMP、原Phase92、源仓七项与opencode.json不动。

G3仍要求L03＋W11；W11已verified，L03/真实可靠性/双owner恢复尚缺。F05及实际公开query schema、capabilities、真实owner golden/生成命令未齐，TH-IMPL-01/IN-IMPL-01源仓精确写授权也未取得。**本批不放行G3、F05、TH/IN或200家公司。** 下一步只修JR1–JR3，同批TDD及一次集中联合回验；本IQS交付的commit/push以PWF实际Git回执为准。
