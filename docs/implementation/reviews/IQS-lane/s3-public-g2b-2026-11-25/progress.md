# IQS S3/S4 G2b 进度

- 基线三项 RED 后，`python -B -m pytest -q -p no:cacheprovider tests/test_stockwiki_g2b_frozen_golden.py tests/test_stockwiki_mapping_contract.py` 共 15 项、10 子项通过，目标 Ruff 通过。
- 实际 StockWiki `665f6a85b7d6ba2419bc7731dee1403bfe2a07df` 的 owner 进程使用其既有 `tests/e2e/test_g2b_iqs_cli.py` 夹具播种独立短目录，IQS 新入口由公开 owner CLI 取回实体并通过公开消费者。实时导出 SHA-256 `0efc2c04daa7b6345078410a5df5ae0aa5bec9098b1523d7c25f9f60f53e5d2f`。本次真实 CLI 收据 SHA-256 `0a70248480da935b4a72dbc7bf6eebc89b9045c1c03f9557d99329f575b9ce58`。两个 golden 和测试 owner 库文件字节不变，测试数据根恢复。未读生产库或调用收费服务。
- 手动复验冻结路径时，从 IQS 仓执行以下命令。加实际 owner 时追加 `--stockwiki-root <code-root> --owner-root <isolated-data-root> --entity-id <entity-id> --as-of <timestamp>`。收据带 `proof_mode` 和可选 `live_owner_export`。

```powershell
python -B -X utf8 scripts/stockwiki_g2b_acceptance.py `
  --golden docs/implementation/contracts/goldens/stockwiki-g2b-72531b5-provisional.json `
  --mapping-golden docs/implementation/contracts/goldens/stockwiki-mapping-72531b5-four-state.json
```

独立复核通过。按正式 master 精确基线、正常 hooks 和快进发布。活跃 Dashboard 分支保留。
