# 新版本联合链输入与测试适配

本目录接续[JR1–JR3唯一整改卡](../joint-2026-10-08/remediation.md)与[原联合验收](../joint-2026-10-08/acceptance.md)，属于同一个大节点。当前只是总控 IQS 目录内的准备；不增加任务、审查门或新生产客户端。

## 当前状态与权限

- StockQA 源码观察基线：`bc41908e4cdc44c13fefda97f3118e5434aed5f8`。Phase111 有限软件已经发布，原隔离回归与集中审查保持；本准备不重复861项测试。
- StockWiki 观察基线：`c40de21403720306ba21edbf71b9634a40ee58f8`。JR1/JR3四个候选文件与原 `d253fea5f4f6e4242d2b91eaf8d89d3dac8b45ff` 相同。
- 人类尚未答复本批 StockWiki 四文件与唯一 writer 问题。不得修改源仓、生产库、名单、UI、其他文件或安装镜像；授权问题不能由超时、施工卡或本文件代替。
- 待授权范围只有 `stockwiki/quick_scan_import.py`、`stockwiki/quick_scan_observations.py`、`tests/test_quick_scan_observations.py`、`tests/test_quick_scan_delivery.py`。若用户安排其他 harness，由其独占 writer；总控仅接收实际 commit/handoff。
- `inputs-01.json` 是只读观察，不是修复后的执行锁或权限凭证。`tests_passed=null`、`joint_ACK_closed=false`。新适配器尚未在运行时执行，AST通过只能证明语法可解析。

## 为什么旧脚本不能直接重跑

现在 StockQA 的 `begin_result_delivery()` 必须先有持久 consumer binding。旧测试驱动直接 begin，会在发送意图之前被正确拒绝。不得删掉新验证，也不得从收到的 ACK 推测预期目标。

`qa_actor.py` 只补 `bind-consumer`；其余操作转交原样复制的历史 `qa_driver.py`。`sw_actor.py` 只补 `receiver-owner`；其余操作转交原样历史 `sw_driver.py`。两个适配器均限定请求、结果、包、release和ACK路径在明确的 `E97_OWNED_ROOT` 内。

`receiver-owner` 从合成工作区中的真实 `QuickScanObservationStore.store_id` 生成 `joint_receiver_fixture/1.0.0` 描述。它必须在 begin/send/ACK 之前获取，由 QA 的公开 `bind_result_delivery_consumer(work_item_id, consumer, source_ref=...)` 持久绑定描述文件及其 SHA。

**这是测试工作区的目标绑定来源。它不是新的生产 CLI、真实发行人 identity DTO、事实 golden 或公共 query golden，不解锁 TH/IN。** 接收库路径改变可能改变 store_id；恢复到另一个目标时不能自动替换发送中的绑定。

## 留档格式与入口

运行 `python -B -X utf8 docs/implementation/reviews/G3/joint-2026-10-09-rebase/freeze_inputs.py` 会检查12个固定源 Git blob、接口签名、源仓 HEAD/分支/状态、六个既有内部依赖及四个新文件的 SHA，再写一次 `inputs-01.json`。已存在时明确拒绝覆盖；历史观察不得改成新修复状态。脚本不导入源模块、不建测试库、不读个人配置或密钥、不发网络请求。

执行前必须等实际 StockWiki 修复交付，然后在这里另建有序的 `inputs-02.json` 或后续执行锁，记录两 owner 的新 commit、真正完整的非秘密运行依赖白名单、fixture/guard/工具和配置摘要；不能把当前12文件观察清单当作完整可运行副本。固定文件需核对 Git blob 与工作树内容域，保留原字段，不能因换行差异改写冻结证据。

新运行环境只能在 IQS 下创建全新短名独占根，拒绝已有根、junction、symlink或其他 reparse。不要恢复或调用已删除的 `runs/joint-2026-10-08-01`、`runs/n111a` 以及旧固定根的一次性 helper。

准备者必须复制已锁定的非秘密源码、synthetic fixture 和惰性配置，不复制 `.git`、真实 DB、名单、网页正文、财报、个人配置或 API key。历史原件保持：

- [QA历史驱动](../joint-2026-10-08/qa_driver.py) → 新独占根 `legacy_qa_actor.py`。
- [SW历史驱动](../joint-2026-10-08/sw_driver.py) → 新独占根 `legacy_sw_actor.py`。
- [既有Python守卫](../../QA-C06-02/second-remediation-2026-10-08/sitecustomize.py) → 新独占根 `guard/sitecustomize.py`，按锁原字节复制。
- [既有惰性供应商配置](../../../intake/SW-REPAIR-02/2026-10-08-sr02-4b/verification/llm_providers.inert.yaml)只在必要的测试配置位置按锁复制。

各子进程只继承必要系统环境，去掉所有真实凭据，`STOCKQA_RUN_LIVE_E2E=0`；TEMP/TMP/TMPDIR、cwd及 E97_OWNED_ROOT 均指向本次独占根，禁字节码与外部pytest插件。PYTHONPATH先放 `guard` 再放该 owner 副本及其所需 src。网络守卫的实际探测为验收证据，不能只宣称环境已隔离。

在完成这些前置后，测试 actor 的调用形状为：

```powershell
python -B -X utf8 <fresh-owned-root>/qa_actor.py <fresh-owned-root>/cases/bind.request.json <fresh-owned-root>/cases/bind.response.json
python -B -X utf8 <fresh-owned-root>/sw_actor.py <fresh-owned-root>/cases/receiver.request.json <fresh-owned-root>/cases/receiver.response.json
```

尖括号是未来实际新根占位符，不是可直接执行的命令；实际验收必须记录完整 argv、cwd、PID/终态退出码、时间、stdout/stderr、输入及结果原字节 SHA。不用临时手造 ACK 或删字段得到通过。

接收方请求的精确结构：

```json
{"op":"receiver-owner","root":"<fresh-owned-root>/cases/sw"}
```

接收描述的字段固定为 `schema_version`、`synthetic_only`、`basis`、`workspace_root`、`consumer`。consumer只有 `component=StockWiki`、`namespace=quick_scan`、实际 `store_id`。QA绑定请求结构：

```json
{"op":"bind-consumer","root":"<fresh-owned-root>/cases/qa","question_id":"IQS_01","receiver_descriptor":"<fresh-owned-root>/cases/receiver.response.json"}
```

QA actor 输出真实 binding、descriptor SHA、before/after owner snapshot、`synthetic_only=true`、`incoming_ack_used_as_authority=false`。这些字段是测试留档，不增加 ExchangePackage/ImportAck 的字段或改变其原hash配方。

## 一次集中联合验收的顺序

1. Fresh-root锁与守卫自检 → SW合成身份 seed，必须保持 provisional → SW receiver-owner。此时尚无 ACK。
2. 从派发前冻结的synthetic manifest及题库锁独立生成release；来源不能取自接收到的 Observation。StockQA真实公开CLI冷跑，模型HTTP仅使用既有边界替身；保存完整原包、标准答案、attempt/账务。
3. QA按每个实际 work/head 调公开 bind-consumer → begin。缺目标绑定时先验证明确阻断、零发送与owner快照不变。
4. SW真实 `observation-import` 接收实际包，按公开 `ack_for` 原样读取原ACK；校验 [ImportAck1.0](../../../../../schemas/quick_scan/exchange.schema.json) 的 `$defs/ImportAck`。原ACK不能手工投影或补填consumer。
5. QA按预先绑定目标 apply原ACK，验证原包/原attempt/原费用未变；同ACK重放、丢回程后ack_for对账、重启及暖恢复不能增加模型/搜索HTTP。
6. 所有受影响用例同批完成后，按原大节点规则集中审查与实际提交交接。不为这些测试 helper 单独加审查门。

## 同批必测正反例

| 组 | 必须观察的真实行为 |
|---|---|
| 新公共ACK | accepted/already_present/rejected/conflict 全状态合法，严格10根字段与consumer形状，公共error taxonomy一致；事务保存并稳定重放ack_id/received_at/原JSON |
| 历史ACK | 原enriched1.0 JSON/SHA/ID只读保留；默认 legacy_wire_pending，不自动delivered，不在读取时删字段伪兼容 |
| 目标绑定 | 缺binding、错误store/namespace、错误package/item/hash/observation、旧head均原子拒绝；同binding幂等，发送中不同binding不可替换 |
| 接收解析 | 实际raw JSON顶层/嵌套/数组内重复键、NaN/±Infinity/±1e400均拒绝且观察与ACK零写；直接dict入口非有限数值同样拒绝 |
| 恢复 | 新合法ACK丢回程→读取原件→QA落定，独立warm/reopen/seal为零增量HTTP；未知发送仍hold，不因重试、换模型或换目标洗成成功 |
| 内容与查询边界 | 低分、unknown/null、N/A、watch、完整长body均保持；合成身份仍provisional，测试fixture绝不能冒充真实identity/facts/query正例 |

完成后只关闭被实际证明的JR1/JR3和对应联合软件问题。G3、F05、L03、金融事实/计价认证、真实 owner query/golden、TH/IN写授权及一键启动有各自原前置，不能由本目录准备或synthetic软件用例自动关闭。

## 结束与下一位接手

保留原请求/输出/失败/修复日志，不重写过去的RED或原探针。结束时由新根owner先核对实际子进程终态、完整路径集合、真实lstat/reparse/nlink、每文件大小/SHA；只删除本次自有根，不碰共享TEMP、旧根、外仓未跟踪项或生产库。最终交接记录源码commit、接口/CLI版本、真实测试数与范围、原日志索引和清理证明；尚未执行的项目写pending。

目前唯一跨仓下一动作仍是人类答复StockWiki四文件与writer范围，按JR1/JR3卡修复并交实际结果，再生成新执行锁做上述一次联合验收。没有活测试或Git handle，不能把等待授权写成进程正在运行。
