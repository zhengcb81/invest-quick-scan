# OPS R1 独立静态审查记录

2026-10-11，审查者 `/root/ops_r1_package_review`。一次包级审查，范围为 OPS-DESK-01 原 R1—R4 的冻结 remediation-01，未实现 Lab、未启动 API 或生产命令。结论 `changes_requested`；R4关闭，R1—R3续做。总控后来用真实公开 CLI、CommonMark AST 和读取计数补验，见 [集中验收](OPS-DESK-01-R1-acceptance.md)。静态发现不冒充 reviewer 自己运行过测试。

冻结产品0867efb、实际HEAD bab279f；本地冻结路径 `C:/Users/郑曾波/Projects/invest-quick-scan/runs/ops-r1-acceptance-2026-10-11-01/source`。下列行号针对这份副本，不代表后续 writer 工作树。

| 原组 | 代码依据与问题 | 所需续做 |
| --- | --- | --- |
| R1 类型/长度合同 | `src/iqs_operations_lab/bundle.py:259` 对未校类型 protocol 做字典 membership，295—296 又用于 get；262—263 先转无界十进制字符串。364/396/446及引用检查用全长40，537用全长60，与schema的前缀后长度不一致 | 类型/长度先检查，稳定拒收；按原schema接收合法边界，不能改小schema掩盖误拒 |
| R2 链路/总量/错误 | `paths.py:47` 只 lstat 最终文件；中间目录 junction 在同根时仍通过。`bundle.py:321—329` 在 all_evidence 循环后判总量，473/477 已完成单文件读取。`strictjson.py:35` 重复key异常直接带入原key | 逐组件核可信路径链；事前/期间约束总量；错误只含安全code与结构位置，不回显原key |
| R3 纯文本 | `render.py:41` 动态反引号围栏与原值直接相邻，值首尾反引号会合并成不同长度的run，失去code span。`tests/util_cli.py:113` 用substring去除而不遵循真实匹配规则 | 用真实Markdown解析器验活动AST，首尾反引号/换行/HTML/图片均须保持非活动文本 |
| R4 手册资格 | 基线和文档范围已标明；快扫配置未核实；旧preview限旧协议；新permit派发not_available；eligible_provisional例外保留 | 接受这组；保留兼容回归即可，不重写/不实现owner |

非法时间、refs/owner类型、synthetic闭合、单文件界限与二进制、具名1.1零证据partial、旧1.0原件保持等已改善。剩余问题全部是原三组根因的边界，只有一张 [R2续做卡](OPS-DESK-01-R2.md)，没有增加逐函数审查门。
