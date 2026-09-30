# S03 刷新后独立审查

- 审查日期：2026-09-27
- 审查范围：S03 问题源、DUR-04 版本拒绝与归档包回放、S03 计划范围测试
- 方式：只读；未修改实现文件，未运行测试或外部 API
- 结论：**当前 3.2.0 题库与归档包回放通过；P0/P1 为 0，P2 为 1 项范围限制**

## 审查结论

S03 的八个问题源和参考文件与先前核对的 C02 题义契约保持一致：24 个核心构念与 ID 保持不变，`IQS_05/18/20/21` 的 rubric 为 2.0.0，`PRE_REVENUE_04` 继续替代 `IQS_20`，兼容导出同步对应题义。除 `tests/test_question_sets.py` 外，这八个 S03 文件的 SHA-256 与前次审查相同；该测试文件新增了版本头拒绝和归档包回放用例。

S03 计划和验收用例均为 1.10.1。S03 `allowed_changes` 当前正好列出八个题库源、兼容导出、说明文档和测试路径；[`test_s03_change_allowlist_names_real_question_sources`](../../../../tests/test_implementation_plan.py) 现在用集合相等断言检查，不接受额外路径。

## DUR-04 与归档包回放

拒绝用例现在明确名为 `test_s03_current_manifest_rejects_an_unsupported_older_template_header`。它先以当前库生成 manifest，再把 `template_version` 改成 `3.1.0`，验证当前 catalog 不接受不匹配的版本头。这是正确的负例，证明当前 3.2.0 manifest 不能靠伪改旧版本头绕过校验；它没有把该产物称为真实的旧版 manifest。

归档回放用例把 `questions/releases` 复制到隔离临时根目录，另复制 legacy baseline，再在该根目录下以 `package_id` 生成新 manifest 并归一化答案。临时根内没有实时 `questions/catalog.json`、`questions/common.json`，也没有其他题库源文件；新 manifest 的质量分可正常算出。这个测试是有效证据，说明当前 content-addressed release package 可以在没有 live 题库文件时重建并归一化 manifest。

必须限定历史版本结论：归档测试取 `questions/releases/current.json` 的 package ID；对应 release lock 标记的 `catalog_version` 是 `3.2.0`。仓库所有 JSON 中都没有 `template_version` 或 `catalog_version` 为 `3.1.0` 的实际 metric manifest。因此，这不是旧版 3.1.0 manifest 的读取测试，也不证明某个真实 3.1.0 metric manifest 如何被读取或拒绝重解释。归档测试中将新生成 manifest 的版本头改成 3.1.0 仍只是合成错配输入。不得据此把旧 S03 receipt 宣称为当前 v2 已通过。

**P2 范围限制：**仓库没有真实 catalog 3.1.0 metric manifest fixture，旧版本 manifest 的读写兼容路径尚无真实 3.1.0 数据验证。该限制不否定当前 3.2.0 归档包回放，但审查结论仅覆盖上述回放能力，不覆盖真实旧 receipt 的兼容性或刷新结果。

## 验证记录

审查者未运行测试。当前隔离日志记录 S03 选择器 6 tests passed、plan tests 80 passed；计划验证结果按任务所有者提供的状态为 true（103 tasks、327 cases）。归档日志的 SHA-256 为 `BD1D357FF60F7064E5989A4B9A8425F9B3607D060409BF4EC22931A7BD4963C9`，计划测试日志为 `9833ABDA9090EFF7E20B8C7422F07DE206C7AF00174DC416469B50CE5A812F8D`。旧的 `validation-S03-refresh-after-S06-2026-09-27.log` 仍记录旧 selector 集合，未用它证明新归档回放测试已运行。

## 审查字节 SHA-256

| 文件 | SHA-256 |
|---|---|
| `questions/catalog.json` | `252DAB9E3F71868A71147ECB7DAC64CC187D7D56002B28B266A74F406FACAF10` |
| `questions/common.json` | `6900922FC077B0558DF49631C2F79E7677B2888C159D29E230D269F23ADFDBE3` |
| `questions/types/pre_revenue.json` | `DF9A8C51AE1B330AD22A1FD0B035A3DF9A6D536140DD8D8F1A12DC4104B1F55C` |
| `main_questions.json` | `1A21260B972784E94870006E4F47C74C4AD5804CE21269F10FABD2E2FFB7FC9B` |
| `docs/durability-and-change-design.md` | `7063A474B897B79646AD69C0B8F0332281E05763344336223E2836A75CFCD2EC` |
| `references/buy-side-questions.md` | `34DAA33665449CE26F0CD356BE05E7D57F8109E66E4377139AE9354C275A2A2D` |
| `references/common-framework.md` | `651A81A3A332C9E29F796DD7F8C1A179B2AA6ED9F7A788E5BCD1C82F88A068BE` |
| `tests/test_question_sets.py` | `07E70B3863A6BDA5EC2CCBFAA25AACC92B4B2D5EA49A766A3DBCD9D8B0A686F2` |
| `docs/implementation/tasks.json` | `7510806D1937183EC86364DF559D5AC6443EBB30139779A922AAC77BDFDB8BD9` |
| `docs/implementation/acceptance-cases.json` | `C405815A7D541A0A3F22C2EAF9A75EFAB4EE7362FD2C8257414E1287208D7A8B` |
| `tests/test_implementation_plan.py` | `FE04104FEA629858845B44D4AB489A1C0D09BDA508824919487044B150D93687` |
| `questions/releases/current.json` | `8950DC3FA28B287AE5E9E7E0B3775360659F3A74A78107664D6B2C5EB5EBE985` |
| `questions/releases/packages/pkg_24f07923f23cf0a2be5d7fb4b36a11925c779a8f4a68bdc9c81457084ded080f.json` | `284BE44F2C67F91E3359A038425579682052F1BDAB67CFA426390EE8A468F7AA` |
| `questions/releases/locks/modrel_18c097b26b82746d3b48d9f2da4858a15ce216bce39c2572d10c2dcef23d32b9.json` | `E755ED9557BB78EAACD4318CCFF2036F69F51A54DE96C8C55FCDDCEA095B5CA6` |
| `docs/implementation/contracts/validation-S03-DUR04-archive-2026-09-27.log` | `BD1D357FF60F7064E5989A4B9A8425F9B3607D060409BF4EC22931A7BD4963C9` |
| `docs/implementation/contracts/validation-plan-S03-allowlist-2026-09-27.log` | `9833ABDA9090EFF7E20B8C7422F07DE206C7AF00174DC416469B50CE5A812F8D` |
