# EVID-LAB-01 第二次整改集中独审

2026-10-08；审查者 `/root/evid_lab_remediation_review`。只读静态核查，未运行 Lab 程序、未写源仓。源码结果 `d4360fdbbd9a83d2830066546edf1827ab424834`，接收 HEAD `aeff0e68022f56b331a58503df7b53ed8d2b3882`。动态证据由总控在独占副本补充，见 [验收](acceptance.md)。本轮只做一次集中独审。

六项原修复已落地：custom 期间保留起止并比较；历史答案始终与归档答案比对，省略可选 hash 不再关闭比对；严格 JSON 解析拒绝 `1e400` 溢出；冲突来源加未知窗口会 abstain；来源类别检查覆盖所有记录、未收集 FX034 不伪称真实片段；费用公式按实际输出上限 10000 重算为 0.82296 USD，展示上限 0.83。CLI 0.2.1、diagnostic schema 1.2.0、semantic/structure rules 3 与新增理由一致。完整、未修改答案省略可选 hash 可以通过，这是卡内允许的选择。

## P1 — LR-02B：历史 fixture 入口没有校验归档锁

`src/iqs_evidence_lab/fixtures.py:27` 的 `_archive_rows()` 从环境选择的 IQS 根读取当前 `results.jsonl`，白名单限制 run 名称，不校验文件仍符合输入锁。`fixtures.py:131` 新增的答案比较保护了“只改 fixture”场景，却比较的是当前归档。`src/iqs_evidence_lab/cli.py:265` 的 `prepare_fixture_replay()` 没有调用严格输入锁验证；index 路径在 `cli.py:144` 调用 `verify_lock(..., strict=True)`。

建议最小反例：在总控独占副本中保留原 lock/index，修改 FX032 对应归档答案，并同步修改 fixture、去掉可选 answer hash；通过真实 CLI 回放。预期非零且不发布，静态追链预计会成功发布 historical、summary 仍称 verified_before_write。本独审没有执行此反例。

总控随后实际确认：完整答案省略 hash exit0；只改 fixture exit4；同时改副本归档和 fixture exit0并发布；同一漂移走 index exit2。见 [四项原回执](../../../intake/EVID-LAB-01/2026-10-08-second-remediation/verification/archive-binding-corrected/archive-binding-result.json)。这是原 LR-02 来源链内的剩余缺口，不是新增事实准确性或评分研究范围。

## 边界

handoff 披露一次会话事故：在 IQS 根生成并删除 `nul`。`verification.external_writes=false` 只适用于其明确限定的验证/测试/CLI，不能称整个会话零外写。总控没有独立证明已消失文件的历史归属或大小。

可确认范围是输入经总控先验冻结时的离线重算、显式维度诊断、来源分层与已验证的 Windows 原子发布。提案仍为未签核草案。事实准确性、精确投资评分、人类 gold、模型实际 revision、实验执行及 L02/G3/F05 不随本包局部通过。
