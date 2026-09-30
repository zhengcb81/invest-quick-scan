# G0 预审包（待独立审查）

**状态：pending。** 本文件由实现者整理，是给独立审查者的索引，不是审查结论，不冻结契约，也不放行M1。外部仓库已在用户授权后做只读复核，没有修改；基线报告仍只代表2026-09-22时点，最新源码观察单独记录并绑定工作树文件hash。

## 当前快照与计划

- 计划版本：`1.4.0`；`tasks.json` SHA-256：`CE8DA9B6468A1B79931BCDC71204689510725C2CB9C5650C1F3FA194904E8311`。
- 验收场景 SHA-256：`08FF3D678469FD0B65B26E6A7ECEBDE5E81DEB5B8B36B646522F832BC604BBC9`。
- 当前invest-quick-scan HEAD：`25b8d14316c06390450e5a1d8883583bfd039d0d`；工作区有用户/前序计划的未提交内容，不能以HEAD代表实现快照。
- 候选文件hash及逐卡回执、历史快照差异见 [`candidate-snapshot.json`](candidate-snapshot.json)。该manifest明确是候选快照，待审查通过后才能冻结。

## P00、C01—C07 状态

| 卡片 | 实现状态 | 独立审查 | 检查数 | 回执 | 回执SHA-256 |
|---|---|---|---:|---|---|
| P00 | `implementation_complete` | `pending` | 2 | `docs/implementation/baselines/receipt-P00.json` | `0D7CCCBAB76842AC7BD45E94E23242DA88FF18A0C34B0910A310842CE0EE5983` |
| C01 | `implementation_complete` | `pending` | 5 | `docs/implementation/contracts/receipt-C01.json` | `41C5308B510101F7783A548C7B402F045CCFA5775C9D3BF123B21DCDF107B0F8` |
| C02 | `implementation_complete` | `pending` | 7 | `docs/implementation/contracts/receipt-C02.json` | `E2EB563C7B69E28E35916DBC3BFB9D5E9B915E4789451DBF94F9383CB24EA139` |
| C03 | `implementation_complete` | `pending` | 10 | `docs/implementation/contracts/receipt-C03.json` | `89E5AB3631BF2317FCF44B866A38A0C2B34E3C13B3C7BCF13E7E1BBF4E36C230` |
| C04 | `implementation_complete` | `pending` | 12 | `docs/implementation/contracts/receipt-C04.json` | `D166254012CF78B552F8696F33FA66DD8A4743F81936253CF294E26CDBFCC240` |
| C05 | `implementation_complete` | `pending` | 20 | `docs/implementation/contracts/receipt-C05.json` | `DD429ED0FA0A831DA325ED9DDF31922E4FE6799D5372BA4C80EA87614A803ADB` |
| C06 | `implementation_complete` | `pending` | 16 | `docs/implementation/contracts/receipt-C06.json` | `C49650EF572BB639C86E1966E9073DA1B972293DF9502B31928FCC240709F914` |
| C07 | `implementation_complete` | `pending` | 17 | `docs/implementation/contracts/receipt-C07.json` | `83D791C0BC707FC1940EE5388AC744F09EECD28F4875484228BD6672B136DCBB` |

所有回执仍为 `review=pending`。C01—C07 的本地实现状态为 `implementation_complete`，不等同于verified或生产能力已经上线。

## 已有/复跑证据

- P00基线记录在 [`baseline-report-2026-09-22.md`](../../baselines/baseline-report-2026-09-22.md)，记载当时读取的StockQA/StockWiki/company-wiki版本与边界。原报告的 `BASE-02` 包含访问 `localhost:8080` 的探测命令；本次未重放该命令，也未从本地快照推断当前外部仓状态。审查者应判断该证据是否足以满足BASE-02。
- 为补齐C01—C03旧回执没有保存的原始输出，当前目录复跑身份5项、指标/优势变化6项、评分/规则8项及计划验证。原始输出见 [`validation-local-baseline-2026-09-23.log`](validation-local-baseline-2026-09-23.log)，SHA-256 `92D69A47EF13F8214FCD49881870FD1C351A20C4E47457206A6F61354262E500`。pytest各套件各有1条warning；需审查者从原文核对warning内容，不将其隐藏为skip。
- C04/C05/C06/C07原始命令输出分别位于：`docs/implementation/contracts/validation-C04-2026-09-23.log`、`.../validation-C05-2026-09-23.log`、`.../validation-C06-2026-09-23.log`、`.../validation-C07-2026-09-23.log`。各SHA与结果写入对应回执；当前实现工件hash匹配，C04—C06仅`tasks.json`及planning状态文件因后续卡片推进而与历史收据快照不同。
- C07最终复测：部署契约13、C06 14、C04 15、C05 provider/budget 16、model policy 9、计划工具41均通过；`implementation_plan.py validate`为73 tasks、162 cases、G6且 `product_tests_executed=false`。C07日志SHA-256 `5544FC7AE4667718CF70D5187508E606E1B5983A2358B3EB92764FA3EF56C3CE`。`E2E-05`已修正为实际selector `test_e2e_05_readiness_requires_evidence_from_same_release`。
- 随后全量本地回归`python -X utf8 -m pytest -q -p no:cacheprovider`通过：174 tests、106 subtests。原始输出在[`full-local-test-2026-09-23.log`](full-local-test-2026-09-23.log)，SHA-256 `4EB11DDFF90AC05BE83EFE2F4069E5BA9A99300170567C5B1721699F9182348B`。该全量套件仍只验证本仓离线行为，不替代真实搜索、数据库、provider、UI或跨仓集成检查。
- 机器比对发现P00与C01—C07任务卡的全部case IDs均能在各自回执中找到对应记录，没有缺项或多项；详见[`case-coverage-audit.json`](case-coverage-audit.json)，SHA-256 `F0BEEEF6BCB8ABA1AA369D0EE0666FABCD7AAC5CAECAED5719F98CB78E739C64`。该比对只证明映射齐全，不证明测试断言充分或独立审查已经通过。
- G0所列I01/I04/I05/I08/I12/I17/I18及BASE-02/REV-01/02/03的预期、证据与未完成项已逐项列入[`invariant-review-matrix.md`](invariant-review-matrix.md)；全部保留pending，供独立审查者逐条复核。
- 依赖图预检表明，在P00及C01—C07实现后，唯一ready任务是G0；64项任务的传递依赖包含G0，且无其他未完成的iqs任务能绕过G0。详见[`dependency-gate-audit.json`](dependency-gate-audit.json)，SHA-256 `09EBB404C49C188A787D0D1C2C66AADED41F5F8BD10BD195175BF55B3170C778`。
- 本地完整性预检验证了8份回执JSON、65个已有输出hash引用、C07的10个快照hash和本包10条相对链接；零不一致。详见[`integrity-audit.json`](integrity-audit.json)，SHA-256 `285653B02466DCD90571957E3622387E8389636D8203D557426E928931CD5793`。依赖审计与当前计划hash一致。此项同样是实现者预检，不是独立审查。
- 全部11份本地JSON Schema均通过对应draft的自校验；91条本地/外部URI引用全部在本仓schema注册表中解析成功，结果见[`schema-ref-audit.json`](schema-ref-audit.json)，SHA-256 `B1AD0784F6412A09A181F8EACFE00483627060F1CEE5E99F46E6D06BC7790AFF`。这证明schema拓扑完整，不证明跨仓消费者已实现或兼容。
- 最新外部工作树的只读接口观察见[`external-interface-snapshot.md`](external-interface-snapshot.md)。该材料用逐文件SHA-256绑定StockQAbyLLM、StockWiki、company-wiki及两个研究skill的实际源码，并明确当前缺少搜索工具载荷、评分端到端传递、统一发行人主键及quick-scan消费入口；这些是下游实现缺口，不能被写成已上线能力。

## 供审查者重点核验

1. 以 `tasks.json` 与 `acceptance-cases.json` 为唯一预期，逐卡复述 C01—C07 的身份、评分、规则、时效、模型费用、交换查询及部署边界，再检查最新代码/schema/fixture/日志是否满足每项正反例。
2. 检查每个事实/配置/工作状态只有一个写入owner，尤其StockWiki名单与轻量观察、StockQA问答与费用、company-wiki原件采集、研究技能只读消费之间没有共享可变状态或文档落盘。
3. 核对 C06—C07 所有 `contract_versions` 名称和版本在引用schema之间一致。实现者发现初始C07曾用 `model_policy`，而C06使用 `model_policy_schema`；当前已统一并有定向断言。检查其他字段是否有同类别名或单位/身份错配。
4. 从原始输出复现失败/skip/测试数量。不可用计划校验或纯离线策略函数替代真实owner仓库的运行测试。
5. 明确P00/C01—C03的历史证据缺口和跨项目快照时效；核对最新[`external-interface-snapshot.md`](external-interface-snapshot.md)中的当前源码事实，不把下游待实现能力误判为G0已经交付的生产能力。

本次结构核查注意：CodeGraph `codegraph_callers(assess_readiness)`返回“无调用者”，但源码测试通过`import deployment_contract as dc`后直接调用`dc.assess_readiness(...)`。这是跨文件别名解析的索引局限，不是测试未覆盖的证据；独立审查者应以[`test_deployment_contract.py`](../../../../tests/test_deployment_contract.py)中的实际调用和原始测试结果为准。

## 已知自审修正与待解决事项

- C07 canonical schema引用曾重复内嵌，令绝对路径约束没有施加到响应分支；已统一引用`ProcessIdentity`/`ComponentStatus`并通过相对路径负例。
- C07 `contract_versions` 初稿曾与C06模型策略键名不一致；已统一成 `model_policy_schema` 并重新生成fixture/hash、测试和回执。
- C07任务卡E2E-05曾写错selector；已绑定现有测试名并重新校验任务清单与测试。
- C01—C03收据原来没有原始输出文件/hash；本预审包补充本地重跑输出，不改写历史收据。
- C04—C06规划文件hash漂移是后续任务推进结果；请只依据每卡自身工件、日志hash和可解释规划演进，不将后续planning变更误判为代码快照漂移。
- G0独立审查正在执行；StockWiki/StockQA等真实入口、数据库、provider/search、费用和UI联调证据仍未产生。只读源码核查不能替代owner实测；在审查结论落盘前G0保持pending。

## 审查记录栏（留给独立审查者）

- Reviewer / review date / reviewed snapshot:
- REV-01 result and evidence:
- REV-02 result and evidence:
- REV-03 result and evidence:
- BASE-02 result and evidence:
- Findings (id, severity, trigger, expected, observed, fix/test):
- Decision: pending / needs_revision / verified:
