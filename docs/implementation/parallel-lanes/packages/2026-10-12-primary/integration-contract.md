# 共同数据接口、合并与验收

## 主产物

1. `content/reference-pack.json`：冻结FIN `iqs.financial_reference_pack/1.2.0`完整90行，保留companies/inputs/protocol/原顺序和全部题义绑定。只能更新自身30行；外60 canonical hash等于targets。所有分数/区间null、独审needs_revision/全局资格未授。不能把三份90相加为270题。
2. `content/calculation-ledger.json`：原 `iqs.calculation_ledger/1.0.0`。不相干公司的原账项逐hash不改。本公司需改旧Entry时有expected_old_sha256+理由；新CALC用专属前缀。数值计算只用原注册方法/roles/期间/币种/单位/主体口径，未注册财务方法写独立calc-notes而不是新引擎或computed。group和parent混算拒，parent entity_name对应上市主体而非控股母公司。不能从PE/股价反推EPS/外汇，也不能以年末余额作全年平均资本。
3. `content/qualification-index.json`：私有候选protocol `iqs.primary_source_qualification_candidate/1.0.0`，结构见下方；不是生产接口或金融签收回执。逐公司30题原分母，不能省缺答。
4. `content/changes.json`：protocol `iqs.primary_reference_changes/1.0.0`，package_id/company_key/baseline_pack_id、rows列表{reference_id,expected_old_sha256,new_sha256,reason,new_fact_ids,new_source_ids}及ledger_changes列表{calc_id,expected_old_sha256|null,new_sha256,reason}。新record用自己的RPA/RPC/RPS命名空间，不能引用另一包新ID。

## Qualification index字段

根字段严格为protocol/package_id/company_key/information_cutoff/baseline_pack_id/reference_pack_sha256/calculation_ledger_sha256/rows/source_proofs/limitations/qualification_granted。qualification_granted必须false；hash为所交原文件raw SHA256。rows恰好30，按targets顺序，每项为reference_id/question_id/baseline_row_sha256/current_row_sha256/status/proof_ids/residual_gaps。residual_gaps为对象数组，逐项严格{fact_id:null|本row事实ID,reason:非空字符串,needed_evidence:非空字符串}；null只表示整题其它缺口，不能代替对每个现有fact的处置。

status只能confirmed_primary、contradicted_by_primary、limited_primary、unconfirmed、cutoff_unresolved、not_applicable；缺真实正文/范围/日期不能confirmed_primary。每个现有非contradicted事实必须在对应residual_gaps或proof的fact_ids内有明确处置，不能因同题有一条官方新闻就掩盖其它数字未确认。

source_proofs每项严格为proof_id/source_id/company_key/source_url/source_owner_type/original_read_status/disclosure_public_at/retrieved_at/locator/fact_ids/reference_ids/claim_scope/entity_name/currency/unit/period_start/period_end/evidence_note/contradictions/excerpt_sha256。proof_id前缀PROOF-<本包namespace>-，无重复；source_owner_type枚举official_issuer/official_regulator/official_exchange/licensed_republication/third_party/unknown；original_read_status枚举readable_read/original_pdf_link_only/navigation_only/body_unavailable/not_attempted。claim_scope沿事实group/parent_company/segment/security/unknown，entity_name是来源声明的主体，不是新身份ID。日期合法ISO并区分披露/期间/访问；未知允许null，confirmed_primary所需披露日不能null或晚于cutoff。excerpt_sha256是实际短evidence_note UTF-8摘要或null，不得冒充网页/原文件全文hash。至少有一个fact_id和reference_id，引用闭合且属于本公司，URL与包中Source相同；只证明本次定位/引用映射，不靠自报hash证明原件真伪。

每条proof只有一种scope/币种/单位/期间。一个来源含多范围/多表可拆多个proof共用source_id；单位不明→unknown，母公司/集团必须分别定位。proof.fact_ids只引用本pack对应合法facts。owner/name表述与上市主体不一致的内容进入contradictions，不能用公司近似名称修补。外公司/未知来源/搜索摘要/PDF入口不允许确认。

## 允许与禁止的变化

原Source记录对象和ID内容全部不变；追加独占SRC/FACT/CALC命名空间。旧错误fact保持原claim/value且标contradicted并记录前序hash，新事实用新ID；原正确转载fact保留，为新增原件佐证生成新的fact/proof和changes，不能悄悄把旧Source改成官网。copy已存在parent62新ID和map时保持原义，不再从旧quarantine重复导入。新增更精确主体口径须原schema能表达，不能把unknown或母公司填group绕校验。

pack_id用原content_hash.compute_pack_id，research_summary用原research_summary.compute_research_summary；不能重新定义canonical content算法。行/Source/Entry冲突比较用UTF-8 JSON ensure_ascii=False/sort_keys=True/separators=(',',':')/allow_nan=False SHA256。只有created_at/pack_id/research_summary和清楚声明的limitations可更新，其他top-level/题义/公司绑定冻结。targets给的是共同1.2基线，不拿旧1.1增量覆盖新集成。

## 本包CLI目标

本地`python -B -X utf8 -m primary_reference_lab validate --candidate content/reference-pack.json --ledger content/calculation-ledger.json --qualification content/qualification-index.json --targets fixtures/targets.json --inputs-lock fixtures/dependency-lock.json`。该名字是本包薄封装的目标，各新Lab可同名但不能写共享安装目录。它核允许变化/qualification引用/预算范围，然后调用冻结FIN现有validate入口，不复制财务验证器。exit0只候选结构+范围可合并；exit2为坏输入、exit3为export拒覆盖。`export --output <new-dir>`同参数，只在全验证成功后原子发布，无错误时半正式输出。原FIN的validate/export先真实调用并记录0/2/3，不把本包wrapper成功当跨仓生产E2E。

另公开IQS交接shape命令（无需修改IQS）：

```powershell
python -B -X utf8 C:/Users/郑曾波/Projects/invest-quick-scan/scripts/parallel_handoff_cli.py --catalog C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-12-primary/manifest.json --package-id PRIMARY-ALPHABET-03 --input C:/Users/郑曾波/Projects/iqs-primary-alphabet-lab/docs/handoff/PRIMARY-ALPHABET-03/handoff.json
```

替换自己package-id/根。它仅handoff形状与声明范围，不验证金融/网页/owner，不授写入权限。

## 一个集中测试包

| 层 | 业务输入 | 预期 |
| --- | --- | --- |
| Unit | 合法自身30原件佐证；外公司row/source/entry变动、新ID撞另一namespace、删原题 | 合法追加可过，其余2；无正式输出 |
| Unit | 官网页导航/PDF入口/转载改official、未知公开日、截止后事实 | 不能confirmed_primary；实际unknown/gap保留，非官网URL不能自签primary |
| Unit | 集团/母公司混、ordinary/perpetual资本混、CNY/HKD1:1、期末当均值 | original FIN可表达的非法账2；语义确认撤回或具名gap，不能造数 |
| Unit | proof.fact_ids不属于所列row，claim_scope/期间/单位不匹配，近名不同发行人，引用dangling | 2；不写正式内容；正确同源多proof可过 |
| Integration | 正确完整90/自己30/外60/43锁/所有旧Source；fixed merge时点下独占模拟另一公司增量 | hash和分母一致；两顺序同；同一基线ID不同内容明确冲突拒last-write-wins |
| CLI E2E | 剥key/网络拒绝；随机cwd/中文空格路径，合法validate/export、坏JSON/重复key/NaN/1e400、已有输出 | 原与本包入口0/2/3，拒绝前不能产生正式目录；清理恢复前环境 |
| 来源审查 | 三主题以上官方定位＋自己的全部30处置；新闻只支持其明确事实，数字/币种/期间/范围及反证 | 访问/未读/缺口分别留档，confirmed_primary不能仅有搜索摘要；不能把软件通过率当金融准确率 |

无需每题新审查。一个稳定包做一次集中来源审查/软件回归；无法独立agent复核就标self_review/not_independently_reviewed，不声称独审。产品验收是机械接口及真实研究记录可复核；事实评分/官方资格和G3/F05由总控原节点决定。

## 交回的固定目录

`docs/handoff/<package-id>/handoff.json`、README.md、interfaces.md、coverage.md（30题逐一 baseline/current/proofs/gaps）、sources.md、changes.md、calc-notes.md、review.md、case-map.md、isolation.md、artifacts.json、logs/和planning/三PWF。content中的四JSON及本包CLI/tests/锁都纳入artifacts。所有文件按实际path/bytes/raw SHA，不遗漏planning/metadata，不把自己manifest列自身hash。README列branch/product commit/最终HEAD、精确复现命令、实际通过/失败/skip、剩余缺口；不中途把缺口或未开始改成“完成”。

总控只取本公司30行+独占增量，按targets的expected base hashes与此后实际FIN当前记录三方比较。总控活动源前进时冲突只做审查与显式合并，不自动覆盖/回滚；原source/ledger shared ID不同内容先拒绝。统一merge时间/原hash算法，完整90上一次集中验收；资料候选不写生产库或新名单，也不关闭模型准确性、真实owner或UI门。
