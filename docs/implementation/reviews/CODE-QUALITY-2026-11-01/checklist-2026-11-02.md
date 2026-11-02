# 整改清单逐项核对

核对日期：2026-11-02。原清单是同目录 `report.md` 的发现1—10及随后实测遗漏，另核 Dashboard NEW-6；不重做全项目验收。主控亲读代码、原日志与原账本，三名非对应实现作者交叉核对。本文是现有整改的对账表，不新增施工支线、审批或凭证。

## 总结

**原10组已全部按原发现的软件范围闭合；本轮补齐原5/8/9/10，最终safe无CP恢复原owner/SDK E2E1P/656.77秒及集中独审通过。** 上轮把这些项合称“源码整改已完成”过宽，现更正。测试通过不代表测试没覆盖到的整条链已完成；以下每个子项分别判断。这不是全项目完成率。

|原发现|准确状态|尚缺什么|
|---|---|---|
|1 已付回答恢复|已完成原软件范围|原actor/撤权/主体/响应与预算材料仍检查；不放开未知重发|
|2 共享额度|已完成原软件范围|没有真实共享整公司36题/18包完成证据；请求数足额不保证未知token和网络耗时|
|3 UI锁及分页|已完成原软件范围|锁外慢读、冻结部署、写CAS及跨工作区分页已有覆盖|
|4 超时冲突|已完成|设置与owner使用同一规则|
|5 可选草稿故障隔离|**已完成**|可选读取/形状/嵌套坏容器局部降级，原子快照与未知文案；必需bank仍正常失败|
|6 跨期间指标|已完成原软件范围|未知指标ID仍应拒绝，不能把本次模型命名违规当坐标修复失败|
|7 模块元数据|已完成原发现要求|旧读取兼容；同义critical元数据补齐的same-method升级另有限制，见下|
|8 模型能力及顺位|**已完成本轮软件范围**|SDK同源能力；原1.6顺位、真实route/预算原子cap与已付safe无CP恢复E2E通过，旧确认不扩权|
|9 薄边界|**已完成**|生产task/engine全部改接QA公开context/transport/validation；AST边界与语义回归|
|10 实验假设与旧工具|**已完成**|指定workspace/work库与caller相对路径、真实HTML、历史检查标签；未指定work则明确未检查|

整改前核对源版本（历史基线，最终提交见PWF）：IQS `758ee3b`；StockQA `2e4f01b`；StockWiki `381811e`包含本组`719520b`；Company Lab `d1d92a2`；Runtime Lab `5839ef4`；原UI `iqs-question-bank-ui-lab`为`8fc9072`。IQS外来10/10 README保留，其他本组所核源仓tracked干净。沙箱git status误报非worktree后用已授权外层只读核实，没有checkout/reset。

## 逐子项核对

源码路径以IQS为默认；`QA/`、`SW/`、`Company/`、`Runtime/`、`UI/`分别指上述实际仓库。测试名为已存在的针对性覆盖，不意味着本次全套重跑。

|原项与子项|结论|实际代码与验证|
|---|---|---|
|1 委托到期与已付保全分离|完成|SW `quick_scan_refresh_delegation.py:378,568`及approval `:132,149`；`test_paid_response_inspection_survives_expiry_and_new_model_policy`及actor/revoked负例|
|1 只保全原已收响应、不新claim/send|完成|QA `quick_scan_refresh_admission.py:312,333`、execution `:143,360`；`test_paid_recovery_requires_known_original_response`、`test_paid_recovery_session_cannot_claim_or_register_new_send`|
|1 过期leased safe与SDK初始化顺序|完成|QA execution `:247–271`先设恢复模式，Store `:4575–4620`核原物理响应/token/epoch；初始化与过期原lease保存两用例|
|1 分类期限、原anchor及截止日|完成|QA owner_refresh `:258,451`沿原anchor/raw/binding；真实IQS manual override到期、旧分类日期不覆盖scan cutoff两用例|
|1 混合scope和分母|完成|QA execution `:184–212`核原scope，只物化原work，保留original_registered_question_count；原mixed-scope测试|
|1 UI恢复不把调用者布尔当许可|完成|`dashboard_execution.py:454,519`读原registered recovery；paid permission helper、native verified leased scope及unverified拒绝三例|
|1 outer日期缺省与原非首选路由|完成|QA原parser只有outer缺key才沿inner；显式null/冲突拒绝；非首选无key原route恢复用例，不因新首选改写历史|
|2 生产资源脱离实验8请求|完成|Company `scan_profile.py:66–115,181–219`先分packs再派资源；36题18包默认足额，冻结实验LIMIT_CAPS仍8|
|2 显式模型请求cap不足先拒绝|完成|同模块`:103–110`及`test_insufficient_explicit_request_cap_rejected_before_any_transport`；没有把未知实际token消耗说成已预测|
|2 接续原task/资源/控件/计数|完成|QA shared entry先读原task；旧8192不被新32768覆盖；原Runner cap1保持、counter0→1，原CP不改|
|3 慢只读锁外、写CAS保留|完成|`dashboard_service.py:421,468`；`test_slow_owner_read_does_not_block_setup_or_pause`|
|3 读取冻结部署视图|完成|同文件_read_view深copy配置；`test_read_keeps_original_deployment_during_config_change_and_snapshot_cannot_cross`|
|3 分页不得跨工作区|完成|同文件`:568–586`及old/unbound snapshot、cross-workspace测试|
|4 设置与owner超时一致|完成|`dashboard_owner.py:24–29,111`公开同一规则，service `:115`复用；saved_timeout与bounds_agree参数测试|
|5 后端草稿局部降级|完成|service `_drafts:403–419`；HTTP坏JSON/坏结构/读取异常9例保正式结果|
|5 前端启动隔离同一坏草稿|**完成**|UI77d372c：读取/JSON/形状/嵌套容器局部降级；坏可选源不崩溃、不显示假无记录；原子重载，必需bank坏仍失败。独审真实ESM5反例及7P/16子例|
|6 IQS与QA统一指标坐标|完成|IQS `metric_coordinates.py:12–34`与QA同名规则AST一致；ID/period_start/end/basis/currency共同定位|
|6 真重复和模糊期间仍拒绝|完成|standard_answers `validate_content`及原QA验证：同坐标换措辞/证据仍拒，重复缺日期/单位冲突仍拒；旧单行未知期间可读|
|6 多期比较不再取最后一行|完成|standard_answers `compare:412–490`按ID聚list再按完整坐标配；2023/24对24/25保留3行；原部分重叠及完整双年测试|
|6 fact内指标经济范围独立|完成|各fact item独立校坐标，不把不同事实行混为重复；`test_fact_items_keep_their_own_metric_scope`|
|6 质量聚合不静默吞多期记录|完成限定行为|scoring_rubrics `:168–175`建ID字典前拒重复question/observation/construct；它按单快照每构念一条聚合，不将多期偷偷取末值或平均|
|7 新diagnostic中性映射|完成|question_manifest `metric_mapping:33–69`保留framework、新未知归diagnostic；旧冻结schema保留原读法；新framework及旧manifest测试|
|7 新critical冻结、缺整行仍风险|完成|scoring_rubrics `aggregate:226–288`读冻结critical，缺行仍unresolved；新critical core、旧rubric fallback测试|
|7 旧profile入口边界明确|完成|旧profile数量限制保持兼容入口说明，多业务引导原route；未宣称旧profile本身已无限扩容|
|8 共享入口消费SDK能力|**完成**|QA d1d22cc：研究SDK构造与公开能力复用同一纯函数；普通web_search不冒称final_json研究可用，native/external通道分别验证；新顺位发送前跳过确定不兼容目标|
|8 32k贯通、旧tools16k兼容|完成|QA ResearchChatSession`:269–283`沿原应用上限，Runtime新1.1/旧1.0分支；SDK40P、独立实际函数4P、两pack32k软件E2E|
|8 共享自动跨模型顺位|**完成本轮软件范围**|1.6原确认/完整targets与binding5冻结；原runner实际route，已结拒绝才继续，已完CP不重问，原budget原子总cap不重置。两模型E2E1P及最终无CP已付恢复E2E1P/656.77秒；旧确认不扩权|
|9 UI不管理QA私有连接|完成|dashboard_prepare `:211`调用公开continuation_binding_snapshot；QA原RO事务自管。atomic/detached/failure closes transaction用例|
|9 公开脱离对象的task输入|完成|QA `quick_scan_company_context.py:13–50`纯copy投影，production factory/preflight消费；projection detached/no I/O测试。QA仓内私有读取及legacy研究路径不误算跨界|
|9 生产engine全部私有接口收口|**完成**|生产factory/engine改用company_scan_inputs、split_standard_answer_transport、validate_registered_inputs、validate_company_scan_task；AST禁止私有穿透，原transport28种结果/异常一致。legacy研究task保留旧合同|
|9 delivery明确参数及两import环|完成|dashboard_delivery `:55`不再拿整个Gateway；error拆dashboard_errors；module_registry/routing共同依赖纯routing_contract，无上述反向环|
|9 纯构造/getter去重复current核验|完成限定范围|QA bind_task_owner_binding/client_for/attempt_observations、engine纯preflight减少重复；真正generation/commit仍核当前权限，不声称所有检查只运行一次|
|10 新部署中性默认与模板|完成|dashboard_service defaults `:65–78`工作区/发布目录留显式未配置；原defaults/template测试不再指Alphabet实验|
|10 旧subject写生成器退役|完成|owner_admission_subject只解析旧参数后明确retired，无读库/写库；legacy_apply测试|
|10 机械检查复用原合同|完成此子项|financial_mechanical_check接受显式workspace，HTTP来源、多期和成功fact items与标准一致；HTTP/多期、fact、pure import三例|
|10 身份审计无公司或000002豁免|完成|verified_evidence_audit导入纯化，删除PRE_EXISTING/公司名例外；原roster案例明确无证据仍拒|
|10 旧one_click的provenance两库|**完成**|IQS d168425：显式workspace推导观察库，--work透原work库；无work明确skipped/未知不假通过；caller相对路径先resolve，原SQLite/CLI正反例与字节不变|
|10 旧金融HTML链接|**完成**|显式--html实际生成并建输出目录，字段HTML转义；测试运行真实CLI核产物，仍仅机械检查不授金融资格|
|10 旧preflight标签|**完成**|旧固定实验检查单列标历史，不当当前工作区检查或日常扫描门；真实入口回归|

## 后续实测遗漏与交付范围（整改前核对记录）

|项目|结论与证据|
|---|---|
|构造失败不得先claim|已修。Runtime port`:364–366`先_resolve_session/controlled校验，实际step仍在原generation_scope；构造失败/controls mismatch/当前撤权/无budget四反例通过|
|精确原未发送lease释放|已修。Store release_unsent只接受精确Lease，sent/unknown/safe/CP/未结拒；epoch及旧worker fence保持；原独立13P|
|只读not_sent分类与接续|已修。原RO快照核同epoch事件/native intent优先；replay_only/已有receipt拒新发送，原CAS仍核；独立getter27P、接续63P及124P相关组|
|成功子包先保存|已修。原subset safe/receipt/语义逐成员保全，原entry仍incomplete、不发布完整export；两pack原owner/SDK32k软件E2E1P/396.47秒，第一CP保存、第二401保持失败，重入0HTTP|
|真实短证据实送|已证实。原pre-send CP/task/request builder/SDK纯构造hash等于实际intent payload；两年短原数和unknown published=null均实送，thinking enabled/max32768。不是只看到配置或软件替身|
|gen7金融内容、CP/ACK/缓存|仍未闭合。FCF两年数值/算术改善，但未登记年份后缀metric_id拒绝；分红总额/范围、归母与合并归属、方案最新状态仍有限制。raw保留，不改分/不重发。gen6早间delivered/CP1不变，gen7仍leased/response_available/CP0；账本87HTTP/US$2.053896、0在途/未结，本次核对无新增费用|
|普通配置恢复|已核原prepare对象及policy原字节恢复，pack2/thinking/max32768/shared=null/refs=null、60包保留；本次核对不写配置/原库|
|测试清理|本轮明确自有外层TEMP已清；前次未定位的AppContainer测试目录不能称全部清理。原报告的笼统清理措辞应收窄，不为此新建清理凭证门|
|Dashboard NEW-6|最终候选定点通过。5scope判断+实际TS AST/JS6深链精确observation_resolved、原SW32P；Dashboard代码e7ce9ae/文档edd964b，service3eb99cd/UI6f0391e/SWb3084ff。未代签D00并线、浏览器或E07。原复测报告及本地result.json已亲读|

额外兼容限制：scoring_rubrics的_signature/validate_upgrade直接比较core_basket原dict；旧rubric补上与legacy有效语义完全相同的critical布尔值，聚合结果不变，same-method升级仍要求新method_id。旧读取兼容与原critical风险修复通过，不等于这类同义元数据升级已经平滑支持。当前8766未调用该聚合器，不扩成新产品阻塞。

## 测试证据与局限

亲读既有日志：`runs/code-quality-fix-2026-11-01/focused.log`为154P/76.44秒；同目录`native-scored-full-owner-sdk.log`为1P/744.04秒；`runs/shared-partial-finalize-2026-11-01/main-units.log`为124P/17.47秒，`native-partial.log`为1P/396.47秒；`runs/new6-retest-2026-11-01/`内SDK/inspection63P、partial59P、unsent13P、getter27P、not_sent63P及actual-preflight4P。结果有重叠，不累加成总通过数。两packE2E不冒签其后写的not_sent分支，wire替身不冒充金融准确性。

本次另做纯内存能力反例与UI原store mock fetch反例，无真实网络；只针对未能从原记录直接闭合的6/7、UI/旧工具做小批量定向复验，不跑小时全套。本次指标/元数据20P/32.07秒来自工具实际结果，没有另存文件日志，自有TEMP已清；另一UI/旧工具pytest尝试未得有效断言输出，已停止、不记通过。实际Node反例有效，不能拿旧154P执行模块补签前端boot。准确选择与环境限制见progress。

## 接续顺序

本轮四组已完成，不再重复实现或重跑长例。新增paid窗口真实原owner/SDK测试1P/656.77秒，独审尾组28P；边界与提交见[最终结果](remediation-2026-11-02.md)。下一主线按根PWF回到原小池回答质量。金融/gen7内容、规模、F05与消费者/配套仍未完成，不用本轮软件测试代签，不新发支线或增加门。
