# S02 MiniMax / 混合提供商消费者独立复审

复审日期：2026-09-26  
范围：只读审查 `scripts/question_sets.py`、`tests/test_question_sets.py`、`references/stockqa-integration.md`；未编辑源码或测试，未调用真实 API。

## 决定

**通过本轮指定的回执验收。未发现阻断问题。** 现代路由回执缺少完成结果、缺少最终实际 provider、或最终 route trace 与成功结果矛盾时，导入结果会 fail closed，不发筛选分数或审核回执。混合路由不能靠只保留最后一条“直连”attempt来使用旧单 provider 兼容分支。StockQA 的单 provider 离线 CLI fixture 也实际通过导入验收。

## 核验结果

`_check_screening_execution()` 在 [question_sets.py:1017](../../../../scripts/question_sets.py:1017) 起检查 `dispatch_outcome`；它通过 `.get()` 读取字段，因此缺失和显式 `null` 都会被认作无结果。凡任一 attempt 有 route 标记、存在 dispatch outcome，或批次 provider 为 null，执行都会进入 modern 校验；最终 provider/model 必须完整。携带 route 标记的回执还必须在最终 attempt 上提供 route ID、ordinal 和配置引用，route trace 的末项必须是匹配该 route 的 `accepted_answer`。缺少或非 completed dispatch outcome 会被拒绝。

指定的负例在 [test_question_sets.py:686](../../../../tests/test_question_sets.py:686)–737 和 [test_question_sets.py:739](../../../../tests/test_question_sets.py:739)–782：覆盖失败 route trace、缺最终 provider/model、非 completed/missing dispatch outcome，以及“此前存在 routed attempt、最终 attempt 删除路由标记并伪装直连”。常规套件的 dispatch 负例将该字段设为 `null`；我另做了无文件副作用的内存探针，直接删除该字段，导入器同样返回 `unusable`。四个探针结果分别为：缺 dispatch outcome、缺最终 provider、`provider_failure` trace 配 completed dispatch、prior cascade 伪装 direct，全部拒绝且分数为空。

直连兼容条件有独立覆盖：[test_question_sets.py:739](../../../../tests/test_question_sets.py:739)–750 保留固定单 provider、仅 provider 配置别名、无 route 元数据且 `dispatch_outcome=null` 的旧回执。更关键的是 [test_question_sets.py:854](../../../../tests/test_question_sets.py:854) 起的跨仓 fixture 配置单个 OpenAI provider，导入真实 StockQA 的 parser、answer generator 和 `main_with_llm.main()`，只在 `http_client_manager.get_sync_session` 边界注入固定离线 Responses API 回包；整个 manifest 经真实 CLI 输出后由 screening consumer 成功导入，筛选分数为 8，状态为 `screening_checked`，正式深研仍是 `not_accepted`。该用例同时检查 CLI prompt 与 manifest 绑定、attempt HTTP 200、输入题目哈希、cleanup 与 StockQA bytecode 快照无变化。

[stockqa-integration.md](../../../../references/stockqa-integration.md) 所述兼容规则与实现一致：单 provider 旧回执可只带 config alias 且无 dispatch outcome；任一 attempt 带 route 标记时按现代路由校验，必须有最终路由身份和 completed dispatch。文档也明确说明这些离线测试没有证明真实联网或来源准确性。

## 验证和隔离

在唯一短 TEMP 根中运行完整 `tests/test_question_sets.py`：CWD、`TEMP`、`TMP`、`TMPDIR` 和 pytest basetemp 均位于该根，使用 `python -B`、`PYTHONDONTWRITEBYTECODE=1`、`--no-cov`、`-p no:cacheprovider`。结果为 **49 passed，107 subtests passed**。此外，四项上文提到的对抗回执以内存探针验证通过。两个唯一 TEMP 根均已清除；事后确认没有残留 `s02rv-*` / `s02p-*` 临时目录。定向 `git diff --check` 通过，StockQA 交叉仓 fixture 未触发源码 bytecode 漂移。没有 live network、LLM 或费用调用。

复审开始和结束时，三个目标文件均保持候选工作树的 `M` 状态；哈希与委托值完全一致，复审没有改动它们。

| 文件 | SHA-256 |
|---|---|
| `scripts/question_sets.py` | `EA0B27D45EDDC1C43FD57B69DA69AB22545A67F87E475960E168FD5CDB5C3B35` |
| `tests/test_question_sets.py` | `7B9BA65164B09C2AA40993BDFD6E4233207247F237A3CA89F24E82630A0F5107` |
| `references/stockqa-integration.md` | `F09BBDF7DBC432E80E885124695D0DB9372E19BE9A5D946374A1885AE092EB87` |

