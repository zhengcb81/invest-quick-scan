# SW-REPAIR-02 summary

- 包：`SW-REPAIR-02`（lane `stockwiki`）
- 基线：`master@04dfc5190589a8bbe224a47e94b045779c884b80`（开工时 clean）
- 结果：`master@9f9e0afe16a327b475cb7a6e3d40bd1578bb9b0f`（**未 push**，只在本地 master）
- 写授权：用户在分派消息里批准唯一 writer + 卡列路径；执行中另行向用户确认了
  `backups/quick_scan/owner_registry.json` 这一个新持久化文件与新增
  `tests/test_swr_*.py`、`docs/handoff/SW-REPAIR-02/`。
- 交接目录：`docs/handoff/SW-REPAIR-02/`

## 最终行为

| ID | 最终行为 |
|---|---|
| **SWR-1** | 恢复目标可以**不存在**，也可以是**已存在的空目录**，两者都成功。非空、复制途中被并发写入、symlink/junction 目标、解析到工作区之外的目标，全部在写任何字节**之前**拒绝，并在发布前再检一次。对目标唯一会执行的操作是（复检后的）`rmdir`——OS 对非空目录必拒——失败时把原目标建回；**全程没有对目标的递归删除**。失败只清理自己的 staging。 |
| **SWR-2** | `prune` 有四道闸：非 partial、非链接、冻结结构 + 逐字节校验、以及 `backups/quick_scan/owner_registry.json` 中 `name ↔ manifest_sha256` 的受信登记。外来自洽 manifest（空 files / 外来 schema / `1.garbage` / name 不符 / 重复或越界路径 / 改写 `executor_side`）、未知、损坏、链接目录、以及**没有登记的旧备份**全部 `skipped`，不自动 adopt。旧无登记备份仍可只读 `verify` / `restore`。 |
| **SWR-3** | `staging.rename(final)` 是唯一提交点，且在失败处理**之内**；失败会回滚 owner 登记并清空暂存目录。manifest 的成功字段在提交前只存在于暂存目录，不会被 `list`/`prune` 看到。`list` 显式输出 `partial` / `complete`；`.name.partial-<id>` 残留被标为 partial、被 prune 跳过、且连 `verify`（名称规则）都无法接收。 |
| **SWR-4** | 观察按**可比键**（subject+revision / scope+security+listing / 题义版本 / provider+model）分组；组内按**信息时点**取新（不是 import 顺序），因此倒序导入的旧观察不会变成“最新”。多个不可比组时 `score_fields[field_id]` 变为 `status="ambiguous"`、`score=null`、`variants` 全列（W07 判 `unknown`，高分无法入选），而详情 `groups` 保留每个变体的原始 subject/scope/model/版本/分数。同 issuer 多挂牌仍一行，同名不同 issuer 不并行。 |
| **SWR-5** | 浏览器可增删任意多条分项条件（至少两条），AND/OR 只是提交给服务端，评分始终由 W07 三值引擎执行，JS 不重算。`qsStateKey` 绑定全部 leaf + combine，改任一 leaf 即丢弃旧 snapshot 并重新签发。真实浏览器验证“一项过、一项不过”：AND 共 0 条、OR 共 137 条且 LEAD 行内两个叶子分别显示 命中/未命中。unknown 显示 `待核实`、详情 `无分`，绝不补 5。 |
| **SWR-6** | 无条件查询的 `query_hash` 保留 Git `9f552a67` 的 `{text,filters,view}` 口径，旧真实 snapshot 继续翻页且 `ordered_ids` 逐条一致；带条件查询使用**另一种** hash（追加 `conditions`+`combine`），两形态互斥，因此错查询、错条件、跨形态复用一律 `snapshot_query_mismatch`。协议以 `quick_scan_query_snapshot/1.0.0` 显式声明在 `capabilities.snapshot_protocol`。 |

## 边界

- 只动了施工卡授权范围内的文件；`stockwiki/ui_quick_scan.py` 无需改动（保持原样）。
- 没有新建第二研究数据库，没有改动 `data/quick_scan/` 下任何 sqlite（**迁移：无**）。
- 新增的唯一持久化文件是 `backups/quick_scan/owner_registry.json`（运行时数据，gitignored）。
- 未改 IQS / StockQA / CWP / 研究技能 / 安装镜像 / 生产库 / 名单 / config / 凭据 /
  原 SW 交付 / 原冻结 RED；原 `acceptance_cases.py` 一个字节未改。
- 没有为了对齐残缺包放宽 Observation/ACK 语义。
- `live=off`：清空 `*API_KEY`/`*API_TOKEN` 环境，外部网络/搜索/模型/下载计数为 0；
  仅本包 loopback HTTP（证据见 `logs/green_e2e_browser.log` 的 `loopback HTTP only` 行）。

## 兼容与回退

- **manifest**：`format_version`/`schema` 字符串未变，旧备份仍可 verify/restore；
  变化只是“从写入升级为强校验”，旧的合法 manifest 本来就带这些字段。
- **owner 登记**：新文件；旧备份缺登记 ⇒ prune 跳过（保守方向），不 adopt。
- **查询**：`QUERY_RULES_VERSION` 未变；新增的只是 `capabilities.snapshot_protocol`、
  行级 `score_condition_outcome`、`coverage.by_field.*.ambiguous` 计数。
- **UI URL**：新 `c=` 参数；同时兼容旧的 `field/op/value/combine` 链接。
- **回退**：回退本 commit 即可回到原行为；回退**不会**删除已产生的观察、备份、
  owner 登记、水位/ACK 与历史（owner 登记只影响 prune 是否放行，verify/restore
  不依赖它）。回退演示**没有**通过恢复生产库进行。

## 已做

1. 只读复核基线与原 freeze，保留原 RED；把原 7 场景映射进本仓（`tests/test_swr_cases.py`），
   并用**最终版**测试文件对**基线源码**复跑得到 `6 failed, 1 passed`。
2. 先做 SWR-1/2/3（空/非空/并发/foreign 自洽 manifest/损坏/链接/rename 异常/WAL/旧备份兼容），
   再做 SWR-4/6，最后 SWR-5 真实浏览器。
3. 一次受影响批次（74 passed）+ 一次真实浏览器 E2E（11 passed）+ 一次 `--static-only`
   （exit 0）+ **两次** `--full`：在本包 commit `9f9e0af` 上 1032 passed / 18 skipped
   （`logs/check_full_at_9f9e0af.log`），以及在并行 worker 的无关 narrative 提交合入后
   于合并树上 1046 passed / 18 skipped（`logs/check_full.log`），两次均 exit 0。
4. 原 `acceptance_cases.py`（sha 未变）对本包源码 7/7 通过（audit-hook guard 下）。
5. 关闭本包服务/进程/浏览器，核端口与逐路径清理，见 `isolation.md`。

> **master 在本包施工期间发生了并行变动**：代码 commit `9f9e0af` 之后、handoff commit
> `753dfca` 之前，另一个 worker 把无关的 `42fba06878fc58c01f58c0206f4d694a68e4d451`
> （narrative 文件，与本包路径**零重叠**）fast-forward 到 master，随后又有若干 narrative
> 提交。本包的 `result_commit` 因此固定为 `9f9e0af`；两次全量门分别对应“本包自身提交”
> 与“合并后状态”，见 `handoff.json.verification.checks`。

## 未做 / not_run

- TTL/replacement 策略、W15 replacement mapping：`not_run`
- 真实 QA C06 → W05 导入/ACK → UI 整链、跨 owner 双库恢复：`not_run`（总控 G3）
- F05 / 真实身份与事实 golden：**missing**（`logs/golden/identity_golden_status.json`）
- G3 / F05 关闭：不在本包权限内
- 独立审查：`review.status = not_run`
- 原 990 套件逐 hunk 重跑：按施工卡禁止，以一次 `--full` 代替

`complete` 仅指本卡定义的**本地交付完成**：六项反例全闭合、WAL 正例保留、真实浏览器
多条件通过、旧 snapshot 与未知状态兼容、环境清理完成。联合项目未验收。

## 准确入口命令

```bash
# 静态门（提交前）
python -B scripts/checks.py --static-only

# 受影响批次（74）
python -B -X utf8 -m pytest tests/test_swr_cases.py tests/test_swr_backup.py \
  tests/test_swr_profiles.py tests/test_swr_query.py tests/test_quick_scan_backup.py \
  tests/test_quick_scan_profiles.py tests/test_quick_scan_query.py \
  tests/test_ui_quick_scan.py -q

# 真实浏览器离线 E2E（11）
python -B -X utf8 -m pytest tests/test_e2e_quick_scan_ui.py -q -s

# 全量门（一次）
python -B scripts/checks.py --full

# 原冻结 7 场景对本包源码（需先重建导出根，见下）
python -B -X utf8 docs/handoff/SW-REPAIR-02/build_export_manifest.py \
  --repo C:/Users/郑曾波/Projects/StockWiki \
  --out C:/Users/郑曾波/Projects/StockWiki/runs/swr02-acceptance-<unique>/export-manifest.json
#   mkdir -p <root>/runtime && cp -r stockwiki tests <root>/runtime/ && \
#   find <root> -name __pycache__ -type d -exec rm -rf {} + && \
#   git show 9f552a67:stockwiki/quick_scan_query.py > <root>/runtime/legacy_quick_scan_query.py
python -B -X utf8 docs/handoff/SW-REPAIR-02/run_frozen_acceptance.py --work-root <root>

# 基线 RED 复现（最终版测试对基线源码）
#   git archive 04dfc5190589a8bbe224a47e94b045779c884b80 stockwiki | tar -x -C <root>/runtime
#   cp -r tests <root>/runtime/tests 且同上 legacy 文件
#   cd <root>/runtime && PYTHONPATH="<root>/runtime;<root>/runtime/tests" \
#     python -B -X utf8 -m pytest tests/test_swr_cases.py -q

# golden 重建
python -B -X utf8 docs/handoff/SW-REPAIR-02/build_goldens.py \
  --repo C:/Users/郑曾波/Projects/StockWiki \
  --out C:/Users/郑曾波/Projects/StockWiki/docs/handoff/SW-REPAIR-02/logs/golden
```
