# 施工交接规范

本规范适用于本目录的 F05-OWNER-MAINLINE-02、TH-IMPL-02、IN-IMPL-02。各包专属范围优先。

1. 先核验 `inputs.lock.json` 的 source HEAD 与 dirty 状态；从锁定 commit 的 tracked Git tree 创建各自新 Lab，不用源仓 working tree、未跟踪文件或既有目录。移除新 Lab 的 remote；只在 Lab 的专属分支本地提交，不 push。
2. 将 IQS `acb03e3` 的 facts/capability 文件作为只读接口输入。不同实现若需要改公共 schema、CLI 或 IQS 源码，停在 Lab 内并把建议作为 `open_items` 返回，不擅自改 IQS。
3. 开发采用行为测试先行：新增/改变的公开行为先有失败反例，再实现并跑该包定向单元、接口集成和隔离入口 E2E。只运行受影响测试及目标仓规定的提交前检查；不得为了包交付运行一小时全仓测试，除非该仓 `AGENTS.md` 明确要求 major checkpoint。
4. 测试只用合成 facts、临时 owner store 和临时 CLI 工作区。不能打开、复制或改动 `StockWiki` 源仓的 untracked data；不能把 synthetic 结果标为 real owner golden。Owner query 为 snapshot/replay 写入其 capture 属于接口语义，所以测试里的 `--root` 必须指向自有临时 owner root，不能指向 source 或生产路径。所有请求保持零模型、零搜索、零下载、零付费。
5. 仅清理由本 Lab、本测试明确创建且可证明位于 Lab/TEMP 内的临时目录；不得清理 source repo 的现有文件或别的 Harness 的文件。
6. 交付前由不同于作者的真实独立 agent 做一次最终审查，检查实际 diff、正反测试、公开接口、边界、错误/未知/partial、测试原始计数和清理。作者修完全部 findings 后，对最终 commit 做一次复审；把 reviewer 身份/agent 会话引用、检查 commit、finding 与修复写入 `docs/handoff/<PACKAGE-ID>/report.md`。作者自审不能冒充独立审查。
7. 每个包在 `docs/handoff/<PACKAGE-ID>/` 返回 `report.md`、符合 IQS `docs/implementation/parallel-lanes/handoff.schema.json` 1.0.0 的 `handoff.json`、测试命令与原始汇总。若 real owner golden/当前服务仍不可安全读取，诚实标 `partial` 或把它列作产品验收 open item；不要补造数据，也不要把 package complete 等同 F05/G4/G3 全项目完成。
