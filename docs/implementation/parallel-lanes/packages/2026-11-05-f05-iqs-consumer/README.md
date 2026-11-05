# F05-IQS-CONSUMER-01 施工包

本包只补 IQS 对 F05 事实查询 wire 的消费端合约，使用独立 IQS Lab。它接续 2026-11-04 已交付的 StockWiki owner 侧候选，不改 owner 仓，不读取生产运行库，不调用模型或搜索。

| 施工包 | 独立工作目录 | 冻结输入 | 本包交付 |
|---|---|---|---|
| [F05-IQS-CONSUMER-01](F05-IQS-CONSUMER-01.md) | C:\Users\郑曾波\Projects\iqs-f05-iqs-consumer-lab | IQS aca0f4be5adcb96f0c7d8f58e0c4a205e6c17981；F05 owner candidate 63a6ffcf23f8d16f47acf44bdbcf3e567a85458e | IQS facts 请求/响应合约、固定 CLI 分派、2.7.0 wire 能力兼容和离线跨边界合约测试 |

状态：**已备妥，尚未分派/实施。**

本包的完成状态只表示 IQS 消费端合约代码完成。F05 仍是 partial，直到总控取得受支持的真实 owner 只读入口与真实 owner golden，并完成真实公共 CLI 互操作验收。不要将本包的合成测试称为真实 owner 验收。
