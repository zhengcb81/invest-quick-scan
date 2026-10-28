# UI-UNIVERSE-28：用户股票池 TXT/CSV 批量上传与逐行确认组件

唯一写根：`C:/Users/郑曾波/Projects/iqs-universe-import-ui-lab`；分支 `codex/ui-universe-28`。先读共同规则/manifest/本ID输入锁。编卡时Lab不存在；开工核无人写入。其他Lab、原UI/IQS/StockWiki/StockQA只读。

## 1. 真缺口与唯一owner

现生产UI只有单家公司选择→原universe/preview→apply，没有TXT/CSV上传和逐行人工消歧。用户会提供几百家股票池；**只接受用户显式选择文件，不扫描Projects、不挑2000、不搜索/扩充名单**。

StockWiki已有原identity-preview（JSON候选、要求ticker/market和明确as-of）、候选staging和单entity幂等add。candidate-import只是暂存，不创建entity/member；entity-import需要另外正式owner证据，本组件绝不调用。不能新造identity/证券/挂牌或第二名单库。

交付**可嵌入原UI的ESM文件上传/列映射/候选人工选择/原单entity preview-confirm-apply组件及host适配候选**。只写本Lab，最终root唯一合入原UI/gateway。当前没有批量HTTP/全批atomic receipt/通用operation-id查询；不得在mock里发明这些端点并宣布生产接通。

## 2. 公共组件与依赖注入

```javascript
export function parseUniverseFile(bytes, {format, encoding, columnMapping})
export function mountUniverseImport(container, {adapter, connectionIdentity, options})
// 返回 {dispose(), getDraft(), loadDraft(draft), exportProposal()}
export function createUniverseImportAdapter(request, {capabilities})
// request=宿主原public client，复用原csrf/error/timeout；无另一鉴权/fetch层
```

adapter窄接口（只调用宿主注入函数）：

- `listUniverse({universe_id})`：原GET universe列表，返回原universe/version/members；
- `resolveCandidates({universe_id,row,as_of})`：已有原检索/readonly preview。当前UI通过原universe/preview的query路径展示候选，返回resolved/ambiguous/unresolved/choose_entity与原候选。名字不能自动resolve，即使只有一项也必须选；ticker/market合格才能在后续gateway接原identity-preview。缺能力明确unavailable，不发明 `/bulk-resolve`。
- `previewMember({action:'add',universe_id,entity_id,reason,priority,pin})`：原单entity preview，保留can_apply/blocked_reasons/preview_token；
- `applyMember({...原preview参数,preview_token})`：**只在用户明确确认该行/该批已选行动后**调用原单entity apply，保留原返回结果；
- `inspectMember({universe_id,entity_id})`：通过原名单读取确认当前member/history可用性；无精确operation receipt能力则报告缺口，不把当前active归因“就是本次POST成功”。

`integration/host-patch-proposal.md` 精确列原product.js挂载/文件input和gateway缺项，仅建议不写原仓。原owner `add_member` 要已存在universe/entity、reason非空、priority严格int（bool拒）；已active重复add返回原member不改version/reason；logically_removed需独立restore，**不能静默恢复**。原身份候选/成员结果必须沿用，不自签verified。

## 3. 闭式 DTO 与状态机（不是新工作账本）

所有自身DTO均 `1.0.0`，required字段不省、additionalProperties=false；不保存正式身份或owner正例。

parse输出 protocol=`iqs.ui_universe_upload/1.0.0`，required：`protocol,source_file,format,encoding,column_mapping,rows,warnings`。source_file闭字段 `{display_name,raw_sha256,bytes}`；rows每项 `{row_id,line_number,raw_fields,name_claim,ticker_claim,market_claim,security_type_claim,parse_status,issues,duplicate_group}`。所有claim为string|null，代码保留字符串和前导零；parse_status=parsed|invalid|empty；原行号稳定、重复仍保留出处，不能删行伪称全入选。TXT支持显式单列name或ticker以及tab分列；CSV支持带引号/换行/BOM并允许用户明确列映射；encoding只显式utf-8/utf-8-sig/gb18030，不猜错编码。原文件只读；单文件上限8MiB/10000行，超限明确错误。

draft protocol=`iqs.ui_universe_import_draft/1.0.0`，required：`protocol,source_ref,universe_id,as_of,connection_ref,rows,operator_reason,limitations`。rows required：`row_id,input_ref,state,candidates,selected_entity_id,selected_security_id,selection_reason,owner_preview,owner_result,reconciliation`。候选 required `{entity_id,display_name,identity_state,securities,source_ref,issues}`，证券每项保留 `{security_id,listing_id,market,ticker,valid_from,valid_to}`（未知null）；不创造缺失ID/日期。owner_preview/result为原client返回值，作为只读opaque payload与raw canonical hash绑定，不把其中模型字段升格authority；自己的wrapper required `{payload,payload_sha256,observed_at}`。

state枚举：parsed、invalid、unresolved、ambiguous、candidate_selected、needs_preview、preview_ready、confirmed、applying、applied、already_active、rejected、unknown、observed_active_needs_reconciliation。用户未明确选择/确认时不得写。纯名字、过期挂牌、跨市场同ticker、候选截断或缺身份来源均不能自动activate。

proposal protocol=`iqs.ui_universe_import_proposal/1.0.0`，required：`protocol,input_sha256,universe_id,as_of,rows,counts,production_applied,limitations`；rows包含 `row_id,selected_entity_id,selected_security_id,reason,state,original_preview_ref,original_result_ref,needs_reconciliation`；production_applied在Lab固定false。这是前端恢复/审阅草稿，不是原owner凭证或新receipt系统。总计分别列原行数/唯一已选entity数/重复行/未解决/实际ACK成功/unknown，不用“已解析”冒“已入库”。

## 4. 最小可用流程和失败边界

1. 上传用户文件→预览前10行/编码/列映射→逐行解析；名字原值保留。未选文件不读本机路径。文件名/备注不进入网络日志。
2. 明确选择要查询的行并请求原候选；展示名称+entity+每个market/ticker/shareclass/有效期。相似名字只提示，不合并；同entity多挂牌可在最终成员动作去重，但逐行来源仍在。
3. 操作员明确选**原候选**entity/证券并填写理由；禁止自动选第一项。未知/缺原候选的行留待处理，不创建公司。
4. 逐行原preview展示原token/blocked原因；行可单确认，批量确认须列出具体entity/行动/理由/待排除行，让用户审后才发送。默认串行（不扩并发）；本批前一次成功改变原名单version时，下一行须重读/重预览，原语义或状态变化要重新确认，不能继续旧token。
5. 双击只发一次；POST超时/连接切换/未知结果即unknown，停止后续写，**不自动重试**。先原inspect/list/history核；active但缺本次精确ACK标observed_active_needs_reconciliation，不能谎称本次成功。原API若不足，导出只读resumeproposal并标root需gateway，不自行补owner能力。明确rejected不同于unknown；不能借原add幂等盲重发。
6. 取消/离页不回滚真实owner已确认行为，不假造全批事务；草稿导入恢复必须校验输入hash/当前连接/universe/as-of，并重新读取原状态，不恢复旧操作许可。禁止localStorage自动存真实名单/后台上传；演示只本Lab合成数据。

## 5. 必须验收的TDD矩阵

- 空文件/单行/千行/BOM/GB18030/CSV引号及嵌套换行/错列/异常编码/超限/文件名XSS；字符串前导零不丢。
- **中微公司688012 vs 中微半导体688380**（两独立合成entity）；中英文别名冲突不能名称合并。
- CATL A/H同entity、两个security/listing；US多类shareclass不得合并security；相同ticker不同market；ticker被复用及 `[valid_from,valid_to)` 边界；日期未知显式未核实。
- 原候选0/1/多项/分页截断/缺ID；1项仍人工选；纯名字无ticker时不伪造identity-preview输入。
- 相同行重复、不同来源同entity、同ticker不同股类；保留每个源行和已选member动作去重依据，不擅删公司。
- unresolved/ambiguous不preview写；原can_apply=false/blocked/逻辑删除不得apply或隐式restore；reason空/priority bool等拒。
- 原已active幂等返回显示原version/reason，不声称新入库；批中名单版本改变使后token失效、明确重新预览/确认。
- 双击、在途禁编辑、POST前已被拒、POST后超时可能提交、成功ACK丢失、当前member由别的writer变更、连接切换迟到返回、dispose；未知全部先核原状态，自动POST数保持0。
- reload加载resumeproposal后不自动继续写；只有原明确ACK才能算applied；缺inspect能力提供gateway缺口，不造原receipt。
- fake adapter调用次序和精确参数真实记录；真实DB/API/key/model调用0，locale/XSS/可访问性；1000行分页与键盘，行总数不丢。

unit：原字节解析/映射/状态与proposal；integration：实际ESM DOM事件+注入mock adapter/拒绝与未知；E2E：本Lab mock服务和隔离浏览器完整upload→多歧义人工选→逐行preview→具体确认→成功/超时→核状态→导出恢复草稿。mock是合成契约测试，必须标fixture_only，不能叫StockWiki owner正例。至少一产品RED再GREEN；最终集中真实不同agent审查全部流程/测试/隔离，发现问题全部修好才交。

## 6. 运行和交付

工具module=`iqs_universe_import_ui_tools`，verify-inputs、demo（127.0.0.1:18772）、validate-delivery，遵守共同CLI/清理。产物src组件/局部CSS、schemas、fixtures、demo、tests、integration建议和 `docs/handoff/UI-UNIVERSE-28/`。默认lab demo没有任何生产client；不可通过命令行传原workspace/DB/API URL。原handoff1.0 task_ids=[]，production_ready=false，独立review final绑定最终payload C/输入锁/所有文件pins，缺证据必须partial。总控之后才接原UI/唯一owner、做真实用户文件/原幂等验证，Lab不得宣布生产导入已完成。

