# EVID-REF-02 R2：集中接续验收，仍需整改

本次接续原 EVID-REF-02 的同一次包级验收，不是新项目或新增小节点审查。R2 修好了部分实质问题，但正常原输入在隔离副本里仍不能通过公共校验，若干准确性与请求绑定缺口也还存在。因此状态为 **needs_remediation**，下一步按 [R3集中续做卡](EVID-REF-02-R3.md)收口。

## 实际接收与历史限制

| 项目 | 实际观察 |
|---|---|
| 源仓 | `C:/Users/郑曾波/Projects/iqs-evidence-lab` |
| 分支 | `codex/evid-ref-02-r2` |
| R2产品commit | `ffb1e7046423e9e97dec6aefba6e66a366fb119f` |
| 交接HEAD | `b2c7c73812fca4a5ae3a4e2bc8b4ecf8f793099c`，后于产品提交，属于交接文档提交 |
| 重建基线 | `b59d5b976478887e386b12cfc0bc7d5eb9a633e7` |
| 原历史对象 | 原R1 `70498e40918ea28476b8d0185a0294be7bbb6e0e`、原产品 `44aa20402125b23de151e2c7c0f4abff7082a7cb` 在当前Git中不可读取 |
| 脏树 | 实际状态为5份旧 EVID-LAB 清理回执未跟踪；本次未删除、未改写、未提交这些文件 |

交付已披露 `.git` 误删后重建。不能将重建commit说成旧Git历史已恢复，也不能用重建基线证明此前全部修改范围。验收以当前真实文件字节、可读取commit、此前总控冻结证据为准，不修Git、不伪造历史。

## 运行结果与证据范围

验收在新独占副本执行，没有写源仓、PWF、生产数据库或名单，没有付费API、网络访问或下载。实际Python为3.13.9，原 offline guard 的 SHA-256 保持 `abc0128dc92a2bf99e57dbbbfe2355aea376b584f67e9e51c0bd0ebbc871e682`，另加普通文件写入 fence；子进程环境仅传明确系统字段和自有路径。

| 核验 | 实际结果 |
|---|---|
| R2交接artifact大小/SHA | 16/16匹配 |
| 冻结源文件 | 287份，前后0漂移 |
| 本次所需锁定输入副本 | 32份，原文件/副本大小SHA一致，前后0漂移 |
| 新增R2测试文件 | 29项：16通过、13失败、0skip、0error；pytest 8.138秒，子进程10.034秒 |
| 正常原pack，原锁与输入全搬副本 | 公共 `tools/reference_entry.py validate`、`evaluate` 均exit2，尚未进入目标语义比较 |
| 只搬Lab，IQS root仍指原IQS | 公共validate仍exit2，Lab的必需preregistration角色失去锁覆盖 |
| 旧1.0报告摘要 | 公共summarize exit0；accuracy为null；重复输出exit3 |
| 实际staging junction | 公共summarize exit3，目标仅自有sentinel且SHA未变，无输出、无staging写入 |
| 补充纯语义观察 | 21例，7个反例重现；明确不是公共CLI原锁正控的替代 |
| 清理 | 自有清单逐文件核SHA后非递归清理330文件、61目录；7个临时根absent；保留必要日志和报告；观察到的自有存活进程为0 |

没有重跑旧214项。16个绿色测试中，有些仅断言exit2/4，实际被无关锁覆盖错误提前挡住，不能证明相应根因已修复；13个失败包括忠实回答、正常端点、正常六题、普通输出等正常控制。不能把源仓中自报的全绿替代隔离可复现结果。

## 原九类根因的接续结论

| 根因 | 已确认的变化 | 仍需处理 |
|---|---|---|
| ER2-01 文本准确性 | 裸年份/单位、单独错指标现在降级 | 否定本题收入数值的句子仍得到text accuracy=supported。词匹配oracle仍升级为语义准确性。 |
| ER2-02 弃答残值 | unknown/value及insufficient/score矛盾在实际纯函数中所有维度not_verifiable；正常无值弃答保留 | 保留修复，公共整链正控受ER2-09阻断。 |
| ER2-03 冻结资本题义 | 改editable definition无法绕过真实冻结IQS_10；ROIC/WACC缺口仍阻止支持评分 | 保留修复；R2同编号legacy摘要测试不能替代这一根因的资本题控制。 |
| ER2-04 端点来源绑定 | 不存在source ID增加了闭合检查 | Alphabet IQS_05端点改引用CATL的已有来源，该来源只支持CATL事实、未绑定Alphabet本record，仍过schema/约束并授予评分准确性。只检查ID存在不够。 |
| ER2-05 staging祖先 | 真实 `.temp-roots` junction在public publisher写入前被拒；普通输出成功、重复输出拒绝 | 保留修复，不再为本例另开审查门。 |
| ER2-06 完整请求分母 | 缺失历史question_ids可拒；真实单题未被扩成48题 | 同步删除F02答案与显式题目ID，保留原指纹，得到5请求/5回答/0缺失；全0错误指纹也被接受。请求身份尚未独立冻结。 |
| ER2-07 旧摘要准确性 | 旧1.0源的accuracy计数为null，只保留旧一致性计数 | 保留修复和旧字节。 |
| ER2-08 检查资格 | 空actor/time/ref增加约束 | 仅提供非空的不存在检查记录ref或通用URL，仍得到准确性支持；没有绑定检查记录、source/hash/subject/time。 |
| ER2-09 隔离重定位 | 原锁没有被放宽或重写 | 正式source-root-map未实现；按当前绝对root匹配原锁，正常复制后必需角色失去覆盖。原pack公共正控不成立。 |

同一内容检查还发现：把record披露日设到冻结信息截止日之后，schema/语义约束仍通过，数值仍accuracy=supported。核验日期可以晚于信息截止日，所用财务披露及来源信息不能越过冻结截止日；这两个时间必须分开。

补充21例使用真实公开模块的纯函数，正常schema/语义约束控制通过；未patch函数或锁。它们帮助定位剩余机制，不冒充正常公共入口走通。首版controller曾误传空confusable_names，导致一项错公司假阳性；第二版传真实冻结名单后正确拒绝，已明确撤回，不计入7个反例。

## 公私证据与后续验收

本公开文档只记控制结论、接口范围、commit及测试统计，不复制来源短文、私有金融输入、真实数据库或密钥。完整局部变更、构造例、精确命令和原始记录见：

- [独立完整报告](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/intake/parallel-acceptance-2026-10-11/evid-r2/acceptance.md)
- [独立交接JSON](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/intake/parallel-acceptance-2026-10-11/evid-r2/handoff.json)
- [实际公共命令记录](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/intake/parallel-acceptance-2026-10-11/evid-r2/public-calls.json)
- [21例纯语义记录](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/intake/parallel-acceptance-2026-10-11/evid-r2/controller-results-02.json)
- [JUnit](C:/Users/郑曾波/Projects/invest-quick-scan/runs/ear2/logs/r2-focused.xml)、[原始测试stdout](C:/Users/郑曾波/Projects/invest-quick-scan/runs/ear2/logs/isolated-r2-focused.stdout.log)、[真实junction结果](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/intake/parallel-acceptance-2026-10-11/evid-r2/junction-result-03.json)

下一次仍为同包集中接续：先让原字节pack/锁在正式重定位下公共validate/evaluate正控成功，再检查未收口反例；保留已绿保护，复用一批正反例和一次包级review，不重新审旧包，不新增九个小门。

源码/来源事实检查不构成人类金融oracle。本验收不保证金融准确率，不关闭G3/F05/B01/L03、全池或生产发布门。
