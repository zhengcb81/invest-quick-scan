# W02 身份主档导入：只读接口勘察

状态：设计准备；StockWiki、company-wiki 均未改动，W02 依赖 W01 完成并需另行确定 StockWiki 写入范围。

company-wiki 已有 `SecurityMasterStore`，以各市场 `cn.json`、`hk.json`、`us.json` 为带 `schema_version`、`retrieved_at`、`sources`、`record_count` 的版本化 JSON 快照。`SecurityRecord` 含市场、交易所、代码、`security_id`、名称与别名、是否活跃、来源 URL/记录 ID，以及字符串 `identifiers`；**没有可直接信任的跨市场发行人 `entity_id`**。`company-wiki-identify` 默认从这些快照只读解析单个查询；显式 `--refresh` 才联网更新，快扫导入不得使用该开关。它的查询结果不能替代完整批量快照导入。

W02 应把三地快照作为可选只读输入，经 schema、记录数和来源版本验证后转为 StockWiki 的证券候选；另接受用户 CSV/JSON 清单。每条导入行存原始 market/security ID、snapshot 文件 hash、retrieved_at、source_record_id。StockWiki 自己分配稳定 `ENT_...` 和 `SEC_...` ID；不要用股票代码、名称或同品牌作 entity 合并键。官方发行人识别符存在且完全一致时也先产生候选桥接与出处，待 W02 的核实规则/人工确认后才使经营题跨证券复用。冲突、缺失、多候选都挂起对应证券，保持其他对象可导入。

ADR 比率与基础普通股关系必须另有官方核实记录；无法核实时 `adr_ratio=null` 且证券层折算/估值为 unknown。A+H 同一发行人与母子上市公司必须用两组固定反例测试，避免按名称去重。导入应有只读 preview，展示将新增、将关联、待核实、重复和冲突；apply 使用 W01 的短事务与版本记录。任何步骤都不创建 company-wiki 公司目录、不刷新证券主档、不下载报告。

实现前再次核实公司主档真实快照字段、缺失市场与许可范围，并按 W02 任务绑定 `ID-01/02/03`、`UNI-02/06` 测试；这份勘察不等于 W02 验收。
