# EVID-LAB-01 isolation（临时根、网络/费用、进程、清理）

## 临时根（全部在 Lab 自有 `.temp-roots/`，manifest 独占）

| 路径 | 创建者 | 清理 |
|---|---|---|
| `.temp-roots/pytest-<pid>-<uuid>/` | `tests/conftest.py` 会话开始创建；同时重写 `TEMP`/`TMP`/`TMPDIR` 与 `tempfile.tempdir`，pytest `tmp_path`、子进程全部继承该根 | `atexit` 删除（会话结束核验：最终回归后 `.temp-roots/` 无残留条目） |
| `.temp-roots/smoke1/` | 交付前 CLI 冒烟（`replay --input index`） | 会话内 `rm -rf` 删除并核验 |
| `.temp-roots/log-replay/` | 日志采集用 replay 输出 | 采集 `replay-verification.json` 后删除并核验 |
| `reports/` | 本包预留输出目录（`.gitkeep`） | 测试期间未使用；E2E 输出一律进 `.temp-roots` |

- 不按 mtime/pytest 编号/目录名清理共享 TEMP；只删本 manifest 列出的自有路径。
- 全程未创建 junction/symlink；删除前检查 `is_symlink()`。
- 未读取、未写入其他仓库；未创建 `.env`。

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
  225 项）做前后对比，字节级一致。
- IQS/StockQA/StockWiki/company-wiki 全程只读；未 reset/clean/stash 任何他人改动。

## 错误后环境恢复

- 输出目录在**全部输入验证与计算完成之后**才 `mkdir`：输入漂移（exit2）、输出冲突（exit3）、
  fixture 期望失败（exit4）均不产生任何文件。
- 失败用例断言：原输出目录文件清单不变、guard 无网络尝试、临时根仍受控。
- 测试失败路径同样走 conftest 的 atexit 清理（环境恢复）。

## 异常与残留

- 无未清理残留；`.temp-roots/` 最终为空；`cleaned=true` 有核验依据。
- 旧 pytest/冒烟目录若在异常中断下残留，只会位于 `.temp-roots/` 内，可安全删除；
  未触碰共享 TEMP 或他仓路径。
