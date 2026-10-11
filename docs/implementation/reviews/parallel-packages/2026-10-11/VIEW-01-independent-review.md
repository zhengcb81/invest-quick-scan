# VIEW-01 独立审查归档

2026-10-11，一个用户已授权的独立review agent `/root/viewer_contract_review` 对实际HEAD dff41052的已知源码/schema/冻结契约/frontend/接口文档只读审查。未执行Lab代码、联网、读取凭据、写仓库或向外部harness发消息。以下五类静态结论与总控集中复现合并；不另外增加五个审查门。

1. **P1 展示可信等级**：bundle.py:212–227允许banner.none/空及未知重标签；adapter.py:64–79忽略status，unknown5有效；adapter.py:160–166保留恢复加分声明。总控CLI/DOM确认，恢复项仅确认字段矛盾，没有断言UI实际做了加法。
2. **P1 原wire支持**：adapter.py:334–342只看外壳；:513–514在unsupported分支前解读watermark可崩；原request/response实际版本/operation未闭合；schema:118/146重复additionalProperties。总控确认两类未来raw仍supported、两类未来容器exit1、严格schema重复键拒绝。data_kind=[]另复现exit1。
3. **P1 owner比较/事实引用**：adapter.py:168及378–385采任意portable自述，同题lastwins；冻结ObservationProjection无此字段。facts只信bundle.capabilities；没有独立owner具名消费。第一条self控制被同题后条覆盖，未作成功复现；改两条self控制后浏览器确认owner可比误标。
4. **P1 快照范围/分页**：adapter.py:567/:711–712全局sid最后覆盖；app.js:370不带snapshot；:679–706以已加载rows为total且忽略cursor；全bundle时间排列误推跨query/store旧水位。总控确认旧列表→新详情、partial控制150→100/cursor丢失；跨query水位尚是静态风险，R1要求明确范围测试，不称已真实owner复现。
5. **P2 详情/交互**：正式profile详情:430–443无listings/scope_as_of，只有stub有；app.js:396静默空挂牌。页面依赖page.page_size_limit.max_page_size但文档未列，缺选择比较pair；焦点与无参数返回未恢复。总控原fixture挂牌/DOM/独立浏览器确认；实际截图显示窄屏无全页溢出但六列密集逐字换行。

有效组件、原71P/1skip、输入/工件匹配、无remote/正常branch及owner_integration=not_run均保留。总控处理为[同包唯一R1](VIEW-01-R1.md)，不代改产品、不关闭金融/UI生产门。详见[验收](VIEW-01-acceptance.md)；受控案例、原始stdout/stderr、PID/请求/截图与清理证明仅在本机私有runs留档。
