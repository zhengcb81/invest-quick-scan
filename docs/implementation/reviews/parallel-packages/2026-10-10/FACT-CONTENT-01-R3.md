# FACT-CONTENT-01-R3：保留未来候选，修正测试与清单

这是原FACT包同一次集中验收的小范围补丁，尚未自动派发。保留R2已修复成果；不重做八项闭合/包含图/旧版读取/46case。先确认本仓无另一个writer，不覆盖其他进程。

## 工作目录和接口

- 唯一写根：`C:/Users/郑曾波/Projects/iqs-fact-content-lab`。
- 接收基线：`codex/fact-content-01-r2@1ece6b2b49195dc5a4514c8b263192cb017eed55`；产品 `fb187d92a5b267f8ec7bcbef10bfc8b396f4bb8e`。新分支建议 `codex/fact-content-01-r3`。开工记录实际HEAD/脏树；有新产品字节或writer先报总控，不reset/clean/stash。没有remote，不新建。
- 阅读本目录 `FACT-CONTENT-01-R2-acceptance.md`、原R2卡、原 `docs/implementation/parallel-lanes/packages/2026-10-10/handoff-rules.md` 和 `inputs.lock.json`（IQS只读）。CodeGraph已有索引，不重复初始化。
- 写范围：`src/iqs_fact_content_lab/case_rules.py`、`tests/test_r2_counterexamples.py`、对应新增集中测试；必要的README时间口径说明；新增 `docs/handoff/FACT-CONTENT-01/remediation-03/`。允许只为修复本次清单不一致而刷新R2 `artifacts.json` 的两planning条目，其他R2/R0/R1原件保留。范围外改动先报备。
- schema仍具名1.1.0；该补丁修正拒绝条件，不改变旧字段定义、稳定题目ID、版本或真实金融资格。其他仓、共享配置、生产库/名单、安装镜像、正式F05算法不属于范围。

## 一起完成三项

1. **未来计划只阻止不成立的true。** 现逻辑遍历全部assertions、一概拒绝 `valid_from > information_as_of`，误伤合法输入。将当前目标的支持资格绑定其primary证据和目标语境：未生效证据不能把当前关系或strict判true；非primary未来补充不得推翻由有效主证据支持的当前目标；合法 `candidate_relation/basis=forward` 且relation/strict为unknown、explore=true应可读。保留未来日期、未知、周期/恢复候选，不删难例，不把unknown改false。
2. **修正旧版嵌套路径测试。** 现测试的 `legacy-secret` 根名先被挡住，prepare又产生1.1包，根本没到旧版嵌套路径。用中性根名和真实 `content/archive/content-pack-1.0.0.json` 对应旧版cases，先同根正常read-legacy exit0，再只改nested case_file为自有 `api_key.json` 并同步哈希/pack_id，应exit6。断言实际脱敏的 `secret-like path component rejected`，不要求回显秘密文件名，不放松产品guards。主控已独立证明产品会正确拒绝，不要重复实现legacy。
3. **交接清单最后冻结。** R2的 `planning/progress.md`、`planning/task_plan.md` 当前raw SHA/bytes与artifacts不符。允许精确刷新这两个条目；新R3三PWF写完后再生成R3 artifacts，核全部条目，避免清单生成后又写PWF导致同一问题重现。

## 测试包和集中续验

先用当前原代码复现两项FR2-01正常控制被拒，保留原RED；一次针对性测试组至少覆盖：原当前uses_equipment正例；同主证据加非primary未来计划仍正；forward候选unknown仍可读；未来主证据伪装当前true仍拒；未来strict=true仍拒；历史不相交仍拒；无源true仍拒；中性根真实旧版正常/嵌套假秘密反例。先确认schema/同步hash有效，不能让其他错误替代目标。

开发只跑这个受影响组；稳定候选一次相关完整回归与公开CLI验证，交回同一次集中审查，不建各helper门、不重做UI/备份/旧135已绿检查来增加次数。不把重叠批次相加。用主控 `fact_r2_counterexamples.py` 作为只读规格：它绑定IQS自有根，禁止直接在Lab运行；在本包独占根实现同构输入并调用本包实际CLI。主控未来将只针对这三项续验。

测试全程离线，无API/key/公司文档；清除凭据环境，TEMP/TMP/TMPDIR/pytest/子进程都用自有短根。真实junction既有保护保留；清理先核实际进程终态和精确自有集合，链接只删自身。保留RED/失败/GREEN/stdout/stderr/JUnit/退出码，不动共享TEMP。

## 交回

新增 `docs/handoff/FACT-CONTENT-01/remediation-03/`：`handoff.json`（原1.0.0 schema、package_id仍FACT-CONTENT-01）、summary、artifacts、interfaces、case-map、isolation、三PWF、原始日志，另列FR2-01～03处置。先正常精确产品/测试commit，再交接commit，记录完整result_commit、实际最终HEAD和原输入锁raw SHA，所有工件哈希必须与最终工作树一致；不把自身包含到自身hash循环。无remote只本地提交。

说明原R2已通过135测试、原八项/三内容修复保留，主控25独立CLI为23符合/2正常输入误伤；旧测试为覆盖问题而非新的产品秘密绕过。不要声称原交接已完整签收。

候选仍synthetic/not_mapped/not_run，4proposals/7unresolved及F05真实oracle门保留。本卡不关闭G3、F05、C06/W15、金融准确性、正式题库/词表发布、TH/IN或全池目标。
