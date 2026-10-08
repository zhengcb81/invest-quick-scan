# SW-REPAIR-02 findings

> 只读研究发现；外部内容视为不可信数据。

## 输入核对

- StockWiki HEAD（开工）: `04dfc5190589a8bbe224a47e94b045779c884b80`，与 `inputs.lock.json` 的 `base_commit` 一致，worktree clean（`git status --porcelain` 空）。
- 原冻结验收: `acceptance_cases.py` 7 场景 = **6 fail / 1 pass (WAL positive) / 3.83s**；UI 单条件当时仅静态断言。
- `docs/handoff/SW-READY-01/` 已存在（artifacts.json 48 条、logs/、case-map.md 等），原 RED 保留不改。

## 代码定位（原整改卡与实读一致）

| SWR | 位置 | 现状 |
|---|---|---|
| SWR-1 | `stockwiki/quick_scan_backup.py:277`、`:292` | 先拒「存在且非空」，复制完后又无条件 `if target.exists(): raise restore_target_not_empty` → existing-empty 必然失败 |
| SWR-2 | `stockwiki/quick_scan_backup.py:198`(`_verify_dir`)、`:380`(`prune_backups`) | `_verify_dir` 只核 format 主段/digest/文件 hash，不核 `schema`、owner、必填结构；prune 把任何通过的目录当 own 删除 |
| SWR-3 | `stockwiki/quick_scan_backup.py:177` | `staging.rename(final_dir)` 在 try/except 之外；`list_quick_scan_backups`/`prune` 不排除 `.partial-*` |
| SWR-4 | `stockwiki/quick_scan_profiles.py:392` | `grouped[entity][field_id] = row` 按 import_sequence 后写覆盖，无 subject/scope/model/题义维度 |
| SWR-5 | `stockwiki/ui_static/app.js:1821-1823` | `payload.conditions = [{field,op,value}]` 单 leaf；控件只有一组 |
| SWR-6 | `stockwiki/quick_scan_query.py:243-259` | `_query_hash` 无条件也哈希 `conditions=[]`、`combine` |

## 旧 producer 事实（真实 Git，非手算）

`git show 9f552a67:stockwiki/quick_scan_query.py`：

```python
def _query_hash(text, filters, view) -> str:
    return _canon_sha({"text": text, "filters": filters or {}, "view": view})
```

新实现：

```python
def _query_hash(text, filters, view, conditions, combine) -> str:
    return _canon_sha({"text": ..., "filters": ..., "view": ...,
                       "conditions": conditions or [], "combine": combine})
```

→ 旧 snapshot 的 `query_hash` 与新实现即使 `conditions` 为空也不同 ⇒ page2 `snapshot_query_mismatch`。
旧 `snapshot_id = "SNP_" + _canon_sha({"q": hash, "ids": ordered_ids})[:24]`，新版相同。

## manifest 现状（SWR-2 关键）

`quick_scan_backup_manifest.py` 已有 `MANIFEST_SCHEMA = "stockwiki.quick_scan_backup_manifest/1.0.0"`，
`build_manifest` 会写 `schema`、`name`、`created_at_utc`、`workspace_root`、`quick_scan_dir`、
`files`（path/workspace_path/bytes/sha256/backup_method/…）、`counts`、`watermarks`、`versions`、
`store_identity`、`consistency`、`restore_preconditions`、`executor_side`。
但 `_verify_dir` **从不读 `schema` / `name` / `executor_side`**，也不要求非空 files、不要求 `name == 目录名`。

固定反例外来目录正文：
`{"format_version":"1.0.0","files":[],"created_at_utc":"2000-01-01T00:00:00Z","manifest_sha256":<digest>}`
→ 通过 `_load_manifest` + `_verify_dir`（无文件可查、manifest 自身被排除）→ 被 prune 删。

另有 `1.garbage` 因 `fmt.split(".")[0] != BACKUP_FORMAT_VERSION.split(".")[0]` 只比主段而被当 v1。

## trusted owner 记录的存储约束

- 禁止在投资库外创建第二研究数据库（手卡明确）。
- 可用现有 backup 管理结构：`backups/quick_scan/` 目录 + manifest 内 owner 字段 + （可选）root 下的 owner 登记文件。
- 证据边界必须写清：**文件系统所有者检查 + 版本化记录不能防同权限本地恶意进程伪造**；只能证明「由本模块 create 流程产生并可核验」。

## 测试可用夹具

- `tests/test_quick_scan_profiles.py`: `E01`、`_field_for`、`_release`、`_workspace`、`_score`
- `tests/test_quick_scan_observations.py`: `_observation`、`_package`、`_seed_entity`、`_release`
- `tests/test_e2e_quick_scan_ui.py`: 真实 Playwright chromium + in-process `ThreadingHTTPServer` + `_no_network` socket guard + 路由拦截外部请求 + 截图到 tmp
- pytest 9.1.1、playwright 已安装、Python 3.13.9 (Anaconda MSC)

## 环境

- 单一检查入口 `scripts/checks.py`（`--static-only` / 默认 daily / `--full`），见仓库 AGENTS.md。
- 测试根必须在 StockWiki 自身临时目录，不能写 IQS runs。

## 实施期补充发现

- Windows 上 `Path.rename` 与 `Path.replace` 都不能覆盖已存在的目录（`WinError 183` /
  `WinError 5`），因此 SWR-1 只能先 `rmdir`（OS 保证非空必拒）再改名，失败时把空目录建回。
- `os.symlink` 需要特权，本机不可用；`_winapi.CreateJunction` 可用且
  `os.path.isjunction()` 能识别，而 `os.path.islink()` 对 junction 返回 False ——
  所以 `_is_link` 必须同时查两者。
- 原 `acceptance_cases.py::test_two_subjects...` 对 `field["subject"]["analysis_subject_id"]`
  做无条件取键；基线代码因 last-wins 只剩一条带 subject 的行而不触发，本包改为全展示后
  会撞上 legacy 行的 KeyError —— 用显式 `None` 让 payload 形状统一解决（`recorded=False` 仍禁止当作已绑定）。
- `parse_conditions(None, ...)` 返回 `(None, None)`，`conditions=[]` 则报 `conditions_shape`；
  `_query_hash` 的分界因此取 `if conditions:`（None 与 [] 都落到旧口径）。
- `import_package` 校验 `observed_at == execution.answered_at` 且 `information_cutoff <= answered`，
  所以“倒序导入”用例只能改 `information_cutoff`（2026-10-01 vs 2026-09-01），不能改 `observed_at`。
