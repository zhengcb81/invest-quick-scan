# C06 十二题原响应恢复

同一批十二题使用 StockQA 正式登记和运行入口。选题和分包来自原授权及生产组合器。旧用例混合了多轮研究任务和一次性题包响应，SDK 在第一次发送前将 259,925 字节的保守预留量与 240,000 输入 token 上限比较，无法抵达原响应保存后的强停位置。

## 场景

- **原响应恢复**。沿用五方固定版本和既有合成主体。原十二题必须组成一个题包，固定输入上限保持 240,000。实际 HTTP 客户端只在已经解析供应商逻辑端点后，将这条请求送到随机端口的 127.0.0.1 夹具。夹具以 MiMo 原协议提供合成答案、搜索使用量和来源元数据。
- **强停边界**。真实 owner 端口返回已保存的原响应后，IQS 测试探针使子进程直接退出。下一次正常写入 IQS 响应收据尚未发生。原 checkpoint 须存在 pending intent，且没有 pending receipt。
- **冷读**。移除模型、费率和合成支出配置，用新子进程执行 `--seal-deliveries --recover-checkpoints`。只读取先前真实发送的试验响应。须恢复相同的 12 个题目 ID，原 checkpoint 字节保持一致，预算账本无新增支出，模型新增请求为零，原生回放为一次。夹具输出标为 `scripted_wire` 且不能用于金融结论。
- **超限拒绝**。同一公开入口在独立授权和相同题包上使用一个显式偏小的测试预算。真实 SDK 在发送之前记录 `research_session_resource_limit`。该用例要求零 HTTP、零预算请求和无正式结果。原旧版混合模式的 259,925/240,000 拒绝记录单独保留，正常用例不放宽配额。

## 隔离复验

使用 IQS 施工分支的精确提交，并在临时目录归档 StockQA `86f633d8f36e1039323ae492e47f8a8067031d5a`、StockWiki `6cd6d7ef5ad706c1e4581e91f2c87107be112572`、Company Agent `9fb4b945415782dfd41b9436d4d4ec063247d658`、Runtime Bridge `cae47ec7d9c4b439a3f390db792e52fa8f70d0fe`。包含各自的 schemas 和原有合成授权夹具。令 `IQS_C06_OWN` 指向仅含隔离源码和测试数据的临时父目录，其下 `iqs`、`sw`、`qa` 分别为这三份归档。配置现有 C06 运行变量 `IQS_C06_RUN_INTEGRATION=1`、`IQS_C06_COMPOSITION_CODE_ROOT`、`IQS_C06_COMPANY_ROOT`、`IQS_C06_BRIDGE_ROOT`。

使用既有离线网络护栏及空凭据环境分别运行：

```text
python -B -m pytest -q "<isolated-root>/iqs/owner_tests/test_shared_company_engine_native_e2e.py" -k crash
python -B -m pytest -q "<isolated-root>/iqs/owner_tests/test_shared_company_engine_native_e2e.py" -k oversize
```

从隔离的 StockQA 归档根执行，测试文件可用隔离 IQS 归档中的绝对路径。Windows 子进程通过无窗口启动，工作目录、数据库、输出和日志都放在临时目录。退出后清理临时归档和产物，仅保留脱敏计数、版本、测试状态及清理回执。此文件描述此十二题用例，其他 C06 组合仍按各自的证据收口。

## Windows 验收

测试源固定到 IQS `ba3df8c95974e4cd75f0c5a2b04e2a8f1b9cd629`。原响应强停及冷恢复用例通过，用时 655.54 秒。超限拒绝用例单独通过，用时 290.12 秒。两个进程各执行一项，并各自排除另一项。导入的 StockWiki 合成夹具仍产生一条未知 `smoke` 标记警告。

原任务只有一次本机 HTTP 和一次原响应回放。恢复封存十二题，新增 HTTP、外部请求和追加费用均为零。包括开发复现和正式复验在内的五个沙箱均已清除。脱敏的证据绑定及计数见 [机器回执](c06-native-recovery.json)。
