# 分层测试入口（2026-10-25）

日常从仓库根运行 `python scripts/run_tests.py`，默认仅运行 `fast`。不要每次小改都跑全套，也不要用快速层通过代替大节点验收。测试使用原来的断言与实现，没有把慢测试改成skip。

同日后续基础题/UI节点复核：fast为544 passed、372 subtests passed，pytest77.57秒、含清理总88.413秒，0失败/错误/跳过。下面540项/39.608秒是分层首次落地时的历史实测；耗时会随负载和用例变化，不承诺每次固定40秒。仍不应为日常小改运行完整小时级验收。

本轮最终实测：fast 48文件，**540 passed、372 subtests passed**，pytest 36.08秒、含启动清理总耗时39.608秒；0失败/错误/跳过。入口及原两失败定向复核共17项通过（26.86秒，含一次G0整仓哈希）。这不是整套测试从78分钟优化到40秒，而是把日常反馈与大节点验收分开。

| 命令参数 | 范围 | 何时运行 |
|---|---|---|
| `fast`（默认） | 契约、纯逻辑和轻量组件；当前48文件 | 一组相关改动完成后 |
| `integration` | 本仓CLI、题库发布、临时SQLite、整仓候选哈希及跨组件兼容；当前48文件 | 改到这些边界时，按变更选相关文件或整层 |
| `e2e` | 本地产出链真实CLI端到端；当前1文件 | 大功能节点 |
| `native` | 原owner/SDK/缓存恢复脚本wire；当前2文件 | 生产接线、预算、封存或恢复边界变化时 |
| `offline` | fast + integration + e2e，依次独立进程 | 合并较大变更或里程碑；不要求每次都跑 |
| `all` | 上述全部，含native | 发布或重大跨仓节点，先备好隔离runtime |

`native`是脚本传输的离线原生集成，不能当真实金融/付费测试。它要求原有隔离runtime及 `IQS_C06_RUN_INTEGRATION=1`、`IQS_C06_OWN`、`IQS_C06_COMPOSITION_CODE_ROOT`、`IQS_C06_COMPANY_ROOT`、`IQS_C06_BRIDGE_ROOT`。未配置时 `native/all` 在执行任何层之前报错，不会静默skip后变成全套通过。两个native模块会修改进程环境，逐文件单独进程、串行执行；普通层也分进程。当前不自动启用xdist或共享数据库并行。

```powershell
# 查看范围，无测试导入、无执行
python scripts/run_tests.py all --plan

# Windows建议短的、已存在的临时父目录；只创建并删除唯一子目录
python scripts/run_tests.py fast --temp-root C:/Temp
python scripts/run_tests.py integration --temp-root C:/Temp
python scripts/run_tests.py e2e --temp-root C:/Temp

# 一次具体修改可先只跑受影响测试，再按上表选择扩大范围
python -m pytest tests/test_shared_semantic_replay.py -q -p no:cacheprovider
```

每次运行在 `runs/test-reports/<时间-随机ID>/` 保留逐层日志、JUnit XML、最慢20项和summary；临时fixture根正常退出后清理。pytest测试进程阻断socket连接/DNS/sendto，传给子进程的环境剥除API密钥、live标志和外加pytest参数。这个hook并不自动传播到CLI的所有子孙进程，CLI集成仍须遵守原有stub和隔离夹具；不要把它宣传成整个进程树的网络沙箱。真实收费搜索/模型探针继续使用已有明确预算、输入锁及账本入口，不能通过此运行器隐式启用。

任何一层失败立即停止后续层，summary保留实际已运行范围和退出码；不能将未运行层算作通过。缺native前置、配置错误、清理错误和XML错误均不返回成功。查看JUnit的skipped/errors，不以退出码0或文件存在推断全部case已经验证。

`tests/suites.json`是唯一归类清单，当前99文件各归属一次。新增测试必须登记所属层；缺失、重复、未归类或越界路径在执行前拒绝。`pytest.ini`将普通发现限定于 `tests/`，避免误收 `runs/`、文档及冻结副本。直接 `python -m pytest` 仍收集全部正式测试，不会暗中只跑fast；日常使用上面的分层入口。

原78分钟运行没有找到逐项计时，不能据此断言某个模块占比。已有历史JUnit证明一项native完整链约645秒，而附近63项定向回归约5.9秒；两者范围不同，不是优化前后对照。首轮静态分类实际跑257秒，其中G0整仓哈希约206秒，已据真实边界归到integration；另有继承全题库发布夹具的S06也归integration。首轮两个失败如实保留并单独定位，不能把移层当修复。最终fast的540项/372子测试与39.608秒实测见本文顶部，不是全套通过。完整离线/native/live验收仍保留，只按风险和大节点选择，不为每个小步骤新增审查门。
