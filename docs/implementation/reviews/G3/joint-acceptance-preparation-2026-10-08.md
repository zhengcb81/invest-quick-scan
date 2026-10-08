# QA／StockWiki 联合验收准备

状态：`prepared_not_executed/finite_inputs_received`（2026-10-08 Phase107后）。这是总控的单次联合验收说明，不是新施工包、生产执行器或已通过测试。QA原四链、SW SR02-4B、Lab LR-02B的有限软件整改已分别签收；总控仍只读各源仓、原writer归属不变。最新观察见[source-state](joint-source-state-2026-10-08-after-repairs.json)，旧[source-state](joint-source-state-2026-10-08.json)保留为历史。

## 输入与开工条件

当前接收的QA软件结果`b6eaa082e6e1df1306fa144bd623aa6de68213a1`／交接`a39d7eafceacfa1114f5e5cb094eadb32030652c`，见[QA有限签收](../QA-C06-02/second-remediation-2026-10-08/acceptance.md)；StockWiki软件结果`cc587a8cf76f2c50a0cdfb4693d3767dfa5944fa`／交接`d253fea5f4f6e4242d2b91eaf8d89d3dac8b45ff`，见[SW有限签收](../SW-REPAIR-02/sr02-4b-2026-10-08/acceptance.md)。两个输入已具备有限软件联合执行条件，仍需新编号隔离根和固定快照，不能复用已清根或测试动态树。QA公共handoff因历史TEMP声明exit2的保留按报告单列，不伪改原件为valid，也不扩大为已通过的软件新小门。

Lab的来源绑定单项已[独立签收](../EVID-LAB-01/lr02b-2026-10-08/acceptance.md)，不人为阻塞QA/SW联合链；其准确性/校准与历史清理保留仍按原边界核实。本次联合仍未执行，不以准备说明或三局部GREEN关闭全局门。旧QA`7e71b2c`／SW`9f9e0af`与原changes_requested证据保留，不能将这些旧结果当新整改成果。

既有输入与反例直接复用：

- [QA 四组＋交接整改](../QA-C06-02/remediation-2026-10-08.md)、[原九例](../QA-C06-02/acceptance_cases.py)、[原 133 文件字节清单](../../intake/QA-C06-02/2026-10-08/verification/source-snapshot-extended.json)。
- [StockWiki 五组整改](../SW-REPAIR-02/remediation-2026-10-08.md)、[原反例](../SW-REPAIR-02/acceptance_cases.py)、[原导出清单](../../intake/SW-REPAIR-02/2026-10-08/verification/source-snapshot.json)。
- [跨仓接口](../../parallel-lanes/packages/2026-10-07-wave2/interfaces.md)、[原跨仓反例](cross_owner_cases.py)、[共同隔离规范](../../parallel-lanes/packages/2026-10-07-wave2/handoff-rules.md)。旧源码和 RED 原件只读保留，不将旧拒绝输入改为预期拒绝后声称修复成功。

新 result commit 必须可读取；测试从 commit 导出 allowlist，不复制动态工作树。遇到冻结文件的 Git LF／交付 CRLF 差异，必须由 owner 的双 hash 和还原说明唯一确定执行字节；不自动换行、重签 manifest 或使用当前工作树填补缺失原件。新增接口／参数先从冻结副本 help 和 owner 文档核实。

## 一次执行的顺序

| 顺序 | 实际入口与输入 | 必须留下的证据 |
|---|---|---|
| 0 | IQS 公共 handoff CLI、两仓 result commit 与授权清单 | 实际 diff／SHA／EOL 口径；格式 valid 与功能验收分开；所有输入固定在本次 manifest |
| 1 | StockQA `main_with_llm.py` 真实子进程，从冻结 manifest／identity／authority 与 HTTP 边界替身生成回答、checkpoint、完整封包 | 每次真实子进程 argv／退出码；替身次数；完整 body、原 attempt／provider／model／时点及各层 hash；不可默认补字段 |
| 2 | StockWiki `python -m stockwiki.cli --root <isolated-owner-root> observation-import --package <package> --release <frozen-release>` | 原包字节、匹配的 release、真实导入回执与 ACK；只在 owner 临时库落地；不能从观察自身反推 release 让其合法 |
| 3 | StockQA owner 已公开的 ACK 接收 API／入口，在其独立子进程调用 | 完整 ACK 与 work／head 绑定、落定前后公开状态；没有公开 ACK CLI 时如实使用并注明 owner API，不发明 `--ack` 参数 |
| 4 | 另进程 warm／seal、ACK 丢失与重复恢复、旧 head 与未知发送 | 额外模型／搜索 HTTP 为 0；原答案／attempt／费用不变；每个重放用配对首次与再次回执，不拼接不同根的证据 |
| 5 | 两 owner 公开恢复入口、StockWiki query／UI | watermark、真实查询变体及不可比状态；能力不支持记 unsupported/not_run，不用 UI 页面可打开代替整链就绪 |

这里的 `<...>` 是运行时由独占根分配的绝对路径，不能复制到生产环境执行。步骤 2 的参数已在原 owner CLI 及 W05 处理器核实；仍需对新快照复核。StockQA 原交付只核实 `--seal-deliveries`，没有据此确认公开 ACK CLI。各仓使用各自解释器／cwd／PYTHONPATH，不在同一进程混装两个仓的模块。

现有 QA fixture 的 31 个合成答案只用于软件链路。可复用其 HTTP 替身与冻结题义，不编造公司事实、verified 身份或 owner golden。真实身份／事实正例必须来自 StockWiki 的真实 owner serializer、来源资格与生成命令；缺失时本次真实数据部分为 missing/not_run。合成端到端通过不能满足该缺口。

## 同一批正反例

下面是本次验收分组，不新增中央 task/case 或逐组审查门。按现有 C06／Q10／W05／W12／查询与 UI 任务归属登记结果。

| 组 | 情景 | 必须断言 |
|---|---|---|
| J01 | 合成完整 scored／insufficient_evidence／N/A 与低谷关注输入 | 真实导入与 ACK 落定；原状态、null、低分、watch 信息、长 body 不被过滤或截断；不因质检生成新分数 |
| J02 | 错 definition／semantic／template／scope，重签 envelope | 在生产者读 key／预约／HTTP 前拒绝；消费者独立拒错 release；不能用正常包自述生成权威题义 |
| J03 | 两独立 run／scan／attempt、同次重放与明确运行映射 | 独立执行 ID 不碰撞；恢复沿原映射，不能借新 run 标签；同次封包字节稳定 |
| J04 | authority／body 嵌套重复键与非有限 JSON | 真实入口明确拒绝或 durable block；不退为 legacy compact／默认 5 分；无额外调用 |
| J05 | 包 hash 篡改、缺实体、错 security／subject／revision | 包级错误不写观察；项级拒绝 ACK 与公开计数一致；没有资格的输入不升级 verified |
| J06 | StockWiki 已提交、ACK 回程丢失、同包重放／同 ACK 重放 | 公开对账后恢复同一观察与 ACK；StockQA 最终只落定一次；不重复 LLM、搜索或费用 |
| J07 | 错 namespace／store／package／item／payload／observation ACK | 匹配失败不能 delivered；原 head／事件／费用不变；验证所有键而不是只比较 status |
| J08 | 合法旧 compact→完整 head，旧 ACK；非法改 claim／metric／metadata／started_at | 合法加法升级保留历史；旧 ACK 不落定新 head；非法替代原子拒绝、revision/head 不变；已 delivered 只读 |
| J09 | send_uncertain／结果未知、重启及上游离线 | 先原 attempt 对账；证据不足保留未知与预留，不重发／fallback／生成新 attempt；阻断原因可查 |
| J10 | 配套备份恢复与故障中断 | 两 owner 恢复水位明确，未导入结果／已导入未 ACK 不丢不重付；不得复制生产库或用伪造的双 owner 恢复成功标记 |
| J11 | 相同公司题目不同 segment／period／basis／model／rubric，>=8 查询与详情 | 原变体都可追溯；无明确选择时 ambiguous/null，不把 2/9 混成 9 入选；query 与 UI 一致 |
| J12 | query capabilities／coverage，严格／探索关系和空 partial | 实际能力、版本、snapshot 与 coverage 保留；facts=false 不声称已完成 F05；无能力不输出“无该业务”；不自动触发搜索／刷新批准 |

J01 的合成样例不叫真实投资正例。J05 的真实身份输入仍须真实 owner 工件。J10、J12 依赖尚未交付的入口时，不造 stub 绕过被测功能，登记精确缺口。既有 v5→v6 旧包／ACK 迁移和故障 rollback 已有 GREEN；只有新改动触及其路径才补定向回归，不重复全部历史 suite。

## 隔离、结果与关闭边界

全部运行落在新 IQS 独占临时根，两个 owner 的副本、库、TEMP／TMP、日志及子进程分别隔离。移除真实 key 与 live 可用性；只有模型 HTTP 边界替身。query／UI 如需本地服务，只开放本次端口并记录 loopback 数，其他网络／下载／付费为 0。保留原始命令、退出码、stderr 和超时片段；timeout 要 kill/wait 自己的子进程，不能吞日志后宣称通过。

清理按共同规范：已知进程终态与严格扫描、精确 manifest／SHA、无重解析／单硬链核实后 dry-run→Apply，仅删本次自有路径；共享 pytest TEMP、其他 writer 根、旧 Phase92、`nul` 与 `opencode.json` 不动。扫进程失败不当作 0；未能清理明确记录残余。

只安排一批受影响单元／协议／真实跨仓进程 E2E及一次集中独立审查；原 owner 已跑无变化的整仓 suite 接收原日志，不重复。结果逐组为 passed/failed/unsupported/missing/not_run，controller 故障另列，不计产品 RED。源仓新 commit 与 handoff 未齐时只保持本说明准备态。

联合离线链通过仍不自动关闭 G3：其正式依赖为 L03＋W11；W11 已 verified，L03及真实可靠性证据尚未齐。F05、真实 owner query schema/capabilities/golden／生成命令、TH/IN 精确写授权另行核实。三个整改的局部 GREEN、公开 handoff 格式 valid 或本说明完成均不允许启动 TH-IMPL-01／IN-IMPL-01 或全池扫描。
