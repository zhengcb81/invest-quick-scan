# QA-C06-02 一次集中独立审查

审查agent：`/root/qa_c06_02_acceptance_review`；源码只读，未运行外仓测试、写仓、读取key或收费。起点为StockQA结果7e71b2c、交接a12bc29和原施工卡。以下分清独审静态判断与总控动态复证，不宣称agent重新跑1037。

| 独审定位 | 判断 | 总控动态结果 |
|---|---|---|
| `quick_scan_c06_authority.py:125` `_crosscheck_manifest` | 题集/prompt双hash检查漏逐题metadata，比已有bind_question_context少约束 | 三definition/semantic/template例RED；错误template真实CLI31stub发送，IQS公共CLI随后拒收 |
| `quick_scan_observation_context.py:255` / `:397` | stored work/checkpoint未核run_id/scan_id；runner`:1560`生成另一个run/固定scan | FOREIGN_RUN/SCAN封存RED；正常31与反例31实际DB无匹配run/scan |
| `quick_scan_c06_authority.py:233` / `quick_scan_observation_context.py:283` | 两入口普通json.loads，既有外层重复键用例不覆盖 | authority重复schema_version和正文重复score均RED，最后值被接受 |
| `quick_scan_work_store.py:3258` / `:3281`，outbox`:251` | supersede校compact binding，未核完整body/context/原started_at | 改claim与started_at并全层重签可落新head，RED；原侧表仍原输入 |
| `_apply_v6_migration` 与ACK/终态路径 | 有单事务和旧head保护，未见正常路径确定静态错误 | 真实v5有旧sealed/ACK迁移和migration中途抛错全rollback两GREEN；相关原用例GREEN |
| `test_qa_c06_02_e2e.py:238` / `:271` | 原三个所谓CLI E2E同进程调用main；不证明真正重启 | 总控已补真实子进程cold31、warm/seal0；不作为代码缺陷计数 |

审查收敛为四代码组、一交接组，见同批整改卡。原能力保留，不为小步骤加门。总控环境缺SQL/过严网络guard/async超时单列controller问题，未让agent静态疑虑冒充动态失败，也未因迁移GREEN宣称整包通过。
