# 共享引擎生产接线整节点独立审查：第一轮

审查者：`/root/production_node_review18`；实现者为 `/root/mainline_map18`、`/root/native_research_durability18` 与总控，审查者未实现候选源码。此次为整节点中的阶段发现，**不是节点通过，也不授予生产、owner 或金融资格**。

本轮已读 Company 候选 10 个修改文件及原有任务、证据、事件、答案和恢复边界。交付基线为 `company-candidate-handoff.json`、`company-cas.json`，原 Lab commit `4cb4e3d1b9bcc4e662c73135339de9b51a991916`。StockQA 原子输出持久化和生产 adapter 尚未形成冻结交付，待一并审查。

## F01 / P1：摘要可把原合成证据重新标为公开证据

位置：Company 候选 `src/iqs_company_agent_lab/provenance.py` 的 `summarize_runtime_evidence`、`read_runtime_summary`。

报告核对了 evidence-board 文件与外层 run 的哈希，却没有把 board 的实际 epoch 与原始事件链绑定。独立反例保持原始 journal 完全不变，将全部 `.invalid` 证据 URL 换为 `public.example.org`，然后重算 board 文件引用、run 字节和 runtime summary。报告成功输出 `evidence_origin=fixed_public_context`。两种变体都复现：保留原 `run.evidence_epoch_sha256`，以及将该值也重算为新 board epoch。后一变体说明只增加 board→run 的自证检查不足以修复根因。

应修复为最终 board 内容、run epoch 和原始 journal 最后有效 evidence epoch 的一致性校验；同时覆盖正常初始 intake、后续新增和失效。不能通过修改独立反例或撤掉摘要来源校验绕过。

## 独立反例结果

`runs/shared-engine-production-2026-10-18/independent-review/company_probes.py` 共 6 个参数化测试，结果 **4 通过、2 失败**。失败均为 F01；已通过的反例包括敏感 native metadata 拒绝、部分观测不冒充完整 HTTP/费用、相同物理 ID 冲突拒绝、布尔 token 不冒充整数。JUnit：同目录 `company-probes-r2.xml`。所有数据均为原测试夹具产生的合成数据，0 模型/搜索 HTTP、0 原仓写入、0 密钥读取。

一次 PowerShell 文本管道读取 JSON 的辅助检查因编码转换报错，改为 Python 直接按 UTF-8 读取原文件完成检查；不计入测试结论。隔离产物保留在独审目录，没有尝试删除或绕开清理限制。

## 保留的范围限制

现有任务/报告仍固定 12 个题位和注册日界 `2026-10-14`。它们不是本轮新增缺陷，但生产接线必须明确注册范围，不能暗示支持任意题数或任意信息日期。原隐藏推理不得进入持久化；owner authority 和金融资格必须保留为独立准入判断。
