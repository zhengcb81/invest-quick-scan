# Phase91 跨仓公开入口预检：独立集中复核

日期：2026-10-07。审查者：独立只读 agent `identity_wire_review`。本报告只评审本批预检，不签收 G3、X09、F05，也不评审或刷新旧任务回执。

## 结论

本批预检有效，归档结果为 **3 RED / 3 GREEN / 4.56s**。三条红例证明两类新的 StockQA 交付阻断：已封装为 `ready` 的观察缺少消费者必填元数据；不同实际执行 attempt 产生相同 observation ID。现有 982 项仓内检查通过与本批跨仓反例不冲突，前者未证明这些原包可被 StockWiki 接收。

三条绿例只证明当前拒绝 ACK 幂等且没有观察落库、篡改包在公开入口被拒绝、同一工作接续不再请求 HTTP 且保持原包。它们不能证明完整包导入、接受 ACK 返回生产者、真实身份/关系 golden、模型和时点比较或全链可用。

未发现需要增加第三类产品整改的证据。整改文档针对真实输入来源、不可变上下文、历史封包兼容与集中 TDD 的要求合理。不要修测试 fixture 来给原包补字段，也不要放宽 StockWiki 消费者。

## 实际审查范围与方法

- 读取本批 `cross_owner_cases.py`、`cross_owner_guarded.py`、整改文档和归档 JSON/日志，核对内容、原字节 SHA256 与运行结果。
- 只读取得归档 commit 的三个公开 fixture Git blob，检查 setup/HTTP 替身与真实 CLI 的边界。未执行它们、应用代码或测试。
- 未重跑 982 项或六项预检；未调用 API、访问真实凭据或真实库、打开待清理的 runtime SQLite、写外仓、改 PWF 或刷新回执。
- 报告中“通过”指原始运行日志与所执行测试源码共同支持的结果；本审查没有新产生一轮执行结果。

本批执行源码基线：QA remediation `84e24ef79901ce7c817054f6354b90a15c44afd3`、交接 `09f68a69bbdbf76e3a4fff63043cdd4815572e5b`；SW `04dfc5190589a8bbe224a47e94b045779c884b80`。QA 导出 manifest 保留更早的 base freeze commit `d160d80dc2340c6fb6cef0453b289b5210cf2cb6`，并明确 overlay；不能把 base freeze commit 当本批全部执行字节。

## 公开入口与 fixture 边界

`produce()` 调用已导出的生产者 fixture `setup()` / `invoke()`。`invoke()` 设置真实 CLI argv 后调用 `main_with_llm.main()`，执行生产 QAEngine、runner、work store、checkpoint、outbox 和封包代码。其 monkeypatch 只作用于合成题目、当前工作目录/argv 和 HTTP manager。HTTP 替身先返回首模型合成额度拒绝，再返回备用模型合成答案；模型标签和 attempt 来自这条实际离线 transport 路径。

跨仓测试从真实 `QuickScanWorkStore.get_result_delivery()` 取得原始 package，随后以 JSON 序列化输入 StockWiki `stockwiki.cli.main([... "observation-import" ...])`。正常导入路径未修改 observation 字段、ID 或 hash，也没有把 producer package 换成手造消费者正例。篡改测试是唯一主动改 `answer.score` 的路径，且刻意保留旧 hash 作为负例。

消费者 fixture 只准备临时 identity seed 和 release：真实 `QuickScanStore.migrate()` / `save_entity()` 建立临时库，再调用真实公开 import。release 增加 `IQS_01` 的字段定义，不等于给原包补 `field_id`。未替换 validator、importer、observation store 或 ACK store。

这些入口为同进程调用公开 `main()`，不是 shell 启动两个 CLI 子进程；对本批入口集成结论足够，但不要把它描述为子进程或已安装分发包验收。

## 两类阻断的归档证据

### QA-C06-1：完整观察未生成

`test_producer_package_accepted_by_public_consumer` 真正得到 `summary={"rejected":1}`，拒绝 ACK 的 item 状态为 `rejected`，错误为 `observation_missing_field`；不是找不到公司或文件读取错误。生产者此前 CLI exit0，且 outbox state 为 `ready`。

`test_generated_observation_preserves_comparable_metadata` 与归档原包核实：缺少 `schema_version`、`field_id`、`question_version`、`template_version`、`method_id`、`cohort`、`information_cutoff`、`run_id`、`observed_at`。归档 execution 还有 `answered_at`，没有消费者要求的 `started_at`。缺字段集合不是只修首个错误就能消除的契约差异。

上述两个 RED 为同一类完整性阻断。后续补齐后仍须让消费者完整校验，当前“首个缺字段被拒”不能证明其他下游约束已通过。

### QA-C06-2：独立执行的观察 ID 碰撞

`scan-a-partial-package.json` 与 `scan-b-partial-package.json` 的实际 attempt 分别为 `6cbe9099-1731-4133-b59f-d7078789ac7d`、`5a90fdd8-cc5d-41d0-b8db-f33d89c0ddf2`，来源于两个独立临时工作根；封包也不同。两个 observation ID 却均为：

`obs_9b80079253f97158204099caa9dc7523635bca1995c1d98290c96a021415251c`

`test_independent_actual_attempts_do_not_share_observation_id` 在确认 attempt 不同之后才检查 ID 并失败，排除了把同一次接续误当新扫描的解释。当前实证是同 entity/question/entity scope 的不同执行；不同模型、security、segment 的不碰撞属于下一批必须补充的测试，不是本次已经实跑的范围。

## 三条 GREEN 的具体含义

| 原测试 | 可接受的结论 | 尚未证明 |
|---|---|---|
| `test_rejected_consumer_ack_replays_without_an_observation` | 同一临时消费者重复导入原包，两次公开 CLI exit0、均 `rejected:1`，测试逐字比较两次 `ack_id` 相同，并读取真实 store 确认 observations=0 | 接受 ACK 或生产者公开接收 ACK；不能用归档里两个不同测试的 ACK 文件证明同 ACK |
| `test_tampered_package_rejected_before_observation_write` | 修改 score 且不重算 hash 的包被公开 CLI exit2 / `package_hash_mismatch` 拒绝 | 没有新增对落库计数的直接断言；“写入前”还依赖公开 importer 的校验顺序，不能把该测试说成独立的零观察计数证明 |
| `test_public_producer_warm_resume_keeps_package_with_zero_http` | 换独立输出文件后接续同一生产工作，HTTP call_count=0，attempt 列表和封包保持不变 | 保留的是当前残缺原包，不说明其已可消费，也不证明新扫描执行的结果交付 |

最终日志为 `FFF...`、三条指定失败和 `3 failed, 3 passed in 4.56s`。结合六个测试的声明顺序与断言，支持上表三条 GREEN；没有另起一个隐藏成功用例。

## fixture 更正与 982 项旧范围

`fixture-first.log` 为 4 fail / 2 pass / 8.51s，额外失败源于仅抓 stdout，遗漏 stderr 的错误 JSON，断言为 JSON 行数 `0 == 1`。`fixture-stderr-fixed.log` 为 4 fail / 2 pass / 5.04s，已取得 `package_hash_mismatch`，额外失败仅为预期 exit1，实际公开 CLI exit2。最终源码同时收集 stdout/stderr，按公开语义断言 exit2，因此回到三红三绿。这两轮不是新增产品缺陷。

QA export manifest 中 982 passed、exit0、无 skipped、85.81s 全门/74.95s pytest 是此前 StockQA 仓内验证结果，本审查没有复跑或追加到其计数。跨仓六项为新的消费者组合测试，应单独列为 needs_revision；不能用 982 GREEN 覆盖三红，也不能说 982 变成失败。

## 隔离与清理记录边界

guard 要求单个 `IQS/runs/cross-owner-*` 自有根及两个 export manifest；移除 API_KEY/API_TOKEN 和 RUN_LIVE 环境变量，把 TEMP/TMP/TMPDIR、pytest basetemp/cache/log 都定向自有根，禁用插件自动加载与 pyc。Python audit 禁止根外写、DNS/连接、registry 和子进程，启动 canary 必须拦下根外写与 DNS；最终三份日志都有 `cross_owner_guard_canaries_passed`。

Windows 例外仅限标准库 `socket.py` 的 `_fallback_socketpair` loopback self-pipe，普通 localhost 请求并未获得通用豁免。这是针对本次受控 Python fixture 的 guard，不是任意原生代码的 OS 沙箱。实际 HTTP handler 为合成替身，setup 使用 literal `offline-fixture-key` 和合成费率；日志中的 masked/offline key 不是读取真实 credential 的证据。

本次最初归档的 `result.json` 明确 `cleanup_status=pending`，因此最初证据只证明执行隔离，不证明已清理。最终更新后 `cleanup_status=completed`，并新增 `cleanup-manifest.json`：事前 strict CIM、active_processes=0、deleted=true、shared_temp_touched=false、external_repo_cleanup=false。清单为 483 个唯一文件，全部路径位于精确自有根、具备有效 SHA256 且 owner/run_id 一致；原件执行日志 hash 与清理清单中对应项一致。源仓前后状态未变与工具 session 终态由主线记录，本独审未重新打开运行库、扫描进程或占用已删除根。清理结论依据该最终归档，不能回溯把 pre-cleanup 日志单独称为清理证明。

## 归档 ACK 角色澄清

初始归档的 `consumer-rejected-ack.json` 来自“正向原包导入失败”测试，ack ID `ack_47a7f824cabd8d5f7a787146`；`replayed-rejected-ack.json` 来自另一个“拒绝 ACK 重放”测试最终 receipt，ack ID `ack_607f5cf4ca444670c3b1636f`，package/store_id 也不同。它们不是 first/again 配对。

已向主线反馈此证据命名歧义；最终 `result.json` 的 `artifact_roles`、`ack_replay_proof` 已明确分别来源及首次 receipt 未另行归档，两个 ACK 原件保持原字节。此问题已在本批澄清，不构成第三类产品阻断。同 ACK 的 GREEN 依据该测试内部精确断言与原始运行日志，不能据两个归档文件 ACK 不同判产品 bug，也不能把两个文件假称一对重放证据。运行根已清理，不为补齐第一次 receipt 重跑测试或伪造原件。

## 本次源码/fixture SHA 快照

| 文件/原字节范围 | SHA256 |
|---|---|
| IQS `cross_owner_cases.py` | `cb49c7a66e577b8c0f9fb94b14199050e5a1f3cf586a14231577ee03412c98b3` |
| IQS `cross_owner_guarded.py` | `210c582f7bb9aba5c0deaa5e15bf866b344ad4052db25d5fcbdb096fc88e5c6e` |
| QA transport fixture 归档实际 CRLF 字节，18615B | `dcf528a1954a105d9e17d6d82611ba2ac3fbca37ddffa400f62872ee39570a6c` |
| 同 fixture 的 `84e24ef` Git LF blob，18191B | `fd5582d1566c977df10bec8c60eef7a64a8992d2cc6b7e91ef4a5cc547800f30` |
| QA CLI fixture `84e24ef` Git blob，19955B | `c4f2ba57375cf7a2581e27eac92fcc8e35525e0727248b47782c21b81ef1f32e` |
| SW observation fixture `04dfc519` Git blob，39494B | `b5a83507fdf8eb5d119eae8f244fc1860909af4390e5d6c45df1ca143eb2e297` |

对 transport Git blob 仅在内存将 LF 转 CRLF，所得字节数/hash 与归档执行 manifest 精确一致；未修改文件或模糊忽略其他字节差异。初始 archive index 的 12/12 原件大小和 SHA 均匹配；最终更新后的 index 为 **13/13 匹配**（新增 cleanup manifest、更新 result，原始包/ACK/日志字节未变）。

最终归档快照：

| 文件 | 原字节 SHA256 |
|---|---|
| `artifacts.json`（13 项索引，自身不计入 items） | `fbcb02f2b1d6228f036030d04da703d8528b58cedbf66ed7757997919f502a94` |
| `result.json`（2341B，completed 与 ACK 角色澄清） | `65a330ccabb2b201f389b1042156bd59ff55137bafb681eec4bf467d4e65e452` |
| `cleanup-manifest.json`（177475B，483 文件） | `ec6a03d355270269d1d0961de51fa9bb6a6e4fc01efcc4db19eca2096f102c51` |
| `acceptance-red.log`（32410B） | `95573428d6151860a899c7fabb5380e6243b2e8629d6eb6bdc1408a77a52405a` |
| `producer-partial-package.json`（1943B） | `04feb9c263191a9cd79a6a3940bf8ed97d113b3a10a01ffbeb982f01acea9d2a` |
| `cross-owner-remediation-2026-10-07.md`（6179B） | `1aeef8af443a67e87c87b20283755292d7ea0db9ddfa1cf84605d0ddd2daa8b8` |

## 后续接受标准

按整改文档合并为一个 StockQA 实施批次：从冻结的真实定义和运行上下文生成完整观察；接续从耐久 checkpoint 恢复原上下文；同执行重放稳定、独立实际执行不碰撞；旧 sealed 包/ACK/收费账本只读保留，完整后补包有版本和替代链；最后用两个真实公开入口完成接受、ACK 丢失重放与生产者接收。集中测试与一次独立复核即可，不增设逐 helper 审查门。

真实 StockWiki identity DTO/关系 golden 和后续 G3/X09 仍须 owner 按既有接口交付，不能由本次合成 fixture 替代。
