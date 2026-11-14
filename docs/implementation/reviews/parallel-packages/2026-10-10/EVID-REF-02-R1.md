# EVID-REF-02-R1：参考资格、完整分母与安全交接整改

这是原EVID-REF-02同一次包级验收的整改续卡，不是新研究项目。可以独立交给一个harness；唯一写目录 `C:/Users/郑曾波/Projects/iqs-evidence-lab`。FACT、IQS、StockQA、StockWiki等全只读；不与FACT整改共享临时根。总控尚未派发，收到人类指令后核本仓唯一writer。

## 必读与接收基线

- [原施工卡](../../../parallel-lanes/packages/2026-10-10/EVID-REF-02.md)、[共同规范](../../../parallel-lanes/packages/2026-10-10/handoff-rules.md)、[原输入锁](../../../parallel-lanes/packages/2026-10-10/inputs.lock.json)、[原manifest](../../../parallel-lanes/packages/2026-10-10/manifest.json)。原授权、轻量、不下载文档和一次包级审查规则保持。
- [实际验收结论](acceptance.md)、[集中复现脚本](acceptance_counterexamples.py)。脚本是controller证据，不得照抄输出或机械固化本次bug。原raw结果在IQS `docs/implementation/intake/parallel-packages/2026-10-10/logs/evid-*`；本卡已列所有必要断言，无需聊天。
- 实际接收 `codex/evid-lab-01@1597a08e38a485264b94b4528761a3d5dcf02cec`，产品`369d17d2286678a5a3c3310eb34a59676b5f80a8`。源受控树无改动，仅原CodeGraph两项未跟踪设施。无remote，不新增远端。开工重新核HEAD/status/固定输入SHA；无关HEAD前进不自动回退，相关字节漂移交总控。从该实际HEAD正常新建 `codex/evid-ref-02-r1`，不要reset/clean/stash旧成果。

写白名单：原 `src/iqs_evidence_lab/reference/`、本包reference schemas/fixtures/tests、`tools/reference_entry.py`；新增本包范围内的版本schema/fixtures；`docs/handoff/EVID-REF-02/remediation-01/`。原`tests/conftest.py`仅允许保留/完善已有receipt路径override的最小隔离兼容hunk（默认旧行为不变），这项是本卡明确限定扩展，不追认上轮越界。其他旧Lab源码/guards/hashing/cli/诊断/fixtures/旧交接/生产仓禁止写。不要重写已交付reports；可在本包remediation目录生成新版结果并明确旧评测非合格准确性基准。

宿主pin `PWF_PLAN_ROOT=C:/Users/郑曾波/Projects/iqs-evidence-lab/docs/handoff/EVID-REF-02/remediation-01/planning`；独占三份PWF，原计划/交付文档只读。全部旧交付bytes留档或从完整commit可重建，升级不能丢旧未知态/历史模型/日期/题目ID。

## 实施顺序与必须覆盖的断言

1. **先固化有鉴别力的RED。** 使用原pack/历史答案，明确资格不足、缺答、双方同步错主体、合规假秘密输入和旧目录输出的实际拒绝原因。每个反例有原validator正常控制例，不能让无关schema/hash错误代替目标失败。原ER08第一次INP-FAKESECRET不合法是controller fixture错误；正式反例使用合法INP-9999和自有`{}`，绝不读真实key。
2. **资格与机械一致性分开。** 数值一致可另记，但source_checked非passed、来源冲突/关键口径缺失不能numeric_accuracy=supported；unknown、弃答遵守与事实得到证实分别记录，未知永不计正确或零。历史raw答案不改。citation是否支持当前claim独立判断，不以URL存在或双模型同意授予真值。
3. **评分证据与题义绑定。** 无ROIC/WACC同口径时IQS_10区间必须null/insufficient；其他评分区间的锚点/端点/反证逐条可追溯，无独立人类gold不填唯一正确分数。不能拿份额/盈利替代资本回报题；年份/发行人/会计scope/景气常态不匹配保留not_verifiable。保留周期低谷、优势保全/不可逆衰退/资金窗口的区别。
4. **分母闭合。** 从锁内实际请求题集/manifest得到expected_question_ids；每run显示requested/answered/missing/unknown，全部已请求缺答保留item或明确拒绝不完整输入；登记但未请求的槽位单列not_evaluated，不硬拼48为每run请求。重复ID拒绝、额外题目拒绝、同回答复跑不增加独立金融样本。原六题删除F02仍须六个请求单位，不能降为五。
5. **外部身份、文字及口径绑定。** 消费锁内companies/实际身份原件，核cncb_h=中信建投/06066/HKEX；公司与record一起改成中信证券或A股必须拒绝。reporting_basis/listing仅在答案实际声明可核时判断，没有字段就是not_verifiable，不推断。`2024。`不能证明文字正确；混入比较年也不自动放行。可自动检明确矛盾，不能用“未找到冲突词”作为语义支持。
6. **读写边界闭合。** 所有顶层、嵌套input/answer/schema路径在读取前拒秘密、symlink/junction/reparse和越界；守卫不能只管CLI参数名。只许本包明确输出根（如remediation-01/generated和专有临时根），旧交接/源码等输出exit3；staging祖先也检查，重复输出exclusive。秘密拒绝exit6、普通输入/schema/hash错误2、内部约束4，正常控制不能被一并禁用。
7. **补标准交接与诚实证据。** 使用既有handoff schema1.0.0和原package_id=`EVID-REF-02`、lane=`iqs`、task_ids=`L02,B01`；真实result_commit/branch，authorized_paths是实际本卡路径。旧原RED/GREEN若无法恢复明确unavailable，不伪造；本轮RED/失败/最终GREEN/raw exit全部保留。Junit精确分组/selector/log SHA，原182回归与64reference不得再写成134。收集网页次数与离线CLI次数分开，不填网络false冒充网页0。

允许版本化新evaluation（例如1.1.0）增加完整分母/资格字段；保留1.0.0只读解析和旧字节，不在旧1.0.0上静默改字段意义。interfaces写迁移、旧结果缺少哪些新资格、unsupported未来版本怎么拒绝；旧结果不能补造证据。新pack来源缺口可以诚实未解决，不强求PDF或全30题评分实证；不能把缺口算通过。

## 集中测试与交接

开发只跑受影响测试。最终一次相关完整Lab回归（旧guards等保护回归必须在此批，非新增门）+实际validate/evaluate/summarize CLI+上述独立正反例；不跑付费模型、重做旧备份/UI。包级内容审查只回同一验收；修复后的新字节复验，不重复未变GREEN。

每次执行全新短独占根，env无key可用性，父子进程离线；不在旧EVID-LAB-01目录写测试receipt。原始日志和PID/exit/时间/源SHA入remediation-01/logs；终态后严格清自己的临时副本与网页短暂缓存，保留必要轻量工件，不动共享TEMP或他人文件。

交付到 `docs/handoff/EVID-REF-02/remediation-01/`：标准handoff.json/summary/artifacts/interfaces/case-map/isolation/三PWF、逐ER修复映射、新reference/evaluation/完整覆盖与冲突清单。artifacts原字节SHA包括所有执行候选与日志，不循环hash；既有交付不覆盖。正常精确git add/产品commit后引用完整真实commit，最终交接commit也写明；无remote不用push。总控用原manifest+原package_id公开预检新handoff，再一次包级核新源和反例。

完成只解除本包缺陷。G3/F05/F01/F06/L03/B01整体、真实金融gold、TH/IN和200家/全池/生产发布仍归总控，不要填写已关闭。无需为了普通包内修复再次申请既有用户授权；若确需改白名单之外的旧公共源码，先给总控具体反例和最小路径，不自扩范围。
