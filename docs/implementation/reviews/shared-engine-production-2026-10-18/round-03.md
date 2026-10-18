# 共享引擎整节点独审：公开组合与恢复窗口

整节点仍 `in_progress`；Company 的精确源码签收范围不变，不把组件通过当作生产闭门。

## F04 / P1：收到已知答复后、receipt journal 持久化前的恢复入口缺失

候选 `composition-candidate/scripts/shared_company_engine.py` 的原实现只在合成 `RunCrashed` 分支写 checkpoint。真实 SDK 异常或真实进程中断只保留 task-bundle/events，而公开 `resume_shared_engine` 必须接收 checkpoint。

独立反例通过原始 Runner 和明确合成的 port 发出一次调用、拿到一份已知安全 receipt，随后在持久化 `receipt_model` journal 的原子 rename 处注入 I/O 失败。其余原始 intent/runtime-request 仍在持久化 journal 中，但 session 没有 checkpoint，无法进入公开 resume。复现：`runs/shared-engine-production-2026-10-18/independent-review/composition_probes.py`；`composition-probes-r2.xml` 为 1 个实质失败。

测试第一轮的 run_id 含 `disk-window`，其中 `sk-` 触发原凭据写路径守卫，尚未抵达目标窗口；已仅修测试 run_id 为 `storagewindow` 后得到上述第二轮有效结果。第一轮产物保留，不记作另一项产品缺陷。

实现方正在用不增加调度循环的薄 port 包装修复：在已持久化的原 intent/runtime request 之后、任何模型 HTTP 之前，写原始可验证 pending checkpoint；收到安全 receipt 后先更新原 checkpoint，再交回同一原 Runner。最窄的原生 pack 已发送但尚未有 receipt ref 的窗口，必须有原 store 的 intent→receipt 绑定；没有原证明就应明确 pause，不能用第二个 ledger 或合成证明补过。

还须检查旧合法 checkpoint 的兼容性：其原 journal 若已含 `response_available` receipt，不能不加核对地换成时间/session-handle 不同的重建投影后重复记同一物理 attempt；原 metrics 对两个已完成冲突事实的拒绝必须保留。该项目前为待测试的静态风险，尚未另立实证缺陷。

本轮 0 付费请求、0 密钥读取、0 原仓/生产数据库写入，隔离产物保留。审查者未修改任何实现源码。

## 修复复验与 F05

F04 的原始故障窗口已独立转绿：`composition-probes-r3.xml` 为 1 通过，已知 receipt 后 journal rename 失败仍有 pending checkpoint，且通过原 `_verify_snapshot_against_history`。组合实现增加了原始 resume、旧 receipt 兼容、未知结果拒绝和真实 OS 进程退出测试；最终组合文件仍在完成该同一节点的最后绑定，不因此提前关闭生产 owner 门。

新增通用 native intent join 另暴露 **F05 / P1**：其 getter 只核对成员列表自哈希，未与原物理 pack 成员表对照。独立隔离 SQLite 反例将 `work_item_ids_json` 改为外组并重算 `binding_sha256` 后，原 getter 接受了外组与真 receipt 的混合；`intent-probes-r1.xml` 1 失败。总控修为从原 singleton attempt 或原完整 pack getter 推导真实成员和请求 SHA 后比对；同一反例 `intent-probes-r2.xml` 已 1 通过。原 native ledger 和模型/owner 守卫未放宽。

Company 源码已由总控提交为 `cd5e3e7ff44aa94cff3f7728c5c38811e9192b85`；独审只读复核 11 个已应用文件均与已签收 CAS 完全同哈希。其他 native/owner/组合范围与真实公司验收仍按各自实际证据保持进行态。
