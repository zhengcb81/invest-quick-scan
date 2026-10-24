# PIPELINE-AUDIT-17｜快照判定 × 组装 profile 的管线一致性审计

- 批次：`2026-10-24`
- 写范围（唯一）：本主仓 `invest-quick-scan`（工具 + 报告；两 lab 仓只读）
- 性质：**审计卡，不是实现卡** —— 产出差异清单与管线建议，不改判定语义
- 交接协议：`docs/implementation/parallel-lanes/handoff.schema.json#1.0.0`

## 1. 背景（实测发现）

把已验收的 applic 快照（10272 格四态）与 CATL 实跑用的组装 manifest 交叉核对，发现**两侧从未对齐过**：

| 侧 | CATL 的模块判定 |
|---|---|
| 组装 manifest（实跑 38 题用） | common / operating / **auto** / **industrial** / mature（5 模块，手工 profile） |
| applic 快照（机器判定） | common / operating / auto / mature / **cross_border** / **dupont** / **porter** / **scaling**（8 模块） |
| 交集之外 | `industrial` 快照=**unknown**（谓词判假：industry=[auto] 不满足 in[industrial]，反证 assumed）；`cross_border/scaling/dupont/porter` 快照=applicable 但组装**未选** |

两条已知成因（先记下，不预判责任）：

- 组装器的行业轴语义是「选至多 2 个行业模块」，CATL 手工 profile 把 auto+industrial 都放进了 `industry_modules`，而快照谓词对 industrial 判假（CATL 的行业标签只有 auto）；
- 快照对 dupont/porter 是所有者裁定恒适用（D-AR14-DIAG-01/02），组装器没有这两个模块的等价通道（诊断模块在 profile 里靠 `diagnostic_modules` 手工开）。

## 2. 必做交付（缺一不可）

| # | 交付物 | 位置 |
|---|---|---|
| A1 | 审计工具 `scripts/applic_pipeline_check.py`：输入 = 组装 manifest 路径 + 快照路径，输出 = 逐模块交叉表（composed vs snapshot state/basis）+ 差异分类（一致 / 快照选而组装未选 / 组装选而快照非 applicable / 两侧 ID 未对齐）+ 退出码（全一致=0，有差异=2，数据错=3） | `scripts/` |
| A2 | 214 家全量对账：用 roster 的真实组装（如无可复用 profile 则如实报告覆盖数），不局限于 CATL 单例 | 报告 |
| A3 | 差异归因报告 `PIPELINE-AUDIT-17-report.md`：逐条差异 → 根因分类（轴语义差 / 所有者裁定通道缺 / 手工 profile 错 / 快照谓词错）+ 每条的管线建议（改组装 / 改谓词 / 加映射 / 记录为已知偏差） | 交接套件 |
| A4 | 测试：合成 manifest×快照夹具覆盖四类差异 + 全一致正例；不依赖 lab 仓数据 | `tests/test_applic_pipeline_check.py` |

## 3. 红线

1. 两 lab 仓零写入；本卡只产审计工具、报告与测试。
2. **不改任何判定语义**：组装器、谓词、快照一概不动；报告里的建议是建议，落地另卡。
3. 差异报告**先分类后结论**：每条差异必须给根因类与证据（快照 basis.reason / manifest profile 字段 / 轴语义文档引用），不许只写「不一致」。
4. 所有 sha256 磁盘实算；报告中的每个数字可由工具复跑重现。
5. 测试模板不填假通过。

## 4. 门禁

- **G0**：核锁（快照 `applicsnap_d296902c…` sha、CATL manifest sha、roster sha）。
- **G1**：工具设计（交叉表字段、差异四分类定义）经主控确认。
- **G2**：**无所有者新裁定项**；若归因中发现语义级问题（如「工业轴 vs 行业轴」的架构分歧），停下来问所有者，不得自定。
- **G3**：TDD 实现工具 + 测试。
- **G4**：跑 CATL 单例 + 214 家全量对账，产出报告。
- **G5**：所有者过目报告（原话签收）。
- **G6**：交接套件 + 主控 CLI `--verify-references` exit 0。

## 5. 验收用例

| ID | 用例 | 期望 |
|---|---|---|
| AC-01 | CATL 实跑 manifest × 快照 | 交叉表如实列出 8 applicable/5 composed 差异（industrial unknown、cross_border/scaling/dupont/porter 未选），退出码 2 |
| AC-02 | 合成夹具：全一致 | 退出码 0，零差异 |
| AC-03 | 合成夹具：四类差异各一 | 分类正确、退出码 2 |
| AC-04 | ID 未对齐（一侧有他侧无的模块 id） | 报「未对齐」类，不算判定差异 |
| AC-05 | 214 家全量 | 每家给出 composed∩snapshot 一致数与差异数；无可复用 profile 的家数如实报 0 覆盖 |
| AC-06 | 数据错（坏 JSON/缺 entity_id） | 退出码 3 + 具体路径 |

## 6. 非目标

- 不改组装器/谓词/快照；不做「修复」—— 差异的任何修复都另立卡
- 不建「快照驱动组装」的新管线（本卡只审计，架构决策归所有者）
- 不关闭包级门；`production_ready=false` 不变

## 7. 风险

1. **R1** roster 的 214 家可能没有可复用的组装 profile（现组装流程按需手做）—— A2 如实报告覆盖数即可，不硬凑。
2. **R2** 模块 ID 两侧语义同名不同义（如 industrial 行业轴 vs 谓词标签）—— 这正是要审的差异，归因报告的核心产出。
3. **R3** 快照谓词与组装器的轴定义演进不同步（谓词 pred_6ffa4a71 vs 组装器模板 3.2.0）—— 报告须记录两侧版本并注明时效。

## 8. 参考

- 交叉核对实测：本卡开卡前已跑（8/5 差异如 §1 表）
- `runs/thin-bank-catl-full-2026-10-22/composed/manifest.json`（profile 字段）
- applic 快照 `applicsnap_d296902c…`（cells[].state/basis）
- `docs/modular-question-bank-design.md`（轴语义：行业至多 2、诊断手工开）
