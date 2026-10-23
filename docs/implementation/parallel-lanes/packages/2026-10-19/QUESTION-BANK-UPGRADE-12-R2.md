# QUESTION-BANK-UPGRADE-12 整改要求（R2）— 生成器覆盖导致 B3 回退 + B2 快照链未闭合

- 包 ID：QUESTION-BANK-UPGRADE-12
- 交付快照：HEAD `9c08550`
- 结论：**R1 的实质内容整改（B1/N2/N3/N5/N6）已在 HEAD 验证通过；但 B3 被你自己的最后一个提交覆盖丢失，B2 快照链差一步闭合。修完这两项即可验收。**

## 总控在 HEAD 上的逐项核对结果

| 项 | HEAD 状态 | 证据 |
|---|---|---|
| B1 capital_markets 3.0.0 | ✅ 已修 | `docs/decisions/capital_markets.json:17,27` 现写「rubric_version 升 3.0.0（后继题…）」 |
| N2 compose 环检测 | ✅ 已修 | `tools/compose.py:112-125` DFS 状态检测，环 → `BankError("dependency cycle: …")` |
| N3 悬空事件 + 引用校验 | ✅ 已修 | `tools/validate_bank.py:335` `ref not on disk` 逐条校验 |
| N5 文档版本 | ✅ 已修 | README:6、bank-design:3、migration:3 均 4.2.0/62/257（migration:40 保留「v4.0.0 时点」历史账目，属正确表述） |
| N6 lock id | ✅ 已修 | 主控 CLI `--verify-references` **exit 0 / valid** |
| 三份 round-03 | ✅ passed | content/format/architecture，`reviewed_commit=ec8cd97` |
| **B3 数字 26** | ❌ **回退** | `git show HEAD:docs/handoff/QUESTION-BANK-UPGRADE-12/report.md` AC-07 仍写 **31** |
| **B2 快照链** | ⚠️ 差一步 | `reviewed_commit=ec8cd97`，但其后还有 2 个提交（`6ce17a4` 内容修正、`9c08550` handoff 套件） |

## 阻塞项 1（B3 复发）— R1 修复被你自己的 handoff file set 提交覆盖

证据链：

1. `6ce17a4` 正确修了 B3：AC-07 改为「+ 26 仪器标记；R1 更正：原写 31 为 v4.1.0 时代锁的输出，当前 active 锁实测 26」，并新增 B3 已修说明与 B1 流程说明；
2. `9c08550`（"R1 handoff file set @ final snapshot 6ce17a4"）对 report.md 做了 **-34 行 / +8 行** 的重建，把 AC-07 打回 **31**，R1 整改记录、B3 已修说明、B1 流程说明、根因与教训**全部丢失**；
3. 结果：HEAD 上的 report.md 是一份精简旧版（5 个标题，R1 字样仅存 "R1→R2" 无关字样）。

**根因判断**：`docs/decisions/_authoring/build_handoff.py`（在 `6ce17a4` 中改了 37 行）生成 handoff 文件集时，report 模板/数据源不含 R1 内容，手改 report.md 的成果被下一次生成整体覆盖。

**要求**：
1. 把 R1 整改记录（含 B1 流程说明、B3 更正说明、根因与流程教训）**并入生成器的 report 数据源**，重跑生成器，使 `git show HEAD:docs/handoff/QUESTION-BANK-UPGRADE-12/report.md` 同时包含：
   - AC-07 = **26**（含与 31 的口径差异说明）；
   - R1 整改记录一节（逐条 D/B/N 对应）；
2. **在 report 中明确记录本次覆盖事件与根因**（生成器源不含 R1 → 手改被覆盖），这是第二次转录类事故（B1 是审查记录先于修改写 fixed，本次是修复被生成器回滚），必须写成可执行的流程约束：今后改 handoff 报告必须先改生成器源，再生成；
3. 生成后重跑三件套（validate --releases / unittest / diff --old baseline）并贴真实输出。

## 阻塞项 2（B2 尾巴）— reviewed_commit 未指向最终 payload

当前：三份 `final.json` 的 `reviewed_commit=ec8cd97`，但 `ec8cd97..HEAD` 还有 2 个提交：

- `6ce17a4` 含**内容级**变更（README/bank-design/migration 的 N5 修正、`build_handoff.py` 改动）；
- `9c08550` handoff 套件（元数据级）。

按交接规则，`review.final.json.reviewed_commit` 必须引用最终 payload commit（handoff 元数据提交之前的那个 HEAD）。

**要求（二选一，说明选了哪个）**：
- **A（推荐）**：本轮修完 B3 后，把三份 `final.json` 的 `reviewed_commit` 更新为最终内容提交，并在各 round-04（或 final 的 note 字段）中写明该快照相对 `ec8cd97` 的差异清单（应只有 report/生成器/文档级变更，无 modules/tools 内容语义变更）；
- **B**：若认为 `6ce17a4..HEAD` 全部属元数据级，那么在 `report.md` 中列出这 2 个提交的逐文件差异定性表（内容 vs 元数据），并让三份 final.json 显式声明「payload 冻结于 ec8cd97，其后仅元数据」——但注意 N5 的文档修正就是内容级，选 B 必须先把 N5 文档修正回挪到 ec8cd97 之前的语义位置（新提交即可），否则 B 不成立。

## 复验要求

1. `git status` clean；
2. 以下**全部在 HEAD 上验证**（`git show HEAD:<path>`），不接受「在历史提交里存在过」：

```
git show HEAD:docs/handoff/QUESTION-BANK-UPGRADE-12/report.md | grep -E "26 仪器|R1 整改"
git show HEAD:docs/decisions/capital_markets.json | grep "3.0.0"
```

3. 重跑五条 check 命令（validate --releases / unittest / compose / diff / simulate）全绿；
4. 主控 CLI：

```
python scripts\parallel_handoff_cli.py --input <lab>\docs\handoff\QUESTION-BANK-UPGRADE-12\handoff.json --package-id QUESTION-BANK-UPGRADE-12 --catalog docs/implementation/parallel-lanes/packages/2026-10-19/manifest.json --verify-references
```

要求 exit 0；
5. report 中新增「R2 覆盖事件记录」一节，写明：谁覆盖了什么、为什么、如何防止（生成器源约束）。

## 边界

不关闭 S01/S04/S05/S06 包级门；`production_ready=false` 不变。B1 的历史虚假整改声明、本次的生成器覆盖，都只修正事实记录，不改审计结论本身。
