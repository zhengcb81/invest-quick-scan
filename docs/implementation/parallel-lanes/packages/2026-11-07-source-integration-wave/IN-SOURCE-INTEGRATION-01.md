# IN-SOURCE-INTEGRATION-01｜把快扫事实接进行业研究技能源仓

**唯一写入 Lab：** `C:\Users\郑曾波\Projects\iqs-in-source-integration-01-lab`
**只读源仓基线：** industry-research `main@98640a9a1f52fc87ba9813676a3cc5ab9bf045c9`
**只读已验收 consumer：** `iqs-in-impl-02-lab@ba54e00f5356831b9bb3ded952c06d43c4c01606`
**接口：** IQS `acb03e3c084f61ca2b49181180195118077d43e3`，facts wire 2.7.0，schema SHA-256 `cd3e03417289a99f5194263603ead6d954fd601b875cd3d5c08a74505ba8cbad`。详见同目录 `inputs.lock.json`。

## 目标

把已经验收的离线 quick-scan consumer 移植到行业研究技能源仓，在行业公司评估和报告生成中提供可选、可追溯的公司事实/关系补充。行业框架、行业评分、证据判断、收入预测和估值保持原样；快扫不能替代研究结论。

## 只允许的改动

- `SKILL.md`：加入可选 quick-scan 使用说明和严格边界。
- `modules/company-evaluation.md`：说明如何为已选主体读取和展示快扫线索。
- `modules/report-generation.md`：加入独立 facts/coverage 小节，不改变既有评分表。
- `tools/quick_scan_client.py`：移植已接受 consumer；通过显式参数调用公开 CLI，不使用绝对本机路径、私有 Python import 或直接读数据库。
- `tests/test_quick_scan_integration.py`、`tests/fixtures/quick_scan/**`：本包所需的定向测试和合成 fixtures。
- `docs/handoff/IN-SOURCE-INTEGRATION-01/**`：交接文件。

先核实冻结源仓树是否已有同名文件；若路径与本卡不同，只可在本 Lab 内对齐到功能等价的原入口，并将实际路径写入报告。不得触碰其它文件或扩大范围；如确需超出 allowlist，交回理由，不顺手重构。

## 行为与边界

- 只查询用户/研究流程已经选择的公司和 subject；不扫全池、不自动加入公司、不刷新、不下载。
- facts 在线性独立的“快扫事实与关系线索”报告章节出现，保留 subject/listing、关系方向、期间、source refs、coverage、snapshot、模型/时间元数据；不进入行业评分或共同比较计算。
- strict、explore、unknown、unverified、partial、stale、完整无命中必须分开表示。缺数据不能写成行业里不存在该公司/关系；探索候选不能写成已证实产业链。
- 同 issuer 多挂牌、不同 `analysis_subject_id/revision` 不得合并。调用失败/不支持时旧行业报告仍可完成。
- 只读消费；不触发 LLM/search、不写 StockWiki、不改名单或历史公司清单、不改 PDF acquisition/配置、不访问私有源仓 API。

## TDD 与验收

1. 先写原公司评估及报告入口的最小失败测试：quick-scan 关闭时旧评分/报告保持原行为；开启时新增独立 facts 章节且评分结果不变。
2. 定向测试覆盖：strict/explore、来源引用、时点/期间、unknown/partial/stale/unsupported、完整空响应、CLI 错误/超时/坏 JSON、多挂牌/多 subject、snapshot/cursor 错误和无重复刷新副作用。
3. 用 fake public CLI 和 2–4 家虚构公司构造行业研究隔离 E2E，从公司评估走到报告生成，验证评分字段/数值不被 facts 改动，报告准确保留来源与缺口。运行新增和受影响测试及仓库现有包校验（先读当前真实帮助/README）。不要求实 owner、真实公司扫描或网页下载。
4. 所有测试 workspace、fake owner root、输出置于本 Lab/TEMP。只清除本包自己创建且位于这些根内的内容。

## 交接含义

交付表示行业研究源仓候选已接入离线 consumer 并通过合成测试。它不表示本地 canonical 源仓已被总控合并、不表示 F05/W11 当前 owner 已互通，也不关闭 G4。按 [handoff-rules.md](handoff-rules.md) 做一次最终独立 agent 审查；修完全部问题、最终 commit 复审 approved 后，交 `docs/handoff/IN-SOURCE-INTEGRATION-01/report.md` 与 `handoff.json`。
