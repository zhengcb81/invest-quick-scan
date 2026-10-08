# QA-C06-02 第二轮集中独审

审查者：已有独立agent `/root/qa_c06_02_acceptance_review`。只读、未跑测试、未改仓库；一次集中审查。本文件记录其结论，动态结果见[验收](acceptance.md)，不能把静态预测当运行证据。

代码结果 `acb7dbfae0e6a45221924e2d1d5742a4999f4c9d`，接收 HEAD `361a721df382c468640b27bbafc484e31c8aa321`。

| 原组 | 已落地 | 同链边界与定位 |
|---|---|---|
| 1 题义/发布绑定 | loader接入共享check_context_matches_manifest，原definition/semantic/template校验已接入 | context.py:221–224只比entity/scope，未比security_id/segment_id。改IQS_22为SEC_FOREIGN并重签context，可能在HTTP之后才拒绝。 |
| 2 run/scan | work_store.py:2737–2762记录冻结标签，seal.py:95–108检查映射 | work_store.py:3156–3225完整write重建缺run检查，直接prepare可能绕过既有c06_run_scan_unbound。 |
| 3 严格JSON | 重复键hook/NaN/Infinity拒绝接入authority和正文 | outbox.py:94–98未拒1e400经float溢出为inf；context.py:336可能返回含inf正文。后续canonical仍拒，未预测错误head。 |
| 4 full持久绑定 | prepare/supersede均重建已有完整context/body/original started_at | work_store.py:3196–3201遇缺侧表直接return；新完整Observation可能回退compact规则。应拒绝新完整write，保留历史读取。 |

真实CLI已增加独立cold/warm/seal子进程，补首轮同进程main()缺口。迁移、ACK幂等、旧head ACK、send_uncertain正常保护静态未发现新的错误。真实StockWiki、owner golden、G3/F05仍not_run；共享TEMP未证归属是交接限制，不能按编号删除。

审查已收敛结束；四组由总控在同批隔离复验，不加小节点审查。
