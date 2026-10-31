# 当前生产接线与验收范围只读核实

核查时间：2026-10-31 UTC（本次线程；工作目录中的11-01只是标签）；核查者 `/root/audit_mainline_runtime`。仅已知源码、现存不可变验收资料、只读Git及原8766 GET；0收费调用、0公司文档下载、0原数据库写、未启动/停止服务、未运行测试。

## 实际部署与版本

当前IQS HEAD及origin/master同为 `d2c575fc1608da2cf2ddb6df2850305146eb1d97`。外仓实际只读Git：StockQA `0dc799a4553b8bdd6313f2cdaf915f0d5d67e260`；StockWiki `8527bc771692c501517d8f04c387603a92a77ec0`；原UI `03d6b9aa3d45011f09bc77ef69e62b4a1d21e00e`，与前轮签收一致。

`config/dashboard.local.json` 仍使用 `runs/r25-live/owner-workspace`，workspace_kind明确是 `isolated_research`；运行原8766服务不等于迁移到另一正式生产库。执行runtime为 `runs/u25-live/runtime`，54个历史/当前execution bundle、1个import bundle；注册数量不能当54份当前任务或完成公司数。universe_id里214是既有标识，不能从ID推导实时成员数。

实际原 `GET http://127.0.0.1:8766/api/product/doctor` envelope为 `{ok,data,elapsed_ms}`。本轮读取data：`ready=true`、`blocked_reasons=[]`；StockWiki available、StockQA available、model_policy present；`paid_connectivity_tested=false`、API_requests/network_calls均0。这说明部署文件及原owner/执行包可读，不证明每个新包都已获准或付费联网厂商当前畅通。初次脚本未解data而读到null，随即按真实envelope纠正；不是服务故障。

## 已经闭合的工程链

1. 原UI比较/名单已接线：原始组件范围证据是 `docs/implementation/reviews/UI-INTEGRATION-30-2026-10-30/report.md`；其中“仍在进行/下一步108”仅为当时组件节点历史，不是现在整体验收状态。
2. 三市场每家36题、总108有效槽已实际回答/CP/standard/context/封存/入库/exact ACK；口径是105原成功+3真实受控替代，原3failed仍保留。实证见同目录 `native-three-market-recovery/actual-recovery-first-stage-review.json`、`metadata-audit.json`、`cold-independent-final-review.json`。不能写“原108 work全部ACK”。
3. 原8766同配置冷重启前后108所需持久化元数据与ACK不变，0新增HTTP；`cold-independent-final-review.json` 明确verdict `passed_cold_persisted_metadata_reopen_not_TTL`，79HTTP/1865393micros在该节点前后不变。它证明持久化/历史恢复，不证明TTL命中。
4. 真实A/B两次普通新准备→授权/准入→执行→原ACK刷新已完成，额外各1HTTP，累计81HTTP/$1.903319仅是当时历史基线；`native-ttl-and-coverage/README.md`及 `ttl-a-independent-final.json`、`ttl-b-independent-final.json`、`ttl-b-after-ACK-metadata.json`。A真实info_as_of=2026-08-12、B=2026-04-09；当前24h拒绝reuse是现规则预期，不是接线失败。不能写新生成即fresh。
5. 同目录B readonly恢复保留原CP/standard/context/outbox/ACK/费用，0新HTTP，但requested_scope_completed=false：历史引用恢复，不是新研究完成。
6. 有效期内复用→自然过期→正常刷新软件分支有真实原生隔离动态时钟验收，历史1541.604秒。根PWF明确记录，不必重复25分钟整段。但它不替代实际真实模型样本的fresh正例。
7. TIME/RESULT最终读视图已接原服务及原UI，三市场实际浏览器验收，`docs/implementation/reviews/TIME-RESULT-WIRING-2026-10-31/independent/final.json`与report绑定IQS接线C c1ee64f/UI03d6b9a；当前生产runtime与该C一致，后续e8/f16仅测试基础设施。

## 当前真正未闭合的点

- **真实模型答案有效期内复用正例仍未验收。** 原24h TTL+information_as_of把这些实际样本判旧；本轮仅核实既有证据，未再付费询问或篡改旧日期求绿。
- **新TIME按题义多时钟策略尚未成为派发/复用决策。** `scripts/dashboard_temporal.py:build_entity_view`显式 `read_only_shadow`、production_reuse_applied/current_context_verified/reuse_authorized=false；旧113观察中112仅clock解释、1旧release未绑定，证据见最终report。
- **金融可靠性不是软件签收。** ANSWER已经把来源访问与命题审计完成并保留未知，不等于原分数通过金融核验；审核中已发现真实期间/归属/截尾问题。未来何种可靠性门对应白名单使用必须有可执行验收，不可拿测试数或交接形状当通过。
- **215/约2000家持续运行规模没有整体验收。** 三市场研究工作区试用成功不等于全池吞吐/时效/成本完成。原性能瓶颈仍存在，36包新候选更慢，不应装入原服务。

## 避免扩大“阻塞”的口径

当前原StockWiki `stockwiki/quick_scan_freshness.py:freshness_status`按information_as_of/valid_until/事件分类；`observation_compatible`按原question/routing/scope/meaning/cutoff/check_level匹配。**它本来不依赖新TIME的identity_revision或可信verification_receipt。** 所以不能把“新TIME缺这些字段”写成“原扫描/原入库/原24h缓存尚未接通”。原24h策略仍可继续保守使用，真正欠的是实际模型样本fresh命中的证据与更实用的刷新语义。

可信核查凭证、当前identity_revision、按字段披露日历是**如果采用新多时钟复核续期**才必须正确设计的新增集成工作，不能伪造，也不应无范围说明地追加成一切MVP试用的前置。`native-ttl-and-coverage/freshness-semantics-discussion.md`原文当时明确“仅讨论/未来/本次不更改政策”；后续TIME包已实现候选与只读视图，生产策略替换仍未做。建议总控将原缓存fresh正例与新策略生产接管分为两个可判定里程碑，明确哪个是完成原用户承诺所必需，哪个是改进项。

原始目标的可用小范围试用已经存在（用户认可名单、可组合题库、原UI、真实扫描、原入库、比较/名单、历史恢复）。原始“大池持续扫描、跳过近期更新、跨模型/时间比较、主题/行业联动”的整体完成不能单由三家公司演示关闭；这些范围的现状态应由总控另据对应已签接口清单汇总，而非把全项目剩余缩成TIME一个接口。

## 工具与环境说明

CodeGraph context一次有界尝试31秒未返回，已终止，随后仅读取已知具体文件；没有建索引。外仓Git和本地GET沙箱拒绝后，在既有授权内提权只读核实成功。两次按猜测文件名读取不存在，后改读实际目录现有文件；不作为缺交接或产品bug。未将本次shell原始config输出当发布材料，未读取model配置内容或密钥。
