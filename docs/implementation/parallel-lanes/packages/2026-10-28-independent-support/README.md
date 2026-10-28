# 2026-10-28：两个独立产品组件施工包

本批只发布以下 **2 包**，数量来自实际产品缺口。旧的离线 COMPARE-PLAN、UNIVERSE-DESK、TEST-SLICE 候选已撤销，未创建 Lab，不派发。分层测试本身已由 `scripts/run_tests.py` 实现，本批不重复施工。

| 施工卡 | 唯一可写 Lab（启动前再次确认不存在/无人写入） | 具体产品增量 |
|---|---|---|
| [UI-COMPARE-28](UI-COMPARE-28.md) | `C:/Users/郑曾波/Projects/iqs-comparison-view-lab` | 可嵌入正式结果 UI 的多公司×动态题目矩阵、日期/模型轴、原始记录和结构差异解释 |
| [UI-UNIVERSE-28](UI-UNIVERSE-28.md) | `C:/Users/郑曾波/Projects/iqs-universe-import-ui-lab` | TXT/CSV 上传、逐行原身份候选人工选择、原单实体 preview/明确确认/apply 的前端组件 |

两包可同时交不同 harness，互不读取对方未交付内容，唯一写目录完全不同。主 IQS、StockQA、StockWiki、现 UI 仓库、共享 PWF/配置/数据库均只读。**总控唯一负责最终把组件合入原 UI 和必要 gateway；本包交付不等于已接生产。**

每个 harness 开始先读本卡、[共同交接规则](handoff-rules.md)、[输入锁](inputs.lock.json)、[批次 manifest](manifest.json)。锁含 raw 工作树 SHA256/字节数、冻结 commit、Git blob OID 及 blob 原字节 SHA256；这些值不能混用。21 个输入文件是全部上游参考范围，不读取真实答案、名单、运行目录或 key。根目录路径是部署上下文，代码不得硬编码作者机器路径。

## 为什么确实需要

- 现 `product_core.js:134–150` 的 `comparisonRows` 仅按 qid 并列两边、固定 `comparable:false`；`product.js` 的 history 是单一公司选两条 observation。没有生产多公司×题目矩阵。旧 thin_compare 是固定历史草稿页面，不能当作正式库组件。本卡仍不授予金融可比性。
- 现 `product.js:529–575` 是单公司 picker→preview→apply，没有文件上传或逐行歧义选择。StockWiki 已有唯一身份与幂等成员 API，candidate-import 仅候选暂存；本卡复用这些能力，不建第二套名单/身份库。
- recovery 结果视图和测试分层已经存在，不另做同名工具。

## 完成标准与集成边界

工作顺序仅三个大节点：输入/写根确认→完整 TDD 实现及本 Lab mock E2E→**真实不同 agent 集中全面审查，修尽问题后 passed/open_findings=[] 再交接**。不为每个小函数新增审批或审查门。能力缺口写明 `integration/host-patch-proposal.md`，不得虚构已存在 HTTP endpoint/owner receipt。

允许本 Lab 合成 mock 服务仅绑定 `127.0.0.1`：COMPARE 默认 18771，UNIVERSE 默认 18772；端口冲突退出，不杀他人进程、不接 8765/8766。可完全内存 mock；不得调用真实 owner/API/模型，不下载依赖或资料。组件测试环境、进程、端口必须 finally 清理。

## 原交接公开预检（只由总控执行）

本 `manifest.json` 含原 CLI 所需 `packages[].id/lane_id/task_ids/write_scope/readiness`；handoff 仍严格为原 schema **1.0.0**，独审扩展挂独立文件，不向旧 schema 添加未知字段。示例由总控在 IQS 根运行：

```powershell
python scripts/parallel_handoff_cli.py --input C:/Users/郑曾波/Projects/iqs-comparison-view-lab/docs/handoff/UI-COMPARE-28/handoff.json --package-id UI-COMPARE-28 --catalog docs/implementation/parallel-lanes/packages/2026-10-28-independent-support/manifest.json --verify-references
python scripts/parallel_handoff_cli.py --input C:/Users/郑曾波/Projects/iqs-universe-import-ui-lab/docs/handoff/UI-UNIVERSE-28/handoff.json --package-id UI-UNIVERSE-28 --catalog docs/implementation/parallel-lanes/packages/2026-10-28-independent-support/manifest.json --verify-references
```

worker 不运行 IQS/源仓脚本；在自有 Lab 用冻结 schema 验证形状。上面 exit0/valid 仅说明原公开预检所覆盖的形状/引用，不证明独审真实、产品接通、生产/金融门关闭。总控还须核实际文件、审查调用、测试、hash 与独立集成。当前状态是施工设计，未派发、未实施、未验收。

