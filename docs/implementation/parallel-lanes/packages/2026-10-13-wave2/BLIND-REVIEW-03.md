# BLIND-REVIEW-03：匿名评审包、双人核证与准确性分母工具

独占C:/Users/郑曾波/Projects/iqs-blind-review-lab，分支codex/blind-review-03。读[共同规则](common-rules.md)、[接口](integration-contract.md)、[manifest](manifest.json)、[锁](inputs.lock.json)、[handoff模板](BLIND-REVIEW-03.handoff.template.json)。冻结iqs/evid/fin/score，不依赖新CHAIN，不改EVID/FIN/MATRIX或生产执行器。

## 目标及复用

现有EVID能检历史326答案的hash/来源join，但两位agent分开审196/130，不是同答案双人一致性，也不是人类金融gold。FIN参考仍partial、90分数null；SCORE45合成案例可用于软件期望，不能当公司真值。现要补真实小样本实验可用的匿名评审/同题双人裁决桥，不重写EVID诊断、MATRIX比较器或自动评分器。

## 实施顺序

1. 校冻结输入，探测原EVID hashing/read_json/诊断CLI、FIN pack1.0/1.1/1.2 reader边界和SCORE盲评约定。公开需要的薄适配及实际被复用函数清单；引用旧库只能自有fixtures副本，不执行历史run_checks作者脚本。
2. 定义显式review-input候选适配：每一实验answer对应subject label、question_ref、cutoff/period/scope/basis、原answer rawSHA/规范完整对象SHA、claims/citations/缺失状态以及私有model/search/pack/费用/速度metadata。拒错主体、题义、期间，unsupported原格式不猜补。保留全部输入题分母，包括解析失败/无回答/搜索失败；没有真实输入也能用合成fixtures完成工具。
3. build-packet将metadata、私有映射、文件名/路径/HTML属性中的模型/搜索/费用线索与公开review内容分开。保留原回答事实与引用，不用regex删除公司名/改语义；模型自述在文本内无法完全遮蔽时明确blinding_limit，不声称完美盲法。reasoning_content独立思考正文不进评审公开包；原件hash保留在私有映射，禁止散发思考全文。匿名case ID不能将model名字或成本写进路径。相同输入/显式排序种子确定性输出；相同答案跨不同请求仍保留不同样本而非去重缩分母。
4. 为每个同一answer生成两份独立review template，A/B先不互见。字段包含reviewer_id、answer/object hash、claim_ref、支持/矛盾/不足/不可验证、source定位、score_basis、评分可评区间或null、适用/置信/理由；没有填写就not_reviewed，不自动补accept。工具不调用LLM。两位审不同分区只能算覆盖，不能算agreement。
5. join-reviews严格验证同answer/题义/主体/期间及原hash，重复、额外、缺失、不一致都明确报告。分歧留双记录，另adjudication需explicit裁决人/理由/证据，不按多数模型或两评同意自动产生金融接受。工具不能鉴别人类身份，reviewer声明不等于认证。
6. 报客观事实支持、矛盾、不足、未审、拒答/覆盖、评分区间重叠及双审一致率。accuracy分母=可核的supported+contradicted，review coverage单独列；分母0率=null。主観候选评分/合成oracle一致不混进客观正确率。准确率高但coverage低不能自动winner；默认不设白名单阈值/金融门。费用/速度仅在显式unblind后按原同口径元数据附表，不替代准确性。

## 公开输出与私有边界

module=iqs_blind_review_lab，validate/export按共同接口；build-packet --answers <自有显式输入> --references <固定参考集> --seed <显式字符串> --output <全新公开目录> --private-output <另一个全新私有目录>；join-reviews --packet <公开包> --review-a <A> --review-b <B> [--adjudications <已给裁决>] --output <新目录>。公开/私有输出根不得重叠、不能一个在另一个之下；所有输入验完再发布，两边失败均不留半份正式输出。

主content/blind-review-contract.json，protocol=iqs.blind_review_contract_candidate/1.0.0，records为三个格式接口定义和实际适配范围：review_input、review_packet、review_join；各payload严格{interface_protocol,schema_ref,implementation_entrypoint,supported_input_versions,unsupported_input_versions,qualification_limits}。各接口自有封闭schema/版本及真实最小样例，未来版本拒，旧reader兼容有独立样例，不用任意自由dict躲开引用检查。

build公开目录含packet.json、review-a.template.json、review-b.template.json、readme.md；private映射只在自有明确private/另新目录，不能同export夹入、不能在tests.json/handoff/raw manifest传播真实model解盲表。交付合成private样例可明确synthetic，实际用户私有映射默认Git忽略。packet内qualification_granted=false/owner not_mapped，参考事实必须带candidate_not_financially_accepted；FIN标签不是ground truth，SCORE期望只synthetic oracle。

join输出metrics.json、disagreements.json、review-ledger.json、limitations.md，保留全样本和每分母。纯派生，不签Score/Observation、不访问StockWiki、不重算财务。输入单个≤8MiB、答案≤1000、每答案claim≤64、评审/裁决≤64000；超限拒绝不截断。

## TDD和一次包级检验

至少12个有业务意义的合成情景：实质支持/矛盾/来源不可得/无claim/拒答/坏解析/unknown冒5/期间错/同名主体错/高准确率低覆盖/双评不同分区/双评同样本分歧；引用先验为合成，不能伪装历史真实接受。

先RED：盲包文件名/元数据/HTML属性泄露模型；公开export夹带private映射；删除失败题缩分母；326分区join冒agreement；哈希冲突/两模型同答案被合并；缺review自动接受；多数答案冒真值；null分母变0；reference未来事实或未核candidate变gold。

集中unit、真实EVID/FIN/SCORE副本接口integration、真实子进程CLI E2E及一次包级审查。交接记录完整协议、适配/unsupported列表、真实日志/cleanup、原参考边界和总控接线示例。真正模型调用与至少两位独立盲审由总控后续组织，不为了宣称e2e伪造真人/真实回答/gold。
