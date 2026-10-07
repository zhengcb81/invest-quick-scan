# SW-READY-01 隔离与清理记录

## 1. 前后状态摘要

| 项 | 开工（观察值） | 交付（观察值） |
|---|---|---|
| 源仓 | `C:/Users/郑曾波/Projects/StockWiki` | 同 |
| 分支 / HEAD | `master@9f552a6741dd093dc760ad6965458989cd027251` | `master@0d76dc39e8d9d53d451b1ce84c7147b0dd1bd2c5`（实施期间 master 被其他进程 fast-forward 到 `0b48919`，零路径重叠；见 summary §8） |
| 工作树 | clean（`git status --porcelain=v1` 空，与 inputs.lock `dirty_path_count=0` 一致） | 仅 `?? docs/handoff/`（本包证据目录，随后单独提交）；预存在的未跟踪 `nul` 于会话中出现又消失（非本 worker 创建或删除） |
| 暂存范围 | — | 仅本包 20 个文件（`git show 0d76dc3 --stat` 逐文件可核），未 `git add -A`；未提交任何外部仓/生产库/配置 |
| 其他仓（IQS/StockQA/Theme/Industry） | 只读 | 未写入（本包全部命令仅作用于 StockWiki 与 %TEMP%） |
| 真实工作区 `data/quick_scan/**` | 见 `logs/GREEN-real-data-acceptance.txt` 前置哈希 | 前后逐文件 SHA-256 一致（测试内断言 `_hash_tree(REAL_ROOT) == real_before`） |

## 2. 临时根 / 数据库 / 端口

| 用途 | 位置 | 创建 | 清理 |
|---|---|---|---|
| 单元/集成 tmp（pytest `tmp_path`） | `%LOCALAPPDATA%\Temp\pytest-of-郑曾波\pytest-{6..9}\…` | 是 | **已删除**（`rm -rf pytest-6..9`，本包截图/日志先复制到 `logs/e2e/` 与 `logs/`；删除前逐目录核对内容均为本包测试名） |
| E2E 工作区（2000 实体种子 + 观察导入） | `…\pytest-9\qs-e2e-ws0` | 是 | 随上删除 |
| E2E/HTTP 服务器端口 | `127.0.0.1:0`（每次临时端口，观察到 59070/65500 等） | 是 | 进程内线程 `server.shutdown()+server_close()`，测试结束端口释放；无监听残留 |
| Playwright chromium（headless） | `ms-playwright\chromium-*`（只读使用） | 每测试启动，fixture `context.close()+browser.close()` | 已退出（现存 `chrome.exe` 均为用户自有 `C:\Program Files\Google\Chrome`，与本包无关，未触碰） |
| golden 生成临时根 | `%TEMP%\tmp*\golden_ws`、`golden_restore` | 是 | **已删除**（证据已落 `logs/golden/`） |
| 真实数据副本 | `…\pytest-*\real-copy`、`restore-target`（只含 `data/quick_scan/**` 最小复制） | 是 | 随 pytest 根删除；真实工作区只读（哈希前后一致断言） |
| 覆盖率数据 | `scripts/checks.py --full` 的独占 scratch（不在仓内） | 是 | 由 checks.py 自管（`COVERAGE_FILE` 指向 scratch），仓内无 `.coverage` 残留（`git status` 仅 `docs/handoff/`） |

## 3. 网络 / 搜索 / 模型 / 付费计数

| 计数 | 值 | 证据 |
|---|---|---|
| 外部网络请求（TCP 连出） | **0** | 三重防护：① 测试内 `socket.socket.connect` loopback guard（非 127.0.0.1/::1 直接 AssertionError）；② 浏览器 `page.route` 拦截并记录所有非本服务 URL（fixture teardown 断言为空）；③ 所有响应回执 `network_calls=0` |
| 搜索调用 | **0** | 快扫路径不下载财报/网页/公司文档；未调用任何 search 函数；下载相关目录未创建 |
| LLM/模型调用 | **0** | `llm_calls=0` 回执 + 无新增 `*llm*` 模块导入（测试断言）+ loopback guard；`live=off` 未启用任何 provider |
| 付费调用 | **0** | 无 provider 凭据使用、无费用预留；恢复回执固定 `执行侧未核验、禁止恢复收费`、`paid_dispatch_restored=false` |
| 外部仓写入 | **0** | `external_writes=false`：只写 StockWiki 仓内本包文件 + 上述临时根 |
| 真实生产数据写入 | **0** | 真实数据测试为只读 + 副本操作，前后哈希断言 |

## 4. 清理证明

1. 手工删除的仅为本包创建的临时根（§2 表中标注“已删除”），删除前核对目录内容属于本包测试；共享/真实目录未做任何删除。
2. 权威数据未删未改：`data/quick_scan/**`、身份/名单版本、观察、ACK、费用相关文件在真实工作区前后哈希一致；`backups/` 下未对真实工作区写入任何备份（真实数据测试只对副本执行 create/restore）。
3. 保留策略反例证明 `prune` 不会触碰权威目录（`test_rev04_retention_only_removes_own_verified_backups`）。
4. 测试进程/端口已结束（无残留 chrome/headless、无监听端口）。
5. 仓内未留下 `.coverage`、缓存或临时 JSON（`git status` 仅 `?? docs/handoff/`；`__pycache__` 为 git 忽略的解释器产物）。

## 5. 异常与残留（如实记录）

1. `check_all --full` 日志中出现一行 `Exception occurred during processing of request from ('127.0.0.1', …)`（`http.server` 在某客户端提前断开时的 stderr 提示）：**无测试失败**（990 passed / 18 skipped，exit 0）；单独重跑 UI HTTP 测试 11 passed 且不再出现。判定为无害的既有 HTTP 服务器日志，未修改产品行为。
2. 18 个 skipped 全部为既有跳过：`tests/e2e/test_cwp_*` 17 个（需 `STOCKWIKI_CWP_PROJECT`，本包未配置也不应配置）+ `tests/test_narrative_process.py` 1 个（Windows 进程守护，POSIX only）。**本包 34 个测试在 `--full` 中全部实际执行**（无 skip/xfail）。
3. 未跟踪文件 `nul` 于会话中出现后消失：非本 worker 创建或删除，未暂存、未清理；记录以备总控核对。
4. 实施期间 master 被其他进程 fast-forward（`codex/g2-sw-daily` 合并）：与本包路径零重叠，按 README“无关变化记录新基线”处理，未覆盖、未回退对方改动（见 summary §8）。
