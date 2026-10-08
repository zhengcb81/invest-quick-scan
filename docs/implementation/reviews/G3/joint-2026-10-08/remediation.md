# 联合链整改 JR1–JR3

本卡属于现有C06/Q10/W05的大节点，不新增中央task/case或逐helper审查门。依据[实际验收](acceptance.md)。**先读本卡、验收、原回执与冻结1.0契约；不重做之前三包。** 未经对应源仓授权不能写；施工文档不授予权限。

## 起点、owner与允许范围

| Owner | 当前观察基线 | 本卡精确功能范围 |
|---|---|---|
| StockQA | master a39d7ea；软件b6eaa08；七项原未跟踪保留 | `src/utils/quick_scan_result_outbox.py`、`src/utils/quick_scan_work_store.py`；`tests/unit/test_quick_scan_result_outbox.py`、`tests/unit/test_q10_delivery.py`、`tests/unit/test_quick_scan_work_store.py` |
| StockWiki | master d253fea；软件cc587a8；clean | `stockwiki/quick_scan_import.py`、`stockwiki/quick_scan_observations.py`；`tests/test_quick_scan_observations.py`、`tests/test_quick_scan_delivery.py` |
| IQS总控 | Phase108结果，待本批提交回执 | 本卡/契约解释、冻结公开1.0及现有契约测试、跨仓定向回验/PWF |

StockQA已有用户全仓写授权，但总控本批截至交付仍只读；实施前报备、重查当前状态和writer归属。**StockWiki这四文件的新整改仍需人类明确授权。** 每仓最多一个writer；不同owner不改对方仓或IQS。不得动生产库、名单、个人配置、原七未跟踪项和镜像安装目录。开工重读HEAD/status，变化不是锁：卡内代码变化交总控重定基线，无关变化记录后保留，不能reset/clean/stash盖掉。

两个owner可在本卡公开接口冻结后分开施工。QA绑定API实现完成不等于SW ACK已合格；SW单侧测试过不等于闭环签收。writer在独占临时工作区测试，交真实commit和共同隔离证据，总控集中汇合一次。

## JR1：公共ACK与历史兼容（StockWiki owner）

1. **先RED**：用正常新导入、已存在/同包重放、缺实体、题义错release、观察/执行键冲突四种状态的真实公开CLI及ack_for原件，对IQS冻结ImportAck1.0校验；accepted/already_present/rejected/conflict都覆盖。不能手工删字段制造正例。
2. 本次优先保留公共1.0：十个根字段、严格consumer结构和既定错误taxonomy保持。**在新导入本地事务里生成并持久保存合法公共DTO**；local sequence、原内部reason、原引用单独保留审计，不塞到1.0根。不放宽additionalProperties、不覆盖冻结schema语义，不随便把schema_version改成1.1。
3. 公共error稳定映射：缺实体→missing_entity；未知题→unknown_question；unsupported schema→unsupported_schema；题义/scope/subject/身份版本链不匹配→lineage_violation；形状/分值等→invalid_payload；不可变观察/执行键冲突按公共immutable冲突码。内部原诊断原样留审计，不丢具体reason。公共状态/error组合必须满足schema，不能只改一条missingentity分支。
4. 新public DTO持久重放须完全一致（含ack_id/received_at），导入重复、丢回程后ack_for对账、重启和恢复都返回同一对象；不从当前时间拼新回执。
5. 历史已存enriched1.0保持原JSON/SHA/ID，**不能在读取时临时删除字段覆盖原件**。默认明确`legacy_wire_pending`/不自动delivered；如实现legacy恢复，先向总控提交严格注册策略：已知版本/完整字段形状、目标绑定、原ACK SHA、原诊断与审计、durable恢复DTO及stable replay。未获契约签认不自动兼容。禁止把待对账写成成功。保留旧terminal原ACK原样读取/重放。
6. 若选择公开sequence等1.1扩展，先由总控冻结严格typed新schema、能力协商和旧1.0读取，不能由owner单方面改协议；本卡默认实现原生合法1.0，不依赖新增字段。

## JR2：发送前绑定目标库（StockQA owner）

1. **先RED**：正确全部IDs/hash但store_id为qsobs_unrelated_target；ready与已写send_intent两种状态均不能delivered，完整work/head/events/attempt/费用前后不变。现有证据已两次实错。
2. 增加公开owner绑定入口，输入来自接收方公开owner信息/受信配置，而非incoming ACK。至少持久绑定component=StockWiki、namespace=quick_scan、具体store_id与delivery/head；返回/记录稳定绑定hash及来源。不要把新字段擅自塞进旧ExchangePackage1.0导致包hash漂移。
3. 绑定必须先于begin的send_intent，缺目标时明确阻断且不发送；ACK落定事务按事前绑定逐项比较。相同binding幂等；不同target或head不能在发送中/terminal悄悄替换；fallback/恢复不能猜目标。
4. 持久升级/迁移用事务与具名失败；旧terminal历史读取、原ACK重放保留。旧pending/send_uncertain缺事前目标证据保持pending/unknown，不从首ACK补目标；若要恢复须有明确、受信、可审计的迁移/对账流程，不能自动补造。
5. 新合法1.0原ACK全状态往返、同ACK重放、错误namespace/package/item/observation/payload/store及旧head都回归；新head不得被旧ACK落定。consumer实际值与绑定一致后才accepted→delivered。

## JR3：严格接收JSON（StockWiki owner）

1. 复用本批重复summary负例：最后值保持原值/原hash，无需重签却当前落库1。先写真正公开CLI RED。
2. 接收文本/bytes时，所有嵌套对象（包含数组内部对象）拒绝重复键，拒NaN/Infinity/-Infinity及1e400/-1e400有限float溢出；正常有限JSON保留。包级反序列化失败返回明确非零/具名JSON错误，零观察/ACK项写入；不退为compact、默认5分或吞异常后继续导入。
3. 直接dict入口不能绕过非有限/shape检查；dict无法表示重复键，不能用dict用例代替原始JSON文本用例。release外部文件等相同接收路径若使用同loader也保持严格，不另外复制实现。

## 集中验收与交接

- 开发期只跑受影响单元/集成。两个owner完成后，总控按本批固定原输入做一批真实CLI生成→SW导入→原ACK→QA绑定/落定→重复/丢ACK恢复；独立q8 unknown重启与阈值查询仍独立，不依赖故障造成的状态。
- TDD关键断言：公共四种状态schema合法、原回执重放；正确目标成功、所有错误绑定/未知版本/未知字段原子拒绝；旧terminal/迁移rollback；deep duplicate/非有限零写入；恢复额外模型/搜索/付费0、原attempt/包不变。不为每个helper新设审查，不重复未变全仓/UI。
- 正向仍为合成软件fixture，实际身份保持provisional；真实身份/事实owner golden另交，不造verified正例。保留原低分/unknown/null/不适用/watch与完整长body。
- 交付每个owner实际result commit、基线/状态差异与授权来源、精确changed_paths、版本/API说明、全部实际argv/退出码/raw边界、fixture provenance/hash、公共golden生成命令和逐文件隔离清理证明。历史共享TEMP不能以新根cleanup追认。
- 收到交付后一次集中独立审查；原红/控制器错误不可删除。G3/L03/F05/THIN/双owner恢复未由本卡自动闭合。总控负责PWF、镜像同步与跨仓整合。

## 本批另留能力缺口：requested与resolved

J03的HTTP model=B、请求仍A不是真B路由。当前严格实际==请求会阻断checkpoint；不能改HTTP actual为A，不能直接删相等断言。后续另在现有Q10模型追溯链处理，不拖三项联合整改：

StockQA核心范围为`src/providers/llm_client.py`、`src/utils/quick_scan_work_transport.py`、`src/utils/quick_scan_work_store.py`、`src/runners/llm_runner.py`，及现有client/transport/store/runner/subprocess tests。请求model_requested与HTTP model_resolved分别记录；resolved必须在response_available事务绑定原response/receipt SHA并不可变，checkpoint严格比durable resolved，搜索证据与模型解析策略分开。是否允许已注册alias解析必须显式配置；任意A→B仍可honest mismatch_blocked。旧attempt缺resolved不可由requested补造，历史terminal只读；不扩大整个Q10，不自动启收费比较。
