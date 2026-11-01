# 时间解释与结果可信信息：原工作台接线

本功能扩展原 `scripts/open_dashboard.py` / `iqs-question-bank-ui-lab`，不建立第二个服务、库、缓存队列或LLM调用器。本机原配置仍是 `config/dashboard.local.json`，地址 `http://127.0.0.1:8766/`。正常浏览、展开原记录和解释日期均不调用模型。

## 使用

进入“公司研究 → 生产结果”，选一家已有记录的公司。展开某题的“完整理由、来源与记录”，即可看到“结果可信信息”和时点说明。“查看原记录（只读）”在同卡片展开原JSON，不发起写入或跳到别的公司。历史与事实页也保留原记录；没有父级ACK、金融核查或研究状态时明确显示未提供。

归属异常的行不计入当前公司记录；父级身份冲突时也不展示其C06、质量汇总为当前公司结论。原值留在隔离诊断中。未知分数、版本、模型修订和日期不补造；不把分数平均后当作公司质量。界面中的原状态 `missing_date` 可能是缺少信息日期或有效期，特别是原字段时效策略尚未接入时；不能据此把已存资料日期抹掉。

## 版本与兼容

| 接口 | 版本/行为 |
|---|---|
| 原 `GET /api/product/entity?id=...` | 原DTO及草稿附加字段不变 |
| 新 `GET /api/product/entity-view?id=...` | `iqs.company_research_view/1.0.0`，`entity`内保留原DTO，另带`temporal_shadow` |
| 时点侧附 | `iqs.temporal_shadow/1.0.0`，固定`read_only_shadow`、`reuse_authorized=false`、`production_reuse_applied=false` |
| 原日期解释 | `iqs.temporal_clock_explanation/1.0.0`，统一`context_assessed=false`，不另作当前路由/缓存许可判定 |
| RESULT组件 | 原`iqs.result_trust_view/1.0.0`；只读、无网络、无时钟推断或评分 |

客户端仅在旧服务明确返回`method_or_route_not_allowed`时回退到原entity接口。超时、身份错误、错误wrapper协议不会触发静默重读/降级。旧消费者无需接受新字段；原refresh plan/request/policy严格schema、`refresh_id`、TTL、调度/预算权限均未修改。

## 数据与时钟边界

原owner worker通过现有公开观察读取方法取得不可变原payload。先绑定父实体、观察ID、题目/字段、scope/证券/分部、SHA、观测时点和截止日，再匹配固定题义definition及release。TIME目录包含222评分题与61事实题的候选分类；当前仅对已固定release的222题有definition绑定，事实题或新旧题义不匹配时保守未绑定，不能借相同question_id套用。目录不作为当前路由证明。

当前适配器统一调用TIME纯时钟函数，解释执行时点、行情、财务期间、来源发布时间和事件失效；保留未来信息、截止日期及未知/撤回来源约束。不再构造captured-context复用决策或要求verification_clock，不因缺少独立核查凭证制造刷新提示。原身份版本或模型派发信息缺失仍可解释已有日期；原观察完整性和公司/题义归属检查保持。旧核查元数据留在原DTO只读兼容，不从模型自称`verified_at`补造核查。

原native“新鲜缓存”规则继续由原预检决定。侧附中的24小时候选钟只是实验解释，不是当前owner政策的重新计算。当前路由与主体兼容性由原owner判定，不能由本视图认证。2026-11-01进一步精简：取消另建独立核查凭证签发/续期系统的计划；已有核查元数据仍可只读显示，但缺失不阻塞扫描、入库、浏览或原缓存复用。后续时效改进直接使用真实事件、字段日期和原成功搜索时间，不用查看/导入时间续期，也不把机器检查标为金融核实。

## 依赖固定与升级

精确来源、固定Git C、原始SHA、目标SHA和变换见[time-result-source-pins.json](time-result-source-pins.json)。只携带TIME纯函数与候选目录，不导入Lab的`vendor_upstream`、CLI或`sys.path`注入。旧规则数学由当前部署的原StockWiki提供，标签明确非原冻结副本或活跃政策许可。RESULT的唯一文字补丁将`missing_date`说明扩为日期或有效期，不改原状态、规则、来源或分数。

新增模块/升级题义须显式升级pins和题义绑定，再跑关联组与原生只读/浏览器验收；未知版本继续可读但不猜政策。不要求每个小改动重复小时级上游全套。

## 本轮验收状态

2026-10-31原8766已使用原配置启动；腾讯、微软、宁德时代真实GET对比，新旧DTO除生成时间一致，292个原工作区文件hash不变。三者分别展示38/37/38条观察、各36个题目；额外条目是原历史变体，不称新增完成槽。112条可绑定观察已走原TIME钟解释，一条旧release观察保持未绑定；这些旧观察没有原身份修订，全部兼容性保持未知。没有重跑108题、修改资料日/TTL或调用付费API。

关联后端74项通过；随后事件约束补充及最终受影响32项复验通过，重叠项不加总。原UI关联53项通过，最终受影响3项（含Node宿主断言）复验通过。真实CUA三市场面板/原记录回调均通过，最终不同agent已签实际IQS/UI C与Git清单，见[完整报告](reviews/TIME-RESULT-WIRING-2026-10-31/report.md)。审计覆盖完成、ACK、UI接线和金融准确性四者分别记录；新鲜缓存真实正例及金融准入未由本功能关闭。
