# MATRIX-CASE-01-R1：同包引用与比较资料一致性集中收口

这是总控集中整改卡，未自动派发。唯一实施目录 `C:/Users/郑曾波/Projects/iqs-comparison-case-lab`。IQS/StockQA/StockWiki、其他Labs、生产数据库与名单均只读；不代实现比较/评分/身份/查询/预算引擎，不调用模型、搜索或任何网络API，不安装到全局Python、不改全局配置。不修Git历史，不删除旧交接或scratch来掩盖问题。

先读原MATRIX-CASE-01卡、本批handoff-rules、原inputs.lock.json和原handoff模板。完整集中验收在IQS `docs/implementation/intake/parallel-acceptance-2026-10-11/matrix-case/` 的review.md/result.json；正常与坏输入在 `controls/`，原公开CLI日志、真实命令/PID/guard证明在 `reports/`。`retention-manifest.json`逐项记录原运行相对路径、当前留档路径、bytes/raw SHA；总控已清理自有 `runs/mc01`，原日志里的运行实参保持历史原字节，不使用已删除路径。有必要的反例可复制到自己独占运行根，注明原raw SHA/bytes；不要向总控留档写入。

## 当前基线与交接事实

实际分支codex/matrix-case-01，HEAD4629e2a79a1d514f99f8db42394e39203dae06f0，原工作树102项改动，无remote。handoff仍partial、result_commit=null。最早可见32858b7已含产品，没有纯初始化提交；保留这个客观限制，不补写假的base，不reset/stash/clean未知状态。开工重新读HEAD、完整status与稳定字节，若已有其他writer或变动先记录，不能把旧102项当成当前事实。

原共同输入锁raw SHA=3ce74d8399e2bee7e163a8b1ecc32cf6335f26bb15d23071a367bdc144e0d46c。27份本包快照及验收时当前源都匹配；锁不因整改重写。锁内题目文字、ID、anchors、权重、scope和发布指针不得变动。新版确需新增owner输入，向总控列具体缺口，旧锁与旧快照原字节保留，不用自制注册或相似文件顶替。

32例覆盖8类，每类有正常控制与边界；不为达到36–48凑数。保留原稳定case_id与旧版本字节；若案例含义确需改变，具名新版本并归档旧pack，不复用旧ID代表不同含义。正常的not_comparable/unknown/N/A仍是合法资料，不能为了strictness删掉难例。

## 要完成的行为

1. **真实冻结引用。** `validate`与`export`通过现有公开入口检查实际snapshot文件的bytes/raw SHA、consumer/path绑定和锁版本。当前verify_input_files只比较ref声明与lock声明。不得只比较两份声明，不得把整锁SHA或pack_id正确当成nested文件完整性。只读定位既有 `fixtures/locked-inputs`，路径必须从固定本包根、锁中相对path和source_refs的精确关系得来；允许复制到移动后的独占副本仍以相同相对路径读取。若确需新定位参数，两条公开CLI一起明确声明并测试，不靠monkeypatch/root猜测/后缀搜索，也不改原锁。拒跨根、secret/reparse及未来锁格式。
2. **对照真实定义。** 原冻结rubric已有core_basket的question_id、construct_id、definition hash和scope，必须校对引用，不只是双方hash相等。两侧同时填相同假hash也要失败。区分definition/semantic hash与raw文件SHA，不把它们混作同一域；缺少semantic来源明确null。核rubric_release_id及method_id实际来源，当前冻结method为core-constructs-v1-operating，案例常量iqs.quality.default需澄清字段含义，不能任取字符串。module/metric/construct引用无事实时保留未核实缺口，不伪造owner注册；匹配未校准候选不等于金融校准通过。
3. **案例内部矛盾。** 不实现第二比较器，只核声明事实与声明动作能否同时成立：即使time/model轴为false，FY/H1、score/ratio、USD/CNY无FX基础、同题义hash冲突或评分尺冲突也不能仍以same_basis授予数值派生。合法且说明清楚的边界case必须继续通过。不同module release本身不能自动判不可比；向后兼容且题义/评分尺不变可继续展示，未证实兼容则明示unknown/gap，不能无依据宣称已认证可比。
4. **保留未知。** `must_preserve`的side/field/value_state必须与本例left/right对应。保留指令仍unknown、右侧却scored/value/5属于自身矛盾；该校验不要求工具恢复已完全删除的历史事实。comparability unknown/not_comparable不得获得任何矛盾的数值差/数值比/归一化动作；保留未知、N/A、partial与其分母，不默认填5或0。
5. **基础值。** 用真实日历校验日期；1–10 score边界不依赖JSON int还是float。不要误把非score单位的金额/ratio也限到1–10。实际缺模型与request/actual混淆保护继续保留；未来schema、重复JSON键/ID、输出拒覆盖与失败无正式输出继续守住。
6. **可提交交接。** 保存原RED和真实反例；修后的正常/反例都由公开CLI实际执行。接口hash记录真实hash而不是“bytes-hash”的拼串或无出处版本标签。恢复原安装入口测试的安全执行条件：不能删除guard或环境检查来让它绿；确需安装验证，只用本包自有离线环境，不动全局环境。未能验证则准确not_run，不把测试工具错误或不可创建的链接计入产品通过。

## 一次集中实施序列

1. 在本Lab独占运行根冻结当前产品、27份snapshot和原锁；记录Git/owner，PWF只写本包planning。对当前dirty集合逐项解释为本包已有交付，不进行“全部删除”或随意提交其他writer材料。
2. 先重现正常32例、两次无损导出；再从总控固定输入复制C06–C10、C13、C17–C18、C21、C25–C26和C30建立有鉴别力的RED。每个破坏case正确重算pack_id，保留其余原字段与must_preserve，避免错误被其他shape原因替代。
3. 在现有validator/CLI/schema与测试中完成上述引用与内部一致性修复，复用现有canonical、安全读取和闭合schema。不要新增第二评分器、自动比较器或owner写入路径。
4. 只跑受影响组进行开发；稳定后一次原相关回归、一次公开CLI正反例和一次集中review。不要每字段/helper开审查。原tests用custom _params，使用实际支持该标记的测试入口，不把pytest fixture错误算产品失败。
5. 完成同包文档、原1.0读取/新版兼容说明、case-map和隔离证据。保留已绿的32例无损导出、覆盖保护、真实junction边界；不重做无关owner或金融实验。
6. 精确提交本包产品与测试，写实际完整result_commit；再提交交接资料。正常hooks，不force/skip，不混入未知staged。无remote就仅本地提交，不新增remote或推送目的地。

## 一批正反例和审查标准

| 控制组 | 正常控制 | 必须拒绝或显式unsupported的反例 |
| --- | --- | --- |
| 锁与引用 | 原27文件、原32例、合法移动副本 | 实际nested字节+1LF；未来lock2.0；双侧同假definition hash；错题/metric/construct与来源绑定 |
| 口径 | 同basis数值展示；明确not_comparable边界 | 轴flag关闭仍有FY/H1、unit/currency、题义/评分尺混合并授予数值派生 |
| 未知 | unknown/N/A/partial原状态保留 | must_preserve unknown被完整改成5；unknown得到numeric_ratio或其他数值派生 |
| 类型与版本 | 真日期；1–10的int/float；旧合法1.0资料 | 2月30日；score=11.5；未来artifact/schema；重复ID/JSON键 |
| 输出和隔离 | 两份导出字节相同、全部case保留 | 覆盖已有输出、失败遗留正式输出、真实owned junction指向marker、假秘密回显或写到自有根之外 |

允许not_comparable的正常case，通过本身不证明金融结论正确。不得把错误case的expected_exit改成0然后声称RED已过。拒绝应有对应named reason；timeout、未知进程状态或安装环境不成立不算正确拒绝。可用原正常控制与已有原日志解释复用，不累计重叠选择器凑更大通过数。

## 环境与交接

全程无key、无网络、费用API0。父/子TEMP、cache、SQLite（若有必要）和所有写入限定到自己的独占根；强制guard须跨Windows subprocess argv字符串及环境变化保持。测试阶段真实PID/终态、原stdout/stderr/JUnit或原runner日志全部保留。真实junction清理前核链接与目标，仅删链接；hard-link pending aliases清理前须枚举同device/inode组全部自有链接并核实st_nlink等于组大小，保留原字节后仅清这组精确路径；不能证明闭合的具体路径保留并披露。先迁出必要正常/坏输入与轻量证据，再清本包临时副本/cache/scratch，不以保留整个测试根代替环境恢复。历史系统TEMP/外写限制如实保留，不能追称此前没有发生。

交接新增 `docs/handoff/MATRIX-CASE-01/remediation-01/`，同时准确更新主handoff：summary.md、handoff.json、interfaces.md、case-map.md、artifacts.json、isolation.md、原日志、source/锁前后清单及planning。artifacts每项相对path、bytes、raw SHA、purpose、source_class，不含自身hash；pack_id的canonical域与raw SHA分开。handoff记录实际base/result/最终HEAD、范围、原命令/PID/退出码和未解项；result_commit是产品提交，不用交接HEAD替代，也不造自身SHA循环。

最终只交一包给总控集中续验；不自行关闭W14/V17/V18/U03/U04、金融准确性或其他owner门，不自动派发下一步，不把原候选评分尺说成已真实校准。
