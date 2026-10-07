# Q10 跨仓接口集中整改：完整观察与不可变扫描ID

这是Phase91从已冻结源码实跑得到的下一批整改输入，不是新小节点审查门、写入授权或G3签收。StockQA已有用户全仓修改授权，实施者每批报备精确路径；StockWiki仍只读，不为接收残缺包放宽消费者校验。当前QA源码84e24ef、交接09f68a6，SW04dfc519。

## 真实反例与保留边界

公开StockQA CLI → 真checkpoint/outbox/sealed package → 公开StockWiki `observation-import`：首模型合成额度拒绝、备用模型合成成功；网络只在HTTP边界替换，其他代码和临时SQLite真实执行。StockWiki返回`rejected/observation_missing_field`，不是import error、文件错误或无匹配公司。producer内部`ready`不能当consumer可导入。

完整观察缺少schema_version、field_id、question_version、template_version、method_id、cohort、information_cutoff、run_id、observed_at；execution还缺消费者要求的started_at。实际全部要求以既有C06 Observation及execution schema和消费者验证器为准，不能仅补这次首个错误字段。同企业/同题/同scope的两次独立真实store attempt产生相同observation_id，无法保留新时间/新模型的不可变历史；不同挂牌/分部也不能仅以scope类别区分。

最终六检查3 RED /3 GREEN/4.56s。两个fixture修正（错误回执走stderr；输入拒绝CLI exit2）前的4fail/2pass日志保留，不归成四个产品问题。红项为完整导入、可比元数据、独立扫描ID；绿项为拒绝ACK幂等且观察0、包篡改exit2、warm新输出HTTP0/包和attempt不变。全部明确synthetic，不是StockWiki真实身份/关系golden，不关闭X09、G3、F05。

归档`consumer-rejected-ack.json`来自导入正向失败case，`replayed-rejected-ack.json`来自另一重放case的末次回执，**两文件不是重放配对**。首次重放回执未另存；同ACK结论只由该case内部first/again精确断言、GREEN原始日志和被测源码hash支持，不以两个不同根/包的归档文件作配对证明。

## 完整修复要求

1. 从IQS已冻结的题定义/发布、问卷/ScanRecipe与明确运行上下文获得观察元数据；从实际checkpoint/HTTP attempt获得答案、provider/model/request/attempt/search/prompt与时间。不按qid拼field_id、不按机器当前时间猜信息日期、不用requested model覆盖actual、不以空cohort/default method伪装已齐。
2. 若现有authority1.0.0确实不承载足够信息，设计可版本协商的扩展输入和模板，保持旧文件可读取。旧输入缺信息须durable block，不能输出标准C06能力声明的残缺ready包。未知/不支持的新版本失败关闭。输入校验必须与发布schema一致。
3. 在checkpoint之前或同时耐久保存完整、hash绑定的上下文，接续/后补封包从原始冻结输入恢复，不能读取后来变化的题库悄悄改口径。验证实际题面/semantic/definition/module/scope/identity/subject修订一致；证券/分部按真实scope_id绑定。
4. observation_id须依据不可变观察身份及实际执行上下文确定，同次重放相同、不同执行/时间/模型/subject/scope不碰撞。item/package hash沿既有内容寻址规则重算；不能只随机换ID来绕过执行键或消费者冲突检查。
5. 历史已sealed的残缺包只读保留，不能回写payload/hash、删除执行账本或再问LLM来修数据。明确设计后补完整包的版本/替代关系和审计链；如果现有unique-work outbox不能表达，应按store owner版本化迁移，保留旧ACK和旧包，区分旧包拒绝与新包交付，恢复收费必须仍关闭。不得把清空库当向后兼容。
6. 使用StockWiki公开导入入口接受新完整包；丢ACK后重放得同ACK/单观察，再由StockQA公开接收入口落定。保留低分、unknown/insufficient/N/A、实际模型/信息日期/观察时点，来源和身份不足不能直接计入白名单。消费者无需放宽。

## 实施包与集中测试

实施前从当前工作树核实并报备StockQA最小允许路径：预计C06 adapter/authority与schema、delivery seal/outbox/work store、runner的冻结上下文接线、对应unit/integration与本包docs。**这是预计范围，不指示盲改全部文件**；取得确切输入映射后再定精确名单，不改StockWiki、IQS中央schema或其他writer文件。

同一批TDD测试须覆盖：公开完整导入与ACK丢失重放；缺各必填上下文/错误hash/错题/错scope持久阻断且LLM0；同attempt重放ID稳定、不同attempt/model/subject/security/segment不碰撞；跨两次扫描信息日期不漂移；旧1.0authority/旧sealed包/旧账本仍可读、升级后补答案不再收费、旧ACK不能落定替代包；unknown/null和低分没有fallback；轻资产哨兵不长期保存原始HTTP/网页/密钥。

定向单元+双真实公开入口离线集成后，一次仓现有全量门与同批独立审查；不要给每个helper追加review。实际owner真实数据联调与执行侧/StockWiki配套恢复仍是G3未完成部分，离线合成通过不能替代。

## 可复现入口

IQS `cross_owner_cases.py`和`cross_owner_guarded.py`在同目录。从现有QA `remediation-export-manifest.json`和SW `export-manifest.json`用各自已交付`export_runtime.py`导出到一个新的IQS/runs/cross-owner-*根，子目录分别为qa-net01-intake-runtime与sw-ready01-intake-runtime。设置IQS_CROSS_OWNER_ROOT后执行guarded脚本。当前精确快照预期3 RED/3 GREEN，不能为CI通过而改期待值。修复后单独登记新源码manifest、保留旧RED。

所有真实仓和真实库只读；凭据环境和live开关移除，Python guard禁止根外写、HTTP/DNS、registry及子进程。Windows asyncio例外只限stdlib self-pipe，不开放普通localhost。导出Git发生在guard安装前，仅只读精确白名单；此保护不是任意原生进程的OS沙箱。runtime只管理单个manifest根，结束后严格核CIM进程、SHA/owner/run_id/无reparse，再逐文件清理；扫描失败即停止，不能按mtime清共享TEMP。
