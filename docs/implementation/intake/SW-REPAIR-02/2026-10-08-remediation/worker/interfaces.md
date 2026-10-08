# SW-REPAIR-02 interfaces

产出 commit：`9f9e0afe16a327b475cb7a6e3d40bd1578bb9b0f`（基线
`04dfc5190589a8bbe224a47e94b045779c884b80`）。

> **第二轮整改（2026-10-08，SR02-1..5）产出 commit：`c83c148af35407a5ae01072314ba9bd17e59b3d9`**
> （父提交 `6d1dddbc1289a17a2fb91d40a0d4f57494fa1bfd`）。下表中标注 **(R2)** 的条目描述
> 第二轮之后的现状；未标注的条目仍是第一轮的记录，两者都有效。字节口径见第 10 节。

## 1. 快扫备份 manifest

| 项 | 值 |
|---|---|
| 名称 / 版本 | `stockwiki.quick_scan_backup_manifest/1.0.0`（`format_version=1.0.0`） |
| 方向 | produced |
| 兼容性 | **compatible**（版本与 schema 字符串未改；只把「写入」升级为「强校验」） |
| 生成命令 | `python -m stockwiki.cli --root <ROOT> quick-scan-backup create [--name NAME]` |
| 结构校验入口 | `stockwiki.quick_scan_backup_manifest.validate_manifest_shape(manifest, expect_name=...)` |
| 变化 | 无新增字段。新增冻结读取策略 `SUPPORTED_MANIFEST_SCHEMAS`、严格三段 `format_version`、`name`↔目录名绑定、`files` 非空/唯一/安全、`executor_side`/`consistency` 禁改、全目录链接扫描 |
| **(R2) 受管路径重解析拒绝** | `stockwiki.quick_scan_backup._refuse_managed_reparse(paths)` 在 create/list/prune/verify/restore 的**任何 I/O 之前**用 lstat 口径检查 `<ROOT>`→`<ROOT>/backups`→`<ROOT>/backups/quick_scan`；任一段是 symlink/junction 即 `backup_root_link_refused`。**不先 `resolve()` 再当安全根**（SR02-2） |
| **(R2) 合法 JSON 也过形状校验** | `list` 用结构判定：对象且 `files` 为列表 ⇒ `manifest_shape="object"`；`[]`/`null`/`0`/`{"files": null}`/解码失败 ⇒ `manifest_shape="invalid"` 且 `complete=false`，目录保留并在 `prune` 计入 `skipped`（SR02-4）。判定靠结构校验，不靠吞异常 |

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
| **(R2) 版本策略** | 读取策略 `validate_owner_registry`（`quick_scan_backup_manifest.py`）：严格三段 `format_version` 且主版本等于 `BACKUP_FORMAT_VERSION`、`schema` 精确相等、`records` 必须是列表；未知版本 ⇒ `owner_registry_version_unsupported`（**fail closed**），schema/形状不符 ⇒ `owner_registry_invalid`。登记损坏或版本未知时 `create` 与 `prune` 都**拒绝执行且不重建**（静默重建会抹掉既有 owner 记录） |
| **(R2) 删除权绑定** | `owner_record_grants_deletion(record, manifest=...)` 要求记录**同时**满足：`record_version`、`owner_module`、`workspace_root ↔ manifest.workspace_root`、`manifest_sha256 ↔ manifest`。只有 `name`+`digest` **不构成**归属；不符的记录只让该备份被 `skipped` 保留，登记本身不被改写（SR02-3） |
| **(R2) 迁移/恢复** | 无自动迁移器。备份搬进别的工作区后其 manifest `workspace_root` 仍是原工作区，登记须与该 manifest 一致才继续有删除权；要重新授予只能在原工作区重新 `create` 或由 owner 明确重建登记。主版本 1 + schema 精确匹配的旧合法登记行为不变 |

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

## 6. 变体投影（SWR-4 / SR02-1）

| 项 | 值 |
|---|---|
| 名称 / 版本 | `quick_scan_variant_projection` / **`quick_scan_profiles/1.1.0`（R2；第一轮为 `1.0.0`）** |
| 方向 | produced |
| 兼容性 | **changed**（字段加法 + 可比边界扩展；旧消费者读旧键不受影响，`projection_version` 用于区分两种载荷） |
| 语义 | `score_fields[field_id]` 单一可比时＝原行；多个不可比口径时＝`status="ambiguous"`、`score=null`、`variants=[…]`（W07 判 `unknown`）；`groups[*].fields` 保留每个变体的原始 subject/scope/model/版本/分数并带 `ambiguous`/`variants` |
| 可比键 | `analysis_subject_id + revision`、`scope/security_id/listing_id/**segment_id**`、`question_id`、`question_version/template_version/method_id/module_package_id/module_release_id`、`construct_id`、`provider/model_resolved/model_revision`、**`period_start`/`period_end`/`basis`（R2 新增）**。**缺失维度＝`None`＝自己的取值**，永远不等于显式记录的维度 |
| rubric 维度 | 不单独入键：导入时 `rubric_version` 必须等于 `question_version`（否则 `rubric_version_mismatch` 拒绝），故已由 `question_version` 覆盖 |
| 组内择新 | 按 `information_cutoff → observed_at → imported_at → import_sequence → observation_id` 取最大（**不是** import 顺序）；时间**不属于**可比键 |
| **(R2) 新增显示字段** | 字段行与变体摘要新增 `segment_id`、`period_start`、`period_end`、`basis`（详情与 `variants` 均可读）。歧义 judgment 上这四个键为 `null`——未选择可比维度时不得暗示某一维度 |
| 公开入口 | `stockwiki.quick_scan_profiles.build_profiles/build_entity_detail`（只读）；`>=8` 命中只走 `search(...)` |
| 无查询期变体选择 | **公共接口目前没有安全的查询期变体选择能力**，因此未选择可比维度时一律 `ambiguous` 并退出筛选（`unknown`，不返回公司）。要让某个变体参与条件，只能在**导入侧明确只保留该可比变体**（测试 `test_explicitly_selected_single_comparable_variant_decides_the_condition`：选低分 2 不命中、选高分 9 才命中）；本包**没有**发明任何默认选择 |
| golden | `logs/golden/query_variant_ambiguous_ok.json`（R2 重生成，`variant_key` 含新增维度） |

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

> **R2 重生成说明**：同一命令对 R2 树重跑，`query_variant_ambiguous_ok.json` 的
> `variant_key`/`variants` 多出 `segment_id`/`period_start`/`period_end`/`basis` 四键，
> `backup_owner_registry_ok.json` 只有 `created_at_utc`/`recorded_at_utc`/`workspace_root`
> （临时工作区路径）随运行变化；其余 golden 字节未变。第一轮 golden 保留在 git 历史
> `6d1dddb:docs/handoff/SW-REPAIR-02/logs/golden/`。

## 9. 尚缺接口

- C06/C07 envelope 的正式 schema 冻结与联合校验（总控 / G3）。
- 真实 QA 输出 → W05 导入 → ACK → UI 的端到端接口 golden（跨仓，`not_run`）。
- TTL/字段注册表接口（`freshness_policy_available=false` 仍为真）。
- W15 replacement mapping 接口（`GAP_REPLACEMENT_MAPPING` 仍为显式缺口）。

## 10. `content_hash` 的字节口径与从 commit 重建（SR02-5）

**（R2 修正）** 第一轮 `handoff.json.interfaces[*].content_hash` 用的是**交付时工作树字节**的
sha256（本机 `core.autocrlf` 把检出转成 CRLF），且 `quick_scan_variant_projection`
（声明 `quick_scan_profiles/1.0.0`）绑的是 `quick_scan_rows.py` 的工作树 hash
`ce206537…` —— 文件与契约不对应，且工作树字节无法从 commit 复算。

R2 起统一为：

| 口径 | 定义 |
|---|---|
| 单文件条目 `content_hash` | `sha256(git show <result_commit>:<path> 的字节)`，即 **git blob 字节**，与本机换行设置无关 |
| 多文件条目 `content_hash` | `sha256(canonical_json(manifest))`，`manifest = {"byte_basis": "git_blob_at_<result_commit>", "files": [{"path": ..., "sha256": <blob sha256>}, ...]}`，canonical_json = `json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))` |

R2 的两个多文件绑定：

- `quick_scan_variant_projection` ← `stockwiki/quick_scan_profiles.py` + `stockwiki/quick_scan_rows.py`
  （`cb068968cf577f81ed54edeb50f064f64e832c636c86ce00091749796e8e7bbc`）
- `quickscan_search_http_payload` ← `stockwiki/ui_quick_scan.py` + `stockwiki/ui_static/app.js`
  + `stockwiki/ui_static/index.html` + `stockwiki/ui_static/styles.css`
  （`2be992188da50470d84d28e6853249001ba47551b705b01e2b1eb31c8ba5456c`）

从 commit 重建（任一台机器、任意换行设置都得到同一值）：

```bash
# 单文件（git-bash；PowerShell 管道可能改字节，建议用 Python 或 git-bash）
git show c83c148af35407a5ae01072314ba9bd17e59b3d9:stockwiki/quick_scan_query.py | sha256sum
# 等价 Python（推荐）
python -c "import hashlib,subprocess;print(hashlib.sha256(subprocess.run(['git','show','c83c148af35407a5ae01072314ba9bd17e59b3d9:stockwiki/quick_scan_query.py'],capture_output=True).stdout).hexdigest())"
```

**工作树 vs git blob（9 项仅 EOL）**：`export-manifest.json` 的 `files[]` 同时记录
`sha256`（工作树字节）与 `git_blob_sha256`（commit 字节）以及
`eol_only_difference`。R2 生成时 20 个受管文件中 **9 个**工作树与 blob 字节不同，
**全部且仅**是 CRLF↔LF（`eol_only_difference=true`），**内容差异 0 项**：
`quick_scan_backup.py`、`quick_scan_backup_manifest.py`、`quick_scan_profiles.py`、
`quick_scan_query.py`、`quick_scan_rows.py`、`ui_static/app.js`、`ui_static/styles.css`、
`tests/test_swr_backup.py`、`tests/test_e2e_quick_scan_ui.py`。
**旧日志一个字节未清洗、未重算 hash**：`logs/` 下第一轮的 RED/GREEN/full-gate 日志
保持原字节（`artifacts.json` 对它们按当前磁盘字节记录 sha256，用于核对文件未被改动），
第二轮证据一律另存为 `*_r2.*` 新文件，不覆盖旧证据。

R2 的 `handoff.json` 接口条目（`c83c148`）：

| 条目 | content_hash（git blob / 多文件） |
|---|---|
| `stockwiki.quick_scan_backup_manifest/1.0.0` | `58897c13a190f55dc25b63889aa35a682932ff7cea89db8cd63358329e259fc6` |
| `stockwiki.quick_scan_backup_owner_registry/1.0.0` | `58897c13a190f55dc25b63889aa35a682932ff7cea89db8cd63358329e259fc6`（同一生产文件） |
| `quick_scan_query_snapshot/1.0.0` | `accedc49f4b0e20aa651ea246008f1b98e962a09128758a95ce93eb1e88b1f2e` |
| `stockwiki_w09_read_primitives` / `quick_scan_query/1.0.0` | `accedc49f4b0e20aa651ea246008f1b98e962a09128758a95ce93eb1e88b1f2e` |
| `quick_scan_variant_projection` / `quick_scan_profiles/1.1.0` | `cb068968cf577f81ed54edeb50f064f64e832c636c86ce00091749796e8e7bbc`（多文件 manifest） |
| `quickscan_search_http_payload` / `ui_quick_scan/1.0.0` | `2be992188da50470d84d28e6853249001ba47551b705b01e2b1eb31c8ba5456c`（多文件 manifest） |
| `legacy_query_producer_9f552a67`（consumed） | `271b1ba2434123180d27a64437e3f14487d390ffb5c6276471e5302a06c0639a` |
| `sw_ready01_frozen_acceptance_cases`（consumed） | `72b2e1250947a705f87426557ccdf8b09121d761ba09ae89da3df152db81d452` |
| `swr02_remediation_counterexamples`（consumed，R2 新增） | `e9f40166752d17e7324a729098c83a9f5a2f1e4558b9eeb974c29b2671ac68e2` |

SR02-1 最终输入（IQS 只读 intake，未改动一个字节）：`segment.json`
`0f1751603fe4f20d60f365783a9fe4cd307534445c86d9f5975d1e3d009d2dda`、`period.json`
`379994a517ad8fbb89c565bd8e518f153e1f4fe8b648a8dd012c5e9c748321c0`、`basis.json`
`35c71cb0a38991033832bbae488a159c9dfa7a219f650ac6f49690fdff6f3b72`（bytes 21058 / 21241 /
21227），见 `export-manifest.json.remediation_inputs`。
