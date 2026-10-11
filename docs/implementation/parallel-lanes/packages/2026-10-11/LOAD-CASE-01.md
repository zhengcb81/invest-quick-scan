# LOAD-CASE-01：全池负载、公平性、接续与费用案例

唯一工作目录 `C:/Users/郑曾波/Projects/iqs-load-case-lab`；编制时不存在。可新建独立仓，分支 `codex/load-case-01`。本包支撑O02/L03/X09的可复现负载和观察工具；不实现第二个队列、执行器、重试器、费用账本或公平调度器。

先读[共同规则](handoff-rules.md)、[输入锁](inputs.lock.json)、[模板](LOAD-CASE-01.handoff.template.json)。别的包/生产仓只读，无相互依赖。所有生成与分析离线，不调用LLM/搜索，不实际向provider发压力请求。2000仅合成容量，不替用户选择2000家公司。

## 目标与数据接口

交付有限场景生成器和trace分析工具。输入是锁中的现有作业/模型/预算契约、公开schema/示例与运维设计；复用字段/状态口径，未知adapter映射须列缺口，不凭猜测换成产品状态。

建立具名封闭 `iqs.workload_case/1.0.0`、`iqs.workload_trace/1.0.0`、analysis-report/collection schema：

- scenario：scenario_id/version、seed、UTC逻辑时钟、明确合成对象/字段ref、优先级/策略份额/限额/预算/单价定义、终止条件；logical_ref仅 `synthetic.*`，不得生成权威Entity/Subject/Work ID。
- 生成输入：声明的arrival、freshness/缺口、手动增加、stop/restart、provider明确拒绝/结果不明/晚到、ACK晚到等外部事件。**这些是声明事件，不是实际派发记录**；不要模拟实现一套scheduler把它们直接当成功trace。
- trace：有界JSONL事件，event_id、event_time、capture_time、run/work/attempt别名、provider/model/费用桶、event_kind、金额/币种/计量、source_ref。输入顺序与事件时间分开，禁止同一event_id不同内容；未来版本/非法日期/不完整trace显式拒绝或incomplete。
- provenance：`synthetic_fixture`或`owner_capture_unverified`，捕获的公共命令/组件/文件raw SHA可引用，但自报owner名不是认证。报告始终 `certification=not_owner_qualified`；真正执行资格仍由owner现有校验链决定。
- analysis：逐scenario的观测值/约束违规/unknown、统计分母、截断/缺事件/时钟不明，保留未结束的reserved暴露。不能从fixture通过声称真实全池公平或真实花费。

金额用decimal字符串/明确币种与费用单位，不用二进制float凑守恒。套餐请求/搜索credits/现金USD各列；未有单价不得填0。不要将provider/model名称当共同费用桶，桶归属由冻结策略声明。

## 场景组（约18—24组，不盲目扩展矩阵）

| family | 覆盖重点 |
| --- | --- |
| L01规模 | 10/200/2000合成对象×30逻辑字段；默认small，2000只按显式参数生成；流式有界、可重复、无全量大内存常驻 |
| L02公平 | 一批首次覆盖、持续热点增量、手动单公司插入并存；策略显式给首次覆盖最低份额/最大等待条件；不能用吞吐高代替不饿死 |
| L03新鲜度 | recently-updated跳过、到期字段、新增模块只新增字段、全fresh零派发；保留总分母和各类缺口 |
| L04并行 | 两/多worker的重叠in-flight、不同attempt、同work去重，收到明确拒绝后允许按原顺位换模型；未知请求不能自动改模型重发 |
| L05额度 | 5小时共享桶/窗口边界、明确quota/cooldown与本地并发上限、拒绝后下个顺位；不真实测50RPS，不把月credits当现金 |
| L06预算 | spent+reserved+remaining守恒、零价格/未知价格、成功搜索后模型失败、模型结果不明仍占暴露、重启不归零 |
| L07接续 | 已答未ACK只重投同一结果，不重问；late response/reconcile；重复事件幂等但错payload冲突；stop后排空或unknown而非删除 |
| L08边界 | 欠缺trace首尾、乱序capture、重复ID、不同币种、时钟跨度/请求桶缺失；拒造全绿和假零费用 |

公平性检查必须绑定显式策略和可调度窗口（eligible且非因预算/能力整体阻塞）；先输出未知/有效等待分母，不能在无任何派发资格时声称scheduler饿死。限额用冻结桶/事件时点，边界清楚，例如半开窗口；不能按requested model拆开绕共享桶。

## 入口和工程步骤

1. 核锁/新仓PWF/base commit。定义场景与trace协议，逐字段说明来源及尚无owner映射。先写手工可算正常trace与一处变异的RED控制，期望结果独立于生成器。
2. `python -B -X utf8 -m iqs_load_case_lab generate --scenario ... --size small|200|2000 --seed ... --output ...` 只生成案例/声明事件；默认small，已有输出拒绝。记录生成耗时/峰值内存的实际环境，不硬设跨机器毫秒门。
3. `validate --input ... --inputs-lock ...` 校验结构/引用/锁。`analyze --scenario ... --trace ... --output ...` 只分析已有trace；没有trace拒绝，不由generator自行补实际send/ACK/成功。发现违规报告后exit4，缺证标unknown，不把工具exit0当调度器全绿。
4. 至少四个独立手算基准：并发重叠区间、5小时边界共享桶、search-spent+model-reserved、重启/ACK重投零新增模型发送。包含更改一个事件后必须变成违规的负例；不能复制分析算法进测试或同函数生成expected。
5. unit：decimal/时间/重复event/边界/partial；integration：固定seed、大小有界、stream读写、错锁、拒覆盖；公开CLI E2E：中文/空格/随机cwd、small全链、2000仅合成容量、违规真实exit4/unknown报告。一次稳定相关全回归与一次集中review，其他组定向。

不得启动owner守护程序、修provider policy、对生产账本“对账”、发出请求或自动调整预算；只提供模板的未来owner-adapter说明，实际adapter接线留总控。

## 交回与集成

交 `content/scenarios/`、有限手工trace fixtures、schemas、CLI/测试与 `docs/handoff/LOAD-CASE-01/`。报告分开synthetic算例、真实owner捕获尚未提供、生成性能；所有模型/搜索/API0。大规模展开JSONL是自有临时产物，保留配置/seed/生成命令/摘要可重建即可，清理大文件，不保留公司文档或第二运行库。

总控后续以实际StockQA/StockWiki公开入口捕获trace并做映射/预算资格验证，再用于O02/L03/X09。该Lab交付不使这些任务、G3或全池门自动关闭。
