# DWA-04R 基线漂移全面审查与修复报告

- 审查人：IQS 总控（本次会话）
- 日期：2026-10-02
- 对象：`docs/implementation/reviews/dirty-worktree-audits/2026-10-01/DWA-04/` 冻结基线（6124 条）与 `2026-10-02-reaudit/DWA-04/` 新基线（416 条）
- 目标仓库：`C:\Users\郑曾波\Projects\revenue-forecast`（`fcap@ee0a82bf1eec935cf4e567eb42f0ef79efa0226`，两份快照 HEAD 一致）
- 独立复核：read-only agent 独立重推全部归因数字（结论 VERIFIED，无差异；其自查发现的自身解析 bug 已自纠，不影响结论）

## 1. 审查发现的缺陷与修复

### 1.1 快照生成器长路径漏哈希（已修复）

`2026-10-02-reaudit/DWA-04/snapshot-files.jsonl` 首版把 2 条超长路径（269/295 字符）误标 `inaccessible`。根因：Windows MAX_PATH 下 `open()`/`stat()` 对 260+ 字符路径失败。修复：以 Win32 扩展长度前缀 `\\?\` 重新 stat/哈希，2 条均成功且 SHA-256 与 10-01 快照同路径哈希**逐字节一致**（`1cbfb1a2ed055fa1…`、`0b2b9fdf710255e0…`）。当前 manifest：416/416 全部 `hashed`，0 inaccessible；`snapshot.json` 计数与 `baseline_note` 已同步更新。

### 1.2 探针假阴性（方法学教训，已写入 findings.md）

相对路径 236–255 字符时 Python `os.path.exists`/`listdir` 返回假阴性（同文件绝对路径与 `cmd dir` 均可见）。后续深路径存在性核查一律用绝对路径 + `\\?\` 前缀，探针失败不得当文件消失。

## 2. 基线漂移归因（本次审查核心）

两份快照差异：` D` 3778→0；`??` 2334→404；` M` 12→12 不变。HEAD 一致，reflog 自 09-27 后无 checkout/reset/restore，`.git/index` mtime 仍为 09-27。

### 2.1 3778 条 ` D`（git 记为已删除）：幻影条目，非真实删除

| 证据 | 结果 |
|---|---|
| 3778 条路径今日磁盘存在性（绝对路径+`\\?\` 全量核验） | **3778/3778 全部存在**，0 条真消失 |
| 361 条两份 manifest 共有路径 SHA-256 对比 | **0 条不一致**（内容从未变） |
| 25 条随机抽样 mtime/ctime（Windows ctime=创建时间） | **全部 ≤ 2026-09-21**（最新 09-21 21:00:36），远早于 10-01 快照 |
| reflog / HEAD | 无任何恢复类操作；HEAD 与两份快照相同 |
| git 今日 stderr | 仍报 3 条 Permission denied + 1 条 Filename too long（可见性受限自证） |

**结论**：` D` 是 10-01 快照捕获时 git/文件系统可见性失败造成的幻影条目（与今日 stderr、`\\?\` 探针差异同族现象），不是事后删除或恢复。文件自 09-21 前创建后未被改写。

### 2.2 `??` 数量精确闭合

| 集合 | 数量 | 今日状态 |
|---|---:|---|
| 冻结 `??` 总数 | 2334 | |
| 其中 `.tmp-zr408-unit*`（`os.listdir`/`icacls` 均拒绝访问，mtime 停在 08-18） | 1971 | 当前 shell 不可见，**去留未知** |
| 其中 `reviews/revenue/scratch/{model-tests(1),publication-tests(8),pytest(5)}` | 14 | 父目录拒绝访问，**去留未知** |
| 其余正常路径 | 349 | 349 条全部仍在今日状态中 |
| 今日新增（不在冻结清单） | 55 | mtime=ctime=**2026-09-27 10:05–11:11**，父链 mtime 全停在 09-27——是 10-01 快照**漏视**的旧文件，非新文件 |

等式：2334 − 1971 − 14 + 55 = **404** = 今日 `??` 数（404 + 12 ` M` = 416）。独立复核重推得同一组数字。

### 2.3 归因边界（保持未知的部分）

- `.tmp-zr408-unit*` 三目录为何对当前 shell 长期 ACL 拒绝（icacls 亦拒绝）而 10-01 捕获环境可见：**环境可见性差异，机制未知**；其中 1971 条文件是否仍在磁盘无法验证。
- 14 条 scratch `??` 同理。
- 快照当时 git 报 ` D` 的具体失败层（stat vs index 交互）无法从现有只读证据区分；不影响"非真实删除"结论。

## 3. 处置建议（均需 owner 精确授权，本次不执行）

1. **不清理、不恢复、不提交** revenue-forecast 任何路径；3778 条"幻影 D"不是待删清单。
2. DWA-04R 复审卡的"第一问"（漂移归因）以本报告为总控结论收口；独立 harness 的逐路径盘点可以只对当前 416 条做，加上对 1971+14 可见性受限组的"未知"标注。
3. 若 owner 需要 `.tmp-zr408-unit*`/scratch 组的去留判定，需要在能读取该 ACL 的环境（或由 owner 本机）执行只读核查。

## 4. 变更清单（本仓）

- `2026-10-02-reaudit/DWA-04/snapshot-files.jsonl`：2 条补哈希
- `2026-10-02-reaudit/DWA-04/snapshot.json`：计数更新 + baseline_note
- 本报告：`2026-10-02-reaudit/DWA-04/coordinator-review-2026-10-02.md`
- `task-packet.md`：归因结论写入（见同目录）
- 目标仓库零写入；无网络/API/下载；临时脚本在系统 TEMP，验收后清理。
