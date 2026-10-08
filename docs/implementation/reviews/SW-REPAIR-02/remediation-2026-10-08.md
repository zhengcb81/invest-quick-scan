# SW-REPAIR-02第二轮整改卡：保留交付，修五组边界

交给**原StockWiki唯一writer**。工作目录`C:/Users/郑曾波/Projects/StockWiki`；本卡不是给总控新的外仓写授权，也不授权碰IQS、StockQA、Lab、company-wiki或安装镜像。若另一writer正在改本包路径，先由owner统一写入者；不reset/clean/stash整仓，不删除或提交他人改动。

## 接手基线与已有成果

代码结果`9f9e0afe16a327b475cb7a6e3d40bd1578bb9b0f`，交接`753dfcabd32b03887a3f340d4e5727f04549a94c`，总控2026-10-08收尾HEAD `6d1dddbc1289a17a2fb91d40a0d4f57494fa1bfd`，master/clean。后续narrative合入但卡内源/测试无diff；这只是时点快照，**开工先重新只读核实际HEAD/status**。原代码/文档/RED/GREEN日志保留，新增提交可在当前master上最小修改，不退回9f9e0af覆盖别线。

原六整改81项（74+7）与11真实浏览器已在总控隔离副本通过；原worker1032/1046全套日志留档。新增12个逻辑边界失败，见[验收](acceptance-2026-10-08.md)、[固定用例](acceptance_cases.py)、[最终输入/输出](../../intake/SW-REPAIR-02/2026-10-08/counterexamples/)、[原执行日志](../../intake/SW-REPAIR-02/2026-10-08/verification/result.json)。请勿重复实现原六项、换掉原反例或把尚未执行的跨owner验证写成完成。

## 写入边界

沿用原owner授权范围，预计代码主要在`stockwiki/quick_scan_profiles.py`、`stockwiki/quick_scan_rows.py`、`stockwiki/quick_scan_backup.py`及必要的`quick_scan_backup_manifest.py`；测试沿用`tests/test_swr_profiles.py`、`tests/test_swr_backup.py`、`tests/test_swr_cases.py`，必要UI回归仍在原获批`tests/test_e2e_quick_scan_ui.py`。文档限原`docs/quick-scan-backup-restore.md`、`docs/ui.md`、`docs/handoff/SW-REPAIR-02/`。原授权以owner施工消息/执行补充为准；本卡不凭harness自报扩权。需要新文件、数据库迁移、生产数据修改或新公开不兼容接口时，先提出具体范围，不代改。

没有凭据/生产库/名单/下载/收费调用需求。不要加第二调度器、下载财报、重发历史实验或自行补真实身份golden。其他QA和Lab整改可独立进行，勿访问它们动态未交付代码运行联合正例。

## 五组实现要求

### SR02-1：不可比观察必须保留且默认不入白名单（P1）

用真实公共观察导入入口分别导入同一entity/field的两条合法2分和9分。必须覆盖三个独立组：segment A/B；FY2025与2026H1（cutoff2026-09-30，均结束）；同2026H1 current与normalized。最终原输入是counterexamples中的segment/period/basis.json，不是`*-initial.json`。

当前accepted=2却丢2分。修复从SQL读取→detail字段投影→variant/comparison key→筛选的整条只读链，保留必要的segment、period_start/end、basis及已有主体/模型/rubric等比较维度。缺失维度不能和明确维度默认等同。详情可看完整2/9变体；未选择可比维度时score=null/status=ambiguous，`>=8`不能返回公司；不得平均或选最新高分。原subject/model/rubric隔离保持。

增加一个明确选择单一可比变体的正例，确认选低分不命中、选高分才命中，并保留仅一条正常entity观察的查询正例。若现公共接口没有安全选择能力，先保持ambiguous退出筛选并说明，不能暗中发明默认选择。新增显示字段兼容旧消费者，必要版本改动写明；不以改阈值、删除观察或去掉低分掩盖问题。

### SR02-2：备份根及父目录junction不能授予写/删权（P1）

总控两项真实Windows junction令create成功，备份写入逻辑workspace外（实际目标仍完全在总控自有根）。必须在备份操作实际写入前拒绝受管路径中的根/祖先重解析，不能先resolve再把目标当受管根。检查create、list/prune、restore相关路径是否共用错误安全根假设，保持原restore内部junction拒绝正例。

RED/GREEN至少覆盖根自身与backups父节点两个create例；补充同路径list/prune不删逻辑workspace外哨兵的反例/正例。**总控本次没有动态证明prune越界删除，勿伪称已有证据。** Windows原生junction不可用时明确skip和未覆盖，不能把POSIX symlink模拟写成Windows通过；最终需要Windows实际验证。

### SR02-3：删除登记必须绑定版本、owner和workspace（P2）

两份合法备份backup_a/backup_z；修改owner_registry总format_version为999，或仅backup_a记录的owner_module、workspace_root。当前keep=1均删backup_a。修复须使未知版本fail closed，错误owner/workspace不授予删除权；保留并报告，不偷偷重建或接受这个登记。

正例保留合法登记keep=1仅删除旧自有备份；受损/foreign备份被跳过时合法条目仍按明确策略工作。不要仅校manifest自digest，也不能让“登记记录含name+digest”绕过归属。registry/manifest版本和迁移/恢复策略在文档明确，旧合法版本行为不能无声改变。

### SR02-4：合法JSON也必须验证形状（P2）

在备份根放外来manifest `[]`、`null`、`0`、`{"files":null}`。list/prune不能因AttributeError/TypeError中断，也不能给外来目录删除权；将其报告为skipped/invalid并保留，同时正确保留backup_z、删除合法旧backup_a。通过结构验证完成，不用吞掉所有异常冒充成功。原损坏JSON、未知版本、内部链接等防护保持。

### SR02-5：交付必须可由公共入口接收（交接）

1. handoff authorized_paths用真实获批的具体test_swr文件名，不使用CLI不支持的literal glob或“带解释的路径”冒充实际授权。保持用户授权来源，不能靠扩大validator来过关。原正式handoff exit2 changed_path_out_of_scope；仅范围展开的总控诊断副本exit2 temporary_root_not_cleaned，均留档。
2. 原worker共享TEMP109/110/111未清，截图还有105。列出完整且真实的自己创建根/文件、进程终态和清理处置。**不能按pytest编号/mtime删除共享TEMP，也不能虚填cleaned=true。** 先取得可核对的独占归属清单；无法安全证明的残留保持open并由owner处理，整包不能声称已恢复。后续全部测试改用新独占basetemp，并把TMP/TEMP/浏览器profile设在同根。总控只清了自己的769文件，没处理这些worker根。
3. projection接口版本profiles/1.0.0当前却绑定rows.py hash ce206537…；修正为明确生产文件/契约及对应hash，或明确多文件manifest。工作树与Git blob9项仅EOL，不清洗旧日志，说明hash所指字节及从commit重建的办法。
4. 新handoff指向真实新result commit，正确标 review/结果/未完成项，重新生成artifacts原字节size/SHA。外仓remote推送仅沿用owner授权；总控不替你push。真实identity/facts golden、QA联合流、双owner恢复、F05/G3仍missing/not_run，不用synthetic填绿。

## 一批TDD与验收方式

先把12固定反例纳入本包测试，保留RED原日志；再同批完成五组。不要每改一个helper就申请独审。功能完成后一次运行受影响的原74+最初7+新增边界与必要正例，再一次11真实浏览器，必要仓库check按既有规范执行。原全套已有通过证据；本轮只在新变化/失败或仓库required check要求时扩大，不机械反复重跑。

原总控命令（已执行留档，不要原地重跑覆盖intake）：

```powershell
# IQS只读公共handoff预检；有效结构不等于整包验收。
python -B -X utf8 scripts/parallel_handoff_cli.py --catalog docs/implementation/parallel-lanes/packages/2026-10-07-wave2/manifest.json --package-id SW-REPAIR-02 --input docs/implementation/intake/SW-REPAIR-02/2026-10-08/worker/handoff.json
# 总控隔离快照执行模式：core / extra / extra -k junction / aligned / browser
python -B -X utf8 docs/implementation/reviews/SW-REPAIR-02/guarded_run.py core
```

这些harness脚本固定绑定旧result和已删除临时根，用于解释旧证据，**不是对新HEAD直接再跑的生产工具**。writer把反例移入自己的获批测试、使用自己的新独占根；总控回验另建新commit快照和新intake，禁止覆盖旧基线/日志。原prepare_acceptance.py拒绝既有intake，勿为重跑删它。

测试后先关闭已知runner/浏览器/监听，严格CIM失败即停止清理；inventory前不跟随junction，核两端精确绝对路径、只非递归解除自己的链接节点，然后核文件set/size/SHA/无硬链，逐清单删文件及空目录。生产workspace、StockQA、Lab、旧Phase92和opencode.json全部保留。发生适配错误保留日志，不算产品RED或隐藏失败。

## 交回内容与关闭标准

一次交回新分支/commit、实际前后status/并发变动归属、具体授权范围、版本/接口hash、五组对应RED/GREEN日志、原六项保留回归、真实浏览器截图/loopback次数、公开handoff结果、artifacts及严格隔离清理回执。每个not_run/missing保持真实。

关闭需：12固定边界及新增合理正例通过；原81/11相关功能保持；handoff范围/临时根/hash可以真实接收；唯一writer与外仓边界无冲突。总控核实际新commit和工件，做受影响回验及一次集中独审后签本包范围；**仍不自动关闭G3/F05或放行TH/IN/L03**。无需为每个小步骤建新的审查节点。
