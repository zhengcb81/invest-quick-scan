# 本轮共同接口、边界与交接

## 开工与输入

每包只写自己新Lab；IQS、StockQA、StockWiki、company-wiki、原Lab、上一轮三个Lab及本轮其他Lab均只读。新根若已有不明源码或writer，先报告，不覆盖、不reset/clean。可在自己的根建Git/PWF；不改总控三份PWF。未初始化CodeGraph按项目规则询问，但可先读交接，不因此暂停所有只读准备。

`inputs.lock.json`为本轮固定输入，path相对快照根，bytes/raw SHA256必须核对；缺失/篡改/重复路径/越界拒绝。搬迁使用显式 `--inputs`，不回活动源补文件或混用import。输入包含：

- `iqs/` 原scripts/schemas/questions，特别是实际标准答案validator/指标字典/1.1研究驱动；不是完整Git工作树。
- `company/` 已交付策略src/schemas，commit4cb4e3d；`stockqa/` 原研究SDK及相关src/schema，commit8557d862。SESSION复用这些接口，不新造模型HTTP/搜索/账本。
- `trial/` T0问题、公开证据、schema/指标及实际routed12投影；`trial-t1/` 已终止的T1三会话result/events、measurement及计划会话清单（缺失会话保持not_started）。不含API密钥、预算SQLite、私有provider消息/隐藏思考。
- `reviews/` 两轮独立匿名金融判定，供错误案例与缺口设计；不带private解盲映射。工人不是新的金融验收者，不能根据这些反例自行宣布后续模型达标。
- trial-t1/measurements.json的quality_review=pending是生成该计量快照时的状态，原件不回写；最新已完成审查以reviews/independent-review-02.json及冻结rules中的T1结果报告为准，不因旧pending字段重做盲评。
- `reference/` 十个独立主标量的有限核验范围，仅CLAIM的离线验证/测试可读；不能放进生成/批判模型提示以假装模型自己找到证据。主标量支持不等于整个复合fact/评分获得gold资格。
- `rules/` 固定质量规则和已登记实验说明，保留各轮真实限制。所有新提示仅用公开board，不向生成LLM泄漏私有评审结论、rubric或预期测试答案。

对象函数只能声称canonical-object hash：UTF-8 `json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)` 的SHA256。文件边界另记raw SHA/bytes，两者不能混用。context来自调用方可信原任务绑定，至少company_key、cutoff、question_canonical_sha256、evidence_board_canonical_sha256；不能从误传board临时重算expected并当身份验证通过。

原题、实际题号与1/5/10锚点不改；OPERATING_01不是给IQS_11改名。标准最终答案继续原 `standard_answers.validate_content`，原题/指标/日期/status/score语义保持。旧schema、fixtures、ResearchRun/owner DTO不改；新载体用本包新protocol，未知版本拒绝，不能伪装旧载体绕校验。

## 实现共同要求

Python模块可复用已有纯工具；CLI `python -m <各包名> --help`，默认无网络，不加载环境key，不执行输入命令。成功stdout机器JSON、错误stderr且非零；输出目录独占创建，不覆盖。严格UTF-8 JSON，重复键/NaN/Infinity/未知字段/超界输入拒绝；路径防绝对外跳、`..`、symlink/junction及Windows长路径误处理。不自动安装共享依赖、不改全局Git/Python、不创建远端。

不发收费模型/API搜索；不产生生产owner、正式评分、股票池或预算修改。EVID可用harness已有浏览/搜索读官方公开页面，记录查询次数及来源；工具费用未披露时写unknown，不能宣称项目总费用0。不给脚本注入Brave/Tavily/ZAI等key，不调付费API，不另写检索客户端。不保存财报/PDF/原始全文HTML或隐藏思考。

测试使用自己的临时工作区和合成provider，禁真实网络/外根写；EVID的人工核源与离线测试分开。失败也finally清理自己创建的文件/进程/端口，递归删除前核resolved路径属于自己测试根；冻结输入/用户文件/既有数据不删。保留必要日志和输入引用。真实公司数据用于数据流和已核事实反例，不伪造真实owner正例或金融gold。

## 交接格式

各自根 `docs/handoff/<PACKAGE-ID>/`：report.md、handoff.json、tests.json、artifacts.json、cleanup.json。对应模板在卡片同目录。

- report：公开签名/协议/CLI实例、复用位置、完成与未完成、兼容矩阵、边界/失败语义、实际测试与skip、最小接入示例。不能只给截图或“测试全绿”。
- tests：argv数组/cwd/UTC开始结束/exit_code/pass-fail-skip/真实stdout-stderr引用及rawSHA；留关键RED与最终整包结果即可，不做每helper审查。
- artifacts每项 `{path, bytes, sha256, role}`，相对自己根；只列源码/schema/fixtures/报告/必要日志，不含.git/缓存/密钥。artifacts不hash自身或handoff；handoff引用artifacts的hash。
- cleanup：自己创建的绝对测试根、运行前状态、清理数/字节/进程端口、结束后剩余及理由。不声称清掉所有文件，却把生成资源留在外仓。
- handoff：填package_id、status=delivered_candidate、source input_lock rawSHA、branch、payload_commit、package/schema版本、artifacts引用、tests/report/cleanup路径、实际API调用数与limitations/unrun；production_ready=false/financial_qualification_granted=false。不要为元数据commit自引用无限改hash；先代码payload commit、再交接commit，最终HEAD另行报告。

在自己根正常提交，不自动push或新建remote。总控收到后只读冻结、整包验收和最终接入。工人不互相发消息/派任务，不等另一新包；需要接口改变在自己根写proposal，不能修改共享合同逼其他writer跟进。

## 总控保留范围

本轮不接管原生预算未知请求恢复，不解除USD0.10预留，不重置旧账或消费旧确认。SESSION只交注入式会话策略，CLAIM只交核查/批判输入，EVID只交资料及检索计划。真实模型/搜索对照、跨模型复问、实际owner与预算准入、结果入库/UI均由总控负责。三包成功不代表金融/生产门关闭。
