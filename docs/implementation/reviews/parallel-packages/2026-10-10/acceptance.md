# EVID-REF-02 / FACT-CONTENT-01 集中验收

结论：两包均为 `changes_requested`。交付成果保留，不能作为已签收的准确性基准或生产事实语义 oracle。本轮没有代改源仓。整改卡独立、目录互斥：[EVID-REF-02-R1](EVID-REF-02-R1.md)、[FACT-CONTENT-01-R1](FACT-CONTENT-01-R1.md)。每卡修复后只回到本次包级验收，不增加小节点审查。

## 固定输入与实际检查

| 包 | 接收 HEAD / 分支 | 产品 commit | 实际包级回归 | 公开 handoff 结构预检 |
|---|---|---|---|---|
| EVID-REF-02 | `1597a08e38a485264b94b4528761a3d5dcf02cec` / `codex/evid-lab-01` | `369d17d2286678a5a3c3310eb34a59676b5f80a8` | 182 passed，0 failed/error/skip，pytest 63.290s；控制器69.231s | exit 2，schema_invalid |
| FACT-CONTENT-01 | `f7fb07895e36ebff67f2ba8932a592fd569cb9cd` / `codex/fact-content-01` | `3ffedfcf634841761bf1cd922eb580c1ed5c04e8` | 77 passed，0 failed/error/skip，pytest35.619s；控制器36.476s | exit 0，仅形状/自述范围有效 |

两个产品 commit 均真实存在且为接收 HEAD 的祖先。241个受控源文件逐字节固定到 IQS `runs/p114a`；213个输入锁原件无漂移，73个工件清单条目 bytes/SHA 全部匹配。EVID原 `.codegraph/.gitignore`、`.codegraph/config.json` 未跟踪设施保留；FACT工作树clean。两仓没有remote，不添加远端。

回归在各自副本运行，禁用插件自动加载、清空凭据可用性、TEMP/PYTHONPATH/子进程归属本轮。外层 socket 守卫及各包原守卫保持；公开CLI子进程也隔离。下面的counterexample脚本自身exit0只表示复现完成，**不表示产品安全断言通过**。

| 集中复现 | 原始记录 | 结果 |
|---|---|---|
| EVID第一次 | 本机原始记录：`docs/implementation/intake/parallel-packages/2026-10-10/logs/evid-counterexamples-01.stdout.log` | 9个缺陷复现；秘密路径例因控制器ref_id不合schema而提前exit2 |
| EVID仅修正该fixture | 本机原始记录：`docs/implementation/intake/parallel-packages/2026-10-10/logs/evid-nested-secret-corrected-02.stdout.log` | 合法INP-9999后嵌套假秘密路径仍被读入并exit0；补齐第10个缺陷 |
| FACT一次 | 本机原始记录：`docs/implementation/intake/parallel-packages/2026-10-10/logs/fact-counterexamples-01.stdout.log` | 6个机械缺陷复现；4项原内容矛盾另由独立包级审查，不冒充执行结果 |

完整指令、PID、终态、stdout/stderr SHA 留在本机 `docs/implementation/intake/parallel-packages/2026-10-10/logs/*.result.json`；该 intake 日志路径受仓库 `logs/` 忽略规则覆盖，没有纳入提交。JUnit是准确分母；EVID交接自述134不符合本轮实际182，其中新reference tests为64，不能照抄旧数字。FACT32个rejection/9个export/13个semantics与其case-map自述26/8/11不符。起始PWF转述EVID预检exit1，以本轮实际公开入口原始回执exit2更正；拒绝内容一直是schema_invalid，不能把转述当进程证据。

## EVID阻断

1. **资格和未知态没有进入正确性判断。** CSC F01–F05 `source_checked=failed`，相等数值仍numeric supported；原交付110个item里有30条这样的CSC历史答案。unknown/null也判supported（原17条F06），与自述unknown永不计正确的政策冲突。需要保留“数值一致”和“遵守弃答”记录，但它们不能充当准确性通过。
2. **评分依据不足，却用宽区间当oracle。** CATL和Alphabet IQS_10缺ROIC/WACC同口径支持，仍给[4,9]并把7分判supported；CATL其他年份的叙述也没有进入区间依据约束。不能靠行业优势说明替代资本回报问题的证据。
3. **缺答从分母消失。** 原六题请求保留F01–F06、删除F02后，真实evaluate CLI exit0且只产生五条。请求范围、缺答、未请求的登记槽位必须分别显示。原110条仅覆盖24个不同槽位，不等于48槽完整评测。
4. **身份与自身对比，未核被冻结外部身份。** 同时将中信建投公司和全部issuer记录改成中信证券并重封hash，真实validate仍exit0。必须绑定锁内公司身份与H股挂牌，不靠可变company_refs自洽。
5. **嵌套秘密路径未拒绝，输出范围过宽。** 自有 `{}` 假api_key.json作为input_ref后被读入，真实validate exit0；没有触碰任何真实秘密。输出到副本旧EVID-LAB-01交接目录新子目录也成功，越过原卡写边界。
6. **未发现关键词冲突，被误称文字/会计口径支持。** `2024。` 或“2024是比较年；2023年收入为166.77…”均text supported。reporting_basis和listing答案字段在normalize丢失后，subject维度仍宣称basis binding。
7. **交接合同不闭合。** handoff不符合既有1.0.0 schema，task_ids和authorized_paths不正确；缺原RED/失败/GREEN stdout/stderr/exit，logs仅relocated-receipts.json。实际新增tests/conftest.py与自述reports在原精确卡范围之外；后续卡只明确限定所需兼容hunk，不追认历史越界为合规。

诚实缺口本身可以接受：CSC网页只提供标题，未读取PDF；人类金标准未请求；旧引文无法重建。**拒收原因是把这些缺口继续算正确，不是缺口存在。** 主控另只读打开[CATL原网页](https://www.catl.com/en/news/6278.html)，确认文中同时出现37.5%和26.9%；保留冲突正确。SEC原JSON通过当前网页工具打开失败，不据此否定原采集，也不宣称本轮已独立核实Alphabet数字。主控此次公开网页读取2次（1成功/1失败），不是network=false；无收费搜索/LLM/文档下载。

## FACT阻断

1. **源question/file SHA未绑定。** 改FACT_02两hash为全零、重封pack，省略可选question-map视图，实际validate exit0。
2. **拒绝测试假阳性。** 同样错误pack带旧视图时exit4只因source_pack_id漂移；原负例只断言任意exit4，不能证明题目hash、术语或关系的目标检查。
3. **导出重读未验证输入，可越界覆盖。** 实际validate成功后，受控故障注入仅替换副本cases为case_id=`../../sentinel`。真实export实现导出成功、带旧hash，并覆盖输出根父目录的自有sentinel.json。未覆盖真实源文件；这是确定性TOCTOU反例，不是测试替代产品validator。
4. **语义标签缺少结构化判定目标。** 渠道事实supports distributes_via，标签false理由却否认未声明的sells_to终端关系；设备使用也拿制造销售作否定。FC12把字节重放当业务关系支持。需要分离source_facts和被判定claim/query。
5. **内部语义矛盾未拒绝。** evidence=explicitly_absent、内容明确“未使用”却保持supported/strict=true，重新封所有hash后仍exit0；2026-99-99也被接受。不是要求发明生产F05算法，而是本包内部一致性检查。
6. **写边界由schema override扩大。** 把schema查找指向副本Lab之外、但在本轮自有根内的目录，真实export允许写该目录。schema查找不应重新定义授权包根。输入reparse和真实provenance的锁内绑定也需同一包补足。
7. **原内容矛盾。** FC07身份未核/evidence conflicting却用false代unknown；FC10关系2025年底终止却2026当前strict=true；子公司继承集团与二者不等价规则冲突；cycle_sensitive与recovery互斥不合理且无待决说明。需整体内容修正，保留周期低谷/反转组合，不能为测试漂白答案。

可以保留61题ID/field/module/order/max_items、五轴模块、原关系码/候选新增码分离、全部synthetic/not_run声明。它们不受本轮退回影响。正式TermRelease/F05/生产owner映射pending本身不是包内缺陷。

## 接续与清理

两整改卡互不依赖，总控没有向其他harness发消息或自动启动。原C06/W15 checkpoint07和`runs/c15a`继续保留；G3/F05/L03/B01/真实金融gold/TH-IN/全池门未关闭。精确同批修复后分别一次包级复验，不重新做已经验收的UI/备份或旧工程回执。

运行副本结束后只清本轮`runs/p114a`：先保存必要日志/反例结果，核源仓241字节、锁213、源Git和全部子进程终态；严格lstat/reparse/单硬链与清理集合bytes/SHA复核，再删除。实际结果以本轮`cleanup.json`为准；没有该终态回执前不宣称cleaned。所有正式原交付、共享TEMP、其他活根、未知nul/opencode和生产库不动。
