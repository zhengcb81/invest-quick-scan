# G3-BATCH-RESUME-HARNESS-01｜批次接续端到端测试工装

**唯一工作目录：** `C:\Users\郑曾波\Projects\iqs-g3-batch-resume-harness-lab`

**冻结 IQS 输入：** `da557350b0dd11ea92382ad22479f874026d4ad8`

**工作分支：** `codex/g3-batch-resume-harness-01`

**复用场景目录：** `docs/implementation/parallel-lanes/packages/2026-10-11/LOAD-CASE-01.md`，SHA-256 `99E7A7D3C98A07A2F70F7BD6C99E0137CE39F60238EE7AECB9C6E805135E2431`

**包索引：** [本批 README](README.md)

## 目标和边界

做一套在本地独立、可重复运行的 G3 批次接续集成测试工装：从冻结 IQS 快照找到现有公开批次/运行入口，以本地合成实体、合成结果和 fake provider 跑一批 200 个测试主体；在固定检查点中断后重启，验证已付/已保存回答恢复、未完成项接续、结果入库幂等与时间/模型来源保留。

本包只增加测试工装和报告，不改 IQS 产品代码、数据库 schema、实际名单、模型顺位、账本、调度器或扫描配置。若现有公开入口不能支持该测试，记录可复现缺口并提交最小 patch proposal 给总控；不得用 monkeypatch 绕过核心保存/恢复/导入路径来制造通过。

**200 个主体全部是合成测试数据。** 这是软件端到端证据，不是 200 家真实公司扫描，不是 G3 签收，也不替代总控 PWF 里的实际小池/200 家真实试点。

## 隔离输入和写入范围

1. 从本地 IQS 仓库创建独立本地克隆，检出冻结 commit `da557350b0dd11ea92382ad22479f874026d4ad8`，不使用 shared worktree；移除 clone 的 `origin`。例如：
   ```powershell
   git clone --no-local --no-checkout "C:\Users\郑曾波\Projects\invest-quick-scan" "C:\Users\郑曾波\Projects\iqs-g3-batch-resume-harness-lab"
   git -C "C:\Users\郑曾波\Projects\iqs-g3-batch-resume-harness-lab" checkout --detach da557350b0dd11ea92382ad22479f874026d4ad8
   git -C "C:\Users\郑曾波\Projects\iqs-g3-batch-resume-harness-lab" switch -c codex/g3-batch-resume-harness-01
   git -C "C:\Users\郑曾波\Projects\iqs-g3-batch-resume-harness-lab" remote remove origin
   ```
   不得运行或修改原工作区中的生产 UI、服务、数据库、名单、预算或未跟踪文件。
2. 对 `LOAD-CASE-01` 只读复用其已有场景与边界，提交前复核其 SHA 与上列值相同。不得复制整套场景矩阵、改写该施工卡或重复 IMPORT-PERF-30 的入库性能基准；本包只实现“实际公开运行入口上的批次恢复工装”。
3. 新增内容限定于克隆内的 `g3_harness/`、`tests/g3_harness/`、工装自己的配置/fixture，以及 `docs/handoff/G3-BATCH-RESUME-HARNESS-01/`。IQS 上游源码保持原样；不要在总控仓产生旁支文件。
4. fake provider 不访问网络；不调用 API，不使用真实公司/题库答案/StockWiki 生产数据，不读密钥；所有 SQLite、缓存、日志和临时文件放在本 Lab 的唯一随机临时根。

## 必须验证的行为

先读冻结入口，找出真实公开 runner/service 和依赖；不要凭名称假造 API。一次工装运行至少做到：

1. 生成固定 seed 的 200 个合成主体，使用一个有限且固定的扫描范围；记录每个主体/问题的预期与实际状态、输入数、完成数、缺失数及运行时间/峰值资源。时间和资源是测量结果，不设跨机器的虚假硬时限。
2. 在确定性检查点中断（例如完成预设分片后正常终止 worker），保留本 Lab 运行状态，再从公开接续入口重启；验证已保存回答不重复发出、未完成工作最终进入终态、重试/重复导入幂等、失败状态不会伪装成完成。
3. 在可控 fake provider 下覆盖一次明确拒绝后的顺位切换，以及未知发送状态不自动换模型重发；确认最终记录仍保留实际模型、请求/扫描时间戳和去重键。若固定源入口没有相应 provider seam，不得 monkeypatch 隐去缺口；记录缺口和实际可测范围。
4. 展示重复启动同一运行的结果：相同已完成项应被复用/去重，缺口继续处理；状态混合（已完成、部分完成、未知、待处理）应可恢复。测试报告把实测成功、失败、unknown 分开，不把 unknown 当成功或失败。
5. 提供 one-command CLI，支持 `--entities 200`、固定 `--seed`、隔离输出路径和 `--resume`；CLI 应通过项目真实公开入口驱动流程。以新的临时目录重复运行能重现状态结果（随机ID可归一化比较）。

## 测试与交付

- **单元：** 合成数据/固定seed、状态归一化、恢复计划和报告统计。
- **集成：** 针对冻结源中的实际 runner、存储和导入边界，使用本地临时 SQLite 与 fake provider；验证中断/恢复和幂等。
- **端到端：** 执行 200 个合成主体的公开 CLI 完整运行，再运行中断—恢复路径；记录命令、退出码、语义分母、耗时、临时根及清理结果。
- 临时数据库、缓存、子进程、临时端口和原始测试日志在成功或失败后均清理；仅保留可重建 seed、简短摘要、测试结果及 hashes。递归清理前核对路径确在本 Lab 临时根内。
- 提供本地提交、`handoff.json`（IQS schema 1.0.0、`lane_id=iqs`、`package_id=G3-BATCH-RESUME-HARNESS-01`）、一条可复制测试命令、独立审查证据及 open items。测试工装可以 `complete` 交付，但报告中必须写 `production_G3_status=not_closed`；任何由工装发现的 IQS 产品缺陷列清复现，不在本包改上游源码。
