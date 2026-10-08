# SW-REPAIR-02 interfaces

产出 commit：`9f9e0afe16a327b475cb7a6e3d40bd1578bb9b0f`（基线
`04dfc5190589a8bbe224a47e94b045779c884b80`）。

## 1. 快扫备份 manifest

| 项 | 值 |
|---|---|
| 名称 / 版本 | `stockwiki.quick_scan_backup_manifest/1.0.0`（`format_version=1.0.0`） |
| 方向 | produced |
| 兼容性 | **compatible**（版本与 schema 字符串未改；只把「写入」升级为「强校验」） |
| 生成命令 | `python -m stockwiki.cli --root <ROOT> quick-scan-backup create [--name NAME]` |
| 结构校验入口 | `stockwiki.quick_scan_backup_manifest.validate_manifest_shape(manifest, expect_name=...)` |
| 变化 | 无新增字段。新增冻结读取策略 `SUPPORTED_MANIFEST_SCHEMAS`、严格三段 `format_version`、`name`↔目录名绑定、`files` 非空/唯一/安全、`executor_side`/`consistency` 禁改、全目录链接扫描 |

## 2. 快扫备份 owner 登记（本包新增）

| 项 | 值 |
|---|---|
| 名称 / 版本 | `stockwiki.quick_scan_backup_owner_registry/1.0.0` |
| 载体 | `<ROOT>/backups/quick_scan/owner_registry.json`（运行时数据文件，用户单独授权；非数据库、无迁移） |
| 方向 | produced |
| 兼容性 | **changed**（新协议） |
| 记录字段 | `record_version`、`owner_module`、`name`、`manifest_sha256`、`created_at_utc`、`workspace_root`、`recorded_at_utc` |
| 生成命令 | `python -m stockwiki.cli --root <ROOT> quick-scan-backup create --name NAME` 后读取该文件；样例见 `logs/golden/backup_owner_registry_ok.json` |
| 消费方 | 仅 `prune_backups`（verify/restore 不需要它） |
| 证据边界 | 版本化溯源记录，非签名；同权限本地进程可同时伪造目录与登记文件，本包不作相反宣称 |

## 3. 查询快照协议（SWR-6）

| 项 | 值 |
|---|---|
| 名称 / 版本 | `quick_scan_query_snapshot/1.0.0` |
| 规则版本 | `quick_scan_query/1.0.0`（未改） |
| 方向 | both（produced + consumed） |
| 兼容性 | **changed**（显式版本化，两种互斥 hash 形态） |
| 无条件 hash keys | `["text", "filters", "view"]` —— 与 Git `9f552a67` 的 producer 逐字节一致 |
| 带条件 hash keys | `["text", "filters", "view", "conditions", "combine"]` |
| 跨 query 复用 snapshot | refused（`snapshot_query_mismatch`） |
| 改 leaf / 组合使 snapshot 失效 | 是 |
| 查询能力声明 | `GET /api/quickscan/capabilities` → `snapshot_protocol` 块 |
| golden | `logs/golden/query_capabilities_ok.json`、`logs/golden/query_legacy_snapshot_page2_ok.json` |

## 4. W09 读原语 payload

| 项 | 值 |
|---|---|
| 名称 / 版本 | `stockwiki_w09_read_primitives` / `quick_scan_query/1.0.0` |
| 方向 | produced |
| 兼容性 | **changed**（additive） |
| 新增字段 | 搜索结果行 `score_condition_outcome`（`pass`/`fail`/`unknown`，多叶子时的**整行**结论）；`capabilities.snapshot_protocol`；`coverage.by_field.*.ambiguous` 计数 |
| `c06_envelope_validated` | 恒为 `false`（本包不冒充 C06） |
| `facts_available` | 恒为 `false` |

## 5. 快扫搜索 HTTP payload

| 项 | 值 |
|---|---|
| 名称 / 版本 | `quickscan_search_http_payload` / `ui_quick_scan/1.0.0` |
| 路由 | `POST /api/quickscan/search` |
| body | `text`、`filters`、`view`、`page`、`page_size`、`snapshot`、`conditions`（**完整叶子列表**）、`condition_combine`（`all`/`any`） |
| 未知字段 | `payload_unknown_field`（400） |
| 方向 | produced |
| 兼容性 | **changed**（`conditions` 由单叶子升级为叶子列表；单元素列表与旧行为一致） |
| 浏览器 URL hash | 可重复 `c=<field>~<op>~<value>` + `combine=all|any`；同时向后兼容旧的 `field/op/value/combine` 链接 |
| 前端约束 | 页面只提交条件，不重算分数、不调用 LLM/下载；评分始终由服务端 W07 执行 |

## 6. 变体投影（SWR-4）

| 项 | 值 |
|---|---|
| 名称 / 版本 | `quick_scan_variant_projection` / `quick_scan_profiles/1.0.0`（`PROJECTION_VERSION` 未改） |
| 方向 | produced |
| 兼容性 | **changed** |
| 语义 | `score_fields[field_id]` 单一可比时＝原行；多个不可比口径时＝`status="ambiguous"`、`score=null`、`variants=[…]`（W07 判 `unknown`）；`groups[*].fields` 保留每个变体的原始 subject/scope/model/版本/分数并带 `ambiguous`/`variants` |
| 可比键 | `analysis_subject_id + revision`、`scope/security_id/listing_id`、`question_id`、`question_version/template_version/method_id/module_package_id/module_release_id`、`construct_id`、`provider/model_resolved/model_revision` |
| 组内择新 | 按 `information_cutoff → observed_at → imported_at → import_sequence → observation_id` 取最大（**不是** import 顺序） |
| golden | `logs/golden/query_variant_ambiguous_ok.json` |

## 7. 消费的外部接口

| 名称 / 版本 | 方向 | 结果 |
|---|---|---|
| `legacy_query_producer_9f552a67`（`git show 9f552a67:stockwiki/quick_scan_query.py`，bytes 20260，sha256 `271b1ba2434123180d27a64437e3f14487d390ffb5c6276471e5302a06c0639a`） | consumed | **compatible** |
| `sw_ready01_frozen_acceptance_cases`（sha256 `72b2e1250947a705f87426557ccdf8b09121d761ba09ae89da3df152db81d452`） | consumed | **compatible**（原文件 7/7 通过，未改一个字节） |
| IQS `schemas/quick_scan/query.schema.json` | consumed（只读） | 见下节，本包未改动 |

## 8. 公开 query schema / capabilities / golden 实际现状

| 对象 | 现状 | 位置 / 生成命令 |
|---|---|---|
| 正式 query JSON schema | **本仓没有**。schema 主权在 IQS：`invest-quick-scan/schemas/quick_scan/query.schema.json`（`inputs.lock.json` 记录 bytes 23536、sha256 `e7fc264b43d85e4cdd5c82a71b9fedb579dd0fc1196f3c5fde661f14fa1756f8`）。本包未新增、未改动它 | 只读引用，无生成命令 |
| query capabilities 契约 | **已存在**，由代码产生，非 schema 文件 | `GET /api/quickscan/capabilities` 或 `python -c "from stockwiki.quick_scan_query import query_capabilities; ..."`；golden `logs/golden/query_capabilities_ok.json` |
| capabilities golden | **已产出**（synthetic） | `python -B -X utf8 docs/handoff/SW-REPAIR-02/build_goldens.py --repo <StockWiki> --out <StockWiki>/docs/handoff/SW-REPAIR-02/logs/golden` |
| 旧真实 snapshot golden | **已产出**（旧 producer 实跑） | 同上，`logs/golden/query_legacy_snapshot_page2_ok.json` |
| 条件查询 golden | **已产出**（synthetic） | 同上，`logs/golden/query_search_condition_ok.json` |
| 变体歧义 golden | **已产出**（synthetic） | 同上，`logs/golden/query_variant_ambiguous_ok.json` |
| owner 登记 golden | **已产出**（synthetic） | 同上，`logs/golden/backup_owner_registry_ok.json` |
| **真实 StockWiki 身份 golden** | **missing** —— 本包无权创建/认证，**不合成 verified 填空** | `logs/golden/identity_golden_status.json`（`status: missing`，`generation_command: null`） |
| C06/C07 envelope 校验 golden | **missing**（总控未冻结 C06 envelope；本包 payload 恒标 `c06_envelope_validated=false`） | — |

## 9. 尚缺接口

- C06/C07 envelope 的正式 schema 冻结与联合校验（总控 / G3）。
- 真实 QA 输出 → W05 导入 → ACK → UI 的端到端接口 golden（跨仓，`not_run`）。
- TTL/字段注册表接口（`freshness_policy_available=false` 仍为真）。
- W15 replacement mapping 接口（`GAP_REPLACEMENT_MAPPING` 仍为显式缺口）。
