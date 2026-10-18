# 生产任务载体的最小增量建议

状态：只读设计建议，不是新验收门、实施承诺或生产授权。2026-10-18；作者 `/root/production_node_review18`。本次未写实现源码、未调用 API、未改名单或数据库。当前工程节点已经完成；delegated-owner 候选不在本次设计范围。

## 判断

Task3 的“12题、2026-10-13、free_agent、零搜索、MiMo pack”应继续作为冻结实验入口保存。生产入口应新增显式 `iqs.company-scan-task/1.0.0` 和 `iqs.company-scan-profile/1.0.0`，复用同一个 Runner、RuntimePort、原 StockQA SDK/owner/费用账。不要修改旧常量来让旧入口“也能跑”。仅删除 IQS 工厂的12题检查不够：策略、证据接纳、计划/实绩判断、回放仍有冻结假设，会造成新日期表面生效、内部仍按旧日期判断。

## 一个任务需要固定什么

新工厂从**实际当前批准的 owner**构造任务，问题集合为 owner 原 manifest 的非空唯一合法子集。保存原题全文/语义 hash、module locks、完整 SubjectRef、实际 information cutoff、原5项输入引用、选中 route id，以及确定性执行 profile。总题数不受实验12题约束，但仍受原批准范围、请求大小/令牌和预算限制；超限在 claim/POST 前明确拒绝。

profile 最少只有：`protocol`、`mode=one_shot_packs|singleton_research`、有序 `question_ids`、确定性 `packs`、`pack_by=module|dimension|single`、`max_questions_per_pack`、原 `route_id`、实际 cutoff 和资源上限。packs 是调度元数据，不给问题改 ID，也不以旧 IQS_01 等别名给新问题指派事实领域。模块/维度取原题中已有字段；维度缺失时按模块或单题，不能猜一个行业维度。首先满足原 `lifecycle.question_pack_group_key` 的兼容条件，再在其内按 module/dimension 切包。

每包大小先保留 **1–12**，允许总任务超过12题。这样可立即复用现有 action-intent、submit_answers、patch 的每次12项上限，不必放大整套 wire schema。分包还要满足原 owner 批准的 pack size、原 provider 能力、token 上限。顺序、分组参数、原题 hash、profile hash 都进入 task/checkpoint；恢复重算必须得到相同 packs，不能因为当前配置更新重新分组。

## 具体最小修改位置

| 位置（Projects 根下） | 最小变化；旧入口保持原行为 |
|---|---|
| `invest-quick-scan/scripts/shared_company_task.py` | 保留 `create_native_task` Task3；新增单独 `create_company_scan_task`，仅从当前实际 owner/manifest/route 生成新载体。可把原题/主体校验提成共用纯 helper，不能减少检查。 |
| `invest-quick-scan/scripts/shared_company_engine.py` | 明确按**已知协议**分流 preflight：Task3 仍固定12/日期/MiMo；新载体验证原批准子集、profile、每包能力和实际 route。复用现有 execute/resume、pending checkpoint 和 native intent lookup，未知协议拒绝。 |
| Company `src/iqs_company_agent_lab/task.py`，新增小型 `scan_profile.py` | 验证/恢复显式生产 profile、深拷贝并锁定其 hash。旧 Task1/2/3、targets loader 和 limits defaults 不变；不能靠 `origin=owner_public` 自动升级。profile 只是数据，不能当 owner grant。 |
| Company `strategy.py` | `strategy_for_task` 增加精确生产协议分支，调用简单 `ModulePackStrategy`：取首个未完成原包，提交/修复也限本包≤12题。原 fixed3/free/evidence 策略和旧 QUESTION_IDS 投影不改。拒绝/未知状态仍终止或暂停，不自动换包重发。 |
| Company `runner.py`、`replay.py` | 共用一个小的“任务校验上下文”构造函数：旧任务返回原冻结值；新任务返回已锁 profile 中的实际 cutoff/批次。fresh、replay、resume 必须使用同一上下文，继续同一 Runner/state applier。 |
| Company `evidence.py`、`answers.py` | 新载体把实际 cutoff 的次日作为 publication-exclusive 边界。`EvidenceBoard.intake` 不能继续硬编码2026-10-14；`check_binding_semantics` 不能继续用 `FROZEN_INFO` 判断计划/实绩。保留旧默认；新 profile 的 board snapshot/epoch显式绑定边界和policy hash，旧 snapshot/epoch字节不加字段，恢复不可丢边界。 |
| Company `request_context.py`、`export.py`/`reporter.py` | 只对新 profile 显式携带/导出 `execution-profile` 薄 sidecar，绑定 task/run/问题/分包 hash，并校验后标注“生产扫描配置，非冻结实验可比组”。旧请求/导出不增字段。完整原题、schema、tool 定义仍进入稳定前缀，选中包/主体/证据进入动态部分；原1MiB/令牌上限继续约束。 |
| Runtime `src/iqs_agent_runtime_lab/port.py` | 四方法接口和原 SDK 会话可复用，无需第二个 bridge。新的 profile 只选择原服务已允许的 mode；缺会话/超范围工具/配置超 task cap 继续拒绝。需要做原 request/response/tool-result 兼容回归，不新增 HTTP 实现。 |
| StockQA `src/utils/quick_scan_owner_research.py` | 已能校验任意 task.questions 的原 contract/module/subject 和 owner 实际 cutoff，大部可直接复用。把 profile/选定 packs 纳入注册输入不可变检查；在每包派发前仍执行原 group/route/current owner guards。不要把原 `assert_provider_model` 改成信任 profile。 |

生产 sidecar可以复用原 research-run/metrics 的计算结果，增加清楚的执行配置标签即可，不需要另写一套报告或统计引擎。横向比较必须先对齐 profile 版本、cutoff、原问题 hash、module locks 和口径；不能因都输出 research-run/1.1 就直接与旧冻结实验比较。

## 可以立即复用与暂不支持的边界

1. **首个可交付切片：one-shot 小包/单题。** 任意原批准子集、实际日期、按模块/维度分包，单包≤12。MiMo 多题只在原 native pack 能力/批准允许时使用；其他已支持原 SDK 的 route 首先单题。换模型必须是原批准的 route；原 owner 不允许时走原 action/批准流程，不能修改现有 client/model 或凭 profile 静默 fallback。思考保持开启，原 immutable 回执、未知费用和安全可见输出规则不改。
2. **随后可复用 singleton native_session。** 新 profile 明确 `singleton_research`、每 intent 一个 work，继续原 session 登记/不可续刷 turn cap/每POST原预算与当前权限。不能因为“每包只有一题”就把多个不同 work 塞进同一 native session。进程重启只能回放已安全保存的回答；隐藏 conversation 和未完成 tool calls 不恢复，没有证明就暂停。
3. **仍不支持：multi-turn pack、过期 lease 答案续写、正式 search-proof checkpoint。** 外部证据可作为现有安全上下文参与研究，但不能冒充原 external-context/native search proof。首个切片 search cap 仍为0，先消费已有证据或如实 unknown；接原 search coordinator/proof 是单独后续能力，不是放开 profile 字段即可实现。

对缓存的最小做法是固定同一任务的稳定前缀与原题顺序，动态部分只放本包目标、当前证据与状态。不要为提高命中率省略原问题/评分锚或把其他主体证据混入。profile/原题改变产生新 task hash；恢复不能套用旧缓存。此处不对实际命中率或模型准确性作实验结论。

## 5个本质正反例（一次切片整体验证，不加小门）

1. 实际原 manifest 选17题，两个模块/若干维度，实际截止日非2026-10-13；按原合法 group 分成≤12小包，与同一 Runner 单题模式得到相同题目覆盖/严格 answer shape。跨题范围、篡改原题或模块锁必须在任何 POST 前拒绝；评分本身需另用真实证据评价。
2. 同一份2026-10-17发布证据，在 cutoff=2026-10-16拒绝、cutoff=2026-10-17允许接纳（非自动判可靠）；计划/实绩按该实际日期判断。fresh/replay/resume一致。旧冻结 fixture 的旧epoch/导出字节和结果保持。
3. 同一合法集合把维度缺失题回退单题，异 SubjectRef/不同原 pack group 不混包；非法多题 route 拒绝或预先生成明确单题计划，不能在失败后无记录静默降级。
4. 某包原安全响应落盘后OS退出；fresh process按原 profile、原 owner/intent恢复，新增HTTP=0。改 cutoff、包顺序、route、任一问题 hash，或原批准已撤销/未知旧发送，必须拒绝/暂停，不能重新发包。
5. 原单work native_session两轮与 cap，思考开启；第三轮超限/不同work/多题/session重登记不增额度，正式checkpoint缺搜索proof仍拒绝。旧 Task1/2/3、研究1.1和原盲测比较全部保持旧语义，不因新 profile 变成生产资格。

建议先做第1切片：原批准子集 + 当前cutoff + 动态小包/单题 + 原恢复，接入真实小样本实验。此后再接 singleton research 与搜索证明。无需再发外包卡、无需造新调度平台，也不应把2000家公司数量变成单公司任务上限。
