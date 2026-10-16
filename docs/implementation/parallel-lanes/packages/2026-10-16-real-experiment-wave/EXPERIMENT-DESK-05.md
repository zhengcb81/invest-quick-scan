# EXPERIMENT-DESK-05：只读离线实验矩阵与时轴

唯一可写根 `C:/Users/郑曾波/Projects/iqs-experiment-desk-lab`，编卡时不存在，开工复核不得覆盖writer。把本卡、integration-contract.md、interface-spec.md、handoff.template.json、总控发布inputs.lock.json与本包完整输入子集一起交harness即可独立施工。不等CATL/CSC包、不等主线T2、不使用未来结果。IQS/所有旧Lab/PWF只读。

交 Python 包 `iqs_experiment_desk` 1.0.0，薄只读文件loader+确定性派生view+本地静态交互UI。它消费已签收judge/cache/claim/evidence载体，保留来源与未知，帮助人查错，不计算新金融判定或跑模型。不得重建六工具业务规则、SDK、缓存计费器、盲评系统、生产查看器或正式owner写入路径。

## 固定输入与数据流

- `trial-t0/`：已冻结T0六会话的result/events、questions/evidence-board/metrics/answer-schema/routing/measurements；不是当前运行目录。
- `trial-t1/`：冻结T1三场启动会话result/events、原六planned-sessions、context-ref、subject-provenance、measurement。保留原登记72槽；adapter只有36输入槽，15合法答案、57登记缺失。未启动场次显示not_started，不能消失。T0有4/72合法答案、68缺失。
- `quality-reviews/`：两轮独立匿名人工审查，仅供已完成判定状态/局限展示。不带private解盲map；不能凭匿名条目顺序/模型猜测关联。没有显式合格join时只能phase aggregate，行级 quality=unreviewed/diagnostic，不能虚构判定匹配。旧measurements pending保留原值，在UI列snapshot_status与later_review_status，不能倒写旧测量。
- `tool-products/{cross-T0.json,cross-T1.json,evidence-cross-output.json}`：实际跨包离线产物，明确工具比较没有导入新判定时accuracy/winner=null；不能以旧金融审查存在而把该comparison的null补数。
- `tools/{codec,judge,cache,session,claim,evidence}/`：已签收package1.0.1的明确schema/示例/必要纯代码或数据，只读固定输入。CACHE schema是Python source定义，不能当JSON文件硬解析或伪造schema；可用其冻结纯模块导出或在本包明确写只读schema-adapter，并标adapter版本/源hash。CLAIM真实example为载体样例，不能冒充真实T0判定；需要时调用冻结纯函数离线派生并标derived、输入hash和source版本。无来源的字段显示unknown。六工具其余schema用于兼容和诊断，不强迫每个产物都有对应真实实验正例。
- `rules/`：固定T0/T1/六工具报告，解释范围与不可关闭门；缺文件/改hash必须拒绝。输入全部由总控source-requests逐项冻结，不追活动Lab。

上游protocol/schema先验锁后验证，纯adapter把固定载体读为新view；旧载体不改。新manifest由调用者显式提供，公司/phase/strategy/repeat/model/endpoint/cohort/evidence版本完整绑定，缺值=null+missing_fields。不从目录名推company、不拿模型display name代ID、不把相同ticker的不同证券混并。真实样本只有Alphabet，CATL/CSC可用明确synthetic=true的多公司fixture验证筛选，不能伪装真实公司实验已跑。

## 必须交的 API、schema、CLI

```python
def validate_manifest(manifest: dict, *, inputs_root: str, lock_path: str) -> dict: ...
def build_view(manifest: dict, *, inputs_root: str, lock_path: str) -> dict: ...
def build_bundle(manifest: dict, *, inputs_root: str, lock_path: str,
                 output_root: str) -> dict: ...
def serve_bundle(bundle_root: str, *, host: str = '127.0.0.1', port: int = 0): ...
```

落地闭合schemas `iqs.experiment-desk-manifest/1.0.0` 与 `iqs.experiment-desk-view/1.0.0`，完整字段与join/unknown语义见interface-spec。提供锁内真实样本manifest与合成多模型/多phase/多证据版/缺槽/乱序回执/恶意文本 fixtures。真实manifest构造不改输入，以explicit registration为准，不能猜不存在的字段。

```powershell
python -B -X utf8 -m iqs_experiment_desk --version
python -B -X utf8 -m iqs_experiment_desk validate --inputs $snapshot --lock $lock --manifest fixtures/real-t0-t1.manifest.json
python -B -X utf8 -m iqs_experiment_desk build --inputs $snapshot --lock $lock --manifest fixtures/real-t0-t1.manifest.json --output .test-work/run-01/bundle
python -B -X utf8 -m iqs_experiment_desk serve --bundle .test-work/run-01/bundle --host 127.0.0.1 --port 0
```

成功stdout机器JSON，serve首条输出URL/PID/bundle_sha256；服务日志stderr，不向网页注入本机secret路径。非法输入exit2、输出存在/路径冲突exit3、未知carrier版本exit4；不覆盖输出，不绑定0.0.0.0。所有assets本地，GET/HEAD只读，POST/PUT/PATCH/DELETE405。禁止任意文件读取、upload/import写接口、执行输入命令、自动刷新活动目录、外网fetch/CDN/analytics/模型API。UI过滤仅在已构建view进行，不回源或后台发请求。

## 界面行为

默认显示数据集ID、冻结时点/证据版、真实vs合成标识、registered/supplied两分母及unknown状态。公司（完整subject）、模型/endpoint、phase、strategy、repeat、证据版本可组合筛选与重置。筛选状态可复制为本地URL参数，但不允许参数变任意路径。多个证据版本同列对照时强提示未配对，不跨版本宣布优劣。

矩阵：行=明确题号/维度，列=模型×phase×strategy×repeat×evidence version；每格分别显示执行状态、合法答案状态、原独立质量状态/未审、claim问题计数、证据partial/proxy/missing/contradicted、费用unknown。缺答案不显示0分，missing registration不缩分母，不把valid涂成correct绿色。点击单格打开原答案/修订、来源片段及artifact hash、判定来源与未关联诊断；公开盲评bundle不泄露private身份。原文本安全转义，不将source/title/rationale当HTML执行。

时轴：按session分行，区分SDK step/native attempt/HTTP response/unknown dispatch，标duration未知/clock缺失/未启动，缺时间独立组不伪造坐标。点击event定位矩阵对应行；没有可靠关联则显示unlinked事件。重复回执去重依据明确ID，ID相同内容不同以冲突可见，不安静取最后一项。

计量区：已知估算小计、完整费用、现金账单、未知receipt、预留分别展示，图表缺值断开/标unknown，不能归零。请求/response/step各计数及耗时coverage单列。工具comparison accuracy/winner=null保持；独立审查partial/sufficient只是显式已导入来源状态，不能把结构计数当准确率或新赢家。无充分判定时不显示每正确答案成本。原S1累计预算不在此UI增减/重置。

在1280宽桌面和390宽窄屏可用，矩阵允许受控横向滚动但页面关键状态/筛选/明细不溢出；键盘可筛选/切换/打开关闭详情，状态不只靠颜色表达。显示可理解的错误、空筛选、schema版本不支持与资料缺失，不能静默退回demo或另一公司。

## 必须执行的测试

- 单元：join完整主键、同公司异证券、同模型不同endpoint、phase/repeat/证据版不混、null计量不归零、同回执两载体不双计、ID冲突拒绝、时间缺失不造0、未解盲匿名判定不逐行关联、valid≠correct、partial≠充分、input hash/重复键/NaN/未知协议/路径大小写碰撞/junction/穿越等反例。
- 实际输入集成：固定T0/T1构建，T0 registered72/supplied72/legal4/missing68；T1 registered72/supplied36/legal15/missing57，另外三场not_started可见。cross comparison accuracy/winner保持null；T0已知估算USD0.100300、T1已知小计USD0.107693与未知usage/完整费用null分别可见，不伪造账单。实际EVID保留53维，before42missing/7proxy/4partial、after21missing/16proxy/16partial/direct0。匿名review不能擅自填slot级结果；CLAIM example明确synthetic/example来源。原件rawSHA全部保持。
- CLI E2E：validate→build→serve，读取真实bundle，GET200/写方法405、path traversal拒绝、错误bundle/hash非零、已存在输出拒绝；搬迁后核心对象hash一致，不回活动源补文件。
- 浏览器E2E（真实浏览器自动化）：1280与390宽、筛选公司/模型/phase/repeat/证据版、矩阵↔时轴联动、明细原文与null状态、空结果/坏版本、键盘和窄屏；捕获所有网络请求，除本机GET/HEAD外0，POST不会写，恶意`<script>`/事件属性/URL不执行。实际服务进程/端口finally退出并核释放，原输入保持。截图只作佐证，需可复现断言/日志。
- 一个整包集中审查接口、UI交互、数据含义、真实反例和清理，不逐helper门。允许合理本地实现选择，不以生产产品扩展范围。

交 `docs/handoff/EXPERIMENT-DESK-05/`（统一模板），含启动示例/录屏或截图引用、单元+集成+CLI+浏览器测试真实argv和结果、兼容矩阵、未知/未关联字段清单、来源输入保持和清理。正常payload+handoff提交、不push/remote。它只是候选实验桌面，production_ready/financial_qualification_granted=false；没有新准确率/赢家/模型请求，不接生产UI。
