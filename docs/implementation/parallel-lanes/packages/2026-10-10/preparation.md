# 2026-10-10 新并行施工包编制记录

状态：编制中；不是派发或开工回执。根 PWF 仍由总控独占。

- 用户要求提供几个不会相互影响、可独立交给 harness 实施的大施工包；原“实施全部 PWF”目标保留。
- 当前总控正在独占 IQS 的 `runs/c15a`，实现完整 C06/W15 查询及真实执行前主体绑定；StockWiki 与 StockQA 的对应生产接线保留给总控，不派第二 writer。
- 已发布工程基线：IQS `8d57f2ae1855d8105fa8abaccfef13ed2ff090ce`；StockWiki `a5a97d6efbf5f0ee79122a1ec375def388700690`；StockQA `6aafc32eae5339668e893b8a2b246d0655075584`。三者均须在外部 harness 开工时重新核验，观察不是锁。
- 私有 query v2 的 62 个合成契约测试通过，但尚未审查或生产发布；不能作为消费者的已签收公共接口。新只读 owner reader 的第一次 RED 为缺模块导致 collection error（实际 pytest 2，1 error，2.03 秒），不是已执行的产品反例，更不是金融准确性证明。
- TH-IMPL-01 / IN-IMPL-01 仍受 G3、F05、W11 与真实公共 owner query/golden 前置约束。本轮不重做预研、不以总授权代替证据门。
- 历史 wave2 的 EVID-LAB-01 已交付；新的候选包应补真实准确性参考或独立运行支持，不重新实现其离线评测、生产 HTTP 客户端、搜索器、缓存、费用和 outbox。
- 旧 lane-manifest 中的 owner 根目录与旧授权措辞是历史记录，不能用其 `local-skills` 路径或逐文件等待覆盖本轮实际源仓与人类全部后续授权。
- 读取时误猜 `docs/implementation/handoff-2026-10-04.md`，文件不存在；当前权威交接为 `docs/implementation/handoff-for-new-agent.md`。未写入或执行旧入口。

选包原则：真实未完计划、有稳定只读输入、独占工作目录、可在未闭合的 query/facts 门之外交付有用成果；最后仅在包级集中测试/审查，不增加每个小节点的关口。

## 实际核查与选包

- 新一轮只读核查：Lab `codex/evid-lab-01@2c0efb6370e401ca84d5f23cd5047de2bbfdec0a` 原工作树 clean；Theme/Industry 原 HEAD 与历史相同且 clean。计划的新 `iqs-fact-content-lab` 不存在。它们不是目录锁，分派前仍应确认唯一 writer。
- 用户明确选择“建立 CodeGraph 索引”后，已实际运行 Lab `codegraph init -i`，exit 0，30 files / 611 nodes / 581 edges。随后真实 Git 状态有新增 `.codegraph/.gitignore`、`.codegraph/config.json`，均为本次索引基础设施，不读密钥、不覆盖旧交付、不并入产品提交；新包应保留这两项，并记录与产品范围分开。
- 只读独立拆包建议已收：本轮两个大包足够有价值。`EVID-REF-02` 补可复查的真实参考事实和评测资料；`FACT-CONTENT-01` 补61题事实内容、歧义术语、方向/时期/分部和严格/探索语义的可执行验收资料。
- 不新增第三个重复的 UI/备份/强杀恢复包。Phase111、SW-READY/SW-REPAIR 的原已验收场景保留；也不在不稳定 query v2 上搭假的消费者实现。
- Lab 当前旧 README 的零网络约束属于 EVID-LAB-01：新 EVID-REF-02 只在其独立资料采集阶段允许 harness 的公开网页只读取证；旧 replay、guards 和历史归档继续零网络。新 CLI 仍离线，不扩外部 HTTP/LLM/搜索客户端，不调用收费 API。
