# UI-COMPARE-28：正式结果多公司矩阵及日期/模型轴组件

唯一写根：`C:/Users/郑曾波/Projects/iqs-comparison-view-lab`；分支 `codex/ui-compare-28`。只在该新Lab完成组件；主UI/StockWiki/IQS/StockQA只读。先读同目录handoff-rules/manifest/inputs.lock中本ID条目。编卡时Lab不存在，开工重新确认唯一writer。

## 1. 真缺口、目标、停止边界

现 product_core.comparisonRows仅按qid并列left/right、固定comparable:false；现renderHistory只单公司左右两条观测，不是多公司生产矩阵。旧thin_compare历史草稿不可充正式数据。本包交付**可由总控直接嵌入原UI的原生ESM组件与公开client适配候选**，不是离线planner、另一个答案库或静态截图手册。

用户要从约2000家公司池选择几家公司，逐题看原分数/null、理由、信息日、模型、题义版本和主体范围。全部基础题含杜邦7/五力5，但组件须由实际bank/observations动态发现，**不得硬编码24/36/某行业题数**。增加新题/模块无需改组件。

不发模型/搜索、不复算营收/PE/分数/均值、不重新评分或排名、不把相同结构签成金融可比。保留原 `owner_comparable`；原false/未提供绝不可被结构检查改true。未知/NA/证据不足/null不变0。数据缺失照实显示，不补模型/日期/主体。

## 2. 必交付与 host 接入

- `src/compare_view.js` + `src/compare_client.js` +局部CSS，无框架/全局store绑定；`schemas/`接口schema；`demo/`合成可用界面；单元/集成/真实浏览器mock E2E。
- `integration/host-patch-proposal.md` 只基于锁内 constants/product 等实际可核实入口建议导航/挂载/清理。main/router未锁部分由总控后续定位，列为待接线缺口，不读取锁外源码、不虚构函数或声称已精确查过。不要改原仓。使用原public GET `results?query=&limit=&offset=`、`entity?id=`、`history?id=`、`coverage`；由宿主注入既有request，**不另写鉴权/fetch层**。

```javascript
export function createComparisonClient(request) // request=原async request(endpoint, options)
// 返回 searchCompanies({query,offset,limit}), readEntity(entityId), readHistory(entityId), readCoverage()
export function mountComparison(container, {client, bank, connectionIdentity, options})
// 返回 {dispose(), getSelection(), setSelection(selection), exportViewState()}
export function inspectAlignment(leftRecord, rightRecord, {mode, ownerPairVerdict = null})
// 只给结构差异解释，不给金融资格或数值分差
```

所有client调用只有原GET；无源host真实能力时返回明确 capability_unavailable，不虚构 `/compare` backend。自己的demo路由不是生产route。

`selection` JSON protocol=`iqs.ui_comparison_selection/1.0.0`，required闭字段：`protocol,mode,entity_ids,question_ids,module_ids,observation_choices,date_range,model_filters`。mode=company_grid|model_axis|date_axis；ID数组字符串唯一；空question_ids表示从当前bank/实际records发现全部，不能当0题；observation_choices是 `{entity_id,question_id,observation_ids:[...]}` 数组；date_range=`{from:date|null,to:date|null}`；model_filters字符串数组。显式观测ID选择，禁止在不同日期/模型/代际里偷偷拼latest。

记录投影的 required 闭字段：`record_ref,entity_id,analysis_subject_id,analysis_subject_revision,perimeter_sha256,scope,security_id,segment_id,question_id,question_semantic_sha256,question_version,rubric_version,score_direction,module_package_id,information_cutoff,information_as_of,observed_at,provider,model_resolved,model_revision,status,score,coverage,confidence,missing_fields,evidence_review_status,publication_status,owner_comparable,source_pointer`。未知元数据为null，数组缺失与[]区别保留；score为原1–10整数或null，status原值保留；不把旧compact未知状态改scored。source_pointer指原响应字段位置，真实正文只在宿主已有records内短暂显示，不另存库/日志。

`inspectAlignment` 输出 protocol=`iqs.ui_comparison_alignment/1.0.0`，required：`protocol,left_ref,right_ref,mode,structural_alignment,differences,gaps,owner_comparable,financial_qualification_granted`。structural_alignment=aligned|mismatch|unknown；differences数组 `{axis,left_value,right_value,reason_code}`，gaps字符串数组，owner_comparable为原boolean|null，financial_qualification_granted固定false。**pair owner_comparable不能由两个per-record flags作AND/OR，也不能由structural_alignment=aligned合成true**；两个原row flags在各自record保留。只有原owner精确绑定本 `left_ref/right_ref/mode` 的pair verdict可透传（ownerPairVerdict闭字段=`{left_ref,right_ref,mode,comparable,source_ref}`）；绑定不符拒绝透传。当前GET没有pair verdict能力，默认输出null，原明确的pair false可保留false；不能把UI自己生成的false或模型自报字段冒称owner判定。实际金融资格仍一律false。每个轴独立：同qid题义/rubric/方向冲突必须指出；不同公司ASJ ID本来不同，不能机械要求相同ID使全部跨公司对照失效；同公司ASJ/perimeter修订必须警示范围变化；entity与security、不同证券/股类不能混。跨模型模式就是看不同模型原值，不能因模型不同把页面全挡掉；缺模型仍unknown。日期轴允许有意看不同日期，标记信息日、取证上限、回答时间三个不同字段，不伪装同日。

## 3. 最小可用体验

1. 搜索原公司，显式多选、取消；保留唯一entity和挂牌提示，同名不合并。
2. 动态选择模块/qid；表格公司为列、qid为行（或可切轴），固定题目/公司表头、横向滚动、键盘可用。加载/空/失败/缺题分别展示。
3. 每cell看原score/status/三日期/模型及待审状态；展开原理由、来源、版本/主体。日期为空显示未提供，取证cutoff不覆盖answer as-of。可切单公司模型/日期轴并选明确observation_ids。
4. 结构差异逐轴列出，始终说明原记录并列不等于金融核验；未审核数据不涂成已核验白名单。
5. 当前连接/generation/请求serial边界：旧请求迟到、切公司或连接不能覆盖新选择；失败可保留旧显示但标stale、不得继承操作权限；dispose取消监听/本Lab轮询。只读无POST。

默认最多同时12家公司，可由宿主选项在1–50调整；这是视图资源边界，不限制池/题目总数。大题表分页或虚拟渲染，不能静默丢题。筛选/导出viewstate只保存引用与选择，不自动归档回答全文。

## 4. TDD与大节点验收矩阵

至少包含如下真实断言（不是每行另开审查门）：

- 3公司×基础36，137动态qid、未知新module、空bank/缺题；动态题增减不改代码、不补假题。
- 不同entity同显示名、同公司A/H证券、多类US股、entity/segment/security、ASJ修订；不按名称/ticker合并。
- 同qid不同semantic/rubric/version/方向；同语义旧新package可原样展示并报告差异，不假定package不同就完全不可看。
- model_axis不同provider/model可有效并列；缺revision/模型未知；date_axis显式不同as-of/cutoff/observed_at，空日期、过期标签，不用今天补齐。
- insufficient_evidence/NA/search_unavailable/null/零字段，不产生平均分、分差、排名或金融comparable=true。
- 两个原row flags都true但无pair verdict→pair owner_comparable仍null；结构aligned不能产生true；foreign left/right/mode verdict拒绝透传；原明确pair false保留；缺comparable/伪qualified flag不晋升，保留review_pending/unreviewed。
- 原public返回缺能力/错误、duplicate observation_id、多条同qid、部分加载失败、换连接旧请求迟到；原记录不突变。
- XSS `<script></script>`、恶意URL/长中文/前导零代码；键盘/焦点/表头可访问性；窄屏/宽屏各截图（仅合成）。
- ownclient mock调用逐项证明GET only；源码/真实库/网络均不触碰；mount/dispose连续20次无监听/定时器/进程残留。
- 合成2000家公司目录+选12家×137题：记录实际耗时/内存及渲染行数，分页无遗漏。不做N²全池比较或假称达到真实金融准确率。

unit：纯投影/轴解释/选择；integration：client注入+实际ESM DOM事件；E2E：本Lab合成服务/隔离浏览器真实搜索多选→矩阵→切模型/日期→错误重连→dispose。至少一个目标RED保留，再GREEN。浏览器不可用诚实partial，不能用静态截图替代交互。

## 5. 运行与交接

本Lab工具module=`iqs_compare_view_tools`：verify-inputs、demo（127.0.0.1:18771）、validate-delivery；遵守共同CLI退出码/新输出目录。生成demo数据全部合成，三家公司名称仅scenario label。公共ESM导出/DTO schema/host建议/测试/cleanup/真实不同agent最终passed全部齐备，方可按原handoff1.0交接到 `docs/handoff/UI-COMPARE-28/`。task_ids=[]、production_ready=false。独审要实际试用全部三轴与上述反例，发现问题作者全修，再冻结最终payload C和文件hash。总控后续才接原UI和验生产数据，不把本包mock成功称生产已接通。

