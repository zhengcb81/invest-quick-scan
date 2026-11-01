# Dashboard NEW-6 定点复测

日期：2026-11-01。结论：**NEW-6 在交付候选范围通过**，不是 Dashboard 全部产品验收或并线完成。

交付目录：`C:/Users/郑曾波/Projects/dashboard-iqs-b03-company-result/.planning/unified-dashboard-2026-10-26/handoffs/external/X-IQS-B03-COMPANY-RESULT-IMPL-01/`。

主控亲读 handoff 和原独审报告；另派未参与实现的 agent 直接复测最终源码。Dashboard 文档 HEAD `edd964b`，产品代码 `e7ce9ae`；IQS service `3eb99cd`、UI `6f0391e`、StockWiki `b3084ff`。不是只沿用早期 `97cabb6` 报告。

## 实际复测

原缺陷是挂牌页面的请求 scope 污染公司结果深链。现在链接按结果自身 scope 生成；历史行以精确 observation 定位，清除可能属于另一行的 listing/subject。

- 最终适配器的五类判断通过：公司结果＋挂牌请求、挂牌结果＋无挂牌请求、同挂牌、同 subject、跨挂牌拒绝。
- 用 TypeScript AST 提取实际 `QuickScan.observationLink` 和 `safeLocalLink`，导入实际 `deep_link.js`；六条结果/历史路由均为 `observation_resolved`，且定位精确 observation。非浏览器模拟截图。
- 最终新增的 provenance 保留原 run 引用；原 StockWiki 公司快照模块 **32 passed / 11.28 秒**，包括 run/scan 引用与缺 run 拒绝。
- 命令：`C:/Miniconda/python.exe -B -X utf8 C:/Users/郑曾波/Projects/invest-quick-scan/runs/new6-retest-2026-11-01/check.py`。本机复跑脚本和结果位于该忽略目录；没有另造准入凭证。
- 0 收费请求、0 服务启动、0 生产数据写入；自有 TEMP 已清理。

## 未代签的范围

外包四仓尚须由 Dashboard D00 按原写域组合并线。真实生产公司正式结果注册、挂牌身份材料、浏览器任务/D06/E14 和 E07 整体仍按原交接记录为 PARTIAL/NOT_RUN。本次不改外包树，不把它的实验 authority 合入 IQS 原部署，不要求原快扫日常使用取得额外审核回执。
