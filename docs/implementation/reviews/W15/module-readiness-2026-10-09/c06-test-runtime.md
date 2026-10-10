# C06 组件测试与隔离集成环境

这是原 C06 大节点的测试接线，不增加审查门。代码仍为 `runs/c15a` 私有候选，尚未在三个生产源仓发布。

普通 QA/StockWiki 单仓 pytest 不要求导入对方产品。跨仓集成测试明确 opt-in：`IQS_C06_RUN_INTEGRATION=1`，且 `IQS_C06_OWN` 指向本次自有运行根，包含 `qa/`、`sw/`、`iqs/` 和隔离 `guard/`。固定 CLI 子进程分别只加载自己的组件；IQS 纯契约校验不读取数据库或访问网络。单仓未启用集成时，集成模块明确 skipped；这不计测试通过，更不能签收 C06。启用后环境错误须报错，不能默默跳过。QA 纯组件测试若缺 IQS 纯契约依赖也明确 skipped。

总控必需集成批次通过 `run_c06_producer_checks.py <新唯一标签> <QA相对测试路径…>` 运行，设置实际三个组件路径、临时目录和同一 socket/SQLite 守卫。选取 StockWiki 测试可用 `../sw/tests/…`。每批实际 PID、child exit、源 SHA、JUnit、日志均进入 intake；不能将控制器 exit0 误认为 pytest 通过。必需集成批次须真实执行、skipped=0；不能用普通 collection 的跳过来关闭门。

首次空观察库设置由 owner 公开 CLI 执行：

```text
python -B -X utf8 -m stockwiki.quick_scan_subject_dispatch_cli --operation initialize --root <绝对workspace路径> --expected-schema-version 0
```

这是设置动作，不是日常 read/refresh 的隐式迁移。它只创建本命名空间 schema3，零模型/搜索请求；重复已初始化库使用 expected-schema-version 3 保持原库字节和 store_id。已存在 schema1/2 明确要求备份后的受控升级，本入口不升级；未来版本、坏库、现存未标版本库、预期版本不符均拒绝。日常事前登记必须已有 schema3，否则派发前拒绝，不替用户自动升级。旧 schema2 reader/writer边界保持。

`producer-init-green` 的 7 项实际测试包括6项首次设置/拒绝反例和1项真实主程序的部分扫描接续。`producer-portable-green` 的75项是真正集成执行、无跳过、零API；`normal-collection-03.json` 仅记录正常单仓 collection，executed_tests=0。首轮collection因移除隔离守卫必需的OWN变量被控制器拒绝，次轮是控制器误以为collect-only会输出skip总数；日志原件保留。改用独立opt-in开关并显式读取-rs的模块skip记录，原守卫不变。两类证据不得混用。

仍需原 C06 全节点集中审查、真实 owner golden/生成记录及源发布；首次设置不代表统一安装器、ReleaseSet生命周期或200家扫描已交付。


## 2026-10-10 接续补记

新增preview纯契约25P、原账本只读检查8P为实际独立批次；不合并为金融准确率。新适配器仍待测试，原guard不改，source执行前后SHA稳定，失败原件保留。7文档发布已有具体人类授权，结果以实际终态为准。
