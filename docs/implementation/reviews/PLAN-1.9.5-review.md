# 实施计划 1.9.5：全局复核与暂停记录

日期：2026-09-26  
范围：完整实施路线、任务依赖、跨仓owner、组合式组件演进与向下兼容、receipt证据闭环、真实数据隔离测试，以及已知S04/S05实现状态。本轮仅修改本仓规划文档与规划结构校验器，不实施产品功能，不写外仓、不调用模型/API或处理公司数据。

## 结论

1.9.5计划已达到可审查、可按任务拆分执行的状态：103张任务卡、327个验收case、53条固定约束，最终门为G6。计划数据校验无任务依赖环，跨仓写入owner和阶段链仍保持分离。独立只读复核最终未发现剩余P0—P2。

复核没有把“计划规格通过”解释为产品实现通过。全部327个验收case仍为`specified_not_executed`；真实StockQA/StockWiki全链、联网搜索、公司数据、UI和真实数据E2E均未因本次审查而获得验收结论。

## 全局覆盖矩阵

| 领域 | 本次核查 | 当前执行边界/残余工作 |
|---|---|---|
| 公司/证券/分部身份及多挂牌 | entity、security、segment分层；来源、同主体多挂牌、母子公司、暂定身份和身份变更revision；不按名称/代码猜合并 | StockWiki仍是权威名单及身份owner；跨仓数据库与并发行为待对应W卡验收 |
| 组合模块、路由与版本演进 | 基础模块加行业、生命周期、周期/恢复等多轴选择；模块唯一owner、独立release/hash、锁定题义、确定性依赖闭包、冲突仅针对已选组合、候选不得付费派发 | S04/S05/S06实施及完整真实入口验收未闭合，详见下节 |
| 评分和纯信息事实 | 分数、状态、来源和事实分离；事实包可选、不得渗入评分；第一/第二曲线、产业链和恢复候选保留独立维度 | facts生产链需V13/V14/V15完整接通；本轮没有扩大事实题库运行范围 |
| 稳定优势与产业变化 | 品牌/渠道/规模等持久优势、迁移速度与失效机制、产业变革受益/被颠覆、低谷/困境与恢复条件分列；低分可保留关注标记，不替代风险判断 | 需依照冻结题库、来源与证据门实际运行；计划并不承诺模型判断准确 |
| 答案、模型、搜索与时间轴 | 有限答案/证据状态；实际provider/model、模型版本、信息时点、执行和搜索回执；横向比较须对齐方法和信息日期，纵向保存不可变时间戳 | StockQA唯一拥有问答执行、额度、费用和attempt；live搜索与额度回退仍未完成生产E2E |
| 刷新、接续、回退与并发 | 按字段增量、freshness与unknown冷却续扫；旧recipe和attempt先安全结算；影响范围不清时阻断；active ReleaseSet与组件资格分离，CAS/permit/POST一次性语义固定 | StockWiki/StockQA owner实现、双worker/真实临时SQLite和恢复测试待执行 |
| 轻资产存储及消费者 | StockWiki quick-scan SQLite独立命名空间为唯一可写权威，导出和UI为只读投影；主题研究/行业研究只读消费并查询同一画像库，缺能力返回unavailable | 不向company-wiki复制文档；跨仓迁移、导入ACK、页面及真实技能加载待验收 |
| 启动、操作UI与隔离测试 | 首次setup和持续start/status/stop/resume、用户排序的模型配置、断点续扫、一键启动、简洁结果UI、测试前后清理/路径围栏和零漂移都纳入任务与case | 现有规格要求正常快扫零公司文档下载；X09离线联调不能代替X10有界live验收 |
| 任务证据和独立审查 | 唯一case owner、跨任务`requires_tasks`、atomic assertion、独立review绑定源码快照、P01 receipt v2和G0—G6依赖闭包 | 新验证器和各仓receipt还未实施；旧回执在下节按历史证据处理 |

## 本轮复核发现与计划修订

独立审查最初发现两项P2计划歧义。第一，旧receipt v1只能作为`legacy_historical`，但依赖任务的关闭规则未区分当前通过证据和只读上下文；P01若要求P00先具有当前v2回执，会在receipt验证器尚未存在时形成启动闭环。第二，P01的最终自验日志若重新计入自身receipt正在哈希的证据集合，会引入自引用。

计划现以I53、RCPT-03和全局`historical_context_edges`收口。所有普通`depends_on`都要求当前receipt v2；历史上下文豁免需在全局allowlist和任务卡中双向匹配，路径/hash manifest必需，只能读不能放行前置任务。当前唯一allowlist边为P01→P00：P01可锁定现有P00 baseline作为只读输入，但绝不据此把P00标为当前完成。P01验证通过后按BASE-01/02重跑P00并生成新v2，再重跑C01—C07的全部当前case/assertion并生成新v2，最后由G0/G6按通常依赖验证。任何旧v1文件保留原字节、不补签。P01以两轮review和分离的hash方向消除自验循环：封存前实现review只绑定源码/测试snapshot并进入receipt core；封存后sidecar绑定sealed core/validator hash，封存后证据review再绑定core与sidecar，后两者不回写core或前置review。

`scripts/implementation_plan.py`现验证历史上下文边字段形状、必须是已声明依赖、全局allowlist精确双向一致、边无重复且端点存在。回归覆盖唯一边、未授权边、allowlist漏声明、未知端点、重复/畸形字段；这个校验器只验证计划结构，不执行任务，也不验证未来receipt运行行为。

## 可组合、可演进与兼容性检查结论

本轮从“扩题模块”扩展到完整生命周期逐层检查：

- 组件分别由一个owner发布，schema/版本/hash/能力声明独立；跨层运行的`ScanRecipe`冻结实际题义、路由、评分/事实/筛选、刷新、provider和执行限制。
- 兼容不是单一semver判断。声明需绑定精确producer release、consumer release与具体动作；UTC窗口`[valid_from_utc, valid_until_utc)`，不兼容、过期或歧义在副作用前失败关闭。历史读取、新写、付费派发、迁移、回退分别判断。
- 旧观察和attempt不可被新题包、解析器、lens或provider升级重写。新增字段只补增量；只改聚合规则或别名只重算派生投影，不重发模型。影响面不确定时转`needs_review`/`blocked`，不能扩大成全池重问。
- router/LLM可提出分类，只有证据和注册策略能把候选映射到已发布模块；人工override有理由/TTL。低置信度保留公司并仅运行确定通用与必要风险问题。
- 故障恢复先按旧冻结recipe和attempt做幂等对账，再决定是否允许新版本派发。provider结果不确定时禁止盲目重试、fallback或新attempt。
- UI、industry-research与analyze-theme-value-chain只消费权威查询结果，不另建可写事实库或复制完整模型/网页正文；消费端版本缺失显式返回unavailable。

实现层的模块契约分成三张卡：S04校验registry和归档release完整依赖图；S05检验历史reader及只对`module_id + artifact_sha256`可信基线开放的legacy字段适配；S06对本次选中集合递归展开依赖并以无向语义拒绝冲突。互斥候选可以共存于目录，选中冲突时必须在零模型派发下失败。这样发布、历史读取和运行时组合不会被一个笼统“模块加载成功”布尔值覆盖。

## 仍未关闭的产品实施问题

- S04归档reader的依赖图修复已经存在于工作树，独立复核曾确认它修复了`validate_release`接受自洽hash循环归档的问题；但MOD-14全部atomic assertions仍未转成完整固定自动测试，既有S04 receipt属于旧计划，不覆盖当前MOD-14。S04仍不可关闭。
- S05/MOD-17当前实现仍有按module ID授予legacy豁免的精确身份缺口；MOD-17规定的`module_id + artifact_sha256`可信基线拒绝反例尚待实现并复核。它仍是P1实施问题。
- 曾报告的350项产品全量通过没有与当前源码hash、日志和当前case集合组成receipt v2闭环，故不作为本轮放行依据。产品回归、本地case、独立review和完整receipt必须绑定同一快照。
- StockQA Q04、StockWiki W01等既有跨仓变更按各自已授权范围保留；本轮不新增外仓修改，也不重跑任何外仓/真实API测试。

## 独立终审与验证

独立只读审查分两轮指出上述依赖/自验问题，并在增加allowlist双向校验和明确P00及C01—C07重验顺序后复查。最终无剩余P0—P2，无新增任务环；审查者未运行产品测试，未写任何文件。

主线程本次最终验证：

- `python -B -X utf8 scripts/implementation_plan.py validate`：通过，103 tasks、327 acceptance cases、G6，`product_tests_executed=false`。
- `python -B -X utf8 -m unittest discover -s tests -p test_implementation_plan.py -q`：79项通过。
- `git diff --check`：退出码0；只有既存LF/CRLF换行风格提示。

上述是计划包/规划校验器的回归，不是S04/S05、真实LLM搜索、股票池、UI或跨仓产品验收。本轮到此暂停产品实施；恢复时从P01 receipt v2开始，再按计划继续S04 MOD-14测试和新receipt、S05可信legacy修复、S06 MOD-18闭包及剩余任务。任何后续StockQA/StockWiki写入仍遵循既有精确授权边界。
