# 本批共同施工与交接规范

这是完整接手规则；不要求读取聊天。施工卡限制的是本次交付范围，既有用户对后续必要工作的授权持续有效。把卡交给某 harness 是认领包的信号；harness先确认本目录没有另一个活动 writer，再写入。若有人仍在写同目录，交总控协调，不自抢文件、重置或删除其成果。

## 目录、计划与输入

每包只写施工卡给出的唯一源仓及白名单；其他仓全部只读。IQS 根 PWF、`runs/c15a`、StockQA、StockWiki、company-wiki、名单、生产 DB、安装镜像、用户秘密配置均不是写范围。Lab是资料/验收工具，不是第二研究状态数据库或第二扫描执行器。

实际开工先读取本仓适用 AGENTS.md，用 CodeGraph 查结构，记录 Git root/HEAD/branch/完整 `status --porcelain=v1 -uall`。没有索引按 AGENTS 询问，已有索引不重复初始化。禁止为了 clean 状态使用 reset/clean/stash、改全局忽略或删除别人的未知文件。

每包独占计划目录 `docs/handoff/<package-id>/planning/`。使用 planning-with-files resolver 明确选中本目录：在启动 harness 的宿主环境 pin `PWF_PLAN_ROOT` 为这个绝对目录，目录内只放本包三份 PWF 文件，不建 competing root plan、不改共享 `.active_plan`。环境变量只在子 shell 设置不能绑定已运行宿主；宿主无法 pin 时在卡的独立仓/工作区按本包显式读取计划，禁止由hook静默接收其他包的根计划。无法消除计划选择歧义就先纠正 pin。

消费[inputs.lock.json](inputs.lock.json)指定的文件，检查路径、bytes、SHA和相关 commit；本批工作树 raw SHA 与 Git blob/EOL口径分开。只读导出时须是明确允许的非秘密原件，保留 raw SHA。不复制整个生产 data/raw/config/TEMP，不扫描 key 值。无关新变化仅记录；固定输入变更则停止该输入消费，交总控差异，不用新文件悄悄替换旧基线。

`freeze_bundle.py`是总控已执行的一次性编制工具，不是harness开工入口；不要重跑、重新生成inputs.lock或修改本批IQS施工卡。源文件字节变化时请求总控给新版锁；仅HEAD前进而固定输入字节/接口均相同时记录新HEAD，继续消费原已锁内容，不要求还原整个仓库。

## 实现和测试

先固定有鉴别力的失败例，再最小实现；开发只跑受影响单元/集成。整包交付一次集中相关回归和一次集中审查，发现问题在同一审查里复验。禁止给每个 helper 新增审查门、重跑已验收 UI/备份/Phase111，或为覆盖率写逐行照抄实现的测试。

每次 test/replay 用自有唯一短临时根；TEMP/TMP/TMPDIR、pytest basetemp、缓存、日志和子进程都进入它。子进程同样隔离；默认清除 key 可用性，不读取/打印 key；网络和费用边界覆盖父、子进程。真实 CLI E2E调用本包实际代码，不能用测试内重写一套实现通过自身断言。

原结构化 Observation、question/field ID、未知分数、模型/时间、历史数据保持原样。局部资料的 `candidate`、来源核实和金标准资格是不同维度；包级软件 GREEN 不能变成公司准确性、owner identity/golden 或全池放行。

FACT 全程零网络/模型/费用。EVID 的人工/harness公开网页取证与本包离线校验分开记账；仅公开只读网页工具，不调 API key、Brave/Tavily/ZAI/MiMo等收费接口，不调用新模型、不写网站、不下载公司文档。新 CLI/所有自动测试保持离线；不松动旧 Lab guards。网页读取次数不能填写 network_calls=false。需要付费实验的矩阵/预算/输入由总控再组织，不把旧预算变成 worker 的新实验默认许可。

## 异常、清理和提交

保留首次 RED、每次实质失败和终版 GREEN 的原 stdout/stderr/退出码；超时与明确供应商拒绝不同，观察工具 yield 不等于进程退出。只对自己创建、精确验证 PID/启动时点/父子链的子进程做终止。任何未知发送不自动重发，本包本来就没有模型发送权。

清理前确认自身进程都终态，核绝对根在白名单内、无symlink/junction/reparse或外来硬链、清理集合与自有清单/SHA一致。保留必要证据后，原子地或分步骤删自己生成的内容；失败也清理。不按目录名、mtime、pytest编号清共享TEMP；核实不了的残留写明，不能 `cleaned=true`。参考短事实/例子是最终交付，临时页面缓存/运行副本不是。

只 `git add` 自己的精确路径，不 `git add -A`。已有外来 staged 文件先停本次提交并报总控，不混入。正常hooks，不跳过、不force；先提交产品/测试，再交接中引用真实完整 commit，避免自包含hash循环。仅用已有获准远端，不为Lab新建remote；新FACT仓只正常本地commit。`result_commit`不能null而自称complete。

## 标准交接

各源仓 `docs/handoff/<package-id>/` 必交：

| 文件 | 内容 |
|---|---|
| `handoff.json` | 按本卡模板填真实分支/完整commit、输入/输出状态、改动路径、检查、审查和未解项；格式沿用1.0.0 |
| `summary.md` | 最终行为、读写界限、全部可复制命令、已做/未做、升级与回退 |
| `artifacts.json` | 相对路径/bytes/raw SHA/用途/来源类别，禁止自身hash循环 |
| `interfaces.md` | 本卡声明的 schema版本/内容hash、实际CLI/退出码、生成命令、消费与产出契约；附件独立链接不扩handoff字段 |
| `case-map.md` | 本卡case ID→真实selector→原日志/hash→passed/failed/skip/not_run；精确分母，不拼重叠测试批 |
| `logs/` | 原RED/失败/终版GREEN/stdout/stderr/exit，禁止key/独立思考/整页或完整API原文 |
| `isolation.md` | 自有临时根/进程、网络与收费实际数、受保护外仓SHA前后、清理集合/结果 |
| `planning/` | 只属于本包的task_plan/findings/progress，下一步与未完成门清楚 |

EVID再交reference pack、逐项来源核验、精度/口径/争议、旧答比对与采集账本；FACT再交content pack、61题映射与语义case、术语歧义和候选变更影响。各卡详细规定格式。

模板的 `lane_id=iqs` 表示本批为IQS研究/内容支撑，不授予IQS仓写权；`scope.task_ids`与manifest严格一致。authorized_paths写实际本卡路径，changed_paths列实际相对路径，不包含旧Lab成果/CodeGraph设施。`external_writes=false`指没有越出本包源仓；索引初始化另记基础设施，不冒充产品实施。

`complete`只表示本卡限定交付完成；没有人类金标准可以完整交付诚实的候选参考集，但不能填写human_approved。G3、F05、F01/F06正式发布、L03、200家公司、TH/IN和一键开启不由worker关闭。未执行必须not_run；未解决源证据缺口保留，不能靠改模板/裁掉失败样本过门。
