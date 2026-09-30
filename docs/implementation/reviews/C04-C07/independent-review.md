# C04–C07 独立审查报告

- 审查者：`/root/g0_independent_review`（独立只读审查 agent）
- 审查日期：2026-09-24
- 审查范围：C04、C05、C06、C07 的本地契约实现、任务卡、验收 case、回执、原始日志及当前测试；未调用真实 provider，未写 StockQA、StockWiki 或 company-wiki。
- 结论：C05 可在“本地离线契约”范围晋级 `verified`。C04、C06、C07 均有可复现的 BLOCKING 契约缺口，且其回执（C04 部分、C06/C07 大部）未绑定当前字节，不能直接从 `implementation_complete` 晋级。

## 审查快照

| 项目 | SHA-256 |
|---|---|
| `receipt-C04.json` | `D166254012CF78B552F8696F33FA66DD8A4743F81936253CF294E26CDBFCC240` |
| `receipt-C05.json` | `60ECF2AD87CE70CB592015A37418859465E4A9B1153EBA72C58A7F9809DECD78` |
| `receipt-C06.json` | `3C6D989DB0246FE6B75C8B1E0C6D41ADDC63C61A7DDEFF922C4E5ADC3D6433FD` |
| `receipt-C07.json` | `C7853A53E91CE017C18BA4A103D63590C5508CE1DE20B99B5E7F7C1AAE76D5B9` |
| `tasks.json` | `55DBB8D63A27A8D8A8ACD37C46322CD0FBDCE2D5113CEEC3E416E16AA401AC0F` |
| `acceptance-cases.json` | `38642BFDBEA9C3BEBB7272D13EED6D3C4C85BEBC99D5A9C7B372CC7400E557FA` |
| `scripts/contract_validation.py` | `637287FB18CE33BF0DAA98865AA79C8399C2282DBAEEB2A22FFC1102191ABC69` |
| `tests/test_g0_regressions.py` | `3851A9044B5C17E7CA5179610E646EEE4D1F12334D59166802BE9FB3C375FD83` |

### C04 当前行为文件

| 文件 | SHA-256 | 与回执 |
|---|---|---|
| `schemas/quick_scan/work.schema.json` | `A67F82C77F43561A787D42756C8C71CED06AAF8B3A37B8229442EFD73D60A8BF` | 一致 |
| `scripts/work_contract.py` | `4A86CAD70EF2C8C636C0C6D794C3652ED2F62A15EC151D4D4BBFB5C45BCBA3CA` | 一致 |
| `tests/test_freshness_and_jobs_contract.py` | `A4DBEA82EF839FB570B59E55075AA64999D8E6BFE88BA182024316C11A17F967` | 一致 |
| `docs/implementation/contracts/freshness-and-jobs.md` | `D5E00C322A14FDC28950152E5ACFF77FE2033B7171A2B652502F65F30D6E142B` | 不一致；回执记录 `C393…36BA` |

### C05 当前行为文件

| 文件 | SHA-256 | 与回执 |
|---|---|---|
| `schemas/model-policy.schema.json` | `E6188237EF0FD07C4EE63C1EAB25AB250426BA7C12E6D0BC71A9D4AB1D7D0455` | 一致 |
| `examples/model-policy.template.json` | `215FA6A7DEFEDBF7D24FC5083F31849849839DECE9728499B2B5791F7012B013` | 一致 |
| `scripts/model_policy.py` | `C181B8B2348944A0897B6E49CEE2798BA2E38A7A770D30D8BF6D4C47211245D0` | 一致 |
| `tests/test_model_policy.py` | `DF628F2603395425318B2C70724BF7276CEC4D163ECDA11E09EE76825632E551` | 一致 |
| `tests/test_providers_and_budget_contract.py` | `A7A7008EFBC6660B1F530E661C564AB1B36558F75AE0B468B1AA36496B229F6B` | 一致 |
| `docs/implementation/contracts/providers-and-budget.md` | `629618F2EE172CD43A853AF84CF8B5CA30D2EACE6B2F7B0133C3CCA39E8F6B52` | 一致 |

### C06 当前行为文件

| 文件 | SHA-256 | 与回执 |
|---|---|---|
| `schemas/quick_scan/exchange.schema.json` | `EFDF0E3427D1BBB73892E9573FBF3B1F0389218E3F5A0C8DFF4CA0CD63764122` | 不一致 |
| `schemas/quick_scan/query.schema.json` | `E7FC264B43D85E4CDD5C82A71B9FEDB579DD0FC1196F3C5FDE661F14FA1756F8` | 不一致 |
| `scripts/exchange_contract.py` | `BFA6A227F4A4B6E87F876BCEBD8562C86FE105AAF5840AD27ADE3E8F0C99E335` | 不一致 |
| `tests/test_exchange_and_query_contract.py` | `31DE044430DEBE51DAAB581116DC3D63C8EA4DA5B143D052C6A4E3E798BAA2F7` | 不一致 |
| `docs/implementation/contracts/exchange-and-query.md` | `10748596AC468241845BF8493F2E0468D2AF10B62360BE035D6E236C967F2379` | 不一致 |

### C07 当前行为文件

| 文件 | SHA-256 | 与回执 |
|---|---|---|
| `schemas/quick_scan/deployment.schema.json` | `AF7C5745FF00A63110BA8049D345ACD9B639A48A9B7E09528FB784C34640ECA1` | 不一致 |
| `scripts/deployment_contract.py` | `AD6AFEEC826ABCE59A107754D36AA399069F37BF33F7AB102291D98A582EB247` | 不一致 |
| `examples/quick_scan/deployment-contract.examples.json` | `44BDBC6B6CA7FFBFCA5AB0742C00854E81A2636213A5B2DB7193773EE14D819C` | 一致 |
| `tests/test_deployment_contract.py` | `7AD2614F394B4B89F06C61D1319887AEA00A56E5FA77184D95369E8BEB1C511C` | 不一致 |
| `docs/implementation/contracts/launch-and-release.md` | `C6B3943DEB71824A4E0F877D70E1F78D746BC761322C178951508D1FEEC72AAD` | 不一致 |

## 原始日志与独立重放

四份历史日志的当前字节 hash 均与各自回执一致：C04 `3C69ADFE…04C43`、C05 `EB546C1C…4DA7`、C06 `1084F338…CF91B`、C07 `5544FC7A…6C3CE`。日志中的计划摘要为当时的 73 tasks / 162 cases；这是历史证据，不能代表当前 172-case 计划，也不能绑定上表已经变化的行为文件。

我将 `TEMP`/`TMP` 指向独立目录 `iqs-independent-c04-c07-28c35bd76b694672a080847537f1d804`，设置 `PYTHONDONTWRITEBYTECODE=1` 并禁用 pytest cache。重放结果：

- `python -X utf8 -m pytest -q -p no:cacheprovider tests/test_freshness_and_jobs_contract.py`：`15 passed, 5 subtests passed`。
- `python -X utf8 -m pytest -q -p no:cacheprovider tests/test_model_policy.py tests/test_providers_and_budget_contract.py`：`25 passed, 15 subtests passed`。
- `python -X utf8 -m pytest -q -p no:cacheprovider tests/test_exchange_and_query_contract.py tests/test_g0_regressions.py`：`21 passed`。
- `python -X utf8 -m pytest -q -p no:cacheprovider tests/test_deployment_contract.py tests/test_g0_regressions.py`：`20 passed`。
- 运行后隔离 TEMP 目录为空。

这些结果证明既有 selector 当前通过，但以下最小反例未被现有测试覆盖。

## Findings

### C04-IR-01 — BLOCKING：`uncertain_attempt_id` 可指向不存在的 attempt

- 触发：构造 schema-valid `WorkItem(status="uncertain")`，`attempts=[{"attempt_id":"ATT_REAL",…}]`，同时设置 `uncertain_attempt_id="ATT_MISSING"`。
- 位置：`schemas/quick_scan/work.schema.json:316-440` 只要求 attempts 非空及 uncertain ID 为字符串；`scripts/contract_validation.py:131-143` 只检查 scope 所属关系；`scripts/work_contract.py:164-190` 接受调用方分别传入的两个 ID，却不接收或核对持久化 attempts。
- 实测：Draft7 schema 与 `contract_validation.validate_work_item()` 均接受该对象。
- 影响：状态记录没有把“待对账 attempt”绑定到真实尝试；调用方可围绕不存在的 ID 提交一致的参数并越过“同一 attempt 对账”意图。回执所称“绑定唯一attempt”未闭合。
- 修复要求：公共 WorkItem 语义 validator 必须要求 `uncertain_attempt_id` 在 attempts 中恰好出现一次，并拒绝重复 attempt ID；状态转换入口应从已验证 WorkItem 读取该 ID，或显式核对该 WorkItem。
- 验证：增加缺失 ID、重复 ID、匹配 ID 三组负/正例，并通过公共 validator 与真实状态转换入口重放 JOB-08。

### C04-IR-02 — BLOCKING（证据包）：C04 回执未绑定当前完整契约入口

- 触发：当前文档 hash 已从回执的 `C393…36BA` 变为 `D5E0…142B`；当前 scope 语义依赖后来新增的 `scripts/contract_validation.py`，但该文件不在 C04 回执快照中。
- 影响：即使修复 C04-IR-01，也不能把现有回执原样改为 verified；它没有精确标识当前可执行契约闭包。
- 修复要求：修复后生成新回执或审查 addendum，绑定当前 schema、helper、公共 semantic validator、测试、文档和原始日志 hash。

### C06-IR-01 — BLOCKING：公共 exchange validator 不验证 package/item/payload hash

- 触发：读取合法 `exchange-package.example.json`，只修改 `items[0].observation.answer.summary`，保留旧 `payload_sha256`、`item_id`、`package_sha256`，再调用 `contract_validation.validate_exchange_package()`。
- 位置：`scripts/contract_validation.py:207-210` 只做 schema 和 extensions 检查；`scripts/exchange_contract.py:41-78` 仅在构造新包时计算 hash。
- 实测：篡改包被公共 validator 接受（`tampered_hash_package_accepted=True`）。
- 影响：C06-CONTRACT-01 的“不可变 hash 经公共 reference validator 校验”未实现。消费者若信任 validator，可导入正文与声明 hash 不一致的包；结构有效不等于内容寻址有效。
- 修复要求：公共 validator 重算每项 observation payload hash、由 observation ID/payload hash 重算 item ID，并在移除 package hash/id 后重算 package hash与 ID；任何不一致均拒绝。构造与验证须共享同一 canonicalization。
- 验证：分别篡改 observation、payload hash、observation ID、item ID、package 元数据、package hash/id；每个只改一处均须失败，原包须通过。

### C06-IR-02 — BLOCKING（证据包）：C06 回执是修复前快照

- 触发：exchange schema、query schema、helper、测试、文档五项当前 hash 均不同于回执；当前 C06 语义还依赖未列入该回执的 `contract_validation.py` 与 `test_g0_regressions.py`。
- 影响：历史日志虽 hash 正确，不能证明当前候选；回执不能原样晋级。
- 修复要求：修复 C06-IR-01 后建立绑定当前完整闭包的新回执/审查快照。

### C07-IR-01 — BLOCKING：full readiness 响应验证信任自报布尔值，不核对组件实载状态

- 触发：由合法样例构造 schema-valid `full_release_verified` 响应，提供同 release 的 G0–G6 和两个 consumer；仅将一个 required component 的 `actual_loaded_sha256` 改为其他 64 位 hash，同时保留 `all_required_component_hashes_match=true`。
- 位置：`scripts/deployment_contract.py:90-119` 校验 evidence release/gates/consumers，但在 full 路径没有把 `result.components` 交给 `assess_readiness()` 或等价检查。
- 实测：`validate_readiness_response()` 接受该响应（`full_with_bad_component_hash_accepted=True`）。
- 影响：响应可在组件实载 hash 与 release manifest 不一致时自报 full，直接违反 C07-CONTRACT-03 的“组件 hash 缺失/错误不得 full”与同一 release 证据闭包要求。
- 修复要求：响应 validator 必须用 release set、components、setup/doctor/live receipts、gate evidence 重新推导 readiness，并要求推导值等于响应值；至少逐个拒绝缺失、重复、额外、版本/hash/contract/capability/interpreter 不匹配的 required component。
- 验证：对每个 required component 分别篡改 actual/expected hash、版本、契约、能力、解释器，及重复/缺失组件；任何 full 自报均须失败。

### C07-IR-02 — BLOCKING（证据包）：C07 回执是修复前快照

- 触发：deployment schema、helper、测试、文档当前 hash 均与回执不同，且当前回归依赖未列入原快照的 G0 文件。
- 影响：历史 2026-09-23 日志不能证明当前实现；回执不能原样晋级。
- 修复要求：修复 C07-IR-01 后建立新回执/审查快照，并继续明确真实进程、真实 paid search 和跨仓 E2E 未执行。

## 每任务结论

| 任务 | 本地 case 结论 | 回执晋级 |
|---|---|---|
| C04 | TIME-01..08 与现有 JOB 测试通过；JOB-08 的持久化 attempt 绑定存在未覆盖反例 | **needs_revision** |
| C05 | C05-CONTRACT-01/02/03 的当前离线 schema/helper/template/test 快照与回执完全一致；未发现本地契约阻断 | **verified（仅本地离线契约）** |
| C06 | 查询 coverage/lineage 回归通过；交换 hash 公共验证存在反例 | **needs_revision** |
| C07 | lifecycle/readiness 回归通过；full readiness 的组件闭包存在反例 | **needs_revision** |

C05 的 verified 不认证真实 provider 顺序、共享限额、并发、费用账本或 paid call。C04/C06/C07 的结论也只针对本仓契约；真实 StockQA/StockWiki 运行与 E2E 不在本次执行范围。
