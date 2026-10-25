# BASIC-BANK-EXPANSION-21 独立整包审查：Round 01

- 日期：2026-10-25；审查者：独立子 agent `/root/review_bank21`；实施者/总控：`/root`（修复后实施者另为 `/root/fix_bank21`）。
- 被审 HEAD：`046df087b4b3503aa4f765a076c469e4cb4de7c7`；源码逐文件 SHA256 固定在 `probe-results.json`。
- 结论：**CHANGES_REQUIRED**。以前报告的 AC-02/03/06 全通过声明范围过宽，至少以下 5 项反例成立。该报告保留初轮事实，修复后另写复审记录，绝不把历史失败改写为 passed。
- 权限：只读产品与外仓，仅在本 `basic-review/` 写证据；零网络/零 API/零下载。不代签 G5 owner，不授予金融或生产准入。

## 实际读过的输入与核查范围

施工卡、实施报告、PWF 最新节；主仓 `module_contract.py`（模块、registry、upgrade、release 校验）、`question_sets.py`（库校验、summary、manifest core 派生）、`routing.py` 最小题数、`scoring_rubrics.py` 版本/比较/分母；银行 `tools/validate_bank.py`、`banklib.py` 与关键测试；UI `scripts/build_data.py`、`adapters/paths.py` 与 `tests/test_catalog.py`。CodeGraph context 首轮返回历史 intake 同名符号，后续已限定实际 `scripts/` 路径并读已知源码，未以历史拷贝代替当前代码。

## 可复现发现

| ID | 严重性 | 路径/位置（初轮） | 最小反例与实测 | 根因/建议 |
|---|---|---|---|---|
| B21-R01 | P1 | `scripts/question_sets.py:94` `validate_library` | 合法 common diagnostic 扩展，`construct_id=null`、无 replaces；模块契约通过，但库校验 `AssertionError` | `expected_construct` 把所有 common 题都当 core。只对 common core 期望 id，其他 common diagnostic 期望 null；补整库扩张反例，并确保指标映射同批补齐。 |
| B21-R02 | P1 | `scripts/module_contract.py:131` `_validate_common_question`；`scripts/question_sets.py:443` `summarize`；银行 `tools/validate_bank.py:128` | common 诊断扩展 `critical=true` 被主仓模块校验接受；24 核心均 8 分时质量 8.0，追加该诊断题 1 分后质量 null；同题银行拒绝 `common extension must not be critical` | 主仓允许矛盾语义，消费端把诊断项当质量门。入口与消费端 fail-closed 拒绝 diagnostic+critical，覆盖 generic diagnostic 模块，不静默忽略真正关键风险。现存16个 diagnostic 题均 critical=false。 |
| B21-R03 | P2 | `scripts/module_contract.py:289` `validate_upgrade` | `3.1.0` 中存在 EXT，`3.1.1` 删除 EXT + 正确墓碑，竟被接受 | 删除扩展分支未校验至少 minor，只有 added 分支校验 minor。删除也应拒绝 patch，并保留墓碑累计/复用拒绝。 |
| B21-R04 | P2 | `scripts/module_contract.py:297` `validate_upgrade` | `3.1.0` 旧库含 EXT；`4.0.0` 删除 EXT+墓碑，同时追加 IQS_99 核心（24→25），被拒绝“major reserved for core changes” | extension_removal 分支没有考虑同次核心变化。至少允许因核心变更需要 major 的组合升级；保留纯诊断删除是否允许 major 的既有约定，测试分开。 |
| B21-R05 | P2 | UI `scripts/build_data.py:30` `EXPECTED`、`:355` `verify`、`:385` `main` | 当前 generated manifest 校验无错误；合法新增1诊断题使 `questions=223` 后，verify 返回 expected222/actual223，main 写前 exit1 | 构念数虽已派生，生成器还用历史全局总题数锁住扩张。将历史fixture哨兵与实际生产输入一致性校验区分，生产按 catalog/module 派生总量，补扩张build/verify集成测试。 |

复现：`python -B runs/reconcile-production-2026-10-25/basic-review/probe.py` 和 `python -B runs/reconcile-production-2026-10-25/basic-review/ui_probe.py`。输出分别是 `probe-results.json` 与 `ui-probe-results.json`。R01 用 `unittest.mock` 注入只增加一题的库及该题合法 diagnostic 指标映射，隔离数据准备影响；没有写 authoring 源数据。R05 直接调用 CLI 写出前使用的同一 verify 函数，未修改/重建外仓 generated 文件。

## 通过的定向观察

- 核心集合从 common 中 core role 投影；正常诊断 minor 追加被 `validate_upgrade` 接受。
- `routing.minimum_question_count` 在原库/加核心/只加诊断分别返回 24/25/24，分母派生真实存在。
- 固定比较的维度分数不会因合法诊断扩展而加权变化；但 R02 所述矛盾 critical 标记会意外阻断质量门。
- rubric 的 expected_core 从 basket 长度派生；显式 core map 能检查集合与维度一致；不传映射的内部一致性降级是施工卡约定，不据此虚构外部校验。
- module registry 发布路径逐版本调用升级校验、累积墓碑，历史题定义有 owner/hash 不可变守卫；R03/04 是该升级校验中的特定空缺。

## 测试与限制

初次运行 5 个目标测试文件：99 passed、117 failed、42 teardown errors、124 subtests；错误日志 `pytest-output.txt` 主要含沙箱原生 TEMP 的 PermissionError。此结果标为 **ENVIRONMENT_BLOCKED**，不据此推定产品有117个缺陷。已另用自有 `runtime-temp/` 固定 TEMP/TMP 重跑，最终结果另存 `pytest-output-fixed.txt`，待其结束登记。测试不得据实施报告原述冒充本轮实测。

未重跑主仓78分钟全套；未复刻旧AC-01逐字节探针（原报告所引 `.test-scratch/ac01_probe.py` 不在本轮交接证据中），因此本轮不重新断言所有历史产物逐字节无差异。实际题库内容没有扩张，现有基线通过也不代表扩张端到端通过。G5保持待所有者签收。

## 初轮测试后续登记（不改写上面的失败结论）

- 固定 TEMP/TMP 到自有根后：125 passed、43 failed、207 subtests，134.40 秒；43个失败均在临时发布 `os.link` 处遇到沙箱 WinError 5。日志 `pytest-output-fixed.txt`，仍标 ENVIRONMENT_BLOCKED。
- 后来启动的沙箱外基线套件与一次预冻结修复套件，按总控“等全部最终源码冻结再跑”要求中断，分别保留 `pytest-output-unsandboxed.txt`、`round-02-main-tests.txt`；二者**没有最终完成结论**，不可引用为通过或最终失败。
- 已清理明确自有 `runtime-temp/` 与 `runtime-temp-unsandboxed/`；默认沙箱 Temp 的45个日志配对路径仅做只读核对（`cleanup-empty-dir-proof.json`），当时均不可见/不存在。对其没有执行删除，不据此宣称跨进程临时环境全部恢复。
- 一次以日志正则集合生成递归清理目标的请求被自动审批拒绝，原因是不能充分证明每个推导目标均属本测试；没有执行该删除，未采用间接方式绕过。遵总控要求后续不清理默认 Temp，由总控按需只读核实。
