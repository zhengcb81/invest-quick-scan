# RELEASE-DIFF-10：模块版本变化与历史兼容性诊断

唯一写根 **C:/Users/郑曾波/Projects/iqs-release-diff-lab**；branch `codex/release-diff-10`；module `iqs_release_diff`。先读 [共同契约](integration-contract.md)、[输入清单](input-catalog.json) 的本包段。不修改原模块、module_contract、生产路由或历史观察。

## 要解决的问题和真正边界

用户要求模块可组合、可独立升级并与旧扫描结果共存。原 `module_contract` 已定义不可变问题、墓碑和继承规则；本包复用它，而不是另造发布器。交付一个可解释“两个已冻结 release 到底变了什么、哪些历史题目需要保持不同口径”的离线差异工具，以及能供总控接线测试的回归集。

不声称新旧分数可直接比较；只报告结构变化及风险理由，不生成权重/路由、迁移 DB、更新 current.json、批准新版本或把 semantic hash 一致等同金融意义一致。与 ROUTE-COVER/SCORE-ANCHOR 的行业适用与评分锚点内容工作不同。

## 输入、API 与输出

输入 `iqs.release_diff_request/1.0.0` 闭合字段：`protocol,before_ref,after_ref,requested_modules`。两个 ref 为 ArtifactRef，指向锁定 release；requested_modules 是唯一 module_id 数组，空数组表示完整 release。两 release 的全部 artifact_ref 闭包必须已在本包锁中；禁止请求工作树 latest。合成变体以独立 synthetic fixture 明确标注，使用原 `seal_release`/原 validator 构造，不偷改旧 baseline。

```python
def compare_releases(request: dict, *, input_root: Path, source_root: Path, lock: dict) -> dict: ...
def evaluate_cases(casebook: dict, *, input_root: Path, source_root: Path, lock: dict) -> dict: ...
```

CLI：`python -B -X utf8 -m iqs_release_diff compare --input request.json --input-root vendor/iqs --source-root vendor/iqs --lock inputs.lock.json --output runs/diff-01`。另提供共同 validate/evaluate、version/help。

结果 `iqs.release_diff_report/1.0.0` 使用共同 result 顶层。payload 闭合字段：`before_release_id,after_release_id,source_validation,release_field_changes,routing_policy_changes,module_changes,question_changes,format_resource_changes,counts,compatibility_limits`。

- source_validation 两侧各闭合为 `side,release_id,validator_ref,passed,error`；error nullable。必须实际调用锁定 `module_contract.validate_release`，原加载器只读包内锁定 artifacts；`validate_upgrade` 使用原名称/签名，不能用自己 hash 比较替代调用。源拒绝时报告 exact error，本包不得强行生成“兼容通过”。
- release_field_changes 必须覆盖 schema_version/catalog_version/renderer_version/router_version/retired_question_ids/routing_policy_ref/routing_policy_sha256 这七个字段，每个恰一行，不能因为 module 内容都相同而省略 release 变化。每行闭合 `field,before_present,after_present,before_value,after_value,change_kind,risk_codes`，change_kind=unchanged|added|removed|changed；missing 与 JSON null 用 presence 布尔区分。risk_codes 增加 release_schema_changed/renderer_changed/router_changed/routing_policy_changed/retirement_list_changed/catalog_metadata_changed；字段未变也按 unchanged 保留分母。
- routing_policy_changes 闭合 `before_policy_ref,after_policy_ref,before_presence,after_presence,raw_hash_verified,validation_scope,field_changes,limitations`。两个 policy_ref 为 ArtifactRef 或 null；presence=not_declared|present；1.0 release 无 policy 字段是合法 not_declared，不猜默认策略。存在声明的 policy 文件必须在来源锁内，raw hash 必须等于 release.routing_policy_sha256，缺文件/hash错/重复JSON键拒绝整个请求，不能报告 unchanged。validation_scope 固定 raw_hash_and_json_structure_only；本包不认证政策行为。field_changes 按安全 JSON pointer 对两个 JSON 树作确定性逐叶结构差异，行字段同 release_field_changes（field=pointer）；非空数组保留原顺序、不做语义相同合并。若政策整体新增/移除，根 pointer 的 added/removed 明确保留；双方 not_declared 时为空。政策的 materiality/rules 等实际变动必须能看到，但不执行路由或授比较资格。原仓此 commit 没有独立 routing-policy schema；不编一个官方 schema，不让 route-decision schema 代替 policy 验证。
- module_changes 每条 `module_id,before_version,after_version,change_kind,field_changes,upgrade_validation`。change_kind=unchanged|added|removed|changed；field_changes 为安全 JSON pointer、before/after 原值和规则 ID；upgrade_validation=passed|rejected|not_applicable，理由保留。新旧无公共模块不能假装升级验证已通过。
- question_changes 每条 `module_id,question_id,change_kind,before_definition_sha256,after_definition_sha256,successor_ids,retirement_state,risk_codes,source_pointers`。change_kind=unchanged|added|removed|changed_same_id；risk_codes 为固定版本化 enum，至少 reused_retired_id/changed_same_id/metric_changed/scope_changed/rubric_changed/activation_changed/format_resource_changed/unknown_field_semantics。不能将这些 risk 自动变成“允许比较”。
- format_resource_changes 每条 `resource_path,before_sha256,after_sha256,change_kind,affected_question_ids,coverage`；coverage=exact|conservative_all|unresolved。对于不在 release 内提供的格式资源，保留 unresolved，不扫描源树猜依赖。counts 明确 before/after 全部分母、请求子集及各类数，不只报变动题。compatibility_limits 固定含 `historical_observations_rewritten=false,comparison_authority=false,routing_authority=false`。

JSON 只记录实际存在的原字段，字段缺失用 nullable/明确缺失状态，不补版本或 successor。使用原 canonical/digest/question definition 规则；本包仅组合诊断。未知源 schema 保持 unsupported。输出排序固定按 module_id/question_id/规则 ID，报告运行时间等元信息不能进入可复算业务 payload。

## 实施与主要测试

1. 冻结输入，建立自己的 PWF/README，记录 native API/加载路径和完整 artifact 依赖。先用现有三个 release 的任意两个完成原 validator 校准，再写差异 RED。无另一包依赖。
2. 做全部题、模块、release字段、政策和格式资源的分母/对照；同一 release 自比较应原样 unchanged，反向比较不能丢墓碑风险。真实三份 release 的48个模块内容相同，但 1.0/schema1/router1 → 2.0/schema2/router2.0 的政策引入，以及 router2.0→2.1/政策hash和规则变化，都必须在 release_field_changes/routing_policy_changes 中出现；不能只报告“题目未变”。
3. 最少 18 对有因果区别的案例：纯相同；新增行业模块；common 核心不可更改；原题原封新增题；同 ID 改题面；同 ID 改锚点/metric/scope/rubric；新增 successor 并正确累计墓碑；复用退休 ID；删题无 successor；改变 applies_when；activation/dependency/conflict 变化；元数据版本号变化但内容相同；hash 与原文不匹配；锁外 artifact；format resource 改动但题面未变；可选模块子集+完整分母；未知 schema；新旧方向反转。
4. 集成：spy 证明原 `validate_release` 和适用时原 upgrade validator 实际被调用，返回拒绝不被吞；使用三份真实已发布 release 原始 Git blobs 及其两个 routing_policy_ref 原件，至少完整做 schema1→schema2/router2.0、router2.0→2.1 和各自反向比较，断言上述实际变化及七字段分母。另做缺policy、policy hash错和仅policy变化的反例。仅作软件格式/历史差异，不是金融真实样本。
5. E2E：完整公开 compare→validate→evaluate，中文空格路径和随机 cwd，修改 artifact/hash/重复键必须失败且没有正式成功输出；所有源与历史 fixture bytes 保持。全部离线，无生产 DB。

交 `content/casebook.json`（case_id/request_ref/expected_ref/rationale/source_rule_refs）、版本化闭合 schemas、工具、实际测试日志、原源 validator 复用证据、`integration-map.md` 和共同完整交接。expected 不由运行被测工具反向生成；独立 reviewer 必须审查规则边界并编写未见反例。总控消费为升级评审/回归候选，不修改模块生产发布流程。
