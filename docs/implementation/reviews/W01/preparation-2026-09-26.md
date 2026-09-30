# W01 StockWiki 快扫身份库：写入前实施边界

状态：只读勘察与设计；尚未修改 StockWiki。StockWiki 工作树目前存在大量其他进程改动，实施时只对下列精确文件做局部操作，并在动手前重看状态。

## 已核实的仓库现状

- StockWiki 的现行 `stockwiki/schema.py` v2 迁移对象是 YAML 工作区和 `.schema_version.yaml`，没有可复用的全局 SQLite 数据库。`WorkspacePaths.data_dir` 是唯一应复用的路径约定。
- 正式研究沿用 `data/companies/{ticker}` 与 YAML 分类；快扫没有现存 `quick_scan` 表或目录。W01 不调用 `migrate_schema()`，不改正式 YAML、ticker 目录或通用来源 worker。
- 新数据库默认定位 `WorkspacePaths.data_dir / "quick_scan" / "scan.sqlite"`；测试可用 `WorkspacePaths.from_root(tmp_path)` 整体重定向。部署时统一 data_root 可选择别处，不能把用户正式库当测试库。
- 身份契约 C01/G0 只认可发行人实体、证券和分部的显式关系；同品牌、同 ticker 字符串不能据此合并。company-wiki 资料目录与正式 StockWiki profile 都可为空。

## 请求的精确写入范围

1. 新增 `StockWiki/stockwiki/quick_scan_store.py`：独立 SQLite v1 迁移、短事务与身份/成员基础存取。库的 `PRAGMA user_version` 与旧 YAML 工作区版本各自演进；打开时启用外键和合理 busy timeout，拒绝高于代码版本的数据库，迁移在事务中进行，重复迁移无新写入。
2. 新增 `StockWiki/tests/test_quick_scan_store.py`：全部使用唯一 `tmp_path`，包含下列红绿验收，不读取或改写生产库。
3. 仅在 `StockWiki/.gitignore` 增加精确快扫运行库例外，防止真实公司数据库被误提交：`/data/quick_scan/*.sqlite*` 和 `/data/quick_scan/backups/`。不改已有忽略项。

不改 `stockwiki/schema.py`、`stockwiki/paths.py`、现有正式分类/来源相关文件，不建 company-wiki 公司目录，不下载文档。W02 的主档导入、W03 的完整名单命令、W05 的不可变观察导入均留给对应卡；W01 不把半成品 API 当成全系统就绪。

## SQLite v1 最小逻辑模型

- `quick_scan_entity`：稳定 `entity_id` 主键、规范名称、注册国家、可空 `company_wiki_ref`/`formal_stockwiki_profile`；不以名字作为唯一键。
- `quick_scan_security`：稳定 `security_id` 主键、`entity_id` 外键、市场/交易所/代码/币种/类型/挂牌状态，ADR 比率及基础证券引用可空；联合约束和显式应用校验确保同一证券不能归属两个实体、基础证券不能跨实体、未知 ADR 比率保持空值。代码只做查找索引，不能作为自动合并键。
- `quick_scan_segment`：`segment_id` 主键和 `entity_id` 外键；同名分部不能自动合并。分部占比可空并约束 0—100。
- `quick_scan_universe`、`quick_scan_member`：一个稳定 universe ID，成员以 `(universe_id, entity_id)` 唯一，保留 `membership_status`、`manual_pin`、版本/加入/移除/恢复时间与理由。现阶段只提供底层事务接口，W03 才提供可审计的业务命令。软目标 2,000 不是硬上限。
- W05 再加观察/导入/筛选表；不预先创建没有不可变键语义的占位观察表。

所有 ID、枚举、空值与关系在写入边界按 C01 验证；启用 `PRAGMA foreign_keys=ON`。库文件仅保存结构化身份与状态，不保存公司文档、网页正文或正式 evidence_span。

## 验收与故障注入

| Case | 固定输入/操作 | 必须断言 |
|---|---|---|
| DB-01 | `tmp_path` 下建旧 ticker 目录及分类 YAML，记录逐文件 SHA；迁移两次 | 独立 SQLite 可用、版本不变、旧文件 SHA/路径/目录清单不变；不触发正式 YAML 迁移。 |
| ID-01 | 经显式关联的 A 股和 H 股两个 security 指向同一 entity | 只一份实体记录、两份挂牌；按实体查经营对象只有一份，按证券查有两个币种。 |
| ID-02 | 母公司与上市子公司同品牌/同 ticker 字符串、不同实体 ID | 仍是两个实体；重复 security ID 指向另一实体必须拒绝，不自动并档。 |
| ID-04/DB-06 | 两个关联指针为空；输入带模型自称正式 accepted/evidence 字段 | 入库和读回不依赖 company-wiki/正式 profile；不产生文档或正式来源工件；额外正式资格字段拒绝或明确忽略，不能写到 YAML。 |
| UNI-04 基础 | 成员可超过 2,000、`manual_pin=true`，模拟底层逻辑移除/恢复 | 无容量淘汰；pin 与历史版本保留。完整业务命令与审计由 W03 验收。 |
| 迁移失败 | 在事务内注入错误，再重启迁移 | 不留下半套 schema；新版本库由旧代码打开须拒绝；外键错误回滚。 |

验证顺序：固定反例先红 → 最小实现 → 目标 pytest/ruff → StockWiki `bash scripts/check_all.sh`（如其工作树并发改动造成无关失败，明确记录归属，不改他人文件）→ 独立只读审查 → W01 局部 receipt。所有测试 SQLite 位于 `tmp_path`，测试结束关闭连接，由 pytest 管理自己的临时目录；不触及生产 `data/quick_scan`。真实工作区验证仅只读检查旧状态和路径，不运行真实库迁移。
