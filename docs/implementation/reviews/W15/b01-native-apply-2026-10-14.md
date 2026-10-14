# 原 B01 首条原生确认已消费，真实账本升级19

当前日期：2026-10-14（Europe/London）。本记录接续85c3f69的终端交接，**首条操作已完成，不再等待首次确认，不再执行旧确认helper或重复apply**。

## 实际结果

用户在真实终端完成确认，operator-handoff/20261014T215129_318244Z的confirm进程21008 exit0，stdout SHA与收据一致。原namespace的不可变rc1记录存在，method=native_owner_terminal，confirmed_at=2026-10-14T21:53:08.909104Z；preview、request SHA、当前policy和原生主体由原公开authority重新核验。没有根据聊天文字构造confirmation、注入confirmer或代填挑战。

StockQA公开`src.utils.quick_scan_work_decision_apply_cli`实际进程25624正常exit0，返回`stockqa.work_decision_apply/1.0.0`、status=recorded。它先验证真实StockWiki确认，再构造Store：

|项目|之前|之后|
|---|---:|---:|
|work schema|18|19|
|leased|26|25|
|failed|0|1|
|result_ready|4|4|
|owner work decision|0|1|
|work_event|184|185|
|已结算物理模型请求|13|13|
|历史费用|CNY1.268162|CNY1.268162|

唯一结案对象为原Alphabet试点IQS_01的length响应；reason=output_length。`failed`是该旧请求输出不可用的任务状态，不是给公司打低分或剔除股票池。没有重发请求、生成新评分或覆盖原回答。0正式评分、ACK0与4个insufficient_evidence检查点保持。

原work SHA由236e5aa4c4252a37f76c092100c8012c9abff11ee60914edb839bf424b0864e2变为a5e77ef5aa427b630a0a463e2cb9088a38ab7619f38b0a0d27eadbe572dafb05。即时备份保留于apply-execution/work-before.sqlite，原6库备份仍保留。后续不能继续用旧SHA断言原库仍18，也不能修改旧helper的预期SHA来重跑。

## 后验核对及真实薄弱点

原生apply已成功后，协调脚本断言误以为只会改变决议表和work_item，漏算原流程的work_event及其sqlite_sequence。该父脚本因此exit1；实际原生子进程exit0与已提交数据均保留，**没有重放apply、重试模型或把失败日志改绿**。

独立只读postcondition脚本核实：

- 原34张表中，除work_item、work_event、sqlite_sequence三张，另外31张表的每行和rowid摘要完全相同；原schema定义保持，新增19决议结构。
- 原其他29条work逐字段一致。IQS_01仅status、lease_token、lease_expires_at、updated_at改变，lease_epoch和其他字段不变。
- 原184条work_event逐行保留，仅追加一条known_response_resolved，绑定该work/attempt/lease_epoch，from_status=leased、to_status=failed。
- sqlite_sequence只将work_event自增1；其他序号保持。
- 新增唯一决议行与原公开CLI返回的document完全一致，引用本次真实确认与原物理响应；不是补SQL或自造grant。
- 原4checkpoint、标准答案、预算策略、13个物理attempt及terminal和原6个owner数据库rawSHA均保持。

后验verification.json状态verified。这个反例要求后续执行与核验分离：先保留真实子进程的exit/stdout与决议，再核事件；父级核验失败不能被当成“请求未执行”而盲重试。只在大节点做整体回归，不为每个helper追加审查门。

## 当前接续

现有实际状态是25leased（14length、11completed但无已接纳checkpoint）＋1failed（已获真实结案决议）＋4result_ready（insufficient_evidence）。旧26组请求资料仍保留为准备时历史；其中IQS_01已消费，应从后续待结案批次排除。

原生owner policy仍是1.1、仅原一公司/score.iqs_01/MiMo Pro。首次确认没有批准其余25项、新的retry/comparison、模型变化或收费执行。用户总体后续实施与预算授权持续有效；这里区分实际原生记录的动作范围，不能伪造额外确认。

下一步按[有界批量恢复设计](../../plans/b01-native-batch-recovery-2026-10-14.md)复用既有单项证明和决议端口，减少逐题确认与重复固定CLI启动。当前原生CLI仅有单项work-decision控制，批量能力尚未实现；不得把请求数组塞进原1.0单项封套或用fixture confirmer补齐。普通控制/同模型比较保持明确1.2，跨模型明确1.3；保持原13次费用，后续价格/配额调整按原公开配置和owner报价走，旧cap15已用13、剩2不能被重置。

COMPANY-AGENT-01仍在用户外包线，不进入其目录。金融参考资格仍0，G3/F05、生产UI、一键与全池尚未完成；本次仅关闭首次真实owner确认→原生apply→真实升级/结案这个工程节点。

## 本机证据与环境

证据根为C:/Users/郑曾波/Projects/invest-quick-scan/runs/b01-resume-2026-10-14-01/：

- operator-handoff当次目录位于owner-execution下；保留真实确认stdout/receipt、原namespace rc1原件。
- apply-execution含before/after、原work备份、真实apply.started/result/stdout/stderr，以及独立verification.json。始终使用keyless/禁网护栏，仅顶层原生apply可写精确原work路径，子进程保持原work只读。未修改StockQA/StockWiki源码。
- 当前work写是本次明确授权的真实生产写，不能继续把原库描述成未迁移或“本轮所有数据库写0”。收费API/下载公司文档/新名单或身份变更均0。
- apply-execution/temp为空，实际PID+创建UTC闭包0；发现1个复用PID，仅记录未操作。备份与真实运行日志保留，不当作测试临时物删除。
- 从启动到收据约97.65秒，目录留下85份不同PID的guard启动记录。该计数不是LLM/HTTP请求数，PID重用可能影响完整进程计数。后续可复用纯不可变验证，当前权限/主体/原件核验及批准不能被缓存结果替代。
