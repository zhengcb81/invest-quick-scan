# QA-04、SW-IDENT 与消费者预研接收审查

观察时间：2026-09-30 22:02 UTC。IQS 总控只读核对外仓交接、提交和公开入口，并在用户已授权且事先报备的 StockQA 两个文件中修复 QA-04 复审发现的热更新缺陷。下列判定仅针对冻结快照，不把 worker 自述的测试或授权当作验证结果。

| 交付 | 当前判定 | 已独立验证 | 尚不能签收的部分 |
|---|---|---|---|
| QA-04 | 功能案例通过；交接/提交仍为 partial | `StockQAbyLLM master@3c685dd` 的公开 CLI 与运行时回归；本轮 RED/修复/GREEN；当前相关批次 246 passed，Ruff 与 diff check 通过 | 55 项共享脏树未提交；`q04_handoff.json` 自报 `partial`、`result_commit=null`，其源码 hash/坏配测试声明已被本轮修复超越，需在安全冻结当前文件快照后刷新 handoff。不能把这份旧 JSON 当作最终签收凭据。 |
| SW-IDENT | W01–W03 部分成果通过；整个包 partial | `StockWiki master@8bc454e`，新增 evidence store 的 SHA 与交接一致；独立复跑 evidence/mapping/snapshot 43 passed；公开 G2b 跨仓正反例及两份 frozen golden 哈希复现 | 新 evidence store 尚未接入 resolver/snapshot/export/扫描链；W02 候选导入、裸 ticker 歧义、名单筛选和 W03 CLI/身份事件仍缺。完整 W01–W03/G2b 不关闭。交接 JSON 虽满足基本 schema，IQS 公开 handoff CLI 拒绝：`changed_path_out_of_scope`，因为新增源码/测试未列入 `authorized_paths`。其授权来源也须由交付方提供可核对记录。 |
| TH-01 / IN-02 只读预研 | 两份 `prestudy_complete` 已接收并按 SHA 归档；T01/T02 实施 `not_started` | 完整 Markdown+JSON、公开 handoff CLI、关键文件哈希、实际接入点/字段映射/缺口及设计但未运行的测试；TH-01 报告的 15 项离线合同测试独立复跑通过 | 报告冻结于较早 StockWiki/IQS 快照；G3/F05/W11、生产 query/golden 与消费者写授权未满足，实施前需增量核对独立仓库与 `local-skills` 的 owner 归属。 |

## QA-04 复审与修复

原交接文件 `C:/Users/郑曾波/Projects/StockQAbyLLM/q04_handoff.json` 通过 IQS `parallel_handoff_cli.py --package-id QA-04` 的格式/自述范围预检，但其中“损坏热 quota group 整体拒绝”测试是同一 `policy_version`：`_refresh_policy_revision` 在读取损坏 group 前早退。独立审查以真正新 revision 重放，旧代码采纳不存在的 group，持久健康路由随后抛 `KeyError`。总控先在 `tests/unit/test_llm_integration.py` 增强反例，RED 为 1 failed（该 `KeyError`）；再在 `src/utils/llm_integration.py` 先构造、校验全部候选 provider/route/quota group/派发元数据，然后一次性更新运行时状态。GREEN 为 1 passed。独立复审确认 P1 半更新已消除；三处未使用变量做无行为变化清理后 Ruff 通过。

当前 SHA-256：`src/utils/llm_integration.py=e44878d0b6ed9390a55d8210920952e9f16c89c1c49e1d7cbe34e516b9f6a21e`；`tests/unit/test_llm_integration.py=913eaba45191cfae73e69577f31680a8ddf8066f2045e64ea6173952bf1a5f75`。其余 QA-04 路径未由总控修改。使用 StockQA PYTHONPATH、IQS 临时 cwd 与 pytest basetemp、禁 cache/base_url/coverage 插件，最终六文件单元/集成批次 **246 passed**；独立 reviewer 另复跑公开 CLI 与策略/PAR-11 共 **52 passed**。测试未触真实 API/网络、未下载公司资料；全部精确 `.tmp-qa04*` 临时根/脚本已在核对 IQS 根路径后清理且不存在。StockQA 仍为 55 项既有共享脏树；没有整树暂存/提交。

## SW-IDENT 交接差距

交接文件 `C:/Users/郑曾波/Projects/StockWiki/.planning/sw-ident_handoff_2026-09-30.json` SHA-256 `baee5595ac95528c14134e4f862299adc717c27e376d434529a1121015f460ac`，自报 `status=partial`。实际 HEAD 是 `8bc454e`，其所述结果提交 `1cabb47` 是祖先；原有 `.claude/` 未跟踪且未处理。`stockwiki/quick_scan_evidence.py` SHA-256 `2b48d1f14e97f05b703dc1d865b1810ed557b66aad979e53879f94ac666e7525` 与交接一致；其独立 SQLite 存储目前只被自身测试调用，所以可验证 DB-09/ID-14 的存储子项，不可外推为生产身份解析或扫描资格。

IQS `parallel_handoff_cli.py --input ... --package-id SW-IDENT` 返回 `invalid/changed_path_out_of_scope`：`changed_paths` 有 `stockwiki/quick_scan_evidence.py`、`tests/test_quick_scan_evidence.py`，`authorized_paths` 却没有它们。交接文字声称另获用户授权，但这不代替可核对授权或机器字段。独立审查仅复跑了 **43** 项聚焦测试与 IQS 公开 G2b 脚本，不能把回执自述的 125 或 680 项当成本轮独立复测。Entity golden SHA `0efc2c04daa7b6345078410a5df5ae0aa5bec9098b1523d7c25f9f60f53e5d2f`、mapping bundle SHA `da3991c0d85ef9a0bce7c9152475b9184942df74c34fab4c5c935fb0e375a96f` 复现，临时 owner/test 根清理。完整 G2b 仍需 verified、多挂牌、AnalysisSubject 与真实有效期/近名解析生产证据。

## TH-01 / IN-02 原件与仓库归属

用户随后给出精确子目录：`C:/Users/郑曾波/Projects/analyze-theme-value-chain/prestudy` 与 `C:/Users/郑曾波/Projects/industry-research/docs/handoff`。两仓分别将原件存为提交 `3c9a49c` 和 `4a80f99`；首次仅按文件名找不到原件的记录已由此更正。两份 JSON 均通过 schema 和 IQS 公开 `parallel_handoff_cli.py`，报告的接入点、字段映射、降级与测试设计均经独立只读复核。TH-01 报告 SHA-256 `e40a079d9d6936181b28c2b5955542fe0696c8e4fde8010ea3420da99099ea87`，JSON `5f930f90d57bbe335fad32bb1821d0327da28f3a8c2e8d06af62903167e96d4b`；IN-02 报告 `023f9a7960c87b5f4085d54f8f76393255165bb844e3fa89841e132ffe04c35e`，JSON `0791a54ecd365cb0a94accc7c4d201866c41e77f61dc1bfa14ab8314b99dbfdf`。中央副本按报告哈希命名、字节不变，索引见 `docs/implementation/parallel-lanes/prestudy/archive-index.json`。

报告基于 `local-skills@ec4db38`、`StockWiki@72531b5`、`IQS@65e96ba`（TH-01 还观察至 IQS `7a53bf5`）；当前 StockWiki/IQS 已推进，原结论是历史快照。独立技能仓库与 `local-skills` 对应 SKILL.md 字节一致，但原施工包把 `local-skills` 设为实施 Git owner；未来开工前须明确唯一写入仓库并做增量预研。两份报告正确认定 StockWiki 没有公开 `capabilities/search/get_profiles/request_refresh` 端点或生产 response golden，把 G3/F05/W11、身份/事实字段和授权缺口列为阻塞，未把虚构 query fixture 当生产正例。IN-02 还指出既有 `company_list.json` 写入与 `companies.json` 读取不一致，已按源码位置核对。预研接受不解除 T01/T02 施工前置。
