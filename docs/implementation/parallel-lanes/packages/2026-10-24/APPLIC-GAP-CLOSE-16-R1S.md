# APPLIC-GAP-CLOSE-16 整改补充（R1S）— 独立审查新增 1 个阻塞项 + R1 自身缺陷 + 6 项一致性

- 包 ID：APPLIC-GAP-CLOSE-16
- 适用对象：**正在进行的 R1 整改**（独立审查确认 worker 已于 11:55 左右开改 `parity_check.py` / `tests/test_parity_known_gaps.py`）
- 来源：独立对抗审查（pin 在交付 HEAD `6b15c55`，gate 复现用**已提交 blob** 而非脏工作树）
- 结论：R1 的核心判断被独立复现确认（含「交付数据结论正确、门禁不成立」）；但 **R1 漏了一个阻塞项（B2），且 R1 自己给出的「任何非同值即 open」规则与 gap-2 的缺席兜底冲突（N4）**。按下面一起改，不要只按 R1 原文改。

## B2（新阻塞）— 测试里有一条**断言 fail-open** 的用例，R1 漏了

`tests/test_parity_known_gaps.py:211-225` 的 `test_absence_fallback_does_not_open_rewrites_gap` 断言：

```python
# 非同一值对（no_rule_fail_closed -> no_route_decision_in_source）→ 期望 closed
```

这不是「测试覆盖不足」，而是**把错误行为写成了回归锁定**：修好判定逻辑后这条测试会红，必须**反转它**（改成正例断言 open 或删除并替换为正确的缺席兜底测试 —— 见 N4 的区分）。

**要求**：修好后该文件不得存在任何断言「非同值 → closed」的用例；新增以下四类（R1 已要求，此处重申并补第五类）：
1. 全部同值 → closed；
2. 已知改写目标（`routing_gate_below_threshold` / `routing_rule_matched`）且左≠右 → open；
3. **未知目标非同值 → open**（原 fail-open 的回归锁）；
4. 混合（同值 + 未知目标非同值）→ open；
5. **空集与畸形输入 → 不得 closed**（见 N3）。

## N4（R1 自身缺陷）— R1 的「任何非同值 → open」与 gap-2 缺席兜底冲突，必须分类

独立审查指出：R1 的规则在「UI resolver 少返回格子」时会产出 `basis -> None` 对，按 R1 一律判 open 会**误伤**（这不是改写，是数据不完整），并与 gap-2 的「缺席 = not_evaluated」语义混淆。

**要求**：把 `basis_gaps` 的每一对按**三类**归类，而不是两类：

| 类别 | 判据 | 对 gap-1 的作用 |
|---|---|---|
| `identity` | 左侧 == 右侧，且右侧非空 | 计入同值 |
| `rewrite` | 右侧 ∈ {两个已知改写目标} 且 左≠右 | **open**（原判，正确） |
| `deviation` | 其余任何 左≠右 且 右侧非空 | **open**（fail-closed，本缺陷的修复目标） |
| `missing` | 右侧为空 / None（UI 未返回该格） | **不得 closed**：gap-1 报 `incomplete`（第三态），并列出缺失对计数；是否同时使 gap-2 变化由实现自定，但必须在报告里说清 |

`closed` 的合法条件收窄为：**`identity` 覆盖全部对，且 `rewrite`/`deviation`/`missing` 均为 0，且 `pairs_total > 0`**。

## N3 — 空集与畸形输入不得 closed

独立审查实测：`{}` → closed（total 0）；`{"noseparator": 3}` → closed；`{"applicable -> common_always_applicable": 7}` → closed（右侧不是改写目标但左≠右）。

**要求**：
- `pairs_total == 0` → 第三态 `no_evidence`（或 `incomplete`），**不得 closed**；
- 无法按 `" -> "` 拆分的对 → `deviation`（并计入报告），不得静默归为同值；
- 左侧本身就是 `routing_rule_matched` 的同值对（如 `routing_rule_matched -> routing_rule_matched`）不得被误判为 rewrite（先判同值，再判 rewrite）。

## B3 — 已签收文档中的 fail-closed 表述**当前为假**，修好后必须让文案与实际一致

独立审查逐条核对：`demo/signoff-gap-close-16.json:21`（及问题 `:11`）、`handoff.json:118,124`、`summary.md:36`、`report.md:18` 都声称「closed 判定随实测自动回退、证据不足不会报 closed」。实测：仅「回退到 BRIDGE-15 前行为」这一窄场景成立；未知目标、空集、缺格三种场景都会假 closed。

**要求（不得静默改写已签收文件）**：
1. 代码修好后，先确认新保证的**确切范围**（四类判定 + 空集 + 缺格）；
2. 若新保证覆盖全部四类，则文档表述改为「按 identity/rewrite/deviation/missing 四类分类：任何非 identity 或缺失都不报 closed」；
3. **不要直接编辑 `demo/signoff-gap-close-16.json`**（那是所有者签收时的原文）。新增 `demo/signoff-gap-close-16-amendment-1.json`，写明：原签收文案的技术表述在 R1S 修复前不成立、修复后的确切保证、修正时间；并在 `report.md` 与 handoff `open_items` 引用该 amendment；
4. 若修正后的保证与所有者签收时理解的语义有实质差异，**停下来问所有者**，不得自签 amendment。

## N1 — UTC 标签错误（时间戳必须真实）

- `demo/signoff-gap-close-16.json:6`：`decided_at_utc = 2026-10-24T11:22:08Z`，但记录落盘发生在 10:24Z 左右（本地 11:22 BST 被误标为 UTC）。正确 UTC 应为 `10:22:08Z`。
- `tests.json:16,24,44,52`：同类误标（本地 +01 写成 `_utc`）。
- **要求**：以上字段改为真实 UTC；`_local` 与 `_utc` 两套字段都保留时须相互换算一致（差 1 小时）。

## N2 — 红相计数自相矛盾

`tests.json:65` 记「13 failed / 4 passed」，与 `report.md:29`、测试文件实际数量不一致，且**无 RED 日志/命令产物**。

**要求**：给出可复跑的 RED 命令 + 输出日志（`docs/handoff/.../logs/red-phase.log`），`tests.json` 与 report 数字统一为日志实测值。

## N6 — 文档残留旧结构

`docs/interface-proposals.md:71,91` 仍用 `known_gaps["ui_rewrites_basis"]` 字典下标语法，而 `known_gaps` 现为 `list[dict]`。**要求**：改为按 `gap` 字段查找的写法（或注明这是提议文档的历史语法）。

## N7/N8 — 可复核性脚注（不阻塞，但要在 report 说清）

- **N7**：`cli_chain.log` / `unittest.log` 的 artifacts hash 是 CRLF 工作树字节，与 committed blob 不同（11491 vs 11524、24329 vs 24533，因 `core.autocrlf=true` 且无 `.gitattributes`）。**要求**：report 注明该口径（沿用上一包先例），或加 `.gitattributes` 统一换行（若加，须重算全部 artifacts）。
- **N8**：`handoff.json` 的 `temporary_roots.created=true` 与 `cleanup.json` 的 `existed_before_run=true` 互相矛盾；`report.md:27` 的「G1 主控核对」与 `.tmp/gen_meta16.py` 删除均无产物。**要求**：字段改为一致（真实值），G1 若无产物则改写为「设计确认：主控以卡 §2 结构为准（无独立产物）」或补产物。

## 复验清单（R1 + R1S 一起）

1. `pytest tests -q` / `unittest discover -s tests` 全绿，数字如实（预期 171 → 171+新增）；
2. 逐条给出四类判定的单元测试名（identity/rewrite/deviation/missing）+ 空集 + 畸形；
3. 8 步 CLI 链 + parity 对准 `0f3dc3e`，输出与修复前除新增字段外一致（closed 结论不变）；
4. 主控 CLI `--verify-references` exit 0；
5. report.md 新增「R1S 整改记录」，逐条对应 B2/N3/N4/B3/N1/N2/N6/N7/N8；
6. 元数据纪律不变（payload commit 真值、metadata 另记、hash 磁盘实算）。
