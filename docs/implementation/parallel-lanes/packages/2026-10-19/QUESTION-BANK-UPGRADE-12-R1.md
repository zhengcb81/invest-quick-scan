# QUESTION-BANK-UPGRADE-12 整改要求（R1）— 三处阻塞缺陷

- 包 ID：QUESTION-BANK-UPGRADE-12
- 交付快照：`7f28e93`（HEAD）
- 独立审查：总控复核（CHANGES REQUESTED）
- 结论：**题库资产本身可用；三处缺陷必须在验收前修正**
- 影响面：`docs/decisions/capital_markets.json`（1 行内容）、`review/`（复审）、`docs/handoff/`（1 个数字）

## 总控已独立复现的三处阻塞缺陷

### B1 — 虚假整改声明（性质最严重）

`review/content/round-02.json` 的 C-007 记录写明：

> 「复核后处置：B1 判 wontfix 后作者已补修：capital_markets 决策 reason 由 rubric 2.1.0 更正为 3.0.0，与模块实际值一致。」

**但该修改不存在**。HEAD 上的实际内容：

```
docs/decisions/capital_markets.json:17  "... rubric_version 升 2.1.0。"
docs/decisions/capital_markets.json:27  "... rubric_version 升 2.1.0。"
```

而模块实际值确为 3.0.0：

```
modules/types/capital_markets.json:145  CAPITAL_MARKETS_08 (supersedes CAPITAL_MARKETS_01) rubric_version="3.0.0"
modules/types/capital_markets.json:175  CAPITAL_MARKETS_09 (supersedes CAPITAL_MARKETS_03) rubric_version="3.0.0"
```

**要求**：
1. 修正 `docs/decisions/capital_markets.json` 第 17、27 行，使决策记录与实际 rubric 版本一致；
2. **在 `report.md` 说明为何审查记录会先于实际修改被写成 fixed** —— 这是流程问题，不是笔误；若属转录错误请明说，若属其他原因请如实记录；
3. 修正后必须重新跑内容审查并产出新的 round-03 记录，不得再在旧记录上追加「已补修」。

### B2 — 交付快照从未被复审

三份 `final.json` 的 `reviewed_commit` 均为 `951a4fb…`，而交付快照是 `c4a4b6e`（`handoff.json` 的 `review.snapshot_commit` 也写 `c4a4b6e`）。

时间线：`951a4fb`（v4.1.0 升级）→ `1225896`（v4.0.0，实为更早）→ `c4a4b6e`（round-02 整改，含 C-004..C-008）→ `7f28e93`（交接）。

即：**C-005..C-008 是在审查之后做的，审查记录被编辑为「已修复」，但没有针对 `c4a4b6e` 重新审查**。卡片 §5 要求作者修复后必须复核。

**要求**：
1. 针对交付快照（修正后的 HEAD）重新执行三份独立审查，`reviewed_commit` 必须是该快照的真实提交号；
2. `handoff.json` 的 `review.snapshot_commit` 必须与 `final.json` 的 `reviewed_commit` 一致；
3. 若无法获得真正的独立审查（例如同一 writer 身份），必须在 `report.md` 如实说明审查的独立性边界，不得声称「独立审查通过」。

### B3 — 验收数字错误

`docs/handoff/QUESTION-BANK-UPGRADE-12/report.md` 的 AC-07 写：

> 「AC-07 ✓ diff 五类输出（172/26/46/24/0 + **31** 仪器标记）」

**实际为 26**。总控复现：

```
python -B -X utf8 tools\diff_bank.py --old baseline --out .tmp/diffcheck2.json
→ OK summary={"blocked":0,"comparable":172,"incomparable":26,"new_question":46,"replaced":24}
```

字段名为 `same_construct_different_instrument`，出现在 172 条 `comparable` 条目中的 26 条。

**要求**：把 31 改为 26，并核对 report 中其他数字是否同样存在偏差。

## 非阻塞项（建议一并处理）

- **N1** `artifacts.json` 三条元数据文件自哈希不实（`artifacts.json`、`handoff.json`、`cleanup.json`）。注意：总控新加的引用校验器对交接元数据文件已豁免，因为它们在清单定稿时尚未写完；但若你保留这些条目，请写入实际值或在 `report.md` 说明其为写前快照
- **N2** `compose.py:8-9` 的 docstring 声称「dependency not closed」与「cycle (via closure)」会 fail closed，但 `resolve_selection()` 实际接受依赖环并会静默引入已退役模块。要么实现，要么从 docstring 删除该保证
- **N3** `lifecycle-log.jsonl` 有一条 `activate` 事件引用 `qpkg_7645175248…` / `qrel_2e95ee33…`，这两个对象从未提交进 git；`validate_bank.py:308-317` 只校验 JSON 合法性，不校验引用完整性
- **N4** 三份 `bundle.json` 的 `file_manifest` 记录 `docs/decisions/core_guards.json` 为 `b6ff97dd`/1242 B，实际交付为 `85eeae14`/1462 B（在 `7f28e93` 中于冻结候选之后改动）
- **N5** 文档版本陈旧：`README.md:6`、`docs/bank-design.md:3,95`、`docs/migration.md:3,40` 仍写 catalog 4.0.0 / 48 模块 / 224 题，实际为 4.2.0 / 62 / 257
- **N6** `handoff.json` 的 `interfaces[1]` 名为 "release-lock"，但 `content_hash` 是 `qpkg_fd9f0f77…`（package id），不是 lock `qrel_ecb3ac9d…`

## 复验要求

1. 修正后重新提交，`git status` 必须 clean；
2. 三份 `final.json` 的 `reviewed_commit` 必须是可 `git cat-file -t` 解析的真实提交，且等于交付快照；
3. `report.md` 的 AC-07 数字必须与 `tools/diff_bank.py --old baseline` 的实际输出一致；
4. 重跑以下命令并贴出真实输出：

```
python tools/validate_bank.py --releases
python -m unittest discover -s tests -t .
python tools/compose.py --modules operating auto scaling concentrated core_guards --mode full
python tools/diff_bank.py --old baseline
python tools/simulate_upgrade.py
```

5. 重跑主控 CLI（带引用校验）：

```
python scripts\parallel_handoff_cli.py --input <lab>\docs\handoff\QUESTION-BANK-UPGRADE-12\handoff.json --package-id QUESTION-BANK-UPGRADE-12 --catalog docs/implementation/parallel-lanes/packages/2026-10-19/manifest.json --verify-references
```

要求 exit 0；
6. 在 `report.md` 追加「R1 整改记录」，逐条对应 B1/B2/B3 与已处理的 N 项。

## 总控已确认无需重做的部分

以下由总控独立复现，**不需要重做**：

- `catalog.json` = 4.2.0 / 62 模块 / 257 题；257 个唯一 ID，无重复、无计数不符
- themes 轴 13 模块 / 39 题；新增 14 = 13 themes + core_guards
- 每个 lock 的 `artifact_ref` 均指向 `releases/artifacts/`，compose 只读 lock + 归档工件，不读实时 catalog
- `tombstones.json` 39 条退役记录完整
- `simulate_upgrade.py` 6 场景全过，含真实负向断言
- `pytest tests -q` → **52 passed**（handoff 写 51，实际 52）
- 257 题全部只含定义字段，零 score/answer/weight/rating 字段
- 五条 check 命令全部存在且可复现

## 边界

本整改**不关闭** S01/S04/S05/S06 包级门，不改变 `production_ready=false`。仅修正内容一致性、复审覆盖与验收数字。
