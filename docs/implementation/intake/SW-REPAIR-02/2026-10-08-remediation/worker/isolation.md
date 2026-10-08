# SW-REPAIR-02 isolation

所有测试/导出/黄金样例都在本包自己创建的根里进行；生产库、名单、config、
凭据、IQS `runs/`、StockQA 与安装镜像均未写入。

## 临时根（逐路径）

| 路径 / 标识 | 谁创建 | 用途 | 终态 |
|---|---|---|---|
| `C:/Users/郑曾波/Projects/StockWiki/runs/swr02-acceptance-20261007` | 本包 | 重建冻结 runtime（`stockwiki/`+`tests/`+legacy producer）并用原 `acceptance_cases.py` 复跑 | **cleaned=true**（`rm -rf`，已核不存在） |
| `C:/Users/郑曾波/Projects/StockWiki/runs/swr02-red-20261007` | 本包 | 最终版 `test_swr_cases.py` 对基线源码的 RED 复现 | **cleaned=true**（`rm -rf`，已核不存在） |
| `%TEMP%/pytest-of-郑曾波/pytest-109`、`-110`、`-111` | pytest（本包各次运行的 basetemp） | `tmp_path` 工作区、备份/恢复 fixture、浏览器截图临时落点 | **cleaned=false** —— 由 pytest 自身保留最近 3 次运行的机制管理；共同规范明确禁止按 mtime / pytest 编号 / 目录名清理共享 TEMP，因此本包不手工删除。截图已在删除前复制到 `logs/screenshots/`。 |
| `docs/handoff/SW-REPAIR-02/logs/**` | 本包 | 交接证据（RED/GREEN 日志、截图、golden） | 保留（交接内容） |

`git status` 在交接前只余 `?? docs/handoff/SW-REPAIR-02/`；`runs/` 下本包两个根
已删除，未留下未跟踪残留。

## 数据库

- 所有 sqlite 都在上述临时根内创建（`WorkspacePaths.from_root(tmp)` /
  pytest `tmp_path`）。**没有**对仓库或生产 `data/quick_scan/*.sqlite` 的读写。
- 本包唯一新增持久化文件 `<ROOT>/backups/quick_scan/owner_registry.json` 只在
  测试/黄金样例的临时工作区产生；仓库 `backups/` 目录（内含既有的两个历史 zip）
  未被本包写入，且该目录本身 gitignored。
- **迁移：无**。未改动 `data/quick_scan/` 下任何 schema。

## 端口与进程

| 项 | 观察 |
|---|---|
| 本包 HTTP 服务 | 每个测试用 `ThreadingHTTPServer(("127.0.0.1", 0))` 绑定**临时端口**，fixture `finally` 中 `server.shutdown()` + `server.server_close()` |
| 实际出现的端口（最后一次 E2E） | `127.0.0.1:{49314,49423,50426,53940,54802,57479,59242,60615,60805,62431,62624}` |
| 浏览器 | Playwright chromium headless，每个测试 `context.close()` + `browser.close()` |
| 收尾核对 | `netstat -ano \| grep LISTENING` 无本包端口；`tasklist` 无 playwright/chromium 残留（仅宿主自身的 `msedgewebview2`，与本包无关）；StockWiki UI 默认端口 8765 未监听 |
| 子进程 | 本包测试不派生常驻子进程；`guarded`/`run_frozen_acceptance` 的 audit hook 明确禁止 `subprocess.Popen`/`os.system`（金丝雀已验证） |

## 网络与费用

| 指标 | 计数 | 证据 |
|---|---|---|
| 外部（非 loopback）HTTP/浏览请求 | **0** | `tests/test_e2e_quick_scan_ui.py` fixture 的 `route_handler` 把非 `127.0.0.1` 请求全部 `abort()` 并记录，teardown `assert not external` 通过；`tests/test_ui_quick_scan.py`/`test_quick_scan_profiles.py` 的 socket guard 会在任何非 loopback connect 上抛错 |
| DNS | **0** | `run_frozen_acceptance.py` 金丝雀：`socket.getaddrinfo("example.com", 443)` → `PermissionError`，日志 `swr02_guard_canaries_passed` |
| LLM / 搜索 / 下载 / 模型调用 | **0** | `llm_calls=0`、`network_calls=0` 在每个 payload；`test_browsing_is_offline_and_never_writes` 断言无新 `*llm*` 模块加载 |
| 付费调用 | **0** | 无凭据读取；运行前删除全部 `*API_KEY`/`*API_TOKEN` 环境变量 |
| 本包 loopback HTTP | **142 请求 / 11 次测试 / 11 个临时端口** | `logs/green_e2e_browser.log` 中 11 行 `[e2e] loopback HTTP only: N requests to ['127.0.0.1:PORT']` |
| 浏览器真实页面请求 vs “网络为 0” | 如实区分：页面对本包 loopback 服务的 142 次请求**不是**外部网络调用；外部请求仍是 0 | 同上 |

## 写入范围核对

- 只 `git add` 了本包确切路径（15 个代码/测试/文档文件 + `docs/handoff/SW-REPAIR-02/`），
  没有 `git add -A`，没有混入他人 staged 路径（开工与提交前两次 `git status --porcelain`
  均只含本包路径）。
- 未修改 `invest-quick-scan/`、`StockQAbyLLM/`、`company-wiki/` 或任何其他仓库
  （`inputs.lock.json` 中其余仓库的脏状态是他们自己的，本包只读）。
- 未 push 到任何远端。

## 异常 / 需要如实说明的残留

1. `%TEMP%/pytest-of-郑曾波/pytest-{109,110,111}` 三个 pytest basetemp **未删**
   （理由见上表；共同规范禁止按编号清理共享 TEMP）。如总控要清，应由 pytest 自身
   的保留机制或人工确认后处理，本包不代劳、也不谎报 `cleaned=true`。
2. `logs/green_e2e_browser.log` 尾部之外，运行中出现过一次
   `Exception occurred during processing of request from ('127.0.0.1', …)`
   的 `ConnectionAbortedError`——这是 Playwright 拦截/中止连接时服务端的
   正常噪音，**测试全部通过**（11 passed），且该连接是本包 loopback。
3. `--full` 日志里同样出现一次上述 loopback 断连噪音，不影响 exit 0。

---

## 第二轮整改（2026-10-08，SR02-1..5）

### 独占根与 basetemp（本轮新政策）

本轮**不再使用共享 `%TEMP%` 作为 pytest basetemp**：所有测试、TMP/TEMP/TMPDIR、
Playwright 浏览器 profile 全部落在本包自己创建的根里。

| 路径 / 标识 | 谁创建 | 用途 | 终态 |
|---|---|---|---|
| `C:/Users/郑曾波/Projects/StockWiki/runs/swr02-remediation-20261008-01` | 本轮 | 独占 `tmp/`（全部 `--basetemp`、`TMP`/`TEMP`/`TMPDIR`）、`logs/` 原始输出 | **cleaned=true**：证据先复制进 `docs/handoff/SW-REPAIR-02/logs/`，再按清单删除并 `lstat` 核不存在（`logs/cleanup_receipt_r2.json`，`applied=true`） |
| `C:/Users/郑曾波/Projects/StockWiki/runs/swr02-acceptance-20261008-01` | 本轮 | 从结果 commit `c83c148` 导出的 `runtime/`（`stockwiki`+`tests`+legacy producer）与 `export-manifest.json`，跑原冻结 7 场景 | **cleaned=true**（同上，回执同一文件） |
| `docs/handoff/SW-REPAIR-02/logs/**` | 本轮 | 交接证据（RED/GREEN 日志、截图、回执、清单） | 保留（交接内容） |

**junction 处置（严格按卡内协议）**：清理前先做 inventory（`lstat`/`os.scandir`
**不跟随链接**）——两根内共 **48 个重解析点**（本轮 junction 反例在 `tmp_path` 里的
fixture），逐一解析两端精确绝对路径并核对**全部落在本包自己的根内**；随后**只非递归
`os.rmdir` 解除链接节点本身**（48/48 成功，48/48 目标在解除后仍存在），确认没有链接
残留后才逐树删除，最终 `lstat` 核两根均不存在。没有跟随任何 junction 删除外部内容。
CIM（`Win32_Process`）查询成功，若失败即停止清理；逐文件 SHA 与硬链接清点**未做**
（file set/size 已记在 `logs/isolation_inventory_r2.json`），范围如实写在
`logs/cleanup_receipt_r2.json.verification_scope`。

### 上一轮共享 TEMP 残留的现状（如实报告，不代删、不虚填）

`logs/isolation_inventory_r2.json`（本轮 inventory 原文）：

| 路径 | `lstat` 结果 | 本轮是否删除 |
|---|---|---|
| `%TEMP%/pytest-of-郑曾波/pytest-105` | **absent** | **否**（本 writer 没有对该路径执行任何删除） |
| `%TEMP%/pytest-of-郑曾波/pytest-109` | **absent** | **否** |
| `%TEMP%/pytest-of-郑曾波/pytest-110` | **absent** | **否** |
| `%TEMP%/pytest-of-郑曾波/pytest-111` | **absent** | **否** |
| `%TEMP%/pytest-of-郑曾波/pytest-146`、`-147`、`-148` | present | **否**（内容属 filing-fetch/publication-registry 另一条 lane 的测试，非本包创建，按卡内禁令不按编号/mtime 触碰） |

如实说明：

1. 这四条是**第一轮** worker 在共享 `%TEMP%` 下留下的 basetemp，第一轮 handoff 记录为
   `cleaned=false`（原始记录仍在 git 历史
   `git show 6d1dddb:docs/handoff/SW-REPAIR-02/handoff.json`）。
2. 本轮开工时它们**已经不存在**（`os.lstat` 逐条核对，`deleted_by_this_writer=false`）。
   可观测到的事实是：pytest 自身“保留最近 3 个编号目录”的清理机制在后续**其他 lane**
   的运行（`pytest-146`/`147`/`148`，2026-10-08 08:55–09:01）创建编号目录时会删除更早
   的编号目录。**具体是哪一次运行删除的无法事后取证**，因此本包**不声称**自己清理了
   它们，也**不把它们填成 `cleaned=true`**；`handoff.json.verification.temporary_roots`
   只登记**本轮自己创建**的两个根。
3. 目录内容已随路径消失，**归属/内容清单无法再回溯核对**；该取证缺口作为
   `open_items` 交 owner 确认，本包**不声称共享 TEMP 已恢复**。
4. 本轮全部测试改用独占 `basetemp`（上表），此后不再产生共享 TEMP 残留。

### 本轮端口 / 进程 / 网络

| 项 | 观察 |
|---|---|
| loopback HTTP | **143 请求 / 11 次测试 / 11 个临时端口**（`logs/green_e2e_browser_r2.log` 中 11 行 `[e2e] loopback HTTP only: …`，逐测试计数 `[18,10,12,18,13,12,9,18,10,9,14]`；汇总见 `logs/evidence_index_r2.json`） |
| 外部网络 / DNS / LLM / 付费调用 | **0**（同第一轮：socket guard、route abort、金丝雀 `swr02_guard_canaries_passed`） |
| 残留进程 | 无 playwright/chromium/pytest 残留；`Get-CimInstance Win32_Process` 命中的只有宿主 `msedgewebview2`（系统 WebView）与本命令自身，见 `logs/isolation_inventory_r2.json.processes` |
| 监听端口 | 所有测试服务绑定 `127.0.0.1:0` 临时端口并随进程结束关闭；无固定端口占用 |

### 本轮写入范围核对

- 只 `git add` 了卡内授权路径：`stockwiki/quick_scan_{backup,backup_manifest,profiles,rows}.py`、
  `stockwiki/ui_static/app.js`、`tests/test_swr_{backup,profiles}.py`、
  `docs/quick-scan-backup-restore.md`、`docs/ui.md`（结果 commit `c83c148`），
  以及 `docs/handoff/SW-REPAIR-02/**`（交接 commit）。没有 `git add -A`。
- 未改动 IQS / StockQA / Lab / company-wiki / 安装镜像 / 生产库 / 凭据；
  IQS 只读引用（`acceptance_cases.py`、`counterexamples/*.json`）字节未变。
- **未 push 任何远端**。
- `stockwiki/services/backup.py`、`ui_quick_scan.py`、`quick_scan_query.py`、
  `quick_scan_store.py` 等**未改动**（R2 无需改）。
