# C06 组件测试与隔离集成环境

**2026-10-10 当前主线接续（checkpoint08；下面旧“当前”记录均为历史）：** 两外包集中验收保留changes_requested，R1尚未派发；总控只写runs/c15a私有副本。71候选/13变化/12终态批次已固定到producer-checkpoint-08.json，原guard abc0128…不变。固定StockQA→StockWiki原生OS同意读取已实际实现，1.1明确fresh_registration/current_permissions，原1.0不变；原Q13 schema16仅增加不可变action控制表，与原work/run refs/owner binding同事务，重放保持原work。最新受影响五文件143P/21.14s（45356/exit0），权限22P/2.62s（43764/exit0），真正三组件公开CLI E2E1P/125.50s（23892/exit0）分别记录，不相加为准确率。E2E明确合成同意/身份，以实际serializer、authority3/context2精确1题登记原队列；原owner DB不变，attempt/预算attempt0，策略变化拒绝，队列变化后只读当前权限可重放。存储原语仍permission_authenticated=false，尚无公共accepted admission服务/主执行器消费，没有实际人类确认或收费调用，也未整C06独审/源发布。

**唯一下一工程动作：** 在原Phase113步骤4，把这些现有组件接成可信公共admission服务：从部署固定的原producer bundle读取/验证完整manifest、身份、authority3/context2，逐项与原确认的完整SubjectRef/field/question/generation/provider/model/route核对；不能公开caller specifications/confirmed/registered布尔值。新动作完整重核、已登记动作按原耐久记录重核当前权限，Q13提交成功后才accepted；原主runner只消费该已确认精确范围，发送仍经Q09。复用与result_ready只接原引用/续传、0新LLM，不确定发送仍保留原停机/核对语义。完成其余原C06操作后整节点一次集中审查、源发布与strict自有清理；不加helper门，不跑全池、不写Lab整改或生产库/名单。c15a及真实身份克隆real-owner-01仍在用。C06/W15/G3/F05/L03/B01/事实/UI/TH-IN/全池门保持开放。四份PWF/接手及三份W15说明的获准文档可正常Git到既有origin，源码/真实golden/数据库/新跨仓快照未扩入导出范围；实际Git只按终态回执记，不盲跑旧publisher。


这是原 C06 大节点的测试接线，不增加审查门。代码仍为 `runs/c15a` 私有候选，尚未在三个生产源仓发布。

普通 QA/StockWiki 单仓 pytest 不要求导入对方产品。跨仓集成测试明确 opt-in：`IQS_C06_RUN_INTEGRATION=1`，且 `IQS_C06_OWN` 指向本次自有运行根，包含 `qa/`、`sw/`、`iqs/` 和隔离 `guard/`。固定 CLI 子进程分别只加载自己的组件；IQS 纯契约校验不读取数据库或访问网络。单仓未启用集成时，集成模块明确 skipped；这不计测试通过，更不能签收 C06。启用后环境错误须报错，不能默默跳过。QA 纯组件测试若缺 IQS 纯契约依赖也明确 skipped。

总控必需集成批次通过 `run_c06_producer_checks.py <新唯一标签> <QA相对测试路径…>` 运行，设置实际三个组件路径、临时目录和同一 socket/SQLite 守卫。选取 StockWiki 测试可用 `../sw/tests/…`。每批实际 PID、child exit、源 SHA、JUnit、日志均进入 intake；不能将控制器 exit0 误认为 pytest 通过。必需集成批次须真实执行、skipped=0；不能用普通 collection 的跳过来关闭门。

首次空观察库设置由 owner 公开 CLI 执行：

```text
python -B -X utf8 -m stockwiki.quick_scan_subject_dispatch_cli --operation initialize --root <绝对workspace路径> --expected-schema-version 0
```

这是设置动作，不是日常 read/refresh 的隐式迁移。它只创建本命名空间 schema3，零模型/搜索请求；重复已初始化库使用 expected-schema-version 3 保持原库字节和 store_id。已存在 schema1/2 明确要求备份后的受控升级，本入口不升级；未来版本、坏库、现存未标版本库、预期版本不符均拒绝。日常事前登记必须已有 schema3，否则派发前拒绝，不替用户自动升级。旧 schema2 reader/writer边界保持。

`producer-init-green` 的 7 项实际测试包括6项首次设置/拒绝反例和1项真实主程序的部分扫描接续。`producer-portable-green` 的75项是真正集成执行、无跳过、零API；`normal-collection-03.json` 仅记录正常单仓 collection，executed_tests=0。首轮collection因移除隔离守卫必需的OWN变量被控制器拒绝，次轮是控制器误以为collect-only会输出skip总数；日志原件保留。改用独立opt-in开关并显式读取-rs的模块skip记录，原守卫不变。两类证据不得混用。

仍需原 C06 全节点集中审查、真实 owner golden/生成记录及源发布；首次设置不代表统一安装器、ReleaseSet生命周期或200家扫描已交付。


## 2026-10-10 接续补记

新增preview纯契约25P、原账本只读检查8P为实际独立批次；不合并为金融准确率。新适配器仍待测试，原guard不改，source执行前后SHA稳定，失败原件保留。7文档发布已有具体人类授权，结果以实际终态为准。


## checkpoint06实际接续

**2026-10-10 当前接续（checkpoint06，覆盖下方历史）：** 精确7份第一方文档已正常提交推送a0d283de665f91740190b2371b4722a2af25e557，远端master相同；未导出跨仓源码/真实golden/数据库。独占runs/c15a的StockWiki公共刷新预览已走实际OS账户、当前主体/成员/模块锚、冻结Query2 capture和原Q09/Q13只读账本，并保存不可变owner控制工件。当前63份私有候选，未集中审查/源码发布。最新35纯契约＋1公共CLI为同次36P；受影响账本/工件/公共CLI另批19P。此前128项为126P/2F，坏JSON已拒绝但错误边界未归一，修复后19P；不能拼成128全绿或金融准确率。result_ready只需导入续传时新增HTTP/费用为0，不因模型额度耗尽阻断。动态名单/模块须owner显式current_owner_members/current_manifest配置，身份仍由真实serializer独立验证，不以名称join。全部测试终态、guard原字节不变、0API/生产库/名单写。唯一下一工程动作是已认证owner对精确预览的独立确认、耐久幂等交给原Q13并在原Q09发送时扣账，再其余原C06操作；完成整个节点后一次集中审查，不增小节点审查。实际用户确认/收费提交尚未发生，C06/W15/G3/F05/L03/B01/事实/UI/TH-IN/全池门保持开放。c15a与real-owner-01仍用不清；两个内容包未派发。



## checkpoint07实际接续

**2026-10-10 当前唯一接续（checkpoint07，以下均为历史）：** 独占runs/c15a已有原生owner交互确认入口与不可变幂等工件，公共CLI会拒绝管道/自报确认；确认前后重核精确预览、当前主体/成员/路由/政策/原预算，scope变动要求新预览。另有固定owner只读同意检查入口与原Q13单事务批量登记原语（复用原表/算法、不另建队列）。最新同批实际36P/74.04s、子进程7660/exit0/source_changed为空；保留之前30P/6F的计数fixture表名错误原件。原语本身permission_authenticated=false，公共确认仍handoff_pending/registered_with_executor=false；真实owner读桥正例使用明确合成的同意工件，实际人类确认/收费提交/公开Q13接线尚未发生。67私有候选checkpoint07已固定，未集中审查/源码发布，0API/生产库/名单写，guard不变。唯一下一工程动作：固定QA OS桥读取owner原件，绑定完整authority3/context2及精确question/subject范围，再耐久幂等登记/公开重放/原主执行器消费，Q09仍在实际发送前扣账；之后其余原C06操作并同节点一次集中审查，不增helper审查。7份获明确许可的第一方文档已实际推送a0d283de665f91740190b2371b4722a2af25e557，远端一致；本次后续同7文档的实际Git结果按documentation-publication-02.json核对，代码/数据库/golden不在该导出范围。C06/W15/G3/F05/L03/B01/事实/UI/TH-IN/全池门仍开放，活根不清、内容包未派发、目标active。

