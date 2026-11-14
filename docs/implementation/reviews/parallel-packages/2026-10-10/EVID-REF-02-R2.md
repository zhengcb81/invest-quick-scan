# EVID-REF-02 R2：接续同一次包级验收

这是可独立交付的整改卡。尚未自动派发，也未由总控修改源仓。开工前确认 EVID 没有另一个 writer；FACT 不属于本卡。

## 工作目录、基线与边界

- 唯一写入仓：`C:/Users/郑曾波/Projects/iqs-evidence-lab`。
- 接收基线：`codex/evid-ref-02-r1@70498e40918ea28476b8d0185a0294be7bbb6e0e`；产品 `44aa20402125b23de151e2c7c0f4abff7082a7cb`。
- 新分支推荐 `codex/evid-ref-02-r2`。先读实际 Git 状态；若有另一 writer 或产品字节变化，报告真实新基线，不覆盖别人的改动。
- 阅读同目录 `EVID-REF-02-R1-acceptance.md`、原 `EVID-REF-02-R1.md`、施工包 `docs/implementation/parallel-lanes/packages/2026-10-10/EVID-REF-02.md` 与 handoff-rules/inputs.lock（IQS 仓只读）。
- 写范围：`src/iqs_evidence_lab/reference/`、对应1.1候选 schema/fixture、`tests/reference/`、固定入口 `tools/reference_entry.py` 和新增 `docs/handoff/EVID-REF-02/remediation-02/`。保留旧1.0 schema/原始 pack/报告和 R1 交接字节。如确需范围外修改，先向主控报备具体文件，不代改 IQS、StockQA、StockWiki、FACT 或共享配置。
- 无收费 API、联网采集、公司文档下载、重写历史答案/请求/旧金标准、人类审批或生产分数。本包参考结果仍不是人类 gold。

## 一组工作，九类根因

按验收报告 ER2-01～09 一起整改，可按依赖顺序实现，但不追加九个验收门。

1. **先保证正常输入可在隔离副本校验。** 重定位必须有明确配置/契约，核原源仓符号、相对 path、role、大小/SHA及实际副本字节，拒绝伪造源根、错误路径、错字节和换锁。路径变更不能当内容授权，更不能跳过原 `_verify_against_batch_lock`。不要将真正的原锁写成隔离路径，也不要用源仓运行214项掩盖不可复现。正控必须是正常 pack 的公共 CLI 成功；此前主控派生锁只作为合成反例参照，不是正式新机制。
2. **归一化状态和完整请求。** unknown/insufficient 与 value/score 矛盾应拒绝或降为不准确，输出/聚合必须一致；正常无值弃答保留。请求 ID 集合来源要独立于回答，缺 F02 仍在六题分母；确实单题请求不可硬扩为48槽位。删除 question_ids 或篡改请求指纹不能缩母。
3. **把一致性与准确性完全分开。** 对语义未验证的文字/引用只给机械一致性，或 not_verifiable。年份、单位、数字词共现及“没有发现错误”都不能证明支持 claim。旧1.0可读，只保留其一致性；新 accuracy 字段不可复制旧 verdict，即使附 notice 也不够。
4. **绑定题义、资格和评分端点来源。** 资本问题使用冻结 question_ref/稳定ID与题义，不使用可编辑 definition 决定 guard；ROIC/WACC 仍缺时不授予评分准确性。端点来源逐项闭合、绑定本记录/证据/对应锚点，不能仅非空。source_checked passed 需要可追溯检查记录，空 actor/时间/ref、缺记录或通用引用不能升资格；不新增虚构 human_approved。
5. **保护真实 staging 祖先。** 在本包调用共享 publisher 前，检查 `.temp-roots` 全部祖先和对象类型，拒绝 junction/symlink 等，保证在任何 staging mkdir/open 之前失败。优先在本包 entry 收紧，不扩大旧共享 cli 写范围。用真实 Windows junction 指向本卡自有目录做反例，保留普通目录成功和重复输出拒绝控制，删除链接自身而不遍历目标。
6. **补同一次内容口径。** SRC metadata/短事实SHA只能证明引用闭合，不证明金融语义；需要可追溯、与 record/source/hash/时间口径绑定的检查依据，缺则准确性未证实。IQS_05 的4..9若无法具体解释两端锚点和反证就保留区间候选或 null/缺证，不以收入、capex或区间内成员关系独立证明护城河评分准确。

## TDD与集中验收

新增鉴别力反例应先看见目标缺陷，不接受被 schema/hash/路径的无关错误挡住。每类至少一个正常控制；复用同一批运行记录，不要求每例单独进程或审查。

整包完成后只需一次全套回归、一组公开 CLI validate/evaluate/summarize 正反例、同一次包级独审。实报 JUnit/退出码/时间/覆盖范围；有失败、skip或未测项写清，不覆盖 RED。尤其检查 unknown_total 与正确数、完整请求数、旧摘要的结构化 accuracy、端点真实来源、真实 junction 的写入前拒绝。

源仓只用于实现和提交，验收在独占副本执行；删凭据环境变量、封 socket、禁止收费；临时根记录 ownership、过程前后原输入SHA和 Git、实际存活 PID、严格清理清单。保留源仓/共享 TEMP/CodeGraph，不使用工作区全局递归清扫。

## 交接格式

在 `docs/handoff/EVID-REF-02/remediation-02/` 留 `handoff.json`、`summary.md`、`artifacts.json`、`interfaces.md`、`case-map.md`、`isolation.md` 和原始 stdout/stderr/JUnit/退出码。handoff 使用原1.0交接 schema，package_id 仍 EVID-REF-02，授权引用此卡；写准确 product/result commit、实际最终 HEAD、脏树口径、实际路径allowlist、schema版本/hash、兼容性范围、未关闭门。

artifacts 核真实大小/原始字节SHA，输出只含轻量结构化事实/判断与短证据，不保存网页/财报正文。如果报告随 Git 的 EOL 会变化，明确 raw Git blob 与工作树 hash 的区别，不把目录hash当文件hash。`human_signoff=false`；不得关闭 G3/F05/B01/L03/全池或宣称模型金融准确率。

请提交产品和交接成果，保留原始失败记录；不需要向 IQS origin 推送私有原始产物，也不写总控 PWF。主控收到交接后在新独占根接续同一次包级验收，不重做旧包或小节点审查。
