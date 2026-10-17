# 2026-10-17｜三条独立研究施工线

**状态：本波次文档已由独立agent发布审查通过（`passed`，`open_findings=[]`，2026-10-17）；卡片可以交给独立harness准备实施。实际开始前，总控仍须提交这批文档并提供每包通过校验的dispatch-lock；每个Lab根目录也须再次检查是否已有内容或writer。** 这三包是新方向，不续做已经完成或有重叠的施工：`SCORE-ANCHOR-02`/`ROUTE-COVER-02`已有评分构念与模块路由覆盖；`MATRIX-CASE-01`及后续多模型实验已覆盖时间、模型、题集版本；`FACT-CONTENT-01`/`CHAIN-*`处理术语和供应链事实；`CLAIM-GUARD-04`、`EVID-GAP-04`、`RETRIEVAL-AUDIT-07`处理主张与来源质量。此前拟议的周期、转型、银行评分模块在读到当前题库后被撤回，不得分发。

| 施工包 | 唯一可写工作根 | 独立目标 | 付费/外部请求 |
|---|---|---|---|
| [TAXONOMY-CROSSWALK-09](TAXONOMY-CROSSWALK-09.md) | `C:/Users/郑曾波/Projects/iqs-taxonomy-crosswalk-lab/` | A/HK/US官方行业分类体系到本项目中性行业树的版本化、多对多映射样机；不分配真实公司 | 不调用模型/搜索；仅使用公开官方分类资料 |
| [LOCALE-ROBUSTNESS-09](LOCALE-ROBUSTNESS-09.md) | `C:/Users/郑曾波/Projects/iqs-locale-robustness-lab/` | 控制同一问题、证据、模型和时点，测中文/英文题目及证据表达是否改动答案质量 | 最多90模型HTTP、0搜索HTTP；具体模型/现金与套餐额度由总控锁限定 |
| [PROMPT-TRUST-09](PROMPT-TRUST-09.md) | `C:/Users/郑曾波/Projects/iqs-prompt-trust-lab/` | 用合成材料实测网页/搜索摘录中的恶意指令是否能诱导改分、换身份、泄露测试哨兵或触发工具 | 最多40模型HTTP、0搜索HTTP；具体模型/现金与套餐额度由总控锁限定 |

三根目录互不相交；三包均不改 IQS、StockQA、StockWiki、company-wiki、local-skills、数据库、名单、安装镜像或其他 Lab。三个 Lab 当前不存在（2026-10-17 编卡检查）；收到卡片后须再次确认路径，若已存在或有 writer 则停止，不清理、不接管。每个包只依赖本卡、[共同施工与交接契约](integration-contract.md)及总控随包提供的`dispatch-locks/<PACKAGE-ID>.json`。共同契约使用[`dispatch-lock.schema.json`](schemas/dispatch-lock.schema.json) 1.1.0；无通过schema及wave级窗口/预算交叉检查的锁不得开始；禁止追活动仓获取输入。

代码/离线测试可以并行。两个真实模型试验若共用quota group，锁的半开执行窗口必须不重叠，并给不同budget owner；wave级锁校验结果随handoff归档。不满足就只做各自离线准备，等待总控调整，不得通过并发去“抢额度”。TAXONOMY最多使用公开官方分类资料；LOCALE计划78模型HTTP并留12次reserve，硬上限90；PROMPT-TRUST计划32模型HTTP并留8次reserve，硬上限40；两个模型包搜索/Fetch均为0。不切换模型、不自动重试不明发送、不查询或记录密钥。每包独立交付与验收，不引用其他包结果作为前置。

卡片的独立发布审查已通过；实施方还必须在完成前另用与实施者不同的真实agent/task对最终实施payload作一次整包审查；所有有效发现均修完并经同一reviewer复核至`passed`且`open_findings=[]`才可交接。LOCALE调用前还须由独立双语reviewer签收全部翻译manifest，以免为错误译文付费调用。身份必须由总控可直接打开的原始agent/task与review artifact证明，作者自填的JSON不能证明独立性。

本文件不是生产功能或全股票池数据已完成的声明。结果只作为总控后续评估的候选；是否接入、是否扩到2000家、是否改变路由/评分/名单都留给总控现有大节点。
