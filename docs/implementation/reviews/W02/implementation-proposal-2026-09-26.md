# W02 身份主档导入与跨挂牌核实：实施提案

状态：只读勘察与可执行设计；**W02 尚未实施或验收**。此文件只在 invest-quick-scan 仓库内，不授权写 StockWiki 或 company-wiki。W01 的 SQLite v1 已存在，W02 依赖其独立复审通过。

> 后续身份审计补充（2026-09-26）：本提案以下“仅候选、加法 v2”是安全的最小阶段，却无法让缺注册国/证券类型/币种/精确挂牌状态的三地快照一键形成约 2,000 个可扫描对象。为满足完整产品目标，先按[暂定身份设计](../W03/provisional-identity-design-2026-09-26.md)修订 C01；W02 仍限下列四个 StockWiki 文件，但 v1→v2 可能需要在单一事务中重建身份表以支持显式未知值、同库 provisional/verified 状态和身份修订。实施前将冻结并测试最终 v2 DDL，不把这里的加法迁移草案误作已获验证实现。

> C01独立复审补充：`source_binding_ref` 的唯一性不足以防止两个不同BND指向同一来源行。StockWiki必须在事务中对来源行身份键设唯一约束，并使同一键的后续快照/身份修订复用同一稳定绑定；不能只在单个Entity JSON内检查。只读检查真实快照发现：`(market, security_id, source_record_id)` 三元组在CN/HK/US各自均无重复，但仅`source_record_id`分别有258/0/653个值被多证券共享（最多分别2/1/9条），所以不能把CIK等来源记录ID单独当证券唯一键。最终DDL应按来源命名空间加三元组实现唯一性，并给代码变更/来源键变更保留经证明的连续性事件。

## 已核实的输入与边界

- company-wiki 的 `SecurityMasterStore` 在 `.source_catalog/security_master/{cn,hk,us}.json` 保存 schema `1.0` 快照。当前本机真实快照分别有 CN 6,137、HK 2,746、US 6,959 条，来源时间均为 2026-07-19；快照 JSON 含 `schema_version`、`market`、`retrieved_at`、`sources`、`record_count`、`records`。每条 `SecurityRecord` 含 `market`、`exchange`、`ticker`、`security_id`、`canonical_name`、`aliases`、`active`、`source_name`、`source_url`、`source_record_id`、`identifiers`。`company-wiki-identify` 默认只读，`--refresh` 才更新快照；它是单查询解析器，不是批量导入接口。
- 实际 identifier 只有 CN `org_id`/`cninfo_category`、HK `hkex_stock_id`、US `cik`。它们**不是跨市场共通 issuer ID**；US 的一个 CIK 还可能对应多证券。`security_id` 在当前三个来源中实质是代码，代码可能改名或再利用。来源没有法人注册国家，也没有普适可靠的证券类型；US 快照含一个 iPath ETN 样本。CN 6,136 条标记 `A股`，1 条 `CDR`。US 有 `NYSE AMERICAN`、`NYSE ARCA`、`BATS` 等，超出 W01 交易所枚举。
- W01 的 `quick_scan_entity` 要求两位 `incorporation_country`，`quick_scan_security` 要求已知 `security_type` 和枚举交易所。因此未知国家/证券类型不能靠挂牌地、名称或默认 `ordinary` 填充。W02 先存候选与缺口；得到可核实的补充输入后再 promotion。这个策略保留 C01 v1 契约，避免虚构发行人属性。后续若要自动把所有来源行直接建为可扫描实体，需单独修订 C01/W01 的 unknown 语义，不能在 W02 偷填 `CN`、`HK`、`US` 或 `ZZ`。

## 精确文件清单与职责

仅提议以下 StockWiki 四个文件，实施前仍需对这四个文件取得写入授权；**不改 company-wiki**，不写它的快照或公司目录。

| 文件 | 操作 | 最小目的 |
|---|---|---|
| `StockWiki/stockwiki/quick_scan_store.py` | 修改 | 加法 v1→v2 迁移、v1/v2 签名校验、来源映射/候选/桥接表与短事务接口；旧 entity/security/member 原值不改。 |
| `StockWiki/stockwiki/quick_scan_identity_import.py` | 新增 | `preview`/`apply`/`verify-bridge` 的小 CLI 与纯函数；读取现有 `SecurityMasterStore` 快照或用户 CSV/JSON，给出稳定排序的歧义报告。 |
| `StockWiki/tests/test_quick_scan_store.py` | 修改 | v1→v2、假 v1/v2、事务回滚、旧成员不丢、恢复副本验证。 |
| `StockWiki/tests/test_quick_scan_identity_import.py` | 新增 | ID-01/02/03、UNI-02/06 和来源输入、幂等/竞态/只读副本验收。 |

不改 `.gitignore`（W01 已精确忽略 `data/quick_scan/*.sqlite*` 与备份目录），不改 StockWiki 现有 YAML/正式研究运行时，不在本目录复制生产数据库。若必须发布 CLI 命令，可先用 `python -m stockwiki.quick_scan_identity_import ...`，避免触碰 `pyproject.toml` 或旧 CLI 注册。

## v2 SQLite 加法迁移

保留 W01 的五张表及现有列，`PRAGMA user_version` 从 1 提升至 2。建议增加四类表，名称全部 `quick_scan_` 前缀、带外键与必要唯一约束：

1. `quick_scan_identity_snapshot`：输入种类/来源命名空间、市场、schema 版本、文件 SHA-256、UTC `retrieved_at`、来源 URL 集、记录数、导入时间及相对定位符。`snapshot_id` 从输入字节哈希生成；不存财报、PDF、网页全文或绝对路径。真实文件始终留在 company-wiki 原位置。
2. `quick_scan_identity_candidate`：每个 `(snapshot_id, market, source_security_id, source_record_id)` 一行；保存来源行号、官方证券级字段、原始交易所、别名/identifier 的规范 JSON、证券类别/法人国别补充证据状态、`candidate_status` 与机器可读 reason 列表。`source_url` 与记录 ID 跟行保存。未核实、冲突、范围外仍可留候选，不必伪造 Entity。
3. `quick_scan_source_binding`：`(source_namespace, market, source_security_id, source_record_id)` 唯一指向一个内部 `security_id`；保存 first/last snapshot、核实依据、有效期。内部 `SEC_...` / `ENT_...` 首次升格时分配不含 ticker/名称的 opaque ID，后续只靠持久 binding 复用，绝不重算/改名；ticker 变化产生新来源键，须有明确连续性证据才挂回原 `SEC_...`。相同 ticker 但不同 source_record_id 是冲突/新候选，不能覆盖旧 binding。保留历史键可追溯改名。
4. `quick_scan_issuer_bridge`：证券对、`proposed/verified/rejected/merge_pending` 状态、核实主体与时间、明确发行人/股类或 ADR 关系证据的官方 URL/记录 ID/快照哈希、审核备注。等名、同品牌、代码相同、模糊匹配只产生 `proposed`，不会直接更改 Entity。经过证实 A/H 同一法人且双方未造成其他已观察身份冲突时，挂入一个 Entity；两个已建立且有成员/观察依赖的 Entity 不自动合并，记 `merge_pending` 并输出影响清单。母子上市公司保持两个 Entity。

迁移过程：先检查 `user_version`；对 v1 数据库先以**冻结的 v1 全 DDL 签名**验证旧五表/索引/触发器与外键，再 `BEGIN IMMEDIATE` 新增表、校验完整 v2 签名及 `foreign_key_check`、设置 `user_version=2`、提交。v0 新库可先在同一事务创建 v1 再加 v2。重跑 `migrate()` 返回无改动。伪 v1/伪 v2、未来版、已有表缺约束均拒绝，不“修复”或覆盖；任何失败回滚全部新表和版本，旧 `quick_scan_member`、`manual_pin`、`version`、实体/证券 ID 原样保留。先在临时复制的 v1 库验证备份/恢复，再考虑真实部署，绝不在 W02 测试中迁移真实库。

## 导入、核实与幂等语义

1. `preview` 只读输入快照和只读打开的现有 SQLite；在未建库时也不得创建 DB。先用 company-wiki `SecurityMasterStore.load(markets=..., require_all=...)` 做版本/记录解析，再读取同一文件字节计算 SHA-256；前后哈希不一致则失败，避免边读边刷新导致元数据与哈希错配。额外检查 `retrieved_at` 为 UTC、`record_count` 非布尔整数且等于实际行数、`sources` 为非空 HTTPS 列表、同市场来源键无重复。来源可仅有部分市场，但报告缺失市场与覆盖分母；要求三地完整时显式 `require_all`。CSV/JSON 用户输入走单独、版本化的字段映射；缺少来源 ID/官方证据的行只进候选。
2. 每行先确定证券范围与分类：CN `A股` 可判普通股、`CDR` 判 CDR；US 官方目录已滤 ETF/测试证券但不能据此断言剩余全是普通股或把 ETN 当公司；HK 股票名录亦不能证明注册地/ADR 比例。缺证券类别、法人注册国、US 非 W01 枚举交易所映射证明者标为 `needs_classification`/`needs_country`/`needs_exchange`。`NYSE AMERICAN→AMEX` 可设显式、版本化规则；`NYSE ARCA`/`BATS` 等保留原值并待范围判断，绝不无声改成 `OTHER`。亏损、未知行业不是身份排除条件；ETF/测试证券/ETN 明确标为 `out_of_scope` 或 `needs_type`，避免混入普通股池。
3. `preview` 返回 `input_hashes`、`db_version` 与当前相关行的 digest、`ruleset_version`、候选总数、将新增/重复/关联/冲突/待核实/范围外、按市场去重后的候选实体数与覆盖缺口；每行固定 reason code、来源 ID/URL、可解释的人工动作。缺少跨市场桥接时两个证券各占独立候选，不用相同名称强凑 2,000 家。
4. `apply` 接收冻结的 preview plan 与显式 `expected_digest`；开始事务前再次核对输入哈希，事务内重新确认 DB 版本/相关映射，发现并发变更即拒绝重做 preview。按稳定排序写入 snapshot 与候选；同一输入重导入幂等，不提升快扫数据新鲜度、不改 `manual_pin`/名单成员。不允许一个来源键悄悄改绑内部证券。可核实的提升行在同一短事务写 Entity、Security、binding；其余行保留候选状态，不阻塞无冲突行。无证据的 ADR 比例必为 `null`，证券级折算与估值输出 `unknown`。
5. `verify-bridge` 必须给出两个证券 ID、关系判定、官方发行人/存托协议 URL 或可核验记录 ID、确认时间及操作者；检查两条 Security 所属 Entity、证据证明的法律主体、ADR 基础普通股和明确比例。核实记录 append-only 或带审计版本，拒绝与先前 verified/rejected 冲突的静默覆盖。研究/扫描问题只在 verified 且同 Entity 时复用经营回答；没有比例也不复用证券级估值。

## 测试与独立验收（全部隔离）

- 单元/集成：`pytest -q tests/test_quick_scan_store.py tests/test_quick_scan_identity_import.py`。每例使用 `tmp_path` 的 DB 与快照副本；同时覆盖带三名成员/手工锁定的真实 v1 形状库迁移前后逐行相等、注入中途失败后的版本/表/成员零损、伪 v1/v2 schema 拒绝、事务并发 digest 改变拒绝、preview 前后 DB 与快照哈希一致、重导入零新增、ticker 变更/recycled ticker 不改内部 ID。
- ID-01 固定 A/H 两证券、官方同法人核实记录，得到一 Entity 两 Security，两货币且经营题只一份；ID-02 固定同品牌上市母子公司与相同 ticker 字符串，永远两 Entity；ID-03 ADR 比率未知为 `null`，基础股关联必须经核实，证券估值 `unknown`。另覆盖同 CIK 多股类不可自动合并、一个坏候选不吞掉好候选、缺市场/行业为空及亏损不剔除、ETF/ETN/测试证券范围、UNI-06 重叠/空缺报告。
- C01独立审查固定反例须在W02 owner库落地：两个不同BND、不同Entity修订指向同一 `(source_namespace, market, source_security_id, source_record_id)` 时，第二个绑定的事务整体回滚，旧映射/成员/版本/观察不变；同CIK但不同来源证券ID可并存且不自动合并。另测两个worker并发promote同一来源键，只有一个得到唯一绑定，失败者不能生成孤儿Entity。
- 真实资料 opt-in：设 `STOCKWIKI_REAL_SECURITY_MASTER_DIR` 指向 **只读** company-wiki 快照目录；测试先记录三文件 SHA-256，只复制 `cn.json/hk.json/us.json` 到 `tmp_path`，用复制件运行解析、preview、少量已核实输入的 apply，然后确认源文件原 SHA-256、mtime/大小未变、临时数据库和副本随 `tmp_path` 结束清理；无网络、无 `--refresh`、无下载。测试若未配置该变量，可明确 skip；正式 W02 验收需提供一次未 skip 的真实副本运行摘要与独立复审。
- 全仓必要检查：在获批实施、目标仓变更稳定后运行 `bash scripts/check_all.sh`；如环境门禁失败，分清项目既有/环境问题与 W02 回归，并保存完整摘要与文件 hash。独立审查最新 diff 与反例之后才把 W02 标成 verified。

## 实施顺序与尚待确定

先固定真实快照/CSV 的字段映射与候选 reason code → 写红测 → 完成 v2 加法迁移和回滚测试 → 做纯 preview → 实现带 digest 的 apply → 实现桥接核实/冲突记录 → 跑离线及真实只读副本测试 → 独立审查。整个阶段不调用 StockQA、不下载报告、不写 company-wiki，不把快扫问答变成正式 StockWiki accepted evidence。

尚待确定的产品选择只有**未知注册国家/证券类别的后续处理方式**：本提案按现有 C01 v1 契约保持为候选，W03/之后的身份核实补齐后方可成为可扫描实体；若要大规模自动先入池并以 `unknown` 身份运行，须另立 C01 契约修订及 W01 存储迁移，不应暗中使用挂牌地代填注册地。这个选择不阻挡 W02 的只读导入与候选审查实现。
