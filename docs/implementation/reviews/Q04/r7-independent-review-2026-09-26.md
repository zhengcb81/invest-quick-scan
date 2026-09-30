# Q04 route-recovery r7 独立复审

审查者：`/root/q04_r6_review_retry`。结论：**本次四文件修复范围通过；Q04整体仍为partial**。该结论针对下列最终SHA-256快照，未把此前r6的76项绿测或中间r7的113项绿测冒充最终验收。

| StockQA文件 | SHA-256 |
|---|---|
| `src/utils/llm_integration.py` | `484EEC0A246C93DF0D38EAB2A6DAE33B4E76EA43BD8CC46178B50B9749136581` |
| `src/core/models.py` | `16C4A24C2204DF83E9AEC75706AA85EFC697306D8188846AFC47DE930BE3F589` |
| `tests/unit/test_llm_integration.py` | `DBA955A39DFEC02D33859383EBA10C9351C87E07486DB931A4FB8F06C59A9518` |
| `tests/unit/test_models.py` | `8DD428176294246F774B1592D8A0C48B98E1765B08A7220BA5F5A2F6BDEA8BDC` |

独立复审在单一隔离TEMP副本运行`test_llm_integration.py`、`test_models.py`和公开CLI测试：**114 passed**，3.16秒。生产路径探针使用`OrderedSearchProviderCascade → QAEngine → QABatchResult.to_quick_scan_dict()`，验证首选429、备用模型评分8分时公开状态为`completed`；首选429、备用模型无结果时为`insufficient_evidence`、`score=null`且公开派发状态为`completed`；发送后超时不明为公开`uncertain`。Black和`git diff --check`通过，测试前后四文件hash稳定，TEMP副本已清理，API变量/live opt-in已清除，无真实模型请求或费用。

本轮先有3个固定红测对应原P1，随后备用模型无结果的边界又给出1个红测；最终四项新增回归随114项suite通过。Q04未完成的持久化重试、跨进程配额、运行中策略热更新、StockWiki配置闭环及真实StockQA联网E2E均保持开放，不能由本次范围内通过推导为整体完成。
