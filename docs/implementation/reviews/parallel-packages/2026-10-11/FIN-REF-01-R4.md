# FIN-REF-01-R4：原三组余项，历史兼容已关

原FIN harness唯一写根 **`C:/Users/郑曾波/Projects/iqs-financial-reference-lab`**；原包接续，不新开writer。先读[R3续验](FIN-REF-01-R3-acceptance.md)、[独立记录](FIN-REF-01-R3-independent-review.md)、[原R3卡](FIN-REF-01-R3.md)及[共同规则](../../../parallel-lanes/packages/2026-10-11-wave2/handoff-rules.md)。只写本Lab原src/content/schemas/tests/tools/fixtures与新交接，不改IQS/StockQA/StockWiki/其他Lab/生产库/全局配置。

## 基线与不返工范围

branch codex/fin-ref-01，base775b6a8、product b86b25feff0b71d97f845bf0dab9eddb8d34c5c2、交接2b9b993dc7683b61a93840386659238f536785ba、实际HEAD04633a7cb4151f6413d64874efe6743bc8d4a262。源仅`.codegraph/`，无remote。开工重核最新HEAD/status，保留其他writer后续变化，不reset。131跟踪/33工件/20冻结输入匹配。

**R2关闭**：实际旧1.0完整性、旧1.1 historical读入口和导出reader已实际通过；不重做。81P、47组既有独立validate/export对（94调用）、单文件5MiB/超限锁读取前拒、1e999严格拒、原计算绑定/期间五实例保留。90题、每公司30、18深核、2026-10-11 cutoff、26 facts和评分null保持，不改原锁/旧schema/原交接。

只读复现根 `C:/Users/郑曾波/Projects/invest-quick-scan/runs/fin-r3-acceptance-2026-10-11-01/`，看named_contract_cases.py、named-contract-cases.json、retained-cases、原logs、scope-check.json；不能在该根写或直接运行controller（内部OWN会写在那里），复制必要小seed到自己owned临时根再改OWN。超限大输入已删，必要时在自身根再生成，结束精确清理。

## R1：如实partial已认可，原研究不自动缩范围

72deferred/not_started仍是原待做研究，不改为已完成或gap；继续原官方HTML定向查证范围，一次访问可支撑多题、逐题准确指支持范围/短定位或真实失败。不要求强填分或90次请求，不保存全文/下载公司文档。不足以完成时明确partial/open_items，不能由writer把延期当总控已批准缩范围。

先同步最小残留：V13/SRC-SEC-10K-HTML“截断Item1A”与“已读Item8/Note6”冲突，精确写实际得到结果的途径；CSC入口/TLS失败不推出filings PDF-only；72not_started review_notes不能称逐题已定向研究；债务quote与已选面值含current定义一致。19访问摘要和7 unique-source映射分开，作者“Proves actual access”不是独立验证声明；保留真实访问日志，不新增网络凭证门，不伪造访问或金融gold。

## R3：把具名方法真正接到经济量与操作数

两个固定小控制，先RED→修复。pack/账hash原本正确，不通过改hash碰巧失败：

1. `fcf-method-relabelled-as-roic`：复制正确FCF entry，改metric=financial.roic、reference_ids=[FR-ALPHABET-IQS_10]、served_question_ids=[IQS_10]；OCF/capex的sub公式、73,266 USD_million/inputs/facts/期间不动。当前validate/export0且发布。注册契约应核metric↔method/输入经济角色/结果单位，不能只按作者的metric映射题ID。预期2/2、无正式输出，目标明确为题义/经济量不兼容。允许合法ROIC ratio或NOPAT/平均IC使用明确对应定义，不硬绑一个calc_id或公司名字。
2. `valid-yoy-input-array-reordered`：正确growth(REV_2025,REV_2024)，只reverse inputs数组。所有具名symbol/值/期别/结果不变，当前误exit2 growth_wrong_comparison_year。按formula解析出的操作数角色绑定期间，不拿数组第0/1位置；预期0/0。用合法顺序两种正例和真实2023冒充2024反例守住两边。

保留原不可删served限制、倒序/错期间、同比错年/合法期初期末平均和零分子防线。method契约与版本/profile集中写清，旧材料仍走已关闭的限制只读，不eval、不造新评分器。不增加helper审批。

## R4：累计预算与声明闭合

单文件5MiB与超限锁hash路径已关，不重做。原卡累计读取预算仍未公布/实施：为实际读入的pack/账/锁/短结构冻结输入给合理**累计**预算，读前扣额（同文件重复读取的口径明确），同一公开validate/export路径共享。正常90题/20锁作为正例；用自有小文件与缩小测试预算或精确读观察模拟总额超限，证明未读超额数据，避免造百MB垃圾。不能假称已有16MiB协议；上限选择写明即可。

base→HEAD实际37路径、handoff29遗漏8：tools/gen_artifacts_remediation.py，以及新交接artifacts.json、handoff-commit.txt、5日志/manifest。按产品/交接/末次记录分段列实际变化与commit，自引用记录遵共同规则，原新文件确实跟踪；不改历史清单。最终schema/工件索引包括实际新增metadata，原33工件匹配成果保持。

## 集中收尾与交接

只做受影响unit/integration/公开CLI正反例；稳定候选一次完整兼容回归和包级独审，不逐helper反复全套。实际金融查证与软件绿分别记录，81P和47原对不能称金融准确率。Lab自有隔离根去keys/禁收费/只写owned；仍用原validate/export入口，不新写启动器/下载器。

交接仅Lab `docs/handoff/FIN-REF-01/remediation-04/`，完整base/product/交接/终态HEAD、dirty状态、版本/reader与具名method契约、90coverage/18深核、真实attempt/访问短摘要/事实反证、账、case-map/PWF/review、原RED/GREEN PID/起止/exit/日志SHA、闭合实际路径和工件清单/20输入核对。产品先正常commit再交接commit，无remote不造push。原wave2 catalog/inputs.lock/validation不改。

只清确认绝对范围/普通文件/单链接/ID/bytes/SHA的自有临时资源，保留小反例及失败日志；source/.venv/.codegraph/他人根不清。公共handoff exit0只验形状，不关闭研究/F05/G3/金融准确率/生产门。收到后总控同包一次集中接续，不自动向harness发消息或改Lab。
