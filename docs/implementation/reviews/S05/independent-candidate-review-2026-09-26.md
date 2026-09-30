# S05 首版候选独立审查

审查者：`/root/question_audit`。结论：**needs_revision，复现5项P1**；S05尚不可标verified。审查范围是本仓模块发布、组合、历史解析与标准答案/比较入口，不包括S06候选分类器或跨仓产品接线。

审查者独立运行`tests/test_module_registry.py`，12项全部通过；在唯一TEMP根、临时CWD和禁网络/禁子进程审计钩子下，另用真实公共函数复现以下五项缺口。TEMP已清理；审查前后126个文件SHA-256零变化。本仓原候选完整suite`258 passed, 148 subtests passed`仅证明原测试覆盖内通过，不覆盖这些反例。

1. **跨公司误报方法变化**：同发布包、同题义、仅实体不同的两份`standard-1`问卷具有相同`method_id`和`semantic_sha256`，但`build_observations()`把实体相关`prompt_sha256`放进观察方法hash，`compare(..., "company")`返回`method_id_changed`。
2. **标准答案入口接受篡改问卷**：向已发布manifest的题面追加无证据给10分指令并重算题面/回执哈希，`validate_manifest_metric_contract()`会拒绝，`build_observations()`却接受，因为没有调用权威发布清单校验。
3. **历史答案依赖当前schema/题库**：临时改变当前可编辑`answer-content.schema.json`后，旧发布manifest仍可按归档验证31题，`build_observations()`却用当前schema拒绝历史8分；`validate_observation()`也从当前题库找定义，观察未绑定发布包。
4. **连续两次合法退役被拒绝**：半导体题从3.0.0→4.0.0→5.0.0两次替换、逐版累计墓碑，`validate_upgrade(4,5)`通过，但`publish()`把3→5当相邻升级检查并误拒绝。
5. **模型擅自启用手动投资视角**：`pricing_lens`声明manual，profile没有用户选择，模型候选路由仍可选入并导出25题，manifest复核也通过。S05必须在组合入口核验静态激活权限。

候选审查快照SHA-256：

| 文件 | SHA-256 |
|---|---|
| `scripts/module_registry.py` | `E5042401E757D606391F4646C351038320350AA5D238945F465E26C62B3CF023` |
| `scripts/question_sets.py` | `186C8137DF1B1D03937AA977DC23F4079C0742F4B0E5A4A9834327FEC52A3E9C` |
| `scripts/standard_answers.py` | `BA0CDC5A2A5C1ACC5C4963699395752F10D9C7779C3F8E970469897980B03275` |
| `scripts/module_contract.py` | `069D14199239BBFC0B38AAD88F360228D5FC0A2F6CA324C037850FD2FA183A97` |
| `tests/test_module_registry.py` | `5199DFF65B7E2CD0D8C3885CA75296142E798858F2FBD7D85F13B5B9C8076D74` |
| `questions/releases/current.json` | `7B2CC8B5A827424B25CBC29F7EAACF4ABAB9AF386F96145E832542B5BF3D7FDE` |

实现代理须把五个反例做成固定红测，修复后以新hash重跑目标及全量suite，再请求独立复审；本报告不能用作新版本的通过回执。
