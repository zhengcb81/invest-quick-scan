# JR1/JR3 同次集中审查接续复验

**原 F1/P1、F2/P2、F3/P2 在 `affected-final-02` 固定候选上已复验关闭；发现一项历史短 ID 精确包重放兼容缺口，已交总控同批修复。** 此处“关闭”只指原三项具体软件缺陷，不是 JR1/JR3、G3/F05、真实金融/issuer/facts/query golden 或双 owner 灾备的整体签收。原 [independent-review.md](independent-review.md) 和原 raw 证据没有覆盖或删改。

## 本次固定候选与既有验证

| 文件 | SHA-256 |
| --- | --- |
| stockwiki/quick_scan_import.py | 496c48ef75482e46c6ff8da970068315c13f121706273b959609b16c2b0956dc |
| stockwiki/quick_scan_observations.py | 26b0e6fec9b3581d294b0b97460f1b851e5ce096112ead729bdbbc46e3aeaeda |
| stockwiki/quick_scan_backup_manifest.py | ad75cacec6e83590dbe25cfbe63f557ef828909c0fafb891ea4fcb21cf1175c2 |
| tests/test_quick_scan_observations.py | 24bd6d7520376a5ccf0f9e67bfc4b02f662ccb33475a8bccd9a3fa0cce8f635a |
| tests/test_quick_scan_delivery.py | b50ef0e46cc2a335a93f72eeb3fde6f76b1838ebbc0f637d6df6ae81ee4faeab |

独立探针在新独占根 `runs/r13a/reviewer-recheck` 开始/结束均与以上五 SHA 相同，且明确匹配 [affected-final-02/process.json](../../../intake/G3/2026-10-09-jr13/affected-final-02/process.json)。该批实际 stdout 为 103P；process 记录 wall_s 13.842。review-red-01 的原 10F 与 controller 分类阻断、review-green-01 的语法错误仍保留；review-green-02 实际 10P/42 deselected/1.85s。没有把失败日志改成 green。

联合 `joint-05` 已终态 18P/124.67s，process returncode 0、wall_s 125.212、五候选 SHA 与上表相同、source_changed_during_test 为空。其固定测试使用真实 owner CLI/ACK/ack_for 和事前 consumer 绑定；第二合成执行的请求模型 B 在调度前明确设置。它是软件闭环证据，不是真实 owner 内容 golden。

## 原发现的独立关闭证据

| 发现 | 当前修复 | 真实 owner 路径复验 |
| --- | --- | --- |
| F1：非法/缺失地址写入新 ACK | import 在逐题 decisions 之前预检全部 item 地址；store 在迁移/事务之前预检整批；不再制造 fallback ID | 六项真实 CLI 输入：坏 item ID、空 item、短 observation ID、空 SHA、null observation ID、有效 item 后附空 item，均 exit 2 / ack_address_invalid；observation/ACK/conflict/audit 计数为 0，DB 文件 SHA 前后相同。直接 store 的有效+非法混合 batch 同样具名零写拒绝 |
| F2：原导入误引用 rejected | original reference 限制 ledger status='accepted' | 原三阶段缺实体 rejected→新增合成 entity→新包 accepted→第三包 already_present 完整执行，第三 audit 现在引用第二 accepted 原包 |
| F3：schema1→2 并发伪失败 | BEGIN IMMEDIATE 后再读 PRAGMA user_version | 两个真正 import_package importer 同时从 schema1 升级并各自导入，都 accepted；独立覆盖无 observation DB 的 schema0 并发，两项也成功；两次版本读取均在事务内，最终版本 2；schema1 原 ACK 原样保留 |

另通过四种合法公开状态的真实 CLI：accepted、already_present、conflict、rejected；各原 ACK 通过冻结 ImportAck Schema 和日期 format 校验，并与 ack_for 永久原回执完全相同。当前地址正例使用明确的 synthetic SHA；为了重测旧短地址，探针刻意在 helper 规范化之后修改 observation_id，避免新测试 helper 自动规范化掩盖负例。

证据：[results.json](recheck-evidence/results.json)、[实际探针](recheck-evidence/recheck_probe.py)、[原始 stdout](recheck-evidence/probe.stdout.log)。所有实际 CLI argv、package/release 原文与 stdout/stderr 已逐字节归档；没有额外运行全仓或 UI。

## 同批新发现 F4 — P2：历史短 observation ID 的同包重放被新预检阻断

位置：当前 `quick_scan_import.py:609` 与 `quick_scan_observations.py:336`。新的全地址预检在读取原 ledger 之前运行，所以原来已成功存储的精确历史短 ID 包被当成“新非法地址”直接拒绝。ack_for 保留原件读取，原同 package_id/item_id 的正常 CLI 精确重放却回归。

反例没有手造 enriched 正回执：只读 `git show c40de21403720306ba21edbf71b9634a40ee58f8:<path>` 导出原 owner 两文件至新自有根，调用旧实际 `import_package` 和旧 schema1 store，生成 `obs_legacy_short` 的真实历史 enriched ACK。两个旧文件 SHA 分别为：

- quick_scan_import.py：`87c77921428cb52239f0276a647198aeb3988954f07b4debb468a1a1237dfa56`
- quick_scan_observations.py：`c06f4c58ea5557ab678721f78c5a14d595c26fef5fb1e55843382be956866691`

当前 store 升至 schema2 后，ack_for 仍返回原 enriched JSON，原 ack_json SHA 与 ID/时间不变。但同一原 package/item 的当前真实 CLI exit 2 / ack_address_invalid。对照的 canonical SHA 历史包经同样升级，当前 CLI exit 0，原 enriched ACK 精确重放。这使缺口定位在新地址预检，而非一般历史 JSON 保留或 migration。

最小修复已由总控接收：严格 JSON 和原包 hash 校验先行；全部 item 都有原 ledger 且 package/item/observation/payload 四绑定精确相同时，允许事务快照下只读原 ack_json，或具名 legacy_wire_pending 对账。只读分支不得迁移、补审计、造新地址/DTO或改原 ACK；缺行/缺字段/混合新旧非法包仍走新地址零写拒绝，原 slot 四绑定冲突应具名拒绝。非公共历史 wire 的 pending 标识放 receipt 侧，不改历史 ACK status/error/time；StockQA 仍严格拒旧 wire，不能自动 delivered。总控另将为新 F2 audit 补 accepted 原 item_id，不改旧 audit。

本报告的 F4 **尚未复验关闭**；当前所有上表旧 SHA 产品探针已停止，后续同批兼容修复将固定新的 SHA 再接续验证。

## 控制器替身配置识别复验

旧 runner 仅检查 `providers.openai.api_key` 的一个值，未约束额外 provider 与模型，存在分类覆盖缺口；总控已同批改为完整精确替身形状。当前 `validate_synthetic_config` SHA 对应 controller 整文件 `8b2c4dd3a7cb2398600d655a8088b3a9339a4fc1a180bc243d5ad74ef444901d`。

独立在自有根执行冻结 validator 的**原 AST 函数**：精确 offline fixture 通过；额外 provider/dummy key、未登记模型、非 fixture dummy key、foreign base_url、多余根字段、bool max_retries 共六类全部拒绝。没有创建或读取真实 key。文件归属检查在 JSON read 前检查原 ledger 路径每层 lstat 的 reparse/symlink、文件 nlink=1，并要求 resolved target 在 OWN 内；这证明此 Python 控制器的约束，不宣称 guard 是完整 OS 沙箱。当前代码先 resolve 再 lstat，但未先读 JSON 内容。

第一控制器探针截取 main 的原判定块时，恰读取到刚新增 `validate_synthetic_config` 的版本，因未带入该函数而 NameError。原脚本、冻结 source、stdout/stderr 保留；独立命名 controller_probe-02 随后执行完整冻结 validator 并通过。该失败是 reviewer 自身探针依赖遗漏，不是产品 RED，不用于充数。

证据：[controller-results-02.json](recheck-evidence/controller-results-02.json)、[冻结 controller](recheck-evidence/run_batch-frozen-02.py)、[02 探针](recheck-evidence/controller_probe-02.py)；01 原失败日志在同目录保留。

## 隔离与限制

产品探针使用 `C:\Miniconda\python.exe -B -X utf8 <owned-root>\recheck_probe.py`，cwd 为新独占根，精简无 credential 环境，继承现有 guard SHA `696dfeecfc0aedc0732a3677faafa97c539cb3aaf12a04303359b109089d3858`；该探针终态 key/network ledger 均空。控制器-only 探针随后有意读取本根精确 offline fixture 和 dummy sentinel 配置，全部路径账本保留；没有网络 ledger，没有真实 API/生产 DB/个人配置访问。只读旧源 Git blob 导出不修改 StockWiki 源仓。

原始 source、脚本、结果、CLI 输入/输出、controller 失败与成功日志及 guard 已按字节复制到 `recheck-evidence`；[evidence-manifest.json](recheck-evidence/evidence-manifest.json) 记录 75 个归档文件原 SHA 与副本 SHA一致。SQLite 仅位于自有根，保留未删；没有修改任何候选/fixture/controller、没有发布/提交。

第五 backup schema cap 1→2 仍仅是私有候选且未获源路径授权。本轮软件通过不关闭真实身份/事实/查询/金融准确性、付费与双 owner 备份恢复等既有能力缺口；历史正 ACK 始终保持原件，不能用新 DTO 投影替代。
