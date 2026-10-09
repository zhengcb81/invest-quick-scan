# Phase111 独立集中审查复验

结论：**两项 P2 均已关闭，批准所列冻结源码的有限软件发布；无新增代码阻断。** 这是首次集中审查的同会话修复复验，首次 `final-review.md/json` 及原独占反例脚本/日志原字节保留。第38件 handoff 已在本会话全文核验，无新增阻断；最终结论覆盖38件报备交付路径（37件源码+该文档）及6件IQS消费者的精确字节，不是金融事实或联合验收批准。

## 具名发现关闭

**PH111-R1 / P2 / closed。** `external_search_provider.py:598–611` 在有效 InitializeResult 成功前验证 serverInfo 是dict，name/version 是string。未存远端标识，未扩大客户端或账本。独立复验6类缺/坏字段均拒绝，合法结构接受；实际MCP入口每例仅一次初始化HTTP、synthetic spent=3000 micros、reserved=0，重开后零重发且无模型attempt。两处原合法fixture补serverInfo以免其他负例被新校验遮蔽；保留原协议、ID、capability、SSE/session边界。

**PH111-R2 / P2 / closed。** `quick_scan_external_context.py:251` 与 `quick_scan_external_journal.py:1010` 都比较原检索work_fingerprint.generation与当前item.generation。独立直接build和实际LLM绑定，generation1→2均在模型HTTP前拒绝：model HTTP=0、新answer attempt=0、账务不变。合法fresh generation2新搜索/模型已先获有效proof；随后重哈希旧retrieval引用，持久read_use拒绝。此持久反例在独立guard进程直接调用新增测试函数，不声称另行设计了第二个DB攻击。

合法同generation恢复未被收窄：独立复验先使旧lease过期，由recover_expired+新claim恢复，旧worker发送被fence，新lease重建并复用原已结算短检索后实际模型HTTP成功、当前lease proof有效，搜索HTTP仍1。整批既有跨题/跨lease测试仍通过。未收到、未结算、未知或费用缺失证据仍不能复用；迟到模型无有效proof/checkpoint/public结果；MCP旧控制session不能推进新lease，与REST短证据语义有别。

## 实际执行与字节核验

- RED `whole-phase-review-red-01`：exit1、9 failed/0error/skip，9例均DID NOT RAISE；当时产品src与首次受审字节相同，新增测试已存在。
- 中间 `whole-phase-review-green-01`：exit1、3 passed/6 failed，六MCP实际已拒绝，失败是fixture原猜`mcp_control_failed`与实际`mcp_control_unusable`不符。最后仅纠正错误名断言并格式化，保留单次收费/重开零重发断言；不把这次当通过。
- 最终 `whole-phase-regression-02`：实际exit0、未timeout，**861 passed，0失败/错误/跳过**；stdout145.23s、controller145.863s、JUnit145.012s。9个新增边界case均在该JUnit实证通过。
- `whole-phase-static-04`：isort/Black/mypy src/全部exit0、未timeout，mypy61源；37 before/after同SHA，非scope support未变。
- 保留邻接实证128 passed（stdout9.07s/controller9.876s）与IQS111 passed +216 subtests（stdout265.72s/controller266.366s）。6件IQS及邻接test_question_sets字节未变；JUnit327包含216子测试，不当327独立测试。没有无意义重跑这些未变消费者。
- 独立 `runs/n111a/review-20261009-02`：新断言wrapper，原guard/strip env/HTTP替身，实际exit0、stderr空、3.223s、网络尝试0。6个MCP实际入口、两个跨generation入口、同generation新lease正例、持久回读负例均断言通过。原review-01程序/日志未改。

37件当前源码独立复算SHA全部等于static04 before/after及regression02 executed hashes。相对static03仅3个产品函数所在文件及2个unit测试变化，其他32件未变；IQS6件重新计算与首次报告及消费者执行hash一致。精确命令、process/日志/JUnit SHA及独立wrapper SHA见JSON；检查既有执行结果，不以intent替代通过。

首次全链路审查覆盖继续有效：external retrieval→有界短context→实际sync/async LLM→HTTP provenance→use proof→checkpoint2→public1.1→C06完整standard body/outbox→IQS ROUTE_02，schema8到13真实迁移/旧receipt不补历史、native/hybrid区别、冻结query/domain/identity/manifest/TTL/prompt、每次MCP阶段单独原Q09 intent/派发/结算、unknown与存储失败不重发、lease fence，以及24新OS场景中的11实际kill和完整body封包。此次变更局限已定位边界，最终整批重验受影响路径。

批准只覆盖合成HTTP和价格环境下软件行为及所列字节。没有实付API、真实DB/公司文档/密钥读取，没有厂商定价或互通验收，不批准金融准确率、StockWiki golden/ACK/跨仓授权，不关闭G3/F05/L03/TH-IN或200公司live门。审查者未实施产品修复或外仓发布。外仓基线仍由冻结输入/主控提供，原只读git查询sandbox拒绝未视为clean证明。

## 精确最终 SHA-256

| 私有 StockQA 路径 | SHA-256 |
|---|---|
| `.gitignore` | `b0c7a8302fd657b7a7aeafd6c3be522f9c149b762d5b7b4f14f215b8ba0d7a29` |
| `src/config/quick_scan_search_policy.py` | `22547408ab5951603bb46468179580d127cf2d3ea8666da4848a7d62838fe930` |
| `src/config/quick_scan_search_policy_v1_1.schema.json` | `01cbdd03b7fb6daaff509f0e7fc50c93e421ee8a923cd7e3b561c8003927b782` |
| `src/providers/external_search_parsers.py` | `3c422c2f70c02c8946a1a61fa85bd193857f331acb1f58ea79bbbe3c4cb2dfa6` |
| `src/providers/search_capability.py` | `5cbb8e47a3e2ccd6246aa6605fcc1db6856bfc375da7fc0ffad78fc815d8bfb1` |
| `src/providers/external_search_provider.py` | `c8abe1cdf2a14c3b7028135b50a84c65509bdbc62ebd60dc37e11d97c79af8b9` |
| `src/providers/llm_client.py` | `35daa05ebdbf365309d153c105691566bb43c90c6652d65ba9c652814fd862b6` |
| `src/providers/base_llm_provider.py` | `5be39671dbcae89a63ca0496212c0eb05688bdc3e624f26aada948107c53ca08` |
| `src/providers/llm_provider.py` | `958abf8cae858f8dec040f1d8c1ff4e5e2236933979293c4b866aff89b39a99c` |
| `src/providers/async_llm_provider.py` | `f34ce6ef75be3bf3a3870d1a9076f61af55bb1fa7e7a5d27b494446d4ed86b6b` |
| `src/providers/model_resolution.py` | `37a3d602c4982cdab731a72f50bd5daebac7208d7496968825079c9082db62ce` |
| `src/config/quick_scan_model_resolution_v1_1.schema.json` | `0ce1f3a3f32fbd119f448d7470af28a835653db792bc3409d04e466e6aacc6c3` |
| `tests/unit/test_model_resolution.py` | `7f561bfa4502b9f1488e904f20cbc69bd416edc4ae378fc9ce571c5c94e28800` |
| `src/utils/llm_integration.py` | `ac61cb067b0de62e1ca7fc5021fa4d520693a5e921474ebaf51832c34d118032` |
| `src/utils/http_client.py` | `10048cc98b5c86d69d36e6e5f987afc3096f98c10d328f523f712947aeab6cc4` |
| `src/utils/quick_scan_evidence.py` | `b5160a277dd906c25634602362c14d29df2202b388c04d5e3d04760e1ece118e` |
| `src/utils/quick_scan_external_context.py` | `22ef4cffcb26f2fc758f697417fb983a461539d197df6a205a5c96a6662665b5` |
| `src/utils/quick_scan_external_journal.py` | `da86401022745e8d796faee6dfa5e86b28190b6256f6c3393c02e515257df4c0` |
| `src/utils/quick_scan_mcp_journal.py` | `0410c385042657189c54eaede99d541aef5f61a42bb90c45dbed55224c4e577d` |
| `src/utils/quick_scan_work_transport.py` | `10720388611f067f6debe44c7c50f3c27ed14f1577e6efce7d99382027cf3a9b` |
| `src/utils/quick_scan_work_store.py` | `3ad67286d6936ffbd86d6c68c3531be01c771e5bdfc10df2df53218a5d5a5d49` |
| `src/utils/quick_scan_cost_resolver.py` | `fe66a49a2a81855b1fd03aa4e6b19d334d693ae3f11c2d79be37cfc932d77edb` |
| `src/runners/llm_runner.py` | `2457650741f9df843fa63fd4c340a39a4c3131220f257b6bc3d23c4cf2bfe3ea` |
| `src/core/models.py` | `9afc4263a36e564ecd425c2ed15e81ffc07b98b27e9501687b4333ff4d01cba1` |
| `src/core/qa_engine.py` | `53cc5c901c5a7dcda69b5c5fbf5c585675e6ca32556d7a49bf43af7b21683a94` |
| `src/utils/quick_scan_observation_context.py` | `8780ee2a04c32faa6ab1168e32943c18f8d2eaa2b9040747229e58e4a07bd812` |
| `src/utils/quick_scan_c06_adapter.py` | `3bbc02d429fe74ac059b3c7399b152ee47d836e7bc7c42280b00e790594b87f0` |
| `tests/unit/test_quick_scan_external_context.py` | `a9f74b5c43f37bb31f96282b238ac2286bbbe9782db3304c83e734699bb9b130` |
| `tests/unit/test_quick_scan_mcp.py` | `2db56552b9811ef5b65f10e1d60deed9002e84a29a658fe23ec6d5d01897578a` |
| `tests/unit/test_quick_scan_work_store.py` | `4274fa165b1448283027e1201d126ac3bba6699107c9d92c01813ea40f4260b6` |
| `tests/unit/test_quick_scan_budget.py` | `d40dc9f4176e26e6ee83194636d8cc366b42081f377cd55fb7e47022629c7e06` |
| `tests/unit/test_qa_net01_search_boundary.py` | `dda382bb1a6114898600d7a8b06341e344949f22ecd412068fe104a5a8e942aa` |
| `tests/unit/test_external_search_provider.py` | `c4e6a43fd5ae4ee0257020d03bca698f3876b19986b548e7f793a371dc54a3da` |
| `tests/integration/test_external_context_cli_e2e.py` | `cbffeda38940e5ed7eb85c1a4d9982146b5b8298f1a3c07816a35a25e199abc7` |
| `src/utils/quick_scan_result_outbox.py` | `f71b9aefae6381f7f75d8c10cdbdc2701b5849a806accc4cc6fa2dfc7315ee2e` |
| `tests/unit/test_quick_scan_c06_complete_seal.py` | `483d884c98dd68d289c0bec7fcc758c088e31c32ea6dce6face6fe6e7eeb0939` |
| `tests/unit/test_qa_net01_c06_seal.py` | `91a7892a34bbcbff0a0b367bce2e828921d41bf04541638cb77a267e323c983a` |

| IQS消费者路径 | SHA-256 |
|---|---|
| `scripts/stockqa_adapter.py` | `0b1f8d8a28a9b797a6aaecf4b7dbbfdc56d709ab36f60c65cc1fac3f39a82928` |
| `scripts/routing.py` | `40d0a011dc56fd44387b887ceea272cffff9c8cb8b5268bb630f3d96d67f87ad` |
| `schemas/quick_scan/route-decision.schema.json` | `685949ec73c9eb4579382f69a1369cb856d66790b9978b4f6eb4e6f0a9778894` |
| `tests/test_external_search_result_contract.py` | `64850778e2dd6813598b1e1ed222683edb61b5da2bbbfdae7fc632a06c2b387f` |
| `tests/test_stockqa_adapter.py` | `6d67ca0589c91e4f930d03bf311d62eaa3b60e7d197175c6bcdb2a48bdcd66c5` |
| `tests/test_routing.py` | `d80c39f9300088190459aec640c58578ebc9191a7b1984c2b92c152f009029c6` |

首次报告原字节：`final-review.md` SHA `d99438a4f667ea688b1ee8c4660cf687dbd523ee9eec3265c51daa082532b5f9`；`final-review.json` SHA `40759e173c55cca019ad159311d85e05ac1d3f49f2dbb21f3404017bde677756`。
独立复验wrapper SHA `d91880fc62364c1ee926b3d702a8f48e825621959613edf849ab80ae63ed88f9`；所有运行仅本独占root写入。

## 第38件交接文档同会话核验

主控生成的 `runs/n111a/qa/docs/handoff/QA-NET-01/external-context-2026-10-09.md` 已全文阅读，SHA-256 `600110573428bbde761772949735dae0e05d14020ed1e0dbe886da5eac3026b9`。范围/版本、MCP逐HTTP收费、requested/resolved模型、generation及lease复用、unknown停机、晚到模型与控制session界限、实际验证数量与未关闭门均符合最终源码和执行证据，无新增阻断。文档不在static04的37源码检查集合内，单独记录内容核验与哈希；JSON的publication_artifact_hashes恰为全部38报备路径。未实施任何发布。
