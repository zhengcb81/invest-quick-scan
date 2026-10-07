---
name: invest-quick-scan
description: 通过开启搜索的 StockQAbyLLM，为全球上市公司编排快速评分与非评分事实画像。24个核心判断配合公司类型、行业和生命周期追问，保留周期低谷与反转观察；采集产品、产业链、供应商客户和管理层等短结构化事实，支持公司、时间与模型比较。不保存公司文档，不替代完整盈利预测。
---

# 上市公司快速扫描：评分与事实

本 skill 维护问题内容、分类路由、评分口径与离线编排。LLM 调用、搜索、提供商配置、重试与缓存复用 `C:/Users/郑曾波/Projects/StockQAbyLLM`，不在这里另建客户端或财报下载流程。

保持轻资产：只保存结构化问答、分数、简短依据、来源链接和必要运行信息，不保存财报、公告、网页正文或其他公司文档。company-wiki身份关联和StockWiki结果导入不能成为问答前置条件。

## 通用模板优先

先读 [买方核心问题清单](references/buy-side-questions.md) 和 [分析方法与适用边界](references/common-framework.md)，查看 [通用问题源文件](questions/common.json)。[main_questions.json](main_questions.json) 是自动生成的 StockQAbyLLM 兼容通用模板，包含全部24题及独立评分锚点。用户提供的 `main_questions_sample.json` 仅保留作参考。

核心清单回答八组经济问题：客户与生意、竞争与利润归属、执行组织、资本回报与财务真实性、治理与每股价值、生存与永久损失、成长与再投资、价格与回报实现。公司类别改变指标口径，不能取消这些基本判断。

杜邦和五力是可选诊断模块，只有回报来源或竞争结构存在具体疑问才追加，不默认占据快扫篇幅、不重复计分。财务真实性、普通股东权益和资金生存是关键核查题；重大问题或证据缺口不能由其他高分抵消。高杠杆、低税率、早期阶段或市场集中度本身都不等于高质量。

周期低谷和暂时经营困难另走[恢复观察](references/recovery-watch.md)：区分当前表现、正常化能力与恢复假设。保留低分，同时展示仍有的优势、修复证据、资金时限和普通股受益条件。质量白名单不能成为所有研究候选的唯一入口。

新版评分仅以24个核心构念及类型替代题汇总可比质量分，行业/阶段/属性题保留为专题评分，不因追加题数改变核心权重。使用[统一行业与阶段口径](questions/scoring-contexts.json)，分清当前、正常化、压力和未来假设；新增题义/口径与旧结果不直接连成趋势。

模块独立扩题、证据化路由、发布版本锁与增量补扫的后续实施见[组合式题库设计](docs/modular-question-bank-design.md)及S04—S06/Q13/W15/F06/U04任务卡。现有组合能力可直接使用；设计中的独立升级契约和跨仓接线尚未完成。

事实画像读[标准输出与事实题库](references/standard-output.md)，按需编排[facts.json](questions/facts.json)中的61题。供应商、客户、设备、材料、上下游、第一/第二曲线及管理层均有稳定字段与关系约束，未知留空、不评分。题库已可离线使用，生产facts执行/入库仍须F02/F04接线。

## 执行

1. **确定对象与时间。** 固定公司法定实体、证券代码、交易所／股类、信息截止日；估值另固定报价日期与币种。证券简称或代码有歧义时先消歧，不默认上市地区就是经营地区。
2. **检查外部工具。** 读 [StockQAbyLLM 接入](references/stockqa-integration.md)、[联网搜索与LLM统一规范](references/search-and-llm-playbook.md)及[搜索接入状态](references/search-policy.md)。区分原生搜索与外部证据context，验证实际执行证明；结果不明先对账，不盲重发。公开CLI的`--require-search`仍仅使用已接入供应商；直连探针不等于生产接通，缺证明或证据不足时留空分数。
3. **用 LLM 分类。** 依 [路由规则](references/routing.md) 通过同一上游工具发出分类问题。检查实体、类型、行业、阶段及可确认的business_subtype，写入profile；entity_id/security_id由身份拥有者确认，不让模型自由创造。分类是评分和事实的共同入口，不重复收费做两次相同路由。
4. **离线编排。** 使用 `scripts/question_sets.py compose`。通用框架先出题，再由类型替换不适用的会计题，加行业、阶段与有实质影响的属性题。只读 [目录](questions/catalog.json) 和命中的模块，不一次性装入全部题库。
5. **逐题联网回答。** 导出的questions.json复用StockQA的加载/执行接口；标准模式先核实其原生score/fact解析能力，不把旧外层5分协议套到事实题。保持ID、截止日、评分锚点/事实关系与结构化约定；只保存短依据和来源，不下载报告。StockQA每次另附真实执行时间、请求/实际模型、搜索回执；正常fallback成功即停，显式模型对照另设有预算比较组。
6. **验证与画像。** 依 [评分规则](references/scoring.md) 检查来源、日期、口径、反证和上游错误，再用 `normalize` 生成结果。先展示重大问题与未确认的关键事项，再列八个维度、逐题分数、证据和最值得追问的三件事。同时展示`recovery_watch`的状态、优势、原低分与待验证条件；即使质量分为空也不隐藏。企业质量、成长机会、当前估值和恢复观察分开，不能汇成一个买卖结论。

标准模式用`standard_answers.py build`绑定manifest/题面/执行回执，不能交给旧normalize。独立来源审核仍不可省；结构通过默认为unreviewed。存入StockWiki不可变观察，由每次scan快照引用新旧observation_id，保留原时间和模型。比较前检查[全局契约](docs/system-contract.md)，不将模型换代、回溯回答或重新导入解释成公司变化。

模型顺序由用户填写[配置模板](examples/model-policy.template.json)，数组顺序即优先级；配置与运行状态归StockQA。各模型的接口、能力和脱敏探针记录在[提供商连接配置](examples/provider-connectivity-profiles.json)，其中只记录环境变量名，不保存密钥值；该文件是连通性目录，不代表StockQA端到端验收，也不自动决定顺序或启用派发。并行独立题目/获准题包，遵守全局、账户组和单模型上限；共享五小时额度拒绝、逐题检查点及结果不明处理见[模型策略](references/model-policy.md)。本地仅做配置校验，生产并行/接续仍须实施Q04/Q06—Q10。

## 本地命令

在 skill 目录运行；这些命令不联网，也不读取密钥。

```powershell
python scripts/question_sets.py validate
python scripts/question_sets.py routing --company "公司全名" --ticker "证券代码" --exchange "交易所" --as-of "2026-09-19" --output "runs/routing_questions.json"
python scripts/question_sets.py compose --profile "examples/profile.json" --mode quick --out-dir "runs/example"
python scripts/question_sets.py normalize --manifest "runs/example/manifest.json" --answers "runs/example/raw_answers.json" --review "runs/example/evidence_review.json" --output "runs/example/portrait.json"
```

标准评分、事实及三维比较的离线命令见[标准输出](references/standard-output.md)。新模式依赖requirements.txt中的jsonschema；不含客户端、密钥或调度器。首次生产运行、自动/手动加公司、持续维护和简洁UI统一由StockWiki入口提供，仍待[跨项目实施包](docs/implementation/README.md)接通，不能把本地编排成功称作一键扫描已上线。

`examples/profile.json` 是虚构的路线演示，使用时替换为真实分类。`quick` 保留24道核心题的全部判断，并加高优先级专属题；`full` 展开所选模块。两种模式都不自动增加杜邦和五力。实际题数在manifest中列明，不承诺固定执行分钟数。多业务集团按有实质影响的分部单独选题，不用最大收入分部代表全部业务，也不在本skill中做SOTP。

修改评分问题编辑questions/源JSON，再运行common命令更新兼容导出；事实编辑facts.json，并运行standard_answers.py validate-library。prompt引用的统一口径/schema必须进入manifest hash，不能只更新文字而不记录版本。

当前评分catalog 3.2.0含222题，核心仍24题，事实题库1.0.0含61题。新manifest为3.0、标准观察为1.0.0；旧2.1运行保持原汇总，缺执行元数据标legacy_unattributed，不补造时间或模型。股票池数据库、持续运行与生产UI仍按实施路线开发；本skill的离线代码不是外部运行平台。
