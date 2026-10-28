# 受控恢复子集展示与接线契约

本操作只恢复原owner已明确批准的有限失败范围，不是普通全公司快扫。普通题库和基本必做集合不裁剪，题数动态派生；当前示例36题不是固定限制。

## 原生执行顺序

1. 原隔离owner配置显式切换到支持新purpose的1.2，保留旧1.1配置与历史授权。不得先按1.1确认再换策略复用旧fact。
2. root通过原public CLI为精确源work创建新的有限确认。不可交付旧检查点使用`retry_unusable_checkpoint`；已收响应但未形成已接受答案，则先以真实原因执行原`known_response_resolution`，再对原failed工作使用既有`retry_unusable_answer`。两purpose的源状态分别只能是result_ready/failed；不得把本地程序错误伪称模型格式错误。旧purpose和旧grant不扩权。
3. 原只读control projection校验trusted `prepare.recovery_work_decision_refs`，只为所选实体/主体/证券/模型/截止日匹配的控制字段准备执行子集。无匹配不能回落为全题或空任务成功。
4. 原deriver选择N+1，原admission分配target work ID。原source work/checkpoint/context/outbox/response/费用保留。
5. 原扫描、标准封存、StockWiki导入与exact ACK完成后，显式复位普通1.1配置，移除专用refs。仍在有效期内且期间、题义、主体和模型匹配的观测，经原query按exact observation ID复用；已过期则走原普通下一代刷新。两条路径必须分别验收，不能以derive或仅warm通过代替。

旧source永远保留。普通下一代的写入及发送守卫，只能在同一原生事务里核实原决议、准确后继ORF、原封包、消费者绑定和exact ACK之后，忽略这一条已由后继解决的历史阻塞；新代际须严格晚于该后继。单有`delivered`标签、未封包、缺ACK、错决议/确认或另一未决工作仍不得放行。当前权限、预算与有效期继续按原系统核验。

如果受控后继本身再次失败，只能沿原immutable决议与ORF逐代验证：旧checkpoint的原retry → 确切failed后继 → 该failed工作的原retry_unusable_answer → N+1。每跳同实体/题目/scope且严格+1；当前待创建目标不能用自身证明祖先已解决。仅当前原owner授权的answer retry可以暂时越过自己的确切旧ready祖先，旁支pending/leased/uncertain/ready仍照常阻塞。普通后续刷新必须等链末端真正封包、消费者绑定与exact ACK。这里不承诺其他comparison或跨模型控制类型自动穿越这条祖先链。

保留的最终公开回答、parser通过和HTTP200都不是过期租约的补存授权。现有原接口若没有合法的expired/no-checkpoint收回入口，不得假时钟、延长原lease或直接改库补CP；须按上述原有限处置与重试接续。保留原答文和已发生费用，不将重试伪装成缓存命中。

信息日期不会因重新导入而获得新有效期。缓存验收记录信息截止日、信息日期、TTL、观测/校验时间与实际新HTTP数；已过期结果保留历史用途，但不得算有效缓存。禁止为关闭验收而延长真实TTL、改写历史答案日期或删除旧检查点。

## 锁定的展示接口

以下对象均由可信本机服务返回。浏览器只展示，不借此批准work、模型或费用。

`preview.bank.question_count`、`preview.question_count`、`preview.questions`仍表示完整题库。恢复时另有顶层`execution_question_ids`和`execution_question_count`。

普通操作的`recovery_subset`为null；恢复操作为：

```json
{
  "protocol": "iqs.dashboard-recovery-subset/1.0.0",
  "purpose": "retry_unusable_checkpoint",
  "execution_question_ids": ["IQS_04"],
  "execution_question_count": 1,
  "full_bank_question_count": 36,
  "items": [{
    "question_id": "IQS_04",
    "work_item_id": "SOURCE_WORK_ID",
    "decision_id": "ORIGINAL_CONFIRMED_DECISION_ID",
    "source_generation": 1,
    "target_generation": 2
  }]
}
```

`items[].work_item_id`是原legacy检查点的source work，不能用于当新执行target或UI run ID。target ID仅来自原`admission.registration.items[].work_item_id`。不得预造target。

全部为checkpoint重试时仍返回上述1.0对象，保持旧格式不变。包含answer重试时使用展示协议`iqs.dashboard-recovery-subset/1.1.0`，顶层`purpose`为`native_controlled_retry`，每个`items[]`增加其原始`purpose`，仅允许`retry_unusable_checkpoint`或`retry_unusable_answer`；其余字段和完整题库/本scope执行数含义不变。允许同一明确选择中混合两种原生purpose，每个都必须通过对应源状态、精确决议、N+1和delivery_required=false校验。`items[].work_item_id`在新格式中仍是原source，不是新target。UI把item purpose纳入组一致性签名，未知版本/原因/代际或不一致数据不报完成；展示元数据不产生权限。

prepared result也携带`recovery_subset`、execution IDs/count、`full_bank_question_count`。每个公开registered execution bundle携带同一公司恢复说明`recovery_subset`以及该scope实际的execution IDs/count；其`company_preparation_id`仍是本次preview ID。多scope时scope计数可以小于本公司恢复总数，不能相加重复的公司总数。

## 界面边界

- 预览、选择组、批次和交付必须在主层标明“受控恢复子集；仅本次字段，不代表整家公司题库完成”。完整题库题数和本次执行数分别显示。
- 通过已注册bundle的对象标记识别，不从bundle ID、公司名称或generation字符串猜测。未知/非法恢复标记明确显示无法解释，不伪装为普通全范围完成。
- 普通无标记与历史数据保留原显示。原allowed_actions、原预检、scope顺序、费用确认和写请求幂等不变。界面标记不产生新执行权。
- 完成恢复子集或收到ACK，不代表该公司其他待问题已做完，也不代表金融质量通过。

## 并行所有权

原协议/Store投影/纯contract/schema与Dashboard恢复子集后端由原owner能力线负责；前端仅UI仓product.js、product_core.js和既有实际ESM测试由独立UI线负责；runner严格标准入口另线负责。共享PWF、发布、原实际配置与实际两工作控制只有root负责。源码冻结后统一独审和正常提交，不在活动writer期间触发autostash。
