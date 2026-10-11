# IDENT-EDGE-01-R1：四类同包缺口集中整改

本卡给一个独立 harness，唯一写根 **`C:/Users/郑曾波/Projects/iqs-identity-case-lab`**；不自动认领，不与另一个 writer 同时实施。任务是修复已有 27 个候选案例的真实来源/时期/解析/交接缺口，保留六类框架与未映射状态；不做身份 resolver、StockWiki master/serializer、扫描资格、公司池或金融结论。

## 开工输入与实际基线

先读 [正式验收结论](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/reviews/parallel-packages/2026-10-11/IDENT-EDGE-01-acceptance.md)、[完整独立审查](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/intake/parallel-acceptance-2026-10-11/ident-edge/independent-review.md)、[实际反例结果](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/intake/parallel-acceptance-2026-10-11/ident-edge/result-final.json)、[本批共同规则](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-11/handoff-rules.md)、[原卡](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-11/IDENT-EDGE-01.md)、[输入锁](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-11/inputs.lock.json)。这些总控文件全只读。

接收 HEAD `3a2a26b8f6ade8cebf1e2deb60f5410ca0d567b0`，branch `codex/ident-edge-01`。冻结清单 raw SHA `86d0197e9e41c8437544ad1777a18ac6407f28f10a79f95237588e67f9a700c8`，候选原 raw SHA `bd75c3886908ad49ad85239d083e65bd83de99353ba60a29feaa0ee3bbd9c883`；15 个锁内输入本轮已匹配。开工如有 HEAD 前进先记录实际状态，逐字节确认冻结输入；漂移先通知总控，不 reset/clean/stash、不恢复源码、不自行改总控锁或 `.git`。CodeGraph 未初始化须遵守 AGENTS 的询问要求，不能擅自写索引或其他仓配置。

PWF pin 到 Lab 内 `docs/handoff/IDENT-EDGE-01/remediation-01/planning/`。不写 Lab 旧 planning/handoff/artifacts 或总控 PWF。`runs/ia01` 是已经结束并清理的总控运行根，不得恢复或借用。

## 精确修改 allowlist

以下路径均相对唯一 Lab 根；不列出的文件只读。现有未提交改动须先确认 owner，不能顺手删除或提交。

- 修改 `src/iqs_identity_case_lab/validate.py`、`src/iqs_identity_case_lab/cli.py`，必要时仅 `guards.py` 的本地输入边界；复用现有 CLI/退出码，禁止新造执行器/身份 resolver。
- 修改 `content/identity-edge-candidates.json`、`content/_facts.json`、`content/source-checks.jsonl`、`content/collection-ledger.jsonl`、`content/collection-plan.json`，以及 `content/short-facts/FACT-I01-*` 至 `FACT-I06-*`；新增纠正事实使用同组新的稳定 fact_id，保留旧事实原字节归档，不能把缺证据改成已证实。
- 修改 `tools/build_case_pack.py`、`tools/record_facts.py` 以保证公开产物可再生；不改冻结工具、输入锁或 locked-inputs。
- 新增 `schemas/iqs-identity-edge-candidate-2.0.0.schema.json`；如果 collection/report 合约实际改变才新增对应 `2.0.0` 文件。现有 `1.0.0` schema 原字节只读保留。新增必需根字段属于新合约，不继续冒用原 1.0.0。
- 修改现有 `tests/test_unit_material.py`、`tests/test_red_boundaries.py`、`tests/test_integration_lock.py`、`tests/test_e2e_cli.py`、`tests/test_offline_guarantee.py`，必要时新增 `tests/test_r1_counterexamples.py`。不改变 guard 来让失败变绿。
- 修改 `README.md` 说明最新入口/归档读取；新增且只写 `docs/handoff/IDENT-EDGE-01/remediation-01/` 内 planning、archive-v1、handoff、summary、artifacts、interfaces、case-map、logs、isolation、review；临时文件仅 `runs/ident-r1-<本次唯一id>/`。

`fixtures/locked-inputs/`、所有原 1.0.0 schema、旧 `docs/handoff/IDENT-EDGE-01/` 文件（除新增 remediation-01 子根）均不可变。StockWiki、StockQA、IQS、其他 Lab、company-wiki、用户配置/密钥、生产数据库/名单全只读。使用正常 Git 提交只提交本卡文件，不设 remote、不推送、不跳 hooks。

## 实施要求（四类一起修，不增加小 gate）

**1. 真实主体/locator/短事实闭合。** 不能把 names/aliases/identifiers/listings/parties 里的任意 ref 当定义。公开 validate 应加载本包实际来源记录，核稳定 fact_id、保存短事实原 bytes/raw SHA、重复定义、引用存在和主体/具体 locator/字段/时期支持范围。来源 metadata 和保存字节只证明记录一致，不自动证明事实真假；工具不对网络来源自行签 verified。给每个实质字段可追溯的支持范围，不允许借别公司、别时期或 generic 原则撑当前具体值。

`CASE-I05-control-valid-to-open` 的虚构 00999 可保留为明确合成控制，使用自己的 synthetic 标记/事实，不再标 HKEX 实证 source_checked。`CASE-I02-ownerref-alphabet-golden` 保留真正历史 golden 的只读 cross-reference，去掉 SMIC→Alphabet 的错误事实链；不能克隆 golden 生成新 owner 正例。I06 的 Apple 值原 secondary 页确有，不能以“伪造编号”修；如仅保留教程示例就 partial/exploration，字段短事实须补准确，官方真实案例不足诚实 unresolved。能获得官方出处可追加独立短事实，不凭 authority 字符串变成核验。

**2. 事件类别、状态和半开区间。** 每个 time_point 明确指向自己的 subject 和挂牌 locator、判断的是挂牌存续还是交易状态；不能遍历任一挂牌端点就推断所有对象。`[valid_from,valid_to)` 检查早于 from、from、区间内、to、to 后；未知 from/to 保持未知，null to 不单独证明 active。停牌开始、首次挂牌、公告日、生效日分开，不把停牌日填 valid_from。

8039 的真实来源明确取消上市于 **2026-10-12 09:00 香港时间**。保存事实必须保留该已知精度。为避免无必要扩大实现，本轮采用明确日级政策：如果 time_point 只有日期，取消日 `2026-10-12` 的挂牌存续结果保持 unknown/需要时刻，不能声称整天都不存续；`2026-10-13` 才可据此判断已取消。若现有输入另有完整时刻，按香港时区 09:00 的真实边界处理，但不得私造时刻。历史 day-only 合成 `[from,to)` 控制仍按其自己声明的日级假设正常通过，不能冒充该公告的精确正例。停牌交易状态在 09:00 前后的含义另行标注，不与挂牌存续混用。

Citi 表中的 `2019-07-19 Ratio Change / 2019-11-20 Other` 不能错配；公告日没有证据时也不能当实际比例生效日。现行 8:1 可保留，旧比例/生效期仍 unknown，不下载 PDF 或猜历史值。89988 的人民币柜台起点由目前 FAQ 不支持，应 null/unknown 或追加真实独立出处，不能沿用 2019-11-26 香港上市日。独立报告已有准确 URL 和对应限制。

**3. 严格本地 JSON 入口。** 共用 loader 拒根和嵌套重复 JSON 键、非 JSON 污染、未来不支持版本、超界 bytes/数组/深度，保持 exit 2；正常当前格式必须能读，semantic ref/时期矛盾仍 exit 4。不把前置路径/版本/foreign ref 错误当目标机制已测试。只保留本地文件 validate/export/明确 legacy-audit 能力，不增加网络/任意 URL/shell 执行。

**4. 合约版本和可核交接。** 最新 pack 按新 `2.0.0` 闭合 schema，具有共同 `pack_id/inputs_lock_sha256/source_refs/limitations`，保留候选固定状态。`pack_id` 是排除自身字段后 canonical JSON SHA，raw 文件 SHA 另记；原 master inputs.lock、Lab 冻结 SNAPSHOT、source 文件 SHA 语义不得混用。lock 定位和事实引用按显式相对路径，拒跨根/秘密/reparse，不通过字符串后缀找文件。

修改活跃候选前，在 remediation-01/archive-v1 逐文件保存受影响的 1.0.0 candidate/schema/来源记录/必要短事实原 bytes/raw SHA 清单，不复制整仓或真实生产 DB。旧版本继续可在明确 audit-only 路径读取，报告 legacy/needs_review/not_mapped/not_run；不得静默将原字节改成新合格包或覆盖历史 golden。最新 validate/export 只接受完整新合约；未来版本明确 unsupported。稳定 case_id 保留；旧 case 语义若改变记录新 revision/version 及迁移说明，新增事实用新 fact_id，不偷改旧档。

## TDD 与一次集中验收

先保留真正 RED，再在上述受影响组完成修复；稳定候选一次相关回归、真实公开 CLI 正反例和一次独立 review。现有 43P 可作受影响回归集合，不能不改就反复跑或把重叠 selector 相加；不重做六类预研，也不设字段/helper 审查门。

| 必需鉴别例 | 正常控制与失败预期 |
| --- | --- |
| ref 闭合 | 正确主体/locator/保存事实可读；alias FACT-MISSING、实际文件缺失/原 SHA 不符、别公司或别时期事实失败。00999 合成资料仍可读，不能成为 source_checked 实证。 |
| 来源资格 | 真实已闭合官方候选保持候选状态；明确 partial 教程可探索、unknown 不填假确定。要测升级路径，先让同题 ref/版本/路径全部合法，再只改目标资格字段；原 source-status-upgrade 被 foreign ref 遮挡的记录不作此机制证据。 |
| 时间 | 从前/from/内/to/后正常与反例，指向两个不同 locator 防混判；真实停牌与挂牌分开；8039 日级取消日 unknown、次日取消，真实09时事实保存；Citi旧比例及89988起点未知可正常收录。 |
| JSON/版本 | 正常新版本成功，重复 schema_version（9.9.9 后合法版本）及嵌套重复键 exit2，未来版本拒，超界拒；真正旧1.0归档 audit 正常，不将其标最新完整包。 |
| 包/导出/交接 | 四根字段与ID/锁/来源匹配，逐字段漂移拒；同输入两次全新导出的稳定 bytes/SHA 相同；失败无半份正式输出、已有不同输出拒覆盖；输入锁/原golden前后字节不变。 |

不得新增金融 human gold 或伪 StockWiki verified 正例。证据必须记录实际 tool_exit 与 case_expectations_met、命令/PID/终态、stdout/stderr/JUnit/raw SHA、原始分母；timeout/yield 不是通过。正常中文/空格/随机 cwd、秘密路径、自有真实 junction 等现有隔离控制继续保持。

测试全部 Python `-B -X utf8`，不传 API key 环境，TEMP/TMP/TMPDIR/日志/pytest cache/basetemp/子进程 cwd 全在自有唯一 run 根；使用原离线 guard 及普通文件写边界，无网络/API/生产 SQLite。如需补来源，只在 harness 人工公开网页阶段，沿原账本记真实次数/失败/必要短事实，不下载/保存网页正文/截图/PDF，合计不超过原卡 60 次采集上限。原账本次数不一致先诚实说明，不能造成功记录。

## 交回要求与终态

交 `docs/handoff/IDENT-EDGE-01/remediation-01/handoff.json` 及 summary/artifacts/interfaces/case-map/logs/isolation/review/planning。handoff 沿总控原模板/schema，完整列实际 base/product/result/handoff HEAD、branch、dirty 状态、授权范围和每个修改路径；既有 f8c/0152/640db 三角色必须解释准确，不重建或伪写旧历史。

先完成产品/测试正常提交，再完成本轮 PWF，最后生成 `artifacts.json`：每个实际文件的相对 path、bytes、**64 位 lowercase raw SHA256**、用途、source_class；目录不可代替文件清单、不写自身散列循环。新交接提交单独记录，完整 result_commit 指实际产品提交，不把最终 handoff HEAD 代替产品。保留旧交接原件，仅新记录说明历史差异。

严格清理自己的 run：先核所有 PID 实际终态、精确绝对根/owner、原路径无 foreign reparse/链接、路径集合/大小/SHA；只 unlink 自有 junction 本身并证目标不变，再删自有下载/副本/假秘密/缓存/输出，保留轻量证据。清理失败诚实列出，不扫描/清理共享 TEMP 或别包运行根。不得提交含秘密、真实生产库、整页正文或副本 golden 的新增外部公开材料。

最终状态建议 `ready_for_coordinator_acceptance`，四类逐一用同一次集中证据说明 passed/failed/unresolved；本包不自行签 accepted，不关闭 StockWiki 身份、G2b/C06/G3/O01、金融准确性、TH/IN 或全池门。交回后停止写入，等待总控一次包级续验。
