# VIEW-01：可交付的企业快扫只读界面

## 工作范围与上下文

唯一写根 `C:/Users/郑曾波/Projects/iqs-viewer-lab`，只认一个 writer。关联原 U01/U02/U03/U04/O05/X09，但本包只交前端组件和薄输入适配，不能签收原生产 UI 门。先读 [共同规则](handoff-rules.md)、[manifest](manifest.json)、[输入锁](inputs.lock.json)。本包不依赖 FIN/OPS 或活动 MATRIX Lab。

主线已有题库、身份、查询和执行实现，第一次真实 Alphabet 30题扫描可用评分为0，正修复接续。用户要简洁实用 UI，不要装饰图表。StockWiki 是唯一公司库/query owner；UI 不直接打开 SQLite、不运行模型或付费搜索、不计算新的总分/比较/新鲜度。

冻结当前公开 schema 2.0 get_profiles、pool 2.1/2.2/2.3、research 2.4、review-lead 2.5、capabilities 1.1 的消费边界。不要声称每个 wire 都支持所有 operation；按各独立 schema。主线私有 vendor identity/query 2.6 等不是本包硬依赖，未支持版本明确显示 unsupported，不静默降级或改原观察。

## 交付的可用产品

1. 股票池列表：名称/代码/市场/业务分类文字搜索，owner 提供的筛选命中/未知/失败结果，分页、水位、覆盖与缺口；同公司多挂牌不重复公司数，同主体不同 scope 不合并观察。
2. 企业详情：身份/全部挂牌、信息截止日、每题分数或状态、短依据/安全来源链接、实际 provider/model、metric/rubric/module 版本、原观察 hash、信息时间/采集时间/入库时间。
3. 历史与模型并排：消费 owner 的可比性结论和原因；不可比也能并排阅读，不能自行算差值、汇率换算、万能均分或用颜色认定改善。
4. 风险/恢复观察/数据缺口分别显示。临时低谷低分保留，恢复标记不加分；unknown、N/A、insufficient_evidence、expired、service_unavailable、coverage_gap 不互相混用。
5. 事实关系页按 capabilities 显示可用/尚未采集/不支持。只呈现 owner 已有关系，不能用公司名关键词编供应商或客户。更新/确认/添加公司/模型设置仅 disabled 入口说明，禁止模拟成功或付费请求。

## 明确输入、组件和输出接口

交 `web/` 可移植静态组件与 `src/iqs_viewer_lab/` 薄演示服务。优先原生 HTML/CSS/JS + Python 标准库演示 server；若选框架需解释维护收益且依赖锁定。必须可离线运行，不依赖 CDN、远程字体或 telemetry。

自有演示输入协议 `iqs.viewer_demo_bundle/1.0.0`，closed schema：`protocol`、`data_kind`（synthetic 或 owner_export_unqualified）、`capabilities`、`exchanges`（每项 operation、原 request、原 response、显式 expected_owner、validation_evidence 引用）、`display_annotations`（只允许显示文案/原状态引用，不允许评分资格）、`artifacts`（相对文件/raw SHA）。不得把报文内部 owner 当独立信任来源。合成 bundle 永远带醒目“演示数据”标识；没有实际 owner 校验证据的真实导出永远“未核实导出”，不能白名单。

输入适配要保留原 request/response/Observation bytes/hash，不重封 owner 包；shape 验证不是金融验证。只做展示字段提取，未识别字段/版本保留原数据并显式不支持。比较/筛选资格不由 annotations 自签；缺 owner 比较数据就显示“未提供”，不造本包 ranking。

```powershell
python -B -X utf8 -m iqs_viewer_lab validate --bundle fixtures/demo/bundle.json
python -B -X utf8 -m iqs_viewer_lab serve --bundle fixtures/demo/bundle.json --host 127.0.0.1 --port 0
```

以上是本包必须实现的 CLI，不是 StockWiki 已有命令。validate exit0合法、exit2拒绝；serve 输出实际 loopback URL、PID、bundle hash，拒非 loopback bind/任意目录暴露/越界引用。固定 GET 静态资源和已加载 bundle，仅允许 HEAD/GET；POST/PUT/DELETE 不可用，不内建通用 proxy/subprocess。浏览器只从 loopback 取界面资源，来源点击可交给用户打开安全 HTTPS；自动测试不访问来源。

server 是开发演示适配，不是第二生产服务。总控后续把 `web` 组件接到 StockWiki 既有服务，替换只读供数接口；交 `integration-map.md` 精确列组件 API、输入类型和 root 需接的 owner 入口，不修改 StockWiki。

## 施工顺序与集中测试

1. sole-writer/Git/PWF/输入冻结；画页面草图与输入流，不重复需求调研。
2. 先写坏版本、unknown填5、跨scope混行、错误水位、注入内容等 RED；做薄适配和展示。
3. 交桌面1366×768/窄屏390×844、键盘操作/返回保留筛选、空态/错误态；不添加复杂图表。
4. 同一候选集中 unit（字段保真/拒非法数据）、integration（有界加载/服务只读）、真实浏览器 E2E（Playwright 等，DOM 值/操作/网络断言）与一次 review。

| case family | 必须具体证明 |
| --- | --- |
| V01保真 | null不变0/5；score1/10保留；score11/bool不渲染为有效分；实际模型不被默认模型覆盖 |
| V02身份 | A/H挂牌同公司检索、同issuer不同subject/scope保留；重名不同entity不合并 |
| V03时点 | 三种时间分别显示；过期8分仍可读但不假称当前有效；旧水位分页不混live |
| V04比较 | 不同币种/期间/rubric显示 owner 不可比原因；无比较资格不生成分差/排名 |
| V05安全 | 中文长文本、`<script>`、javascript/data URL、路径穿越、重复JSON键、坏raw hash、未来wire明确拒绝或安全降级 |
| V06交互 | 真实打开列表→筛选→分页→详情→历史→返回；键盘焦点、移动布局、准确空态 |
| V07隔离 | loopback端口随机、无外网请求、无模型/搜索、退出进程/端口清理；来源正文不下载 |

2000行只作明确 synthetic UI 性能 fixture，服务端分页有界（默认50、最多100）；只测页面开销，不自称真实全池扫描容量。失败筛选/不支持能力与零命中不同。浏览器用独占 profile，截图/trace 保留，缓存下载清理。

## 完成交接

交 web/src、closed bundle schema、synthetic fixtures、可复跑测试、桌面/窄屏截图、真实浏览器流程日志、README、integration-map 与 `docs/handoff/VIEW-01/` 全套。沿用 [模板](VIEW-01.handoff.template.json)。未接真实 StockWiki/实际结果时填 `owner_integration=not_run`，不伪造正例，不把 HTTP200/静态截图称完整验收。
