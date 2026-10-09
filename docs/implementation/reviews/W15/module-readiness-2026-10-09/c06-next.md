# W15步骤4接续：正式查询/刷新与真实owner golden

这是原W15未完成步骤4的具体施工顺序，不是新增审查门。root继续唯一writer，用户全部后续所需授权有效。先完成本批基础链的源发布/归档/严格自有清理，再用新独占短根接续；不得盲跑删除后的w15a一次性控制器。

## 本次只读核实的缺口

- 当前 `StockWiki/stockwiki/quick_scan_query.py` 是W09只读primitive；`get_profiles`按entity并project_row，`capabilities`明确C06=false/facts=false/freshness policy=false。它不能仅改标记就成为C06。
- IQS `schemas/quick_scan/query.schema.json` 是legacy query 1.0.0：EntityId不含现行UUID的连字符，CompanySummary无analysis subject/revision/perimeter，get_profiles仅entity_ids。现行身份契约已2.2、Observation2有主体；直接包装该legacy schema会丢范围或拒真实ID。必须显式新query版本，保留原1.0读取，不修改历史原文、不把issuer猜成报表主体。
- 当前W15公开route/refresh wire固定由IQS三schema定义，仍C06=false；QA wrapper只复用scored/已核N/A。事实answered/关系输出与F05分开推进。
- 冻结真实只读备份克隆的实际计数见intake同目录 `query-input-counts-01.json`：3实体、7来源绑定、6证券、216候选、121issuer bridge、1真实analysis subject/perimeter；universe/member均0。这不是“200家公司已有身份/画像”，也不是新鲜生产库快照；正式golden前重核实际owner状态与serializer。克隆没有观察库或公司文档，不能填假观察造真实正例。

## 连续实施顺序与唯一职责

1. **IQS契约版本与纯验证。** 新增query v2 schema及operation语义校验；analysis subject完整key/revision/perimeter、primary issuer、明确scope/security/segment都引用现行身份约束，统一market映射。v1保持原文件/原读分支，不静默升级；先写真实UUID、同issuer两个subject、分页/水位/缺覆盖、跨model原引用、旧v1读取反例。schema成功仍不验证金融正确性。
2. **StockWiki公共只读生产者。** 复用现有subject/identity/Observation存储与W09筛选、比较规则；不复制评分/题库/刷新算法，不新造数据库。按显式主体投影，不合并不同比较组，不用entity summary推断唯一主体。完整查询水位/快照由owner真实读取产生，未知字段/未覆盖返回coverage_gap或partial；不能返回“行业没有公司”。原W09/UI协议保持原样，新公共CLI单独明确版本，先capabilities/search/get_profiles/candidate_set。
3. **受控刷新。** request_refresh只作预览，绑定精确snapshot、主体、字段、owner政策版本/权限及费用上界，复用已交付W15模块planner和QA原projection。approve_refresh必须消费实际认证确认记录/稳定幂等键，重核scope/policy/budget，登记交给原Q13而非自己发HTTP。已有会话授权按真实owner权限适配，不造确认凭据、不从请求自填费用/模型/名单；preview和read都零收费。nominate/conflict只登记线索，不能改身份或自动选股票。
4. **真实owner golden与公开验证。** 使用source owner公开serializer和只读实际输入，记录生成命令、HEAD、contract/capabilities版本、真实数据库水位、输入/输出SHA。有且只有实际原记录可作正例；现有真实主体可演示正确身份/空覆盖，不伪造评分/事实正例。通过IQS公开CLI验证真实golden，再用其副本做错主体/错perimeter/错model/错watermark/截断、重复键、旧snapshot、过期TTL、未授权确认等负例；原owner数据不变。
5. **同一大节点收口。** 当前受影响unit/integration/实际OS CLI批次；一次集中审查及同会话必要补测；正常源提交和严格自有清理。不要重复旧full/UI/原harness交付，不生成逐helper回执。阶段签收按实际能力声明；F05、B01准确性/L03/G3、TH/IN仍须各自原前置，不能由空覆盖golden代关。

## 接续时必读

2026-10-09实际只读定位补记：StockWiki `AnalysisSubjectStore`就在`stockwiki/quick_scan_analysis.py`，不是独立analysis_subject_store模块；其get_subject/get_perimeter_receipt目前打开现有库，CLI import会migrate，正式只读查询不得复用import入口。IQS公开identity CLI为`scripts/identity_contract_cli.py`，legacy query语义函数为`scripts/contract_validation.py::validate_query_response`，尚无公开query CLI；不要猜qs.py或不存在的quick_scan_query CLI文件。CodeGraph files已列现行40 scripts，symbol search找到了legacy validator，外仓subject索引仍缺失。

多个owner SQLite不能声称全局原子快照。新查询要显式标明逐库读取一致性、实际水位和快照内容摘要；分页应绑定原query/主体范围/原Observation引用及捕获水位，不读取live页来悄悄重排，不把自洽hash当认证。数据库缺失、旧schema、权限/读取失败必须与真的空覆盖区分；禁止直接用旧profiles中的SQLite异常→[]掩盖这些错误。以上是原步骤4设计落实，不新增独审门。

- 本目录plan.md、operations.md及同次review最终附记；真实源提交以source-publication/result.json与progress最新回执为准。
- IQS `docs/implementation/contracts/exchange-and-query.md`、`schemas/quick_scan/query.schema.json`、identity/observation/exchange schema及既有validation公共入口。
- 实际StockWiki query/profiles/rows/analysis/identity/Observation/refresh与已发布route/module-refresh，StockQA owner-refresh/Q13与费用/ACK恢复接口。CodeGraph当前context有漏索引，按返回位置判断范围；不能把旧IQS归档当源。
- TH-IMPL-01/IN-IMPL-01仍暂缓：真实query/capabilities/golden和生成命令及G3/F05前置未正式接收。全授权解决写权限，不能替代其证据门。
