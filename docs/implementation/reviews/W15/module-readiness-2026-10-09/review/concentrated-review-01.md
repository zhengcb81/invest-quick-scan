# W15 集中独立审查：初次候选

结论：存在 1 个可复现的 P1 产品阻断，暂不签收。审查为同一 W15 包的一次集中独审；不增加逐 helper 门。产品、私有候选、PWF、外仓与真实库均未由审查 agent 写入；只增加本目录审查材料及 `runs/w15a/review-owned` 自有反例。没有模型/API/HTTP 调用。

## F1 / P1：容量等待后仍准入已失去 current 绑定的发送

位置：`runs/w15a/qa/src/utils/quick_scan_work_transport.py:655–660` 及 `:763–777`。`begin_quick_scan_send` 只在入口调用 `_OWNER_REFRESH_GUARD`。真正的 `mark_send_intent` 可能因预算容量满而等待最多 30 秒；每次再次准入时没有重核 owner current。只读 planner 与最初的 anchor 检查不能给后续等待结束的发送继续授权。

精确反例：在 owner SQLite 中记录 A、B 两个不可变路由快照，先激活 A。QA 建立绑定 A 的 work 与 lease，真实原预算账本中另一个 reservation 占用相同 route 的唯一容量。第一次准入被真实 `BudgetAdmissionError` 拒绝。等待调度点使用真实 StockWiki `set_current` 将 current A→B，再按真实 QA `record_budget_outcome` 释放占用。随后原 transport 第二次准入成功返回 `QuickScanSendAttempt`，原 attempt 已为 `send_intent`；`OwnerRefreshSession.check` 的实际 anchor 调用仅 1 次。

独立反例原终态：PID 53056，pytest **1 failed in 1.95s**，controller 2.55s，returncode 1，source_unchanged=true。观察值：`permit_returned=true`、`attempt_phases=["send_intent"]`、`capacity_waits=1`、`anchor_checks=1`、实际 current B 与绑定 A 不同，rejection=null。这属于产品发送路径问题，不是旧 fixture 或 controller 失败。

证据与执行 SHA：`capacity-anchor-01.stdout.log`、`capacity-anchor-01.stderr.log`、`capacity-anchor-01.process.json`。transport 的执行 SHA256 为 `d8a7fcdbcbde276ab6353453a780b597b611d4659521007ef9f56204df9605bf`，owner bridge 为 `eb4a37a2c1a156e9273fba5bf4677bae965c5bc2e8b8da15fcea96a236de1dbc`。该 process 文件记录实际执行的 19 个候选产品/公开 schema SHA，而不是用发布 commit 代替候选字节。

反例边界：真实 owner SQLite 和 QA SQLite/费用准入事务；原 `UnitValidator` 替代 IQS producer 校验，typed `_call` 替代 CLI 传输但实际调用 owner current 读取；只替代等待调度点，不替代预算拒绝/释放或 `mark_send_intent`。这是 storage/transport 边界反例，不是真实 owner/公司/金融 golden。HTTP_calls=0，复用现有 guard；外来 SQLite 与 Python 网络禁止；不称为全 OS 隔离。

修复应在每次容量准入尝试前重核 owner guard；若 current 漂移，应拒绝并保留 `prepared`，不产生新的费用 reservation 或 send intent。修复后的重复尝试须用新的自有 basetemp 和新的具名证据，保留本次失败原件。

## 其余集中检查结果

以下项目已结合候选源代码和已有实际终态材料检查；未发现第二个已证实的产品阻断，不等于对未执行的环境或金融正确性作保证。

- IQS validator 调用既有 route/manifest 验证器，要求独立 expected ID；history 不授予新 execution。双 raw SHA、原归档、完整 module locks 与原 routing execution 单独保留。产品没有跨仓 Python import。
- StockWiki schema6 路由快照存储 subject revision/perimeter、issuer identity 与 scope，current 按 subject/scope CAS；执行读取来自已存 current，候选自报 decision 不可代替它。旧 router 2.1/2.2 原字段/缺字段保真测试属于 storage unit 边界，不冒称完整 producer golden。
- 模块新增/退出及聚合规则比较保留旧观察；单题比较语义、定义、rubric、scope、period、provider/model。TTL 取 observed_at 与 information_as_of 两者较早值。segment 对 issuer 构念转换作用层、缺 security/segment ID 定向 defer。
- QA 通过固定 first-party CLI 取得 current、自己生成 work projection，再取 refresh 并重核锚点；静态 JSON contracts 只解析三个本地注册资源。owner config 不携带命令/密钥/外来 plan。
- 原 Observation 复用在 hydration/claim 前分流，引用保留原 ID/payload/hash/qualification/model/time，wrapper 将其排除于新增 answers/C06 封包。reuse 在实际使用时重核 TTL；已 delivered 而 owner Observation 缺失会要求先对账。
- v14 binding 只加在原 work ledger，触发器禁止改/删；create/bind 与 send guard 均处于原 BEGIN IMMEDIATE 事务，检查全部 generations 的 pending/leased/uncertain/result_ready。send guard 与原费用 reserve、send intent 同事务；旧 legacy worker 也不会绕过已绑定的未决 work。send intent 或部分 ACK 继续原恢复上下文，不能重绑新 route。
- schema6/备份最高支持版本同为6；原 Observation schema2 与 AnalysisSubject schema1 不改。迁移持 BEGIN 后读版本，备份/独立恢复已有实测；审查未迁移真实库。

## 已读验收记录的准确范围

`handoff-final-01`：原 PID 75248，18 passed / 103.01s，终态0。`executor-final-affected-02`：原 PID 46824，246 passed / 83.26s，终态0。`storage-owner-bridge-02`：原 PID 67540，73 passed / 73.96s，终态0。`storage-wire-contract-01`：原 PID 14356，4 passed / 83.84s，终态0。这些来自不同批次及候选 SHA，不相加，不替代 F1；QA 后续类型注释变化由各 process 的 SHA 区分。

`static-qa-02`：Black、isort、mypy 终态0，Bandit 终态1（9 Low，0 Medium/High；包含新 CLI subprocess 边界及现有/新增 schema 登记 assert）。`full-sw-support-fixed`：第一次完成整个离线 suite，原 PID 5808，终态1；1063 passed、64 failed、18 skipped、21 errors / 225.22s。失败涉及缺失副本支持/配置/UI/legacy fixture、guard 禁 Python 网络、junction 权限、全套 controller 未给新 integration 测试注入 IQS 根，以及旧 schema fixture。这里不将其泛化为64个 W15 产品漏洞，也不把 coverage80% diagnostic 或原 collection失败写成全套通过。该未绿检查的归因与必要接续由主控处理。

真实元数据 clone 的已锁输入为 `real-owner-metadata-input-01.json`，其中 native backup 和26份结构化元数据属于真实 owner 输入；本审查没有读取财报/密钥，也没有以合成答案冒充真实 query/身份/金融 golden。公开 wire 明确 `c06_envelope_validated=false`。即使 F1 修复并软件签收，也不关闭原 query/C06 实际 serializer golden、G3/L03、F05、B01 准确性或 TH-IN。
