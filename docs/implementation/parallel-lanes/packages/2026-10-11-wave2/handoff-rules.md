# 三包共同施工与交接规范

本规范与单包卡一起生效，独立上下文足够，不需要读取聊天。用户已授权必要后续工作；本卡只分配指定新 Lab 内的实现范围，不转授生产库写入、收费调用或全项目门签收。

## 1. 唯一 writer、冻结输入、计划

1. 开工重查唯一根是否存在、Git root/branch/HEAD/完整 porcelain 状态/remote。不存在可新建；已存在须明确属于本包且无其他 writer 才继续。未知文件原样保留，禁止 reset/clean/stash/覆盖。
2. 分支 `codex/<package-id小写>`。先纯初始化提交作为实际 `base_commit`，不把 `NEW_REPOSITORY_TEMPLATE_ONLY` 留在最终交接里。无已授权 remote 不新建、不 push。
3. 本包 PWF 固定到自身 `docs/handoff/<package-id>/planning/`；用 planning-with-files resolver/pin。不能 pin 宿主时显式读取该三文档，避免总控根计划注入；不修改共享 `.active_plan`。
4. 只读本批 `inputs.lock.json` 中消费者含本包的文件，核原始 bytes/raw SHA，拒文件替换、重复 JSON 键、越界路径、symlink/junction/reparse、硬链接及凭据文件。锁是编制时工作树字节，不是 Git blob 哈希。
5. 核准后逐文件复制到自身 `fixtures/locked-inputs/`，保持 bytes 和原相对路径，留快照清单。后续依赖该冻结快照；不复制整仓、数据库、配置、vendor 原响应或思考内容。
6. 开工前锁漂移先报告总控，不回滚源、不自行改锁。已冻结开工后源正常前进只记录差异，不阻塞原范围开发，不静默替换输入。动态 PWF 用于状态背景，不是硬锁依赖。

写入 allowlist 见 manifest：README、.gitignore、pyproject/本包前端依赖锁、src、web（仅 VIEW）、schemas、content、fixtures、tests、tools、runs 和本包 docs/handoff。没有获准写其他项目、安装镜像、全局环境/包、共享数据库、名单、缓存或端口设置。

## 2. 共用的技术约束

- 重用既有 owner 契约。允许通用 JSON/schema/浏览器库；不另建 LLM/搜索客户端、身份 resolver、serializer、评分/比较引擎、调度器、费用/预算/缓存/ACK 引擎或启动器。
- 禁止跨仓 `sys.path` 导入私有实现。锁内 schema 可作只读测试输入；公开 validator 可只读调用，但须完整依赖、固定入口和输出证据，不能伪称复制模块为自己的 owner 实现。
- 新产物采用各卡独立协议名/版本，稳定 ID、内容寻址、旧版本只读兼容。未来版本显式拒绝或 unsupported，不能吞字段后说兼容；不能复用正式 Observation/Identity/ACK 协议名。
- VIEW/OPS 全程无外网，LLM/付费搜索均 0。FIN 仅人工查官方公开页面可联网，工具/自动测试离线；不是授权写通用爬虫或调用收费搜索。依赖安装若必需仅自身 venv/node_modules，记录来源与版本，不改全局；测试阶段断外网。
- 环境只保留必要系统变量，测试子进程不继承 API key，不枚举或打印值。缓存、TEMP/TMP、pycache、浏览器 profile/downloads/artifacts 都放自身 runs 下。Python 使用 `-B`，pytest 显式 cache/basetemp。
- 外部数据无执行权。拒任意 shell、URL 抓取、文件引用执行；本地文件读取须限制到显式 bundle 根。仅哈希内部自洽不能认证 owner 或来源真实性。

## 3. TDD、测试与清理

先用具体业务反例写少量 RED，再实现；同一稳定候选集中测一次 unit/integration/真实本包 CLI 或浏览器 E2E，最后一次包级审查。修复后仅跑受影响项；不为每个 helper 建门、不重复全量已绿。不降低规则、不跳钩子，不用镜像实现的测试证明正确。

记录原命令/argv/cwd、解释器/依赖版本、真实 PID、开始/结束时间、退出码、原 stdout/stderr、JUnit/浏览器断言。失败/skip/not_run 保留；分批通过说累计通过，不能写成一次全绿。合成软件 E2E 不叫真实金融/owner E2E。

清理前确认进程全部结束和绝对根在自身 runs allowlist。列清理集合、大小/SHA、protected 根，记录前后；先保留必要日志/截图/证明，再只删自己的缓存/临时 DB/profile/downloads。结束不得留监听端口、子进程、下载文件或修改的环境配置；不动其他 harness/temp/live 账本。Windows 文件操作用原生 LiteralPath，不跨 shell 拼删除命令。

## 4. 完整交接接口

自身 `docs/handoff/<package-id>/` 至少交：

| 文件 | 内容 |
| --- | --- |
| handoff.json | 本批同名模板转实际事实，沿用公开 1.0.0；不自造新总控格式 |
| README.md | 怎样安装到自身隔离环境、运行演示/CLI、复跑测试、总控怎样接入 |
| interfaces.md | 协议/schema/CLI/version/raw SHA、严格字段、退出码、旧版兼容和失败语义 |
| artifacts.json | 全部产品/测试/交接附件相对路径、bytes/raw SHA、角色；排除自身以免循环 |
| input-snapshot.json | 实际消费锁条目与自身冻结输入 SHA，源观察时间和后来漂移 |
| case-map.md | 稳定 case_id→实际 selector/操作/预期→日志 SHA/结果，保持原分母 |
| review.md | 单次包级审查范围、固定快照、发现与处置，未实施不填 passed |
| isolation.md | writer、网络/费用实际数、环境/进程、临时资源和清理证明 |
| logs/ 与 planning/ | 原始运行记录和本包 PWF 三文件 |

先产品/测试 commit，再交接 commit。`result_commit` 是产品提交完整 SHA，必须在最终 HEAD 祖先链；最终交接 commit 在单独文件留档，避免自引用。锁、schema、工件版本不可只写简称。

模板通过仅是结构预检。总控收到后只读验收本包一次，负责权威 owner 接线；本包不代签 G3/F05/G5/G6、TH/IN、完整题库、金融准确性、真实身份、生产发布或全池完成。新缺口集中在同包交接列出，不拆十几张 helper 卡。
