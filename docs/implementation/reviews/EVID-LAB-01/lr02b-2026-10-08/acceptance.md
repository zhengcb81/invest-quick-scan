# LR-02B 单项收口：有限软件验收通过

日期：2026-10-08（Europe/London）。总控结论：**LR-02B 历史来源锁绑定与拒绝发布的有限软件范围已签收，无剩余该项软件阻断。** 先前六项修复及 SW 已签收结果保留，未扩大到答案准确性或项目全局门。

| 交付项 | 固定证据 |
|---|---|
| Lab 分支／基线 | `codex/evid-lab-01`／`aeff0e68022f56b331a58503df7b53ed8d2b3882` |
| 新软件结果 | `cef3d95969671d10b42138ed97010c9c164b5118` |
| 实际收到的交接 HEAD | `2c0efb6370e401ca84d5f23cd5047de2bbfdec0a`，clean、无 remote |
| 实际版本 | CLI 0.2.2；structure-rules/4；semantic-rules/3；diagnostic schema 1.2.0；fixture schema 1.1.0 |
| 工件／执行副本 | 141 项 raw size/SHA 与接收 Git blob OID 匹配，118 件仅 EOL 差异；固定 Git 导出 142 文件 |
| 执行边界 | 只在 IQS 新独占副本运行；Lab 原 writer 保留，源仓只读 |

修复复用既有 `verify_lock`：所有读取锁定历史归档的入口，先按实际读取的 IQS 根校验原锁、index 和绑定文件，再消费该归档。历史 fixture replay 和 catalog 均在派生／发布前检查，源答案仍完整比较，省略可选 `answer_sha256` 的未改答案继续接受。缺失或漂移变成明确 `InputDriftError`／CLI exit 2；纯 synthetic 和未收集槽继续独立工作。结果提交之后只有交接及归档工具变化，执行源码／测试／fixture继续绑定软件结果提交。

## 总控实际复验

| 范围 | 实际结果 | 证据位置（intake/verification） |
|---|---|---|
| 原回归方法 | **108 passed**；新增十项首次因隔离前缀过长在 setup 报错，不算产品 RED | `worker-regression.*.log` |
| 只补跑新增十项 | **10 passed**／31.45 秒，wall 37.637 秒，源字节和全部断言未改 | `archive-binding-tests-short-temp-in-lab.*` |
| fixture catalog | 34 fixture／350 record／0 问题，类别 28 synthetic、5 historical、1 未收集片段槽 | `public-fixtures.*.log` |
| 三归档重放 | 两个独占输出根，五个核心 payload 逐字节一致，两个 CLI 都 exit 0 | `public-index-a/b.*.log`、`replay-*.json` |
| 逐 fixture 公开重放 | 34/34 CLI exit 0 | `fixture-FX-*.log`、`result.json` |
| 原四真实 CLI 正反例 | 四个预期全部满足，无失败发布或 staging 残留 | `archive-binding/` |
| 隔离 canary／公开 handoff | 均 exit 0；handoff 只证明结构与声明范围 | `isolation-canaries.*.log`、`public-handoff.*.log` |
| 一次集中有限独立审查 | 无剩余软件阻断；动态放行条件已满足 | [独审记录](independent-review.md) |

108 与新增 10 项不重叠，合计 **118 个不同方法通过**，但不是一次 118 全绿运行；首次十项 setup 错误及中间适配失败的日志均保留。初批 40 命令为 39 exit 0 加 1 回归 setup 错误；十项补跑单独留回执。正常 catalog 加 36 重放 wall 共 47.044 秒。原 9／5／6 的单独测试组不机械复跑，相关用例已包含在当前回归中，旧证据保留；worker 的 118 全绿日志仅称收到的证据。

原四反例保持原锁/index，不重新签篡改输入、不改成 xfail，实际 wall 共 3.104 秒：

| 公开场景 | 实际 | 发布 |
|---|---|---|
| 完整历史答案、省略可选 hash | exit 0 | 合法发布 |
| 只改 fixture，归档不动 | exit 4 | 无最终目录 |
| **同改副本归档与 fixture，原锁不动** | **exit 2** | **无最终目录** |
| 同一漂移副本走 index | exit 2 | 无最终目录 |

核心绕过从上轮真实 exit 0／错误发布 historical 改为本轮 exit 2／无发布。catalog 对漂移归档拒绝，缺锁、缺归档、严格 JSON 与 synthetic 兼容也由十项原断言验证。无最终目录意味着没有 `verified_before_write=true` summary；源测试及总控补验都检查了 staging 无残留。

## 隔离适配与证据限制

初次隔离副本使最长测试复制路径达到 266 字符，超过本机 MAX_PATH；原断言未执行。controller 第一次内存适配将 TEMP_ROOT 置 OWN/t，使 replay 输出落到 LAB 外，被产品正确 exit 3 拒绝（8 failed／2 catalog passed）。第二次改 OWN/lab/t，最长绑定输入路径缩短且输出保持在 LAB 内，十项通过。只在内存中调整 conftest TEMP_ROOT、环境与 pytest basetemp，没有改源文件、题义、fixture 或断言。两组失败日志、初版 adapter、最终执行 adapter 分别留档；未重复原 108 方法或扩成新软件整改。

只读 helper 曾猜错不存在的 `guarded_run.py`／`finish.py`，改用实际 `lab_sitecustomize.py` 和 collect/close；一次长补丁格式被拒于写入之前，改为单文件补丁。错误属于 controller 适配，不算产品失败。审查直接读已经明确的固定差异文件；未运行 CodeGraph init 或写外仓索引。

收到的九份新 worker 清理回执声明根已无、无 gap，本轮只读核它们所列根确实不在。回执仍只保存 aggregate manifest SHA，没有逐文件 size/SHA 清单、硬链和独立 OS 进程／监听证明；不能用当前不存在来独立证明过去删除或追认旧环境。先前 `nul` 外写事故／共享 TEMP 取证限制继续保留，`external_writes=false` 只描述对应验证运行。总控不清理、重写或伪补 worker 历史证据。

proposal 仍为 `draft_not_signed / execution_enabled=false / live_not_run=true`；收件不签提案。锁完整性只证明消费字节与可信冻结输入相符，不证明历史模型的事实、评分或证据判断正确，人类 gold 与校准仍未运行。

## 本轮清理和接手

本轮唯一根 `runs/evid-lab-lr02b-2026-10-08-01` 已清理。API key 未传入 child；继承 Python audit 限定根内写入、禁止网络与任意非 Python child，canary 实际通过；不是完整 OS 读取隔离或系统抓包。没有 API／网络收费、下载、真实数据库访问或外仓写入。

原始运行 session51936 实际 exit 0（其 child 回归 setup 错误单列），第一次适配27960实际 exit 1，最终适配45434实际 exit 0；原四 CLI 同步 helper 也实际 exit 0。源测试各自清掉内部临时根并写三份新回执，总控只接收不当历史 OS 清理证明。剩余自有 **396 文件／97 目录**经过 strict CIM0、无自有服务端口、lstat 单硬链无 reparse、精确集合／size／SHA，独立 dry-run 后 Apply（session91535 exit0），最终根已无。原始 dry-run、Apply 和逐文件清单分别归档。

142 导出源、128 原 IQS 锁输入与141工件前后不变；Lab 收尾 HEAD／clean 保持、`.temp-roots` 无子项。旧 Phase92 根、shared TEMP、外仓和既有 `opencode.json` 都未清理。

下一步由原 QA writer 按 [QA 四边界接续卡](../../QA-C06-02/remediation-2026-10-08/remaining-repair.md)提交新交接，再有限复验；QA/SW 两端具备条件后做既有 [联合 12 组](../../G3/joint-acceptance-preparation-2026-10-08.md)。Lab 不人为成为该链前置，也无需重复 LR-02B 实施。**L02 整体、人类 gold／事实准确性、G3/F05、TH/IN、L03 不因本项签收关闭。**

机器结果：[result.json](../../../intake/EVID-LAB-01/2026-10-08-lr02b/verification/result.json)。实际提交推送只认根 `progress.md` 最后回执。helper 写死本轮根，已清理，不能盲跑旧 prepare/run/cleanup；需要新复验时先锁定新提交并建新根。完整历史命令在机器结果与三个独立补跑回执中，raw bytes 由 delivery-index 绑定，不重采网络、不改旧输入。
