# JR1/JR3 同批整改与联合验收

接续 [原整改卡](../joint-2026-10-08/remediation.md)，不新增审查门、不刷新退役 C01–C07 回执。用户已授权四文件并由总控独占 writer。当前只在 IQS 自有 `runs/r13a` 运行，StockWiki 源仓尚未写入；第五路径的一行备份兼容待人类许可，见 [具体补丁](backup-scope-extension.md)。

源码基线：SW `c40de21403720306ba21edbf71b9634a40ee58f8`；QA 已发布 `bc41908e4cdc44c13fefda97f3118e5434aed5f8`。外仓源状态及 Git blob/工作树摘要另存 `intake/G3/2026-10-09-jr13/source-preflight-01.json`。源变化须重新定界，不覆盖别人修改。

## 产品行为与兼容

- 新导入事务保存严格公共 ImportAck 1.0.0（十根字段，原公开状态/错误码，精确 consumer）。内部 reason、detail、序号和 original-import 引用进入独立审计表。
- `scan_observations.sqlite` schema 2 只新增审计表；版本 1→2 原子迁移，不回填历史审计，不改历史 ACK/观察 JSON、ID、时间、SHA。只读已有版本 1 的 ACK 不自动升级数据库。
- 历史包在严格JSON和原包hash校验之后、全四绑定匹配ledger时走mode=ro原回执重放，不迁移、不补审计；旧短地址兼容和公开格式严格准入分别处理。非公共历史wire的legacy_wire_pending只放receipt根。
- mixed批次即使有新槽，也必须核全部已有槽；写事务再次核四绑定，覆盖readonly快照后出现竞争槽，任何错槽整批回滚。
- 历史 enriched ACK 原样回读；QA 未注册这种旧 wire 时保留待处理状态，不能通过删字段伪造成公共 DTO 或 delivered。
- 公共 conflict 统一 immutable 冲突码，具体执行键/ID冲突原因保存在审计。其他 public taxonomy 由同一个映射函数生成，不让原内部详细码泄漏到 wire。
- 接收 raw JSON 在任意对象深度/数组内拒绝重复键、NaN、±Infinity、±1e400；direct dict 同样拒绝非有限值、非 JSON 类型、非字符串键与循环。在导入写事务之前结束。
- 实际审计插入失败，观察、ACK 和审计一起回滚。现有备份工具须将该库上界 1→2，否则实测拒绝新版本备份；其他库上界及备份协议保持。

## 测试原件与范围

原件位于 `docs/implementation/intake/G3/2026-10-09-jr13/`；保留原失败，不修改过去日志以适配新结果。

| 批次 | 实际结果 | 含义 |
|---|---|---|
| ingress-ack-red-01 | 18F / 4P | 14 产品反例失败，4 CLI 反例是子进程未传 guarded env 的测试遗漏 |
| ingress-ack-green-01 | 22P | 修复严格解析、公共 wire 与 CLI env 后的新反例 |
| affected-backup-red-01 | 47P / 2F | 一处旧测试未切到内部 audit；真实 schema2 超 backup cap1 |
| affected-backup-green-01 | 61P | 私有一行 cap2 后，观察/交付/实际备份恢复通过 |
| static-01 | 失败 | Python-only 测试 guard 阻断 Ruff 的 Rust 子进程；框架静态校验通过 |
| format-01 / format-02 | 成功 | 仅五候选路径修复 import/格式；不修改历史工件 |
| static-02 | 成功 | 原 Ruff 范围及框架静态命令通过；Ruff 明确作为非秘密 native 静态工具执行，不伪称 Python audit 覆盖 Rust |
| affected-final-01 | 93P | 格式后当前五路径：观察、交付、备份、查询、新鲜度；含真实 audit 插入失败回滚 |
| joint-01 | fixture setup error | 导出遗漏非秘密指标注册表，发送前停止，无 HTTP |
| joint-02 | fixture setup error | Git LF 与旧独立 fixture authority 冻结的 Windows CRLF byte SHA 不同，发送前拒绝 |
| joint-03 | 2P / 1F，整批不合格 | 测试中格式修订触发 source SHA guard 作废；旧独立模型fixture只改返回B、未请求B，当前Q10正确拒绝 |
| joint-04 | 4P / 1F | 空身份库fixture未migrate，CLI正确拒；控制器把自己明确读取的synthetic配置误算为真实key，原ledger保持 |
| review-red-01 | 10F | 独审三发现的新增反例全部失败；控制器旧全空ledger断言另有失败，原stdout/JUnit保持 |
| review-green-01 | collection error | 删除fallback参数后遗留bare星号，具名SyntaxError留档 |
| review-green-02 | 10P | 严格地址、accepted原引用、锁内版本读取修复后新反例通过 |
| affected-final-02 | 103P | 独审修复及fixture地址标准化后当前五文件，pytest13.29s；与93P分批，不相加 |
| static-03 | 成功 | 当前源码Ruff及框架静态通过，模块尺寸仅诊断警告 |
| joint-05 | 18P | pytest124.67s；实际公开CLI/31包导入/原ACK/预绑定/恢复/备份通过，source_changed为空，synthetic配置读取分别留档 |
| compatibility-red-01 | 2F / 1P | 真实历史短地址准入与原包只读重放的回归；篡改原hash负例已拒 |
| compatibility-green-01 | 13P | 原10审查回归加3历史对账回归，pytest2.26s |
| affected-final-03 / static-04 | 106P / 成功 | 当前历史只读修复候选，pytest13.62s |
| joint-06 | 18P | pytest138.65s；源未中途改变，仍不覆盖随后mixed事务修复 |
| mixed-red-01 | 4F / 3P | 混合顺序与快照后旧槽写事务核验漏洞；反序原拒绝和正确混合原通过 |
| mixed-green-01 | 7P | 两冲突字段/两顺序、模拟旧槽快照边界及正确混合均通过 |
| affected-final-04 / static-05 | 113P / 成功 | 最终五候选固定SHA，pytest14.88s/controller15.48s；Ruff与框架静态通过 |
| joint-07 | 18P | 最终同五SHA，pytest131.36s；source_changed为空，31原包/原ACK及第二独立合成执行 |

93P 与之前22P/61P是分开的执行，不相加作单批数。未运行未变的完整UI、全仓full或收费API。公开正 ACK 必须来自 StockWiki 实际导入与 `ack_for()` 原件，不手造、不投影；错误 ACK 是明确负例。

## 隔离与执行

`prepare.py` 只导出331非秘密 SW 代码/静态资产。`prepare_joint.py` 导出 QA 148 文件，`supplement_joint.py` 明确补唯一指标注册表；惰性配置、空名单、无真实 DB/密钥。原历史驱动按字节复制，当前目标绑定薄适配器已有冻结输入；本批 `qa_actor.py` 只为第二个 synthetic 执行明确请求模型B，不改产品alias验证。

`bind_fixture_bytes.py` 仅将私有 manifest 恢复到独立旧 authority 已冻结的 CRLF 文件域；canonical JSON/问题/authority不改，前后 SHA 与依据分别留档，不能当作真实 owner golden。独立 release 由派发前冻结 manifest 和模块锁生成，不取 Observation 内容。

`run_batch.py <unique-label> <tests...>` 为每次保留原 stdout/stderr/JUnit、实际 argv/cwd/exit/耗时和源 SHA；最终新批还记录 source-before、源中途变动以及各 owner 实际 actor PID/终态/请求回执。E97 guard 限写自有根，环境去真实 key、禁外部插件/网络/字节码，TEMP 指向自有目录。冷 native HTTP 使用明确 synthetic 替身；warm/seal 撤掉替身，须零新增HTTP、原 attempt/包/账务不变。Python guard 不是全操作系统安全认证。

不要盲跑任何已存在或已清理的固定根一次性 prepare，标签不能复用。后续复现先检查 root、创建全新独占短路径并固定完整代码/fixture/config/guard；当前 helper 属于这一次隔离验收，不是生产运行器。

本次只有一个集中独审：[原报告](independent-review.md)，确认一P1/两P2，同一审查者接续历史对账与mixed批次边界的复验，最终正式报告另存 `compatibility-recheck.md`。原证据位于 `independent-review-evidence/`，不覆写。[最终验收](acceptance.md)与[正式同次复核](compatibility-recheck.md)已经留档：F1–F5软件发现全关闭；最终候选/原包已冻结，自有根按cleanup-receipt严格清理。源码发布/外仓Git仍待第五路径的一行许可，IQS归档Git以progress实际终态为准。G3/F05/L03、真实 identity/facts/query owner golden、金融准确性/真实计价、TH/IN授权和一键全池启动仍按原前置，不由 synthetic 软件验收关闭。
