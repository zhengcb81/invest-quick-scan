# COMPANY-AGENT-01：公司研究agent策略执行器与可重放实验台

状态：可由用户交独立harness实施；未派发、未创建新仓。工程交付不等于新策略优胜或金融验收。只在一个新Lab施工，避免另拆几个共享运行时的小包。

独占目录：`C:/Users/郑曾波/Projects/iqs-company-agent-lab`。本包之外所有仓库、其他Lab、共享PWF、真实名单/数据库/旧实验只读。新根若已存在或出现其他writer，先确认归属，不覆盖。用户把本卡交给harness后才开工；本卡不是后台派发命令。

## 开工上下文（必须一起读）

1. [设计](../../../experiments/company-agent-design-2026-10-14.md)与[预注册](../../../experiments/company-agent-registration-2026-10-14.md)。研究比较fixed3、free_agent、evidence_agent；思考开启、准确性优先、所有失败保留。
2. [接口](integration-contract.md)、[目录范围](manifest.json)、[冻结输入锁](inputs.lock.json)、[固定目标](COMPANY-AGENT-01.targets.json)、[交接模板](COMPANY-AGENT-01.handoff.template.json)。机器配置随输入冻结；不能追latest悄悄换题或参数。
3. 本项目AGENTS.md：结构查询先CodeGraph；新Lab无索引时按规则询问，文件读取/离线实施可先继续。使用自己的PWF记录进度，不改IQS总控PWF。

现有三包BLIND-INPUT-04、FIN-PROVENANCE-03、CHAIN-VERIFY-04仅已准备，不能假定已经开工或完成。它们分别负责真实盲评输入桥、金融原件闭合、新关系核证。你不实现这些内容、不创建新gold、不改其目录；自己的实现不等待其新代码，可以用明确合成fixture覆盖策略行为。

主线原试点有30题/13HTTP/26搜索/0正式评分/ACK0，实际work18与source19不同。不要连接、迁移或恢复那个数据库。真实owner/StockQA接线与后续付费实验由总控完成。本包不读环境密钥、不发真实模型/搜索请求，不下载公司文档；这是独立施工边界，不否认用户给总控的实验预算授权。

## 交付目标与复用

实现可插拔的候选策略核心，让同一CompanyTask经三种策略产生每题原格式答案、完整槽位结果及公共执行轨迹。你只造调度/证据依赖/有限修复，不造LLM SDK客户端、搜索HTTP客户端、预算数据库、重试队列、StockWiki身份库或第二个盲评系统。

冻结StockQA源码只供接口定位，**不是独立可运行的完整依赖包**。不得复制十个文件拼一个脱离owner的live runner。运行时通过本卡RuntimePort注入；本Lab只提供SyntheticReplayPort。总控接入真实StockQA后才有live运行资格，无法接线须列明确接口gap而不是假实现成功。

正式答案复用冻结 `schemas/answer-content.schema.json` 全部字段及语义，保留未来兼容边界；研究封套用独立 `iqs.company-agent-research/1.0.0`，不得冒成Observation或生产评分。未知未来版本拒绝，历史题库/schema不原地重写。

## 实施步骤（整包一次集中审查）

1. 建自己的仓/PWF与离线环境。按锁验证并复制自己需要的字节到fixtures；生成inputs-used，记录来源HEAD、rawSHA、路径与用途。读取已登记研究目标，创建严格schema及合成输入；先写主链和关键故障失败用例。
2. 实现公共策略接口/证据状态/逐题slot ledger/确定性assembler。所有策略共用身份/截止/上限/工具约束。fixed3按目标原序三题分组，free_agent由模型tool action决定，evidence_agent按问题所需事实关联分组；不更改原题含义。
3. 实现只读证据工具、带前置hash的定点补丁、有限自审、稳定前缀/证据epoch与delta、不可伪造的usage未知态。支持串并行调度但由RuntimePort统一准入；本Lab不自己对网络重试。
4. 实现冻结事件重放、崩溃检查点恢复、无进展退出、限额与未知结果转交端口。思考协议只使用opaque session_handle，永不落入研究记录；重启标新segment。恢复不能重复调用已完成题，证据变动要显式判哪些题失效。
5. 输出原题不丢的研究封套、请求/搜索/时间/cache计量和盲评候选输入引用。不要实现BLIND-INPUT的格式桥；给出与它对接所需原answer_content、原件安全hash及slot状态即可。
6. 跑下表整包测试和公开CLI，在全新临时目录导出；清理自己的fixture运行残留并核源只读。报告实际通过/失败/未运行，以及live、金融参考与接线仍未验证。正常本地提交后按交接协议回包，不擅自推到新远端。

## 必须覆盖的实质反例

|组|测试与预期|
|---|---|
|答案完整|12题缺1、重复1、陌生ID、重复JSON key、非法score/额外字段/混合markdown；不静默最后值覆盖。slot分母仍12，invalid与unknown不同|
|证据正确|中微公司/中微半导体混淆、跨年或截止后发布、亿元/十亿元、GAAP/调整后、计划/实绩；拒绝证据错误绑定，不能靠自动换标签通过|
|依赖共享|一个来源支持多个题，只搜一次但保持逐题口径；同URL新内容/相反片段不能按URL盲去重；错误fact失效只重开依赖题|
|自审补丁|补丁expected hash错、额外修改正确题、证据未变化却加分；记录草稿/修订/拒绝原因，自审不自授正确|
|自由策略|模型合法search/read_evidence/submit_answers/finish，循环、未知tool、参数错、工具返回指令注入；有界终止、不执行任意代码或读取gold|
|失败与恢复|限额cooldown、403权益拒绝、429频率、超时和outcome_unknown分开；不盲重发。crash在发送前/收据后/提交答案前，精确恢复由runtime receipt判定|
|共享状态|两个公司同名题ID互不串档；同公司两个attempt旧补丁拒绝；改变模型进入新segment而保留旧费用/失败|
|缓存计量|相同前缀不同尾部、首部随机变动、context压缩、跨模型/端点；cached缺失=null，0为真实0，命中不能大于输入；应用warm零HTTP不等于KV命中|
|费用时间|全计划/修复/失败/工具/自审均计；思考属于已报输出时不可重复加价；同物理ref重放不能双计；并发wall不同于request耗时和；套餐价/现金未知不记0|
|轻资产安全|短片段留限，禁止财报下载/正文归档；最终结果/日志/异常/检查点无reasoning正文与key；恶意路径、符号链接/junction、已存在输出拒绝，不清别人文件|
|端到端|固定合成12题×2公司在A/B/C全链运行，缺证/修复/拒绝/恢复分支都有；结果原schema验证、全槽位、明确synthetic，非金融准确率|
|便携复现|移到不同绝对路径重新validate/replay/export；输入不变结果比较域一致，时间/宿主位置另列；输入hash漂移拒绝|

单元测试验证上表局部机制，集成测试验证三策略共用端口和状态不串，E2E从CLI输入到导出/恢复/清理。不能用一组只检查schema的tests充当全链。每个大机制先失败后实现即可，不要求每函数新增一次review或回执。

## CLI交付约定

```powershell
python -B -X utf8 -m iqs_company_agent_lab validate --input fixtures/synthetic/task.json --inputs-lock fixtures/inputs.lock.json --input-root fixtures/locked
python -B -X utf8 -m iqs_company_agent_lab replay --task fixtures/synthetic/task.json --events fixtures/synthetic/events.jsonl --strategy fixed3 --output runs/replay-new
python -B -X utf8 -m iqs_company_agent_lab resume --checkpoint runs/replay-new/checkpoint.json --events fixtures/synthetic/resume-events.jsonl --output runs/resume-new
python -B -X utf8 -m iqs_company_agent_lab report --input runs/replay-new --output runs/report-new
python -B -X utf8 -m pytest -q
```

同样覆盖另两策略。以上路径是需实现的交付接口，当前没有假装已经存在的可执行产品。validate/report的exit0仅表示工件合法，可以合法包含partial；replay/resume只有全部槽位completed才exit0。只要仍有invalid/rejected/outcome_unknown/not_attempted（含预算、时间、无进展耗尽），replay/resume返回4并导出完整slot ledger；2=输入/协议/锁不合法，3=输出冲突/路径不安全。completed中的insufficient_evidence仍不是正确性证明。partial可被report读取，不因此补造有效答案；产品tests不得把所有exit4当成功回答。

## 交接格式与验收

最终目录 `docs/handoff/COMPANY-AGENT-01/`，必须包含：

- `handoff.json`：用模板填真实初始/结果commit、变更范围、实际测试、未完成项。结果commit不可填future或模板值；随后记录handoff自身提交，避免自引用hash循环。
- `report.md`：架构、A/B/C差异、与StockQA现成接口对应及尚缺能力、兼容、问题/修复、限制，明确无live/no gold。
- `inputs-used.json`、`artifacts.json`：实际输入rawSHA及输出相对路径/bytes/rawSHA；不含自身hash，path禁绝对/..；hash域写清。
- `commands.json`和测试原始日志：精确命令、cwd、start/end UTC、exit code、输出hash；不能手写“全部通过”代替执行证据。
- `integration-notes.md`：RuntimePort公共对象/事件、原answer_content输出、源码候选文件清单与baseSHA；总控接线的明确步骤，不改外仓。
- 合成events、可移动的最小重放包与`cleanup.json`：临时目录、进程闭包、清理前后及原文件不变检查。没有下载也写明0。

公开交接形状校验（复用IQS现有工具；只验证结构，不能代替产品验收）：

```powershell
python -B -X utf8 C:/Users/郑曾波/Projects/invest-quick-scan/scripts/parallel_handoff_cli.py --catalog C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-14-agent/manifest.json --package-id COMPANY-AGENT-01 --input docs/handoff/COMPANY-AGENT-01/handoff.json
```

总控接收时一次整包审查与必要复现；问题直接修受影响范围或按工作量再安排。候选通过只代表可进入真实S0–S2，不代表金融评分可靠、cache已省钱或生产已上线。明确失败或结论“不优于固定小包”也是合格实验结果，不能为交付漂亮而隐藏它。
