# G0 第三轮独立复审报告

- reviewer: `/root/g0_independent_review`
- review_date: `2026-09-23`
- reviewed_candidate: `docs/implementation/reviews/G0/candidate-snapshot.json`
- candidate_sha256: `3DE13B1596CEB1EEA0A9A66B46E957334DBE245DB094476C07527564A23C1EB3`
- review_packet: `docs/implementation/reviews/G0/third-review-packet.md`
- review_packet_sha256: `513CAF0AE0127BF15E4F1E59B19253FE6969ADBE512446E250022452FFBCB897`
- declared_scope_files: `145`
- decision: `verified`
- G0_release: `verified_for_local_contract_scope`

## 最终结论

第三轮冻结候选通过独立复审。RR-01 至 RR-04 全部关闭，首轮 G0-01 至 G0-09 最终均为 closed。候选 manifest 的声明范围与实际范围集合完全相等，145 个文件逐一重算 hash 均匹配；全量测试与计划校验独立通过。

本结论只放行 G0 的本仓离线契约、schema、reference helper、计划和审查证据。它不表示外部 owner 项目的生产实现、真实数据库事务、并发调度、联网模型、UI 或跨仓端到端流程已经通过。新增 `E2E-06` 仍是 live 规格且保持 `specified_not_executed`，本地测试没有被登记成真实 E2E 结果。

## 独立执行结果

| 检查 | 原始结果 | 结论 |
|---|---|---|
| 候选文件 SHA-256 | `3DE13B1596CEB1EEA0A9A66B46E957334DBE245DB094476C07527564A23C1EB3` | 与委托值一致 |
| `python -X utf8 scripts/g0_candidate_manifest.py verify` | `{"scope_files": 145, "errors": []}` | 集合等值且全部 hash 匹配 |
| `python -X utf8 -m pytest -q -p no:cacheprovider` | `184 passed, 108 subtests passed in 83.31s`，退出码 0 | 通过 |
| `python -X utf8 scripts/implementation_plan.py validate` | `planning_valid=true`，73 tasks，172 acceptance cases，final gate G6，`product_tests_executed=false` | 通过且未冒充产品测试 |
| RR-01 至 RR-04 独立恶意输入 | 22 个检查，`FAILURES 0` | 全部符合预期 |
| 测试后再次验证 manifest | `scope_files=145, errors=[]` | 审查期间冻结字节未漂移 |

## RR-01 至 RR-04 裁决

### RR-01 — Closed — 可信检查回执已形成对象与等级闭包

公共 `validate_parsed_answer` 现要求可信 receipt record，并绑定：

- receipt ID；
- entity ID；
- question ID；
- observation ID；
- 精确授权的 check level；
- 与等级对应的 issuer；
- active 状态；
- 规范化内容 SHA-256。

独立重放结果：合法同对象 receipt 通过；跨公司、跨题、跨 observation、低等级升级、revoked 和坏 hash 六种攻击均抛出 `ValueError`。RR-01 关闭。

### RR-02 — Closed — full readiness 已绑定同一 release 证据闭包

deployment schema 对 full readiness 要求 G0 至 G6 各一次及两个唯一 consumer；公共 `validate_readiness_response` 先做完整 schema 校验，再把 response/evidence/gate 的 release ID 和 manifest hash 与预期 ReleaseSet 交叉核对。

独立重放结果：合法完整证据通过；重复 gate、缺失 gate、顶层错误 release、gate 错误 release、顶层错误 manifest、gate 错误 manifest、重复 consumer 均被 `ValidationError` 或 `ValueError` 拒绝。RR-02 关闭。

### RR-03 — Closed — 规则 schema 与执行器语言一致

CompositeRule 的递归子节点只引用 CompositeRule，叶子必须使用 `condition` 包装，ScreeningPolicy 不能嵌入规则树。

独立重放结果：裸 threshold 子节点和嵌套 policy 均被 schema 拒绝；包含多层 `all/any/not/condition` 的合法规则通过校验，并由公共 `evaluate_rule` 返回 `pass`，没有形状崩溃。RR-03 关闭。

### RR-04 — Closed — 冻结候选覆盖完整声明范围

`g0_candidate_manifest.py` 从固定 scope patterns 枚举并排序文件，只排除 manifest 自身与本报告以避免自引用。候选类型为 `G0_frozen_for_independent_review`。

独立验证确认：

- 实际范围与 `artifact_hashes` 键集合相等，共 145 个文件；
- 145 个逐文件 hash 全部匹配；
- 人为删除一项会报告 `missing from manifest`；
- 人为增加范围外项会报告 `outside declared scope`；
- 人为修改一个 hash 会准确报告该文件 `hash mismatch`；
- work schema/helper、model-policy 实现与测试、全部 `test_*.py` 和三个 quick-scan example fixture 均已纳入范围。

RR-04 关闭。

## G0-01 至 G0-09 最终状态

| Finding | 最终状态 | 最终依据 |
|---|---|---|
| `G0-01` | `closed` | score/status 条件闭合；非模型等级必须由绑定实体、题目、观察、精确等级、issuer、状态和 hash 的可信 receipt 授权。 |
| `G0-02` | `closed` | entity/security、universe、work scope 与 profile/observation 的跨对象一致性由公共 validator 检查。 |
| `G0-03` | `closed` | C01-C03 调用公共实现；C05-C07 只声明 contract scope；生产 integration/fault cases 保持未执行。 |
| `G0-04` | `closed` | exchange v1.0.0 禁止非空 extension，正文嵌套逃逸被 schema 与公共 validator 拒绝。 |
| `G0-05` | `closed` | release schema-first；readiness 与同一 release/manifest、G0-G6 唯一 gate 和唯一 consumer 闭合。 |
| `G0-06` | `closed` | query status/coverage、scored lineage 和 profile entity 一致性已闭合。 |
| `G0-07` | `closed` | diagnostic 不能进入核心聚合；空规则、裸叶子与嵌套 policy 拒绝；合法多层树可执行。 |
| `G0-08` | `closed` | 来源链递归检查完整祖先、传递依赖、缺失祖先和环。 |
| `G0-09` | `closed` | issuer-index 外部事实已纠正；冻结 candidate 对声明范围做集合等值与逐文件 hash 绑定。 |

## E2E-06 核验

`docs/implementation/acceptance-cases.json` 中 `E2E-06` 的 `level` 为 `live`，`status` 为 `specified_not_executed`。它要求真实公共入口、真实少量公开数据、隔离 workspace/SQLite/下载交换目录、故障矩阵和严格清理验证。当前计划输出明确 `product_tests_executed=false`，本次 184 个本地测试不构成也未被标记为 E2E-06 通过。

## 放行意见

G0 可标记为 `verified` 并按计划进入后续实施 gate。后续 gate 必须继续保持本报告的范围边界：owner 项目的生产 case 和 E2E-06 只有在相应真实入口完成并保留原始证据后才能改为 executed/passed。

