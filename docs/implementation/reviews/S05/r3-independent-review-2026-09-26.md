# S05 r3 独立复审

日期：2026-09-26。审查者：独立 question_audit 子代理。范围：S05 本仓离线发布、归档、问卷拼装、标准观察及其比较契约。本报告不混入 S06 预审，亦不证明跨仓产品已接线或真实联网已验收。

## 结论

**PASS（仅 S05 本仓离线范围）。上轮 2 项 P1、1 项 P2 已关闭；本次复审未发现剩余可复现 P1/P2。**

独立执行了 54 个现有定向测试，全部通过、0 skip；另外通过 31 项内存/真实入口探针。最后增加的 package v1 / schema 1.0 兼容限制经过正反验证：真正旧记录保持只读可读，伪装为当前 schema 1.1 的旧包记录不能进入默认验证或严格入库路径。

结论绑定本报告记录的 S05 源码、测试、schema 和发布包哈希。审查期间两份计划文档被并行更新，已单列；没有将全仓状态误报为零漂移。

## 1. 执行范围与独立性

读取并检查：

- scripts/module_registry.py：源目录注册、归档路径、内容寻址、相邻升级链、资源冻结、旧包能力门禁、不可变写入、原子 current 指针。
- scripts/question_sets.py：发布版 compose/manifest 校验、题义和方法指纹、路由组合接缝、固定核心及预算。
- scripts/standard_answers.py 与 observation schema：manifest 验证、冻结资源解析、发布观察标识、重算有效语义、外部 immutable ID 锚定、legacy只读兼容。
- test_module_registry.py、test_standard_answers.py、test_module_contract.py；同时对 test_question_sets.py 及关联题库/schema作快照。
- 实际 current 包及两个旧包、共同发布锁、48 个原始模块归档；主代理完整测试日志。

独立命令采用内存 Python runner：

```text
python -B -X utf8 -
  importlib.util.spec_from_file_location(...) 加载：
    tests/test_module_registry.py
    tests/test_standard_answers.py
    tests/test_module_contract.py
  unittest.TestSuite + unittest.TextTestRunner(verbosity=1)
  在同一隔离进程继续执行本报告第2—4节的31项独立探针
```

没有编辑上述测试，没有替换被测 compose/build/validation 函数。替身仅用于：唯一 TEMP 根和 ROOT 路径重定向；预设虚构答案/执行回执；原子替换故障探针中明确让 os.replace 抛出 OSError。发布器、归档解析器、schema、方法指纹和比较器都使用真实实现。

独立原始结果摘要：

```text
Ran 54 tests in 40.805s
OK
SELECTED_SUITE {"tests":54,"failures":0,"errors":0,"skipped":0}
INDEPENDENT_PROBES {"count":31,"passed":31,"failed":[]}
```

**主代理结果另列，不算本审查独立重跑：** `docs/implementation/contracts/validation-S05-r3-final-full-2026-09-26.log` 报告 `267 passed, 148 subtests passed in 54.06s`。本审查读取该日志并核对 SHA-256 为 `c0b7c99d7a2a7dc49ca392065fad3d3293a8e6363c8e1be4fcf22b5b3883f2d4`。

## 2. 上轮问题关闭证据

### F06 / P1：协议资源变化没有改变可比性 —— CLOSED

入口：module_registry.publish → question_sets.compose(answer_format='standard-1') → standard_answers.build_observations → compare(axis='time')。

在临时根分别独立修改以下四种源资源，然后发布新包、为相同虚构实体和期间重建问卷与观察：

1. answer-content.schema.json 的 properties.score.description。
2. metric-registry.json 中 financial.roic.definition。
3. observation.schema.json 的协议 description。
4. quick_scan/metric.schema.json 的协议 description。

四项均满足：题目 semantic_sha256 不同、observation method_id 不同、compare不可比；先前旧manifest仍验证31题，旧观察仍能按原冻结资源验证。另修改 quick_scan/score.schema.json，以 screening-1 真实入口确认其题义/方法也漂移，旧manifest继续有效。

实现定位：question_sets.py:482 的 _question_fingerprint 对 semantic_fingerprint_version=2.0.0 纳入格式相关资源摘要；v1仍按原算法解释，未重写旧包。当前策略对验证schema变化采取保守不可比处理，不能将“prompt文字恰好未变”当作验证协议没变。

### F07 / P1：自报语义和降级为 legacy 绕过 —— CLOSED，带明确调用方边界

入口：standard_answers.validate_observation，定位 scripts/standard_answers.py:193、256。

独立反例与结果：

- 合法新观察使用 require_published=True 并传独立保存的原 observation_id：通过。
- require_published=True 但不传 expected_observation_id：拒绝，要求 independently stored observation ID。
- 把 question_semantic_sha256 改为64个f、method末段改为16个f并重算 observation_id：默认验证拒绝，报 semantic fingerprint differs from frozen resources and context；严格入口使用原ID时先拒绝 immutable stored identity。
- 同时删 module_package_id/module_release_id/question_definition_sha256/question_semantic_sha256 并重算ID：默认验证拒绝 missing package binding；严格入口拒绝。
- 再把 schema改1.0.0、移除 method的 module-locked-v1 前缀和cycle字段：严格入口仍以原ID拒绝。即便错误调用方传入这条改写记录自报的新ID，require_published也因无冻结包绑定拒绝。
- 将正常8分改7分并重算ID：严格入口与原保存ID比对时拒绝。
- 真正legacy测试记录可作默认只读验证，严格published入口拒绝。

新记录的schema为1.1.0，method namespace为module-locked-v1，包绑定字段及cycle_sensitive为必填。有效题义根据归档题目、cohort、周期context和冻结资源重新计算，而不是仅比较两个自报字符串的后缀。

**调用方边界：** expected_observation_id 必须来自可信保存的任务/出站记录或数据库，不能从同一个待验证JSON现读现传。记录本体加可重算hash不可能证明它曾经是什么内容。默认 validate_observation 是兼容读取入口，不是新入库授权；后续 StockWiki/StockQA接线必须显式使用严格入口并提供独立锚点。本次只验证本地契约，不声称未来消费者已经正确接入。

### F08 / P2：真实旧包先导出后入库失败 —— CLOSED

公开入口：question_sets.compose(..., answer_format='standard-1', package_id=old_id)。

独立使用两个实际存档包：

- pkg_92fc696506725d96746db07a308cb171e0c52f2c0c100b15e8085785de283006
- pkg_c569ac9753d6b2848264ace794e99e64e21c688ac550fb56d7fd1a9088ce28dd

二者均在创建输出目录之前拒绝，错误为 module package cannot issue standard observations; historical read only。每个旧包仍能通过 load_package读取48个模块，文件字节保持不变。

实现定位：module_registry.py:203 observation_ingest_ready 与 question_sets.py:587 compose。新的标准派发需要 semantic fingerprint v2 和支持 schema1.1 的冻结观察资源，不能仅因为旧包hash正确就派发无法入库的新标准问题。

## 3. 最后 v1 / schema1.0 补丁的正反验证

补丁定位：standard_answers.py:244—250 的只读历史分支。除现有套件外，独立使用真实旧包 pkg_c569ac... 的归档题目、旧指纹算法和冻结 schema，重建一条符合上轮v1格式的**虚构历史观察**；该fixture不是声称真实公司已经存在的旧生产记录。

| 路径 | 实测结果 |
|---|---|
| v1包 + schema1.0 + 旧method语义后缀 + 重算后的合法观察ID，默认验证 | 通过，保留历史读取。 |
| 同一合法v1记录，require_published=True + 原ID | 拒绝 current frozen observation contract。 |
| v1包伪装schema1.1，加cycle及当前method前缀，默认验证 | 拒绝 historical package cannot issue current observation schema。 |
| 上述伪装记录，即使严格入口传其自报新ID | 仍拒绝，不能靠补字段进入新协议。 |
| v1包的历史screening manifest | 原指纹路径仍可验证。 |

未观察到这7行兼容限制破坏正常v1读取或新v2/schema1.1观察。建议后续维护者将这组v1正反fixture长期保留；本报告中的独立探针已提供本次实证，不以主代理全量通过替代。

## 4. 历史可重现、发布安全与邻接回归

本次54个现有定向测试覆盖并实际通过：

- 发布幂等与确定性、模块归档内容不可变；当前可编辑源变化不重解释旧manifest。
- 原题ID内容改动拒绝、追加题不改变旧题意义、全局/无关context变化区分。
- 三代相邻发布与两次连续退役、累计墓碑和历史模块可读取。
- 归档字节篡改/缺失拒绝，renderer不可用时fail closed但归档保留可读。
- 预算不丢S05定义的核心和critical项；类型替代、核心24构念和附加题分离。
- manual lens 的公开导出及已有manifest重新验证均不能被 searched_llm绕过。
- 当前问题源、answer schema、observation schema和metric registry改变之后，旧发布观察继续用冻结资源验证。

独立额外探针：

- 篡改prompt并同步重算receipt/manifest/prompt hash，build_observations仍拒绝。
- 同口径两个虚构公司使用新发布包，compare(company)仍可比，没有重现最早的prompt hash污染方法ID回归。
- 非法package ID '../current' 拒绝；questions/releases/../../escape.json 归档引用拒绝。
- 注入os.replace失败到原子指针写入，旧current.json字节保持不变，.publish-*临时文件清理成功。

安全测试范围是解析后的路径逃逸、非法ID、字节完整性和单次原子替换失败；本次未测试恶意并发文件系统置换、掉电fsync耐久性或跨进程并发发布，不宣称覆盖这些独立故障模型。没有为通过检查关闭或放宽任何生产校验。

## 5. 隔离、文件漂移与精确快照

测试与独立探针均使用唯一临时根：

```text
C:\\Users\\郑曾波\\AppData\\Local\\Temp\\iqs-s05-r3-independent-24a3zegj
```

设置TEMP/TMP/TMPDIR和临时CWD，python -B并设置dont_write_bytecode；审计钩子阻止socket/子进程和TEMP外写入。finally后该临时根不存在。没有网络、API、财报下载、真实公司数据写入或外仓修改。

pre/post共核对132个文件，文件集合没有新增/移除：S05源码、测试、所有schemas、题库/新旧发布包和主代理日志等130项未变；两份实施计划文档发生并行更新。审查进程的写入保护阻止了TEMP外修改，因此不把这些并行文档变化归因于测试，也不声称全仓零漂移。

| 并行变化文件 | pre SHA-256 | post SHA-256 |
|---|---|---|
| docs/implementation/tasks.json | 04949d9e5ace93998ced016d8907225c1576139c8f03b032a5ee5bc80c8cabd4 | 74d6b3a32c29cdc2a2e07444264a9ec0946acee8d04637d92e4b6c8de2da69eb |
| docs/implementation/acceptance-cases.json | 128e8396aee517185ea1b41e489a5634e2f00464bd797170af5063ca22d2493f | ff7c406eb7344fdb9d93a015e4c7048dfe9d311459d5f9844507f65aa5de6bfb |

当前package为 pkg_24f07923f23cf0a2be5d7fb4b36a11925c779a8f4a68bdc9c81457084ded080f；其文件SHA-256为284be44f2c67f91e3359a038425579682052f1bdab67cfa426390ee8a468f7aa。共同release仍为modrel_18c097b26b82746d3b48d9f2da4858a15ce216bce39c2572d10c2dcef23d32b9；此次协议资源包更新没有篡改旧模块归档。

## 6. S05验收边界

本次可以放行的是：本仓离线模块发布/归档、确定性拼装、manifest完整性、冻结标准观察及已定义比较边界。两项P1和一项P2不再阻断该范围。

仍须由后续任务实现/验收：S06证据化分类和执行时TTL、路由风险mandatory集合、Q13真正搜索/派发与费用、StockWiki严格ingest调用方及外部ID可信保存、UI和全链live。缺这些功能不能宣称一键2000家公司产品已上线。旧renderer实现不在当前环境时，manifest会明确不可验证而不是默用新renderer；归档原始定义保持可读。旧包的standard-1新导出被禁用，不等于禁止一切历史读取。

## 附录：132文件pre/post清单

本附录记录本次检查的全部文件哈希；unchanged表示post与pre完全相同。仅报告文件本身是本任务授权新增工件，不属于被测生产快照。

| 文件 | pre SHA-256 | post |
|---|---|---|
| docs/implementation/acceptance-cases.json | 128e8396aee517185ea1b41e489a5634e2f00464bd797170af5063ca22d2493f | ff7c406eb7344fdb9d93a015e4c7048dfe9d311459d5f9844507f65aa5de6bfb |
| docs/implementation/contracts/question-modules.md | cea312558b43d14bf2bd08b3b3cf47c6b963e5584a6445b482b319374cb4748d | unchanged |
| docs/implementation/contracts/validation-S05-r3-final-full-2026-09-26.log | c0b7c99d7a2a7dc49ca392065fad3d3293a8e6363c8e1be4fcf22b5b3883f2d4 | unchanged |
| docs/implementation/tasks.json | 04949d9e5ace93998ced016d8907225c1576139c8f03b032a5ee5bc80c8cabd4 | 74d6b3a32c29cdc2a2e07444264a9ec0946acee8d04637d92e4b6c8de2da69eb |
| questions/catalog.json | 252dab9e3f71868a71147ecb7dac64cc187d7d56002b28b266a74f406facaf10 | unchanged |
| questions/common.json | 6900922fc077b0558df49631c2f79e7677b2888c159d29e230d269f23adfdbe3 | unchanged |
| questions/diagnostics/dupont.json | 4e7b347de35c046abc5edbba8fb789ebd63a5f73ec2c9cfd9c275ae65eab76da | unchanged |
| questions/diagnostics/porter.json | bf24920ebdabb70c4ccc68a7bd3d12213aa937344771bf4c317d8a3e4923f44d | unchanged |
| questions/diagnostics/recovery.json | 7c169010401555458330f2d0008b297db2e3e2f4466a52f2aa8a158e306fcdaa | unchanged |
| questions/facts.json | 82008fa98e81978079aabfac8754c53450545f81adb5e90e3b20616d1b41f432 | unchanged |
| questions/industries/agriculture.json | 1e96fa76068cc7e3f5af162525c0d63c9557cca6b330f5a3fa97d3c1f7b8b5e3 | unchanged |
| questions/industries/auto.json | c5473b0c8e961913b589de1a541f667969e2fcdac8d2cc4be2d60d280780f40d | unchanged |
| questions/industries/construction.json | dff2719ec3931ec787a09d00c17dc383ab7e4dc3750293d21f4dbde3371badef | unchanged |
| questions/industries/consumer.json | a9fbd08fb25c5652aa0f8b9dbd70cc89efcd9d9b84ec81d8e415192220536167 | unchanged |
| questions/industries/energy_transition.json | 8142462503687ba6ad03363be38399f609945c174ff36a40f17fa37d7135165a | unchanged |
| questions/industries/hardware.json | 8b16d4b67c46f5cb7a0ef528d59a7c9422346ce1d60124c9c65b7ea7b93d0f1c | unchanged |
| questions/industries/healthcare.json | c2193e1476fb8d555335f154bd772a254767bcce85d81a4b6864fd79ce69d769 | unchanged |
| questions/industries/industrial.json | d8785039c9bfba72c7d91f0bca4c67236730e87b20f5a8c67a57cd0fc2f8cf47 | unchanged |
| questions/industries/internet.json | 83e50d37ffc2280835c7af5bf9e8d7e0a46a62de6455892fa129c71f1a5604c4 | unchanged |
| questions/industries/leisure_media.json | f34ad9cc846927128489b168617eb92fcd34f9e2c1d90255d1a84594c8ed82a7 | unchanged |
| questions/industries/materials.json | 5375e7c4623c0c54f081eb3c4607b974cdc426081a6182b194d5015989546b2e | unchanged |
| questions/industries/medtech.json | ac54ae9e8c53384595250775ce2330b357640790389f40f0d1e9c65642f3629d | unchanged |
| questions/industries/other.json | 44107a7b57386b783012b2a0ef077a57aadbddfddaec102bc04c7fbbac661405 | unchanged |
| questions/industries/professional_services.json | e2416b58b021c5dab8215f603ca2a88bb394e121b0e8f57ecf3b8437afa052db | unchanged |
| questions/industries/resources.json | b5f5ebec03ebc39b0f8f34bdefd7c28bd52e24a1339aed9abffe02c86e944d43 | unchanged |
| questions/industries/retail.json | 6f3ee9d2bfc703d0772167c500ac8ac093838885f423975b55187dd035350fab | unchanged |
| questions/industries/semiconductors.json | 5924b3398d208dbf355a17069bc649cdf3b2936d22633065f059f80282ccb180 | unchanged |
| questions/industries/software.json | 20a3ca35177853596f6aa2bd67aefcb3c99cc003c18e5973b747145b0b7389e7 | unchanged |
| questions/industries/telecom.json | 3858afe6e41e621cbaceeb123e5bf24b8f57209a7ee23fd1a0020439fb0760d2 | unchanged |
| questions/industries/transport.json | 254df1e98979b9f7422fc39088e1c677a3ace0adecd54ec96b7eeb8bb76a46d1 | unchanged |
| questions/industries/utilities.json | a417a15bdbce282f72e58b673e19480e57bfd411effb51e978886713d50d4326 | unchanged |
| questions/metric-registry.json | 790d0a8295771c372d8266ab1f0883c93b2bb22f4f81ab482dd8d95054bf0e75 | unchanged |
| questions/overlays/acquisitive.json | a4b152e238a2cf011290a19a943b75726c0218c913b4ff35db7148be647809c3 | unchanged |
| questions/overlays/concentrated.json | 2e1a0877d5de37c4a30fdfda15382a12bd967e121f4d9e9eec3cb46dea637268 | unchanged |
| questions/overlays/controlled.json | dd7865cb57980b6a70beadaa7df059f62d07942d12edbfdab591a589e1ce8bec | unchanged |
| questions/overlays/cross_border.json | 1f578a9a1b8ce232bad72cd6bed4ffc4b38a61d529e1e59fe2e7f5322b44e88d | unchanged |
| questions/overlays/distressed.json | 63d83389f9ff499d75659b846e26f2d9794df066f4b0ec2b9e9fa009066fbd23 | unchanged |
| questions/overlays/listing_structure.json | e5094e21540a73fe777b9bff615497cec5e75e72326541f080d0f986821d77ba | unchanged |
| questions/overlays/recent_listing.json | 107a8700f20ff6545152a9bd751491f4aa2577fcdb80083f5be5f68710a6f396 | unchanged |
| questions/overlays/subsidized.json | b1937cda5f401e2436b40c77c108d2ea5ffa5d32cf76098039fe1bb5a4e809b5 | unchanged |
| questions/releases/artifacts/acquisitive/3_0_0-a4b152e238a2cf011290a19a943b75726c0218c913b4ff35db7148be647809c3.json | a4b152e238a2cf011290a19a943b75726c0218c913b4ff35db7148be647809c3 | unchanged |
| questions/releases/artifacts/agriculture/3_0_0-1e96fa76068cc7e3f5af162525c0d63c9557cca6b330f5a3fa97d3c1f7b8b5e3.json | 1e96fa76068cc7e3f5af162525c0d63c9557cca6b330f5a3fa97d3c1f7b8b5e3 | unchanged |
| questions/releases/artifacts/auto/3_0_0-c5473b0c8e961913b589de1a541f667969e2fcdac8d2cc4be2d60d280780f40d.json | c5473b0c8e961913b589de1a541f667969e2fcdac8d2cc4be2d60d280780f40d | unchanged |
| questions/releases/artifacts/bank/3_0_0-acbde8c2b439fa17ecf4b7d1b5778aa0d2976ce1d2df10be9f20dddc0828ba07.json | acbde8c2b439fa17ecf4b7d1b5778aa0d2976ce1d2df10be9f20dddc0828ba07 | unchanged |
| questions/releases/artifacts/capital_markets/3_0_0-c36455dde5c3c037b5c55a3a6a76ab71dda9f3892af7997df5cfa3fbd6b2ef09.json | c36455dde5c3c037b5c55a3a6a76ab71dda9f3892af7997df5cfa3fbd6b2ef09 | unchanged |
| questions/releases/artifacts/commercialization/3_0_0-bc404077787eb2482da70cd6d5575172bb259ad862f6add46b8959f6efbb2ae7.json | bc404077787eb2482da70cd6d5575172bb259ad862f6add46b8959f6efbb2ae7 | unchanged |
| questions/releases/artifacts/common/3_0_0-6900922fc077b0558df49631c2f79e7677b2888c159d29e230d269f23adfdbe3.json | 6900922fc077b0558df49631c2f79e7677b2888c159d29e230d269f23adfdbe3 | unchanged |
| questions/releases/artifacts/concentrated/3_0_0-2e1a0877d5de37c4a30fdfda15382a12bd967e121f4d9e9eec3cb46dea637268.json | 2e1a0877d5de37c4a30fdfda15382a12bd967e121f4d9e9eec3cb46dea637268 | unchanged |
| questions/releases/artifacts/construction/3_0_0-dff2719ec3931ec787a09d00c17dc383ab7e4dc3750293d21f4dbde3371badef.json | dff2719ec3931ec787a09d00c17dc383ab7e4dc3750293d21f4dbde3371badef | unchanged |
| questions/releases/artifacts/consumer/3_0_0-a9fbd08fb25c5652aa0f8b9dbd70cc89efcd9d9b84ec81d8e415192220536167.json | a9fbd08fb25c5652aa0f8b9dbd70cc89efcd9d9b84ec81d8e415192220536167 | unchanged |
| questions/releases/artifacts/controlled/3_0_0-dd7865cb57980b6a70beadaa7df059f62d07942d12edbfdab591a589e1ce8bec.json | dd7865cb57980b6a70beadaa7df059f62d07942d12edbfdab591a589e1ce8bec | unchanged |
| questions/releases/artifacts/cross_border/3_0_0-1f578a9a1b8ce232bad72cd6bed4ffc4b38a61d529e1e59fe2e7f5322b44e88d.json | 1f578a9a1b8ce232bad72cd6bed4ffc4b38a61d529e1e59fe2e7f5322b44e88d | unchanged |
| questions/releases/artifacts/cyclical/3_0_0-3b60a73d32b454a34d1c9292d28114dfff446a13ef28b2971e36cb81f9740569.json | 3b60a73d32b454a34d1c9292d28114dfff446a13ef28b2971e36cb81f9740569 | unchanged |
| questions/releases/artifacts/declining/3_0_0-898fc02538a4a6c60f7bca75b3aa21930392863cec07d6f601bcee86ead919e2.json | 898fc02538a4a6c60f7bca75b3aa21930392863cec07d6f601bcee86ead919e2 | unchanged |
| questions/releases/artifacts/distressed/3_0_0-63d83389f9ff499d75659b846e26f2d9794df066f4b0ec2b9e9fa009066fbd23.json | 63d83389f9ff499d75659b846e26f2d9794df066f4b0ec2b9e9fa009066fbd23 | unchanged |
| questions/releases/artifacts/dupont/3_0_0-4e7b347de35c046abc5edbba8fb789ebd63a5f73ec2c9cfd9c275ae65eab76da.json | 4e7b347de35c046abc5edbba8fb789ebd63a5f73ec2c9cfd9c275ae65eab76da | unchanged |
| questions/releases/artifacts/energy_transition/3_0_0-8142462503687ba6ad03363be38399f609945c174ff36a40f17fa37d7135165a.json | 8142462503687ba6ad03363be38399f609945c174ff36a40f17fa37d7135165a | unchanged |
| questions/releases/artifacts/hardware/3_0_0-8b16d4b67c46f5cb7a0ef528d59a7c9422346ce1d60124c9c65b7ea7b93d0f1c.json | 8b16d4b67c46f5cb7a0ef528d59a7c9422346ce1d60124c9c65b7ea7b93d0f1c | unchanged |
| questions/releases/artifacts/healthcare/3_0_0-c2193e1476fb8d555335f154bd772a254767bcce85d81a4b6864fd79ce69d769.json | c2193e1476fb8d555335f154bd772a254767bcce85d81a4b6864fd79ce69d769 | unchanged |
| questions/releases/artifacts/holding/3_0_0-f0bd04df47e55fbd8610205d93ce961f2ef9ff25a9f2a4de2111eb9390af6395.json | f0bd04df47e55fbd8610205d93ce961f2ef9ff25a9f2a4de2111eb9390af6395 | unchanged |
| questions/releases/artifacts/industrial/3_0_0-d8785039c9bfba72c7d91f0bca4c67236730e87b20f5a8c67a57cd0fc2f8cf47.json | d8785039c9bfba72c7d91f0bca4c67236730e87b20f5a8c67a57cd0fc2f8cf47 | unchanged |
| questions/releases/artifacts/insurer/3_0_0-11643527ac31ac3c98394ff84c3450f469842401fa76db3334411af6201571ad.json | 11643527ac31ac3c98394ff84c3450f469842401fa76db3334411af6201571ad | unchanged |
| questions/releases/artifacts/internet/3_0_0-83e50d37ffc2280835c7af5bf9e8d7e0a46a62de6455892fa129c71f1a5604c4.json | 83e50d37ffc2280835c7af5bf9e8d7e0a46a62de6455892fa129c71f1a5604c4 | unchanged |
| questions/releases/artifacts/leisure_media/3_0_0-f34ad9cc846927128489b168617eb92fcd34f9e2c1d90255d1a84594c8ed82a7.json | f34ad9cc846927128489b168617eb92fcd34f9e2c1d90255d1a84594c8ed82a7 | unchanged |
| questions/releases/artifacts/listing_structure/3_0_0-e5094e21540a73fe777b9bff615497cec5e75e72326541f080d0f986821d77ba.json | e5094e21540a73fe777b9bff615497cec5e75e72326541f080d0f986821d77ba | unchanged |
| questions/releases/artifacts/materials/3_0_0-5375e7c4623c0c54f081eb3c4607b974cdc426081a6182b194d5015989546b2e.json | 5375e7c4623c0c54f081eb3c4607b974cdc426081a6182b194d5015989546b2e | unchanged |
| questions/releases/artifacts/mature/3_0_0-b0eb8ef0b99692835a051080d21a0d604fc99899df28a69e1066a6ad61bf356b.json | b0eb8ef0b99692835a051080d21a0d604fc99899df28a69e1066a6ad61bf356b | unchanged |
| questions/releases/artifacts/medtech/3_0_0-ac54ae9e8c53384595250775ce2330b357640790389f40f0d1e9c65642f3629d.json | ac54ae9e8c53384595250775ce2330b357640790389f40f0d1e9c65642f3629d | unchanged |
| questions/releases/artifacts/operating/3_0_0-eb226c7923039db899de875557d7e18f32689cf8599c5957432921810b90d5d9.json | eb226c7923039db899de875557d7e18f32689cf8599c5957432921810b90d5d9 | unchanged |
| questions/releases/artifacts/other/3_0_0-44107a7b57386b783012b2a0ef077a57aadbddfddaec102bc04c7fbbac661405.json | 44107a7b57386b783012b2a0ef077a57aadbddfddaec102bc04c7fbbac661405 | unchanged |
| questions/releases/artifacts/porter/3_0_0-bf24920ebdabb70c4ccc68a7bd3d12213aa937344771bf4c317d8a3e4923f44d.json | bf24920ebdabb70c4ccc68a7bd3d12213aa937344771bf4c317d8a3e4923f44d | unchanged |
| questions/releases/artifacts/pre_revenue/3_0_0-df9a8c51ae1b330ad22a1fd0b035a3df9a6d536140dd8d8f1a12dc4104b1f55c.json | df9a8c51ae1b330ad22a1fd0b035a3df9a6d536140dd8d8f1a12dc4104b1f55c | unchanged |
| questions/releases/artifacts/professional_services/3_0_0-e2416b58b021c5dab8215f603ca2a88bb394e121b0e8f57ecf3b8437afa052db.json | e2416b58b021c5dab8215f603ca2a88bb394e121b0e8f57ecf3b8437afa052db | unchanged |
| questions/releases/artifacts/property_developer/3_0_0-fae62eabe21ba1190a008f87d24c004a0e026dd722727f9e8376e066bc7dcf7a.json | fae62eabe21ba1190a008f87d24c004a0e026dd722727f9e8376e066bc7dcf7a | unchanged |
| questions/releases/artifacts/property_owner/3_0_0-5e173296f09162c276bad3914bdd22310839963f30a1d3412b1384b8bf822b52.json | 5e173296f09162c276bad3914bdd22310839963f30a1d3412b1384b8bf822b52 | unchanged |
| questions/releases/artifacts/recent_listing/3_0_0-107a8700f20ff6545152a9bd751491f4aa2577fcdb80083f5be5f68710a6f396.json | 107a8700f20ff6545152a9bd751491f4aa2577fcdb80083f5be5f68710a6f396 | unchanged |
| questions/releases/artifacts/recovery/3_0_0-7c169010401555458330f2d0008b297db2e3e2f4466a52f2aa8a158e306fcdaa.json | 7c169010401555458330f2d0008b297db2e3e2f4466a52f2aa8a158e306fcdaa | unchanged |
| questions/releases/artifacts/resources/3_0_0-b5f5ebec03ebc39b0f8f34bdefd7c28bd52e24a1339aed9abffe02c86e944d43.json | b5f5ebec03ebc39b0f8f34bdefd7c28bd52e24a1339aed9abffe02c86e944d43 | unchanged |
| questions/releases/artifacts/retail/3_0_0-6f3ee9d2bfc703d0772167c500ac8ac093838885f423975b55187dd035350fab.json | 6f3ee9d2bfc703d0772167c500ac8ac093838885f423975b55187dd035350fab | unchanged |
| questions/releases/artifacts/scaling/3_0_0-682685e19cb86ec2615d1a0e543213ca4190954a08cb9d5b76edb8b94049e1f1.json | 682685e19cb86ec2615d1a0e543213ca4190954a08cb9d5b76edb8b94049e1f1 | unchanged |
| questions/releases/artifacts/semiconductors/3_0_0-5924b3398d208dbf355a17069bc649cdf3b2936d22633065f059f80282ccb180.json | 5924b3398d208dbf355a17069bc649cdf3b2936d22633065f059f80282ccb180 | unchanged |
| questions/releases/artifacts/software/3_0_0-20a3ca35177853596f6aa2bd67aefcb3c99cc003c18e5973b747145b0b7389e7.json | 20a3ca35177853596f6aa2bd67aefcb3c99cc003c18e5973b747145b0b7389e7 | unchanged |
| questions/releases/artifacts/subsidized/3_0_0-b1937cda5f401e2436b40c77c108d2ea5ffa5d32cf76098039fe1bb5a4e809b5.json | b1937cda5f401e2436b40c77c108d2ea5ffa5d32cf76098039fe1bb5a4e809b5 | unchanged |
| questions/releases/artifacts/telecom/3_0_0-3858afe6e41e621cbaceeb123e5bf24b8f57209a7ee23fd1a0020439fb0760d2.json | 3858afe6e41e621cbaceeb123e5bf24b8f57209a7ee23fd1a0020439fb0760d2 | unchanged |
| questions/releases/artifacts/transport/3_0_0-254df1e98979b9f7422fc39088e1c677a3ace0adecd54ec96b7eeb8bb76a46d1.json | 254df1e98979b9f7422fc39088e1c677a3ace0adecd54ec96b7eeb8bb76a46d1 | unchanged |
| questions/releases/artifacts/turnaround/3_0_0-2f037de28d4beab69519bef7dc062e0e98a60de58e3827c91939da33e49f088d.json | 2f037de28d4beab69519bef7dc062e0e98a60de58e3827c91939da33e49f088d | unchanged |
| questions/releases/artifacts/utilities/3_0_0-a417a15bdbce282f72e58b673e19480e57bfd411effb51e978886713d50d4326.json | a417a15bdbce282f72e58b673e19480e57bfd411effb51e978886713d50d4326 | unchanged |
| questions/releases/artifacts/validation/3_0_0-8f1bfd4f84c6390d3dbde8e92e594f9eb2e635f266f16c90b6b2289585e273bc.json | 8f1bfd4f84c6390d3dbde8e92e594f9eb2e635f266f16c90b6b2289585e273bc | unchanged |
| questions/releases/current.json | 8950dc3fa28b287ae5e9e7e0b3775360659f3a74a78107664d6b2c5eb5ebe985 | unchanged |
| questions/releases/locks/modrel_18c097b26b82746d3b48d9f2da4858a15ce216bce39c2572d10c2dcef23d32b9.json | e755ed9557bb78eaacd4318ccff2036f69f51a54de96c8c55fcddcea095b5ca6 | unchanged |
| questions/releases/packages/pkg_24f07923f23cf0a2be5d7fb4b36a11925c779a8f4a68bdc9c81457084ded080f.json | 284be44f2c67f91e3359a038425579682052f1bdab67cfa426390ee8a468f7aa | unchanged |
| questions/releases/packages/pkg_92fc696506725d96746db07a308cb171e0c52f2c0c100b15e8085785de283006.json | 699ebf997ce72a6fa308c47a2fcff0b471d8b0c00f806f08fda5bf48574d7085 | unchanged |
| questions/releases/packages/pkg_c569ac9753d6b2848264ace794e99e64e21c688ac550fb56d7fd1a9088ce28dd.json | 64982e88662b0f75326f75f3a9f57455a871d43b7194f52dd28ddaed6e21ea1e | unchanged |
| questions/scoring-contexts.json | 1408aa4a154efabd79f8c575e27204d921124777dd666c6b04154e16b9215ef3 | unchanged |
| questions/stages/commercialization.json | bc404077787eb2482da70cd6d5575172bb259ad862f6add46b8959f6efbb2ae7 | unchanged |
| questions/stages/cyclical.json | 3b60a73d32b454a34d1c9292d28114dfff446a13ef28b2971e36cb81f9740569 | unchanged |
| questions/stages/declining.json | 898fc02538a4a6c60f7bca75b3aa21930392863cec07d6f601bcee86ead919e2 | unchanged |
| questions/stages/mature.json | b0eb8ef0b99692835a051080d21a0d604fc99899df28a69e1066a6ad61bf356b | unchanged |
| questions/stages/scaling.json | 682685e19cb86ec2615d1a0e543213ca4190954a08cb9d5b76edb8b94049e1f1 | unchanged |
| questions/stages/turnaround.json | 2f037de28d4beab69519bef7dc062e0e98a60de58e3827c91939da33e49f088d | unchanged |
| questions/stages/validation.json | 8f1bfd4f84c6390d3dbde8e92e594f9eb2e635f266f16c90b6b2289585e273bc | unchanged |
| questions/types/bank.json | acbde8c2b439fa17ecf4b7d1b5778aa0d2976ce1d2df10be9f20dddc0828ba07 | unchanged |
| questions/types/capital_markets.json | c36455dde5c3c037b5c55a3a6a76ab71dda9f3892af7997df5cfa3fbd6b2ef09 | unchanged |
| questions/types/holding.json | f0bd04df47e55fbd8610205d93ce961f2ef9ff25a9f2a4de2111eb9390af6395 | unchanged |
| questions/types/insurer.json | 11643527ac31ac3c98394ff84c3450f469842401fa76db3334411af6201571ad | unchanged |
| questions/types/operating.json | eb226c7923039db899de875557d7e18f32689cf8599c5957432921810b90d5d9 | unchanged |
| questions/types/pre_revenue.json | df9a8c51ae1b330ad22a1fd0b035a3df9a6d536140dd8d8f1a12dc4104b1f55c | unchanged |
| questions/types/property_developer.json | fae62eabe21ba1190a008f87d24c004a0e026dd722727f9e8376e066bc7dcf7a | unchanged |
| questions/types/property_owner.json | 5e173296f09162c276bad3914bdd22310839963f30a1d3412b1384b8bf822b52 | unchanged |
| schemas/answer-content.schema.json | a83236c2aba50115038cd2d404d5810bd50791c2b3f089f252b77b6a6d322547 | unchanged |
| schemas/model-policy.schema.json | e6188237ef0fd07c4ee63c1eab25ab250426ba7c12e6d0bc71a9d4ab1d7d0455 | unchanged |
| schemas/observation.schema.json | 6344d2afc9e0d937e05baba8aef27ad15c91770ab7ecb2ddbd549e5ab4fb70ec | unchanged |
| schemas/provider-connectivity-profiles.schema.json | 3d6aed3cf443d1e0c3108f22ce3b4c45a2afb2b4c241476a1587cfc660b07319 | unchanged |
| schemas/quick_scan/deployment.schema.json | af7c5745ff00a63110ba8049d345acd9b639a48a9b7e09528fb784c34640eca1 | unchanged |
| schemas/quick_scan/exchange.schema.json | efdf0e3427d1bbb73892e9573fbf3b1f0389218e3f5a0c8dff4ca0cd63764122 | unchanged |
| schemas/quick_scan/identity.schema.json | b0f1931b4eb6cdcef0fab0e6f7ac5d6db707686555f363301aea0511c9ae0a82 | unchanged |
| schemas/quick_scan/metric.schema.json | 251ed13329e3a361853ed7539d2ee4fee43674317ea3a686127f9ecfa5741f23 | unchanged |
| schemas/quick_scan/module-release.schema.json | d4510401446a56613451b1c83ace3ad2a3037d32bfb0b489ca33d5a9763ff0a4 | unchanged |
| schemas/quick_scan/query.schema.json | e7fc264b43d85e4cdd5c82a71b9fedb579dd0fc1196f3c5fde661f14fa1756f8 | unchanged |
| schemas/quick_scan/question-module.schema.json | ae74e817c82846540882894a57c0750619ecae3541ced04abb5b0f89c8564b72 | unchanged |
| schemas/quick_scan/route-decision.schema.json | 2ac2fa46d445779d30f7cafcf834cd69df0fa9bcc9cd5722bd6baf3799306071 | unchanged |
| schemas/quick_scan/rule.schema.json | 62d357990d57d3334ee1863fbba7ab6129cb621c2e75cc2db1665a2a10e71b47 | unchanged |
| schemas/quick_scan/score.schema.json | bdb9465f9bb071bb455e04bd30ab4ccfe0020c4dfb725d7525b345a8fb913a2e | unchanged |
| schemas/quick_scan/work.schema.json | a67f82c77f43561a787d42756c8c71ced06aaf8b3a37b8229442efd73d60a8bf | unchanged |
| scripts/module_contract.py | 069d14199239bbfc0b38aad88f360228d5fc0a2f6ca324c037850fd2fa183a97 | unchanged |
| scripts/module_registry.py | 4ae0fd4359a5c2e583f85a790ba8ac929190bc97d1f9111687bfe78a74a35e0b | unchanged |
| scripts/question_sets.py | b6c6ad4219be1ae8a87af44a40cd2199fd2e33a90a5afbc56bc14b04d342bb9b | unchanged |
| scripts/standard_answers.py | 66eadd87503f0bde7794e33b34172a3f77b32525fe805031471f2a3defd012ec | unchanged |
| tests/test_module_contract.py | 9fe357723bd6b991c66e49661ad5a6a355b2d0a5312bf040c02174fed871a56d | unchanged |
| tests/test_module_registry.py | 5d3eb28e56a50ac78ffece4ad06d6115b497e81e9a6b0a94c011a476747e5608 | unchanged |
| tests/test_question_sets.py | 2ff8090c17b2aa89ec96c708302efdf895d3797bd759ed986ad2110970f98fe0 | unchanged |
| tests/test_standard_answers.py | b32403c595eeb7a26d2b5d0ca3509b5071659b289f3e427bf34e48fa93f9f7a1 | unchanged |

