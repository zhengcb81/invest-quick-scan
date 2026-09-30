# S06 第二段实施交接（2026-09-26）

状态：**实现候选已完成本轮离线测试，等待独立审查；未将S06整卡标verified。** 此报告由实施者提供，不代替独立审查。中央task_plan/progress/findings没有由本代理改动。

## 已完成

1. `question_sets.py` 接入route v2：新增 `compose_from_route`；直接 `compose` 同样要求被冻结的profile/package、当前可信UTC时钟及独立expected decision ID。legacy ROUTE_01/严格validate_profile保留，不接受v2绕过成普通profile。
2. 策略为router **2.1.0**、policy schema **1.1.0**。保存48模块机器策略、历史2.0行为、native请求协议与部分派发规则。原2.0包的固定request prompt SHA仍为 `6b35db51280523a71a860d82152054f95ce565cc534da0ca85cd1f05ba056740`，有真实历史包回归。
3. `ROUTE_02` 采用现有StockQA native外层question_id/entity_id/company_name/status/score/description。score只表示分类证据充分度，不进入公司分数；重复key、身份冲突、布尔分、unknown配占位5等拒绝。独立回执仍须匹配prompt、实体、日期和实际搜索。CLI只组装/解析，不调用provider。
4. 新CLI：`publish-routing`（默认只归档）、`routing-v2-request`、`resolve-route`、`compose-route`。输出已有文件时拒绝覆盖；未知模块或非法候选在写输出前失败。
5. 必需风险题进入真实选题和预算：DISTRESSED_01/02与RECOVERY_01—04不能被可选补充题挤出。manifest冻结完整route、policy/package、原执行校验时间及expected ID；重新执行使用当前时间，历史读使用原校验时间。
6. 任一必需主轴低置信/缺失/冲突时，`eligible_module_ids`收窄为common＋必需风险，状态为`ready_common_and_risk`；已核实的行业等分类仍保留在module_decisions。未知类型不能借用高置信行业扩大派发。伪造该列表重签hash仍被本地一致性校验拒绝。
7. 多业务不截断；可兼容且确认边界的full可覆盖三行业，否则保留分部待办。不制造segment身份。事实来源、重大性门槛、迟滞、周期与恢复规则沿用第一段说明。

## 实际通过的组合与CLI检查

| 固定场景 | 公共入口实际结果 |
|---|---|
| 半导体扩张 | quick 28、full 34；均恰好24核心；两种模式核心method相同；类型替代锁为IQS_03→OPERATING_02、IQS_11→OPERATING_01 |
| 成熟周期低谷 | quick 34、full 42；保持mature，追加4道诊断recovery；两种模式核心method相同 |
| 困境成长 | 完整quick 34；预算24写入前拒绝；预算30实发全部6道风险/恢复题，4道可选题列deferred |
| 三项重大行业 | quick请求full或分部；确认兼容scope的full包含全部3行业；legacy profile仍拒绝3行业 |
| 缺搜索/部分分类 | common-only为24题；已知困境为common+distressed+recovery共30题；不伪造type/stage/other |
| 跨轴低置信/冲突 | 保留半导体分类证据但只派common；type冲突且有已知困境则只派common+必需风险 |
| TTL与历史 | 到期瞬间新导出拒绝；旧manifest继续可读；删除route绑定、删除expected ID或篡改原执行时间拒绝 |
| 原生CLI链 | routing-v2-request→native候选解析→resolve-route→compose-route，输出28题并保留实际模型、实体、prompt/decision身份 |
| 绕过与坏输入 | 直接compose省略v2快照/可信时钟/expected ID、改profile、未知ID、重复JSON key、错误内外身份等均在产物写入前失败 |

## 测试记录与隔离

最终命令：

```powershell
python -B -X utf8 docs/implementation/reviews/S06/run-first-segment-offline.py full
```

**最终全量：296 tests passed，0 failures / 0 errors / 0 skipped，169.712秒；TEMP_CLEANED True。** 原始日志：`second-segment-full-final-2026-09-26.log`。包括S02原有消费端与真实StockQA CLI离线stub回归、本轮16个纯路由测试及11个组合/CLI测试。native链没有联网或付费调用。

保留了两个中间失败记录，未隐藏或将未跑通的套件称为通过：

- `second-segment-first-integration-2026-09-26.log`：10个初始组合测试中9通过；唯一失败是实施者把既有operating替代ID断言错写为IQS_02/10。按已存在的归档题义修正断言为IQS_03/11，没有改题。
- `second-segment-full-2026-09-26.log`：296测试，0断言失败、2错误。错误均来自review runner把Windows的`subprocess.DEVNULL`设备`nul`误认为临时根外文件写入。仅在runner中允许精确`os.devnull`，没有跳过或修改生产/沙箱断言。随后重新跑完整296测试全绿。
- 第一段五个内存故障注入红测及70个回归日志仍保留。第二段固定坏输入/预算/TTL/派发反例由真实compose和CLI测试覆盖。

runner统一TEMP/TMP/CWD、禁用bytecode，禁止socket与未审查子进程，禁止临时根外文件变更。完整套件中仅放行已读过的三类离线沙箱子进程：短暂sleep用于进程归属检查、TEMP相对文件写入、两端均在TEMP的junction；另允许OS空设备。所有这些测试最后均通过，临时根已删除。外部StockQA只读导入，测试输出/日志留在唯一TEMP并清理；provider返回值使用既有fixture stub。日志中“正在调用API”是已有stub测试的业务日志，不代表网络调用。

S02原测试区逐字节重建SHA仍为 `7b9ba65164b09c2aa40993bdfd6e4233207247f237a3ca89f24e82630a0f5107`，与独立审查通过的原文件相同；本轮只追加S06测试区。既有S02回归没有被弱化。

## 新候选包与历史保护

- package：`pkg_be20531b533d7db712c4ff8d42d21b6889bdbf3a65c4ee399bfbe860bb0e8418`
- release：`modrel_8f5c8bf1b28e6e36e650af246b0e6730bb3c86265b38cbea1d5c1b81c624f945`
- package文件SHA：`dbba8d524a483e820a392c7c8024f3a3f8f1ee881813ad0fcc1744c9a245bdb0`
- release文件SHA：`f487f554befc80c7e20e4ca61f0cab0abaa8f40f2c977571c83b85a6e81346d3`
- 策略归档SHA：`eef827ab1c7dedd671cd6d40eb7e044c0b9c3e19a9727288493abb453f2c7096`

实际调用activate=False，仅新增上述package、lock、policy三份文件。**56份已有release JSON逐字节未变**，包括S05三个包和第一段2.0候选包；当前指针仍为S05 `pkg_24f079…`，未切换生产版本。完整逐文件清单及前后对照在 `second-segment-snapshot-2026-09-26.json`，发布回执在 `second-segment-candidate-publication-2026-09-26.log`。

## 独立审查关注点与验收边界

请优先从实际公共入口重现：跨轴低置信/冲突后的eligible收窄、预算30的真实六题保留、到期后历史manifest与新导出的区分、删除route/expected ID的绕过、原包字节及2.0请求重现、native CLI的实际派发。所有来源URL、identity_ref、verified_facts、provider回执和用户授权仍由上层受信任入口提供；本模块不联网验真，不提供签名或第二套存储。生产入口需要独立保存的expected decision ID，不能把调用方自己重签的hash当成可信来源证明。

本次只完成本仓离线路由/组合/CLI实现候选；实际LLM连接、持续扫描/接续、跨仓存储/UI与整产品一键运行仍由对应任务验收。没有修改中央计划文件、没有标记S06整卡verified、没有激活新包。源码已冻结，等待独立审查。

## 最终源码与日志SHA-256

| 文件 | SHA-256 |
|---|---|
| `docs/implementation/reviews/S06/run-first-segment-offline.py` | `9dce1ae5dddcf5630f3b11d75513883939b3b5fd4d86e72a574f1569c6ed3bf3` |
| `docs/implementation/reviews/S06/second-segment-candidate-publication-2026-09-26.log` | `abaab02abe084b6dc21e6b77909f6560991d6f25ec93bc8fe04ae31fe9fe2f9b` |
| `docs/implementation/reviews/S06/second-segment-first-integration-2026-09-26.log` | `66451ff72d4faf7f6b75cbfcc7cebccdee7c7c9770c281d9647c0d269d0a7cb9` |
| `docs/implementation/reviews/S06/second-segment-full-2026-09-26.log` | `faabdb1f2aad00c388bdef1718802bb90e002784473b16f77aedf8dec2af1f57` |
| `docs/implementation/reviews/S06/second-segment-full-final-2026-09-26.log` | `f69df7bdd5ea2352ae4cd031011e7e46c93eaa8f622e1ab0874c8f2d50bab968` |
| `questions/routing-policy.v2.json` | `2fdd85723d4031c5f91094a6ae6968ae05d46b063cebd3fd5e8882488f0f55a7` |
| `references/routing.md` | `597e221d7de690ac4635ea8796b70ba2687ef2ab3c09ecac9a317e03759788c2` |
| `schemas/quick_scan/module-release.schema.json` | `6265d0c9c64ce40f25ca1d0906183941e134b868821c1d8e3ed5c83d9ab24601` |
| `schemas/quick_scan/route-decision.schema.json` | `008185fe4550a204099eefc34a155d9f69c0375fa1a77f2632c6747dc12ec036` |
| `scripts/module_contract.py` | `ad9d4621e20d49ffc238167305429466ac00e50178b1c9513f001170fccad914` |
| `scripts/module_registry.py` | `ad38a9e7ce302b84f45569d276210e43ec84b7d67547540424ac640a57ea5a03` |
| `scripts/question_sets.py` | `580b44d5c5408fb3bdabfd48c8306ccb5f520b93d7ba9bcb0404fceea994b3f5` |
| `scripts/routing.py` | `9286b0bad8c931ea4b73a72aaaa3517422dbea5fc481257f38b85afb28305b7e` |
| `tests/test_question_sets.py` | `d85e67d633f8c9a98cb972c4ceb5c676fcb0be60295d64f56e96a74f2de0924a` |
| `tests/test_routing.py` | `75592f97c38a48124823f0ef39b873a69315663311b9c689ef63c4586628c02b` |

