# DWA-01 — filing-fetch 未提交改动只读盘点审计报告

审计执行时间：2026-10-01（会话内完成）
审计范围：目标仓库 `C:\Users\郑曾波\Projects\filing-fetch`（分支 `fcap`，HEAD `d35b6f5b09f1a7dad37d226504bf998802a852d7`）的未提交状态
审计性质：全程只读，未修改、暂存、提交任何目标仓库内容

## 1. 快照核验

| 检查项 | 快照值 | 实测值 | 结果 |
|---|---|---|---|
| HEAD | `d35b6f5b09f1a7dad37d226504bf998802a852d7` | `d35b6f5b09f1a7dad37d226504bf998802a852d7` | ✅ 一致 |
| 分支 | `fcap` | `fcap` | ✅ 一致 |
| 状态条目 | 1（`??`=1） | 1（`??`=1） | ✅ 一致 |
| Porcelain SHA-256 | `b8f89e334f90693f87ca757f033345e41981120638f76b1f2e06eb73bef78354` | 同左（按 `status_digest_canonicalization` 规则：条目 LF 连接 + 尾部 LF，UTF-8 字节 SHA-256） | ✅ 一致 |
| 文件元数据（`config/FMP_API_KEY.txt`） | size=32，mtime=2026-09-27T05:54:08Z | size=32，mtime_utc=2026-09-27 05:54:08（本地存储 +0100 折算） | ✅ 一致 |
| 文件哈希重算 | 快照即 `omitted-sensitive-path`（无哈希） | 按规则不重算、不读取内容 | ✅ 一致 |

- 开始核验：全部一致，基于快照归因成立。
- 审计期间未做任何写操作；结束复验（状态摘要 + HEAD + 分支）与快照一致：**仓库在审计期间稳定，无漂移**。

## 2. 逐项状态覆盖表

| 状态码 | 路径 | 用途 | 证据 | 分类 | 为何未提交 | 建议动作 | 信心度 |
|---|---|---|---|---|---|---|---|
| `??` | `config/FMP_API_KEY.txt` | **未知**。文件名、32 字节大小、纯文本格式与"第三方 API key 凭据文件"形态高度吻合（疑似凭据），但未读取内容（按任务卡禁止），且仓库内无任何证据证实其用途 | 见 §3 证据清单 | 个人配置/数据（疑似凭据，消费方未知） | **未知**。无 `.gitignore` 规则覆盖该项（非"被有意 ignore"），也无未提交的代码改动与之配套；只能如实标注未知 | 不要提交；由 owner 本地确认用途后二选一：加入 `.gitignore` 保留本地，或移出仓库。不依据文件名建议删除 | 路径归属（`config/`、同目录 `company_wiki.json` 已被跟踪）高；用途证据不足 |

## 3. 证据清单（均为只读）

- `.gitignore`（第 1-16 行）：仅覆盖缓存/生成物类路径（`__pycache__`、`.codegraph/`、`e2e/.runs/` 等），无任何 secrets/凭据条目，也不涵盖 `config/` 或 `*.txt`。
- `git ls-files config/` → 仅 `config/company_wiki.json` 已跟踪；`config/FMP_API_KEY.txt` 无提交历史，属新出现的未跟踪文件。
- 全仓库代码与文档 grep：无 `FMP_API_KEY` / `FMP` / `financialmodelingprep` 引用；`fetch_filing.py` 中 config 相关逻辑只读本仓库 `config/company_wiki.json` 及外部 company_wiki_root 下的 `source_catalog.yaml`/`source_acquisition.yaml`（scripts/fetch_filing.py:45,74,131-146,890-995），均不指向被审计文件。
- 提交 `be1f375`（分支 `codex/ff-source-companion-integration`，2026-09-29）含 "FMP" 字样，但其改动仅为 reason 字符串 `cwp_fmp_import_contract_pending`（scripts/transcript_companion.py:141），与该文件无实证关联，仅缩写疑似相同。
- 时间线相关性（仅为相关性，非归因）：文件 mtime 2026-09-27T05:54:08Z；同日下午有提交 `90771d8`（SourceReader v2 verification，15:41 +0100）及 worktree `ff-source-reader-v2-20260927`。该提交的代码不读取此 key。

## 4. 临时文件/缓存判断

- 该路径不属于生成物/缓存类：`.gitignore` 未登记，仓库内无可复现其来源的代码路径。
- 是否可重建：不能从仓库内容重建。只有 owner 知晓其来源（是否可从服务商账户重新获取——此为推测，未知）。
- 是否被依赖：主 worktree 内无消费代码；不能排除被仓库外进程或人工流程使用。仅凭文件名不能建议删除。

## 5. 若考虑提交

不建议提交该文件本身。若 owner 确认为本地开发凭据且要保留，建议提交边界为仅 `.gitignore` 增量（一行 `config/FMP_API_KEY.txt` 或更通用的 secrets 条目），单条提交即可。注意仓库已有 pre-commit/pre-push 门禁（提交 `eceae2d`、`89c8bdb`），但门禁不阻断 `git add -A` 时凭据误入。

## 6. 汇总结论

| 类别 | 数量 |
|---|---|
| 可归档（适合提交） | 0 |
| 可忽略 | 0 |
| 需保留本地（疑似凭据，待 owner 决策） | 1（`config/FMP_API_KEY.txt`） |
| 疑似临时，待 owner 确认 | 0 |
| 不能判断（用途与未提交原因） | 1（即同一文件） |

风险提示：当前 `git add -A` / `git add .` 均会将疑似凭据纳入暂存并可能提交。建议 owner 决策顺序：先本人本地确认内容，再选择 ignore 或迁移；如确认曾误提交则需改密处理。
