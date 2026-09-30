# E2E-06 本地隔离支架独立审查

- 审查日期：2026-09-24
- 审查者：`/root/g0_independent_review`（独立审查 agent）
- 审查范围：`tests/live_e2e_sandbox.py`、`tests/test_live_e2e_sandbox.py`、`docs/implementation/test-strategy.md`，以及相关计划、S03 回执和原始日志状态
- 决定：**verified_for_local_isolation_mechanism_only**
- 阻断 finding：0（首轮发现的 3 项阻断均已关闭）
- 非阻断 finding：0

## 1. 范围声明

本结论只验证本仓离线隔离目录、清理白名单、控制文件保护、外部状态比较和测试子进程收尾机制。它不表示真实 StockQA 搜索、真实 provider/费用、StockWiki 导入与 ACK、跨仓启动或 E2E-06 故障矩阵已经执行。

`docs/implementation/acceptance-cases.json` 中 E2E-06 仍为 live、`specified_not_executed`；S03 回执的 scope statement 仍明确排除 live E2E-06；实施计划验证仍返回 `product_tests_executed=false`。文档没有把 17 个本地支架测试误报成真实 E2E-06 通过。

## 2. 受审字节与原始日志

| 工件 | SHA-256 |
|---|---|
| `tests/live_e2e_sandbox.py` | `C75254A98BD5E414226F7A0F724F7367666870D0D7805F3CEFD99F8E9D11769D` |
| `tests/test_live_e2e_sandbox.py` | `8DC1830F59796F1603DD1C424966CAA6BEAE89D6C1836323DEC943DD36F813A4` |
| `docs/implementation/test-strategy.md` | `1BE342636195EA2C83775FD53D8B13D77C75AA9E3C2CCEC871EFBB8CD25B7B24` |
| `docs/implementation/contracts/receipt-S03.json` | `B83925974496B5F6471029FFB85B2FC46457409C4F5675201B54B4E66C307E4A` |
| `docs/implementation/tasks.json` | `3E0F1E3D3A2B56C4E3758F343674BAC5FFAEC53042CFD280B34DF99EFB6E3E09` |
| 定向原始日志 | `44D1F711A6E18E759F839E6E57C54B9811BFBDBC7986BAD529D392DDE63CD8CE` |
| 全量原始日志 | `6CDCCFDF325EFEF3665C8366C59B7D8D731667D83E0E14D5C5B75D8025EEEBDD` |

原始日志内容分别为 `17 passed in 1.37s` 和 `214 passed, 116 subtests passed in 22.25s`。审查者另行复跑当前字节，结果见第 5 节。

## 3. 首轮阻断项复核

### ISO-B01：manifest 硬链接写穿外部文件

**状态：closed。**

首轮实现用 `open("wb")` 原地覆盖 manifest，若 manifest 被替换成指向 run 根外文件的 NTFS 硬链接，会改写外部文件。当前实现已在每次更新前验证 root 身份、owner 文件及 manifest 是 `st_nlink == 1` 的唯一普通文件，并通过同目录临时文件加 `os.replace` 原子替换 manifest（`tests/live_e2e_sandbox.py:307-364`）。

独立重放步骤：删除当前 manifest，在原路径建立指向 run 根外哨兵文件的硬链接，然后分别调用 `register_artifact()` 和 `cleanup()`。两者均以 `IsolationError: sandbox control file is not a unique regular file` 拒绝；外部哨兵字节保持不变，run 工件保留。对应仓内回归位于 `tests/test_live_e2e_sandbox.py:191-217`。

### ISO-B02：开放 SQLite 导致半清理且无法重试

**状态：closed。**

当前清理先完整校验清单，再将全部登记工件逐个移动到同目录暂存名；任何移动失败都会逆序恢复已移动文件，在此之前不会 unlink 工件（`tests/live_e2e_sandbox.py:458-515`）。外部状态检查也在暂存之后、删除之前执行；失败时同样恢复全部工件（`tests/live_e2e_sandbox.py:517-555`）。

独立 Windows 重放使用一个保持打开的真实 SQLite 连接，并同时登记 download、exchange 和 log。第一次 cleanup 在开放数据库处失败，数据库和另外三份工件内容均完整保留，没有 `.cleanup-*` 残留；关闭连接后第二次 cleanup 成功移除整个 run 根。仓内真实 Windows 回归位于 `tests/test_live_e2e_sandbox.py:219-239`，受控多文件暂存失败回滚位于 `tests/test_live_e2e_sandbox.py:241-265`。

### ISO-B03：空 NTFS junction 未被识别

**状态：closed。**

当前 `_is_link_or_reparse()` 同时检查 symlink、`Path.is_junction()` 与 Windows reparse-point 属性；目录遍历器在进入链接或 reparse point 前失败（`tests/live_e2e_sandbox.py:39-74`）。路径配置、工件登记和清单复核均复用该判定。

独立 Windows 重放用 `cmd.exe /c mklink /J` 创建指向 run 根外**空目录**的 junction。`cleanup()` 以 `run tree contains a link or reparse point` 拒绝，run 根与外部目标均保留；移除 junction 后可以正常清理。仓内回归还覆盖带外部哨兵文件的 junction，见 `tests/test_live_e2e_sandbox.py:267-298`。

## 4. 其他安全边界

### 路径与删除白名单

通过。base_dir 先解析后必须位于系统 Temp 根内；run 根记录设备号和 inode/file-id 组合并在关键操作前复核。所有配置路径和登记文件既检查词法边界，也检查解析后边界，并限制在 `workspace/sqlite/downloads/exchange/logs` 五个专用子目录内。登记文件必须是唯一普通文件，记录 run_id、owner_id、大小和 SHA-256。清理前实际文件集合必须与登记集合完全相等，因此未登记文件、缺失文件、hash 变化、路径逃逸和 owner/run_id 不符都会在删除前失败。

### 暂存失败与外部 pre/post 漂移

通过。仓内测试已覆盖中途暂存失败时所有先前工件回滚。独立附加重放登记 download、exchange、log 三份工件，在状态观察器报告外部哨兵变化时，三份工件全部恢复到原路径、内容不变、无暂存残留；恢复外部状态后可再次 cleanup。

### 进程归属

通过当前支架声明的前台子进程范围。早期版本允许调用者登记任意既有 `Popen`，审查过程中已删除该入口。当前只能通过 sandbox 自己的 `start_process()` 创建并持有句柄，cleanup 只对这些精确句柄 terminate/wait/kill，从不按裸 PID 或进程名清理。测试同时启动一个未登记进程并确认其不受影响（`tests/test_live_e2e_sandbox.py:313-327`）。若未来产品入口会派生独立进程树，仍须按代码注释使用 owner 提供的进程树适配器；本报告不把前台句柄测试扩大解释成跨组件进程树验收。

### 子进程 cwd 与相对写入

通过。`start_process()` 在调用 `Popen` 前把默认 cwd 固定到本 run 的 `workspace`，显式 cwd 则必须通过相同的词法、解析后路径、专用子目录及 link/reparse 检查，并且必须是已经存在的目录（`tests/live_e2e_sandbox.py:248-283`）。独立复跑确认子进程的相对输出只出现在 run-local workspace；仓内回归还用 mock 证明外部 cwd 在 spawn 前拒绝且 `Popen` 未被调用（`tests/test_live_e2e_sandbox.py:329-357`）。这约束默认相对写入；绝对输出参数和产品自身派生进程仍须由真实入口配置与外部状态 oracle 在 E2E-06 中验证。

### 文档和状态表达

通过。`docs/implementation/test-strategy.md:64-81` 准确区分本地支架与 live E2E，说明受保护 cleanup、17 个离线测试的用途、真实 A—H 场景和当前外部入口缺口。S03 保持既有 verified 范围，并继续明确不包含 E2E-06；新增支架没有被塞入 S03 的已审题库实现快照。

## 5. 独立测试结果

1. `python -X utf8 -m pytest -q -p no:cacheprovider tests/test_live_e2e_sandbox.py`  
   结果：`17 passed in 1.50s`，无 skip。
2. `python -X utf8 -m pytest -q -p no:cacheprovider`  
   结果：`214 passed, 116 subtests passed in 19.62s`，无 skip。
3. `python -X utf8 scripts/question_sets.py validate`  
   结果：48 个模块、222 道题，验证通过。
4. `python -X utf8 scripts/implementation_plan.py validate`  
   结果：73 个任务、172 个验收 case、G6，`product_tests_executed=false`。
5. `git diff --check`  
   结果：退出码 0；仅显示现有工作树换行风格提示。

独立附加反例还验证了：manifest 硬链接下 register/cleanup 都拒绝且外部字节不变；开放 SQLite 时多类工件完整保留并可在关闭句柄后重试；空 NTFS junction 被拒绝；三工件外部状态漂移完整回滚。新增 cwd 测试实际启动子进程写相对路径，并确认输出只落在 run-local workspace；外部 cwd 负例在创建进程前被拒绝。

## 6. 最终决定

当前候选可以按 **`verified_for_local_isolation_mechanism_only`** 放行。首轮三个阻断缺陷均由公共实现修复并有 Windows 实际反例覆盖；本次没有发现新的阻断或非阻断问题。

E2E-06 仍必须保持 `specified_not_executed`。只有 StockQA/StockWiki 真实公开入口、真实联网 provider、费用/搜索回执、导入/ACK、故障矩阵和外部零漂移检查全部实际运行并形成同一 release 的证据闭包后，才能将 live case 标记为 passed。
