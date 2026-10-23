# APPLIC-RESOLVE-14 整改要求（R1）— 交接元数据三处事实性错误

- 包 ID：APPLIC-RESOLVE-14
- 交付快照：`2ee2a4e`（HEAD）
- 独立审查：`review/independent-review.md`（round 2, approved）之后的**总控复核**
- 结论：**数据与引擎通过；handoff.json 元数据必须修正后才可验收**
- 影响面：仅 `docs/handoff/APPLIC-RESOLVE-14/` 元数据；`data/`、`src/`、`schemas/`、`tests/` 不受影响，无需重跑

## 总控已独立复现的三处错误

### D1 — `result_commit` 不是 Git 对象

- 现状：`handoff.json` 的 `snapshot.result_commit = c59515757e0cf6d0d22e8fdd5e83ee39a80c0e7c`
- 复现：`git cat-file -t c59515757e0cf6d0d22e8fdd5e83ee39a80c0e7c` → `fatal: could not get object info`
- 真实值：该短前缀对应 `c595157b4bd49503374e119d5b63927d5aa6599c`（`signoff(G5)` 提交）；当前 HEAD 为 `2ee2a4ea567a3afca8f1daf58b0c198920c978ec`
- 判断：40 位十六进制中前 7 位正确、其余为转录损坏。CLI 之所以放行，是因为 schema 只要求 `minLength: 7`
- 同类问题：`summary.md:5` 重复了同一错误前缀

### D2 — `changed_paths` 含 12 条从未存在的路径

- 现状：`scope.changed_paths` 共 91 条，其中 12 条在磁盘与 Git 历史中均不存在：

```
review/logs-round2/a1-lock-failure-path.log
review/logs-round2/a2-predicates-verbatim.log
review/logs-round2/a3-attributes-idempotent.log
review/logs-round2/a5-snapshot-idempotence.log
review/logs-round2/a6-invalidation-rerun.log
review/logs-round2/a7-export-parity.log
review/logs-round2/a8-unittest-rerun.log
review/logs-round2/a9-network-ast.log
review/logs-round2/append-only-scenarios.log
review/logs-round2/chunk02b-bijection-check.log
review/logs-round2/chunk02b-five-company-manual.log
review/logs-round2/chunk02b-symmetry-diff.log
```

- 实际 `review/logs-round2/` 只有 11 个文件，名称完全不同：

```
chunk02b-permutation-verify.log      invalidation-recompute.log
chunk02b-rationale-coherence.log     network-path-scan.log
chunk02b-state-diff-58.log           rest13-manual-dump.log
cli-chain-rerun.log                  snapshot-oldnew-diff.log
distribution-recompute.log           unittest-rerun.log
                                     validate-scenarios-b.log
```

- 矛盾点：`artifacts.json` **正确**只列了真实存在的 11 个，因此两份文件互相冲突
- 要求：`changed_paths` 必须只列真实存在且已提交的路径，与 `artifacts.json` 保持一致

### D3 — UI 接口 `content_hash` 转录损坏

- 现状：`interfaces[ui_applicability_resolver_shape].content_hash = d15d0a810daec45217a28d3ec6b02c927fe13d6faa4f0686315c9f3061a27b20`
- 真实值：`C:\Users\郑曾波\Projects\iqs-question-bank-ui-lab\adapters\contracts.py` 的 sha256 = `d15d0a810daec45217a286d3ec6b02c927fe13d6faa4f068631c9f306a278b20`
- 判断：前 21 个十六进制字符相同，之后分叉 —— 同样是转录损坏，不是另一个工件
- 备注：`adapters/applicability_resolver.py` 的 sha256 为 `373c5571db2a3ea4d8caccdcbddcb5bcc2912659ea31785abce6d2c4966d8e9c`；若该 interface 指向 resolver 而非 contracts，请改用此值并说明指向哪个文件

## 非阻塞项（建议一并修正，不强制）

- **N1** `verification.checks` 与 `tests.json` 的 `command` 是占位符（`…` / 「（8 步，详见日志）」），不符合交接规则第五节「checks 真实命令与结果」。`cli-chain-rerun.log` 确有 8 行 `exit=0`，请把真实命令链写入
- **N2** `src/applic/parity_check.py:199` 把 `ui_repo_writes: 0` 写成硬编码字面量，不是实测值；建议改为实际比对 UI 仓 `git status`
- **N3** AC-07「未映射模块保持 not_evaluated」在真实数据上不可测（48 模块全部有规则，`not_evaluated=0`），仅 fixtures 覆盖；`status-distribution.md:20` 已披露，建议在验收表注明该条为 fixture-only
- **N4** G2-4 的「ttl 默认 180 天」未实现（schema 强制显式 `ttl_days`）；建议要么实现默认值，要么在 signoff 的已知局限中列出
- **N5** `interfaces[module_release_locks].content_hash` 只对应 4 个 lock 中的第 1 个，但 `version` 写「4 locks」；建议改为 4 个 hash 的清单或聚合值并说明算法
- **N6** `demo/ui-export` 是单文件，但 `scripts/export_ui.py:25` 默认路径与 `docs/interface-proposals.md:8` 指向 `demo/ui-export/applicability_export.json`；请统一
- **N7** `tests/test_export_ui.py:3` 明确不导入 UI 仓，字段对齐是对手写模拟的断言；真实互操作只由 `parity_check` CLI 覆盖。建议在测试文件注明该边界

## 复验要求

1. 修正后重新提交，`git status` 必须 clean；
2. `handoff.json` 的 `snapshot.result_commit` 必须是 `git cat-file -t` 可解析的真实提交；
3. `changed_paths` 每条都必须能 `Test-Path` 通过，且与 `artifacts.json` 的集合一致；
4. `interfaces[*].content_hash` 每个都必须能对到某个真实文件的 sha256，并在 `report.md` 写明指向哪个文件；
5. 重跑 `python scripts\parallel_handoff_cli.py --input <lab>\docs\handoff\APPLIC-RESOLVE-14\handoff.json --package-id APPLIC-RESOLVE-14 --catalog docs/implementation/parallel-lanes/packages/2026-10-21/manifest.json`，要求 exit 0；
6. 在 `report.md` 追加一节「R1 整改记录」，逐条对应 D1/D2/D3 与已处理的 N 项。

## 总控已确认无需重做的部分

以下由总控独立复现，**不需要重跑**：

- 10272 格 = 214 × 48，applicable 1846 / unknown 8426 / not_applicable 0 / not_evaluated 0
- `pytest tests -q` → 158 passed + 219 subtests
- `tools/validate_bank.py`（本包为 `scripts/validate.py`）→ exit 0
- 快照内存重建两次均逐字节一致
- 失效精确性：21 格变动 / 2 次状态翻转 / 目标实体外 0 变动
- G2-3 强制路径（`src/applic/model.py:355-386`）与三值逻辑（`:195-208`）
- UI parity 实跑：`state_consistent=true`、0 不一致、UI 仓 HEAD 与 status 未变

## 边界

本整改**不关闭** S06/W15 包级门，不改变 `production_ready=false` / `financial_qualification_granted=false`。仅修正交接元数据的事实准确性。
