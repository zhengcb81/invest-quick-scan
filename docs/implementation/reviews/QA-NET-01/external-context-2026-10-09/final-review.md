# Phase111 独立集中审查

结论：**需修复，当前受审字节不批准发布**。两项 P2 均为边界成功判定/绑定缺口；未发现足以认定重复收费、unknown 自动重发或 native/external provenance 冒用的其他实质问题。此次覆盖完整 Phase111，在同一集中节点等待修复后复验；未实施任何产品修复。

受审基线为 StockQA `42a517c4bd6bc8219f926957c6c332944da3278a` / schema8，最终私有实现 `runs/n111a/qa` / schema13。scope 报备38路径、现存37路径；handoff由主控发布时生成。IQS六件消费者文件另列精确哈希。37私有源码已重新计算 SHA，全部与 `static/whole-phase-static-03/process.json` 一致；本审查仅写两件报告及授权独占反例运行根，不改产品、测试、PWF或原工件。外仓只读 Git HEAD 查询遇到 sandbox Permission denied，基线由冻结 scope/source-snapshot/主控回执提供，不将该拒绝当 clean 证据。

## 具名发现

**PH111-R1 / P2：MCP InitializeResult 必填 serverInfo 未校验。** `src/providers/external_search_provider.py:598–609` 只检 protocolVersion/capabilities.tools；关联200结果缺 serverInfo，或 serverInfo={name:17,version:null}，实际 parser 都返回有效 control，后续记 parse_status=ok 并继续 initialized、discovery、search 收费阶段。这不是任意 endpoint 派发问题，但“已成功初始化”的持久语义不成立。MCP 官方 schema 必填 serverInfo: Implementation，Implementation.name/version 必须为string。[官方schema](https://raw.githubusercontent.com/modelcontextprotocol/specification/main/schema/2025-03-26/schema.ts)。最小修复：返回control前验证必填字段类型，增加对应负例及合法2024-11-05/2025-03-26正例；不保存原serverInfo或重造通用客户端。

**PH111-R2 / P2：context/use owner 未强制同 generation。** `src/utils/quick_scan_external_context.py:246–252` 使用去掉generation的 `_identity_basis`；`quick_scan_external_journal.py:1000` 回读use也未比较检索与当前work的generation。独立反例使用实际fixture先完成generation1检索/Q09，再创建generation2 work/lease，显式向实际context与LLM绑定入口传入旧operation IDs；生成新的有效use proof，检索HTTP共1、模型HTTP共1。正式coordinator cache key已有generation，正常CLI未见该误复用，但实际owner边界可被直接绑定绕过。最小修复：context构建及持久use回读逐检索核同generation，保留同generation跨题与跨lease复用、不改旧receipt/hash。

反例位于 `runs/n111a/review-20261009-01`，由 `C:/Miniconda/python.exe -B -X utf8 -c <inline>` 在该新根执行，原guard+OS变量白名单、原HTTP边界替身，exit0、stderr空、无network-attempts ledger。serverInfo缺失/畸形均accepted=true；generation反例原1→当前2、old_operation_used/new_work_bound/proof_present均true。JSON报告保存实际结构输出、日志SHA与运行约束；复现路径如上，不把它作为事实golden。

## 实际验证证据

三批均实际终态 exit0、未timeout、执行源未变；分别保留原命令与process hash于JSON，不跨重叠批次加总：

- whole-phase-regression-01：17文件，**852 passed**，0失败/错误/跳过；stdout 165.36s，controller166.135s。
- whole-phase-adjacent-regression-01：**128 passed**，0失败/错误/跳过；stdout9.07s，controller9.876s。
- whole-phase-iqs-consumer-01：**111 passed + 216 subtests passed**，0失败/错误/跳过；stdout265.72s，controller266.366s。JUnit327包含子测试，不能称327独立测试。
- whole-phase-static-03：isort check、Black check、mypy src/ 均exit0；记录检查命令及37 before/after SHA相同。GREEN未覆盖上述新增反例，不能据此忽略finding。

## 审查覆盖与有限结论

核对原external retrieval→有界短context→实际同步/异步LLM→原HTTP模型来源/native短事件→使用proof→checkpoint2→public1.1→C06完整standard body/outbox→IQS ROUTE_02。schema8至13按真实旧DDL迁移并原子回滚；旧响应/原native receipt hash、旧checkpoint1不补历史。native/external-only/hybrid保持独立；检索route不是回答model；query/domain/path/identity/manifest/TTL/prompt受到冻结校验。MCP initialize、initialized notification、tools/list、tools/call分别通过原Q09 intent/单次dispatch/结算，无第二账本，默认未自动启用paid路线。

未知发送、费用/usage无法确认或持久化失败保留预留并停止，既有测试用可用合成key+HTTP替身证明不因撤钥假装“不会重发”；晚到模型仅保留response/model/账务，不能得到有效proof/checkpoint，旧lease已fence。已收到、已结算、TTL内的REST短证据可由新lease重新验证后在同generation复用，这是设计，不报作缺陷；MCP旧控制session禁止推进新lease，语义有别。

OS测试确实使用独立Python进程调用main_with_llm.py：5冷/暖组合、5已付费断点、6发送后未知断点、2缺key、3权威变更、3完整body/warm/seal，共24新OS案例、11真实强杀。恢复只推进可注入clock，由CLI recover_expired；测试没有先人工改work或调用恢复API。完整封包保留标准body与18条证据、原包/费用warm不变、无thinking/session公开泄露。思考仅从最终assistant正文提取；实际requested/resolved模型与原HTTP SHA保留。

IQS adapter是无I/O可信producer一致性检查，并不独立认证检索发生、定价或金融事实。合成身份/价格/HTTP替身只证明有限软件行为；没有真实provider互通、厂商计价、金融准确率、StockWiki golden/联合ACK或跨仓写授权验收。StockQA尚未发布，G3/F05/L03/TH-IN与200家公司live门均不关闭。修复改变受审字节后，需在本同一审查会话核新SHA与受影响回归，当前结论不会自动转为批准。

## 精确受审 SHA-256

| 私有 StockQA 路径 | SHA-256 |
|---|---|
| `.gitignore` | `b0c7a8302fd657b7a7aeafd6c3be522f9c149b762d5b7b4f14f215b8ba0d7a29` |
| `src/config/quick_scan_search_policy.py` | `22547408ab5951603bb46468179580d127cf2d3ea8666da4848a7d62838fe930` |
| `src/config/quick_scan_search_policy_v1_1.schema.json` | `01cbdd03b7fb6daaff509f0e7fc50c93e421ee8a923cd7e3b561c8003927b782` |
| `src/providers/external_search_parsers.py` | `3c422c2f70c02c8946a1a61fa85bd193857f331acb1f58ea79bbbe3c4cb2dfa6` |
| `src/providers/search_capability.py` | `5cbb8e47a3e2ccd6246aa6605fcc1db6856bfc375da7fc0ffad78fc815d8bfb1` |
| `src/providers/external_search_provider.py` | `b6caee938729325c197e5994c33a48a5899a580891c67669be0a23807b5669b2` |
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
| `src/utils/quick_scan_external_context.py` | `37dc9f98de2dc532292024c9b1d3fa0d5507efa7f3685cbef4abcf149d26191e` |
| `src/utils/quick_scan_external_journal.py` | `389add0fd0cc6f4af42237cc6150e5dbb7c048af4fc7dddd038688fdfae5d1d0` |
| `src/utils/quick_scan_mcp_journal.py` | `0410c385042657189c54eaede99d541aef5f61a42bb90c45dbed55224c4e577d` |
| `src/utils/quick_scan_work_transport.py` | `10720388611f067f6debe44c7c50f3c27ed14f1577e6efce7d99382027cf3a9b` |
| `src/utils/quick_scan_work_store.py` | `3ad67286d6936ffbd86d6c68c3531be01c771e5bdfc10df2df53218a5d5a5d49` |
| `src/utils/quick_scan_cost_resolver.py` | `fe66a49a2a81855b1fd03aa4e6b19d334d693ae3f11c2d79be37cfc932d77edb` |
| `src/runners/llm_runner.py` | `2457650741f9df843fa63fd4c340a39a4c3131220f257b6bc3d23c4cf2bfe3ea` |
| `src/core/models.py` | `9afc4263a36e564ecd425c2ed15e81ffc07b98b27e9501687b4333ff4d01cba1` |
| `src/core/qa_engine.py` | `53cc5c901c5a7dcda69b5c5fbf5c585675e6ca32556d7a49bf43af7b21683a94` |
| `src/utils/quick_scan_observation_context.py` | `8780ee2a04c32faa6ab1168e32943c18f8d2eaa2b9040747229e58e4a07bd812` |
| `src/utils/quick_scan_c06_adapter.py` | `3bbc02d429fe74ac059b3c7399b152ee47d836e7bc7c42280b00e790594b87f0` |
| `tests/unit/test_quick_scan_external_context.py` | `651e42183ea7cc0926b207bfe45676793c26c747e8f43e41a977dec70e08f9c3` |
| `tests/unit/test_quick_scan_mcp.py` | `0cda59b07fbe940d1a742518ffb2c323d96e1691e55393476de827e85d55a1ec` |
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

机器可读命令、JUnit、process/反例日志hash与边界明细见同目录 `final-review.json`。
