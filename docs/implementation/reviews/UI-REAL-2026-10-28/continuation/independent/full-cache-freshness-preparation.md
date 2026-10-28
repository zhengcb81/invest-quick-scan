# 三市场完整任务缓存验收：时间语义与有限顺序

结论：当前封存观测的 `observed_at` 是**原模型回复完成时刻**，不是后来封包、导入或恢复的时刻。按当前真实 TTL24 规则，这批旧信息截止资料没有一条可以宣称为普通新任务的 fresh 缓存。“原登记任务恢复既有检查点”与“新普通研究任务重用仍新鲜观测”必须分开验收。

本报告只读调查，不代表 full108 已完成、全部入库、金融验证通过或新的执行授权。

## 实际元数据快照

读取时刻：**2026-10-28 16:23:17.501645 UTC**。对原 `runs/u25-live/work.sqlite` 使用 URI `mode=ro`、`PRAGMA query_only=ON` 和一个短一致性读事务；事务持续 **0.0151 秒**，取完元数据立即 rollback/close。没有构造任何原 Store，没有调用 CLI/模型，没有写库或干预正在运行的 owner controls。

仅选取 ID、generation、状态和日期字段。对 JSON 只通过 SQLite `json_extract` 提取指定时间路径，没有将答文、summary、理由或证据正文取到 Python。全部元数据在 [full-cache-time-metadata.json](C:/Users/郑曾波/Projects/invest-quick-scan/runs/resume-recovery-2026-10-28/independent/full-cache-time-metadata.json)。后续合法施工可能改变当前状态，不能把该快照当作最新控制回执。

| 口径 | 数量 | TTL24 stale | missing_date | fresh |
|---|---:|---:|---:|---:|
| 全部原检查点 | 59 | 不把 CP 时间当 TTL | 不把 CP 存在当观测完整 | 不适用 |
| 有完整封存 observation 的包 | 57 | 41 | 16 | 0 |
| 每字段选最新已封存 generation | 56 | 41 | 15 | 0 |
| 同时也是当前最新 work generation 的封存观测 | 55 | 40 | 15 | 0 |

“最新已封存”与“当前最新 work”不是一回事：宁德时代 IQS04 有历史 g4 已交付观测，但当前更高代次尚未成功，不能用旧 g4 覆盖当前工作状态。微软也保留 IQS04 的已交付旧代与后续代记录。两份历史不可交付 CP 仍为 blocked，未伪造封存包。

| 公司 | 全部 CP | 已封存包 | 当前最新 generation 已封存 | 当前其中 stale / missing_date |
|---|---:|---:|---:|---:|
| 微软 | 19 | 18 | 17 | 14 / 3 |
| 宁德时代 | 13 | 12 | 11 | 10 / 1 |
| 腾讯 | 27 | 27 | 27 | 16 / 11 |

在同一快照，三公司108个字段的最新 work 状态合计是：55 result_ready、8 failed、44 pending、1 uncertain。它们是工程工作状态，不是金融质量或最终完成结论；控制正在进行时尤其不能把这组数当作恒定基线。

时间分布：

- 59份 CP 的 `checkpointed_at` 日期：10月25日2份、10月26日15份、10月28日42份。17份较早 CP 中有2份历史 blocked CP，没有完整封存 observation。
- 57份完整 observation 的 `observed_at` 日期：10月25日2份、10月26日13份、10月28日42份；其中15份的原答时距快照已超过24小时。
- 57份完整 observation 的 `information_cutoff` 全部是 **2026-10-25**。
- 41份有 `answer.information_as_of`，范围是 **2024-12-31 至 2026-09-11**；其余16份为 null。不能用今天导入时刻填这些 null，也不能为了缓存通过把旧信息日期改成今天。

## observed_at 具体来自哪里

57份封存包逐项核对，以下四种相等关系均为 **57/57**：

1. `observation.observed_at == checkpoint.provenance.response_completed_at`；
2. `observation.observed_at == 原 durable receipt.completed_at`；
3. `observation.observed_at == observation.execution.answered_at`；
4. `package.created_at == observation.observed_at`。

原代码对应路径：

- StockQA `src/utils/quick_scan_observation_context.py:677` 从检查点 provenance 的 `response_completed_at` 得到 execution.answered_at；`:687` 用该 answered_at 设置 observed_at。
- StockQA `src/utils/quick_scan_c06_adapter.py:214` 也把交换包 created_at 固定为原 answered_at。**包内 created_at 本身也不是实际封包操作发生时间。**
- 真正 delivery 行的 created_at/updated_at 是另一组数据库操作时间，updated_at 还可能随着 ACK 改变；不能拿它们重新计算观测 TTL。

所以 `checkpointed_at`、包内 created_at、delivery 行时间和 observed_at 的语义需要分别保留，不能互相代替。

## 原普通刷新使用的 TTL

StockWiki `stockwiki/quick_scan_module_refresh.py:182–190` 先取得原 answer.information_as_of，日期型值按 UTC00:00 处理，计算：

```text
valid_until = min(
    observation.observed_at + TTL,
    answer.information_as_of + TTL
)
fresh 当且仅当 now < valid_until
```

没有 information_as_of 时不制造 valid_until，原 `stockwiki/quick_scan_freshness.py:103–129` 返回 missing_date；等于到期边界也属于 stale。事件失效、身份/语义/scope/模型/信息截止兼容性等还有独立门，时间检查不是完整准入。

使用原 StockWiki 纯函数 `ttl_valid_until` 和 `freshness_status` 对57行元数据再次核验，结果完全一致：**41 stale、16 missing_date、0 fresh**，见 [纯规则核对](C:/Users/郑曾波/Projects/invest-quick-scan/runs/resume-recovery-2026-10-28/independent/full-cache-freshness-pure-rule-check.json)。这没有执行原 owner 的完整计划或授权检查。

因此，不只是15份较早回答会过期。即便42份10月28日刚回答的结果，其信息日期仍旧或缺失，也不能被普通新任务判成 fresh。日后把它们导入、重新读取或重新封包，都不会刷新该日期。相同旧25截止下反复收费询问，也不保证得到可 fresh 的信息时间，不能无限重问来追求绿色标记。

stale/missing_date 是时间分类，不意味着每题都会立即新增一次 HTTP。原完整计划仍区分 scored、不可用回答的 cooldown/manual 分支、当前 work、原授权和预算；应以有限只读预览给出的实际 action 为准。

## 原任务检查点恢复与新普通缓存复用

**ACK前，原 result_ready 检查点恢复：**同一原 registered 完整任务、原输入与有效 grant，且工作未被更高代次替代时，原 `ApprovedRefreshSession` 固定原 work ID/generation，`restore_registered_checkpoint` 读取和验证原 CP、完整 standard answer、context 和回执，不因重新运行而修改 observed_at，也不需要新的模型 HTTP。这属于恢复原来已经完成的工作，不把它宣称为当前新研究的 fresh 结论。

**ACK后，不能无条件承诺旧任务仍完整 hydrate：**当前 StockQA `src/utils/quick_scan_refresh_execution.py:249–267` 对已 delivered、但原 native 普通计划不能 reuse 的字段，设置 `original_delivery_historical_or_refresh_required`；`:404–412` 的 restore_registered_checkpoint 遇到 deferred 会返回 None。因此“有原 CP/ACK”不等于“旧输入当前仍可普通复用”，也不能只凭0HTTP就声称完整成功恢复。若原任务已经被新代次替代，还会走 `registered_work_superseded`。

原结果、封存包和 exact ACK 的历史幂等读取可以保持0HTTP；其 historical/deferred 标记必须如实显示。需要的新普通任务则重新准备，由原 freshness 与授权机制决定，不能偷偷改变旧任务范围。

## 建议的有限验收顺序

1. **先完成当前原 full108。**保留已有55份当前成功，不把历史 blocked CP、旧已交付代次或失败状态算成最新成功。未知 HTTP 先按原允许流程处理；不因有结果记录就重发。
2. **在最终当前108题都已 result_ready、但尚未全部 ACK 时，做原任务冷恢复。**选择与这些最终 work ID/generation 对齐的原完整 registered 任务和有效 grant，从原 UI 暂停已退出任务后明确 resume；核完整原 CP 恢复、0新增模型 HTTP、CP/standard/package/原回答时间不变。较早已 superseded 的旧准备不适合冒充这个完整验收对象。
3. **再完成原 full108 导入与 exact ACK。**原幂等交付机制逐 scope/包记录，保留原回答时间、原费用与旧代历史。
4. **ACK后验证历史持久性与0HTTP幂等读取。**原结果、包与 ACK 应仍可查且标识不变。如果旧任务的 SDK 路径因上述 delivered/freshness 门返回历史/需新准备，就如实接受这个边界；不把它叫 fresh，也不假报完整 hydrate。真正超出该边界的功能错误由主线另行根修。
5. **新普通旧25任务只做有限只读预览。**核实际返回 stale/missing_date 或其对应 manual/normal-refresh 决策、没有模型请求和新费用。不启动一轮又一轮同旧日期全量重问，不改 TTL、时钟、information_as_of、observed_at，也不悄悄换成28日新scope。
6. **有效TTL内复用与到期刷新采用已有真实原生隔离证据。**此前动态UTC、私有TTL72→24的原生验收已覆盖该软件分支；本轮不为了掩盖旧期结果而额外重扫新28全108。真实三市场本轮重点是完整工作流程、原检查点恢复、入库与历史缓存持久性。

本顺序与总控本节点确认一致。报告没有执行其中任何启动、恢复、导入或控制动作，也没有替主线关闭实际 full108/缓存验收门。
