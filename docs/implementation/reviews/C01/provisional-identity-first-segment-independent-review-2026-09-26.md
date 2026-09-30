# C01 v2 临时身份第一段独立审查（2026-09-26）

结论：**暂不放行作为扫描准入门**。v1 只读入口、v2 显式状态/修订、临时身份的显式 `null`、单实体不能合并两挂牌，以及权威回执参数缺失时拒绝，都在现有单对象测试中成立；但来源绑定的真实归属和 verified 证券展示身份仍有可复现的绕过。审查只覆盖本仓契约第一段，不代表 W02 StockWiki 数据库或 Q06 派发已经实现。

## 发现

1. **[P1] 来源绑定字符串未向 owner 的来源记录反查，不能凭本验证器授予扫描资格。** `scripts/contract_validation.py:198-214` 把回执中的 `source_binding_ref` 与 Entity 中的同一个字符串比较，但仅要求 `source_namespace`、`source_record_id` 非空。将回执的 `source_record_id` 从 `0000000001` 改为 `SOME_OTHER_SOURCE_RECORD`、保持 `BND_SOURCE_1` 与其余字段不变，`validate_entity` 仍接受。再建第二个 Entity/证券/回执但同用 `BND_SOURCE_1`，两次单对象验证也都接受。前一反例是缺少真实 BND→来源键查证；后一反例的跨实体唯一性**只能由 StockWiki owner DB 的 UNIQUE/FK/事务检查或读取权威全量绑定的批量验证器**保证，不应错误地要求单对象函数凭空知道全库。C01 契约应规定“回执、source binding、当前来源记录”三方精确比对是 `eligible_provisional` 的必要条件，且在 W02 建成前不能把本函数的成功返回等同于可付费派发。补 owner 绑定查证与两个实体争用同一来源键的回归。

2. **[P2] `verified` 回执遗漏 ticker 和原始交易所，旧修订可被套到新的挂牌显示身份。** `scripts/contract_validation.py:247-256` 的 `expected_attributes` 没有 `ticker`、`exchange_raw`；`schemas/quick_scan/identity.schema.json:193-220` 要求这些字段，却未规定与核实回执/来源绑定的关系。保持 `identity_revision=2`、`source_binding_ref=BND_SOURCE_1` 和同一回执，分别把 ticker 改成 `UNRELATED` 或原始交易所改成 `BATS`，两次均接受。即使确为合法更名/转板，也应由 owner 的带版本来源绑定或连续性事件确认，不能在同一修订下静默改写。让 verified 回执精确覆盖来源挂牌字段或要求权威绑定版本查证，并加正负例。

3. **[P2] 普通股可携带存托凭证折算比率。** `SecurityV2.adr_ratio` 只限制正数（schema 207 行），`scripts/contract_validation.py:257-261` 只要求回执含同数值；`security_type=ordinary, adr_ratio=3.0` 且回执 `verified_adr_ratios` 含 `3.0` 被接受。该数值没有 ADR 语义，会污染证券折算/估值消费者。要求 `ordinary`/`preferred` 等非存托凭证的比率为 `null`；只有 adr/gdr/cdr 能在核实回执下填正比率。

## 通过的边界与验证

- `validate_legacy_entity_read` 能读 v1，`validate_entity` 拒绝无显式状态/修订的旧对象；来源候选作为 Entity 输入也被拒绝。
- `ProvisionalEntityV2` 对国家、规范交易所、币种、证券类别及挂牌状态允许显式 `null`，保留 `exchange_raw`；单证券上限拒绝把 A/H 或 ADR 靠名称合并。
- 缺 owner 回执、非 active 回执、修订/证券 ID/绑定引用不一致、反证标记为 true、非经营主体 scope 均拒绝；verified 跨证券要求回执覆盖全部证券 ID 和已列属性。
- 隔离运行 `python -m pytest -q -p no:cacheprovider --basetemp <唯一系统 TEMP> tests/test_identity_contract.py`：**12 passed, 17 subtests passed**；Draft7 schema 自检通过；`git diff --check` 对所审三个已追踪文件通过。故障注入脚本仅通过标准输入交给 Python，无源码或生产数据写入。唯一 TEMP 目录已清理，`TEMP_CLEAN=True`；没有外部仓库写入或真实 API 调用。

审查快照 SHA-256：

| 文件 | SHA-256 |
|---|---|
| `schemas/quick_scan/identity.schema.json` | `8D790262D886E593FF9654AB6875ACDAA80EF09E1A4E525338D41D88D3DBAAE1` |
| `docs/implementation/contracts/identity.md` | `EF8D21A0071B9F0EDB41F732CC0E60AC14A09591D2186C6D51CF66B6859DF80C` |
| `scripts/contract_validation.py` | `1D54113BE3D8757BC2472DEE84E00930EBAF3C7F64122A115D982CA324DE2FC2` |
| `tests/test_identity_contract.py` | `2FA6B707EF95D173ED4EE58DA51CB606C9CCFAC261BACE9ABB53806EE5985FC0` |

重审门槛：固定上述四个故障输入为隔离回归；单对象处能拒绝的字段矛盾应先封住，跨实体来源唯一性必须在 W02 owner DB 实际事务与扫描准入测试中验证。保留 C01 第一段为 `partial`，不得据此宣称 W03 已有 2,000 家可扫描公司。
