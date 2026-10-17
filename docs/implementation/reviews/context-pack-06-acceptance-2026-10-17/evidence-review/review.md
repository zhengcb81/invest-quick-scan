# CONTEXT-PACK-06 独立证据验收

审查者：本次工具实际分配的 `/root/accept_context06_evidence`。委托来自 `/root`；实施候选由另一实际 agent `/root/accept_context06_code` 维护。本审查者没有实现候选、没有自审自修。旧审查记录只作为原始来源保留，不替旧 harness 补造调用证明。

最终结论：`passed`，`open_findings=[]`，限于以下明确范围与执行限制。所有资格字段为 false。审查最终候选 package 1.0.1，原 1.0.0 来源记录的限制保留。

## 原件与输入

- 原件 authority：`../snapshot.json`，源 HEAD `169a6735c1ead2d8ece73e1d0776baecdaf398ca`，reviewed payload `54041e324003feecc7f66f915d294305d1df43b1`；metadata-check.json 独立读取逐文件 raw bytes，snapshot 全部匹配。
- 输入 authority：`../inputs.lock.json` raw SHA `968fc8a41653e24e0701feea9bc75353bff90e923ecd96f37f6b8334818d1233`。共享输入只读逐一核 516 行，0 mismatch；列出 68 个锁外文件，全部逐一保存 raw SHA/bytes。没有导入、删除或修复共享目录的 pyc。
- 数量纠正：366 个本 package 消费文件本来就包含 14 个锁内 pyc（evaluation 5、iqs/scripts 9），与共享目录 68 个锁外 pyc 不同。“干净副本”意为严格消费锁子集，不是 pyc 数量为零。原E01在自有副本另外注入 tools/cache/prefixes 的锁外 pyc。
- 独立执行仅用本目录 `payload/` 与 `clean-inputs/`，从 original/ 与干净 366 消费文件副本复制；没有从活动仓补文件，没有 SDK/模型/搜索/网络/生产 DB 操作。

## 已完成的独立验证

真实命令：`C:/Miniconda/python.exe -I -B -X utf8 <本目录>/audit.py`；`... <本目录>/metadata_check.py`；`... <本目录>/run_case.py codec`。audit.py 子进程使用显式最小 environment、自己的 HOME/TEMP/cwd，并装审计钩子拒绝网络连接、DNS/bind 与本目录外写。日志和 argv/exit/hash 为 `*.stdout`、`*.stderr`、`*.run.json`。

- 七个交接 plan：baseline/selected/四包实际分别直接调用冻结原 `company_agent_contrast.prefix_text` 复算，全部 byte equality；evidence_first 先逆还原再比原前缀，byte equality。每个 prefix raw hash 与 full validation context 均实测正确。
- CACHE：用四包真实文本与交接 scenarios 逐 scenario 调原 `iqs_cache_planner.analyze_prefixes`（经薄 adapter），每个内嵌原输出与旧例完全相同。没有重写账本/价格/前缀计量。
- CODEC：使用原 baseline/selected 实物各自的完整 validation_context_ref，均给原 12 题、原 board/schema/registry 与同一个合法 synthetic compact 答调用真原 expand，标准 answers 相同。把题集改成 selected 子集而仍用完整 context_ref 时，原件按 `question_hash_mismatch` 拒绝。
- 资格始终 false；字节投影和理论布局不作实际缓存率、价格、准确率结论。

## 关键实错

E01：原 `src/iqs_context_pack/frozen_deps.py:65` 的 `sys.dont_write_bytecode=True` 只禁止写，仍读取未锁 pyc。自有干净副本保持 `prefixes.py` 原字节/原 hash，仅在自己的 `__pycache__` 放 unchecked-hash pyc（源码原内容 + harmless 标记）。原 configure_frozen 成功、module.__file__ 仍等于锁内 `.py`、标记 `LOCK_EXTERNAL_BYTECODE_EXECUTED` 实际执行。见 pyc-injection.json / pyc.stdout / pyc.run.json。已直接交实施 agent 修复；没有对共享锁外 pyc 做执行推断。

## 旧交接证据限制（不改写历史）

- 原 artifacts.json 81 项有已知 1 项 task_plan.md hash/bytes 过期，其余 80 项匹配（总控 artifact-intake-check.json）。本审查没有修改 PWF。
- invocation-evidence.json 两轮的报告 raw hash 与实际 round 文件吻合。第一轮报告头 reviewer 为 `session-86bd9530743b`，调用元数据却为 `98a90d44-2733-4fa6-a17e-30e407e30496`；两轮缺真实调用时间，只有作者自录工具返回字符串，未附可独立核对的实际 harness 调用记录。不能由此独立证明旧调用真实性。
- final.json 的 round_files 无逐轮 raw hash（相同 hash 可从 invocation 文件交叉核到），handoff.final_head 为占位符；report.md 仍带草稿标题。这些是来源记录的局限，不应补写成已验证历史。
- tests.json 绑定旧 run-20261017T061242Z；源 Lab 实际保留的 suite-evidence 已是 run-20261017T070647Z。只读复制后发现五套 stdout raw SHA 全不匹配旧 tests.json，stderr 均为空匹配。新日志显示相同 64/0/0 计数，但不能充当旧 run 的原始日志。见 metadata-check.json 与 source-suite-evidence/。本次新候选必须另给真实日志并绑定。

## 范围变更与中断记录

等实施 agent 冻结候选后，核 final CAS 原件 before/候选 after；只读审查 E01 防御修复与实施 agent 已有来源测试记录，复核真实测试证据、输入保持与自有清理；正常复算旧产物兼容。总控在平台中断后明确收窄范围：不再生成或执行任何新的字节码、伪模块等对抗载荷。本审查者没有完成候选来源边界的独立对抗执行，不能把原版 RED 或实施者日志冒称为自己独立运行的候选 GREEN。不会重跑不相关的全部原 64 测试。首次 candidate CAS 检查因列表顺序 assert 停止，逐 path 再核 28 条实际一致，且停止发生在复制/载荷设置前，见 interruption-record.json。

## 最终候选复审结果

- 唯一最终 freeze：`../code-review/candidate.freeze.json` raw SHA `361f57824c34adc0bc08848cf4bb6a0ae8705e5b5fadbea609396dc701c2bc7f`。105 文件 / 1,344,117 bytes 全匹配；独立复制后再次匹配才执行正常兼容检查。29 项新增/修改的 before 来自不可变 original，after 来自实际 candidate；0 删除。源 HEAD 背景仍为 `169a6735c1ead2d8ece73e1d0776baecdaf398ca`。
- 应用 CAS：`../cas.json` raw SHA `85228d45a2798fea0139af28bcb3f2d7b58c184e7dab6a1f0292adf7bc9f5444`。逐 path 映射与 freeze 的 29 项 changes 精确一致，before/after SHA 与 bytes 无新增推断；列表排序不承载语义。
- 新版 artifacts.json 的 104 行全部实际 raw bytes 匹配（排除自身）。没有改写原 artifacts、旧 round 报告或旧调用记录。
- E01 以实现审阅及既有实施者测试记录闭合：`_SourceOnlyLoader.get_code` 直接读取 `.py` bytes 并编译，不调用会选取 pyc 的标准 get_code；CLI verifier 先验 raw SHA/bytes，再直接 `exec(compile(verifier_raw,...))`。所有 import 包括后续传递 source 导入受限定 root 的 finder 约束。已缓存的全部 consumer 源模块名预检覆盖 CODEC canonical 等子模块；实际 driver helper 按原优先级精确固定为 `frozen/iqs/scripts/company_agent_research_pilot.py`，路径在执行前核实，锁内 driver 副本同 hash。该静态来源闭合没有由本审查者新增对抗执行。
- 13 个上下文/关联反例的断言实质覆盖四种原输入变更、foreign plan、未知字段/mode/version/缺内容摘要/选题摘要/board 摘要、schedule 顺序及 prefix 引用变更。CLI 还从核锁的原输入重编译核 plan authority；纯 analyze 只验证自身和已提供 schedule 一致性，未被强加外部 authority。limits 继续复用原 SESSION，分析继续复用原 CACHE；可选布局保持无损边界。
- 嵌套字段类型检查先于 `.get`/索引复用，实际新增 RED 与集中 GREEN 记录保留。末次精确 helper pin 后只有 7 条正常 CLI 实跑；早先整组 92 passed 与其后 27 passed 受影响测试处在不同时间点，不能相加，也不称末次整组重跑。新 tests.json 明确这一先后关系。
- `final-evidence-chain.json` 独立核对 9 个保留的测试执行 record 与原 stdout/stderr bytes/hash；7 条末次 pinned-ok CLI 的完整 argv/cwd/UTC/exit 与所有流 hash 一致；harness 变换源/目标 hash 一致。它们是实施者真实运行记录的独立核对，不冒称由本审查者运行。
- 本审查者在最终候选自己的副本上独立正常复算旧 1.0.0 七例，全部 prefix byte equality / hash / full context 通过；原 CACHE 内嵌输出完全相同；真原 CODEC 使用两模式完整 context_ref 展开相同 synthetic compact 答结果相同。正常命令及原始流见 `candidate-{examples,codec}.{stdout,stderr,run.json}`。
- 最终输入再次核：original 86 文件全匹配；consumer 366 / 4,359,090 bytes，14 锁内 pyc、0 锁外文件；共享 516 锁行全匹配，原 68 锁外 pyc 的 path/bytes/raw SHA 与首检完全一致。没有导入共享输入。
- `cleanup.json`：清理本审查自有 558 文件 / 6,630,498 bytes，scratch 余 0；只保留脚本、原日志、来源局限与验收记录。全部 child 为同步短进程且已完成，无服务/端口；没有外根写入或真实请求。

最终结论不认证实际缓存率、价格、模型准确率或金融真值；没有跨操作系统实机测试。根协调者随后应用受审 CAS 并提交时，只需用独立 `source-commit-binding.json` 核 Git blobs 与受审 bytes 同一，不修改本次已签发 final.json 或重开产品审查。
