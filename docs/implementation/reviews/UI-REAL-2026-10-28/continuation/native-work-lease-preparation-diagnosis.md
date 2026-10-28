# Native work-lease preparation 单例失败诊断

结论：本次复现的 `refresh_owner_preview_rejected` 来自 **执行沙箱拒绝原 immutable publication 的 `os.link`（PermissionError / WinError 5）**。不是已发现的 provider/owner fixture 契约过时，也不是 `work_lease_seconds=3600` 的产品回归。未更改任何生产源码、测试源码或 owner 验证；未把 hardlink 改成 copy，也没有绕过 immutable 语义。

## 原因链与直接证据

原 root XML `work-lease-native.xml` 在 scope-1 原 `stockwiki.quick_scan_refresh_owner_cli --request` 返回通用 `refresh_owner_preview_rejected`，尚未到生成带 work lease 的执行 bundle。

第1次诊断仅运行指定原单例：

`tests/test_dashboard_prepare.py::test_native_fresh_prepare_registers_36_original_work_items_without_http_and_replays_exact_result`

使用私有 pytest plugin / sitecustomize 给合成子进程加离线 audit guard、剥离环境及异常 trace；不修改 StockWiki 原异常处理。捕获到：

- `stockwiki/quick_scan_refresh_owner_cli.py:357`，`records.save(request, result, ...)`。
- 具体失败：`PermissionError`, `winerror=5`, staging `.owned-refresh-sgrgnf9u` → 目标 `rv1_5e7d43bca99608fe71d7c5fdc76d4d1395faba336b3a6b975ac44967b6205b3e.json`。
- 对应原实现 `stockwiki/quick_scan_refresh_records.py:112–118`：mkstemp→写入/fsync→**原 `os.link(_native_path(staging), _native_path(path))`**，再清理 staging。
- 所属合成 namespace 为 `runs/dashboard-prepare-test-o47uvhq5/owner/...`。真正 cause 保存在 `native-work-lease-fixture-trace/exceptions-11400.jsonl`。

原 owner 在 `records.save` 前已执行 `service.preview` 并返回，因此本次失败发生在 immutable preview 发布阶段，而不是已捕获的 provider、预算、主体或策略校验失败。原 owner CLI 把普通 OSError/PermissionError映射为通用 fallback，才显示 opaque code。

## Hardlink 的受控 A/B

全部 probe 仅在本人 `runs/nlt-*` / `runs/nle-*` 临时目录写固定 synthetic bytes，使用真正 `os.link`，不涉及 owner、真实账本或生产文件，结束即清理。

| 执行环境 | 普通短绝对路径 | `\\?\` 扩展路径 |
|---|---|---|
| 默认执行沙箱 | PermissionError / WinError5 / errno13 | 同样 WinError5 |
| `require_escalated` 脱离执行沙箱 | 成功，nlink=2，bytes一致 | 成功，nlink=2，bytes一致 |

记录：`native-work-lease-fixture-trace/sandbox-hardlink-probe.json`、`escalated-hardlink-probe.json`。短路径也失败，不能把本次原因归结为 fixture 路径长度或 Windows 扩展路径拼写。这里的 escalation 是脱离工具执行沙箱，并非主张需要更改产品逻辑或 Windows 管理员提权。

## 最多两次单例的实际结果

1. **沙箱、带私有trace：失败，145.66秒。** 精确复现原 opaque refusal，捕获上述真正 PermissionError。原 fixture 按 pytest finally 自动清理。保留 `run1.xml`、`run1-output.txt`，没有覆盖 root 原红色 XML。
2. **脱离沙箱、同一原单例、带私有trace：外层诊断等待240秒超时。** 这是本诊断的限制：全局异常 trace 明显放大了 native 多层子进程开销；过程中只降低私有trace开销，没有改变原owner/fixture语义。不能把此次结果记作完整 pytest pass，也不能把 trace 超时记为产品 lease 功能失败。

第二次 pytest超时后，其本人 native fixture worker继续自然完成。没有发起第三次测试或额外 owner CLI。清理前读取其原 `applied.json`，得到：

- status `prepared`。
- 两 scope question_count `[33,3]`，均原 `registered_with_executor=true`，共36项。
- 两执行 bundle `work_lease_seconds` 都是3600。
- `API_requests=0`，`dispatch_started=false`。

该摘要已保存 `native-work-lease-fixture-trace/orphan-worker-final-artifact.json`。这是正向 native preparation / bundle projection 证据；**没有代替原单例剩余 replay、argv、execution-preview 等全部断言**。完整无trace验收由 root另行安排；本 agent不再重跑。

## 隔离、安全与 cleanup

- 环境只保留平台/runtime变量；没有读取 key、凭据文件内容或真实答案正文。
- 私有 sitecustomize 在测试及后代进程阻止 `socket.connect/getaddrinfo/sendto`；原 synthetic runtime只有“No credentials” fixture。未运行模型/paid入口。
- 唯一测试数据为原例的 example.invalid synthetic issuer、独立 owner/ledger。没有改真实 T/C worker、真实库、owner policy或名单。
- 私有 plugin只把该测试可能生成的全局 stage-report重定向到本人诊断目录，避免覆盖其他并行证据；没有修改测试文件。
- 第1次 `dashboard-prepare-test-o47uvhq5` 已自动清理。
- 第2次 synthetic worker PID9896（经本人fixture child的parent关联识别）在获准清理前已自然退出；无需实际 taskkill。清理前/后窄范围查询确认 `qjkqim_c` namespace 的 Python 后代为0。
- 清理时先核每个 resolved absolute path 在本workspace内且未重定向，只删除以下本人路径：
  - `C:/Users/郑曾波/Projects/invest-quick-scan/runs/dashboard-prepare-test-qjkqim_c`
  - `C:/Users/郑曾波/Projects/invest-quick-scan/runs/nwld1`
  - `C:/Users/郑曾波/Projects/invest-quick-scan/runs/nwld2`
  - `C:/Users/郑曾波/Projects/invest-quick-scan/runs/dashboard-preparation-locks/730fe307cbd80df755cd5122ca034380ef3ef7d0c38792c8307aa00419a67d12.lock`
- 上述4条路径残留均false；本人 namespace Python进程残留0。另一个已有 `dashboard-prepare-test-0_jhemau` 不属于本人，完全未删除或终止。所有诊断证据保留在本报告旁的 `native-work-lease-fixture-trace/`。

不建议修改 fixture provider/owner字段或放松原验证来“修”此次问题。适当测试环境应允许原 hardlink publication，同时保留这些零付费合成隔离条件；本报告不宣称 work lease 产品改动修复了 hardlink 权限。root应使用无trace的同一原单例、脱离执行沙箱完成最终 acceptance。
