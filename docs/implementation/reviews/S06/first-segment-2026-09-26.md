# S06 第一段实施交接（2026-09-26）

状态：**partial / 待独立审查和第二段集成**。本报告是实施者的测试回执，不是独立审查；未将 S06 整卡标记 verified。

## 1. 已实施范围

- route schema 增加严格 v2 分支，保留 v1 历史分支；v1 不能套用带 v2 策略的 release。新增 package、身份引用、冻结 profile、周期/恢复、来源与模型回执、逐模块证据输入、派发计划及可信决策时间。
- 新增唯一编辑源 `questions/routing-policy.v2.json`，对现有48模块机器策略全覆盖。新模块必须先满足 S04 activation/注册要求，还必须有已知谓词，政策不能降低模块声明的置信门槛。
- release v2 锁定归档策略的路径和 SHA-256；package 经 release 绑定。新增 `load_routing_policy`，读取包内归档而非可变源；修改策略必须增加 router 版本。publisher 支持 `activate=False`，保持原默认激活行为兼容。
- `scripts/routing.py` 仅执行纯决策、请求组装、快照与执行校验、预算检查和差集；无网络/LLM客户端/存储器。
- 没有修改 `scripts/question_sets.py`、`tests/test_question_sets.py`；它们的本轮稳定哈希仅作为消费端交接上下文记录。

## 2. 固定口径与已验证行为

| 场景 | 第一段实际断言 |
|---|---|
| T1 半导体扩张 | 选择恰好 common/operating/semiconductors/scaling；候选乱序不变；未知ID拒绝；A/H挂牌保留同一entity，证券上下文各自记录 |
| T2 成熟周期低谷 | mature保留，cyclical正交，追加recovery四题；价格下跌证据不触发；周期位置与恢复理由进入快照 |
| T3 困境成长 | scaling保留，distressed+recovery叠加；两道困境题与四道恢复题列必需；24题预算拒绝、30允许纯预算检查 |
| T4 多业务 | 三行业不截断；quick要求full或分部；full仅明确兼容边界才ready；重复业务标签、冲突类型/阶段进入待处理，不创建segment身份 |
| T5 缺搜索/TTL | 缺客观证据仅common确定；仍有可信困境证据则保留风险；未知不补other；独立搜索回执绑定prompt/entity/cutoff；到期瞬间拒绝新执行，历史仍可读 |
| 新投资视角 | 模型事实不能启用lens；须显式用户授权与TTL；不能通过lens授权对象改写另一模块身份 |
| 门槛/迟滞 | 收入/毛利/投入资本15%；承诺capex/约束订单20%；存续关键性或有证据重大事件独立触发；10%—15%保留，三项可比基础分母均低于10%连续两期才退出；缺分母不猜数 |
| 商业化前 | 可用有来源的主要开发项目触发行业，必须确认为pre_revenue；不伪造百分比 |
| 人工否决 | 客观困境/周期触发仍存在时，否决恢复检查明确报错，不静默删mandatory题。该语义已与主代理确认 |

当前纯预算检查不等于已打通问题派发。T1 quick=28/full=34、T2 quick=34/full=42、T3完整quick=34，以及预算30时真正保留六题并延迟可选题，均须第二段在真实 compose 入口完成断言。

## 3. 实际测试、红测与隔离

复现命令（PowerShell，从项目根运行）：

```powershell
python -B -X utf8 docs/implementation/reviews/S06/run-first-segment-offline.py mutants
python -B -X utf8 docs/implementation/reviews/S06/run-first-segment-offline.py regression
```

- 真实初始红测：在增加v2 schema前，`test_v2_policy_common_and_unavailable_sources_are_representable` 通过 `mc.seal_route_decision` 报 `ValidationError: '1.0.0' was expected`。它不是缺函数/ImportError红测。schema契约异常仍为 `jsonschema.ValidationError`，业务一致性错误用 `ValueError`。
- 最终快照的五个内存故障注入全部被固定断言杀死：顺序泄漏、股价冒充周期、预算无检查、多行业[:2]截断、执行校验忽略当前TTL。结果为5组预期assertion red，0个测试错误；这些是明确故障注入，不冒称生产旧bug日志。
- 最终隔离回归：**70 tests passed，0 failures / 0 errors / 0 skipped，97.788秒**。其中16个S06测试，另54个既有module_contract/module_registry/standard_answers测试。
- 最终日志分别为 `first-segment-mutation-red-final-2026-09-26.log`、`first-segment-regression-green-2026-09-26.log`。第一次中间红测日志保留但不作为最终快照证据。
- runner将TEMP、TMP和CWD设置为唯一临时根，禁用bytecode；Python audit hook禁止socket、subprocess和临时根外测试写入/文件变更。每次运行都报告 `TEMP_CLEANED True`。报告日志由外层shell写入本报告目录。未联网、未调用付费provider、未写外部项目。
- 已保存发布前后逐文件SHA-256到 `first-segment-snapshot-2026-09-26.json`；核对的63个原有/源码文件没有变化。发布只新增下面三份内容寻址工件。

## 4. 未激活的真实候选包

- package：`pkg_5c7facbfd9b772130e3fb5150d2c4d390083e72570b28c82cc4ab67151fd881f`
- release：`modrel_e12314434ad50692ed0a8a16ee2834e528cf47a9ebb6a7e9a692e71e3cf42741`
- policy归档SHA：`0c834ed20a8a87dc0fb95f315c7154d1cb949b13f10f4d298f1875a031bdcf8c`
- package文件SHA：`68170cf56ea74dabee349554c228a13a5ac76fc5ed88ebf78b14f874d7bc9a64`
- release文件SHA：`264523dc221078a45101a0e7875797b1dd728977a74feac6d1baea242b11d67a`

调用 `publish_routing_package(..., activate=False)`，新增lock/package/policy三份工件，仍为48模块/222题。**53份已有release JSON逐字节未变，当前指针仍为S05的pkg_24f079…**。既有三个包全部保留。真实发布回执为 `first-segment-candidate-publication-2026-09-26.log`。

## 5. 下一段接口与未完成工作

1. 等S02独立审查放行后再接入 `question_sets.py` 的 routev2/compose/CLI。原 `validate_profile` 保持严格；不可直接让它吞入null类型或三个行业，再声称全覆盖。
2. `build_route_request` 当前返回候选问题及prompt hash，`resolve_route_decision` 接受已从transport解出的 `{schema_version,question_id,candidates}`。StockQA native外层协议的适配/解析和直接公共CLI路径尚未完成，不能把这一段当作可直接收费运行。
3. 执行入口顺序应为：验证独立存储的decision身份 → `validate_route_for_execution(now_utc=...)` → `enforce_route_budget` → 按route选择范围组合/去重/分部处理 → 在manifest封存整份route与policy/package绑定。预算与profile投影助手不自行承担入口身份认证。
4. `identity_ref`、`verified_facts`、execution receipt和user_policy是调用方可信输入；来源URL不在本模块联网验真。生产接入应强制独立持久化的 `expected_decision_id`。自报hash本身无法识别攻击者整体重签的伪造记录。
5. 第二段仍需T1–T5真实compose计数/风险预算、入口绕过、历史manifest、模块/题義跨期差异与标准输出回归；此后独立审查及全量套件。实际搜索、持久化、增量执行、跨仓协作、UI仍属对应后续任务。
6. `profile_from_route` 与 `diff_routes` 是纯数据助手；只对已验证快照使用。历史v1读路径仍是module_contract；v2历史读用routing.validate_route_snapshot，执行时另检TTL。

## 6. 最终源码与日志哈希

| 文件 | SHA-256 |
|---|---|
| `docs/implementation/reviews/S06/first-segment-candidate-publication-2026-09-26.log` | `74d0febab984c8933ae42597f3b7df7f1c0b815127bc518eb291181626682a5a` |
| `docs/implementation/reviews/S06/first-segment-mutation-red-final-2026-09-26.log` | `c80871a010097a8270b2798e5051670cf85a57b1c04af80c69682260c3732751` |
| `docs/implementation/reviews/S06/first-segment-regression-green-2026-09-26.log` | `76511fd831f3ba88a641cd3184d8181f2cd7e047a62d23ea366a7ab21b946b15` |
| `docs/implementation/reviews/S06/run-first-segment-offline.py` | `53593075448b939b8ec0f218d073a54fcfc9af4222c8aa6c9782f9e5dfd009a7` |
| `questions/routing-policy.v2.json` | `67455b6e47ab7e1292367aec5e7055ed0768cf79d99d93a6804d2fc32d5d50fb` |
| `references/routing.md` | `5909dc2216c20116fdbe96295e3f138d3d314d555945bee5da7fff19efbd4375` |
| `schemas/quick_scan/module-release.schema.json` | `6265d0c9c64ce40f25ca1d0906183941e134b868821c1d8e3ed5c83d9ab24601` |
| `schemas/quick_scan/route-decision.schema.json` | `9cb7b50fd060fd68b08d2fb9239c9e065e3ea35c9e0a81e6c583ecdc32079d11` |
| `scripts/module_contract.py` | `ad9d4621e20d49ffc238167305429466ac00e50178b1c9513f001170fccad914` |
| `scripts/module_registry.py` | `ad38a9e7ce302b84f45569d276210e43ec84b7d67547540424ac640a57ea5a03` |
| `scripts/question_sets.py` | `ea0b27d45eddc1c43fd57b69da69ab22545a67f87e475960e168fd5cdb5c3b35` |
| `scripts/routing.py` | `b69c0346b31353db53af48087530ec6c64f775382968a6f5d9f3ed0cae82da46` |
| `tests/test_question_sets.py` | `7b9ba65164b09c2aa40993bdfd6e4233207247f237a3ca89f24e82630a0f5107` |
| `tests/test_routing.py` | `5f5d11776b4f28632fe928b09104a3de16fdb7aab4a48e45e35e1544c7869778` |

本段实施与测试没有为S06整卡放行；停止在第一段交接点，等待独立审查及第二段授权调度。

