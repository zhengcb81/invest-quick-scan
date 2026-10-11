# OPS-DESK-01：独立只读包级审查

2026-10-11，独立agent `/root/ops_desk_acceptance_review`，仅阅读OPS冻结源码、手册、目录、锁和交接；没有修改文件、执行产品、访问网络或真实owner。本审查与总控公开CLI实测同属一次包级验收，不增加独立的小节点门。

结论为 `changes_requested`，四组修复已经合并到[唯一R1卡](OPS-DESK-01-R1.md)。以下是源码审查发现，实测结果及终态另见[验收报告](OPS-DESK-01-acceptance.md)。

| 优先级 | 发现 | 修复边界 |
| --- | --- | --- |
| P1 | bundle手工校验未完整执行发布schema；错误容器可能TypeError，日期只有regex，synthetic标记缺一致性 | closed验证和稳定错误；不是新增owner状态机 |
| P1 | 证据最大值仅控制是否检测secret，主bundle未同等拒链接，坏编码静默放行 | 读前有界、普通文件和短文本角色；无下载器 |
| P1 | render直接插入不可信Markdown/HTML；真正零证据partial被误拒 | 安全字面显示，明确版本扩展partial，不伪造证据 |
| P2 | 通用Web UI存在被写成快扫设置可用，W16旧preview备用范围不清，provisional被过度概括 | 能力据实标注，新permit语义不退化，保留owner具名例外 |

复核来源：`src/iqs_operations_lab/bundle.py`、`render.py`，`content/user-manual.md`第1/4节、`incident-catalog.json`的provisional/O07；锁内`freshness-and-jobs.md`的permit消费/dispatch_commit线性化要求。源码行号会随整改变化，交接以冻结原字节为准。

保留十个family、26 incident、17命令条目及47来源引用的冻结路径/hash闭合。现有原币种、physical计费、uncertain对账、检查点/ACK区分和不执行拟定命令的设计有效。并未发生远程图片请求或脚本执行，不能把Markdown风险写成已发生的外部执行。

原1.0字节/输入锁/第一轮交接保留；一张卡、同一个稳定候选集中续验，已有有效部分无需重做。不关闭生产、金融准确性或一键门。
