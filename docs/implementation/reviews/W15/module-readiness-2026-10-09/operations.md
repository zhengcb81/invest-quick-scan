# W15操作与接续（评分刷新基础链，真实公司准入仍待）

本包不是金融准确性验收。仅问卷、短来源、结构化答案、身份与任务元数据入库；不下载或保存公司文档/网页正文。用户逐批确认的股票池不由本包扩大。原收费账本、未知请求和ACK不能被清空或换库绕过。

## 单一职责与接口

- IQS `scripts/route_store_handoff.py` 完整校验已经发布的route/manifest，protocol `iqs.route_store_validation/1.0.0`，history不授予新派发；execution必须有caller独立expected decision ID、可信now和发布归档。支持route schema2/发布manifest3.1；不是旧route schema1兼容承诺。
- StockWiki身份库schema6追加route_snapshot/current/history，Observation库仍schema2、AnalysisSubject库仍schema1；历史行、置信度、原模型/时间/缺字段不改。current锚点按subject/revision+scope，以显式期望值CAS激活。schema迁移只能按既有首次配置/备份流程明确执行，CLI读/refresh不自动迁移真实库。
- StockWiki公开独立CLI `python -B -m stockwiki.quick_scan_routes_cli --root <workspace> quick-scan-route-{binding,record,activate,current,anchor,history,refresh}`，与主CLI同注册；protocol `stockwiki.route_store_cli/1.0.0`。`--iqs-code-root`是可信代码根，`--iqs-release-root`是归档/题库根，均由用户配置。binding取得主体ref后才能让IQS作route；record拒绝任意自报其他subject/ref。
- `current --include-raw-bundle`进行完整执行校验，并返回原bytes/base64、双raw SHA、主体/来源绑定、anchor版本。`anchor`只读原bytes SHA/current/当前身份来检测已验证bundle的漂移，明确 `new_execution_authorized=false`；不能单独作为执行许可。运行期间代码/归档根必须维持冻结；部署变更先停新派发，重新完整current验证，不能宣称SQLite跨仓分布式原子性。
- `refresh`使用W06比较语义/定义/rubric/作用层/期间/实际模型，TTL取信息时间与实际回答时间较早者，保持 `exact_period`。未知无retry_at需人工刷新；退出模块留历史，聚合规则变化标不可比。主体缺失的旧观察不回填复用。证券ID缺失就暂缓具体证券题，分部路由把issuer构念绑定到明确segment；不能猜第一个ticker。
- StockQA v14只在已有任务库加不可变owner refresh binding，不另建费用库；`--quick-scan-owner-config`为可选接线，无该参数保持原Q13行为。配置不能携带命令/API key/外来refresh-plan；固定first-party CLI current→QA自己完整work projection→owner refresh→重核anchor。每题hydration/claim前按action分流，新发送继续原租约/预算/HTTP单次发送接口，事务内重新核所有generations的未决项，不能用只读planner替代事务。

## 配置模板（无密钥，所有主体/作用层须由owner实际给定）

```json
{
  "protocol": "stockqa.owner_refresh_config/1.0.0",
  "stockwiki_code_root": "C:/Users/郑曾波/Projects/StockWiki",
  "stockwiki_workspace_root": "C:/ABSOLUTE/OWNER_WORKSPACE",
  "iqs_code_root": "C:/Users/郑曾波/Projects/invest-quick-scan",
  "iqs_release_root": "C:/ABSOLUTE/FROZEN_RELEASE_ROOT",
  "subject_key": "OWNER_AUTHORITATIVE_SUBJECT_REVISION_KEY",
  "scope": "entity",
  "scope_id": "ENT_OWNER_AUTHORITATIVE_ID",
  "ttl_hours": 120,
  "runs_dir": "C:/ABSOLUTE/EXECUTOR_OWNED_RUNS"
}
```

StockQA公开入口同时需要原 `--require-search --entity-id --identity-snapshot --question-manifest --spend-authorization --c06-authority` 和已准入model policy；authority须完整v2，主体与当前owner匹配。模型优先级/价格/搜索配置继续用原接口，不能由owner config偷偷替换；真实api key仅本机环境。填表模板不等于正式准入，未配置或身份冲突在收费前拒绝。

## 输出与恢复

输出外层为 `stockqa.owner_refresh_result/1.0.0`：`observation_references`只带实际原ID/原payload/hash/qualification；`dispatched_result`是这轮新增/被暂缓问题的原StockQA结果格式，零新增时可为null。旧答案不进入新manifest的answers或新C06封包，旧评分/来源/模型/时间仍是原观察。该wrapper schema只验证交接结构，原Observation合法性来自owner原入库/本次绑定，不以wrapper验证冒充金融正确性。

`refresh_id`包含now，仅审计，不作收费防重键；耐久绑定使用原request identity、目标generation和current route锚点。相同refresh重启不能生成G3或第二个work。旧unknown先恢复/对账，不因换模型/题义/截止日绕过；legacy无主体绑定的未决任务保守阻断相同entity/question/scope的新收费，不猜其报表范围。

额度/并发容量等待的每次准入前都重新读owner锚点，漂移具名拒绝且不新增费用预留；work路径保留prepared用于明确恢复。该检查与两个owner的SQLite事务并非分布式原子锁，校验返回后仍可能发生跨仓变化。不能声称消除了所有跨库时间竞态。

未发过HTTP且过期的**相同原owner绑定**租约可经原recover_expired回到pending；send intent则变uncertain，不能自动重问。result_ready/partial ACK/送达不明交接原work ID与原context给现有Q10/outbox恢复入口；新route/prompt不能重绑定。已封包优先按原字节恢复，已accepted ACK只读；owner缺原Observation却执行端已delivered为 `owner_refresh_ack_observation_missing`，先对账，不重新收费。该包暂不在owner刷新中自动重封旧包，也不恢复正式费用许可。

## 验证与边界

本包开发采用独占runs/w15a、凭据剥离/Python网络及foreign SQLite guard；不是全OS认证。baseline原fixture失败、真实RED、修复GREEN各自保留，不合并不同源码/重复suite计数。实际IQS producer＋StockWiki OS CLI＋StockQA SQLite联调是合成公司/答案storage boundary，不是真实identity/query golden或准确性实验。

最终同一包一次集中审查。私有候选冻结、精确源HEAD/dirty重核、正常hooks/commit/push后再严格lstat/SHA/终态核验清自有根；不得删共享TEMP/未知项。StockWiki按现有决定7保持本地无remote。W15软件签收不关闭真实query/identity/facts、G3/L03、B01准确性/F05/TH-IN。

公开wire固定由IQS三份本地JSON Schema定义：route-store-validation、route-store-cli、module-refresh。StockQA按静态本地registry读取，不联网取ref、不跨仓导入Python。CLI始终保留`c06_envelope_validated=false`，当前仅评分`scored`及已核N/A原观察复用；纯信息`answered`、关系字段与事实C06投影尚未接线，留在F05。现阶段不得把该入口改称完整C06 query/refresh或真实owner golden。

全仓诊断曾用真实26份结构化metadata及四份只读SQLite备份的自有克隆；不复制公司文档/密钥或生成真实观察。原库schema5保持不变。完整suite原1063P/64F/18skip/21error，不作通过依据；缺支持资源、隔离guard及旧fixture分别见同次审查分类附记。正式基础链签收只认最终当前SHA的受影响回归与公开CLI；不重复全仓/UI诊断来累加计数。
