# SR02-4B 接续验收：有限软件范围签收

日期：2026-10-08，按用户 Europe/London 时区记日。结论：**SR02-4B 已修复并经总控有限验收，未发现该范围剩余软件阻断。** 原 SW-REPAIR-02 已通过交付保留；这不是 G3/F05 或整个项目的签收。

| 项目 | 固定证据 |
|---|---|
| StockWiki 分支／基线 | `master`／`1831a73b37a3ed1b67d3556f6425ed2b52594a24` |
| 软件结果提交 | `cc587a8cf76f2c50a0cdfb4693d3767dfa5944fa` |
| 实际收到的交接 HEAD | `d253fea5f4f6e4242d2b91eaf8d89d3dac8b45ff` |
| 本轮改动 | backup 源码、`test_swr_backup.py`、backup 说明，共三文件；结果提交后的改动只在 handoff 目录 |
| 总控执行副本 | 固定 Git 导出 296 文件；仅在 IQS 新独占测试根运行，收尾 SHA 不变 |
| 收到的工件 | worker 索引 75 项 raw size/SHA、Git OID、每项 blob_ref 均核验；41 项只有 EOL 差异 |
| 收尾源状态 | 同收到的 HEAD，`master`、clean；75 项原件及另外两份真实回执不变 |

损坏 manifest 原先使公开 list/prune 整体抛 `UnicodeDecodeError`。现在 list 将其列为 invalid，prune 跳过并按正常规则保留、清理合法备份。verify/restore 对损坏 manifest 以 `manifest_invalid` 具名拒绝；损坏 owner registry 以 `owner_registry_invalid` 拒绝，不获得删除权。严格 UTF-8、合法 JSON 形状和既有归属检查继续有效，没有忽略或替换损坏字节、宽泛吞异常。

| 本轮总控实际执行 | 结果 | 原始证据 |
|---|---|---|
| IQS 公开 handoff CLI | exit 0，仅结构／声明范围预检 | `verification/public-handoff.*.log` |
| 两个受影响 backup 测试文件 | **43 passed**，13.28 秒／wall 14.474 秒，包含七个新增损坏输入实例 | `verification/core.*.log` |
| 上轮固定的原两个 list/prune 反例 | **2 passed**，1.10 秒／wall 1.829 秒 | `verification/utf8.*.log`、`counterexamples/` |
| 七次真实公开 CLI 子进程 | **4 成功＋3 预期具名拒绝**，wall 14.755 秒 | `verification/cli-corrected.*.log`、`verification/public-cli-result.json`、`verification/public-cli/` |
| 一次集中有限独立复审 | 无剩余软件阻断，动态放行条件已满足 | [独审记录](independent-review.md) |

CLI 两组分别用 `0xff` 和截断多字节 manifest，均验证 list/prune 继续，外来文件字节不变、仅旧合法备份被删、新合法备份保留，verify 具名拒绝。第三组损坏 registry 的 prune 具名拒绝，两个合法备份都保留。restore 的损坏输入拒绝在受影响源码测试中覆盖，没有另外声称执行了 CLI restore。

这些计数描述各批次，不相加为唯一测试数量。上轮 96 相关／原 12 反例／11 浏览器结果保留，本轮无 UI 或接口改动，未机械重跑 full/UI；worker 的 96 项及 static-only 日志是收到的证据，不冒充总控重跑。副本里的原 12 问题脚本只为原两个反例和 CLI 提供 helper；归档中原 7、原 12 脚本的 `executed` 文件名不表示本轮重跑这两套。

本轮唯一 controller 运行失误：初次 CLI `verify NAME` 缺 `--name`，实际 argparse 拒绝后依据既有公开说明改为 `verify --name NAME`。原命令、exit 1、原 stdout/stderr 和初始脚本完整保留；改用新子目录与唯一日志标签，只重跑 CLI，不将 controller 误差算成产品 RED。读取控制器时曾猜错 parser 文件路径、IQS 接手文档路径及两份清理回执的归档位置；按实际文件定位，未据缺失猜测生成 owner 正例或写外仓。

## 工件与历史清理限制

worker 的 `git_blob_sha256` 字段全是 40 位 Git SHA1 blob OID，名称误标。总控按 OID 核验实际 blob_ref，并独立记录 raw 及 Git 字节的真实 SHA256。75 项均匹配收到的 HEAD；软件结果提交没有后来产生的六项证据、另五项后来改变，按每项实际 ref 归因，不误报运行源码漂移。

worker 的 `cleanup_receipt_r3.json`、`process-listener-final-state-r3.json` 未列入其 75 项索引。总控只读取得真实文件，核对收到 HEAD 的 Git 字节，另列 [supplemental-artifacts.json](../../../intake/SW-REPAIR-02/2026-10-08-sr02-4b/supplemental-artifacts.json)，不改 worker 索引。R3 回执报告 538 文件、671 目录、六个内部 junction 已清理，原根实际已无；总控没有亲历其删除。

R3 dry-run 的 **538 个 `nlink` 均为 0**，不能认证回执文字所称 `nlink==1`。该历史硬链审计仍有取证限制，不用零值冒充单硬链。旧 R2 逐文件 SHA／硬链／正式端口审计仍 `not_performed`；旧 shared TEMP 删除者与时点不明，pytest retention 仅是一种解释。保留事实边界，不用本轮测试或清理追认过去；这不是剩余 backup 软件错误，也不新增小节点 gate。

## 总控本轮隔离和清理

唯一根为 `runs/sw-sr02-4b-2026-10-08-01`。子进程 ENV 白名单去除密钥，使用 inert 空 provider 配置，Python 写入限定该根，外网阻断；没有启动浏览器／服务器，没有收费请求、下载、真实数据库读写或外仓写入。guard 与 canary 记录留档；不声称 OS 全读取隔离或系统抓包。

已确认测试 session `26819`、纠正 CLI `56332` 均终态；清理准备 `41396`、Apply `87965` 均实际 exit 0。strict CIM 进程匹配为零；本轮没有服务端口。六个自有 junction 两端先核在独占根内，只非递归删除节点，目标保留。随后 **693 文件／468 目录**经 lstat 单硬链／无 reparse、精确集合、size/SHA 核验，单独 dry-run，再 Apply 按清单删除，最终根已无。记录见 intake 的 `junction-*`、`cleanup-baseline.json`、`cleanup-lstat.json`、`cleanup-dry-run.json`、`cleanup-receipt.json`。

296 导出文件、131 原 IQS 输入、75 收到工件和两份补充回执前后不变。没有清理旧 Phase92 根、shared TEMP、其他 harness 文件或原 `opencode.json`。

## 接手与下一步

1. **不要重复实施 SR02-4B 或重跑旧完整／浏览器套件。** 本文和 [机器验收结果](../../../intake/SW-REPAIR-02/2026-10-08-sr02-4b/verification/result.json)签收的仅是固定软件范围；提交推送实际回执在根 `progress.md` 末尾。
2. QA 的四同链边界仍按 [QA 接续卡](../../QA-C06-02/remediation-2026-10-08/remaining-repair.md)由原 writer 交新提交；Lab 的 LR-02B 按 [Lab 接续卡](../../EVID-LAB-01/second-remediation-2026-10-08/remaining-repair.md)独立接续。总控不写动态外仓，不向外部 harness 自动派发消息。
3. QA 新交付先有限复验；QA/SW 两端具备条件后执行既有 [联合 12 组准备](../../G3/joint-acceptance-preparation-2026-10-08.md)。Lab 不人为成为这条链的前置。
4. 真实 owner identity/facts golden／生成命令仍缺，facts 可用性不能改 true；QA→W05 import/ACK/UI、双 owner 恢复和 TTL/replacement 未实证，同库多变体查询期选择仍不支持。**G3/F05、TH/IN、L03 不因本项签收解锁。**

可复核历史执行命令见 intake `verification/commands.json` 和 `cli-corrected.result.json`；执行时的守卫、CLI 脚本及两个固定反例逐字节留档。此目录 helper 写死本轮固定提交和独占根，根现已清理；不得盲跑 `prepare/run/cleanup`，复验必须先固定新证据并使用新根。从 IQS 根运行 `python -B -X utf8 docs/implementation/reviews/SW-REPAIR-02/sr02-4b-2026-10-08/close.py --index` 只会重建归档索引，不调用 API；签收后无字节变化时无须再运行。
