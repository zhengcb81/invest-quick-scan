## 2026-10-17 — 最终独审前又修复 REVIEW-CAL 证据板绑定问题

五包的已知修复均已通过各自测试并提交；QUERY、SOURCE、RESUME 的独立反例审查已闭环。最终独审还差 REVIEW-CAL-06 与 RETRIEVAL-AUDIT-07 两包，以及将五个最终源码提交和本次PWF字节绑定并完成签收。本条新增的 REVIEW-CAL 修复须一并纳入独立复核。

总控静态预检发现 REVIEW-CAL 1.1 的 `source_context` 校验在实际调用方未提供 evidence board 时，仍接受输出自报的哈希；调用方提供了哈希时，缺失哈希也能通过，`evidence_board_reason` 亦未与调用方绑定。新回归先重算两个摘要并复现“未抛出 CalibrationError”，修复后覆盖伪造、遗漏、正确绑定和错误 reason 四种情况。REVIEW-CAL-06 新提交为 `9817dcbc5a44a8b0dcca7b3bc69fae4ef98985d4`；全包离线测试 `124 passed`，23.17秒。输入锁 `968fc8a41653e24e0701feea9bc75353bff90e923ecd96f37f6b8334818d1233` 未改，516个锁定文件只复制到隔离测试根，测试后已清理。

完整测试须给子进程 `PYTHONPATH=<lab>/src`；Windows下加 `PYTHONUTF8=1` 后 124 项通过且无编码告警。首次全包命令缺少源码路径时有9个子进程导入/设置失败，正确环境下复跑通过，这不是代码缺陷。证据见 `runs/remaining-package-final-review-2026-10-17/root-review-review-board-evidence-2026-10-17.json`。检索审计包本轮只作静态检查，没有发现新的确定缺陷或改动；其此前159 passed/1 skipped和独立反例GREEN仍需最后独立复核。

独立审查子进程因平台使用额度上限中断。平台提示额度于 **2026-10-22 18:08** 恢复（显示时区未确认）；在此之前不把总控自审冒充独立签收。若恢复后没有新发现，预计同日完成两包复核、最终绑定和PWF提交推送；若发现新问题，则修复后再由同一独立审查者复核，完成日顺延一个修复周期。当前状态细节见 `docs/implementation/reviews/remaining-packages-live-status-2026-10-17.json`；旧 `controller-status.json` 因被归档manifest绑定而保留为历史检查点。

下一步：额度恢复后让真正独立的 reviewer 完成 REVIEW-CAL-06 与 RETRIEVAL-AUDIT-07 的最终源码/测试/commit复核，并检查三个已关闭包的当前提交；输出真实 `passed` 且 `open_findings=[]` 后绑定五个源码commit和当前PWF，再正常提交并推送IQS既有origin。

# 剩余五包修复与验收检查点 · 2026-10-17

**工程修复、实际测试及五个源仓提交已完成；整包最终独立签收尚未完成。** 独立审查进程被平台usage limit中断，不能把这一检查点当作最终passed。机器状态见[controller-status](../reviews/remaining-packages-2026-10-17/controller-status.json)。本轮0收费请求、0下载、0生产数据库/名单写入。

| 包 | 最终源码commit | CLI/包版本 | 实际验证（有重叠，不相加） |
|---|---|---|---|
| QUERY-ENTITY-07 | `dd1f5f1fc26b` | 1.0.0 | 143 passed / 1 skipped；真实lock父junction独立0→3 |
| SOURCE-TIME-07 | `e8a31c22aa9e` | 1.0.0 | 169原套件+6旧回归+2新语义回归通过；最后说明文字改动仅重跑2项及公开35case validate |
| RESUME-CHAOS-06 | `f76bb65e089c` | 1.0.0 | 85 passed集中；最后两个根字段校验变更后12项相关测试通过；实际28case/20 mockHTTP |
| REVIEW-CAL-06 | `9817dcbc5a44a8b0dcca7b3bc69fae4ef98985d4` | 1.1.0（保留1.0入口） | 124 passed；另修证据板上下文严格绑定；双物理根8条公开CLI、每根58项synthetic匹配、业务字节一致 |
| RETRIEVAL-AUDIT-07 | `9324b345f4ad` | 1.0.0 | 159 passed / 1 skipped；root代执行3个真实junction全部拒绝；独立编写的空结果/finite JSON反例由root原样复测GREEN |

## 已落地修复

- QUERY：非有限/超长数、null扩展契约、所有普通输入及锁入口的父junction。真实锁入口独立RED成功读取，修后exit3，正常入口保持exit0。
- SOURCE：明确截止前与当天发布时间的区别，第三方转载不能冒充官方原件；REAL012已有相反记录，不能支持“冻结材料一致”；REAL007缺million表头仅部分支持，同时修正作者supports自述，原引文/问题不改。35题仍19 real/16 synthetic，分布7 supported/5 partial/14 contradicted/9 not_assessable。工程校验不认证实际ticker或金融值。
- RESUME：任何frozen执行前核全部consumer、精确模块来源、报告内容/context及嵌套计数/容器/布尔类型、casebook版本和数量；输出先检、worker原生隔离、自有超时PID回收。四项精确上游故障窗口仍unsupported（C06/C07/C16/C27），不能以近似公开API测试冒称完全覆盖。费用unknown/预约保留，不改为免费。
- REVIEW：按真实casebook重建公开投影/分类/匿名映射，修复重复命题、争议计数、IO残留。显式1.1闭合schema/envelope，content_sha对整个业务对象去自身，stable_business另字段另协议；路径/UTC在独立诊断，旧1.0完整指纹语义/fixture兼容。两物理根实测业务字节一致，诊断不同。
- RETRIEVAL：去原始请求水印、语义validate及匿名派生绑定、输入link拒绝、完整target计数、空检索仍可完成双人比较、finite JSON typed拒、URL只规范scheme/host而保留path/query大小写。rd09已确认的legacy错误校准通过private-only结构化needs_adjudication排除两项post-hoc校准分母；A/B一致性分母不变，不把原始性当真值，不把校准分歧称金融错误。

## 实际独审与未完事项

真正不同agent `/root/remaining_package_final_review` 已静读三包、真实复现并独立GREEN query/SOURCE/RESUME发现，并在RETRIEVAL复审中提出空检索/JSON/URL/legacy校准问题。最终新1.1 REVIEW和RETRIEVAL全部修订尚未获得它的完整复审与最终Git/PWF绑定。三名子agent随后都返回平台usage limit，**没有生成最终passed；这里不伪造签收、不另发整改卡**。

root原样执行其独立编写的检索反例脚本，最终空来源target完成比较、两类非法数字均InvalidInput；这只是总控复测，不冒称agent最终签字。各Lab现有remote均为空，只作正常本地提交，不新建remote。IQS的本检查点文档/薄证据推送既有origin，实际commit/推送回执保存在本机runs；本页不预先编造未来commit。

恢复时先读controller-status，再读[新agent交接](../handoff-for-new-agent.md)最新段。继续同一个整包独审，不重复已完成原CONTEXT/DeepSeek实验、不增加helper审批。审查缺口关闭后再签收并回到原T4/scorer/owner主线；不能现在启动正式2000公司扫描或授生产资格。

## 证据与环境

薄归档在`docs/implementation/reviews/remaining-packages-2026-10-17/`。旧acceptance、initial-source-binding和原作者review是各历史阶段快照；其中pending/旧commit/旧测试数字不自动覆盖controller-status中的最新commit。完整日志、候选和冻结锁在本机各runs；归档不含公司文档、数据库、密钥、完整private map或答案集。

正常Git提交逐项核受测working raw与CAS、按既有Git过滤的commit blob，未跳hooks/改全局配置。REVIEW首次提交因未配置仓库author失败，保留32项准确staging后仅在正常commit调用中复用IQS既有身份，无global/local git config改动。其他writer的2026-10-10 README保留且不纳入提交。

自有三个followup临时树已清1344文件/184733025 bytes；其余新修复/独审副本清理结果另存清理回执。冻结输入及原T4/生产库须在最终检查时复核raw SHA；保留历史日志和未知费用，不重发、不伪造全局环境清零。
