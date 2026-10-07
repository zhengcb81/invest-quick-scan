# SW-READY-01 集中只读接收审查

日期：2026-10-07。审查者：独立 agent `/root/identity_wire_review`。本报告仅写 IQS；未修改 StockWiki、PWF、名单或数据库，未运行测试、应用服务或 API，也未读取凭据。

## 接收结论

**交接工件已查收；实现验收暂不通过，保持 `partial`。** 源码和交接材料中有 6 个固定反例需要 owner 集中整改。现有成果应保留，不重做 W05/身份/规则模块，也不增加逐小节点审查。整改先补对应反例，再运行受影响测试及一次包级验收。

- 实核 StockWiki 当前 HEAD：`04dfc5190589a8bbe224a47e94b045779c884b80`；代码提交：`0d76dc39e8d9d53d451b1ce84c7147b0dd1bd2c5`，20 个本包代码/测试/文档文件。
- `docs/handoff/SW-READY-01/artifacts.json` 的 **48/48** 条目，当前原字节大小和 SHA256 全部相符。
- `handoff.json.status=partial`、`review.status=not_run`；本次报告不回写 owner 原交接，也不将其自报局部完成转成总体验收完成。
- 阅读源码、测试断言、case-map、原始日志及浏览器截图。`check_all_full.log` 记录 **990 passed / 18 skipped / exit 0**；这是 owner 既有运行证据，本审查未重跑、未将覆盖率 81% 作为无缺陷证明。
- CodeGraph 已先查结构，但当前索引未覆盖本包新增模块；随后读取交接索引给出的确定文件，未以猜测路径替代来源。

## 阻断性发现及集中回归要求

### SWR-01｜P1：已有空目标也无法恢复

位置：`stockwiki/quick_scan_backup.py:277`、`:292`。

`restore_backup` 先仅拒绝“存在且非空”的 `data/quick_scan`；复制暂存目录之后又无条件拒绝 `target.exists()`。因此合法备份 + **事先创建的空 `data/quick_scan` 目录**，必然在后一个分支抛出 `restore_target_not_empty`。文档和 manifest 的“目标不存在或为空”并未实现。现有 roundtrip/真实副本/WAL 测试全部在目标目录不存在的情况下恢复，非空拒绝测试不能证明空目录正例。

整改及测试：同时覆盖 absent、已存在空目录、非空目录、复制失败、最终替换失败；合法空目标恢复成功，失败时原目标及历史保留，暂存目录清理。不要通过改文档为“只接受不存在”缩小已承诺的行为。

### SWR-02｜P1：manifest 未验证身份与必要结构，外来目录可被当自有备份清理

位置：`stockwiki/quick_scan_backup.py:198`、`:380`。

`_verify_dir` 仅检查 format 主版本、可重新计算的 digest 和列出的文件内容；完全未核验 `schema=stockwiki.quick_scan_backup_manifest/1.0.0`、必要元数据、非空/无重复文件列表、合法版本结构及执行侧禁止恢复收费约束。`prune_backups` 随后将任何通过该函数的目录追加到 `own` 并删除。

固定反例：外来旧目录里仅有 `quick_scan_backup_manifest.json`，正文为 `{"format_version":"1.0.0","files":[]}` 加上正文的规范 SHA256。该形状通过现有 `_load_manifest` 和 `_verify_dir`：无文件要检查，manifest 本身被排除为 expected。它随后被 `prune` 纳入本包自有备份；有足够新备份时该目录会被删除。同样，换成外来 schema、保留 notes 文件并列出其正确 hash，也没有 owner marker 拒绝。`1.garbage` 亦因只比较第一个段而被当成版本 1。现有 foreign 反例仅测“没有 manifest”，未覆盖这个条件。

此外，restore 回执直接复制 manifest 的 `executor_side`，未验证内容是否仍为 `unverified/prohibited`，可产生与恢复前置冲突的成功回执。digest 是完整性校验，不是合法结构或 owner 身份证明。

整改及测试：冻结明确 manifest schema/版本读取策略，并严格校验必要字段、唯一安全路径、文件大小/版本、owner schema marker和禁止收费字段；未知版本/错 owner/空伪 manifest/重复路径/篡改后重新算 digest 的语义错值均拒绝。`prune` 只处理本模块明确拥有且完整验证的目录，保留外来与不完整目录。集中补反例，不新造一套任务回执。

### SWR-03｜P2：最终 rename 失败留下“看似成功”的暂存备份

位置：`stockwiki/quick_scan_backup.py:177`。

`staging.rename(final_dir)` 位于 `try/except` 清理区之外。复制、写 manifest、复验均成功以后，若最终 rename 因目标竞争创建、共享锁或文件系统错误失败，带合法 manifest 的 `.partial-*` 目录会遗留。`list_quick_scan_backups` 和 `prune` 也未排除此类目录，可能将其显示为完整备份或纳入保留排序。现有 `test_create_is_atomic_on_failure` 只在复制阶段抛异常。

整改及测试：把最终发布纳入失败清理和具名错误处理；故障注入最终 rename，断言最终名和该批暂存目录都不留下成功假象，且不删除竞争者建立的目标。列表/保留策略应显式拒绝 incomplete/partial 工件。

### SWR-04｜P1：按单个 field_id 覆盖会静默合并不等价的分析范围和模型结果

位置：`stockwiki/quick_scan_profiles.py:386`–`:392`（引用起始行，不作行范围链接）。

`_observations_by_entity` 使用 `grouped[entity_id][field_id]=row`，按 import_sequence 的最后一行覆盖。analysis subject/revision、scope、security/listing、model/provider、question/method版本均未参与 variant 选择。后续筛选、恢复判断、详情均只看到这一个值。

固定反例：同一 issuer 的两个不同 analysis subject 对同一字段分别为 2 和 9，或者两个挂牌的证券级字段同名；后导入者覆盖前者，另一个主体的该项结果在详情消失，9 可以进入未选择主体的筛选条件。同一模型历史观察迟到重放也会被称作“latest”。其他字段可来自另一 subject/model/version，从而组装出并不存在的一套公司画像。

现有 `test_two_subjects_stay_distinct_and_legacy_subject_is_not_fabricated` 只断言 subjects 表有两个不同 ID；测试中的**所有观察其实都为未绑定 subject 的 legacy 观察**，未覆盖这个覆盖路径。

整改及测试：保留不等价的 observation variants 与原始维度；选取当前用于筛选/恢复的一组时必须有明确一致的主体、范围与版本选择规则。无法选择则返回 ambiguous/unknown 与原因，不静默把不等价值融合。先覆盖两 subject 同字段、两挂牌范围、两模型、题义版本变化、旧时点迟到导入。**不要求越范围实施完整 W14 比较 UI**，但本包现有 U01/U02 投影必须守住范围边界。

### SWR-05｜P2：浏览器只有单条件，AND/OR 功能和其 E2E 未交付

位置：`stockwiki/ui_static/app.js:1809`、`:1822`。

`qsPayload()` 永远发送 `conditions=[{field,op,value}]` 单个 leaf；控件也只有一组字段/算子/阈值。AND/OR 对单个条件恒等，用户无法表达 `A>=8 AND B>=8` 或 OR。后端两条件单元测试正确，但浏览器 E2E 的 `_apply_condition` 和列表分页用例仅操作一个 leaf。施工包的浏览器接收标准明确要求“分项 AND/OR”，不能以一个无作用的组合下拉框签收。

整改及测试：支持至少两个可增删的条件并保留到导航上下文；真实 DOM 操作两条件，核对 AND/OR 命中差异、unknown 三值结果、接口请求体和详情返回后的条件保留。仍复用 W07，不在 JS 重写评分。

### SWR-06｜P2：同版本的旧查询快照不再兼容

位置：`stockwiki/quick_scan_query.py:243`、`:286`、`:313`。

已只读核对开工基线 `9f552a67`：`quick_scan_query/1.0.0` 的 query_hash 为 `{text,filters,view}`。新实现即使调用者不传 conditions，也无条件哈希额外的 `conditions=[]`、`combine=all`。旧公开返回的 snapshot 翻到下一页时会 `snapshot_query_mismatch`，但模块仍宣称同版本“加法扩展、旧调用兼容”。现有分页测试均从新实现重新生成 snapshot，不覆盖旧接口工件。

整改及测试：无条件筛选保留旧 hash 口径，或设计有明确版本、边界与固定 golden 的兼容读取；不能静默重开快照导致混页。把旧真实返回形状/基线规范 hash作为回归输入，检查第二页和候选导出继续保持原集合。

## 已证实的正确方向与尚未关闭的边界

1. SQLite 使用 `src.backup(dst)`，不是直接复制活跃主 DB；snapshot 转 DELETE journal 后报告其本身的 integrity/schema/watermarks。源码与 WAL 已提交页、未提交事务反例一致；manifest 明确 `cross_file_atomic=false`，未冒充多库原子快照。
2. 未知/N/A/证据不足保留状态和 null，UI 用“无分”，没有默认填 5，也未计算平均质量分；W07/W08 复用，原低分和恢复标记同时展示。HTTP(S) 来源过滤、文本转义、浏览器输入/XSS反例有相关断言。
3. W09返回显式 `protocol=stockwiki_w09_read_primitives`、`c06_envelope_validated=false`、facts=false，未冒充 C06/C07 的完整协议校验。新的接口仍需总控契约冻结/联调，不能靠标签成为 C06 envelope。
4. `store_id` 路径派生导致跨根恢复后的新 ACK 与历史 ACK 使用不同 store_id，这一限制已写入 manifest preconditions 和交接。StockQA执行器/费用快照缺失、跨 owner ACK 水位对账、G3未关闭均明确；本审查不替另一 owner 签收，不允许恢复收费。
5. TTL/真实 stale 浏览器正例、W15 replacement mapping、浏览器级查询故障注入已标 not_run；这些仍 pending。不能把缺策略的 missing_date 宣称为已证明当前有效。
6. 真实数据验收只覆盖 owner 当前 workspace 的身份/名单/subject 与**没有已导入观察**的空评分状态（测试明确断言 `score_fields=={}`）；有分数的真实浏览器 E2E 使用公开导入的 synthetic fixtures。这是有用的两层证据，但尚不证明 QA真实输出→W05真实导入/ACK→UI整链。该跨仓链留待总控 G3。
7. `_fetch_rows` 对 sqlite3.Error 返回 `[]`，可能把 schema不兼容/读取故障显示成“暂无观察”。此处应与已登记的 UI-09 故障注入 pending 一起处理，区分 unavailable/error 与真实空数据；本报告不将该未跑用例改成 passed。
8. Test fixtures 使用临时workspace、loopback guard、浏览器请求拦截、源码中服务器与浏览器 teardown，交接保留隔离清理记录；本审查没有运行其过程，也不独立证明此前所有 TEMP/端口的当前状态。真实副本测试 `_hash_tree(REAL_ROOT)` 当前遍历整个根；后续宜缩到获准的 `data/quick_scan`，避免不必要读取其他项目文件/本地配置。

## 接口与报告快照

下列为本次实际读取的当前原字节 SHA256；48条完整列表以 owner artifacts.json 为准，本审查确认全部相符。

| 文件 | SHA256 |
|---|---|
| stockwiki/quick_scan_backup.py | ff781cd7a5ca92b65182587eefa2dfa4aa6d2bfe0cb396f44e6f6e1c17ef6070 |
| stockwiki/quick_scan_backup_manifest.py | 6ce5dd16b8e2e989e38208cf30abe3a07a2fcc68a6b7ba64f6d4cb0396ca71c5 |
| stockwiki/quick_scan_profiles.py | 11515dd3489772fb0b256712c040be9bc778570de7449ea476aa8c51e653405d |
| stockwiki/quick_scan_query.py | 9ef36001acca2699b0631b8b5431dca0e821157c90bf5ee3ac694ff227e838c6 |
| stockwiki/ui_static/app.js | df2d39b5f8faafd8c073b58d681c6605045a3642be9d693a54b627194a4d0d26 |
| tests/test_quick_scan_backup.py | 065b4ff5d25e8662ffd93726ad3ba3c6c98667f7ad588e4223322ffccb7a5d96 |
| tests/test_quick_scan_profiles.py | 5a4e05ae0206af77ab04b34e9c809bca42958f675c7098a9e5df6af5b5b250ec |
| tests/test_e2e_quick_scan_ui.py | 28f589e783d4f9dd303d0a4c7e5a983f3094f407e43201b346df71bced15848b |
| docs/handoff/SW-READY-01/handoff.json | 1e40fc35354c8e789c77260800d6371c40ea4319d1db78fb98d2b5eaaffc7283 |
| docs/handoff/SW-READY-01/logs/check_all_full.log | acb662b7c883161dbe8c6e0ebd5105d56918a1b5a0048ec5b10f8d1978200791 |

本报告的反例依据为源码条件与基线工件的只读推演；本轮未执行复现程序，所以没有捏造失败测试日志或运行计数。owner 应按以上反例补集中 TDD 实证，再交总控验收。已通过的48条归档完整性、已有代码成果和990项历史运行记录继续保留。
