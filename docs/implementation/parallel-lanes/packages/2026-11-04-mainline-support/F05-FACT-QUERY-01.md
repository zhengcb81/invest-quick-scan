# F05-FACT-QUERY-01｜真实事实与关系查询接口

**唯一工作目录：** `C:\Users\郑曾波\Projects\iqs-stockwiki-f05-query-lab`

**目标仓库只读源：** `C:\Users\郑曾波\Projects\StockWiki`

**冻结基线：** `d8d3303cb4b91fb6bfc8db6202ea3919276f833e`（StockWiki `master`）

**工作分支：** `codex/f05-real-fact-query-01`

**包索引：** [本批 README](README.md)

## 目标

在 StockWiki 原有 C06 public query/capabilities 与 owner serializers 上，交付一个版本明确、可由 IQS 复用的真实事实和关系只读查询面。事实应能按实体/挂牌、细分分部、方向、商业化状态、时间范围和证据状态查找；查询结果须保留原始事实边界和来源引用。

当前基线已有 `quick_scan_capabilities.py`、`quick_scan_query_contract.py`、C06 query 实现和相关测试，但 SW-REPAIR-02 的能力样例明确报告 `facts_available=false`、`fact_relations_available=false`，且该样例为合成旧协议。不能把旧 W09 search/get_profiles/coverage 能力冒充 F05。

## 隔离基线与写入范围

1. 从本地 StockWiki 源创建**独立本地克隆**（不使用 shared worktree），检出上面固定 commit，创建本卡分支并移除 clone 中的 `origin`。例如：
   ```powershell
   git clone --no-local --no-checkout "C:\Users\郑曾波\Projects\StockWiki" "C:\Users\郑曾波\Projects\iqs-stockwiki-f05-query-lab"
   git -C "C:\Users\郑曾波\Projects\iqs-stockwiki-f05-query-lab" checkout --detach d8d3303cb4b91fb6bfc8db6202ea3919276f833e
   git -C "C:\Users\郑曾波\Projects\iqs-stockwiki-f05-query-lab" switch -c codex/f05-real-fact-query-01
   git -C "C:\Users\郑曾波\Projects\iqs-stockwiki-f05-query-lab" remote remove origin
   ```
   不触碰源仓工作树、索引、`.claude/` 或未跟踪文件。不得以源仓当前 HEAD/工作树替代固定提交。
2. 源仓当前可见未跟踪运行数据不是可直接读取的输入：不得直接打开 SQL/文件、复制、修改或清理 `data/companies/688012.SH/research_source_links.sqlite`、`data/dashboard_onboarding/`、`data/dashboard_research_binding/`、`runs/c16b/` 或其他 untracked 路径。若仓库已有**文档明确为只读**的 owner query 命令，且能把输出/临时文件限定到本 Lab，可通过该公开命令取最少量真实 golden；不得直接查库或更改源仓设置。
3. 允许变更仅限 clone 中：
   - `stockwiki/quick_scan_*` 下实现 C06 query/capabilities/owner serialization 所需的直接文件；
   - 对应的 `tests/test_c06_*`、`tests/test_quick_scan_query*`；
   - 必要的新版本化 query schema/config；
   - `docs/handoff/F05-FACT-QUERY-01/`。
4. 不新增第二套事实数据库或旁路 service；优先读取 StockWiki 现有 owner stores/serializers。若缺少持久化的事实来源，报告实际缺口，不临时下载或抄录公司资料填库。

## 行为与兼容要求

- 在现有版本化 query/capabilities envelope 上增量扩展，显式声明新能力和协议版本；旧消费者与旧历史响应仍能按原协议读取。未知协议/能力不得静默解释成“没有事实”。
- 支持至少两种清楚区别的查询：
  - `strict`：只返回满足约定的事实/关系，并完整给出事实期间、分部/主体范围、关系方向、商业化状态和证据状态；缺少必需范围或证据时不把候选当事实。
  - `explore`：可返回待核实候选，但必须标记 `candidate/unknown/unverified` 等真实状态和缺失字段；不得升级为 strict 结论。
- 支持实体身份与市场/挂牌筛选、指定或默认信息截止日、时间/期间、分部、关系类型及 from/to 方向。不得把“设备使用方”改写成“设备供应方”，把合作改写成量产供货，把客户公司直接等同于其下游行业，或把未披露改写为不存在。
- 支持可选的质量/困境反转条件交集；默认查询不得因公司近期处于经营低谷而将其剔除。关系命中要能解释主题匹配路径与覆盖限制。
- 输出应通过公开 schema 校验，分页有稳定排序及快照/游标绑定；能力声明须与真实可执行路径一致。所有事实都要有稳定引用（owner fact/observation ID、来源引用或等价引用）及其时间/状态，不能只给无出处的自然语言摘要。
- 提供机器可复用的候选导出，沿用公开查询结果和同一快照，不另写一套筛选逻辑。导出至少记录协议/导出版本、原查询条件与哈希、信息截止日、owner 快照水位/引用、strict 或 explore 模式、候选实体与挂牌身份、命中路径、关系方向/期间/商业化与证据状态、来源引用、覆盖/未知说明；按稳定规则排序并能重建/校验哈希。不得把完整源文件或网页正文放入导出。
- query 只读，不在查询过程中调用 LLM、联网搜索、抓取或下载文件，也不产生公司文档副本。

## 必须覆盖的测试

1. **单元：** envelope/schema 与版本；实体和分部范围；期间边界/截止日；方向；strict/explore 结果区分；未知与不适用；重复/冲突事实；证据缺失；稳定分页与错误游标；候选导出排序、元数据完整性、快照/条件变更时哈希绑定失效；相同查询条件和快照下，导出候选集合逐页等于公开 query 的完整结果集合。
2. **集成：** 走原 owner serializer 和实际 query service；能力声明与可执行查询一致；一条真实方向关系能被 strict 查询返回；同一实体的反向关系、错误期间、未商业化、未核实候选被 strict 排除而 explore 按状态呈现；旧协议读仍通过。
   - 覆盖任务目录 `FACT-02`、`FACT-03`、`FACT-04`、`FACT-05`、`RULE-04`、`QUERY-10`；必须有 AI 液冷主题和非 AI 主题的正反例。用契约驱动通用查询，不允许按公司名/小行业写特判。
3. **真实 owner golden：** 用新增或更新的可重复命令，从一个 StockWiki 正式支持的只读 owner store/公开只读入口生成至少一个真实实体的 capabilities、strict、explore golden，并记录查询时点、输入版本、真实事实/关系计数和各文件 SHA-256。不得把 synthetic fixture、旧 W09 golden 或手写 JSON 标为真实 owner golden。只保留查询所需的短结构化值和来源引用，不保留源文件/网页正文。
4. 若固定快照中没有可安全调用的只读真实 owner 数据入口，先完成代码与离线测试，将交付标为 `partial`，明确缺的是哪个公开入口/真实样例；不得复制未跟踪生产数据库来制造 golden，也不得将 F05 报成已验收。

## 验证与交接

遵守 StockWiki `AGENTS.md`：每轮只跑受影响的测试；交付前运行 `python -B scripts/checks.py --static-only` 与该改动对应的日常检查。若本次达到其 major checkpoint 条件，完整 `--full` 只跑一次。handoff 说明每个命令的真实通过/失败/跳过数，不能累计重复子测试。

提交只在此本地克隆。交回 `handoff.json`（IQS schema 1.0.0、`lane_id=stockwiki`、`package_id=F05-FACT-QUERY-01`）、最终 commit、路径清单、schema/接口版本、golden 生成命令和哈希、测试命令/结果、独立审查结果及 open items。真实 owner golden 缺失时用 `status=partial`；总控仍需独立验证它与 IQS 公开消费端的互操作后才能关闭 F05。
