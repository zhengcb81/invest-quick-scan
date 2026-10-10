# 原W15步骤4：query v2接口施工约定（实施中）

起点IQS bc9ab49、StockWiki a5a97d6、StockQA6aafc32；原基础批次已交付/自有w15a已清。新独占runs/c15a固定64件IQS scripts/schema原字节与三仓Git状态，inputs-01为准备时点，不是已测试或真实golden。这里具体化原c06-next，不加新的审查节点；整查询/刷新范围收尾集中审查。

第一组TDD先锁定显式主体的get_profiles与输入边界，再扩展search/capabilities/candidate_set、受控刷新和真实owner serializer。接口尚未发布，不能用本文件说C06已通过。

- 新公共模块`scripts/query_contract.py`与`schemas/quick_scan/query-v2.schema.json`。`validate_request(document)`、`validate_response(document, *, expected_request, expected_owner)`纯验证；`load_document(path)`复用原严格JSON/限长规范，拒重复键/非有限数。公开CLI在同批后续接入，不提供任意命令或远端ref。
- request/response显式`schema_version=2.0.0`，保留message_type/request_id/operation时间字段和consumer_id。旧query.schema.json原1.0.0不改、不通过新入口静默升级；旧validator仍可读取合法历史。
- get_profiles payload具体为`subject_refs`、`field_ids`、`information_cutoff`、`include_history`、`model_filter`与可空`snapshot_id`。SubjectRef完整字段：`entity_id`（快扫实体）、`analysis_subject_id`、`analysis_subject_revision`、`primary_issuer_id`（法律发行人）、`perimeter_sha256`、`scope`、`scope_id`、可空`security_id`/`listing_id`/`segment_id`。两个entity id的含义不同，不强行设相等；真实producer必须核owner issuer bridge。共同subject/scope键不能请求两种perimeter；同发行人多个subject保留两条。
- get_profiles result具体为`status`、`profiles`、`missing_subject_refs`、`coverage`、`watermark`。profile为`subject_ref`、`canonical_name`与`observations`，保留原Observation而非重封新分；原模型/信息时间/原hash与范围都可追溯。先验证空覆盖，再用真正原Observation fixture补模型/时间/版本正反例，不伪造真实公司评分golden。
- response必须绑定调用方独立保存的原request与expected_owner.store_id；只有报文内部自洽不能证明来自owner。request_id/operation和profile/missing refs匹配精确请求，禁止名字合并、跨主体/修订/perimeter/作用层取观察。covered/missing fields严格划分请求；未覆盖不可返回complete或“没有业务”。读取故障与真正空覆盖分开。
- 水位沿用store_id/snapshot_id/member_sequence/observation_sequence/ack_sequence/read_at；新增逐库schema/状态和读取一致性说明在同批producer设计时冻结。分页快照内容必须有可重算摘要，固定query语义、原SubjectRefs和Observation ID/hash；不能给mutable live页套个旧snapshot_id。各独立SQLite只能声明真实逐库一致性，不声称跨库原子快照。
- owner真实数据库以只读mode打开，查询不migrate、不写数据/名单、不发LLM；读取错误不转空列表。真实golden生成要记录实际命令/HEAD/schema/capabilities/水位和输入输出SHA，真实评分未覆盖可如实返回coverage_gap；empty正例不关闭金融准确性或F05。

本约定中尚未冻结的水位扩展与分页/刷新细节随本节点实际代码和TDD同步，不新增小卡或重复预研。当前legacy query/C06门仍开放；TH/IN继续等待原G3/F05/W11及真实query交付条件。

## 非空投影的原始来源边界（同批实施中）

新查询不改写原Observation。投影保存原JSON的base64、原字节hash、canonical payload hash、Observation ID和owner入库/ACK序号。原模型requested/resolved、时间、问题/字段、分数与未知状态只从原JSON读取。该base64只允许限长的结构化Observation，禁止公司文档或网页正文；解析后仍严格验证标准答案结构。

主体绑定使用具名轻量sidecar `stockwiki.observation_subject_binding/1.0.0`，独立绑定原观察ID/hash、执行request/attempt、派发前冻结identity/manifest摘要、SubjectRef和事前记录时间。消费者校验时必须有独立owner保存的Observation引用及binding摘要，不允许仅从被验报文构造信任输入。该sidecar的生产/导入尚待接线，不从现有无subject的标准答案或当前route临时推导。读取器明示portable observation dialect，只在新查询入口适配真实UUID拼法，不改旧Observation schema。

旧无绑定的合格原Observation放在result的`legacy_unbound_observations`，与任何subject profile分离，仅作原模型/时间历史查看；不能算当前subject字段覆盖或白名单资格。同一entity多个主体不能因此复制出多份当前答案。查询availability与独立证据资格分开，不能由模型正文或本查询授予资格。

水位增加原query语义摘要、冻结结果内容摘要和逐owner库的schema/状态/序号/读取时间/内容摘要；明确`sequential_owner_reads`。读取失败不得返回完整空覆盖。snapshot摘要可以发现内容漂移，但不是owner认证；指定旧snapshot必须匹配，不能悄悄用live页替代。

上述格式为私有TDD阶段，实际owner sidecar、查询serializer与跨仓接线仍未交付；不使用合成范围绑定签收真实golden，不新增独立审查节点。
