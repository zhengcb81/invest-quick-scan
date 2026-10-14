# 三包共同规则：只写新根，冻结消费，总控统一接线

这批是施工卡准备，尚未启动harness。依赖实际提交与rawSHA以[inputs.lock.json](inputs.lock.json)为准；当前IQS47209ce、BLIND0b0e0666、CHAIN-SOURCE5c5dd140。金融原Lab与BLIND冻结FIN副本不是同一物理树，不把9项缺失错误直接归咎金融原库。所有金融评分null、owner not_mapped、production not_run保持。

## 开工与权限

只写[manifest.json](manifest.json)中本包新根及授权相对路径。目录不存在才新建git，分支codex/<包名小写>；已存在需证明是本harness同任务接续且无另writer，否则停止写并报备，禁止reset/clean/删目录/强制覆盖。所有现有仓、其他新根、共享PWF/输入快照/真实DB/名单只读。目录独占不能替代进程独占；开工记录UTC、完整Git HEAD、dirty与进程归属。新根没有CodeGraph时按AGENTS询问建立索引，可先继续设计和只读处理。

自己建task_plan.md/progress.md/findings.md。不得写共享PWF或在现有Lab实施补丁；本包完成正常本地提交，不自动推远端。总控收到后统一审查/CAS/接线，工人不发布正式schema/current，不SQL恢复任务，不生成owner批准或金融gold。

## 输入与版本

先记录本批inputs.lock自身rawSHA；逐条验证本包input_repositories的bytes/rawSHA，复制到自己的fixtures/<repository>/，原相对路径保留。复制嵌套冻结依赖；Git忽略不代表不是运行输入，6个FINmanifest/questions在锁内必须带齐。fixtures原件不可修改，测试篡改只在本包独占TEMP复制件。不得读浮动latest替代锁，源仓后续变动在总控接线时解决；不同输入必须另声明迁移。

实际调用冻结已有reader/validator/canonical/盲评函数，提供运行spy或端到端证明；函数名和相同算法不是复用证明。可把需演进的产品复制到自己src/schema作为候选并提交精确base/new SHA补丁提案，原fixtures仍不动；禁止monkeypatch跳过原检查、篡改全局sys.path导向浮动仓。不要另造LLM客户端、评分器、身份库、队列、费用账本或重做旧三包。

封闭schema按[接口](integration-contract.md)版本扩展；原1.0/1.1读取语义和样例保留，未来版本拒绝。原题ID、题义、权重、标尺、事实数值及null不重写。原handoff与历史manifest不重签；新的便携manifest只描述新输出。

## 网络与测试

三个包收费API/收费搜索/密钥读取/生产数据库及名单写为0。前两包完全离线；CHAIN仅允许人工现有浏览/搜索工具读官方HTML，不能用key或自动抓取器、下载PDF/财报/网页全文。所有研究与离线测试分开。不得对未读来源、截图缺字、403、仅PDF或future日期补造事实。

TDD先关键真实反例RED，再实现，再一个稳定包级unit/integration/公开CLI E2E；修后只复跑受影响范围，不增加逐helper审查。期望独立于实际，不改输入消除失败分母。合成software通过不代表真实准确率、金融gold或真人审核。

父子进程都使用keyless env白名单，TEMP/TMP/pytest basetemp与必要cache/HOME在本包runs/test-唯一值；python -B -X utf8，禁pytest cache。离线父子禁网，SQLite只允许本包临时根，禁止外部写。Windows NUL、Python executable只精确兼容；原生硬链接/junction沙箱不支持时说明后用同护栏原生隔离执行，不删安全检查。中文空格路径、随机cwd、确定性二次导出、拒覆盖、路径穿越、symlink/junction、duplicate JSON key、NaN/Infinity/1e400、体积/数量/累计读预算和future版本纳入一组边界测试；无需每个小函数设门。

收尾先核实际PID/子进程闭包，再核resolved绝对删除目标在本轮自有临时根且无外部链接。只删本次创建文件，保留实际失败/通过日志、锁、候选、SHA与核源记录；不清共享TEMP、其他writer或源仓。Windows长路径使用原生扩展路径仍核安全根。cleanup列残留，CIM或查询权限拒绝不能当0进程。

## 交接：六份固定文件，真实commit与日志

docs/handoff/<包ID>/：handoff.json、report.md、artifact-manifest.json、tests.json、cleanup.json、inputs-used.json。使用本包handoff.template.json；模板仅形状示意，交付须填自己真实base/result commit、dirty、实际interfaces/checks/open_items。先提交内容，result_commit指该内容commit；随后封存handoff另commit避免自引用。artifact-manifest列相对路径/bytes/rawSHA，排除自身、.git、缓存、密钥、私人答案/思考和临时副本。

verification.checks严格name/command/scope/result/passed/failed/skipped，result=passed|failed|not_run；PID、argv、UTC起止、真实exit/timeout、耗时、stdout/stderr/XML路径/bytes/rawSHA在tests.json。自审review.status=not_run并注self_review；只有真正独立审查才填相应状态。partial可交付，但固定分母完整，未完成项不得隐藏。

形状检查用原公开工具（把ID/路径换成自己的）：

```powershell
C:/Miniconda/python.exe -B -X utf8 C:/Users/郑曾波/Projects/invest-quick-scan/scripts/parallel_handoff_cli.py --catalog C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-14/manifest.json --package-id BLIND-INPUT-04 --input C:/Users/郑曾波/Projects/iqs-blind-input-lab/docs/handoff/BLIND-INPUT-04/handoff.json
```

exit0只证明声明形状，不是软件验收或证据门关闭。本批任何交付不关闭Financial/G3/F05/生产UI/一键/全池。
