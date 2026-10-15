# Alphabet 新截止日路由候选已生成

2026-10-15。用户已确认 AGENT-RUN-02、AGENT-REF-02、AGENT-EVAL-02 三包均在外包施工。总控避开三个 Lab 及各自候选，不代写、不另派、不根据目录推断交付完成。

本次沿现有 `routing.resolve_route_decision` → `question_sets.compose_from_route` → `route_store_handoff.py` 生成新候选，未手改历史 manifest。新 route 的 previous_decision_id 指向原 owner 当前路由，信息截止为2026-10-13；保留原 package、模块和30题，再显式锁定 routed12-v1 的12个有效题。

11题直接对应，IQS_11 对应实际 OPERATING_01 / score.operating_01，答案仍须使用实际题号；不能改名或把通用锚点混入类型题。原题、旧快照、登记文件和两份 worker 输入锁均不变。这份新候选供总控后续集成，不要求正在施工的 worker 追 latest。

## 证据与局限

候选复用原 owner 路由中四组已核实的 deterministic 历史事实，逐字段保留原期间、来源和判断依据；没有将旧模型候选提升为 verified_facts，没有新建或改签模型回执。所用公开日期均早于实验截止日。**本次没有重新检索，不声称穷尽10月11日至13日的新披露，更不是新金融准确性结果。** classification_confidence 仍为 not_run/null，execution=null。

本机候选目录：`runs/company-agent-owner-2026-10-15-01/route13-candidate-2/`，主要原件如下：

| 原件 | 原字节 SHA256 |
|---|---|
| route.json | ac1b1d25bef888e8d63bc8a64751ab91feb1c82f420207d31c59f829c232edd3 |
| composed/manifest.json | e706ce9fc91a2c30acc0741fd216ecb00aa07ba54becbaafa613ef8940106696 |
| question-projection.json | 3917c99d1c9a46ff5c9ec5a652af9a708f198608016ab9ae13ac46f29e810b1d |
| effective-questions.json | e11beb772668e6c94d24e47299e1fbcf85c67eeacac1f087546298548d8d9cdb |

route decision：`route_afb4bdc99c158423968c2e6c0e3da1dd57ccf2888377abfbcc80bde074410304`。

生成进程PID11892/exit0；真实公开CLI复验PID18400/exit0。错误anchor、旧route与新manifest交叉绑定两个原校验器反例均拒绝。进程无密钥、禁网、SQLite query_only，只写本轮准备目录。这里不新增 helper 审查门。

首次尝试PID27936/exit1：当前根虽然有对应模块artifact，却没有原生路由指定的 package 描述，原API报 module package unavailable。失败原件保留在 route13-candidate-01；第二次显式选择原 owner 已使用的不可变 release 资源树，不另造 package、不改正式指针。compose 没有 root 参数，仅配置其资源 ROOT；没有替换任何权限或校验函数。

闭包 `route13-closure.json` 核实原owner10文件、原work账本、新S1预算库及他人README均与原rawSHA一致。收费模型/搜索0；没有安装新anchor、改policy、创建confirmation/admission。新projection 的 execution_ready=false；新候选通过路由格式/执行校验不等于 owner 批准或金融资格，G3/F05等门保持开放。

## 接续

总控下一步准备这12个实际field、DeepSeek及新预算的独立实验owner配置与明确切换/恢复方案。当前每workspace只有一个生效policy，不能静默覆盖旧唯一policy后声称旧25项恢复权限不受影响。新路由安装也须保留原anchor历史并核清其影响。随后走真实公开预览、原生确认及QA admission；不以旧IQS01批准或S0预算探针代替。三包交付后在同一大节点集中集成，不改变它们冻结的开发输入。
