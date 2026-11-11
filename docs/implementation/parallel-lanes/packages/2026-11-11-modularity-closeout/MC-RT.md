# MC-RT：Runtime薄适配与真实源码测试分层

可独立交harness。先读 [总路线](README.md)、[契约/TDD](contracts-and-tdd.md)、[调查](architecture-audit.md)、[交接](integration-and-handoff.md)。重点不是继续扩扫描器，而是发布已有接口、取消历史交付门、证明可替换。

## 输入与写入

- 源仓：`C:/Users/郑曾波/Projects/iqs-agent-runtime-lab`，分支`codex/agent-run-02`，HEAD `5839ef4`不含api；磁盘有API1.4。
- 已有更完整候选：`C:/Users/郑曾波/Projects/invest-quick-scan/.tmp-modularity-runtime-20261110`，49份tracked差异另有新api/_api_runtime/company_agent_api等。不能只取HEAD，也不能只提交测试。
- 实现树：`C:/Users/郑曾波/Projects/iqs-modularity-worktrees-20261111/MC-RT`；`codex/modularity-runtime-20261111`，尚未创建。
- 只写本仓src、conftest/tests/integration_tests/测试工具、依赖声明必要项和本包PWF。旧AGENT-RUN-02报告保留历史内容，不刷新pin/手写计数求绿。外仓源码/DB只读。

## 目标结构

API1.4 → 薄runtime/tool/receipt适配 → C3 services协议；QA实现真实effects。公开runtime只四操作；生产协议与frozen SDK double分离。CA API操作投影有限，保持已有slots句柄。Runtime不拥有新预算/重试器/持久化恢复引擎。

## 实施顺序

1. 归拢候选，把新源码和依赖测试一起迁入隔离树。现有36项局部通过仅作历史参考，不能替本轮当前组合。
2. 写仅公开services fake正例及内部字段访问反例，覆盖task DTO不会被修改、session不泄漏；公共receipt必须保持真实usage/失败状态。
3. 将生产services接口与测试double拆开；避免根conftest无条件注入locked源码/facade。原7个`integration_tests/test_current_sources.py`明确改标legacy来源并保留回放。
4. 新建独立进程的当前公开接口测试，**不继承legacy conftest**；可先测试公开fake，待QA/CA提交再对实际接口运行。不得用只导入成功替代执行。
5. `test_document_claims`、`test_handoff_pins`及旧announce/218/219计数从当前默认功能验收移入显式legacy归档组或取消重复检查。不要篡改旧报告使其冒称覆盖新代码。普通pytest默认只包含当前产品行为和有意义兼容回归。
6. 收敛1657行扫描到域依赖/直接私有访问规则加真实封装测试；先证明原实质负例仍被捕获，不继续解释任意函数返回/反射。
7. 短路径隔离测试，一次独审，形成源码/资源/测试自包含commit。

## TDD矩阵

|场景|结果|
|---|---|
|最小11操作services，无LLMClient/Store具体类|model/search/tool续接通过|
|optional observe_model_receipt声明/不声明|按capability要求，不无条件阻挡|
|缺本次必需操作、未知major|claim和HTTP之前明确错误；不把浏览变成新发准入|
|句柄普通读取session/service/内部port，修改嵌套DTO|读取失败/owner不变|
|失败与恢复|usage/耗时/receipt不伪造；效果仍通过QA操作|
|当前owner干净提交运行且无locked fixture路径|当前组合真实执行，不是legacy冒名|
|添加正常新用例/修改无关说明文字|产品功能suite不因历史218或旧pin失败|
|短临时根搬迁|没有机器源码路径依赖；测试自己清理|

现有短组：

```powershell
python -B -m pytest -q tests/test_public_api.py tests/test_public_task_contract.py tests/test_company_agent_api_compat.py tests/test_preflight_before_claim.py tests/test_module_boundaries.py tests/test_recovery.py -p no:cacheprovider
```

分组后显式记录legacy命令与当前命令。最终可对本仓当前功能suite跑一次完整检查，不能每个小修跑全套；Windows使用独有短basetemp。真实owner组合由总控I1–I4完成，本包若尚缺提交只报依赖，不能偷偷加载canonical未提交状态。

## 交付

自己的命名PWF与`docs/handoff/MC-RT/handoff.md`；注明哪些测试现在是legacy、哪些实际使用当前owner。独立agent必须核这一点及完整diff；修完实质问题再交。只记录最终实现commit和实测结果，不另造冻结签章。
