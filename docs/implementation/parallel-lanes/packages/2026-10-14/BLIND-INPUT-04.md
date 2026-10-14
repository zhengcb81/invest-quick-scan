# BLIND-INPUT-04 独立施工卡

唯一工作目录：**C:/Users/郑曾波/Projects/iqs-blind-input-lab**。只创建/修改此新根，不写其他任何仓或共享PWF。准备时根不存在；开工重查唯一writer。分支codex/blind-input-04。

必须先读[common-rules.md](common-rules.md)、[integration-contract.md](integration-contract.md)、[manifest.json](manifest.json)、[inputs.lock.json](inputs.lock.json)、[BLIND-INPUT-04.targets.json](BLIND-INPUT-04.targets.json)、[BLIND-INPUT-04.handoff.template.json](BLIND-INPUT-04.handoff.template.json)。本卡包含自己的范围/实现/测试/交接；不需要与其他harness聊天或等待它们结果。

输入仓：iqs, blind, fin，逐条rawSHA复制到fixtures；冻结快照运输路径见锁，不能用现有原仓latest替代。新公开主协议iqs.blind_input_bridge_candidate/1.0.0，主文件content/blind-input-bridge.json，module=iqs_blind_input_lab。全部candidate-only，owner not_mapped、production not_run、qualification false；cutoff=2026-10-13。

## 要解决的实际问题

现BLIND1.1能核显式sidecar和做双审分母，但只支持synthetic reference-set，不是原始模型答案/真实公开参考集通用导入器。补的是清晰输入桥接，不能重造盲评/claim真假判定器。旧FIN冻结副本有3 manifest和6 locked input缺失；本包须保留boundary失败，不依赖另包修好，更不能转成参考集可信。

## 实施步骤

1. 开工/PWF与依赖锁检查；先调查冻结schemas/observation-v1.2.schema.json、answer-content.schema.json，以及blind/src/iqs_blind_review_lab/packet.py、schema.py、frozen.py和实际1.0/1.1例。列准确format/字段对照/不支持项，先做sidecar错hash、主体/期间错绑、打包回答漏题、思考泄露、failed reference边界被标可信的RED。
2. 首个必须实现格式为已声明IQS Observation1.2 + 原answer_content侧车：输入参数逐项指定，不把observation_id/entity_id当合法金融身份确认。旧1.0/1.1仅按原支持表读取。另实现明确带schema/version的单题/多题回答wrapper；如要接供应商原JSON，必须给实际官方shape及封闭格式ID，JSON结构相似不允许自动猜版本。没有真实vendor原样本则将该格式列unsupported，不造一个例子说真实调用已验证。
3. 逐题原slot_id/request/attempt/question原顺序映射；合并回答仍每题一槽。unknown、unparsed、no_answer、search_failed、missing_member、duplicate_member、foreign_question、timeout完整保留。重复同answer_id不同request不能合并成一例；同request同原字节精确重放仅标replay，不夸大独立样本。实际state映射一张封闭表；不把错误默认变answered。引用、单位、期间、题义不由模型猜补；subject/period/hash不能一致时拒正式输出，给诊断ledger。
4. 新答案输入适配输出既有review_input/1.1.0和真实原对象/题目sidecar，调用原BLIND loader/build而非只自验schema。严禁重写原模型事实以符合参考答案；claim抽取只允许显式claims或人工标注，不运行LLM、不把主观评价猜成事实。reasoning_content或<think>混在正文且无法可靠分割时保留槽并标requires_manual_segmentation，只输出hash与诊断，不存思考全文或删掉失败题。原始私有输入留调用者原根，不复制进公开包。
5. 增加显式真实公开reference adapter：source-linked FIN candidate refs/原题/时期/证据限制搬到新版本参考封套，每个reference维持eligible/not_eligible及理由。FIN真validator失败、来源未核、错issuer、future source、period不齐或score null不得升为可信评分oracle；可以把gap作为review_input参考缺口，不能把boundary false变true。选择性eligible必须逐字段声明事实资格，不整体给整个pack盖章。未实现资格判定保持not_eligible。区间/主观质量作为独立判断通道，objective准确性只按实际可审事实。
6. 演进只在自己src/schema的复制品，旧fixtures只读；新reference协议独立版、老synthetic reader语义和样例保留、未知未来拒绝。以显式输入根传FIN包/锁/冻结输入，不能硬编码自己的旧fixtures使调用者参数形同虚设。公开与private目录分开，private只有匿名反查/模型/费用/原SHA、无思考/密钥；依赖路径也是脱敏范围。
7. 薄CLI除validate/export外增加adapt-answers、adapt-references（参数在README固定）；完整公开E2E用本包明确合成transport/公开候选reference，执行adapt→原build-packet→两份显式synthetic handin→原join。该正例只证明软件，真人评审与金融准确率not_run。真实存在的公开candidate参考输入至少选三公司各1题做“读入或明确拒绝”的实际回执，拒绝不隐藏；供应商无真实输入时不能宣称端到端真实API通过。

## 输出与验收

主records至少覆盖targets的12类场景，BI04-R001…固定。payload严格{input_format,output_protocol,support_status,source_refs,mapping_rules,losses,retained_denominator,reference_boundary,test_refs}；support_status=supported|partial|unsupported，losses不能隐藏改写，retained_denominator明示输入slots/输出slots/错误slots/replay。

提交格式支持表、adapter规则schema、原件/题目sidecar、可搬迁输入例、参考资格边界、blind复制产品的精准补丁manifest，以及明确兼容与不支持说明。不提交原始密钥、思考正文、实际private模型回答或真人身份信息。输出schema不得超同版本加字段。

## 重点测试包（一个大节点）

单元：所有state映射、multi题缺/重/外题、同答案不同request、重放不增加样本、错raw/objectSHA、错主体/期间/题义、reasoning混排、预算/未来版；reference未核/9错误不能被升资格、null不得进评分准确率。

集成：所有输入参数实际消费、盲评冻结函数真实调用spy；旧1.0/1.1样例读取兼容；父子禁网与外库写护栏；公开/私有metadata及路径/转义泄露扫描。

E2E：单/多题公开adapt→build→join正例；损坏/缺资料保留全部槽位与null rate；各公司公开candidate实际读入/拒绝；中文空格路径+随机cwd+导出到另一目录重验；失败零正式输出、拒覆盖、越界/junction。partial可收，unsupported不假报通过。

本包不负责新模型请求、报价、真实双人审查、修复FIN原仓或真实StockWiki身份。总控随后才把adapter接实际实验。
