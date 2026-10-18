# reviewed delivery v2 独立审查：不通过，已撤下 — 2026-10-18

## 背景

2 题评分 run 的 admission 已完成，但 dispatch 被 reviewed-deployment 门（controller CAS/reviewer 冻结）拦住。为走通，尝试 iqs.deployment_proof/2.0.0：由 reviewed scope + 独立 review 文档绑定，controller_delivery.verify_deployment 对 v2 proof 走新校验。

## 独立审查结论：findings（不能作为 scope）

High（可伪造/绕过）：

1. reviewer 身份自证：任意非空 agent_id，只要不在 author 列表即通过；无 allowlist/签名/commit 绑定。
2. scope 是自选子集，未要求完整运行 inventory；未列入的文件仍会执行。
3. v2 分支绕过 v1 的 source/controller CAS、public-context allowlist、onboarding pins；public_context 直接取自未受信 review，可指向任意 board。

Medium：review 路径不受允许根限制；按模块名导入 verifier 可被 sys.path 遮蔽；allowed_roots 可被调用方放宽；scope 路径按 cwd resolve；proof hash 可选。

Low（QA/schema）：owner_ack_ref 只是标签；validate_retained_rows fresh 分支未查 requests/reserved/spent；assert_research_task 不校验 exposure 结构；schema retained enum 未与 protocol 绑定。

## 决定

- **不接受 v2 作为 reviewed delivery，不绕过 v1 门。**
- 已撤下 controller 的 v2 分支、删除 scripts/deployment_proof_v2.py 与其测试。
- owner policy 已恢复为原 1.5 备份（sha 3239c35b…）。
- 未 dispatch、未付费、未写业务库。
- QA 已补 fresh 分支的 requests/reserved/spent 零值校验（Low 10）。

## 要真正解锁，需要 owner 提供可验证的信任锚

二选一：

1. owner 指定一个固定 reviewer 身份/允许列表（例如 CI key、签名机制），并把它写进 proof 校验；
2. owner 对一次完整 scope（全部运行文件 + public context + controller）做可验证的批准（签名或可验证回执），而不是由 agent 自证。

在此之前，2 题评分 run 只能保持 admitted-but-not-dispatched。
