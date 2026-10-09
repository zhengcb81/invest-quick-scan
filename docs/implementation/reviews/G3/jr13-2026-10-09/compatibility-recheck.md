# JR1/JR3 同次集中审查最终兼容复核

**当前固定五个私有候选的软件行为可有限签收，software findings 零开放。原 F1/P1、F2/P2、F3/P2、F4/P2 和接续发现的混合批次 F5/P1 均已关闭。** 这是原集中审查的接续复验，没有新增审查门；原 independent-review.md、recheck.md 及其失败原件未覆写。

签收只适用于下列五 SHA。StockWiki 四个已授权源路径仍未发布，源基线为 `c40de21403720306ba21edbf71b9634a40ee58f8`；第五 backup schema cap 1→2 仍是私有候选，源路径权限待人类授权。本报告不关闭 G3/F05、真实 issuer/facts/query golden、金融准确性、付费能力或双 owner 灾备等全局门。

## 固定对象与集中验证

| 私有候选文件 | SHA-256 |
| --- | --- |
| stockwiki/quick_scan_import.py | 9ce116b34365a35490a5f0e0d9298e0fa8ea20982294bf5314253689ac9deddd |
| stockwiki/quick_scan_observations.py | d0e0b5e9dbfa37a536ee929e11ce9901e62119ce4458f7974911beb61fde11ff |
| stockwiki/quick_scan_backup_manifest.py | ad75cacec6e83590dbe25cfbe63f557ef828909c0fafb891ea4fcb21cf1175c2 |
| tests/test_quick_scan_observations.py | 22011d69fffdb1440ad45159fe85a30476b24caac6ad2857352a24ddaec2c2f1 |
| tests/test_quick_scan_delivery.py | b50ef0e46cc2a335a93f72eeb3fde6f76b1838ebbc0f637d6df6ae81ee4faeab |

独立 `final-02` 与 `regression-02` 的五文件前后 SHA 均与 `affected-final-04/source-before.json` 相同。总控 `affected-final-04` 实际 **113P/14.88s**，process wall_s 15.48；`joint-07` 实际 **18P/131.36s**，process wall_s 131.882；两批 returncode 0，source_changed_during_test 均为空。static-05 的全 stockwiki/tests/scripts Ruff 和 framework static 均 returncode 0。joint-06 的 18P 属旧 106P 候选，保留为历史软件证据，不用作当前 SHA 的证明。

联合测试保持实际 owner CLI→事前绑定 consumer→原 ACK→QA 严格应用和暖恢复的软件路径。两模型请求在执行前明确冻结。数据、身份和执行收据是 synthetic fixture；实际包字节和原 ACK 不能转称真实公司或金融 golden。

## 发现状态与独立反例

| 发现 | 最终状态 | 当前独立验证 |
| --- | --- | --- |
| F1/P1：新非法地址生成或持久化非公共 ACK | 关闭 | 六项真实 CLI：坏 item ID、空 item、短 observation ID、空 SHA、null observation ID、有效 item 后附空 item，全部 exit 2 / ack_address_invalid，整 DB SHA 不变。direct store 有效+非法混合整批零写拒绝；四种合法状态的原 ACK 通过冻结 ImportAck Schema/format 校验并与 ack_for 相同 |
| F2/P2：already_present 原引用选到前置 rejected | 关闭 | 实际 rejected→补 synthetic entity→新包 accepted→第三包 already_present，audit 只引用 accepted 原 package_id，且新 audit 明确包含该 accepted item_id |
| F3/P2：schema1→2 并发迁移读版本早于锁 | 关闭 | 两个真实 importer 同时从 schema1 以及无 DB/schema0 进入，都成功；实际 PRAGMA trace 的迁移读取均处 BEGIN IMMEDIATE 内，最终版本 2；原 ACK 未改，全部线程已 join |
| F4/P2：历史短地址精确原包重放被新 admission 拒绝 | 关闭 | 用 c40 原 serializer 和 schema1 store 生成 short 与 64hex 两类历史 enriched ACK；当前实际 CLI 各重放两次，另 direct 四键原件重放，均精确返回原 ACK，无迁移、无 audit 表新增、整 DB SHA 不变 |
| F5/P1：前置缺槽掩盖后置旧槽冲突，写事务未复核 | 关闭 | wrong/correct × existing-first/new-first 四批验证；wrong 两顺序均 historical_ack_binding_mismatch，整 DB SHA 不变；correct 两顺序保留旧原 ACK 并提交一项新观察。另真实第二 SQLite 连接在只读扫描后提交竞争槽，外层写事务具名拒绝且较早 new 插入全部回滚 |

最终地址与重放代码位置：quick_scan_import.py:576/630；quick_scan_observations.py:138、180、344、402、423、497、659。完整冻结源码已归档，不依赖后续可变 runtime 文件。

F5 的原独立反例使用公开 `QuickScanObservationStore.apply_decisions`：`[new_valid, old_same_pkg_item_with_wrong_payload]` 在旧 106P 候选上返回成功，observation/ACK/audit 各从 1 增到 2，且返回旧 ACK 的 payload 与传入 decision 不同；反序却具名拒绝、DB SHA 不变。根因是 readonly replay 遇第一缺行立即返回 None，随后 `_apply_one` 仅按 package/item 返回 ack_json。该证据证明公开 store 批次缺口，不声称可以绕过单个 CLI package 的包哈希。

总控同批修复为缺行记 missing 并扫描所有已存行；readonly 与写事务共用 `_checked_original_ack`，复核 package/item/observation/payload 四绑定与原 ACK/ledger 一致性。原 mixed-red-01 **4F/3P** 与 mixed-green-01 **7P** 的写事务边界用例含模拟缺槽快照，不能泛称真实并发。独立 final-02 另外真正执行了原 readonly lookup，然后另一 store/另一个实际 SQLite 连接提交竞争槽，外层才进入写事务；这是确定性双连接交错，没有用 mockNone 替代 lookup。外层失败后整 DB snapshot 等于竞争连接已经提交的 snapshot，第一项新 observation 不存在。

## 历史原件、输入边界与 QA

旧源两文件从 c40 只读导出的原 SHA 为 import `87c77921428cb52239f0276a647198aeb3988954f07b4debb468a1a1237dfa56`、observations `c06f4c58ea5557ab678721f78c5a14d595c26fef5fb1e55843382be956866691`。探针调用原 `import_package` 与原 schema1 store，未手造正 ACK。短 ID 在 helper 自动规范化之后显式赋值，以真实复现历史 short 输入。

两类历史原 accepted ACK 的 ID、时间、sequence、字段、ACK JSON SHA 均不变；返回 ACK 按原 serializer canonical JSON 重序列化后与 ledger 原 ack_json 字节完全相同，且数据库文件全 SHA 前后相同。非公共历史 wire 仅 receipt 根有 `legacy_wire_pending=True`，ACK 原 status/error/schema/时间和内部字段均保留。schema1 exact replay 不升级、不补审计。

在历史 schema1 上另验证六项真实 CLI：未重签原观察内容篡改、nested duplicate summary、array item 内 duplicate item_id、重新签名的新短地址包、历史 canonical 项与新增空项混合、缺 payload_sha256。全部 exit 2、全 DB SHA 不变。direct 错 observation 或 payload 四绑定均 historical_ack_binding_mismatch；没有通过 legacy 分支造新地址或新非法 ACK。NaN/Infinity/±1e400、direct 非有限值和循环输入、原子审计失败、迁移/备份边界的原反例及当前受影响集合证据继续保留，不将本轮重复断言扩大成真实数据证明。

独立 QA 检查先用实际 WorkStore prepare_result_delivery 生成最小出站包，再把旧接收 store_id 事前绑定并 begin。旧实际 serializer 对这个缺完整观察字段的包生成 **rejected enriched 原 ACK**；当前 SW CLI 精确重放原 ACK，QA 实际 apply_result_delivery_ack 拒绝 `import ACK fields mismatch`，状态保持 `send_uncertain`，QA 全 iterdump SHA 不变，无 delivered。该独立跨 owner 负例覆盖 rejected 旧 wire；旧 accepted 原 ACK 的精确保真在 SW 两类历史上独立覆盖。QA 源码的严格根字段检查先于 status 分支；最终 joint-07 另覆盖正常新公共 ACK 的完整闭环。

为尝试加强 accepted 旧 wire 的 QA 正身份绑定探针，reviewer 曾给 synthetic checkpoint 输出补完整观察字段；QA 在 prepare 时正确要求 durable context 和 standard answer，拒绝 WorkConflictError。该路径没有建立完整 durable context，不能作为 accepted 旧 wire 跨 owner 证据，也没有弱化生产 Q10 来制造通过。

## 原失败、归档与终态

本次三个 reviewer 自身探针失败原件均保留：final-01 对最小 QA observation 错误假设有 field_id；regression-01 错误假设新增 readonly replay 后仍只有两个 PRAGMA trace；qa-accepted-01 未建立完整 durable context。前两项在独立命名 final-02/regression-02 修正探针后通过；第三项维持 QA 正确拒绝。它们不算产品 RED，不抹成 GREEN。

`compatibility-recheck-evidence` 逐字节归档 **253 文件**，含原 mixed 失败、旧原 serializer、当前五候选、实际探针、输入/输出、主批与 static 原日志、QA 严格代码、guard 和 PID 终态。[原件索引](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/reviews/G3/jr13-2026-10-09/compatibility-recheck-evidence/evidence-manifest.json) 每项 original_sha256 与 archive_sha256 相同；归档不含 SQLite DB、配置文件内容或真实 key。机器结论另存 [compatibility-recheck.json](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/reviews/G3/jr13-2026-10-09/compatibility-recheck.json)。原两个报告和证据目录完整保留。

所有探针使用精简无 credential 环境和现有 guard SHA `696dfeecfc0aedc0732a3677faafa97c539cb3aaf12a04303359b109089d3858`，cwd/TEMP/项目写入均在各自独占根；成功产品探针 key/network 账本均空。未调用真实 API、未触碰生产 DB/名单或个人配置，未改候选、共同 fixture/controller 或外仓，未执行 Git 提交。guard 只证明本 Python 运行范围，不宣称完整 OS 沙箱。

本轮五个同步 reviewer 进程 PID 37568、60048、42436、39344、80772 已全部退出，实际 CLI 子进程已返回，concurrency 线程全部 join；此前探针也已同步结束，没有后台 helper。未清理任何根，交总控按严格自有范围归档清理。当前 software findings 零开放；源发布授权和全局门保持原状态。
