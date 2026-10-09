# JR1/JR3 集中独立审查（修复前冻结候选）

本轮结论：**发现 1 项 P1、2 项 P2，当前候选不能作为 JR1/JR3 合格交付。** 三项均在独占 `runs/r13a/reviewer-unique` 合成工作区用实际候选代码复现；没有修改候选、源仓、冻结历史 driver/adapter 或联合控制器，没有提交或发布。总控已收到发现并将同批 TDD 修复；本报告只评价以下修复前 SHA，后续新候选须重新验证。

## 范围与冻结输入

StockWiki 源基线为 `c40de21403720306ba21edbf71b9634a40ee58f8`。审查的私有运行时为 `runs/r13a/sw`，公开约束为 IQS `schemas/quick_scan/exchange.schema.json` 的 `$defs/ImportAck`。四个已授权文件与第五个尚待源仓授权文件的冻结 SHA 如下；两次独立探针均检查前后相同。

| 文件 | SHA-256 |
| --- | --- |
| stockwiki/quick_scan_import.py | 5bf472347b29064162fa4ba8d0944ee8566f62cb09bd6f201e4007a88be54b53 |
| stockwiki/quick_scan_observations.py | 5010fce6c906b04787ebcaab61c6174df4fd8fa91b53992e037479075b1c8934 |
| stockwiki/quick_scan_backup_manifest.py | ad75cacec6e83590dbe25cfbe63f557ef828909c0fafb891ea4fcb21cf1175c2 |
| tests/test_quick_scan_observations.py | f54b4d0068d34a4e98865e5821b8265ab4f534dbd2edec12b5a1c4e9d01fcc27 |
| tests/test_quick_scan_delivery.py | 6beb0785fffd764aa3cb5fb95a286dd871bf3bfacf29df5557b5ce6167fec309 |

另检查本批 `test_joint.py`、`joint_harness.py`、`qa_actor.py`、准备/运行/源漂移控制器和实际源演员调用方式。原 `affected-final-01` 的 93P 是该批受影响软件测试的真实结果；它未覆盖以下反例。没有重跑全仓或 UI。

## F1 — P1：新 ACK 可以永久不符合冻结公共 1.0

位置：`quick_scan_import.py:226`（包级预检）、`:284`（item 完整性）、`:554`（拒绝 DTO）、`quick_scan_observations.py:441`（新 ACK 生成与保存）；测试缺口见 `test_quick_scan_observations.py:1145`、`:1182` 与原 CLI 短 ID 正例 `:1071`。

根因：包级检查只要求 item 为 dict，没有先验证公共 ACK 所必需的 `item_id`、`observation_id`、`payload_sha256` 形状。item 拒绝分支原样使用坏地址，或生成 `itm_invalid_0`、`obs_unknown`、空 SHA。store 直接将这些值写入十字段 ACK 与审计；删除 enriched 字段和映射 error taxonomy 不会使错误地址合法。正常 observation 也没有 `^obs_[a-f0-9]{64}$` 检查，所以旧短 ID 可进入 accepted 新回执。

三个实际 SW CLI 反例均正确重算 package hash，使用真实 `observation-import`，没有手造正向 ACK：

| 输入变更 | CLI / 回执 | 持久结果 | 冻结 ImportAck 校验 |
| --- | --- | --- | --- |
| 原合法 item 改 `item_id="bad"` | exit 0，rejected / invalid_payload | observations 0，acked_items 1；ack_for 原样重放 | item_id pattern 失败 |
| item 改为空 `{}` | exit 0，rejected / invalid_payload | observations 0，acked_items 1；ack_for 原样重放 | itm_invalid_0、obs_unknown、空 SHA 三项失败 |
| observation_id 使用原测试同类短值 `obs_cli_1`，item/package 内容地址重算 | exit 0，accepted | observations 1，acked_items 1；ack_for 原样重放 | observation_id pattern 失败 |

公共 ACK 已永久保存，后续 StockQA 的严格接收不会通过；因此不能称为原生合法公共 DTO。93P 中大量原短标识单元/CLI正例只检查状态和幂等，新 `_jr13_public_ack` 仅应用于选定的 SHA 观察 ID 正例，形成了覆盖缺口；它不代表整批新回执均通过冻结 schema。

最小修复：在任何 store 操作前对整包全部 item 的公共地址做严格形状检查；缺失/非法地址必须整包具名拒绝、零 observation/ACK/conflict/audit 写入，不伪造 ID。`apply_decisions` 也需在整批事务前预检这些地址以防公开直接入口绕过。保持合法地址的 per-item invalid_payload 回执能力和历史原 ACK 只读重放。两个获批测试文件的正例短 ID 改成明确的 deterministic synthetic SHA 标识，同时保留非法/缺失地址负例；不要放宽冻结 schema 或更改历史已存 JSON。

证据：[results.json](independent-review-evidence/results.json)、[probe.py](independent-review-evidence/probe.py)、[原始 stdout](independent-review-evidence/probe.stdout.log)。每个 CLI 原始 stdout/stderr 及实际 argv 仍保留在 `runs/r13a/reviewer-unique/<case>/`。

## F2 — P2：already_present 的原导入审计会指向 rejected

位置：`quick_scan_observations.py:427`，特别是 `:430` 的 `WHERE observation_id=? ORDER BY ack_sequence LIMIT 1`。

根因：查询同一 observation 的最早 ledger 行，未限制为 accepted 原导入，也未保存该有效原导入的 item_id。前置拒绝具有相同 observation_id 时，最早 ACK 不对应 authoritative observation 的写入。

实际反例：先将 SHA observation 提交给缺少 `E_NOT_YET` 的合成身份库，得到 rejected/missing_entity；随后通过公开身份 store API 新增同一合成 entity。只改变 created_at 并正确重签的第二包 accepted，第三包 already_present。第三包 `import_audit_for(...).original_import.package_id` 指向第一包 **rejected**，而不是第二包 accepted。状态轨迹为 `[rejected, accepted, already_present]`，未覆盖原历史数据，也未修改产品代码。

最小修复：新 audit 的 original reference 必须选中真实 accepted ledger 原导入，保存其稳定 package_id/item_id/sequence/received_at。原已存历史 enriched ACK 和旧 audit 不做读时投影或改写；增加上述公开导入顺序的回归断言。

证据：[results.json 的 wrong_original_reference](independent-review-evidence/results.json)，实际原/后续三个 ACK 与第三 audit 全部保留。

## F3 — P2：schema 1→2 并发正常导入出现伪迁移失败

位置：`quick_scan_observations.py:142`，其中 `:146` 在 `:154` 的 BEGIN IMMEDIATE 前读取 user_version，随后 `:156` 无条件创建新 audit 表。

根因：两个 importer 都可以先读到 schema 1。第一个获锁创建并提交 schema 2；第二个等待后获锁，继续使用过期的本地 version 1 决策，再次 CREATE，收到 `table quick_scan_import_audit already exists`，被包装成 `observation_migration_failed`。busy_timeout 与 BEGIN IMMEDIATE 只串行化写入，不能使之前读取的 version 刷新。

受控反例调用两个真实 `import_package`，用 sqlite Connection 子类在各自真实 PRAGMA 已执行后安排 barrier，使两者都看到版本 1 再争用原 BEGIN IMMEDIATE；所有候选 SQL 未改变。实际一项 success，另一项 `ObservationImportError / observation_migration_failed`，错误详情为 `table quick_scan_import_audit already exists`。最终版本 2、一张 audit 表、旧 ACK 保持原样，无数据损坏；失败的是本来有效的一次正常导入。这是新 schema1→2 复用窗口的确定性反例，不是同时写源代码。

最小修复：将 schema 版本读取和全部版本判断放进同一 BEGIN IMMEDIATE 之后，持锁重读后再决定是否迁移，并明确处理 commit/rollback；不要仅用 IF NOT EXISTS 隐藏不完整 schema。增加双连接同时升级、旧 ACK 保真以及新旧导入成功的回归，保留现有失败回滚测试。

证据：[concurrency-results.json](independent-review-evidence/concurrency-results.json)、[concurrency_probe.py](independent-review-evidence/concurrency_probe.py)、[原始 stdout](independent-review-evidence/concurrency.stdout.log)。

## 已检查行为、控制器判断与限制

- 新十字段 ACK、consumer 三字段、公共 error/status 映射，与独立 reason/detail/original reference 保存确实在 apply_decisions 的同一事务；现有 audit 插入失败触发器会使 observation 和 ACK 回滚。没有发现该已覆盖事务路径的额外问题。
- 文本/bytes loader 对所有对象使用 object_pairs_hook，覆盖数组中的对象；parse_constant 与有限 float 校验拒绝 NaN/Infinity/±1e400。直接 dict 的有限值/字符串键/支持类型检查以及活动祖先集合循环检查在入库前执行。未将 dict 用例视为原始重复键 JSON 证明。
- schema1→2 升级不回填或重写旧 ACK；ack_for 与同包 replay 保留 stored JSON 对象，历史 enriched 原文/SHA 保留测试存在。现有新版 sender 的严格 wire 接收不会因多余 legacy 字段自动完成 delivered；本审查没有认证任何 legacy DTO 转换/恢复注册策略。公开 `legacy_wire_pending` 操作信号及真实历史 paired 恢复仍不可由当前软件 fixture 推定。
- 第五文件仅将 observation schema 备份上界 1→2，现有真正 backup/verify/restore 软件路径与新增 roundtrip 保存新 audit 和原 ACK；该私有验证不构成第五源文件授权或生产迁移授权。
- 联合正向控制器从 SW 公开 store_id 获取合成目标描述，事前 bind 然后 begin，再读取真实 CLI ACK 和 ack_for；未发现手工删 ACK 字段制造成功投影。当前 QA actor 对第二合成执行在调度前明确请求 model B，没有放松 production Q10 的 requested/resolved 校验。此结果不证明任意 alias A→B 合格。
- 原 joint-01 registry 漏导出、joint-02 LF/CRLF 文件域不匹配、joint-03 请求模型不匹配及 sourceguard invalidate 必须保留。总控在本轮末报告 joint-04 已终态 4P/1F：缺实体 case 没有先建立空身份库，以及替身 b/llm_apis.json 读取被 runner 误算为真实 key；这是待用独立命名日志修正的控制器/fixture问题，本报告没有将其当作产品 green 或自行修改。
- 31 项合成 CLI 往返、低分/null/unknown/not_applicable/watch/长 body、暖恢复零额外 HTTP 等仅为软件隔离证明，不是真实 issuer/facts/query owner golden，也不证明金融内容准确性、真实搜索、真实付费或双 owner 灾备闭环。

## 隔离证据与交接

两次实际命令为 `C:\Miniconda\python.exe -B -X utf8 <owned-root>\probe.py` 与同参数 `concurrency_probe.py`，均 exit 0（探针成功捕获产品反例，非产品验收通过）。cwd 为 `runs/r13a/reviewer-unique`；环境先清空再按现有 controller 相同系统变量白名单传入，只设置 guard/PYTHONPATH/UTF8/no-bytecode/独占 TEMP 与禁止 live 配置。Python 和其 CLI 子进程继承既有 `sitecustomize`，SHA 为 `696dfeecfc0aedc0732a3677faafa97c539cb3aaf12a04303359b109089d3858`。

独占根中 key-opens 与 network-attempts ledger 均不存在；所有测试 DB 和日志保留在自身根，没有移除已有根，没有源仓或生产 DB 写入。原始脚本、结果、stdout/stderr 和 guard 已按字节归档，逐文件原 SHA 与副本 SHA 一致，详见 [evidence-manifest.json](independent-review-evidence/evidence-manifest.json)。候选五 SHA 前后相同。原 22GREEN/61GREEN/93P、原 RED 和失败控制器日志未动。

交接：停止对旧候选执行新探针，由总控在四获批路径集中修复和复验；审查自身证据保持冻结。本报告不授予第五源文件写权，不自行发布。
