# EVID-LAB-01 isolation（临时根、网络/费用、进程、清理）

## 临时根（全部在 Lab 自有 `.temp-roots/`，manifest 独占）

| 路径 | 创建者 | 清理 |
|---|---|---|
| `.temp-roots/pytest-<pid>-<uuid>/` | `tests/conftest.py` 会话开始创建；同时重写 `TEMP`/`TMP`/`TMPDIR` 与 `tempfile.tempdir`，pytest `tmp_path`、子进程全部继承该根 | `atexit` 删除（会话结束核验：最终回归后 `.temp-roots/` 无残留条目） |
| `.temp-roots/smoke1/` | 交付前 CLI 冒烟（`replay --input index`） | 会话内 `rm -rf` 删除并核验 |
| `.temp-roots/log-replay/` | 日志采集用 replay 输出 | 采集 `replay-verification.json` 后删除并核验 |
| `reports/` | 本包预留输出目录（`.gitkeep`） | 测试期间未使用；E2E 输出一律进 `.temp-roots` |
| `.temp-roots/staging-<pid>-<uuid>/` | `replay` 发布staging（structure-rules/3） | 发布成功=rename消费；失败=publish_output清理并核验不存在；崩溃残留仅位于`.temp-roots`内 |
| `.temp-roots/controller-cases-<pid>-<uuid>/` | 总控反例适配版用例根 | tearDownClass删类目录 + atexit删根；实测无残留 |
| `.temp-roots/e2e-public-runs/` | 公开CLI批跑（index×2 + 34 fixture） | 跑完脚本内 `shutil.rmtree` 并断言不存在 |
| `.temp-roots/e2e-remaining-repairs-<pid>/` | 残余整改批跑（index×2 + 34 fixture，runner在 `.temp-roots/` 内、跑完删） | 脚本内 `shutil.rmtree` 并断言不存在；回执 `logs/remaining-repairs-2026-10-08/public-cli-runs.json` |

- **严格清理（2026-10-08起）**：删除前 `tests/conftest.py` 逐文件记录相对路径+SHA256
  清单（manifest_sha256）、检测 symlink/junction（`is_symlink`/`os.path.isjunction`），
  `shutil.rmtree` **不再使用 ignore_errors**；删除后核验根不存在，失败逐条打印
  `[cleanup-gap]`；回执 `logs/remediation-2026-10-08/cleanup-receipt-p<pid>.json`
  与本批 `logs/remaining-repairs-2026-10-08/cleanup-receipt-p<pid>.json`
  （file_count/total_bytes/manifest_sha256/links_or_junctions/gaps/verified_absent）。
  回执 `gaps=[]` 且 `verified_absent=true` 才算恢复；否则在回执中明示缺口。
  两批回执各自独立保留，本批回执不替代上一批的历史归属证明。
- 不按 mtime/pytest 编号/目录名清理共享 TEMP；只删本 manifest 列出的自有路径。
- 全程未创建 junction/symlink；删除前检查 `is_symlink()`。
- **按输入锁只读 IQS**（`inputs.lock.json` 绑定的128个独立文件逐字节核验），
  未写入 IQS/StockQA/StockWiki/company-wiki 或任何其他仓库；未创建 `.env`。

## 网络 / key / 付费

| 项 | 计数 | 证据 |
|---|---:|---|
| 网络尝试 | 0 | `guards.py` 离线守卫拦截 `socket.connect`/`create_connection`；E2E 断言 `network_attempts==0`（含 subprocess 汇总）；`test_network_guard_blocks_connections` 证明守卫本身有效（该用例计数后复位） |
| key 读取 | 0 | `src/` 无任何凭据读取（仅 `IQS_EVIDENCE_LAB_IQS_ROOT` 路径覆盖）；conftest 清除 `*_API_KEY`；subprocess 用例断言环境无 key |
| 付费模型调用 | 0 | 包内无 HTTP 客户端；summary `paid_model_calls=0` |
| 搜索/下载 | 0 | 同上；`search_calls=0`、`downloads=0` |

## 进程与端口

- 唯一子进程：E2E 中 `python -m iqs_evidence_lab replay`（`subprocess.run`，timeout=600，
  已等待退出并断言 returncode）。无后台服务、无端口监听。
- 测试结束无残留 Python 子进程；strict 终态 = 本次会话启动的子进程全部已回收。

## 输入只读核验

- 每次 replay/E2E 前后对 `snapshot_input_hashes(inputs.lock.json)`（lock + 全部绑定文件，
  **224次校验覆盖127个绑定路径，含lock自身共128个独立文件**——校验次数≠文件数）
  做前后对比，字节级一致；本批公开CLI批跑 `input_hashes_unchanged=true`。
- IQS/StockQA/StockWiki/company-wiki 全程只读（按输入锁读）；未 reset/clean/stash 任何他人改动。
- **本批唯一一次越界写入（已当场撤销并披露）**：会话中一条 shell 重定向
  `ls ... 2>nul` 在 IQS 根生成了 0 字节未跟踪文件 `nul`；发现后立即删除。
  事后 `git -C <IQS> status --porcelain` 仅剩先前就存在的 `?? opencode.json`，
  无任何已跟踪文件被修改、无新 commit；锁定输入 128 个文件 SHA 前后一致。

## 错误后环境恢复

- 输出目录在**全部输入验证与计算完成之后**才 `mkdir`：输入漂移（exit2）、输出冲突（exit3）、
  fixture 期望失败（exit4）均不产生任何文件。
- 失败用例断言：原输出目录文件清单不变、guard 无网络尝试、临时根仍受控。
- 测试失败路径同样走 conftest 的 atexit 清理（环境恢复）。

## 异常与残留

- 无未清理残留；`.temp-roots/` 最终为空；`cleaned=true` 有核验依据。
- 旧 pytest/冒烟目录若在异常中断下残留，只会位于 `.temp-roots/` 内，可安全删除；
  未触碰共享 TEMP 或他仓路径。
