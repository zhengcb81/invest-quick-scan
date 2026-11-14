# FACT-CONTENT-01-R1：冻结来源、独立语义与不可变导出整改

这是FACT-CONTENT-01原包同一次验收的整改续卡，可独立交给harness。唯一写目录 `C:/Users/郑曾波/Projects/iqs-fact-content-lab`；EVID/IQS/StockQA/StockWiki等全只读。与EVID整改不共享输出/库/缓存/临时根；总控尚未派发，先核本仓唯一writer。

## 必读与实际基线

- [原施工卡](../../../parallel-lanes/packages/2026-10-10/FACT-CONTENT-01.md)、[共同规范](../../../parallel-lanes/packages/2026-10-10/handoff-rules.md)、[冻结输入](../../../parallel-lanes/packages/2026-10-10/inputs.lock.json)、[manifest](../../../parallel-lanes/packages/2026-10-10/manifest.json)、[本次验收](acceptance.md)。不用聊天上下文。
- 接收`codex/fact-content-01@f7fb07895e36ebff67f2ba8932a592fd569cb9cd`，产品`3ffedfcf634841761bf1cd922eb580c1ed5c04e8`，clean、无remote。开工重新核HEAD/status和锁原件，保留后来的无关变化，不回退。已有branch可继续或正常建`codex/fact-content-01-r1`，记录实际完整commit，不创建远端。
- [反例脚本](acceptance_counterexamples.py)的fact模式和原stdout在IQS `docs/implementation/intake/parallel-packages/2026-10-10/logs/fact-counterexamples-01.stdout.log`。source哈希、阴性兜底、explicitly_absent、非法日期、验证后替换cases、schema覆盖根六项实际已复现。脚本只为复现输入，不能把它输出当新oracle。

白名单沿用原README/.gitignore/pyproject、src/schemas/content/tests/fixtures/tools和本包docs路径；交接新增 `docs/handoff/FACT-CONTENT-01/remediation-01/`。不能修改原61题源、IQS语义生产规则或StockWiki owner，不另建事实DB/匹配引擎/生产金标准。旧候选pack/case和日志通过原commit及具名版本归档保持可重建，不删旧交付/历史未知态。

PWF宿主pin `C:/Users/郑曾波/Projects/iqs-fact-content-lab/docs/handoff/FACT-CONTENT-01/remediation-01/planning`；不写IQS根计划或全局selector。未初始化CodeGraph按本仓AGENTS询问，精确已知文件只读不受影响；不能为测试隐瞒改全局设置。

## 实施步骤

1. **先纠正测试独立性。** 所有变异pack同步可选question-map view，或明确省略并给正常无view控制。阴性断言检查目标错误码/路径/内容，不能接受任意exit4。独立assert错误source SHA和源正确对照；改变其他字段不应触发无关source_pack_id错误掩盖目标。保留首次RED和失败原件。
2. **每行来源绑定。** 冻结61题的ID/field/module/order/max_items/applicability不变；source_question_sha256按实际锁内question对象规范序列化重算，source_file_sha256绑定该实际锁内raw file，不只看proposal与row自洽。错题义、顺序、hash、源文件/version拒绝；根文件/hash域和Git EOL分开。
3. **先验证快照，再仅导出该快照。** validate返回不可变对象/字节及已核摘要，export不重新普通json.loads读取未验证源。即使验证后磁盘替换/删除/重复键/新case_id，输出仍为已核快照或干净拒绝，不带旧hash输出新body。封装完整schema、case_id纯文件名、生成路径再次约束在新exclusive根内。覆盖自有哨兵的`../../sentinel`反例必须变成拒绝/哨兵不变；输出根存在不能写，失败不得留下半成品或覆盖其他文件。
4. **source facts 与被判定target分开。** 每case显式claim/query target的relation、主体位置、对象类型、segment、as_of/历史basis/商业stage；三个标签精确针对这个target，附独立理由。渠道事实可以支持distributes_via，同时不能证明sells_to终端客户；设备使用与制造/销售、OEM与ODM、候选第二曲线与商业化/收入、职位和治理判断各自有独立目标。关系码仍原码为主，新增候选单列；不建立生产查询算法。
5. **补内部一致性拒绝。** 有效calendar date、起止次序与有效区间、scope/分部、evidence_state、身份和commercial stage进入目标一致性检查：explicitly_absent不能支持同一target、未核身份/conflicting是unknown、当前已终止关系不能strict true、qualified不能替商业供应或量产、对称关系也核两端kind。历史关系按真实历史target保留，不因当前失效删除历史；unknown不混同false/零。真实来源case的provenance必须是允许锁内原件且raw SHA匹配，不凭字段存在升级资格。
6. **修正原内容整体。** FC07-homophone-name未核身份保持unknown；FC10拆明确历史供应与认证候选（主体/对象/目标/时期分开）；FC12字节复现只属软件检查，业务target另需真实合成事实支持或unknown。子公司与集团用正确类型/包含关系，不能把集团成员当同义或细分继承。cycle_sensitive与recovery可组合，保留当前差/优势仍存/修复待证及不可逆风险；银行保险复合业务的明确unresolved保持，不强定人为互斥。45原case不得为“排除失败”而删减，按case_id记录目标/标签纠正和版本差异。
7. **固定边界与可兼容版本。** schema目录override只影响查schema，不能改repo授权输出根；读之前检查顶层/嵌套路径、secret和symlink/junction/reparse，不resolve后丢链信息。验证和输出整个链均无网络/keys。增加target的schema/envelope须具名新版本（例如1.1.0），保留1.0.0只读解释/旧字节；旧ambiguous case标needs_review/unknown，不能静默假装有target或把旧语义改掉。interfaces完整写版本选择、旧缺字段处理、未来版本拒绝、hash域；production_mapping仍not_mapped，全部生产case_status仍not_run。
8. **补精确交接。** 旧交接GREEN77是真实本轮原回归，但不代表负例目标正确。新case-map用实际JUnit selector/精确分母/log raw SHA，纠正旧rejection32、export9、semantics13及各FC数量；原日志保留。标准handoff沿用1.0.0、package_id=`FACT-CONTENT-01`、lane=`iqs`、task_ids=`F01,F03,F04,F05,F06,V03,V07`，实际result_commit与source白名单。模板结构合格不替实质门。

## 集中验收与交付

TDD开发仅受影响测试，最终一次整包相关回归+真实validate-pack/export-cases CLI+六个独立正反例，以及一次整体case/ontology内容复核；修复在同一审查续收，不给helper加门。不跑付费/网页/LLM、不重做原UI/备份或TH/IN预研。新目标case独立oracle审查需核来源/target/period，不照抄expected_labels验自身。

全程offline，API钥匙不传入测试环境。每次全新独占短根，所有pytest/子进程/cache/TEMP归此根；不用共享固定TEMP。验证后换文件测试只使用自有sentinel，不制造真实越界写入。终态后清自己的副本，严格路径/reparse/单硬链/集合与bytes-SHA，保留原stdout/stderr/exit/PID；不对别人未知残留清理或伪称cleaned。

交到 `docs/handoff/FACT-CONTENT-01/remediation-01/`：标准handoff/summary/artifacts/interfaces/case-map/isolation/三PWF、新候选pack/明确target的case、61题映射校验、全部变更说明、原内容问题逐项处置。原byte快照/commit可重建，artifacts不循环hash。正常精确git add，产品/测试commit后写完整真实hash，再提交交接；无remote不push。总控用原manifest和原package_id检新handoff、实际新源与同批反例，一次包级接收。

只修本包缺陷，不关闭F01/F05/F06正式生产发布、TermRelease、owner查询/身份golden、G3/L03/B01/TH-IN/200家/全池门。普通范围内修复已有用户必要授权，不重复请求；白名单外改动须交总控具体输入/最小路径，不自行扩仓。
