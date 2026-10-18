# 委托确认大节点独立审查

独立审查者 `/root/production_node_review18`，实现作者 `/root/owner_services18`。本次是新的完整委托确认节点，不重开已通过的共享引擎工程验收，也不纳入尚未验收的 native-continuation 候选。审查者只写本报告目录及专属 independent-review 证据目录，未写实现源码/PWF、生产数据库、名单，未调用收费 API。

## 源码判断

审查覆盖 CAS 中15个精确路径：StockWiki 的固定 namespace 委托/CLI；StockQA 原 consent/admission/journal 与独立 delegated wire 校验；原 budget 只读历史兼容；相关测试、历史 fixture 和隔离 guard。所有候选哈希和实际执行 runtime 中对应最终源码均独立核对。

新入口明确使用 rc2、confirmation-record/2.0、inspection/1.2 和 `native_owner_delegated_agent`。旧 rc1/record1.0/inspection1.1、TTY confirmer 和 work-decision 路径保持原约束；未把 agent 伪装成人类 terminal，也没有 `--yes` 或 caller-confirmed 标志。StockQA 的版本选择与 rc 前缀严格绑定；只升级一个仓库时不构成旧客户端静默接受新记录。

权限来自实际 OS owner principal 与原固定 StockWiki owner namespace。安装文件固定为 `config/quick_scan_delegation_install.json`；CLI 不允许另选安装路径。安装再次校验原 ready preview、准确输入记录及当前 owner 权限；完整绑定原主体/问题/字段/模块/route/model/quote/部署/预算文件。hash、profile_sha 和 harness_ref 只作内容/来源记录，不能认证独立 agent 身份。

同一 preview 的稳定 grant ID 与不可变发布保持首次时间/有效期，不能通过重装延长或换 agent/绑定。rc2 单 action 固定首次 idempotency-key；并发沿用原发布锁、同回执或显式 busy/conflict。当前 principal/owner policy/scope、grant 有效期、不可撤回的 revocation 都在原 inspection/current-permission/POST 链路复核。已准入在途 HTTP 不被追溯取消；撤销不冲销历史费用。并未引入第二个 SDK、账本、预算或执行循环。

原 v18 只读 budgetStatus 的 quota JOIN 缺陷由显式已验证历史 schema 分支修复；没有用 `table_exists` 吞当前库损坏。原 reserved/spent/request/in-flight/unreconciled 保留，quota capability 缺失不等于现金费用为零，历史 isolation 明确不支持。伪改 v18 header、当前库缺表仍拒绝。v15/v18 fixture 先完整移除所有后续 DDL 再降临时 header，未伪造“旧库”。

## 独立未见反例

`delegated_probes.py`：**10 passed，2.75秒**。这些是拒绝态/真实临时 SQLite 测试，不构造成功 owner double：

- 重新封 hash 后，超过24小时/零或倒序有效期/非UTC/控制字符/伪加密身份/布尔型 quote 仍拒绝。
- 实际 hardlink owner 文件、读取期间真实文件变更，在解析载荷前拒绝。
- 实际临时 v18 同时保留 unknown、response-unpriced 和 active reservation：三条原预算记录、两条 unreconciled、原金额与 requests/in-flight 一致；blocking=2、cash incomplete，原文件字节完全不变。

没有为完成案例放宽原 SDK unknown 优先级、owner guard、预算或异常封装。旧第三轮 public 日志的最终失败位于撤销后 `service.admit` 测试误按返回值处理；原实现当时已经正确拒绝。最终测试改为断言原 `AdmissionRejected`，没有改源码去放行。

## 最终真实软件证据

各组单独报告，避免重复叠加计数：31个最终契约测试通过（12.255秒）；103个 StockQA 原回归通过（113.490秒）；22个 StockWiki 原回归通过（3.509秒）；实际公开委托完整软件 E2E 1个通过（248.322秒）。不把测试 fixture 的合成 preview 当作原 owner 正例：唯一完整正例来自实际 public CLI→原 preview/config namespace→真实本机 principal install→rc2 confirm→原 admission/replay→原 SDK。

这个 E2E 的公司/consent/回答是隔离的合成工程数据，vendor wire 为 scripted timeout，不能给出真实公司金融正确性或真实价格/延迟结论。它证明两个原问题中，第一个真实 SDK timeout 后保留 unknown 和原预留，同一 SDK 被原 barrier 拒绝；另一个从未发送且在撤销前已证明原 pre-POST guard 有效的 work，在实际 native revoke 后通过全新 SDK 被当前 owner guard 拒绝，新增POST=0。不能用第一条未知请求的预算/SDK barrier 冒充第二条 work 的撤销验证。

审查者 mode=ro 独立核实际最终 SQLite，读前后 SHA-256 均为 `8711b6f2a8fc06a77f08f0148e5534c3595cc549a2c163238c49dd9bf265c90f`：2个原 work、1个 attempt、1个预算请求、1条 admission、0个 safe output；唯一 budget 状态 `outcome_uncertain`，actual cost为null，原 reservation 1,000,000 micros；另一 work 无 attempt。实际 rc2/record2.0/delegated method 和原 revocation 文件存在且已留薄 hash；未导出 principal、答案、lease 或数据库正文。

最终源码、runtime guard、日志/XML、临时工作区隔离是实际核验对象；旧失败日志与历史 source pin 不被覆盖或冒称最终通过。审查未要求重复耗时的未变 public fixture，只核最终运行及精确源码/DB证据。

## 明确边界

本节点可以签收的是精确源码及实际本机 owner 委托软件链路。它不安装真实生产 grant，不认证远程/加密 agent 身份，不授予 work-control、S1 unknown/旧费用处理、continuation 或财务结论资格。原 S1 旧账本/未知金额仍是原约束，不能换干净库、清 reservation 或复装 grant 规避。native-continuation 是另一节点；其未验收不拖延或自动扩大本次范围。清理以作者最终记录为准，拒绝删除时必须保留并报告，不绕过。

## 正常 hooks 后的最终交付等价附录

已独立核对全部15个候选、实际工作树、最终commit blob。StockWiki交付为 `3fad36d1ae82333d9d1ed1eb4c55ee775d35b0df`（正常检查，无remote）；StockQA交付为 `aaddcd6be6f506ca58791d7ecc375bbffa7b0c70`（正常hooks，原origin推送由总控完成）。14个文件完整AST与受检候选相同，包括StockWiki ruff调整的测试；仅QA `tests/delegated_fixture.py` 顶层import组排序不同。该文件非顶层import AST和完整import集合相同，integration skip仍在imports之前，无授权检查、状态变更、fixture执行或赋值移动，StockWiki/StockQA被导入定义不依赖组间顺序。所有实际工作树与commit blob的AST相同。

精确hash见同一签收引用的 `delegated-owner-independent-review/post-hook-equivalence.json`。原候选/CAS不改，不把import排序误称完整AST相同；这种机械交付变更不重复运行未变的四分钟public流程，也不构成额外小节点验收。
