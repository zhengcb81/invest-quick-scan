# 当前文档与发布证据终审（2026-10-25）

Reviewer：`/root/inspect_production`；状态：**passed**；`open_findings=[]`。本次仅核当前文档和持久薄证据，不重跑模型、测试或恢复，不连接数据库。

已逐项对齐根 PWF 三文件、接手说明、实操手册、当前状态图及 production/README 与真实 result、thin-summary、transition、112 项修复锁及实际独审。七份文档、两个清单、四件实际制品和实际审查的 raw SHA 见同名 JSON。

production 清单 **236/236** 文件的字节数和 SHA 全匹配；旧 130 件原文件字节、原清单行及原清单 SHA 完整保留。publication 清单 **18/18** 匹配，12 项核心测试和 3 项历史保留测试的 XML 均无错误/失败，仅读取既有结果，不宣称它们使用同一中间源码版本。发布器的复审和真实运行的复审分别保留，没有互相替代资格。

当前 R1–R5 完成口径准确：CATL IQS_05，截止 10/18、观察 10/25；新模型/搜索各一次；模型 60.1106 秒，恢复 128.479 秒、0 新 HTTP；双封存同一原 schema2 检查点，delivery 为 ready。原完整账本投影 hash 不变，摘要读取前后库 SHA 相同。累计公开价估算 25023 micros、本代 5894 micros，账单仍 unknown，原两代无效 safe 与未发送 0 成本记录保留。

`same_source_cold_and_warm_claim=false`、ready 不是 StockWiki ACK、金融正确性未评估、没有 38 题/多公司/全池资格，均已写明。typed 产物使用可信规则的显式 Python API；通用 report CLI 的默认空规则边界没有冒称已接通。源码提交实核为 IQS `733186c`、Company 本地 `803ff51`、StockQA `24fc22f`。

下一步已收敛为只读核对现有 ready 封包与 StockWiki 公共导入/ACK 契约，再准备隔离 ACK 集成验收；禁止为此重问模型或重跑现有驱动。后续多题/多公司和过期 lease 的已知 safe 恢复仍是独立后续范围。

初核时未发布的最终证据链接现已存在；handoff 清单位置和 R2 时态也已修正。无剩余文档缺陷。本审查只写本目录两个 documentation-final 文件；提交后的 Git blob 字节核验与推送由总控完成，不在此提前宣称。
