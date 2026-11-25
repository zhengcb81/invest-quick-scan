# IQS S3/S4 G2b 调查

旧验收脚本使用相邻仓库的 `tests/test_identity_g2b_export.py`、`tests/test_identity_snapshot.py`、QuickScanStore、IdentityReceiptStore、MarketRegistryStore 和映射内部实现。IQS 收到的是 DTO，存储测试应在 StockWiki 执行。后者的 `tests/e2e/test_g2b_iqs_cli.py` 已经在 owner 内初始化合成数据库，再从公开命令调用 IQS。

IQS 既有 golden 是 StockWiki 官方历史样本输出。Entity `stockwiki-g2b-72531b5-provisional.json` 的 SHA-256 为 `0efc2c04daa7b6345078410a5df5ae0aa5bec9098b1523d7c25f9f60f53e5d2f`。Mapping `stockwiki-mapping-72531b5-four-state.json` 为 `da3991c0d85ef9a0bce7c9152475b9184942df74c34fab4c5c935fb0e375a96f`。

不带数据参数时脚本重放上述冻结内容。历史只带 `--stockwiki-root` 的调用仍可用，输出准确写冻结重放。旧两个 capture 选项明确指出 golden 归 StockWiki 发布。当前数据使用单次 `python -m stockwiki.cli --root … identity-export-g2b --entity-id … --as-of …`，接受合法成功输出并保留安全的结构化错误码。as-of 是明确传给 StockWiki 的请求时间，收据记录该输入。当前实体导出不回显请求 as-of，IQS 只从实际响应校验实体和合同。当前 DTO 不要求与历史 oracle 的摘要相同，避免把固定样本公司/期次当成运行限制。

此计划只验证 G2b 层边界和已有消费者语义。无需更改正式身份、业务数据、授权和付费路径。
