# IN-02｜行业研究第 6 步读取快扫公司画像

**可单独交给 Industry harness 的施工指令，当前仅可只读预研。** Owner 子树 `C:/Users/郑曾波/Projects/local-skills/industry-research/`；任务 T02，验收 CONS-03、CONS-04、QUERY-04、SC-11、CONS-07。G3、F05、W11 和 StockWiki 公开 query endpoint/golden 为硬前置；用户当前未授权本子树写入。`local-skills` Git 根也包含 Theme，两个 harness 必须在独立工作树/分支写各自子树，最终由总控串行整合。

## 现有流程与目标

行业技能 `SKILL.md` 第 6 步“评估行业公司”，`modules/company-evaluation.md` 目前从研报、行业 wiki、`companies/` 目录找公司，并有本地公司文档/年报读取路径。T02 只给这一步增加**可选的快扫候选/画像来源**，不删除或篡改既有深度行业研究路径；快扫自身不依赖下载文件，读取 StockWiki 的轻量结构化数据。不能为快扫去批量下载财报，不能把本地目录是否存在当成某上市公司是否在股票池的权威判据，也不能自选 2000 家名单。

先读本技能 `SKILL.md`、`modules/company-evaluation.md`、其现有测试/脚本入口，IQS [查询契约](../../contracts/exchange-and-query.md)、[事实字段/时效契约](../../contracts/freshness-and-jobs.md)、[Industry lane](../lane-industry.md) 和 `tasks.json` T02。真正接线还需 StockWiki owner 的公开 capabilities/search/get_profiles 文档、实际 response golden、版本/覆盖/水位语义。IQS 本地协议定义不代表生产端点已经上线。消费者不读 StockWiki 私有 SQLite，不修改其表，不复制 StockQA 客户端。

## 输入与标准输出

输入包括行业/细分行业、市场与 as-of、稳定 field IDs、必要的 Score/Fact 模块 release。先能力协商，再按行业/关系条件查询候选，批量取得 profile 与历史引用。公司主键使用 `analysis_subject_id + revision`，保留法律 issuer 与多个 listing 的区分；同 issuer 多挂牌在公司比较表仅一行，证券/市场指标仍带 listing 口径。每行明确标记数据来源为 quick scan、信息截止日/观察时间、模型/provider、题库/字段版本、证据级别、coverage/freshness 和未知状态。未知分数/null 不是 0；无供应商/客户条目且覆盖未完成，不得解释为“没有供应商/客户”。

输出是行业公司发现表、需补证的细分链条/设备/材料/客户线索，以及快扫评分时间轴入口。快扫不替代行业框架问题评分、正式证据采集、营收预测或估值。旧版能力不支持关系或事实版本时显式 `unsupported/partial`，保留原有行业研究流程，不静默把缺口当成筛选失败。刷新必须先预览并经用户确认；读取报告时绝不自动派发 LLM。

## TDD 工作包（依赖满足后）

1. 记录技能仓 HEAD/status 和现有第 6 步真实公开入口，冻结 IQS/StockWiki 版本与 golden。给用户报备拟写本子树的精确路径和目的，取得写授权。预期仅 `SKILL.md`、`modules/company-evaluation.md`、本技能专属测试/适配器；路径须预检，绝不改 Theme、StockWiki、IQS 或 StockQA。
2. 先写 RED：正常行业多公司、同 issuer 多市场去重、短词误命中、行业归类/关系未证实、`empty`+完整覆盖、partial/not_covered、身份歧义、过期/未知评分、字段 release 不兼容、分页快照一致性、分析范围变更、来源/模型元数据保留。用公开边界 mock 做单元测试，再用 owner golden 做协议集成反例；不自制所谓真实生产返回。
3. 最小适配第 6 步：按 stable ID 而非中文显示名或私有 SQL 取字段；把结果标成“快扫初筛”，保留第 7 步报告既有证据等级和定量逻辑。对 `request_refresh` 只展示 preview/缺口；没有明确授权不得触发派发。
4. 离线 E2E 从行业技能公开入口用虚构行业/少量虚构公司运行，确认原研究流程仍能使用、快扫可用时引入候选、不可用时明确降级；所有临时缓存/输出在唯一根下，结束 assert 清理。网络/API/PDF 下载默认关闭。跑本技能现有定向测试和输出校验；G4/G6 做一次阶段审查。

## 当前可交付的只读准备与完成标准

前置未齐时仅交付第 6 步入口图、字段/口径映射、公开端点缺口、测试矩阵及拟写路径，状态为 `blocked/partial`；**不提交实现，不声称 T02 验收**。正式完成需五个 case 的 owner 实测、真实契约 fixture/版本、unknown 与 coverage 正确呈现、可重跑离线 E2E 和清理记录。

按 [handoff schema](../handoff.schema.json) 返回 `package_id=IN-02`、base/result commit、子树内变更路径/hash、消费的版本/golden hash、测试命令与结果、未触发的网络/费用、review/open items。总控核对后串行整合到共享 `local-skills` Git 根。
