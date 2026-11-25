# IQS S3/S4 公共 G2b 验收

从 `origin/master@fb3fcbe7a897cd748864dcabc39a25c0732168af` 的隔离工作树实施。只写 IQS 验收脚本、目标测试及本计划。现有 `codex/cross-id-dashboard-return-20261121` 分支、其本地 PWF、StockWiki 代码和业务库由各自现有负责人维护。

1. 复现冻结重放需要外仓、读活库范围可隐式推断、旧 golden 写入入口仍可达的问题。
2. 将两个冻结 owner 输出作为 IQS 合同输入。保留 Entity 公开 CLI 正例及五个单字段负例、mapping 五种情形及四个语义篡改负例。
3. 用现有 StockWiki 公开命令增加可选当前 owner 验收。必须提供代码根、数据根、实体 ID 和 as-of，确认读回准确实体，再走 IQS 公开入口。将固定样本重放和实际 owner 查询在收据中注明。
4. 用 StockWiki 自有 fixture 在临时目录播种，验证真实组合。测试后比对原始 golden、临时存储字节和清理状态。
5. 等独立复核同版通过后，用正常 hook 提交和快进正式主线。
