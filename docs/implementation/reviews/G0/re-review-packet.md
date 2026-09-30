# G0 整改复审包

**状态：等待独立复审。** 首轮审查结论见[`independent-review.md`](independent-review.md)，其决定为`needs_revision`。本包只索引整改后的本仓离线契约证据，不宣称外部owner仓的生产能力已经实现。

## 绑定快照

- 计划版本：`1.5.0`
- `tasks.json` SHA-256：`B79165011746B7639C300A190D068F0625A9AD3AA8A1AAB9F08C0EC3E1D963B4`
- `acceptance-cases.json` SHA-256：`9272881EC0E50E73BFF143164BCA7E27D9F09A34E9E44567F14B21EEDC2960BC`
- Git HEAD仅作为基线：`25b8d14316c06390450e5a1d8883583bfd039d0d`；实际复审对象以[`candidate-snapshot.json`](candidate-snapshot.json)逐文件hash为准。
- 整改回执：[`remediation-receipt.json`](remediation-receipt.json)，SHA-256 `D1C270818F86396083C17F072DAE46206B37025B7854BFF9154D773B53BB10E5`。
- 原始验证输出：[`remediation-full-test-2026-09-23.log`](remediation-full-test-2026-09-23.log)，SHA-256 `0DFFF6259A37C496EF3ED81889521C55B2AFE0B2DA640C10406C1046C2ABB3A4`。

## 首轮发现的整改入口

| 发现 | 整改入口 | 复审重点 |
|---|---|---|
| G0-01 | score schema、`validate_parsed_answer` | 非scored不得有分；高检查等级必须有可信回执 |
| G0-02 | entity/universe/work语义校验 | 父子实体、scope、去重计数不可漂移 |
| G0-03 | C01-C03测试与C05-C07新contract cases | 测试调用公共实现；离线证据不得冒充生产case |
| G0-04 | exchange schema | v1.0.0扩展为空，正文无法嵌套逃逸 |
| G0-05 | deployment schema/helper | 先完整Schema校验；readiness由证据闭包计算 |
| G0-06 | query语义校验 | 状态、coverage、score lineage和profile实体一致 |
| G0-07 | metric/rule schema | 诊断项不进核心评分；空复合规则拒绝 |
| G0-08 | `independent_support` | 遍历完整、无环、无缺失的祖先闭包 |
| G0-09 | candidate manifest与外部快照 | company-wiki issuer index事实已纠正 |

## 已执行验证

- `python -X utf8 -m pytest -q -p no:cacheprovider`：181 passed，108 subtests passed，0 skipped。
- `python -X utf8 scripts/implementation_plan.py validate`：73 tasks，171 acceptance cases，G6；`product_tests_executed=false`。
- 11份JSON Schema完成对应draft自校验；34份实施/schema/example JSON可解析。

请复审者直接读取最新源码、schema、测试及原始日志，逐项确认九项发现是否关闭。若仍有问题，继续给出触发输入、预期、实际和所需回归；只有全部阻断项关闭后才能把G0判为`verified`。
