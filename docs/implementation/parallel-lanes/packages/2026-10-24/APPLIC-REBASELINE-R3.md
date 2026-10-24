# APPLIC RE-BASELINE（R3 后）｜输入指纹更新与「零语义变化」取证

- 日期：2026-10-25
- 触发：R3 裁定（发布契约方案 B + 路由默认诊断）使主仓 `questions/routing-policy.v2.json`
  升 **2.4.0**、`questions/releases/current.json` 改指 v1 包 `pkg_ca11c5c3…`
- 性质：**输入指纹重钉 + 取证**。不改任何判定逻辑、不改任何模块文本

## 1. 问题

applic 侧上一把输入锁 `inputs.lock.rule-scope-19.json` 钉的是 policy `99130fb5…`（2.3.0）。
R3 后 policy 字节已变，旧锁 fail-closed 拒绝加载（设计如此）。若不重钉，任何新的
applic 重建都无法进行；若重钉而不留证，未来看到 snapshot_id 变化会误判为语义回归。

## 2. 处置

新建 `inputs.lock.rule-scope-19-r3.json`（**不修改旧锁**，append-only）：

| 文件 | 旧锁 | 新锁 | 变化 |
|---|---|---|---|
| `questions/catalog.json` | `3e145130…` | `3e145130…` | 不变 |
| `questions/routing-policy.v2.json` | `99130fb5…` | **`913380ce…`** | **变**（2.3.0 → 2.4.0） |
| `questions/releases/current.json` | `c4baa334…` | **`a17f2fcb…`** | **变**（改指 v1 包） |
| `roster-status.json` | `6aaa7257…` | `6aaa7257…` | 不变 |
| 四个 `modrel_*` 模块锁 | — | — | 全部不变 |

`verify_inputs` → **files_ok 8 / files_total 8，status ok**。

## 3. 取证：判定零变化

重跑 8 步链的前四步（verify_inputs / build_predicates / build_attributes / run_eval）：

| 产物 | 旧 | 新 | 结论 |
|---|---|---|---|
| `attributes_version` | `attr_897fecae…` | `attr_897fecae…` | **不变**（属性与输入无关） |
| `predicate_version` | `pred_6b258097…` | `pred_f4ecf4cc…` | 变（policy sha 进版本键，预期） |
| `snapshot_id` | `applicsnap_26f494e5…` | `applicsnap_3ed74894…` | 变（inputs 进内容寻址，预期） |
| `distribution` | 1846 / 0 / 0 / 8426 | 1846 / 0 / 0 / 8426 | **完全相同** |

**逐格比对（10272 格）**：

- 键集合完全相同（214 家 × 48 模块）
- **判定差异格数 = 0**（state + basis.kind + decided_confidence 三元组全等）
- basis 分布完全相同：`negative_evidence_not_verified` 8409 / `common_always_applicable` 642 /
  `predicate_true` 1204 / `attribute_unresolved` 17
- state 分布完全相同：`unknown` 8426 / `applicable` 1846

即：**新快照与旧快照在判定上逐格等价，差异仅限 `inputs.policy_sha256` 与
`inputs.predicate_version` 两个溯源字段**（以及由它们派生的 snapshot_id）。

## 4. 语义解释

`predicate_version` 变而判定不变，是因为 policy 2.4.0 的改动只在**路由侧**：
新增 `default_diagnostic` 谓词供路由驱动组装使用，未改变 48 条适用性谓词的求值结果。
CATL/industrial 的收窄（3.1.0 文本）早在上一轮快照已生效，本轮 policy 变更不触及它。

## 5. 边界

- 旧快照 `applicsnap_26f494e5…` 按不可变红线**保留**，未删除、未覆盖
- 旧输入锁 `inputs.lock.rule-scope-19.json` **保留**（历史包可比性）
- 未重跑 parity（UI 侧 basis 值未变，10272 格全同值，无需重跑）
- 未重跑 LLM 通道 shadow（通道判定与 policy 无关；如需可另跑）
