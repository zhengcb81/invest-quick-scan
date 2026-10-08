# EVID-LAB-01整改复验：原反例通过，保留六处残余整改

总控2026-10-08完成一次集中只读验收；裁决**partial_verified / changes_requested**。原六组整改有实质进展，离线重算和发布流程在本范围可确认；不能签“所有来源/语义入口已正确”，也不能把提案当已签预注册执行。原writer按[残余整改卡](remaining-repairs.md)同批修，不重建项目或重做已通过功能。

## 基线与实际执行

Lab唯一源仓`C:/Users/郑曾波/Projects/iqs-evidence-lab`，分支`codex/evid-lab-01`，前轮HEAD `d87cf718a0fa90f2d0929e902ad2faa70c39580a`。整改代码`f5149b9`、版本结果`62fe8b2f51bf498d0925b65e998c7b0a4dba7192`；收到及收尾HEAD `380cb496f30c72128c2cc8e3c88e36924f3c4f2c`，实际clean、无remote。结果后是handoff/证据/PWF及新工件生成器`tools/make_artifacts.py`，src/tests/fixtures运行代码无后续变更。

从真实交接HEAD导出105个Git文件到新的IQS私有根运行，不运行原Lab工作树。工件**104/104工作树size/SHA和Git blob OID匹配**，收尾raw再次104匹配。84个原字节差异仅EOL，双口径已声明，不能称内容篡改。公开IQS handoff CLI shape/scope **valid/exit0**，仅验证声明结构，不能代替实现验收。

| 执行 | 实际结果 |
|---|---|
| worker整改测试 | 81 passed / 9.63s，命令wall 10.568s；含原54、固定9和18新增 |
| 总控原9固定反例 | 9 passed / 2.002s，命令wall 2.423s；与worker9重复验证，不算90个唯一方法 |
| 公共validate-fixtures | 34 fixture / 42 expectation / 350 diagnostic，exit0 |
| 三历史归档公共replay | 两个新输出根均exit0，5个核心payload逐字节一致 |
| 每fixture公共replay | 34/34 exit0；其中FX034仍未收集占位，非真实source正例 |
| 上述集中命令 | 39命令，0失败；没有live/搜索/模型请求 |
| 新边界首批 | 5方法：2 failed / 3 passed / 2.68s |
| 独审发现定向确认 | 6方法：6 failed / 0.64s，含前两缺口的公共路径复现 |

最后两批聚合为**六项残余问题**，有custom期间和数字溢出的重复证明，不称11项独立漏洞。原9固定case仅将写盘故障匹配从final路径改为真实staging的metrics.json文件名，并增加stage无残留/同路径重试断言；其他原断言保持，[适配记录](../../../intake/EVID-LAB-01/2026-10-08-remediation/verification/counterexample-adaptation.json)及执行字节留档。

## 已确认的整改

quarter/half字典不再丢子期间，缺year不补猜；原无source窗口误pass和正常比较列误fail已经修好。重复JSON键和NaN/Infinity常量可拒，FX031保留指纹时score/rationale篡改被发现；即便改chunk自digest，真实归档比较仍拒绝。fixture原字节SHA、答案canonical SHA、字段定位和jsonschema依赖已有改善。

实际第二文件IO故障与final rename故障均不留下最终目录或stage，同一路径可成功重试。本轮Windows目标在发布时出现，旧owner marker保持，exit3；不宣称已验证所有平台rename语义。300计划题位成为主分母，失败/未发题位没有消失，条件分母标注。非执行草案有题组、查询/cache规则和Phase96关系，仍`draft_not_signed/execution_enabled=false/live_not_run=true`。

## 残余问题（均有实际证据）

| 编号 | 优先级 | 最小实证与影响 |
|---|---|---|
| LR-01 | P1 | custom同2026年、日期分别1–3月与4–6月，公开replay exit0、semantic.period=pass；日期被忽略。暂不支持就abstain，不能肯定一致 |
| LR-02 | P1 | FX032删provenance.answer_sha256再改score/rationale，公开replay exit0并发布historical_model_output。缺指纹成为绕过来源校验开关 |
| LR-03 | P1 | JSON数字1e400解析成inf；无answer/chunk的synthetic方向案例公开replay exit0并产semantic.direction=pass。不是仅后续exit1拒答，也没有把Infinity字面写入输出；输出只携带错误通过诊断 |
| LR-04 | P2 | claim2026，来源A=2025、来源B无窗口，实际source.url_window=fail；未知B被移除后错误断言所有引用冲突，应abstain |
| LR-05 | P2 | 已公开重放的FX021 synthetic中structure.duplicate_json记录仍标historical_model_output；不是题包记录，原测试仅查package子集遗漏 |
| LR-06 | P2 / 草案签核前 | 生成输出上限10000，费用公式只用5000；冻结价格十进制复算USD0.82296，高于声明0.48276和0.49。只确认草案非执行，不签费用上界 |

输入/实际结果在[counterexamples](../../../intake/EVID-LAB-01/2026-10-08-remediation/counterexamples/)，三项公共发布的原文件另存published/；全部是私有synthetic或明确故障注入，不是伪造公司golden或修写历史原答案。代码位置和判断边界见[一次集中独审](independent-review.md)。隔离说明尚有“225项”“未读取其他仓”等旧口径，更新为224次校验/127绑定路径/含lock128文件、IQS按锁只读；此文案纠正不单立门。

## 原件、环境与后续

128个独立IQS输入含lock，测试及所有追加案例后SHA均不变；105个导出原文件无改变。所有数据库/输出/TMP/TEMP均在新唯一`runs/evid-lab-remediation-2026-10-08-01`，环境只含Windows运行白名单、无key，Python子进程继承audit，无socket/非Python子进程/外根写；此保护不宣称完整OS读隔离。生产库读写、源仓写、下载/收费均0。

本轮266文件/67目录经lstat单硬链/无重解析、严格CIM无活动私有进程、精确set/size/SHA，dry-run→Apply已清，见[清理回执](../../../intake/EVID-LAB-01/2026-10-08-remediation/cleanup-receipt.json)。Lab收尾HEAD/clean未变，声明.temp-roots一级条目实际0；worker原cleanup日志仍只是收到证据，不用本轮回执替代其历史归属证明。旧Phase97/98归档、Phase92根、共享TEMP、opencode.json保留。

原离线重放统计186模型/24搜索/396契约答案/326评审join/48温度偏差保持；264失败包内题无item_inspection仍不可测，历史片段缺失仍abstain，不把agent标签当人类gold。完整事实金额、归母/扣非精确层级和投资评分准确性不因本工具的维度检查被证明。**L02完整校准/G3/F05、TH/IN/L03不放行**，不执行草案、不重发旧收费矩阵。

本次只写IQS证据/PWF；不代改Lab或创建其remote。原writer只修六项残余及说明，交新commit/版本/原字节、GREEN和清理回执后做一次受影响回验；不为每个helper增加审查，也不继续无边界找新功能。
