# F05-IQS-CONSUMER-01 施工包

本包只补 IQS 对 F05 事实查询 wire 的消费端合约，使用独立 IQS Lab。它接续 2026-11-04 已交付的 StockWiki owner 侧候选，不改 owner 仓，不读取生产运行库，不调用模型或搜索。

| 施工包 | 独立工作目录 | 冻结输入 | 本包交付 |
|---|---|---|---|
| [F05-IQS-CONSUMER-01](F05-IQS-CONSUMER-01.md) | C:\Users\郑曾波\Projects\iqs-f05-iqs-consumer-lab | IQS aca0f4be5adcb96f0c7d8f58e0c4a205e6c17981；F05 owner candidate 63a6ffcf23f8d16f47acf44bdbcf3e567a85458e | IQS facts 请求/响应合约、固定 CLI 分派、2.7.0 wire 能力兼容和离线跨边界合约测试 |

状态：**隔离代码包已完成并通过独立复审；F05 整体仍为 partial。** 最终 IQS Lab HEAD：`08e5b4d660bd09cfbb6fe9cba0d7ec7aad31d388`。facts/capabilities/CLI 定向测试 82 passed；exchange/query 与 deployment 相邻组 30 passed、7 subtests passed。

总控验收修复了公开导出只校验自哈希却未绑定原查询/owner profile，以及跨日 snapshot replay 错用新请求日期的问题；增加在重算哈希后仍拒绝候选、查询、截止日、snapshot 和错误 owner 篡改的反例。测试仅用合成数据。旧查询兼容组仍有一个在冻结基线已存在的 `model_self_qualification` 失败，单独记录为已知基线失败。

本包的完成状态只表示隔离 IQS 消费端合约代码、测试和复审完成。F05 仍是 partial，直到总控取得受支持的真实 owner 只读入口与真实 owner golden，正式接线后完成真实公共 CLI 互操作验收。不要将本包的合成测试称为真实 owner 验收。
