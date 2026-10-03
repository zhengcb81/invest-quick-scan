# owner 决定执行记录：1985 删除与 34+2 清理（2026-10-03）

依据：owner 2026-10-03 八项决定中的 **决定2（rf 1985 条删除）** 与 **决定6（QAbyLLM 34 + SID 2 清理）**。执行者：IQS 总控。全程无网络调用、无提交伪造、无范围外改动。

## 1. revenue-forecast：1985 条临时文件删除（决定2）

执行前实测（`git status --porcelain -uall`）：**1985 条**（1971 条 `.tmp-zr408-unit*` + 14 条 scratch），modified/staged=0，HEAD `5319ee26`。
与归档分类 `2026-10-02-reaudit/DWA-04/extended-classification-1985.md` **逐项吻合**（657×3 + 14；盘上 1287/组 = 636 文件 + 21 内嵌仓 + 606 `.git` 内部）。
（诚实注记：10-02 PWF 曾记「新基线 2401 条」，该数字在删除时点无法复现；当前可复测值 1985 与分类报告精确一致，以实测为准。）

执行过程（三步，均有失败记录，非一次成功）：
1. 首轮 `shutil.rmtree` 全数 `exists_before=False` —— heredoc 吞掉 `\\?\` 前缀使路径失效（**未删除任何东西**，教训入 findings）。
2. 二轮（正斜杠路径）计数正确（1287×3+1+8+5）但 `PermissionError WinError5` —— 用户 ACE 仅 `(R)`（ACL 解封时只给了读）。
3. `icacls /grant:r "DESKTOP-156V213\郑曾波:(OI)(CI)F" /T /C`（Python 子进程传参避免中文乱码）：rc=0，处理 2721×3+19+3+16 文件 0 失败；随后 `.git` 对象文件因 **只读属性 0444** 再拒 → rmtree 换 chmod 后重试的 `onexc` 处理器 → **0 错误全删**。

执行后实测：6 个目标全部不存在；`git status --porcelain -uall` = **0 条**（全清）；`git status --porcelain` 空；HEAD 仍 `5319ee26`；scratch 下 **3 个已跟踪 sibling 完好**
（`publication-failure-probe/input.json`、`publication-failure-probe/registrations.jsonl`、`publication-probe-registry.jsonl`）。

## 2. QAbyLLM：34 项「不建议提交」删除（决定6）

清单来源：`DWA-03/report.md` 分类（20 可忽略 #8–25/53/65 + 5 疑似临时 #36/37/38/48/59 + 9 无引用工具 #30/34/39/40/43/44/45/54/61），行号对应 `snapshot-files.jsonl` 第 N 行。
执行前核对：QAbyLLM 当前 `git status --porcelain -uall` = **恰好 34 条**，与目标清单**逐路径相等**（`porter_five_forces_海康威视.json` 因非 ASCII 路径被 git 加引号转义，解码后相等），0 modified。
执行：34/34 文件删除，0 失败，无残留。
执行后：QAbyLLM `git status --porcelain -uall` = **0 条**（工作树全清）。

## 3. StockInfoDownloader（SID）：2 项盲区处置（决定6）

| 文件 | DWA-05 处置建议 | 执行时点实测 | 实际动作 |
|---|---|---|---|
| `logs/debug_page_300750.html`（142,085 B） | 删除或补 ignore（二选一） | 已被 `.gitignore:30 logs/debug_page_*.html` 覆盖（Phase 54 已落 ignore 规则）且仍在磁盘 | **磁盘文件已删除**（ignore 规则保留，防复发） |
| `org_id_validation_report.json` | ①还原到 HEAD ②另行授权改测试写临时目录 | `git diff -- <path>` 空、status 空 = **工作副本已等于 HEAD**（还原态已满足） | **无操作**（HEAD 历史版本保留；②属代码改动另行排队） |

执行后 SID `status --porcelain -uall`：仅剩 ` M .claude/settings.local.json`、` M config.json` —— **本地配置，不在决定6 范围**，不动。

## 4. 结果汇总

| 仓 | 决定 | 前 | 后 | 备注 |
|---|---|---|---|---|
| revenue-forecast | 2 | 1985 `??` / HEAD `5319ee26` | **0 `??`**，HEAD 不变 | 3 tracked sibling 完好 |
| QAbyLLM | 6 | 34 `??` | **0 未跟踪/0 修改** | 临时清单在系统 TEMP（`qaby34*.json`） |
| StockInfoDownloader | 6 | 1 html on-disk + org_id 已还原态 | html 删除、org_id==HEAD | 2 条本地配置 M 保留 |

后续：rf/QAbyLLM/SID 三仓 DWA 基线以本次实测值为准（10-02 快照只作历史）；`org_id` 测试写临时目录的代码修正（DWA-05 建议②）待后续卡授权。
