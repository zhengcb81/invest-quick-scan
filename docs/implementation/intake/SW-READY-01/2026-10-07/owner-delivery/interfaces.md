# SW-READY-01 接口清单

所有哈希均为**原字节 SHA-256**；`inputs.lock*` 标记的来自开工冻结清单（本包只读消费，未修改），其余为本包生成/交付时实测。

## 1. 消费的接口与输入（consumed）

| name | version / 冻结点 | content_hash | 说明 |
|---|---|---|---|
| `iqs.docs.implementation.tasks.json`（W12/U01/U02 卡与 case_ids） | `inputs.lock@2026-10-07` | `a7c6167d4bf9aca56b529bd85bd70b0ae01a99125033e06dcbcdcbb06731bf60` | 只读；scope.task_ids 与 manifest 一致 |
| `iqs.schemas.quick_scan.query.schema.json`（C06 查询契约） | `inputs.lock@2026-10-07` | `e7fc264b43d85e4cdd5c82a71b9fedb579dd0fc1196f3c5fde661f14fa1756f8` | 只读对照；**本包不实现 C06 envelope**，读取面显式 `c06_envelope_validated=false` |
| `iqs.docs.implementation.contracts.exchange-and-query.md` | `inputs.lock@2026-10-07` | `9f2559ba91c49210906fa3c1c75606f3c403e6ca7d5f896908fb1371675f398b` | 只读：浏览/筛选/查询不触发模型与费用的边界 |
| `iqs.docs.implementation.contracts.freshness-and-jobs.md` | `inputs.lock@2026-10-07` | `2d8f6d4be7ae05ef996e7cdb71f58dff355bf3229de4241b6a0dc8acbeee3f93` | 只读：`valid_until` 未知 → `missing_date`；TTL 由中央字段注册表提供，本包不臆造 |
| `iqs.docs.implementation.contracts.question-modules.md` | `inputs.lock@2026-10-07` | `039f789b0905c69705798288fbbfa8dc884b0fa70b7b2af9e1f221be804512a6` | 只读：模块/替代关系属 W15/F06，缺口显示 |
| `iqs.references.standard-output.md` | `inputs.lock@2026-10-07` | `2545f8e9001a794f9d05f0a0c642d965b2709f160cf3a12dd8910b1502c6731b` | 只读：answer 结构（evidence/confidence/information_as_of） |
| `iqs.docs.implementation.results-ui.md` | 交付时实测（未在 inputs.lock 冻结，本包未修改） | `74e9053cc005bffcbf477484645f92a6008a0ce9a1912099ee82356e3b621be5` | U01/U02 行为规格来源 |
| `iqs.docs.implementation.acceptance-cases.json`（DB-05/REV-04/STORE-03/UI-01…14） | 交付时实测（同上） | `6793d24ce5704dddd1297852315acc807127c9870d6bcc18ed4d828b21ea9d37` | case-map 的断言原文来源 |
| `stockwiki.tests.fixtures.quick_scan_exchange_example.json`（C06 官方交换 fixture，既有 owner 测试） | 交付时实测 | `fbd555de608abcb071b9f93d0c2b20b0436ad40b62a92b2c0a0a4efa44b7adb4` | 本包测试不直接改写字节；其正反例由既有 `test_quick_scan_observations` 在 `--full` 中回归通过 |
| StockWiki W05 公开导入入口 `quick_scan_import.import_package` / CLI `observation-import` | `1.0.0`（源码，交付提交内） | 见 `git show 0d76dc3` 中 `stockwiki/quick_scan_import.py`（**未修改**） | 本包 fixture 全部经公开导入入口进入，不手工补库 |
| StockWiki W06/W07/W08/W10/W11 模块（freshness/rules/recovery/delivery/refresh） | 源码，交付提交内**未修改** | 同上（0 diff） | 只读消费：时效判定、三值规则、恢复卡、runtime 计数、名单 |

> 本包没有消费任何外部 producer 的新 golden 字节；测试中的交换包由测试内 fixture 生成器按 C06 结构自行构造并明确标为 fixture/synthetic（`test_quick_scan_observations` 的 `_package/_observation`），不冒充生产或真实公司证据。

## 2. 产出接口（produced）

### 2.1 快扫备份 CLI + 版本化 manifest（W12）

- **version**：CLI 行为 `stockwiki quick-scan-backup/1.0.0`；manifest `format_version=1.0.0`，`schema=stockwiki.quick_scan_backup_manifest/1.0.0`
- **content_hash（样例 manifest 原字节）**：`5fccd9140bb97bcaeb03d45cf767a73b797c24b58b679d07ba3580dfe3843baf` → `logs/golden/quick_scan_backup_manifest_sample.json`
- **样例 `manifest_sha256`**：`61c8e341b5bd0922c3883259c8e0c6bffd4de575a89023e05397813886d80e53`（= 该 manifest 除 `manifest_sha256` 外规范 JSON 的 SHA-256；与 `create` stdout 一致）

签名（全部路径解析自 `--root`，仅允许 `<root>/backups/quick_scan/<name>` 与 `<root>/data/quick_scan`）：

```bash
python -m stockwiki.cli --root <ROOT> quick-scan-backup create  [--name NAME]   # 成功 stdout=1 行 JSON, rc=0
python -m stockwiki.cli --root <ROOT> quick-scan-backup verify  --name NAME     # rc=0 {"ok": true, ...}
python -m stockwiki.cli --root <ROOT> quick-scan-backup restore --name NAME     # 目标 data/quick_scan 必须不存在或为空
python -m stockwiki.cli --root <ROOT> quick-scan-backup list                    # rc=0 {"backups":[...含无 manifest 的外来目录]}
python -m stockwiki.cli --root <ROOT> quick-scan-backup prune --keep N          # N>=1；只删自有且校验通过的备份
# 错误：stderr 单行 JSON {"error_code","detail"}，rc=2
```

错误码全集（`docs/quick-scan-backup-restore.md` 有表）：`backup_name_invalid`、`backup_name_required`、`backup_target_exists`、`backup_source_empty`、`backup_failed`、`manifest_missing`、`manifest_invalid`、`manifest_hash_mismatch`、`unsupported_format_version`、`file_missing`、`file_hash_mismatch`、`unexpected_file`、`integrity_check_failed`、`schema_mismatch`、`schema_newer_than_supported`、`restore_target_not_empty`、`keep_invalid`、`quick_scan_backup_failed`。

manifest 必含字段：`created_at_utc`、`files[].{path,workspace_path,bytes,sha256,backup_method,user_version,journal_mode,integrity}`、`counts`、`watermarks.{ack,observation,roster,subjects,candidates}`、`versions.{rules,roster,observations,ack,subjects}`、`store_identity`、`consistency.cross_file_atomic=false`、`restore_preconditions[]`、`executor_side{provided=false,status=unverified,fee_restoration=prohibited,message="执行侧未核验、禁止恢复收费"}`、`manifest_sha256`。

**正反例 golden（owner 隔离生成，命令见 §4）**

| golden | sha256 | 含义 |
|---|---|---|
| `logs/golden/backup_create_ok.json` | `4dedc6a7255d5fb673f95b1f8e782aa4627f8b56e15db88ca0af48da55b3f3f7` | create 回执（逐文件 hash + 水位 + executor 拒绝收费） |
| `logs/golden/backup_verify_ok.json` | `3ed05166994ae6d46967fe0217a68a9c32d553863180a8740f390be48d8444c0` | 校验通过 |
| `logs/golden/backup_restore_ok.json` | `f712323178eafc2b699b9960242a8f69c5708d9588b6a49122dac2ed75a498db` | 空目标恢复回执（`fee_restoration=prohibited`） |
| `logs/golden/backup_restore_nonempty_rejected.json` | `2a9bf24b55ed6a880588dd33451749f4f89eaf73b31d0aa5fdb4c16966f56195` | 反例：目标非空 `restore_target_not_empty` |
| `logs/golden/backup_verify_tampered_rejected.json` | `f2d33d3a848dfee07a0fa34470e05fd10b1a52d158b8b2716dbf15509f44f5da` | 反例：字节篡改 `file_hash_mismatch` |
| `logs/golden/backup_verify_missing_rejected.json` | `374e3b4d10792403b5fd76578404857ffe5c425ae58d50247b24e7c7a9eed740` | 反例：备份不存在 `manifest_missing` |

### 2.2 读取接口（W09 原语，加法扩展）

- **version**：`quick_scan_query/1.0.0`（rules_version 不变，字段加法）；投影 `quick_scan_profiles/1.0.0`
- **protocol（新增，明示不是 C06）**：`protocol="stockwiki_w09_read_primitives"`、`c06_envelope_validated=false`、`facts_available=false`、`fact_relations_available=false`
- **content_hash（capabilities 样例原字节）**：`41308c65df64d1a444bb2bb70f9565f739eeba3243fcdf61b68dd1de3443ef0b` → `logs/golden/query_capabilities_ok.json`
- **content_hash（带分项条件的 search 样例）**：`2eed4641d4f3fad135887894d00f5630f1b3175aa0ac7fe79e187da27b75dc03` → `logs/golden/query_search_condition_ok.json`

签名：

```
GET  /api/quickscan/capabilities                 -> capabilities + projection/routes/workspace_root
POST /api/quickscan/search
  body: {text?, filters?{market,industry,security_type}, view?, page?, page_size?,
         snapshot?, conditions?[{field,op,value}], condition_combine?("all"|"any")}
  -> {rules_version, protocol, c06_envelope_validated, view, page, page_size, total,
      rows[], next_page, snapshot, refresh_recommended, status, empty_reason, scope,
      condition_rules?{policy_id,policy_version,rules_sha256,combine,conditions,
                       outcome_counts,leaf_reasons,averaged_score_emitted:false},
      llm_calls:0, network_calls:0}
GET  /api/quickscan/coverage?market=&industry=&security_type=
  -> coverage + by_field（字段目录，供条件选择器）+ market_wide_claim:false
GET  /api/quickscan/entity?entity_id=ENT_...
  -> {entity,securities,segments,cohort,roster,subjects[],groups[],score_summary,
      recovery{watch,card},quality{quality_score:null,averaged_score_emitted:false},
      runtime,capabilities,gaps[],protocol,llm_calls:0,network_calls:0}
```

加法字段（旧调用不受影响）：capabilities `protocol`/`c06_envelope_validated`/`score_conditions_supported`/`score_condition_engine`/`freshness_policy_available`；search `condition_rules`、行内 `score_conditions`、`score_fields`、`aliases`、`coarse.stage|company_type`、`roster`；coverage `by_field`。既有字段（分页快照、四视图、`empty_reason`、`facts_available` 等）语义未变。

正反例 golden：

| golden | sha256 | 含义 |
|---|---|---|
| `logs/golden/query_capabilities_ok.json` | `41308c65df64d1a444bb2bb70f9565f739eeba3243fcdf61b68dd1de3443ef0b` | 协议/能力正例 |
| `logs/golden/query_search_condition_ok.json` | `2eed4641d4f3fad135887894d00f5630f1b3175aa0ac7fe79e187da27b75dc03` | `>=8` 命中 1/待核实 1，`leaf_reasons` 含 `status_insufficient_evidence` |
| `logs/golden/query_search_unknown_key_rejected.txt` | `367fccc875f1995dc80c56e6f509e238655607e1236a7938f99cf27756e7e751` | 反例：`payload_unknown_field: root` |
| `logs/golden/query_entity_not_found_rejected.txt` | `b70d8c6c5e405467de59527374902641e9759742ea539625534083e167f10b61` | 反例：`entity_not_found: ENT_missing` |

其余拒収码（HTTP 层同样为 400 + `{"error": "<code>: <detail>"}`）：`page_invalid`、`page_size_invalid`、`page_size_exceeds_limit`、`view_invalid`、`snapshot_shape`、`snapshot_query_mismatch`、`filter_unsupported`、`conditions_shape`、`condition_combine_invalid`、`condition_unknown_operator`、`condition_threshold_not_number`、`condition_unknown_field`、`entity_id_required`。

### 2.3 分项条件语义（W07，页面不自建规则）

- policy：`policy_id=quick_scan_score_filter`、`policy_version=1.0.0`，树 = `all`/`any` + `condition{field,op,value}`（`> >= < <= == !=`）。
- 上下文来自投影行：`value=reported_score`、`status=answer_status`、`fresh = freshness_status ∈ {fresh, missing_date}`、`check_level`、`observation_id`。
- 结果：`pass/fail/unknown`（W07 固定真值表 + 叶原因 `compared/field_missing/value_null/not_applicable/status_*/stale`）；只有 `pass` 进入列表，`unknown` 计入“待核实”，`averaged_score_emitted=false`。
- 已知过期（`stale`/`event_invalidated`）永远不是 `pass`（`过期不冒充有效`）；`missing_date`（TTL 未接入）按“未记录有效期”处理，页面必须显示 `有效期未记录`，不标 `有效期内`。

## 3. 兼容与降级

- 升级：加法字段与新 CLI/路由；旧调用方零改动。降级（回退本包提交）：新字段/路由/命令消失，W05 导入与旧读取完全不受影响。
- 未接入能力一律显式缺口：`facts_relations_unavailable`、`cross_version_comparison_unavailable`、`history_view_unavailable`、`quality_summary_unavailable`、`freshness_policy_unavailable`、`replacement_mapping_unavailable`、`module_catalog_unavailable`、`no_observations_imported`；不以空列表冒充“无风险/已核实”。
- C06 envelope：待总控冻结并另行接入；在那之前任何返回都自报 `c06_envelope_validated=false`，不改标签。

## 4. golden 生成命令（可复现）

```bash
# 备份类 golden：在任意临时根按公开 CLI 生成（fixture 构造见 tests/test_quick_scan_backup.py::_seed_source）
python -m stockwiki.cli --root <TMP> quick-scan-backup create --name golden   > backup_create_ok.json
python -m stockwiki.cli --root <TMP> quick-scan-backup verify --name golden   > backup_verify_ok.json
cp <TMP>/backups/quick_scan/golden/quick_scan_backup_manifest.json quick_scan_backup_manifest_sample.json
python -m stockwiki.cli --root <TMP2> quick-scan-backup restore --name golden > backup_restore_ok.json
# 反例：对副本翻转一个字节后 verify；对已恢复目标再 restore；verify --name does-not-exist

# 查询类 golden（与 HTTP 路由同一函数）
python -c "from stockwiki.paths import WorkspacePaths; from stockwiki.ui_quick_scan import \
 build_quick_scan_capabilities as c, build_quick_scan_search as s, build_quick_scan_entity as e; ..."
# 或经真实 HTTP：python -m stockwiki.cli ui --port <p> 后 POST /api/quickscan/search
```

（本包实际生成使用 tests 内 fixture 种子 + 上述公开入口；输出即 `logs/golden/` 中字节。）
