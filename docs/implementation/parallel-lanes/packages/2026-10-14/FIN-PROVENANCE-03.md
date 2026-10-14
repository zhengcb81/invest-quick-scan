# FIN-PROVENANCE-03 独立施工卡

唯一工作目录：**C:/Users/郑曾波/Projects/iqs-fin-provenance-lab**。只创建/修改此新根，不写其他任何仓或共享PWF。准备时根不存在；开工重查唯一writer。分支codex/fin-provenance-03。

必须先读[common-rules.md](common-rules.md)、[integration-contract.md](integration-contract.md)、[manifest.json](manifest.json)、[inputs.lock.json](inputs.lock.json)、[FIN-PROVENANCE-03.targets.json](FIN-PROVENANCE-03.targets.json)、[FIN-PROVENANCE-03.handoff.template.json](FIN-PROVENANCE-03.handoff.template.json)。本卡包含自己的范围/实现/测试/交接；不需要与其他harness聊天或等待它们结果。

输入仓：iqs, fin, blind，逐条rawSHA复制到fixtures；冻结快照运输路径见锁，不能用现有原仓latest替代。新公开主协议iqs.fin_reference_bundle_candidate/1.0.0，主文件content/reference-bundle.json，module=iqs_fin_provenance_lab。全部candidate-only，owner not_mapped、production not_run、qualification false；cutoff=2026-10-13。

## 要解决的实际问题

上轮BLIND运行实际冻结FIN validate_pack返回9个错误（3 manifest missing、6 locked_input_missing），但金融原Lab中6个manifest/questions实际存在。优先定位运输/依赖路径/完整冻结问题，不预设金融原内容已坏，不重做金融90题研究。目标是一个搬走仍能检验的闭合reference bundle及准确错误诊断。

## 实施步骤

1. 开工/PWF，核本批锁覆盖FIN所有输入，尤其fixtures/locked-inputs/runs/c16b/formal-routes/{alphabet,catl,cncb_h}-questions/{manifest,questions}.json六件；复制实际ignored依赖。读取冻结runtime-reuse.json（IQS runs/next-acceptance-2026-10-14-02/reviews/blind/），定位blind/fixtures/fin与fin原快照差异。先在临时transport副本有意缺6件/路径错/改1字节做真实RED，记录文件缺失与内容不符不同错误，不更改冻结原件。
2. 显式根运行冻结金融公开validator，分别“完整fin副本”“旧blind嵌套fin副本”“完整fin搬迁目录”三个场景。report列真实是否复现9错误、实际错误代码及根。FIN原valid只代表reference_artifact_only，不代表内容金融正确。不得放宽validator、伪造返回值、删lock项或把missing当optional。
3. 建source dependency graph：90references原ID/原题、3question manifests、每题question文本与对象SHA、1058fact原ID、62source、calculation-ledger的operand/source关系、所有locked files逐一验证存在/rawSHA。数量以冻结实际文件为准，若目标计数不符报告差异而非增造；90 expected_score全null。所有unused/orphan输入另列，不删除原事实/旧gap。
4. 便携bundle复制原公有pack/ledger/旧锁/完整依赖/所需schema与代码，先守路径/数量/累计bytes上限，再核hash；不带.private、文档、真实DB或原流程tmp。旧输入锁不修改，new bundle manifest单独记录原根→bundle相对路径、source commit、rawSHA/bytes。bundle自身manifest不包含自己避免自引用；assembly metadata与物料hash分开。
5. 复用原FIN validate/export，增加薄wrapper validate-bundle/export-bundle，只解析显式--reference-pack/--ledger/--reference-inputs-lock/--reference-input-root/--output，实际原validator消费同一root/同一文件；原实现必须root由__file__取时完整复制产品于自有runtime根并说明，不monkeypatch校验。不得校原A却导副本B。搬迁后只能读bundle自身deps；源仓不存在/deny时也能验证，禁止自动回源“补齐”。
6. 若原schema确需新增运输字段则新协议独立版本或独立bundle侧车，不同版加字段；原金融pack1.2、ledger1.0、评分/计量定义保持。若真实原字节不符或缺失，只从本批锁中能够独立核同hash原件恢复；没有同hash原件保持missing，不从模型/二手资料/另harness重算后说原件恢复。源patch提案必须精确old/newSHA，不能在金融原库写。
7. TDD一个集中软件包，公开CLI validate/export实际执行、两次确定性bundle、中文空格/异cwd、搬到独立目录后断开原root再验证。给90题完整索引和哪些金融资料仍partial/unverified清单。收尾做PID/临时路径闭包、正常提交、六份交接。

## 输出与验收

content/reference-bundle.json主records一条对应一原reference，FP03-R001–090按冻结原序。payload严格{reference_id,company_key,question_id,question_ref,dependency_refs,closure_status,diagnostic_refs,financial_status,expected_score}；closure_status=closed|missing|mismatch，financial_status原样引用不自行评议，expected_score恒null。若原90数量不符停止结构完整声明，保留差异。

另交bundle-manifest、dependency-graph、transport-difference-report、missing-inputs-ledger、实际validate收据、可搬迁完整候选bundle与精准补丁提案。历史9错误收据只读保留；新manifest不是给旧历史重新签名。bundle闭合不关闭F05金融验收、G3或生产门。

## 重点测试包（一个大节点）

单元：六原件缺失、单字节错、错误文件替代、跨公司question相同名字、全对象/文本/rawSHA不同、ledger operand指错source、共享dependency重复读预算、超限拒绝、null保持。

集成：实际原FIN函数spy、完整与旧嵌套副本差异、caller选择路径真实消费；原1.0/1.1/1.2支持语义保留、未知未来拒绝；copied product根正确，无外部路径或自动回源。

E2E：原public validate/export→完整bundle→中文空格目录搬迁→原validate重验；删/换题与source不闭合负例；原根不可访问时仍能做成功/缺失拒绝；拒覆盖、失败不留正式半包、路径穿越/链接逃逸。实际FIN错误若不只9条保留全部；structure closure与金融内容真伪是两张结果表。

不做新公司、联网、报表下载、模型/搜索调用或新金融打分，不依赖另外两包结果。
