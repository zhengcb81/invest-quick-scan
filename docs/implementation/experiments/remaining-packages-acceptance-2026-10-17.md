# 剩余五包修复与验收检查点 · 2026-10-17

**工程修复、实际测试及五个源仓提交已完成；整包最终独立签收尚未完成。** 独立审查进程被平台usage limit中断，不能把这一检查点当作最终passed。机器状态见[controller-status](../reviews/remaining-packages-2026-10-17/controller-status.json)。本轮0收费请求、0下载、0生产数据库/名单写入。

| 包 | 最终源码commit | CLI/包版本 | 实际验证（有重叠，不相加） |
|---|---|---|---|
| QUERY-ENTITY-07 | `dd1f5f1fc26b` | 1.0.0 | 143 passed / 1 skipped；真实lock父junction独立0→3 |
| SOURCE-TIME-07 | `e8a31c22aa9e` | 1.0.0 | 169原套件+6旧回归+2新语义回归通过；最后说明文字改动仅重跑2项及公开35case validate |
| RESUME-CHAOS-06 | `f76bb65e089c` | 1.0.0 | 85 passed集中；最后两个根字段校验变更后12项相关测试通过；实际28case/20 mockHTTP |
| REVIEW-CAL-06 | `e9a0ed61802b` | 1.1.0（保留1.0入口） | 123 passed / 0 skip；双物理根8条公开CLI、每根58项synthetic匹配、业务字节一致 |
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
