# 实施计划 1.9.2 独立复核记录

日期：2026-09-26  
范围：对最终全量任务图/案例引用运行校验，并独立复核验收归属、组件演进及跨仓边界；仅修订 `invest-quick-scan` 本地规划/校验文件。没有写 StockQAbyLLM、StockWiki、company-wiki 或其他仓库，没有调用模型或 live API，没有执行产品功能。

## 结论

计划依赖图无环，所有任务仍通过 G6 汇总。独立复核发现，若干早期 owner 卡把后置公开入口、真实联网、导入、UI 或字段刷新列作本卡完成门；这会造成任务无法按依赖顺序完成，或让局部schema/单测被误报为完整跨组件行为。计划已拆分owner本地用例与后置全链用例，新增 `requires_tasks` 依赖声明及校验器规则，并将发布、回退、CAS与实际POST前围栏的关键状态边界写成固定案例。

计划清单现为1.9.2：102张任务卡、289个验收场景、48条固定约束。所有案例仍为 `specified_not_executed`；本记录是计划审查，不是产品验收。

## 验收边界修正

| 早期卡/问题 | 修正后的owner边界 |
|---|---|
| C01 身份与C03规则卡误含ID/唯一性、筛选与真实消费行为 | C01/C03保留契约本地验收；真实证券来源唯一性、跨对象筛选/规则行为移交对应StockWiki与后置集成卡。 |
| Q01/Q03 `SC-01`、Q02 `LLM-01`、Q04 `PAR-08` | 解析到答案生成、CLI/导入的全链归S02；真实搜索完成归L01；策略/运行设置的公开联动归X04/X09。早期卡只验自身可执行边界。 |
| S01/S02 `REC-04`、S03 `TIME-06` | 真正的StockWiki查询/刷新行为分别归W08/W06；题库卡增加本地契约案例，不用未实现消费入口阻塞题库本地验收。 |
| Q05/W01 DB与身份场景、W03路由场景、W13运维重启 | 按实际数据库/身份/公开维护入口移交W05/W09/W13或X05；本地卡保留纯输入、校验器或适配行为。 |
| S04—S06模块语义、Q07/Q10解析、Q11比较、T01/T02消费者案例 | 模块归档/本地解析与运行路由分开；实际刷新归W10，三维快照归W14，旧无recipe统一入口归X05/X09。给早期卡补本地MOD/PAR/MATRIX/CONS用例。 |
| F01/F04事实集成与U01列表页面 | 事实schema/摄取局部行为与查询/导入分开，由F05/X09完成下游链；U01验列表owner路径，U02验实际列表到详情。 |
| W16/X05/X07/X08/X09版本证据 | W16只验owner事务和临时真实SQLite；X05验旧无recipe公开入口；X07只核候选锁；X08核安装hash；X09核隔离运行时实载hash。 |

`acceptance-cases.json` 的 `requires_tasks` 现在表达完整跨任务用例所需前置owner。校验器拒绝未知/错误类型任务ID，并拒绝任何未依赖这些任务的卡把全链case列为自己的完成门。测试覆盖了越级声称、未知依赖和非法形状。

## 可组合与向后兼容审查

- 可替换的组件（题库、路由、答案解释、评分尺、事实本体/词表、筛选lens、刷新策略、provider能力、查询投影）各有唯一owner、不可变release ID/hash及领域schema；跨域 `ScanRecipe/RunManifest` 固定实际加载hash和输入，不能在批次中途热替换。
- 原始回答、来源与信息时间、观察、模型执行、费用和outbox不可变；旧数据无recipe时只读适配，证据不足标 `needs_review`，不得补签伪历史recipe或自动付费重问。阈值/别名/权重变化只重建派生视图，不调用模型。
- `candidate ReleaseSet`只能预览；生产generation/work/预算/POST必须来自具备新派发资格的active ReleaseSet。候选包和测试active指针必须与生产profile隔离。
- component release生命周期与workspace/profile active ReleaseSet指针分离。指针切换本身不自动将原组件release deprecated；deprecated/retired由owner显式追加生命周期事件。回退只切到仍具资格、兼容且通过隔离回放的组合，不能静默复活已退役release。
- V17由已安装且hash匹配的固定实现根据当前StockWiki权威快照确定性重算完整影响plan。W16用单一owner事务CAS绑定快照、身份/成员/适用范围修订、字段generation、recipe、active ReleaseSet ID/status/完整manifest hash/pointer revision和V17实现hash；不接受调用方自签hash或本计划未定义的签名回执。
- W16唯一拥有dispatch fence请求/回执schema，签发精确绑定work/attempt/recipe/active pointer的短时单次permit；StockQA Q15消费后，先把permit关联到本地耐久send_intent再允许POST。lease后、授权前release退役/切换，以及permit签发后、send_intent前崩溃，POST都为0且旧permit不可复用；send_intent后结果不明的attempt按原recipe/receipt对账，不盲目重复付费发送。
- 回退/迁移只处理受影响字段与派生投影，保留低谷恢复观察、manual pin、原评分和旧账本。迁移失败须停止新写/派发、保留旧库/费用/未决attempt；candidate/live资格不能由局部离线测试替代。

## 本轮修订清单

- 补齐前置owner与后置集成case的依赖关系；新增本地替代case，明确局部验证不等于产品全链通过。
- 新增 Q15 与 LLM-17/EVO-76，固定StockQA每次真实POST前的授权栅栏和 lease—退役—发送竞态。
- 统一候选与活动ReleaseSet、组件生命周期与活动指针、确定性V17重算、完整W16 CAS、资格回退与旧attempt结算语义。
- 修正W16重复步骤及case数量描述；修正EVO-66曾允许可信回执替代V17确定性重算的冲突表述。
- 清单数据、README、跨项目交付、演进设计、决策表、测试策略、`task_plan.md`、`findings.md` 与 `progress.md` 对齐1.9.2及102/289/48计数。
- 加强计划校验器，拒绝错误类型的 `requires_tasks` 而不抛未处理异常，并保留该异常形状测试。

## 验证与剩余边界

本轮验证命令及结果：

```powershell
python -X utf8 scripts/implementation_plan.py validate
python -X utf8 -m unittest discover -s tests -p test_implementation_plan.py -v
```

计划验证通过：102任务、289场景、最终门槛G6、`product_tests_executed=false`；计划单测63项通过。`git diff --check`退出0，输出仅包含既存文件换行风格警告。上述命令只验证计划结构和校验器；没有执行生产入口、真实搜索、下载、数据库迁移、UI浏览器验收或跨仓测试。StockWiki除先前精确授权的W01范围外，任何新写入仍需单独授权；StockQA具体跨仓变更仍需在实施前报备目标文件及目的。按用户当前指示，计划复核结束后暂停，不自动继续实现。
