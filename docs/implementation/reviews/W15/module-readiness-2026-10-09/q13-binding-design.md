# W15 → Q13 持久执行接线

2026-10-09；同一次W15整包实施设计，不是第二个逐helper审查门。用户已全授权。只读结构agent `/root/w15_execution_design`确认近期Q13未入CodeGraph，以真实已知源码查链；agent未写入/测试/调用API。以下是设计发现摘要，非运行验收或原始金融golden。

## 已核实际缺口

StockQA `main_with_llm.py` → `LLMRunner._run_single_mode`加载并双向绑定问卷，再调用`plan_manifest_dispatch`。当前仅传generation/router映射到`QuickScanWorkLifecycle`，未消费action。`hydrate_question`与`before_question`均会`create_or_attach`；只打印外部refresh计划仍可能水合旧checkpoint。generation在UNIQUE中意味着G1 uncertain和G2可同时存在，只读planner的未知发送检查不能防止竞态。`find_work_items`上限1000不能作为事务未决扫描的完整性保证。

## 接线顺序与信任

固定owner配置执行StockWiki公开CLI：current（include raw bundle）→StockQA从自身WorkStore自产work projection→owner refresh→再次核current。精确对照expected_decision_id、anchor_version、两raw SHA、subject/perimeter/revision、scope、module locks、provider/model/cutoff；不得接受任意`--refresh-plan` JSON当执行授权。外来protocol/hash/refresh_id自洽不认证来源。实际问卷文件还需与owner原bytes对应；expected ID来自owner current而非输入payload。

完整逐题action须在QAEngine水合前生效：reuse只引用StockWiki原Observation，不能生成新manifest的旧answer/checkpoint/新封包；dispatch_new_*使用owner目标generation再经原lease/预算/HTTP；deferred_unknown/manual_refresh_required/scope_unbound不收费。resume按原work ID分pending（未发可续）、leased、uncertain（只对账）、result_ready（原context补封/送达）处理，不能把当前新prompt重绑定旧项。segment从owner scope扩展原manifest_scope_bindings，不能猜ticker。

事务内需再次扫描同subject/question/scope的全部相关generations并检查未决发送，绑定稳定刷新请求与目标generation，再创建/领取work。refresh_id包含now，只可审计，不作唯一幂等键；使用稳定request identity与source/target generation。数据库正式加法迁移、备份/恢复能力必须配套，不私加未登记表。

原`seal_result_delivery`用原frozen authority/context/实际attempt时间；ACK仍逐item精确校验且target事先绑定。部分ACK仅恢复未确认项，已checkpoint不得再问模型。durable accepted ACK却owner缺Observation应报告target/store不一致，不按missing重新收费。

## 集中验证

同一W15整包集中包：24核心+2新题只有2新work/收费边界请求，旧Observation/model/time/score/hash不改；相同prompt TTL过期G1→G2且重启不变G3；旧uncertain在题义/模型/截止日变化后零新HTTP；两进程同时刷新只有一lease/send且planner后出现的uncertain也阻断；合法重封manifest/伪plan/current切换在预留预算前拒；部分ACK、seal_only、送达不明只恢复原包。真实厂商/金融准确性另门，不用合成结果闭门。

已查测试路径：tests/unit/test_qa_net01_question_manifest.py、tests/integration/test_qa_net01_cli_e2e.py、tests/integration/test_qa_c06_02_subprocess_cli.py、tests/unit/test_quick_scan_work_store.py、tests/unit/test_quick_scan_c06_complete_seal.py、tests/unit/test_quick_scan_result_outbox.py。新适配层须可选；无owner binding时保持现有Q13接口与历史回执。整包完毕再一次独审/精确源码发布，不因一段GREEN宣布W15/G3完成。
