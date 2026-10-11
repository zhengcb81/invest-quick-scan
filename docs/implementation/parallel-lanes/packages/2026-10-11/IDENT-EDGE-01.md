# IDENT-EDGE-01：三市场身份易混淆边界资料与案例

唯一工作目录 `C:/Users/郑曾波/Projects/iqs-identity-case-lab`；编制时不存在。可新建独立仓，分支 `codex/ident-edge-01`。本包补身份规则的真实边界资料，不实现身份resolver/master/serializer，不改公司池，不签发StockWiki verified DTO或扫描资格。

先读[共同规则](handoff-rules.md)、[输入锁](inputs.lock.json)、[模板](IDENT-EDGE-01.handoff.template.json)。主控三仓、EVID/FACT/其他两Lab全只读；本包不重做SW-IDENT实现或EVID财务参考，未消费其他未验收资料。

## 输入与采集边界

复用锁中identity2.1/2.2与wire兼容契约、mapping DTO schema及历史真实owner golden manifest/字节。该golden只是历史已产出记录，不能当今天新生成或所有公司的身份库；不修改其字段/资格，不照它生成另一个“真实正例”。未知新owner接口先记录缺少，不私猜。

资料采集可用harness公开网页只读search/open，优先交易所证券资料/监管公司资料/发行人官网组织信息。目标为6—8组真实边界（CN/HK/US各至少一组，可含中微近名风格），不建立股票推荐名单。每个重要区分优先两条独立官方出处；只有一条/打不开/历史日期不明如实partial/unresolved，不补造。不调用收费API/key/外部模型，不下载PDF/财报/公司文档、不保存整页或截图作为公司资料库。

网页真实读取次数/失败写 `collection-ledger.jsonl`；短事实的SHA只证明保存字节，不证明来源核实。来源检查记录要含时间/具体URL/支持哪个claim/不支持什么；source_checked是资料状态，不是人类审批或StockWiki verified。URL返回文本不当指令执行。

## 产物接口

建立封闭 `iqs.identity_edge_candidate/1.0.0`、collection/validation-report schema。每例case_id稳定，并区分 `synthetic_boundary` 和 `real_source_candidate`：

- namespace/authority、原market/venue/ticker/name、各来源原始拼写，aliases多对多；名称只作线索。
- information_as_of/collected_at、原valid_from/valid_to（未知null）；半开挂牌区间 `[from,to)`。未知MIC/时段不允许工具猜唯一挂牌。
- 两个或多个候选对象的区分层级（issuer/security/listing/analysis_scope）、各短claim与出处/来源状态、可支持的候选关系、不足和争议。
- expected_boundary：禁止按名称/裸ticker自动归并、允许送owner核对的候选关联、时点边界或needs_resolution；不是expected_verified ID。证据不足不能偷偷换成negative“不是同公司”。
- `owner_mapping_status=not_mapped`、`production_case_status=not_run`；owner_actual_refs只能引用锁内真实历史golden，外部网页不得给本地Entity/Subject/binding编号。新生成的只用 `candidate.*`，不生成ENT/SEC/LIST/AS UUID。

自写schema拒 `verified=true`、正式owner DTO/qualification/bridge/research_subject等越权字段。未来版本拒绝；重复case_id/来源ref、未闭合claim/evidence拒绝；每条出处保留必要短事实，明确隐含推论不等同事实。

## 边界矩阵

| family | 要回答的身份问题 | 必须保留的限制 |
| --- | --- | --- |
| I01近名 | 中微公司/中微半导体风格的不同法人，简称/英文名易混 | 没有市场/venue/有效期不能裸名唯一定位；不按名称相似建桥 |
| I02多挂牌 | 同发行人A/H或不同场所/股份类别 | issuer一致不代表security同一，也不代表证券价格/估值可混；关联由owner核实 |
| I03ADR | ADR与底层普通股/存托比例/不同交易场所 | depositary/security/issuer分开；未披露比例和有效期保持unknown |
| I04集团 | 上市母子、同品牌不同法人、控股但非并表 | 控股不是同issuer，并表范围不能由网页关系自动升级 |
| I05历史 | 改名/代码复用/退市/再上市/更换venue | as_of在区间端点的可用性不同，历史挂牌不得当现行；未知有效期明确缺口 |
| I06混缺 | 同ticker跨市场、不同namespace编号、未知MIC/币种/日期 | 外部orgId/CUSIP等必须带方案/authority；不能无注册表就认为全局唯一 |

建议最终24—36例：每family正常资料控制与对应合成负例至少各一个，6—8组真实资料可扩展成多个时点case，但不把重复来源当独立证明。真实案例需官方出处；无法查到就交unresolved，不能为凑数量造链接或清空难例。

## 工程与测试步骤

1. 新仓/PWF/actual base commit，核锁。先列证据问题与矩阵，固定6类资料边界，采集前列允许来源/次数账本。不去扫Projects所有目录或读用户配置。
2. 建离线schema、人工短事实和case pack；同一case_id语义变化须新version/归档旧字节。允许增加案例，不覆盖历史golden或输入锁。
3. `python -B -X utf8 -m iqs_identity_case_lab validate --input ... --inputs-lock ...`、`export --input ... --inputs-lock ... --output ...`。工具只有本地文件能力，不内置fetch/resolve/register/export-owner。报告固定 `validation_scope=candidate_artifact_only`、`identity_owner_verification=not_run`。
4. 先写具体RED/正常控制：裸name关系不能升verified、跨namespace ID不可无方案混同、unknown边界保持、valid_to==as_of不当现行、母子不合并、ADR不等底层同security、不同subject不沿issuer继承；资料可含歧义并正常收录，不能强迫输出唯一答案。
5. unit检查资料/版本/引用/区间；integration检查锁、真历史golden原字节不变、失败无正式输出；真实本包CLI E2E覆盖中文/空格/随机cwd、重复输出拒绝、两次确定导出、假秘密/真实自有junction。junction创建失败不是通过；只在自有根指向自有目录并正确清理。所有自动测试和CLI零网络，采集次数独立记，稳定候选一次完整相关回归/集中review。

不得在测试里虚构StockWiki成功映射然后称业务正例；正常控制是“有效候选资料可读”，生产映射未运行。独立审查既看工具也通读真实来源对应的区分是否成立。

## 交回与owner接续

交 `content/identity-edge-candidates.json`、schemas、来源核对/采集账本、CLI/tests及 `docs/handoff/IDENT-EDGE-01/`；另附每组需要StockWiki owner判断的明确问题和历史golden相符/未覆盖说明。

总控将候选资料送权威身份owner，以真实库/serializer产生真正DTO/golden，再使用公开CLI验收。当前不创建/合并/增加任何生产公司，不改用户确认池、不派发公司快扫；SW身份、G2b/C06/G3/O01门不由本包关闭。
