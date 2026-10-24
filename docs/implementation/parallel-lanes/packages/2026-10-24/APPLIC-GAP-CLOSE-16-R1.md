# APPLIC-GAP-CLOSE-16 整改要求（R1）— `closed` 判定 fail-open：`identity_pairs` 未验证 X==X

- 包 ID：APPLIC-GAP-CLOSE-16
- 交付：applic 仓 HEAD `6b15c55`，payload `c4cad0a`
- 结论：**交付的数据结论正确（本轮 10272 格确实全部同值映射），但本包的核心交付物 —— 「closed 必须由证据门控」 —— 实现不成立。判 closed 的代码路径并不验证同值，存在 fail-open。**
- 性质：`src/applic/parity_check.py` 一处判定逻辑 + 测试；不需要重跑快照/导出

## 缺陷（总控已复现）

`src/applic/parity_check.py:52-97` 的 `_ui_rewrites_basis_entry`：

```python
rewrite_pairs = {
    pair: count for pair, count in sorted(basis_gaps.items())
    if pair.endswith(f" -> {UI_BASIS_BELOW}") or pair.endswith(f" -> {UI_BASIS_MATCHED}")
}
identity_pairs = {
    pair: count for pair, count in basis_gaps.items() if pair not in rewrite_pairs
}
```

`identity_pairs` 的定义是「**不是改写对的都算同值**」，而不是「左侧 == 右侧」。任何不以那两个已知目标字符串结尾的**非同值**映射都会被静默计入「同值」，`rewrite_pairs` 为空 ⇒ 判 `closed`。

与它自己的 docstring 矛盾：

> 唯一合法依据：本轮 basis_gaps 实测。全部 ``X -> X`` 同值映射且改写对……计数 0 ⇒ closed

也违反卡 §3 红线 3：

> `ui_rewrites_basis` 判 closed 的**唯一合法依据**是本轮 basis_gaps 全同值 + 改写对计数 0 —— 不许只改文案。

### 复现（总控实测，无需改文件）

```python
from applic.parity_check import _ui_rewrites_basis_entry

fake = {
    "predicate_true -> predicate_true": 1200,
    "predicate_true -> synthetic_fixture": 4,                      # 非同值，且不属于两个已知改写目标
    "attribute_unresolved -> no_route_decision_in_source": 2,      # 非同值，同上
}
entry = _ui_rewrites_basis_entry(fake)
# 实测输出：closed_or_transitional == "closed"   ← 应为 open
```

现实风险：UI resolver 的兜底路径除两个已知目标外还能产出 `synthetic_fixture`；未来 BRIDGE-15 建议 1 若被回退或改用其它兜底值，本工具会把「改写」报成「同值」，gap 显示 `closed`。**这正是本卡要消灭的「文案声称与证据脱节」，只是换了一种形式。**

### 当前交付的真实状况（对数据的判断不变）

本轮 parity 的 5 组映射逐条检查确为同值：

```
attribute_unresolved -> attribute_unresolved        17
common_always_applicable -> common_always_applicable 214
negative_evidence_not_verified -> negative_evidence_not_verified 8409
owner_ruled_always_applicable -> owner_ruled_always_applicable  428
predicate_true -> predicate_true                  1204
```

合计 10272 —— 所以 `closed` 这个**结论**对；错的是**得出它的代码不验证前提**。修复后结论应不变。

## 修正要求

1. **逐对验证同值**：对每个 `basis_gaps` 条目，按 `" -> "` 拆分左右两侧（注意 basis 名内不含该分隔符；若出现无法拆分或多次出现的条目，按数据错误处理），`left.strip() == right.strip()` 才算同值。
2. **任何非同值映射必须使判定为 `open`**，不论其目标是否是那两个已知字符串；输出中列出全部非同值对（建议称 `deviation_pairs`，保留 `rewrite_pairs` 作为其中「指向两个已知改写目标」的子集，便于既有消费者过渡）。
3. **closed 分支的证据必须可核**：至少包含 `identity_verified: true`、`identity_pairs`（逐条）、`pairs_total`，且 `sum(identity_pairs.values()) == pairs_total`；若存在 `deviation_pairs` 则不允许进入 closed 分支。
4. **测试补齐四类**（缺一不可）：
   - 全部同值 → `closed`；
   - 两个已知改写目标之一 → `open` 且列出；
   - **未知目标非同值（如 `-> synthetic_fixture`）→ `open`**（本缺陷的回归锁）；
   - 混合（同值 + 未知目标非同值）→ `open`。
   现有 stub 测试若只覆盖了前两类，须补后两类。
5. 修完重跑 8 步 CLI 链 + 171 测试（新增后总数如实报），parity 仍对准 UI `0f3dc3e`；输出与修复前**除新增字段外**应一致（closed 结论不变）。
6. **元数据纪律**：result_commit 写 payload 真值、metadata 提交另记（本包 `ba2249b` 的做法正确，沿用）；artifacts hash 磁盘实算。

## 复验

```
python -B -X utf8 -m pytest tests -q          # 全绿，数字如实
python -B -X utf8 -m unittest discover -s tests
# 8 步链 + parity（--ui-commit 0f3dc3e…）
python scripts\parallel_handoff_cli.py --input <lab>\docs\handoff\APPLIC-GAP-CLOSE-16\handoff.json --package-id APPLIC-GAP-CLOSE-16 --catalog docs/implementation/parallel-lanes/packages/2026-10-24/manifest.json --verify-references
```
要求 CLI exit 0。

## 边界

- 不重开 G2/G5 的语义裁定（`closed` 的**定义**不变，只修**判定方式**）
- 不改快照、导出、谓词；不改 UI 仓
- 本包仍未关闭 S01/S04/S05/S06/U01–U04 门；`production_ready=false` 不变
