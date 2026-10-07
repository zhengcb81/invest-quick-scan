# SW-READY-01 交付摘要（StockWiki）

包：SW-READY-01｜W12 + U01 + U02｜lane: stockwiki
源仓：`C:/Users/郑曾波/Projects/StockWiki`（唯一写入仓）
开工基线：`master@9f552a6741dd093dc760ad6965458989cd027251`（clean，与 inputs.lock 一致）
交付提交：`0d76dc39e8d9d53d451b1ce84c7147b0dd1bd2c5`（父提交 `0b48919065a912f1da10d89d36bf6bf1e659db88`）
证据提交：见本目录（`docs/handoff/SW-READY-01/`）

## 1. 问题与最终行为

**W12（可恢复的快扫存储）**
- 之前：只有面向周备份的 `backup.py`（整目录 zip、直接拷贝 `.sqlite`、无逐文件 hash/水位/恢复前置），没有只覆盖 quick-scan 权威库的一致快照，也没有空目标恢复与保留策略。
- 现在：`quick-scan-backup create|verify|restore|list|prune` 对 `data/quick_scan/**` 做 SQLite 在线备份（WAL 中已提交页进入快照，绝不裸拷活跃文件），产物是**版本化 manifest**（逐文件 sha256/`user_version`/integrity、ACK+观察+成员+subject 水位、名单/观察/ACK/规则版本、创建 UTC、恢复前置、`executor_side=unverified` 与 `执行侧未核验、禁止恢复收费`）。创建走暂存目录→逐文件复验→改名，失败不留半份；`verify/restore` 在写入前拒绝 hash 篡改、缺文件、多余文件、未知/更新 schema；恢复目标 `data/quick_scan` 必须为空（REV-04）；`prune` 只删本包自带合法 manifest 且校验通过的备份目录，`data/`、身份/名单/观察/费用历史一律不碰。运维手册：`docs/quick-scan-backup-restore.md`。

**U01/U02（真实观察的列表与详情）**
- 之前：`quick_scan_query` 只投影身份+证券（`profiles_from_store`），没有 UI 路由，评分/状态/来源/恢复从未接到读取面。
- 现在：`quick_scan_profiles` 把身份、挂牌、别名、analysis subject、W05 不变观察投影成查询 profile——原分、`answer.status`、provider/model、信息截止/扫描/入库时间、题义/模板/方法/发布包版本、payload hash、`answer.evidence` 来源全部保真；W06 时效按 `valid_until=None` 判为 `missing_date` 且 `policy_available=false`（不臆造 TTL，不冒充有效）；W07 三值规则引擎做分项条件（`>`/`>=`…，AND/OR，pass/fail/unknown 带叶原因，页面不自建规则）；W08 `evaluate_recovery_watch`+`company_card` 消费恢复观察与原低分；W10 runtime 计数接入详情。**没有已验证质量汇总就 `quality_score=null`/`未接入`，绝不算平均分**。
- UI：`stockwiki ui` 现有服务新增 `快扫结果` 视图与 4 条 `/api/quickscan/*` 路由：名称/代码/别名搜索、市场/行业筛选、分项条件、**四个独立视图**（全部公司/质量白名单/恢复观察/待补数据）、默认 50/上限 100 的冻结快照分页（翻页不重不漏，数据变动只提示刷新）、hash 保留筛选上下文（刷新/后退/复制链接/返回列表）、详情按题族分组逐项展示短依据/来源/时间/模型/版本，事实与产业链显式 `unavailable`，缺口清单（facts、跨版本可比、历史、质量汇总、时效策略、替代映射）常驻可见。
- 协议：所有读取返回声明 `protocol=stockwiki_w09_read_primitives`、`c06_envelope_validated=false`、`facts_available=false` —— **旧返回没有被改标签冒充 C06 envelope**。

## 2. 任务范围

| 任务 | 内容 | 结果 |
|---|---|---|
| W12 | 快扫库一致性备份/校验/恢复 CLI+manifest+手册+保留策略 | 完成（本包接口验收） |
| U01 | 列表、分项筛选（AND/OR）、四视图、稳定分页与导航上下文 | 完成（浏览器验收） |
| U02 | 评分详情、依据/来源、缺失/过期状态、恢复观察 | 完成（浏览器验收；历史/跨版本/替代关系按缺口显示） |

不在范围（按包文明确排除，未借此宣称完成）：W15 模块待办与路由快照、F03–F05 事实关系、W14 全模型时间比较、X 一键启动、U03/U04 完整版、跨仓恢复总验收（G3）、执行器（StockQA）数据库备份与费用账本。

## 3. 入口命令

```bash
# W12（路径全部绑定 --root 授权工作区）
python -m stockwiki.cli --root <ROOT> quick-scan-backup create [--name NAME]
python -m stockwiki.cli --root <ROOT> quick-scan-backup verify  --name NAME
python -m stockwiki.cli --root <ROOT> quick-scan-backup restore --name NAME   # data/quick_scan 必须为空
python -m stockwiki.cli --root <ROOT> quick-scan-backup list
python -m stockwiki.cli --root <ROOT> quick-scan-backup prune --keep 3
# 详细错误码/前置条件/演练脚本：docs/quick-scan-backup-restore.md

# U01/U02（现有 Web 服务）
python -m stockwiki.cli ui --host 127.0.0.1 --port 8765
# 打开 http://127.0.0.1:8765/ → 顶部“快扫结果”
# API: GET /api/quickscan/capabilities | POST /api/quickscan/search |
#      GET /api/quickscan/coverage | GET /api/quickscan/entity?entity_id=

# 验证（单包定向 → 交付门，只跑一次 --full）
python -X utf8 -m pytest tests/test_quick_scan_backup.py tests/test_quick_scan_profiles.py \
  tests/test_ui_quick_scan.py tests/test_e2e_quick_scan_ui.py tests/test_sw_ready_01_real_data.py -q
bash scripts/check_all.sh            # daily：304 passed
bash scripts/check_all.sh --full     # 交付门：990 passed, 18 pre-existing skipped, coverage 81%
```

## 4. 版本兼容

- `quick_scan_query/1.0.0` **加法扩展**：新增 `protocol`/`c06_envelope_validated`/`score_condition_engine`/`freshness_policy_available`（capabilities）、`conditions`+`condition_combine` 入参与 `condition_rules`/`score_conditions` 出参、`coverage.by_field`、行内 `score_fields`/`aliases`/`coarse.stage|company_type`/`roster`。原有字段语义、分页快照、四视图、`facts_available=false` 不变；`search` 对旧调用（不传 conditions）输出兼容。
- 不可变观察导入（W05）、身份决策、评分尺、W06/W07/W08/W10/W11 模块**零修改**（只读消费）。
- 新增 manifest `format_version=1.0.0` / `schema=stockwiki.quick_scan_backup_manifest/1.0.0`；主版本不匹配即 `unsupported_format_version` 拒绝。
- 模块规模门：新模块 385/357/129/93/545/542/128 行，全部 <600；`quick_scan_store.py`(969) 为既有基线警告。

## 5. 验证

| 批次 | 命令 | 结果 | 日志 |
|---|---|---|---|
| RED（TDD 反例先行） | `pytest tests/test_quick_scan_backup.py -q` / `test_quick_scan_profiles.py -q` | ModuleNotFoundError（预期红） | `logs/RED-w12-backup.txt`、`logs/RED-u01-u02-projection.txt` |
| GREEN W12 | `pytest tests/test_quick_scan_backup.py -q` | 12 passed | `logs/GREEN-w12-backup.txt` |
| GREEN 投影+查询 | `pytest tests/test_quick_scan_profiles.py tests/test_quick_scan_query.py tests/test_quick_scan_refresh.py tests/test_quick_scan_backup.py -q` | 34 passed | `logs/GREEN-u01-u02-projection.txt` |
| GREEN HTTP 路由 | `pytest tests/test_ui_quick_scan.py -q` | 8 passed | `logs/GREEN-u01-u02-http-routes.txt` |
| GREEN 真浏览器 E2E | `pytest tests/test_e2e_quick_scan_ui.py -q -s` | 5 passed（种子 22.8s；2000 家条件+分页 4.9s） | `logs/GREEN-u01-u02-browser-e2e.txt` + `logs/e2e/*.png` |
| GREEN 真实数据隔离副本 | `pytest tests/test_sw_ready_01_real_data.py -q` | 2 passed | `logs/GREEN-real-data-acceptance.txt` |
| 交付门（一次） | `bash scripts/check_all.sh --full` | ruff ✓、validate-framework ✓（仅既有 store 969 警告）、990 passed/18 skipped（18=既有 CWP 17+Windows narrative 1）、coverage 81%（诊断） | `logs/check_all_full.log` |
| 提交门 | `python -B scripts/checks.py --static-only` | ALL CHECKS PASSED | — |

包内新增测试 34 个（12 W12 / 7 投影 / 8 HTTP / 5 浏览器 / 2 真实数据）；case 映射见 `case-map.md`。

## 6. 未解项（含部分完成）

1. **UI-03 过期样本**：TTL/`valid_until` 由“中央字段注册表”提供（IQS 契约明确不在实现里臆造统一 TTL），当前无合法可导入的过期观察 → 浏览器端无法展示真实 `stale`；`stale` 分支由单元测试覆盖（`test_stale_score_never_counts_as_a_current_hit`），页面对全部字段如实显示 `有效期未记录`。等字段注册表接入后补浏览器用例。
2. **UI-05 替代题对应关系**：依赖 W15 路由快照（本包范围外），详情以缺口 `replacement_mapping_unavailable` 显示，不编造对应关系。
3. **UI-09 查询故障注入（浏览器级）**：错误状态由 HTTP 层反例覆盖（未知字段 400、未知路由 404、缺失实体 `entity_not_found`、空视图 `empty_reason`），浏览器端故障注入用例 `not_run`。
4. **store_id 跨根差异**：`store_id` 按路径派生，跨根恢复后新 ACK 会带新值（历史 ACK 保持原值），已写入 manifest `restore_preconditions`；跨 owner 的实际对账留待 G3 总控联调。
5. **执行器侧**：StockQA 数据库/费用账本不在本备份内，所有回执固定 `执行侧未核验、禁止恢复收费`；执行侧未提供快照时不得恢复收费（按包文，由 QA-NET-01 owner 提供）。
6. **review**：独立审查未做，`review.status=not_run`（不自签 approved）。

## 7. 回退方式

- 全部为**加法**改动（新增模块/路由/视图/CLI），无数据库迁移、无 schema 变更、无既有语义修改。
- 回退：`gitrevert 0d76dc39e8d9d53d451b1ce84c7147b0dd1bd2c5`（代码+测试+文档一次还原），UI 入口与 `/api/quickscan/*` 随之消失，`quick-scan-backup` 命令消失；权威数据不受影响（本包未改任何既有数据文件，测试只写临时根）。
- 已产生的备份目录 `backups/quick_scan/` 可整目录删除（不属于权威数据）。
- 回退后若需要保留证据，`docs/handoff/SW-READY-01/` 可单独留存（不影响运行时）。

## 8. 实施期间的仓状态变化（记录新快照）

- 开工观察：`master@9f552a67…`、clean（与 inputs.lock 一致）。
- 2026-10-07 ~11:04（本包实施期间）：总控/其他进程将 `master` fast-forward 至 `0b48919`（合并 `codex/g2-sw-daily`：`scripts/checks.py` 单一检查接口、framework validators、`.planning/`、`docs/implementation/g2-sw-daily/`）。
- 归属判断：**与本包路径零重叠**（本包未触碰 scripts/、framework validators、core CLI、g2 文档），按包 README“无关变化记录新基线”处理；本包提交的父提交即 `0b48919`，`git show 0d76dc3 --stat` 可逐行核对本包 20 个文件。
- 另观察到未跟踪文件 `nul` 在会话中出现又消失（非本 worker 创建或删除，未暂存、未清理）。
