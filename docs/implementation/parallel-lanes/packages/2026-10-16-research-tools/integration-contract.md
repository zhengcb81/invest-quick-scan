# 共同接口与交接规范

本文件和各卡组成完整任务授权边界。工人可读输入快照和卡片，只能写本卡指定的新 Lab。不得修改共同文档、冻结输入、总控 PWF 或任何其他仓库；有接口建议写自己根 `docs/interface-proposals.md`。主线输入改变时仍按本次锁实施，不追 latest；总控另立版本接入。

## 一、输入及版本

`inputs.lock.json` 的 `files` 为输入唯一字节清单。`path` 是快照根下的 POSIX 相对路径，`sha256` 为原文件字节哈希，`bytes` 为字节数；不使用语义 JSON hash 替代 raw hash。拒绝缺失、篡改、路径越界及重复路径。只对明确 manifest 输入加载，不扫描任意本机路径；资源加载不得联网。

输入域：

所有对象级函数的hash只能显式标为canonical-object hash；CLI/读文件边界才记录原文件raw SHA/bytes，二者分域，不从dict冒称恢复原始字节。适用于全部三包。

- `iqs/`：原 IQS scripts/schemas/questions，用于原有标准答案校验与指标字典。冻结时研究驱动已具有显式 1.1 bounded3 候选，不表示 1.1 真实试验已完成。
- `company/`：已交付 Company Lab src/schemas，版本 0.2.0，commit `4cb4e3d1b9bcc4e662c73135339de9b51a991916`。
- `evaluation/`：已签收 EVAL src/schemas/resources，版本 0.2.0，commit `01956bdec2790525188451aefad0f2f6546765c0`；资源保持原目录相对结构。某些旧端口需要未包含的历史 fixtures 时应报告，只复用已有所需纯接口，不能声称快照是完整测试仓。
- `trial/`：已结束 T0 的 questions/evidence/schema/metrics、六份 result/events、测量汇总。题目是实际 routed12，包含 `OPERATING_01`；不是旧 `IQS_11` 改名。公开证据十个 facts/六个 sources；不带私有评分 rubric。result 中 answers 是 **list**。
- `rules/`：固定质量判定规则与原 S1R 请求前登记。
- `reference/`：仅 JUDGE 的离线评估器可用的十个独立主标量参考；不能给生成 LLM、CODEC 输入前缀或公开评审包附入未允许的私有信息。父级参考 qualification=false 不被改变。
- `pricing/s0_measurement.py`：已使用的历史价格/窗口估算实现，供 CACHE 核单位和舍入；不当作今天价格或官方假期日历。DeepSeek 官方价格出处为 `https://api-docs.deepseek.com/quick_start/pricing/`，总控最后核查日 2026-10-16；T0 的 flash 历史 USD/百万 token：非缓存输入0.15、缓存输入0.003、输出含思考0.60（非高峰），高峰各为两倍。T0 所有请求均在当日约05:31–05:44 UTC，不跨06:00。官方未明确跨窗口结算规则，未知保留，不从脚本推断官方账单政策。新实验需总控重新核价，本包只复算历史。
- `pricing/historical-rate-card.json`：与上述已核查口径配套的冻结结构化元数据，专用于2026-10-16历史重放；不授权扩展到其他日期/假期。与脚本冲突必须报错，不得默选一方。本文件的源URL/核查日可供 CACHE构造其公开rate_card输入，不需要上网补出处。

路径由显式 `--inputs`/参数传入，不能硬编码作者机器；先隔离复制或从固定只读根导入，记录所有实际模块的来源，拒绝活动源/快照混导。不得 `pip install -e` 到共享 Python、修改环境变量注册表或其他仓 `.git`。使用项目局部依赖/临时 PYTHONPATH；若缺库，仅报告最小依赖与安装命令，不自动联网安装。

原标准答案继续由 `standard_answers.validate_content(answer, question, cutoff, answer_schema=..., metric_registry=...)` 验证，保持原题、锚点、规范单位、日期、status/score 语义。默认根必须指向冻结 IQS；不能为让测试通过重写题库/放松 validator。结构验证不是金融正确性认证。

实验载体显式 `iqs.isolated-company-research/1.0.0` 或 `1.1.0`，`integration_scope=isolated_research`、`production_owner_verified=false`。不能伪装为 ResearchRun1.1/owner_runtime 绕过旧 EVAL 适配器。新工具各用自己的新 protocol，原 schema/fixtures/版本保持；未知 major/minor 版本明确拒绝，不能先删未知字段再当旧版接受。

## 二、共同技术约束

- UTF-8 严格 JSON，拒绝重复键、NaN/Infinity、超大输入、非法编码；schema 关闭未知字段，界限可配置且留文档。不得执行输入提供的 shell、SQL、Python 或任意 URL。
- CLI 用 `python -m <各包名>`，`--help` 可用；成功 stdout 为机器可读 JSON，诊断到 stderr，错误非零。不得把未知/未运行填成 false/0/通过。新输出目录独占创建；遇到已存在目录拒绝，不覆盖、不自动恢复发送。
- 根目录/引用路径防 `..`、绝对外跳、符号链接或 Windows junction 逃逸；测试只用自己临时根。原始输入不可改写，导出转换逐条保留 input raw SHA、显式 protocol 与派生依据。
- 生成模型的隐藏思考不能写磁盘或评审包。只保留已经公开、经过原漏检规则的答案内容；不能将 `reasoning_content` 当答案或以正则猜出可用 JSON。
- package 自己维护语义版本、schemas、公开函数签名、JSON 范例及 `docs/integration.md`。适配/转换只用白名单，不创造答案、分数、期间、币种、引用支持或 production 权限。

## 三、统一交接

唯一交接目录：各自根 `docs/handoff/<PACKAGE-ID>/`，含 `report.md`、`handoff.json`、`tests.json`、`cleanup.json`、`artifacts.json`。用对应 `handoff-*.template.json` 填写，不把模板的 prepared 当 delivered。

`report.md` 必须说明：做了什么/没做什么、原接口复用处、运行命令、测试真结果与 skip 原因、已知限制、可供总控调用的最小示例、版本兼容矩阵、测试环境和清理结果。只以可复现产物声明完成，不以测试数量替代机制。

`tests.json` 至少有 command（argv 数组）、cwd、started_at/completed_at UTC、exit_code、passed/failed/skipped 数、stdout/stderr 原件引用及 raw SHA。RED 反例与最终整包结果各留一份即可；不要求每 helper 单独审查。

`cleanup.json` 列出自己的临时根绝对路径、运行前存在性、自己创建的文件/进程/端口、删除数和字节、结束后剩余、未清理理由；所有递归删除先验证 resolved 路径在自己的测试根。测试失败也 finally 清理自己的临时资源，保留诊断；不删除用户原文件或历史试验。禁网/禁止外根写的执行验证优先于只在文档里声称隔离。

`artifacts.json` 每项 `{path, bytes, sha256, role}`，路径相对自己根，只列实际需要接入的源码/schema/fixtures/报告/原始测试日志；不把 `.git`、缓存、凭据、临时 HTML、隐藏思考算交付。**artifacts 不给自身或 handoff 做递归 hash**。handoff 引用 artifacts 的 SHA，描述源码 payload commit；随后独立 commit 交接元数据，记录真实最终 HEAD。不要为让 handoff 里的 commit 等于包含它自身的 commit 做无穷重写。

handoff 包含明确 `production_ready=false`、`financial_qualification_granted=false`、付费模型/搜索调用数 0；`unrun` 单列，不把实际金融盲评或主线集成虚报通过。请提交自己的代码及交接，不自动推送或配置远端。若已有 owner 远端和额外明确授权，遵从该边界并报告。总控验收才有权更新 IQS 状态。

## 四、集成归属

CODEC 的产物是可选答案传输格式；JUDGE 的产物是隔离运行评测工具；CACHE 的产物是只读计量分析。各包不 import 其他新包，因此现在即可同时开工。总控负责 pin 三份交付、接入现有 driver、构造真正盲评实例并组织人/agent 判定、统一真实预算及跨仓 E2E。三包合格不会自动关闭 G3/F05/生产 owner/UI/一键/全池门。
