# C01 v2 临时身份第一段复审（2026-09-26）

结论：**本仓单对象契约第一段可局部放行**，上一轮三个本地漏洞已封闭；**跨仓扫描准入仍未放行**。StockWiki W02/W03 必须以同一 SQLite 事务对全库来源键和证券 ID 作唯一性与归属检查，才能将临时身份设为可派发。此复审没有验证 StockWiki 实现，也没有授权把候选证券直接加入 2,000 家可扫描池。

## 修复验证

| 固定反例 | 修订后结果 | 位置 |
|---|---|---|
| 回执的 `source_record_id` 改成不存在的 `FORGED` | 拒绝；还必须提供 owner 当前 `trusted_source_bindings` | `scripts/contract_validation.py:159-188, 226-260` |
| Entity 和 owner 绑定同时改 ticker 或 `exchange_raw`，但沿用旧 verified 发行人回执和同一 identity_revision | 拒绝；回执覆盖两字段及来源键 | `scripts/contract_validation.py:296-311` |
| `ordinary` / `preferred` 的 `adr_ratio=2.0`，即使回执声称已核实 | Schema 和写入验证器拒绝 | `schemas/quick_scan/identity.schema.json:193-217`，`scripts/contract_validation.py:215-220` |
| 两个 Entity 争用**同一 `BND_SOURCE_1`**，共用同一 owner 映射 | 第二个被 owner binding 的 Entity/Security 归属校验拒绝 | `scripts/contract_validation.py:173-183` |

故障注入还构造了更重要的跨对象情形：`ENT_OPAQUE_1` / `SEC_OPAQUE_1` / revision 1 与 `ENT_OPAQUE_2` / `SEC_OPAQUE_2` / revision 2 各有表面有效的回执，分别使用 `BND_SOURCE_1` 和 `BND_SOURCE_2`；两个绑定行的**完整来源身份相同**（同 namespace、source_record_id、market、原始交易所、ticker、来源名称），而 owner 映射同时包含两行。`validate_entity` 分别接受两个对象。这不是当前单对象函数可独立推断的全库冲突，也不应通过只约束 `source_record_id` 修复：US 的 CIK 可能对应多证券。StockWiki owner DB 必须为经定义的“来源行键”施加唯一约束，锁定并核验 Entity/Security 归属、identity_revision 和资格回执，提供两条不同 BND 指向同一来源行（包括不同修订）的并发/回放回归；冲突应阻止其中一个成为可扫描对象。C01 文档 24–28 行已明确该跨仓门和可信映射来源。

## 运行证据与范围

- 隔离运行 `tests/test_identity_contract.py`：**16 passed, 31 subtests passed**；唯一系统 TEMP 目录清洁。Draft7 schema 自检通过。反例通过 stdin 运行 Python，未写测试数据或源码。
- v1 仍只走 `validate_legacy_entity_read`，候选对象缺 v2 身份状态不能通过 `validate_entity`；临时未知属性保持显式 `null`，单实体不能借此自动合并 A/H、ADR。
- `trusted_identity_receipts` 和 `trusted_source_bindings` 在 Python 中是传入的映射，局部函数只能校验内容一致，无法证明映射源自 StockWiki；W02 集成必须由 owner 生成可信投影，不能把 LLM/UI/候选数据直接当作该参数。
- 无外部仓库写入，无真实 API 调用，无生产数据库迁移。全仓测试以主实施者已报告的 `313 passed, 214 subtests` 为背景，本复审独立确认上述聚焦测试与故障注入。

复审快照 SHA-256：

| 文件 | SHA-256 |
|---|---|
| `schemas/quick_scan/identity.schema.json` | `228745AA45474E5670D7801D1BAA8211DD7CE8BC911A96C611FF0294ABE7F1F3` |
| `docs/implementation/contracts/identity.md` | `2680AF14EC3E6D1E086B14CF61211D6F649CF3DAE7C18A7654498DAC57321C50` |
| `scripts/contract_validation.py` | `4AC5AB5B164168BD13DB52E6FAB0034350AE4D217FE12EBFB2F4575AB8C899D9` |
| `tests/test_identity_contract.py` | `C4B90BDAB3D86F9C36AAA54B0A8FF59C0BC49FCEC54DC5BCF952536C5A4E809C` |

局部放行含义只限 C01 本仓 v2 契约与纯函数；W02 权威来源绑定、全库唯一性、SQLite v2 迁移、W03 资格/池、旧观察版本隔离和派发仍是独立验收门。
