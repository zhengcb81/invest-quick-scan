# RESUME-CHAOS-06 独立验收与隔离修复

原交付不能直接签收；有效缺口已在本目录`snapshot/`修复并验证，通过候选待总控按`patch-cas.json`精确写回、正常提交和绑定新payload。源仓、原输入和PWF未修改。

源HEAD `b9b9744fd87e9dc15f13a3c212835d9c0a2442ba`；原payload `7e535aa46f16d85142ddc8ba6a2559215dca9981`；锁raw SHA `968fc8a41653e24e0701feea9bc75353bff90e923ecd96f37f6b8334818d1233`。120份artifacts逐项bytes/raw SHA一致；冻结125份交付文件，代码/行为文档对原payload Git blob核对，明确CRLF转换的文本规范化一致；后置review/handoff元数据对最终HEAD核对，不误把自引用约定当缺陷。结束125份源字节、456份锁内consumer（5,877,448 bytes）仍一致，没有追当前SDK或改schema20。

## 有效发现及修复

1. **P1 未核执行源码便导入**。原validate只核锁文件SHA，随后导入SESSION pathsafety来写输出；run也在核consumer前调用冻结guard。独立将隔离副本pathsafety.py追加无害marker写入，公开validate实际exit0且marker出现。已改所有CLI、run API、`-I` worker在任何冻结执行代码之前核全456文件；重试反例exit2且marker未出现。锁解析拒重复JSON/路径大小写碰撞/相对外跳/根链接/缺文件/hash或bytes错，不依赖source_path活动仓。
2. **P2 summary给篡改报告盖新章**。原报告HTTP被改999，或source_context锁改全0且保留原content/semantic hash，summarize仍exit0。现验证内容摘要、语义摘要、上下文、protocol/package版本、计划ID/唯一计数及非负观测；各反例exit2。旧业务1.0.0合法完整报告仍通过；原3个裸dict单元fixture补完整报告信封，独立数字判断原断言保留。
3. **P2 输出冲突检查过晚**。已占用输出最终exit3，却先执行28case并创建SQLite/子进程。现先预检存在、输入/源码重叠和路径，才调用run；反例exit3、原文件不变、test-root完全不存在。
4. **P2 worker隔离绕开外层guard**。`-I`忽略PYTHONPATH，原worker只有socket guard，没有写根audit。现worker内部显式装禁网/自有写根、foreign SQLite/move/link audit并先核consumer，真实`-I`子进程外写反例被拒且文件不存在。
5. **P2 worker超时可能遗留PID**。原communicate(timeout=180)无TimeoutExpired收口。现先校验有限超时范围，超时仅kill此Popen实例并communicate等待，返回timed_out/PID/退出码。真实sleep子进程0.1秒超时被终止，实际PID与已不存在状态见timeout-kill-evidence.json；未按进程名杀任何进程，不把这个Lab生命周期测试冒充原SDK发后故障。
6. **P2 同目录文件可冒充冻结模块**。原verify_frozen_modules允许实际__file__仅与目标同parent。现必须精确目标文件；同目录其他文件反例拒绝。
7. **P2 指数溢出不属有限JSON**。原strict_json_load拒NaN/Infinity字面却允许1e999→inf。现parse_float拒非有限结果，新增反例。金额未知不由此归零。
8. **可复现性补全**。作者测试固定旧inputs绝对根，隔离验证不能去执行其代码。新增显式非密钥IQS_CHAOS_INPUTS测试选择，通过收集hook仅替换测试根；CLI仍显式路径，源码/冻结内容不改。README的旧58测试口径修为原63及新增回归，明确四个能力缺口。

## 原链真实性与实际结果

完整公开CLI validate→run28→summarize独立实跑，原QuickScanWorkStore schema20/permit/ResearchChatSession/SESSION1.0.2/CODEC1.0.1/AnswerSink均来自锁内模块，HTTP仅在原transport边界mock。原样及修复后的完整运行都观察到20次synthetic HTTP调用、28case、0未决finding/执行错误；逐case状态和观察摘要见case-observation-audit.json，完整synthetic报告另保留。不是实际模型API或真实联网结果。

独立核查：发送前预算/空context/route不准HTTP0；reserve/consume后退出仍in_flight；发后timeout/reset仍outcome_uncertain；重启未新增HTTP；200坏schema/tool args/缺usage/actual model错配仍response_unpriced；401为failure_unpriced，不假返0；checkpoint恢复及重复题拒绝；同公司3段累计3请求；原子批不半提交；原task封存未知后仅新独立task获准，ordinary无豁免；amend保留旧row；旧runtime/foreign文件保留。

另加原SDK非法usage实测：prompt_tokens=-1的HTTP200后，原store为response_unpriced，reserved_cost_micros=1,000,000、actual_cost_micros=null、request_counted=1，未变成免费settled答案。该单次是synthetic transport，见invalid-usage-evidence.json，不计真实API或搜索费用。

## 测试与限制

最终**75 passed / 87.58s / 0 skip**：原63+新增12，argv、结果和整个测试期间src/tests字节稳定证明在final-pytest-execution.json及final-short-pytest.log。真实公开CLI反例、report篡改、worker外写/超时独立于作者expected；不只复述自报63pass。

历史失败保留：最初pytest默认logging目标被验收audit拒绝，改显式自有log路径；长隔离basetemp触发Windows MAX_PATH导致C19 fixture写失败（72P/1F），改本根短basetemp后75全过，最长目标238字符。没有改系统设置、伪称修复MAX_PATH或排除失败测试。冻结输入的既有pyc保留原bytes，没有生成新pyc。CodeGraph未初始化按只读源约束使用已知文件fallback，未建索引。

**四项原能力尚未覆盖**：C06内部reserve精确崩溃点、C07内部consume/POST精确窗口、C16原SDK没有发送前凭据拒绝、C27原driver journal内部点。替代公开API/本Lab journal观察不能宣称这些点完整通过。原handoff的remaining_gaps=[]及“one unsupported”旧文字不代表缺口消失；本次仅给离线工程候选通过，生产/金融/评分资格均false。

原外包独审三轮绑定原payload、不同reviewer d04a5178…；其invocation含真实调用自述和prompt而非可独立验证完整工具回执。本次总控实际不同agent `/root/accept_source_time07` 全面重查、修复复核，不重写历史review为已审新候选。新source commit落地后还需总控绑定实际Git blob，不能套旧final。

最小环境不含真实key，HOME/TEMP指自有根，收费/搜索/下载/生产写均0。8个自有运行临时树已删除，自己的worker均已退出，未开端口；保留源交付的原synthetic SQLite证据副本、锁内consumer、薄运行报告/logs/CAS，见cleanup.json，不声称复原宿主已有状态。patch-cas.json精确10文件，原SHA为冻结交付，after为待写回候选，不包含任何冻结依赖或PWF修改。
