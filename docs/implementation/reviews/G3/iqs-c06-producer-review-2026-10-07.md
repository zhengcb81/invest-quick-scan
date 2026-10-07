# IQS C06生产者集中只读审查

审查者：独立agent `iqs_c06_producer_review`。没有修改文件或执行测试/API。结论：IQS本地producer代码门通过，范围内无交付阻断；清理在审查时仍pending，主控之后另附真实receipt。不是StockQA消费端/G3/F05签收。

已核日志：35 passed、24 subtests passed；真实独立子进程CLI 11场景/31题metadata均exit0。两日志SHA分别`86dd38695263d42f88c6ce7ca6d7304d2d74d3b70ecac82e63b221e81c4e9542`、`bf4b11a0db78225c864a901ddb12641d6deefadcf0d969b3a79bac595328398d`。

- 对Git基线diff独立比较：metadata提取前后字段、方法尾码、scope/cohort、cutoff/run/发布绑定含义一致。qid与q.id来自同一映射；完整观察仍带原execution/answer/observed_at及原内容digest。
- authority先验证冻结发布manifest和包可发新观察，由同一helper生成metadata，按归档Observation schema验证。不造答案、执行时间或observation ID；身份只bind原字节hash，不签verified。
- 原文件SHA与canonical manifest/context/schema SHA分开；run精确五字段、primary/comparison约束、answer/observation/catalog三版本有一致性核验。
- staging在目标文件系统完整flush/fsync后exclusive os.link；已有目标不覆盖。单测注入link错误验证清理，实际CLI覆盖重放/拒覆盖/坏输入/目录/缺父目录并检查无staging残留。
- guard在导入producer前安装audit hook并跑canary；独立OS进程执行实际入口，不只调用main的替身。

## 限制

Python audit限制受监控网络/进程/registry和根外写；不限制任意读取，父E2E harness也未安装同一hook。不得夸称OS沙箱证明整个进程树无法读密钥/生产库。identity_schema/model_policy_schema仅声明及文本形状校验，producer/build字段由调用方声明；接收方仍独立核兼容与来源。

metadata等价单测共同调用新helper，独立旧含义证据也包括本次Git diff；detach测试没有覆盖所有调用方别名，源码deepcopy未见缺陷。输入为synthetic，不是StockWiki owner golden、真实公司结果或事实正确性证据。外仓embedded_answer反例和生产loader/store未纳入。

## 审查原字节SHA

| 文件 | SHA256 |
|---|---|
| scripts/c06_authority.py | ad2da1ce3ec1e16fc04d8b3a7298a7c209c583dcfa0df9d0cbf01d3bc7e60805 |
| scripts/standard_answers.py | dc4870362109e2cc19c9fdb98a15c688b43138c5e0d12cb4142b0c23098cf42a |
| tests/test_c06_authority.py | fb839deaf429076d21bd25d13add73d34e892f7f79b551a7a9a3ebd7567e06ce |
| docs/implementation/reviews/G3/c06_context_guarded.py | 62b09065d621fae267b3065039eb0c6e6cef10a93e1b4c95f7301575fdab2b4c |
| docs/implementation/reviews/G3/iqs_c06_cli_e2e.py | 0b4a513609abe2776361d8c859ddc70cde12654c340d7eea9f3771a6b372854d |
| schemas/observation.schema.json | 6344d2afc9e0d937e05baba8aef27ad15c91770ab7ecb2ddbd549e5ab4fb70ec |
| schemas/answer-content.schema.json | a83236c2aba50115038cd2d404d5810bd50791c2b3f089f252b77b6a6d322547 |
| docs/implementation/reviews/G3/c06-authority-v2-input-map-2026-10-07.md | 731996219adadd8cf3252d8a8f1a82ba40cf534cd915b81dff974f0d4dfb9c84 |
| docs/implementation/intake/G3/2026-10-07-iqs-producer/test-results.json | 6183c4cbfba70e0a759aca17e83861dccb54319b22b72812a63809afa71fff37 |

主控后续清理见[原日志与结果](../../intake/G3/2026-10-07-iqs-producer/test-results.json)、[cleanup receipt](../../intake/G3/2026-10-07-iqs-producer/cleanup-receipt.json)；原结果的cleanup_pending保留不回写。
