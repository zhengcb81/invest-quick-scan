# 共享引擎生产接线整节点独立审查：修复验证

审查者仍为 `/root/production_node_review18`，未修改任何候选源码。这里记录整节点审查中的修复证据；生产 owner adapter 和公开 Runner 组合尚待冻结，**整节点结论仍 pending**，不新增分步骤审批门。

## 已闭环的根因

- **F01 / P1**：总控修复 Company 最终 board epoch → run epoch → 原 journal epoch 链及逐次 answer commit epoch 的绑定。独立的“保留原 epoch”和“连 run epoch 也重算”两种伪造来源反例均拒绝。空证据正常运行仍可生成 `unobserved` 摘要。
- **F02 / P2**：独立反例发现 checkpoint 的 task bundle 仍与原 task/恢复 task 共享嵌套引用，会在快照创建后悄然改变并破坏自哈希。实现方在创建/还原边界深拷贝后，“源 task 后改”和“恢复 task 后改”两个独立反例通过。
- **F03 / P1**：独立 SDK+pack SQLite 反例确认，已返回错模型答复并报告已知 token 时，原 response_available 的模型守卫拒绝发生在 receipt 落库前，导致原已知 usage 丢失。实现方转用原 `record_failure` 的 unknown 结果通道保留 receipt/已知用量，同时保留原模型守卫；不落可重放输出，第二次请求仍拒绝，wire 始终只有 1 次。
- **原生安全输出来源加固**：原安全 payload 的自哈希不够证明它等于原答复的可公开投影。实现方将 `research_visible_output_sha256` 加到原 immutable native receipt，并在原子写入和 getter 中核对。独立测试在隔离 SQLite 中替换 output、重算 payload SHA，仍无法骗过 getter。没有保存原隐藏推理/请求历史来实现校验。
- **隐私协议加固**：经原 SDK 的 controller 工具通道测试 `reflection_content`、`</antml:` 两种痕迹；均记录原已消耗请求/用量而拒绝落盘可重放正文。endpoint 密钥与私有思考不进入公开输出。

## 独立执行结果

| 范围 | 结果 | 证据（`runs/shared-engine-production-2026-10-18/independent-review/`） |
| --- | --- | --- |
| Company 不同 agent 自建反例及空证据正例 | 9 通过 | `company_probes.py`、`company-probes-r6.xml` |
| Company 当前 11 文件 CAS 候选原完整测试 | 158 总计，157 通过，1 原 Windows symlink 权限跳过，0 失败 | `company-full-r3.xml`；旧 `company-full-r2.xml` 仅为前一修复检查点 |
| 原 SDK + 原 SQLite 隐私/来源重哈希/跨 OS 进程恢复/错模型 pack 不重发 | 5 通过 | `native_probes.py`、`native-probes-r5.xml` |
| 同一 5 项反例针对总控最终合并 native candidate | 5 通过 | `native-integrated-probes-r1.xml` |
| 当前合并 native session 原测试 | 10 通过 | `session-probes-r1.xml` |

跨 OS 进程恢复实际启动新的 Python 进程，并拒绝 socket 网络连接，只通过原 `get_research_visible_output` 读取第一次脚本 wire 请求的同一安全输出。该项证明安全输出可持久化恢复；不等于已完成 owner 过期 lease 后的标准答案 checkpoint 恢复，更不等于真实模型金融准确性验证。

最初 Company 全测从 IQS cwd 启动，原测试中的相对 fixture 路径报错。已从候选根正确 cwd 重跑完成上表；原失败 JUnit 作为执行失误保留，不冒充产品回归。另一次静态疑虑已撤回：当前 native session DDL 在 `quick_scan_research_output.py` 底部显式组合进 V23 tuple，并非漏建表；当前原 session 测试 10 通过进一步确认。

## 仍须纳入本次整节点的交付

1. 冻结并审查原 owner services adapter 和公开共享 Runner 组合入口，验证原身份、原题、日期、批准范围和预算贯穿到底。
2. 明确实际可用的 pack/多轮策略。当前所见单 work 多轮仅支持 1 个 question；不能因单题 2 turn 正例推定固定 3 题、12 题 agent 或其他 pack 工具轮都已接通。
3. 用最终合并源重新绑定 CAS，并复核未知结果、失败已计费、缓存复用、过期 lease 的真实拒绝边界。最终报告不得靠 `synthetic=False` 标签制造真实 owner 或金融资格。

本轮 0 付费 API、0 密钥读取、0 原仓/生产库修改。所有故障和恢复测试使用独审目录下的隔离数据；产物保留，没有绕过清理限制。

Company 的精确 11 文件源码范围已在同一整节点审查内签收，见 `company-scoped-acceptance.json`（CAS SHA-256 `7d3aa1bc8a38096859327b106443bc4a51fb9c824e329b56ad6970b1e09421e2`）。该记录支持及时提交已完成源码；它明确保留整节点 in_progress，不是生产全部接线或真实模型验收完成。
