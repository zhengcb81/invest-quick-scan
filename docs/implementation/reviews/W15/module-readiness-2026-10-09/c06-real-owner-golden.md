# C06 真实 owner 身份与查询 golden

**2026-10-10 当前主线接续（checkpoint08；下面旧“当前”记录均为历史）：** 两外包集中验收保留changes_requested，R1尚未派发；总控只写runs/c15a私有副本。71候选/13变化/12终态批次已固定到producer-checkpoint-08.json，原guard abc0128…不变。固定StockQA→StockWiki原生OS同意读取已实际实现，1.1明确fresh_registration/current_permissions，原1.0不变；原Q13 schema16仅增加不可变action控制表，与原work/run refs/owner binding同事务，重放保持原work。最新受影响五文件143P/21.14s（45356/exit0），权限22P/2.62s（43764/exit0），真正三组件公开CLI E2E1P/125.50s（23892/exit0）分别记录，不相加为准确率。E2E明确合成同意/身份，以实际serializer、authority3/context2精确1题登记原队列；原owner DB不变，attempt/预算attempt0，策略变化拒绝，队列变化后只读当前权限可重放。存储原语仍permission_authenticated=false，尚无公共accepted admission服务/主执行器消费，没有实际人类确认或收费调用，也未整C06独审/源发布。

**唯一下一工程动作：** 在原Phase113步骤4，把这些现有组件接成可信公共admission服务：从部署固定的原producer bundle读取/验证完整manifest、身份、authority3/context2，逐项与原确认的完整SubjectRef/field/question/generation/provider/model/route核对；不能公开caller specifications/confirmed/registered布尔值。新动作完整重核、已登记动作按原耐久记录重核当前权限，Q13提交成功后才accepted；原主runner只消费该已确认精确范围，发送仍经Q09。复用与result_ready只接原引用/续传、0新LLM，不确定发送仍保留原停机/核对语义。完成其余原C06操作后整节点一次集中审查、源发布与strict自有清理；不加helper门，不跑全池、不写Lab整改或生产库/名单。c15a及真实身份克隆real-owner-01仍在用。C06/W15/G3/F05/L03/B01/事实/UI/TH-IN/全池门保持开放。四份PWF/接手及三份W15说明的获准文档可正常Git到既有origin，源码/真实golden/数据库/新跨仓快照未扩入导出范围；实际Git只按终态回执记，不盲跑旧publisher。


2026-10-10。当前为私有候选软件与真实现有身份记录的交叉验证，未发布生产源，未关闭完整 C06。

四份现有 StockWiki 身份库从 `a5a97d6efbf5f0ee79122a1ec375def388700690` 对应工作区只读复制，源和克隆逐份字节一致；明确拒有 WAL/shm/journal 的不稳定文件。来源见 `intake/W15/c06-query-2026-10-09/real-owner-inputs-01.json`。当前唯一 analysis subject 从真实主档读取，没有按名称猜选发行人，没有创建主体、verified receipt、观察或财务回答。跨文件仅是顺序读取及前后字节校验，不冒充跨库原子快照。

StockWiki 的实际身份导出 parser/handler 经薄公开入口 `stockwiki.identity_g2b_cli` 复用，避免总CLI在身份导出前加载无关LLM配置。旧总CLI保留；首轮失败终态与原日志保留。实际 owner binding 使用既有 `stockwiki.quick_scan_routes_cli quick-scan-route-binding`；新能力入口公开其配置下的独立 store_id，用来验证实际查询结果，不能从查询结果本身抄期望 owner。

生成及校验顺序如下，具体绝对路径、参数、时间、PID和原始输出SHA都记录在 `real-owner-golden-02/generation.json` 的6条 command，不把脚本模板当已执行命令：

```text
python -m stockwiki.identity_g2b_cli --root <owned-clone> identity-export-g2b --entity-id <实际primary issuer> --as-of <实际UTC>
python <IQS>/scripts/identity_contract_cli.py --input <identity-export.stdout.json> --schema-version 2.2.0
python -m stockwiki.quick_scan_routes_cli --root <owned-clone> quick-scan-route-binding --subject-key <实际subject key> --iqs-code-root <IQS>
python -m stockwiki.quick_scan_query_v2_cli --root <owned-clone> --iqs-code-root <IQS> --capabilities
python -m stockwiki.quick_scan_query_v2_cli --root <owned-clone> --iqs-code-root <IQS> --request <query-request.json>
python <IQS>/scripts/query_contract_cli.py --operation response --input <query-validation-input.json>
```

身份 package2.2.0 经 IQS CLI1.1.0 返回 valid。Query2.0.0 经公开纯CLI返回 validated，但实际 result.status 是 **unavailable**：源没有 observation namespace，scores_available/facts_available 都为 false。正确身份可以展示，评分与事实不能展示成有效结果；没有借初始化空库、合成答案或重写旧记录制造“真实正例”。这不证明金融准确性、模型横向比较、当前白名单资格或200家公司扫描完成。

`real-owner-negatives-01/checks-final.json` 收齐14条真实 CLI终态：1次跨进程重启保持原捕获，13个拒绝反例覆盖错发行人、挂牌ticker/来源绑定冲突、截断/重复JSON键、错主体revision/范围摘要、独立owner/水位错配、模型筛选改变、未知snapshot以及过期缓存禁止live替换。主体/水位错误的副本重新封摘要后仍被拒绝，不只测试旧hash。原实际 golden 不变。模型项只验证 cache query绑定，源没有真实模型答案，不能宣称已比较模型回答。过期项是自有缓存元数据故障注入；finally恢复原缓存字节，不声称等待两小时。

负例控制器在13条已完成后调用不存在的序列化helper失败，恢复缓存后只补尚未执行的过期项，未重跑已绿13条。原错误与终态原件保留。所有源DB/克隆原四库字节保持，0API、0费用、0公司文档采集。当前 c15a/real-owner-01仍服务同一C06大节点，收尾后按原隔离清理协议清除，不删除外仓数据。

下一步继续原C06剩余公开操作和明确授权的刷新预览/确认链，之后同一大节点集中审查与源发布。当前capabilities只声明 get_profiles，full_C06_milestone_accepted/facts_producer_ready 都为 false；TH/IN、G3/F05/L03/B01和全池门仍按原前置。Git跨仓快照导出的具体授权问题还未获答，旧34份publisher已过时，不盲跑。


## 2026-10-10 接续补记

刷新预览新增实施没有改写任何真实golden/四库/原capture。当前真实正例仍仅身份与真实缺覆盖；不能借25项合成预览测试或8项账本测试变成真实回答正例。本文已获明确文档发布授权，不包含真实golden原件/数据库。


## checkpoint06实际接续

**2026-10-10 当前接续（checkpoint06，覆盖下方历史）：** 精确7份第一方文档已正常提交推送a0d283de665f91740190b2371b4722a2af25e557，远端master相同；未导出跨仓源码/真实golden/数据库。独占runs/c15a的StockWiki公共刷新预览已走实际OS账户、当前主体/成员/模块锚、冻结Query2 capture和原Q09/Q13只读账本，并保存不可变owner控制工件。当前63份私有候选，未集中审查/源码发布。最新35纯契约＋1公共CLI为同次36P；受影响账本/工件/公共CLI另批19P。此前128项为126P/2F，坏JSON已拒绝但错误边界未归一，修复后19P；不能拼成128全绿或金融准确率。result_ready只需导入续传时新增HTTP/费用为0，不因模型额度耗尽阻断。动态名单/模块须owner显式current_owner_members/current_manifest配置，身份仍由真实serializer独立验证，不以名称join。全部测试终态、guard原字节不变、0API/生产库/名单写。唯一下一工程动作是已认证owner对精确预览的独立确认、耐久幂等交给原Q13并在原Q09发送时扣账，再其余原C06操作；完成整个节点后一次集中审查，不增小节点审查。实际用户确认/收费提交尚未发生，C06/W15/G3/F05/L03/B01/事实/UI/TH-IN/全池门保持开放。c15a与real-owner-01仍用不清；两个内容包未派发。



## checkpoint07实际接续

**2026-10-10 当前唯一接续（checkpoint07，以下均为历史）：** 独占runs/c15a已有原生owner交互确认入口与不可变幂等工件，公共CLI会拒绝管道/自报确认；确认前后重核精确预览、当前主体/成员/路由/政策/原预算，scope变动要求新预览。另有固定owner只读同意检查入口与原Q13单事务批量登记原语（复用原表/算法、不另建队列）。最新同批实际36P/74.04s、子进程7660/exit0/source_changed为空；保留之前30P/6F的计数fixture表名错误原件。原语本身permission_authenticated=false，公共确认仍handoff_pending/registered_with_executor=false；真实owner读桥正例使用明确合成的同意工件，实际人类确认/收费提交/公开Q13接线尚未发生。67私有候选checkpoint07已固定，未集中审查/源码发布，0API/生产库/名单写，guard不变。唯一下一工程动作：固定QA OS桥读取owner原件，绑定完整authority3/context2及精确question/subject范围，再耐久幂等登记/公开重放/原主执行器消费，Q09仍在实际发送前扣账；之后其余原C06操作并同节点一次集中审查，不增helper审查。7份获明确许可的第一方文档已实际推送a0d283de665f91740190b2371b4722a2af25e557，远端一致；本次后续同7文档的实际Git结果按documentation-publication-02.json核对，代码/数据库/golden不在该导出范围。C06/W15/G3/F05/L03/B01/事实/UI/TH-IN/全池门仍开放，活根不清、内容包未派发、目标active。

