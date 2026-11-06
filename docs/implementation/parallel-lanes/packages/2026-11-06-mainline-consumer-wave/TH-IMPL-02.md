# TH-IMPL-02｜主题研究消费快扫事实

**lane：** `theme`
**唯一 Lab：** `C:\Users\郑曾波\Projects\iqs-th-impl-02-lab`
**只读 source：** `C:\Users\郑曾波\Projects\analyze-theme-value-chain`，`master@3c9a49c7ce86f3e60eb9a6c8e6c835164cb8a903`
**合同：** IQS `master@acb03e3c084f61ca2b49181180195118077d43e3`，facts wire 2.7.0；详见 [inputs.lock.json](inputs.lock.json)。
**任务映射：** T01；本卡取代旧 `TH-IMPL-01` 的实施时旧基线/开工判断，不重做已验收 TH-01 预研。

`tasks.json` 里的 T01 `depends_on: ["F05", "W11"]` 是真实产品/owner 接入验收依赖；它不阻止本包以冻结 facts 2.7 契约在隔离 Lab 开始离线实现和合成测试。F05/W11 尚未验收时，交付状态只能是离线实现，不得宣称真实 owner 集成完成。

## 目标和边界

在主题公司候选/公司资料流程中增加一个可选的 IQS facts 输入，输出可追溯的产业链关系线索，帮助定位产品/设备/材料/客户/下游应用候选。主分析仍由 analyze-theme-value-chain 完成：主题适配、因果机制、收入弹性、预测、估值和最终研究结论不得由快扫结果替代。

只在本 Lab 改：`SKILL.md`、新增 `references/quick-scan-integration.md`、新增本仓风格的 `scripts/quick_scan_client.py`、必要的 `tests/test_quick_scan_contract.py` 与合成 fixtures、`docs/handoff/TH-IMPL-02/`。不改 IQS/StockWiki/StockQA、Industry、company-wiki、`local-skills` 或 `.agents/.codex` 安装镜像。

本包是只读消费端，不实现或触发 `request_refresh`、LLM搜索、下载、入库、观察/名单更新，也不扫描全池或自动加公司。只处理本次用户/上游已选择的公司或候选 subject；同一发行人多挂牌、不同 `analysis_subject_id` 必须保留边界。

## 调用合同

- facts schema 固定为 `schemas/quick_scan/query-facts-v2.7.schema.json`，SHA-256 `cd3e03417289a99f5194263603ead6d954fd601b875cd3d5c08a74505ba8cbad`。请求为 `query_facts` 或需要机器候选集时的 `export_facts`；capability 先读 1.1/1.2，未知 wire 显式 unsupported。
- owner CLI 目标形态来自冻结 F05 候选：工作目录 `<owner-root>` 下运行 `python -B -X utf8 -m stockwiki.quick_scan_query_v2_cli --root <owner-root> --iqs-code-root <iqs-root> --request <request.json>`。实现成传入路径/可替换 subprocess adapter；不硬编码用户路径、不导入 StockWiki 私有模块、不直接读 SQLite。Owner query 可能写入 snapshot/capture，测试必须将 root 指向自有临时 owner workspace；本包不调用真实 owner root。
- 当前 canonical StockWiki owner runtime/golden 仍在总控 F05 验收中。因此本包可以用锁定 schema、synthetic response 和 fake public CLI 完成消费端代码，但必须如实写明未做 current owner 实互操作；不得伪造 real golden。
- strict facts 是已按 wire 满足条件的关系线索；explore 是待核候选。`unknown`、`unverified`、`partial` 和“完整覆盖但无命中”是不同结果。只呈现 owner fact/source reference、scope、方向、期间、商业化/证据状态、information cutoff、观察时间、snapshot/coverage；不得隐藏缺口或重命名成正式投资结论。

## TDD 与测试案例

1. 对主题公司池/资料表先写用户可见断言：启用 quick-scan 时出现候选关系及出处/缺口；停用、unsupported 或超时仍可走旧主题研究路径。
2. 单元/contract 覆盖：query/export 版本、相同 issuer 多挂牌、subject scope、客户/供应商/设备使用方方向、严格/探索区分、期间截止、来源引用、完整空与 partial 空、unknown/stale/错误 JSON/CLI 不存在、重复/重试不触发额外调用。事实文本当作不可信数据，不执行命令或自动访问 URL。
3. 隔离端到端：用小型虚构主题、2–4 个虚构公司、临时 fake owner CLI 和合成事实，跑技能第5/6步，核验候选输出字段、关系方向、出处与缺口；同一输入应稳定复现。无财报、网页下载、网络或费用。
4. 跑本包新增/影响的测试和 source `scripts/validate_package.py`（先读真实 `--help`/当前文档确定用法；不可猜参数或降低门槛）。不跑其它技能/全池测试。

## 完成与交接

交付仅表示主题技能能消费锁定 facts contract 并保留原研究流程。加入一位非作者独立 reviewer，对最终 commit 的真实 diff、各状态展示、错误回退、source references、测试和范围做一次集中审查；作者修复所有发现并让 reviewer 复核最终 commit。最终报告在 `docs/handoff/TH-IMPL-02/report.md`，机器结果在 `handoff.json`（handoff schema 1.0.0）。不安装镜像、不推源仓 remote。真实 StockWiki owner runtime 正反互操作由总控在 F05 交付后执行，不挡本包离线实现，也不能由本包代签。
