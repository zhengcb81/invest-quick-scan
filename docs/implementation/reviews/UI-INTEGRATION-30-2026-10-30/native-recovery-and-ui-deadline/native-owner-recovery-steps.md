# 两个真实失败问题的原owner接续步骤（仅供总控执行）

本目录的 `resolution-intent-IQS_22.json` / `resolution-intent-IQS_23.json` 是**原SDK只读derive入口的intent**，不是批准书，也不是可以直接投递StockWiki的完整request。每题的schema诊断只保存874/841字符与800上限、parser完整及原response/receipt哈希，不含回答正文。所有response_sha已与原durable receipt只读核对。

先确认执行部署已加载最终修复、没有用重启中断在途付费进程；不修改旧failed状态、旧租约、旧授权或旧成本。下面命令均是现有公开CLI；本reviewer没有执行preview/install/confirm/apply或真实派发。

1. 在StockQA原代码根，分别运行原只读推导，保留stdout完整JSON到本次总控新目录：

```powershell
C:/Miniconda/python.exe -B -X utf8 -m src.utils.quick_scan_work_decision_inspect_cli --ledger 'C:/Users/郑曾波/Projects/invest-quick-scan/runs/u25-live/work.sqlite' --policy 'C:/Users/郑曾波/Projects/invest-quick-scan/runs/u25-live/budget-policy.json' --intent 'C:/Users/郑曾波/Projects/invest-quick-scan/runs/ui-integration-live30-2026-10-30/ui-review/microsoft-security-diagnostic/resolution-intent-IQS_22.json'
```

IQS23只替换intent文件。输出的 `request` 是由原Q13/physical/subject-dispatch持久事实导出的完整decision_request，不能手拼physical、lease或receipt。必须API_requests=database_writes=0。

2. 组装原StockWiki外层 `stockwiki.work_decision_request/1.0.0`，四字段严格为 `protocol, consumer_id, decision_request, permission_request`。consumer_id用原 `invest-quick-scan`；decision_request只取刚才原SDK输出。permission_request复用原当前owner/同scope refresh请求的合法生成方法：subject_refs必须只等于原dispatch subject_ref；field_ids必须只含该题原dispatch.field_id（不是题号猜值，也不能带本scope另外两题）；source_query的cutoff必须原样等于dispatch.information_cutoff，其余原query/capture/当前route字段按原builder/schema保留。不要拿更晚cutoff或另security的快照替换。原OwnerService会独立读owner receipt和当前授权再核验，并不信任该外层本身。

3. 在StockWiki原代码根，用原work-decision preview：

```powershell
C:/Miniconda/python.exe -B -X utf8 -m stockwiki.quick_scan_refresh_owner_cli --root 'C:/Users/郑曾波/Projects/invest-quick-scan/runs/r25-live/owner-workspace' --iqs-code-root 'C:/Users/郑曾波/Projects/invest-quick-scan' --iqs-release-root 'C:/Users/郑曾波/Projects/invest-quick-scan' --work-decision-request 'ROOT_OWN_NEW_DIRECTORY/resolution-owner-request.json'
```

原preview及record必须真实ready/当前有效，保留其preview_id、原record_sha256。不要复制旧confirmation。

4. 复用既有原固定install/CAS/finally流程，仅向owner workspace的 `config/quick_scan_work_delegation_install.json` 暂存精确七字段：protocol=`stockwiki.work_delegation_install/1.0.0`、workspace_root、原preview_id、原preview_record_sha256、既有已授权agent三字段profile（不改principal）、真实会话authorization_reference、native允许的真实expires_at。先保存原文件存在性/字节，最后只在仍为本次字节时恢复，保留原immutable grant。执行：

```powershell
C:/Miniconda/python.exe -B -X utf8 -m stockwiki.quick_scan_refresh_owner_cli --root OWNER_WORKSPACE --iqs-code-root IQS_ROOT --iqs-release-root IQS_ROOT --install-work-delegation
C:/Miniconda/python.exe -B -X utf8 -m stockwiki.quick_scan_refresh_owner_cli --root OWNER_WORKSPACE --iqs-code-root IQS_ROOT --iqs-release-root IQS_ROOT --confirm-work-decision-delegated REAL_PREVIEW_ID --delegation-id REAL_GRANT_ID --idempotency-key EXACT_ACTION_KEY
```

需保留原确认回执。该动作不是普通refresh的dg1 grant，不能用 `--install-delegation` / `--confirm-delegated` 替代。有效期自然过期就重新原preview/授权，不改时间。

5. 由原QA接口apply真实确认（零模型调用）：

```powershell
C:/Miniconda/python.exe -B -X utf8 -m src.utils.quick_scan_work_decision_apply_cli --ledger 'C:/Users/郑曾波/Projects/invest-quick-scan/runs/u25-live/work.sqlite' --policy 'C:/Users/郑曾波/Projects/invest-quick-scan/runs/u25-live/budget-policy.json' --owner-code-root 'C:/Users/郑曾波/Projects/StockWiki' --owner-workspace 'C:/Users/郑曾波/Projects/invest-quick-scan/runs/r25-live/owner-workspace' --iqs-code-root 'C:/Users/郑曾波/Projects/invest-quick-scan' --iqs-release-root 'C:/Users/郑曾波/Projects/invest-quick-scan' --consumer-id invest-quick-scan --confirmation-id REAL_WORK_CONFIRMATION
```

原work仍failed、原attempt/receipt/pack/成本/旧updated_at应不变；仅新原owner decision/event append。保留新的真实resolution decision_id，不写SQL或伪造admission。

6. 原resolution recorded后，再推导一个新的**retry intent**：kind=`retry_decision`、同work_item_id、独立稳定idempotency_key、purpose=`retry_unusable_answer`、retry_after_seconds=0、comparison_controls=null。使用同原 `--intent` 得到含source_resolution_id和target_generation=N+1的真实request。再次执行步骤2–5的独立preview/grant/confirm/apply，不能复用resolution grant，也不能把comparison或checkpoint purpose混入。该步仍API0，不自行创建新work或增加旧任务请求上限。

7. 原retry recorded后，通过既有 `controlled-recovery-subset-contract.md` 的原UI/owner生产接线，为**精确source work_id +真实retry decision_id**选择新的合法controlled scope。保留原身份、问题、日期/上下文，目标严格N+1，原失败历史与累计预算保留。必要的原policy/route dialect按该生产接口要求办理新的明确授权，不能直接改全局policy/绕过在途scope授权。新原准入完成后才在UI派发纠错重问；强调summary<=800、coverage.reason<=350、未知保持unknown，不剪裁旧答文来补CP。新HTTP进入原累计账本；源failed任务及retained诊断继续保留。

上述两题失败是模型schema长度不合规；严格validator无误。另一个已修复的软件问题是trusted runner已把已收答成员封为failed后，owner原resolution接口不能接纳这类精确终态。修复仅补这个原审计决议入口，不承诺缓存诊断可零HTTP重放。真实owner最终confirm/apply与模型重问、入库仍由总控执行。
