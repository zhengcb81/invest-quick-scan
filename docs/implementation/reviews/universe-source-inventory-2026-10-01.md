# 首批股票池来源清点（候选，不是正式股票池）

观察日期：2026-10-01。只读搜索 `C:\Users\郑曾波\Projects` 下文件名匹配 `*companies*.txt` 或 `*list*.txt` 的文本文件；未导入 StockWiki、未启动公司扫描。

在可读取目录中找到 94 个匹配文件、12 种不同文件字节内容。多数是 `company-wiki` 股票清单在 review/worktree 副本中的重复。`rg` 对若干 pytest/cache/临时目录报告权限拒绝，故本结果覆盖可读取的匹配文件；索引保留每个命中文件的相对路径和 SHA-256。

纳入候选的六份来源如下：

| 来源 | 记录数 | 用途 | SHA-256 |
|---|---:|---|---|
| `company-wiki/companies_list.txt` | 241 行，其中 239 个名称标签 | Company-wiki 目录名称；排除 `_inbox` 与 `_产业链导航.md` 两项管理/文档名 | `3cb3a7b81ffd5b2c047f3d7ebd50b68d9b945d9ae65c3a5dde75016f2c66e94c` |
| `company-wiki/a_share_companies.txt` | 205 | A 股代码与名称 | `70f47d80a806525131368c1baab5d60a8a2c03b4dbbd3c27908f492a1cdb6a5c` |
| `StockInfoDLSimple/v2-clean-rewrite/a_share_companies.txt` | 192 | 第二份 A 股代码与名称 | `16a94e94b9bbbe384e3523537d968a512dd5d2f910f7e6584316a8a45e0a5ce4` |
| `StockInfoDLSimple/v2-clean-rewrite/companies.txt` | 3 | 明确代码的研究目标；代码已落在 A 股候选集合内 | `4210e4653f69e9ce6a8a6dfded6d71c604ced79ef280e31adfde0d165a4845ce` |
| `Research/config/pending_list.txt` | 158 | UTF-16 编码的名称待办清单 | `b8a6c7b180c81ea669d7ef8ab884dd94642a8849cb757de314cf282ebc934c54` |
| `earnings-transcripts/earnings-transcripts/companies.txt` | 7 | 带 NASDAQ/NYSE 来源字段的美股电话会候选 | `ec5f8832ecab1f9f991f33ed918fcfb2ce278bcfbc9bebb5bf8ac22816c721f0` |

按“市场 + 交易所（若来源提供）+ ticker”精确去重后，得到 **209 个 A 股挂牌候选**和 **7 个 NASDAQ/NYSE 挂牌候选**。另有 company-wiki 与 `pending_list.txt` 合并后的 **331 个不重复名称标签**；两个名称文件精确重合 66 项。A 股两来源有 188 个共同代码；并集为 209 个代码。目录清单和 pending 清单没有足够的挂牌字段，因此不计作确认上市公司数。

名称仅用于生成候选提示，不建立发行人身份，也不把多市场挂牌合并。发现一个明确歧义：`中信建投` 同名标签对应来源里的 `CN-A:002168` 与 `CN-A:601066` 两个候选挂牌；须由 StockWiki 权威身份映射核实，不能因同名合并。所有 ticker 的当前上市状态和信息截止日均为未知。

匹配到的其他 `*list*.txt` 内容是 Python 环境包清单、文件路径恢复清单或审查行号清单，不作为股票来源。machine-readable 的候选列表、逐行来源位置、所有 94 个文件的 hash、精确名称匹配提示与排除项见 [JSON 清单](universe-source-inventory-2026-10-01.json)。这份材料只供用户选择首批输入；它不是权威股票池，未获用户确认前不得导入或扫描。
