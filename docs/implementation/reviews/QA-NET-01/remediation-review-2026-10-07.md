# QA-NET-01 主线整改集中复审（2026-10-07）

本审属于同一大节点，未新增小节点门。基线为StockQA `d160d80dc2340c6fb6cef0453b289b5210cf2cb6`，整改提交为`84e24ef79901ce7c817054f6354b90a15c44afd3`。最终13件源码/测试已只读增量复核及hash绑定；本批原五项阻断及R1/R2/R3整改在所测范围内闭合，没有新的生产阻断。主线隔离公开完整检查六步全部exit0，pytest为982 passed/74.95s；本审已读实际日志，未独立重跑。整包仍为partial，external dispatcher、多scope完整闭环和真实跨仓导入/ACK不因本轮GREEN升级为完成。本审未运行测试、读取凭据、发HTTP或写外仓，写入仅为本报告。

五项阻断的修复方向成立：未实施external明确拒绝；reuse沿用原冻结routing；所有已有代次传入lifecycle；prompt升级优先处理未确定attempt；生产lifecycle仅claim，真实client HTTP逐次创建实际route/model/prompt的attempt及reservation，最终checkpoint绑定实际成功attempt。以下记录本批审查发现与已完成的修复，保留原反例及证据边界。

## 关键接线与可保留交付

- `src/runners/llm_runner.py:261-263,388-438`的production `transport_managed=True`仅claim；`QAEngine.process_questions:285-294`以dispatch_context绑定真实work。legacy synthetic生命周期探针保留默认行为；它们不是生产fallback正例。
- `quick_scan_work_transport.begin_quick_scan_send`在work已绑定时不再因own-reservation标记跳过HTTP准入。cascade为每次实际provider调用绑定真实route；现有prepare/mark/outcome冻结及预算门没有放宽。
- client在HTTP成功已落账后生成规范化final_receipt及trusted work_attempt_id；不是模型回答JSON提供的字段。checkpoint只调用store save，不重复record_response。store仍严格核同work/lease、成功phase、model/request/receipt hash，未修改store契约。
- 新`tests/integration/test_qa_net01_transport_e2e.py:217-250`使用公开CLI、真实provider/client/store，stub HTTP边界；在每次POST前断言不同模型/route的send_intent与对应预算reservation。正例断言A确定拒绝、B回答、B checkpoint/C06、warm0HTTP、attempt/package/budget不变。
- 正例失败费用由合成服务器明确model及完整usage与本地合成rate card核算。测试文档明确不是真实API、StockWiki真实身份golden或provider零收费保证。普通错误体缺usage仍暂停；不能宣传所有真实quota拒绝都会自动备用。
- 格式修复正例为既有legacy显式单route、无configured预算；configured v2的format repair仍关闭。该正例覆盖最终HTTP精确source set/hash，不能扩张为v2修复已可用。

## R1 [P1] checkpoint拒绝被吞掉，公开结果仍可声称成功

初审位置：`src/runners/llm_runner.py:403-434`；`src/core/qa_engine.py:293-300`；`src/runners/llm_runner.py:1539-1547`。缺private transport字段时直接return；preflight/store异常仅log后return。engine随后将scored结果加入成功，CLI仅检查answer错误计数，因此仍可能exit0。

无需伪造内部receipt的具体输入：服务器返回合法公司/qid/score和`description='x'*5001`，2xx、搜索及完整usage均有效。`llm_response_parser.py:289-291`只要求非空description，未限制5000；transport已经记response_available及费用，checkpoint preflight上限5000拒绝。输出仍scored/成功，但无checkpoint/C06；租约过期转uncertain，下一次不能warm复用。

修复应让“应保存的回答未保存”产生有界公开error/ProcessingError或等价的未完成回执，保持原transport状态与budget，不再次record或伪改unknown；缺authority但已保存checkpoint形成durable seal block是允许partial，须与checkpoint失败区分。真正provider失败/未知/预算deferred也应保持其原wait/失败语义。

现有篡改测试205-238只检查checkpoint没保存且attempt未变，未检查公开结果不算成功。建议把合法过长回答与公开持久化拒绝断言纳入本批既有E2E。

已修复：最终`llm_runner.py:417-454`对缺权威绑定、无合格最终receipt、preflight/store拒绝抛出有界ProcessingError；engine按既有失败路径返回error而不再计成功。新公开CLI反例`test_qa_net01_transport_e2e.py:380-396`断言5001字description导致exit1/error/null score，已收HTTP仍保持response_available，费用已结算，无checkpoint/C06，不二次覆盖状态。篡改attempt ID/model/hash三项改为明确断言ProcessingError，并保留原attempt不变。缺authority时checkpoint已落且seal durable block的既有partial未放宽。

收尾修正已核：oversize_description从首次调用就直接返回2xx的5001字符description，不经过原429分支；因此该公开负例确实验证checkpoint保存拒绝，没有靠预算deferred间接得到error。Q06/Q09两份旧测试保留原provisional身份和模型不匹配输入，只将预期修正为error/null score、无checkpoint、已有实际response_available及无重复HTTP。没有把provisional改verified，没有伪称StockWiki真实golden；Q09仍断言一次实际发送只对应一份预算reservation。

## R2 [P2] 失败usage缓存别名细节冲突仍可计价

初审位置：`src/providers/llm_client.py:825-854`新增coherent判断；`_normalize_provider_usage:653-690`优先选择input_tokens及其details。

具体冲突输入：`input_tokens=prompt_tokens=100`，`input_tokens_details.cached_tokens=100`，`prompt_tokens_details.cached_tokens=0`，`output_tokens=completion_tokens=50`，`web_search_usage.tool_usage=0`，model及rate card有效。现有顶层别名相等且details都是dict，coherent通过；normalizer只选前者，将100个输入全按缓存收费。另一明确别名宣称未缓存，费用口径矛盾，不能挑更便宜的解释。

建议比较两套已明确提供的计费细节或分别正常化后要求一致；冲突时保持failure_unpriced，备用0HTTP。沿用当前参数化失败usage测试增加一项即可，不新增审查门。

已修复：最终`llm_client.py:865-879`为明确双别名建立alternate视图，分别正常化后要求结果相等；缓存details矛盾使usage保持未知，不能选择低价解释。HTTP边界参数化case已加入conflicting_cache_details，继续断言只发primary、原拒绝确定、预算unpriced/reservation保留且无checkpoint。缺搜索计数仍传observed_search_calls=None，不补零；已有非零失败费用正例保留。

## R3 [P2] 私有receipt早退绕过公开helper的None资格契约

初审位置：`src/core/models.py:341-347`。发现private final_receipt就立即返回_sanitized_receipt，跳过原函数“未执行搜索/未完成/非2xx/缺身份字段→None”的契约。当前save有_preflight作为第二道防线，尚未看到该路径绕过store，所以不把它描述成已接受假成功。

仍需恢复helper的共同资格校验后才返回完整规范化receipt，以免弱消费者将非None当已验证。格式修复错误时`base_llm_provider._merge_format_repair_metadata`会继承initial.work_transport，失败metadata又覆盖response/search信息；private存在本身不能证明最终回答完成。本批可用未执行搜索、未完成、缺必需ID的private候选与repair失败继承候选验证None行为，不要求额外live实验。

已修复：最终`models.py:341-377`先把private规范化receipt作为共同资格校验候选，未执行搜索、未完成、非2xx、缺关键ID等继续返回None；合格后返回原规范化字典，保留usage及原hash。新增三项private候选反例覆盖unverified、incomplete和actual_model缺失。此次没有新增repair失败继承全链E2E，不把三项helper反例扩张为所有repair失败组合已实测；configured v2修复仍关闭，legacy已有正例边界保持。

## 五项整改和整包partial必须分开

F1失败关闭不等于external context已实施；F3/F4增量与恢复正例使用合成manifest、公开StockQA CLI，未运行IQS真实compose/StockWiki identity库；F5planner的unknown/in-flight拒绝与真实发送时未知态不能混为一个层级。新F2以真实client HTTP边界的two-route测试替代旧lifecycle“改actual_model但无真实备用attempt”的例子，不能为满足后者放宽冻结检查。

原验收的多scope全闭环、完整producer manifest锁、authority错误分类与真实StockWiki import/ACK边界仍按原partial留档；本次五阻断修复不自动升级全包完成。共享TEMP仅按名称/mtime删除的既往违规继续保留，当前隔离验证不能证明旧删除无损，也不重现删除。

## 最终源码快照及证据

主线本轮最终为13件源码/测试overlay；原7项未跟踪内容保留。以下13项是**实际执行的导出字节**，逐项从自有runtime读取，全部精确匹配归档`docs/implementation/intake/QA-NET-01/2026-10-07/remediation-export-manifest.json.overlay`；194件base允许文件冻结于d160d80。本次读取的运行/归档manifest SHA256为`db61e6d24dc633ec26dce0e47c231c0bd35fa3b113be1c46d08da80cd94d72d8`。后续补提交ref可能改变manifest容器hash，不能因此改变以下tested bytes/hash。

| 最终StockQA相对路径 | bytes | SHA256 |
| --- | ---: | --- |
| src/config/quick_scan_search_policy.py | 13018 | 021d1378bdd3ffcccac47198187a3f88855f553751d95cc25a543e1c52aa1763 |
| src/core/models.py | 22457 | d98f7613fcfabc0d5d1f1fe0b403eaa734a6948b8c9fad492a993f70bdf00cf1 |
| src/core/qa_engine.py | 17625 | 107fb5be6e5614f4aa7c38ec4140755d1f9e7ee2b448e456eb077e889204c821 |
| src/providers/llm_client.py | 49316 | c4cd7d6ce94d713d76de832df5173afe7b1037428c50a70991e63001946750f4 |
| src/runners/llm_runner.py | 78116 | 73d30b64e6ae527d26e9d03858e38a6e1e16e81a63d702d1cab7a87f01adc73f |
| src/utils/quick_scan_question_manifest.py | 15674 | 72d106709887eda10a506bd39012c4a2aae9eff280f9cfb97cce28374eb76734 |
| src/utils/quick_scan_work_transport.py | 20340 | 8c222e82b1640671493d3391a5172ee27a7d0207d49a38eac3adf3739c41c08f |
| tests/integration/test_qa_net01_cli_e2e.py | 19955 | c4f2ba57375cf7a2581e27eac92fcc8e35525e0727248b47782c21b81ef1f32e |
| tests/integration/test_qa_net01_transport_e2e.py | 18615 | dcf528a1954a105d9e17d6d82611ba2ac3fbca37ddffa400f62872ee39570a6c |
| tests/unit/test_qa_net01_question_manifest.py | 15415 | a011155c0e828f9afb56dccc980081b135d36498fa092ca61068bc2b298d9a63 |
| tests/unit/test_qa_net01_search_boundary.py | 23015 | f1649fe84d5a31b4d05d3dacd91503e10e8efc582654ad365dc5a8a3938dfbe4 |
| tests/unit/test_q09_budget_concurrency.py | 26411 | dae3c629f496bc68ce08e5ca14f86b7d596714ab4c7ace83c941bb1a97e43a3e |
| tests/unit/test_q06_work_binding.py | 22839 | 31b9143965cf72d8961f867ee9b2f96faa9bc31d33aa8711db5a4ba900569f0e |

提交前按StockQA既有mixed-line-ending hook将四件CRLF源文件规范化为LF，不能说这些提交源码与tested字节相同。本审已逐件读取整改提交`84e24ef79901ce7c817054f6354b90a15c44afd3`的13个Git blob比较：只有以下四件字节hash改变，`tested.replace(CRLF,LF)==committed`，其余九件字节精确相同。等价记录`commit-eol-equivalence.json`的本次SHA256为`e82d3dc955cfee1ab175ae40c059c1d7a9790806b9cf9c53361ebc6a4b1ab9bc`。未将换行等价冒称原字节相同。

| 路径 | 提交LF源码bytes | 提交LF源码SHA256 |
| --- | ---: | --- |
| src/providers/llm_client.py | 48054 | 8ab49e3456baf31cb121d156e77c604747e3f739356ba0764ffdebee84733226 |
| tests/integration/test_qa_net01_transport_e2e.py | 18191 | fd5582d1566c977df10bec8c60eef7a64a8992d2cc6b7e91ef4a5cc547800f30 |
| tests/unit/test_q09_budget_concurrency.py | 25763 | 3ec6b6d8bc57f0c0708f1f18ad4d444f162274c2961e20653001ac21457bf53b |
| tests/unit/test_q06_work_binding.py | 22226 | 71244f8ff887e1a9ac9eabc11bce04905d771acd064efd5e2b2c7788d1fc0126 |

`export_runtime.py`先按两个精确Git ref读allowlist/overlay，目标hash不符时只尝试LF→CRLF拼写，仍不符则拒绝；所有hash/bytes通过后才创建新的自有root。其本次SHA256为`f69f18c96d0b6c2ac9784be2a78cc55abd702ff308c5c4e183bda81c7ebde47a`。本审只读算法与提交blob，没有运行重建；不冒称已独立从最终commit重建并重跑。主线报备既有提交静态hooks全部通过、13文件精确stage、原七项未跟踪保留。

## 完整隔离检查与guard边界

本审读归档实际日志`remediation-full-green.log`：black/isort/mypy/bandit/pytest/smoke六步exit0，总85.81s，pytest为982 passed/74.95s。该日志2980 bytes，SHA256 `6fc098341ec326e94bf0317e9f120f10b2462ce8c82ce33a3a30250600f79992`。`remediation-guard-canary.log`为33 bytes、SHA256 `213a366685a77149705fd262acfcc98cc75b6e4c28ce9ff1aa3d022c2fdae031`，明确`inherited_guard_canaries_passed`。不是本审亲自重跑，也不能称真实API/生产数据库验收。

增量guard静态复核：`isolated_checks.py`将temp/cache/log/output限制为自有root，pytest basetemp按PID避免清理其他活跃pytest；只允许已冻结SHA匹配的run_ci.sh/bat外壳和当前Python，补给子进程guard/PYTHONPATH及固定PYTHON。已读两份wrapper，只定位仓根并转发Python checks.py，没有发现额外HTTP或根外文件操作。Windows自管道例外仅限stdlib socket.py的_fallback_socketpair及loopback地址，普通HTTP/DNS继续拒绝；不是开放一般loopback。982项完整执行时的入口guard SHA256为`216c6c0f7541ae7d2d97f1ff4adb48e0c7746b19a172352b0d480c4c8cbf229a`。

本审指出Python -S/-I/-E可绕过sitecustomize/PYTHONPATH后，主线在同批增量禁用这些选项及含S/I/E的合并参数；扫描在-c/-m前停止，避免将代码或模块后参数误当解释器选项。当前guard为7980 bytes、SHA256 `3882e7f9174c2d499b3dccb7371285d24585e6181f717d0fdc8c1f07954ea566`。本审只读该增量及预探针：四种参数-S/-I/-E/-BIS逐项尝试实际Popen，必须在子进程启动前PermissionError；根外写/DNS也必须拒绝。主线实际增量运行canary并执行--list-steps（报备exit0）；`remediation-guard-canary.log`仍明确inherited_guard_canaries_passed；`remediation-guard-no-bypass.log`为1695 bytes、SHA256 `5b57177245f440ee02ceb2c889f8acd8862e993d1ba0f09e1d517617dcdde0f9`，记录公开检查步骤清单。没有重跑982，也不把先前982的执行guard hash改成新hash。

这仍是Python audit级的已知检查路径保护，不是操作系统级沙箱。禁用参数增量关闭已指出的入口，但不能笼统称任意原生子进程均被强制guard。沙箱外启动仅用于Git Bash/MSYS启动，不能据此假称其原生进程也受Python audit覆盖。

本轮收口限定于已列原5 RED及R1-R3整改与实际982项公开检查；历史失败、partial和曾发生共享TEMP删除的影响未知边界继续保留，未靠本次GREEN抹除。
