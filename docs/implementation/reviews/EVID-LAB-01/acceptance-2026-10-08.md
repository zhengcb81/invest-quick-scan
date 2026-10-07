# EVID-LAB-01验收：部分确认，整包需整改

总控2026-10-08验收。Lab唯一源仓只读，分支`codex/evid-lab-01`，起点`cc3c38824c90a210196d63242797113247094b22`，工具结果`35b98cd443c0adf05fae1ebc2bd6cc0e28760019`，收到的HEAD`d87cf718a0fa90f2d0929e902ad2faa70c39580a`。之后五路径仅交接/PWF变更；Git工作树实际clean，无remote。用户通知完成不等于总控签收。

结论：保留全部现有交付和已确认功能；**不能签收语义检查、来源追溯、异常发布及冻结实验提案完成**。不改Lab，不关闭L02/G3/F05，不执行提案。原writer按[整改卡](remediation-2026-10-08.md)在同一仓修，整批一次回归/复审即可。

## 已确认的部分

- IQS公开handoff CLI shape/scope预检valid；worker当前工作树82/82工件size/SHA与manifest相符。
- 从真实HEAD导出的83个Git文件运行实际Lab组件。公开`validate-fixtures`成功：34个fixture、42条expectation、350条诊断记录；28 synthetic、5 historical model output、1 real-source占位。FX034为collected=false、空case，不是假真实来源正例。
- 公开`python -m iqs_evidence_lab replay --input index`成功复算三历史归档：186模型/24搜索、396契约有效答案；published_comparison一致、326 review join一致、实际temperature偏差48次。没有用新实验回写旧结果。
- 53个worker方法在批次回归通过；剩余子进程方法在总控修正guard注入后定向通过，共54个唯一方法得到通过证据。不是一次54全绿的原命令；不把总控harness错误归成产品错误。原失败/适配日志均保留。
- 53被拒题包/264包内题无保留item_inspection，因此不可测；片段已删，396事实支持abstain。agent标签不当人类gold，套餐实扣仍unknown，费用只参考。

## 复现的问题

| 编号 | 优先级与问题 | 直接证据 / 预期 |
|---|---|---|
| EL-01 | P1：字典period丢quarter/half，缺year也pass | Q1 vs Q4、H1 vs H2实测pass；2026H1 vs H1也pass。矛盾应fail，缺必要年份应abstain |
| EL-02 | P1：URL窗口缺信息误通过，比较列误失败 | 只有URL无period实测pass；同报告2026/2025两列实测E_URL_WINDOW_CONFLICT。无窗口应abstain，正常比较列不因同URL而fail |
| EL-03 | P1：fixture追溯可被破坏 | 重复source_category先historical后synthetic的真实CLI仍exit0；FX031复制答案score/rationale被改，provenance verifier仍[]。重复键必须拒，复制字段须完整绑定 |
| EL-04 | P1：写盘失败留下半成品 | 真实replay先写input-verification，注入第二文件写盘OSError后exit1，但输出目录留下；再用同路径会被exclusive拒绝。应原子发布或可靠清除本次半成品 |
| EL-05 | P1/P2：提案分母偏差，尚未冻结 | item分母仅answered items；失败包题位消失。60×5=300计划题，失败一半仍可报150/150。实际五题分组/query/证据选择/hash/费率公式未冻结，USD0.85无法复算 |
| EL-06 | P2：交付字节与诊断定位不足 | 37/82声明工作树工件hash与Git blob不同，全部仅EOL；fixture input/answer hash空，语义定位空，synthetic/agent标签部分被标historical |

总控冻结的[9个反例](acceptance_cases.py)运行结果：**8失败、1通过、0error**。通过项为Windows公共CLI拒绝把另一个锁定价格文件作为index，故没有把静态怀疑算作实际阻断。失败涵盖EL01/02/03/04；提案与诊断元数据由一次集中独审核实，边界与最小输入见[独审记录](independent-review-2026-10-08.md)。

## 测试、来源与隔离口径

[查收与日志](../../intake/EVID-LAB-01/2026-10-08/verification/result.json)包含准确命令、exit、耗时、stdout/stderr hash。[Git字节边界](../../intake/EVID-LAB-01/2026-10-08/git-byte-boundary.json)明确37项仅CRLF/LF，不称内容篡改；不能用工作树hash冒充可由commit直接导出的相同字节。原冻结IQS文件有224次校验、128个独立文件含lock，前后SHA一致；不要将重复校验次数叫225个不同文件。

测试在IQS自有`runs/evid-lab-2026-10-08-01`的Git副本，不运行或写原Lab。进程环境仅白名单Windows运行变量，未带API key；Python audit拒绝网络、限制写根并在每个Python子进程加载。pytest默认NUL日志、Windows Popen executable=None及CheckResult dataclass三个总控适配错误原样留档；对子进程测试重设PYTHONPATH的行为，仅在启动边界补入总控guard，worker源码未改。该保护是Python事件范围，不宣称完整OS读隔离。

实际网络/收费/下载0。网络守卫自测的故意拦截尝试与真实发送分开。原worker环境报告常量不是独立计量器；本次另用无凭据环境与子进程guard佐证。测试会话结束后按清单/hash/无活动进程清理本轮唯一临时根，实际状态见[清理回执](../../intake/EVID-LAB-01/2026-10-08/cleanup-receipt.json)；未生成回执前不得称已恢复。

## 后续边界

保留只读重算器的已确认结论，修复上述问题后再完整验收工具/提案。当前提案是非执行草案；Phase96已另有准确性实测和实操手册，不重复60/24收费矩阵，也不以本包草案覆盖它。增强完整数值/全文核验规则如未实现，明确non-goal/abstain，不能把量纲一致升级成十倍金额、归母/扣非或投资评分正确。

原writer交真实新commit、接口/规则版本、RED/GREEN原日志、更新hash/清理证据；总控只回验受影响例与真实三归档，不为每个helper立门。其他QA/SW外包不受本验收阻断，仍等各自真实交付。
