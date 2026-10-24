# UI-APPLIC-BRIDGE-15 整改要求（R1）— 交接元数据三处表述修正（代码级零问题）

- 包 ID：UI-APPLIC-BRIDGE-15
- 交付：UI 仓 HEAD `0f3dc3e`，payload commit `0474683`
- 独立对抗审查结论：**APPROVED WITH NOTES**（代码级 10 项全过；红线、AC-01..08、118 测试、34/34 artifacts hash 实算全对）
- 性质：**仅元数据/表述修正**，不改 adapters/src/tests 任何代码，不需要重跑演示或测试
- 复验后即可 G7 收口

## 已确认无需动的部分（独立审查 + 总控双核）

- AC-01/02 basis 采纳、AC-03 显式 not_evaluated、AC-05/06 decided_confidence、AC-04/06 向后兼容字节锁：全部 PASS（含 `IQS_UI_EXPORT_JSON` 全量 10272 格灌入 6 项实跑通过）
- G2 三项所有者裁定与 G5 签收：记录格式、原话、时间戳、"agent 未自签"声明全部合规
- 红线：跨仓零写入（38 个变更路径全在 UI 仓内）、三布尔 false、`production_ready=false` 保持
- parity 证据值本身：`state_consistent=true`、`state_mismatch_count=0`、`ui_repo_writes=0`、10272 格 basis 全部 X→X 同值映射
- known_gaps 拆分诚实（`ui_rewrites_basis` 关闭条件已具备 / `not_evaluated_absent` 未完全具备）
- TDD 红相真实（基线 60 failures + 11 errors）

## 修正项（R1，元数据-only）

### R1-A（N2）「parity 对准最终 HEAD」表述不实 —— 必修

`handoff.json:248`、`report.md:40`、提交 `0f3dc3e` 的信息均称「运行 3 对准最终/交付 HEAD」，但 `logs/parity_check.log:13` 的 `--ui-commit` 实为 **`61c141524f7b…`**（G6 交接套件提交），不是 `0f3dc3e`。

实质风险已被缓解（`git diff 61c1415 0f3dc3e` 仅 artifacts.json/parity_check.log/report.md 三个文档，parity 所导入的 adapters 代码逐字节相同），但**声明必须与证据一致**。

**要求**：把三处表述改为事实：「运行 3 对准 `61c1415`；`61c1415..0f3dc3e` 仅文档（diff 留证），parity 所需代码与 `0f3dc3e` 等同」。

### R1-B（N1）parity 运行链表述 —— 必修

套件内不存在「运行 1」（`parity_check.log` 只有运行 2 与运行 3；`git grep "运行 1"` 无命中），但交接叙述暗示 run-1/2/3 完整链。

**要求**：修正为实际链（运行 2 @ `a80658b`、运行 3 @ `61c1415`），并注明「运行 1 未留存/未执行」的事实（哪一种就写哪一种）。

### R1-C（N4）红相计数遗漏 errors —— 必修

`handoff.json:175-177` 与 `tests.json:24-27` 记 `failed=60, skipped=0`，但 `logs/unittest-red.log` 尾部为 `FAILED (failures=60, errors=11)` —— **11 个 errors 未进结构化元数据**（仅 artifacts.json 的 role 文字提及）。

**要求**：结构化记录补齐 errors=11（红相=60 failures + 11 errors），两处一致。

### R1-D（N3）result_commit 与最终 HEAD 的外部绑定 —— 二选一

`handoff.json:11` 的 `result_commit=0474683`，而 `61c1415`/`0f3dc3e` 为其后的交接元数据提交。按 handoff-rules「result_commit 是 payload commit，metadata 提交的 HEAD 由总控验收报告外部绑定」，当前形态**合规**（总控验收报告将绑定 `0f3dc3e`）；但 APPLIC-RESOLVE-14 先例（d75182c「record true result_commit … per handoff rules sec.7」）更完整。

**要求（二选一）**：
- A（推荐，与先例一致）：出一个纯元数据追加提交，把「最终交接 HEAD」外部记录进 handoff 侧（如 report.md 的交接元数据表）；或
- B：在 `report.md` 明确写「result_commit 语义为 payload commit；最终 HEAD 由总控验收报告外部绑定」，由总控在验收档案里绑定。

## 可选改进（不阻塞）

- **N5** `test_ac01_ac02_exemplars_present` 名称含 AC-02 但只验 AC-01 样例（真实导出 not_applicable=0，AC-02 仅 synthetic 单测覆盖）—— 要么改名，要么在合成导出上补 AC-02 样例断言。
- **N6** `test_legacy_cell_rendering_unchanged` 用 assertIn/IsNone 成员断言，弱于「渲染不得变化」红线的严格字节要求（`test_applicability_confidence.py:55-89` 的 JSON 字节锁是严格版）—— 建议对 9ab7a33 渲染输出补黄金字节比对。
- **N7** `handoff.json:246` 声称「独立只读 reviewer 复核 approved」，但套件内无该审查产物（报告未随包）—— 要么附上报告，要么注明其留存位置/会话出处，避免无佐证声明。

## 复验要求

1. 修正后 worktree clean、正常提交（不混入代码改动）；
2. 重跑 `python -B -X utf8 -m unittest discover -s tests`（118 OK / skipped=6）贴输出；
3. 重跑主控 CLI：

```
python scripts\parallel_handoff_cli.py --input <UI仓>\docs\handoff\UI-APPLIC-BRIDGE-15\handoff.json --package-id UI-APPLIC-BRIDGE-15 --catalog docs/implementation/parallel-lanes/packages/2026-10-23/manifest.json --verify-references
```

要求 exit 0；
4. 修正仅限 `docs/handoff/UI-APPLIC-BRIDGE-15/` 元数据（及 R1-D 选项 A 的等价位置）。

## 边界

- 不重开 G2/G5（所有者裁定与签收有效，改动不触及渲染语义）
- 不改 applic 仓、主仓；`production_ready=false`、`financial_qualification_granted=false` 不变
- 包级门 S01/S04/S05/S06/U01–U04 不由本包关闭
