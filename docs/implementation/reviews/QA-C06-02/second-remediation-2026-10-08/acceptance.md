# QA-C06-02 原四链剩余整改验收

结论：`verified_for_finite_software_acceptance_scope`。本轮原四边界通过，总控签收软件整改；历史共享 TEMP 的归属/删除者取证和公共 handoff 清理声明仍有保留。这个结论不代表真实公司身份/评分正确，也不关闭 G3/F05 或启动全池扫描。

用户通知“QA-C06-02再次整改完成，请查收”。只读接收 StockQA `master`：基线 `361a721df382c468640b27bbafc484e31c8aa321`，软件结果 `b6eaa082e6e1df1306fa144bd623aa6de68213a1`，收到 HEAD `a39d7eafceacfa1114f5e5cb094eadb32030652c`。四运行源码、同包测试和交接调整；源仓七个原未跟踪条目保留，没有读取其内容。

## 本轮集中执行

从 result 的 Git archive allowlist 固定 **136** 个源码/测试/schema 文件，以收到的工作树字节执行并逐项核对 Git blob 的 EOL 等价性。**57** 个 worker 索引工件全部 raw SHA/长度匹配，五项仅 CRLF/LF 差异；`.secrets.baseline` 只核不透明 hash，没有复制或打印内容。五个冻结输入未改、未重签。运行前后源 HEAD、状态、工件和136份副本不变。

| 命令批次 | 实际结果 | pytest 时间 / wall |
|---|---|---|
| 原固定6单元＋3集成文件 | 247 passed | 51.48s / 52.427s |
| 原字节9例，含真实v5迁移/rollback | 9 passed | 1.83s / 2.401s |
| 原字节7例＋仓内9个mirror | 16 passed | 5.29s / 5.872s |
| 同QR1B补充segment一正一反 | 2 passed | 1.05s / 1.566s |
| IQS公开handoff CLI | exit 2，`temporary_root_not_cleaned` | 0.422s |

这些批次有语义重叠，不宣称合计为独立验收方法。没有测试失败、setup error或超时；没有重跑1083 full、UI或live。worker 的247/190/static/precommit日志按收到字节归档，其中190和全套日志不是总控重新执行的结果。

所有测试在 IQS 唯一根 `runs/qa-c06-r2-2026-10-08-01` 中运行。白名单环境剥离真实 key、live=0、pytest插件自动加载关闭、TEMP/TMP固定到自有根；沿用已验证的 audit guard，拒绝外网、外仓写入和非Python子进程。沙箱外执行只为 Windows asyncio 内部 socketpair，未放开模型/搜索网络。外部HTTP、付费、下载、生产数据库读写均为0。

## 四条边界与兼容性

- **QR1B**：错误 security ID 现在在 loader 和真实 CLI 入场拒绝。原例和 mirror 的实际记录均为 key opens=0、HTTP stub sends=0、network attempts=0、工作库不存在、结果文件不存在。补充 segment 例只使用合成内存副本：匹配通过，仅把 metadata.segment_id 改成外部 ID 并重签即具名拒绝。没有冒充真实 segment/owner golden。
- **QR2B**：seal、prepare、supersede共用已持久化 run/scan 映射规则；原 foreign-run 例无法绕过 blocked，无新增 revision或替换head。合法晚补输入/运行映射和完整封存回归通过。
- **QR3B**：原 `metrics.value=1e400` 及新增深层数组溢出在标准正文入口拒绝；有限12.5和正常正文保留。严格结构错误不能回退 compact或默认5分。
- **QR4B**：缺持久化 context/body 的 new-full prepare和supersede明确拒绝；即使外部封包各层重签，也不能替代原记录。原成功attempt/send-intent及完整正文重建校验保留；无默认/伪造侧表，compact、历史读取、合法升级和已落定只读回归保持。

真实子进程 cold→warm→seal、错题义、重复JSON早拒、坏正文不重问都包含在247批次。正常cold发送31次HTTP边界替身，后续独立warm/seal额外0次；31份完整观察经IQS公开validator验证，全部run/scan与持久化映射对应。它们都是synthetic，只证明软件链。一次 [独立复审](independent-review.md) 无同范围剩余阻断，未追加小节点审查。

## 交接与清理边界

worker R2回执新增两根完整逐文件 `[relpath,bytes,sha256]` 列表，总控重算两aggregate hash均匹配：1238文件/535目录与1127文件/454目录。该证据比原仅聚合口径更完整，但收到过去的CIM0/删除声明，不等于总控见证其过去清理；历史round1列表不可重建、共享TEMP删除者未证明。公共handoff仍因保留的历史 `cleaned=false` 标记exit2，原件不修改、不伪改为valid；本轮软件有限签收与该保留并列。

本轮自有根：已知进程52864/72795正常退出，无测试服务启动；严格CIM扫描0，不把扫描失败当0。615文件/284目录均lstat单硬链、无reparse，精确set/size/SHA复核，独立dry-run→Apply按清单非递归删除，根已不存在。源仓、旧根、共享TEMP、`nul`、`opencode.json`均未触碰。清理后重新核三个源仓HEAD/状态，无新增源写入。

原始结果见 [verification](../../../intake/QA-C06-02/2026-10-08-second-remediation/verification/batch-result.json)、[实际早拒记录](../../../intake/QA-C06-02/2026-10-08-second-remediation/verification/remaining-observed-state.json)、[清理回执](../../../intake/QA-C06-02/2026-10-08-second-remediation/cleanup-receipt.json)。helper使用固定已清理根，未来不能盲跑；重新复验必须分配新编号并固定当时result。

QA/SW有限软件整改输入现在均已接收，可进入既有联合12组的冻结与执行准备；本次联合仍 `not_run`。真实owner golden、事实/评分准确性、L02整体、L03、G3/F05、TH/IN的精确写授权分别按原门核实，不因本轮GREEN自动放行。Lab LR-02B和SW SR02-4B原签收成果保留。
