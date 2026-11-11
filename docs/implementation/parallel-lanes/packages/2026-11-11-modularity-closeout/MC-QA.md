# MC-QA：执行owner与已付结果边界收口

可独立交harness。先读同目录 [总路线](README.md)、[契约/TDD](contracts-and-tdd.md)、[调查](architecture-audit.md)、[交接](integration-and-handoff.md)。本包只写StockQA，不代改消费者。

## 工作目录与已有候选

- 源仓：`C:/Users/郑曾波/Projects/StockQAbyLLM`，HEAD `4c24789`，磁盘facade1.5、HEAD无该文件。
- **必须同时只读比较**：`C:/Users/郑曾波/Projects/invest-quick-scan/.tmp-stockqa-current-wt-20261110`，同HEAD，facade1.8、87份tracked差异另有新API/测试。这里有已有修复，不是可随意删除的临时垃圾。
- 实现树：`C:/Users/郑曾波/Projects/iqs-modularity-worktrees-20261111/MC-QA`；分支`codex/modularity-qa-20261111`，本轮未创建。
- 允许范围：company facade/task factory/runtime、owner refresh/lifecycle/服务接口、工作库/回答保存/恢复的必要接线、相关provider或runner调用点、针对性测试和本包PWF。既有其它WIP保留；不要整体拷贝87份diff后无差别提交。
- 禁止修改IQS、CA、RT、SW、真实llm配置/额度库/回答与生产部署。

## 设计目标

StockQA独占SDK、搜索、额度、请求状态、已付响应、逐题保存、checkpoint/outbox。普通扫描和共享引擎使用同一owner操作；消费者只拿公开DTO/opaque句柄。core依赖接口，不依赖runner具体类；store/provider各自实现效果，唯一composition装配。

保留candidate的opaque runtime/session和lifecycle Protocol。`quick_scan_company_api.company_agent_public_api`不得在校验操作后再返整个module；改为只使用明确公开导入或有限操作投影。不要新造一套“安全对象框架”。

## 实施步骤

1. 对canonical1.5与候选1.8做功能差异归拢，保留非本包改动，形成可追溯输入；确认所有新增API和支持文件都进入工作树。
2. 先写只公开fake与DTO深复制/句柄访问反例，验证lifecycle业务不索取具体runner/store。若已有通过则保留，不为RED破坏实现。
3. 分清发送与重放：已有结果保存、补封和交付只核原数据/身份/幂等，不重新要求新预算额度或key；新模型请求仍按原budget/lease准入。
4. 收拢跨owner窄接口，移除具体CA/RT源路径检查；按C1/C2/C3协议版本与操作兼容，普通只读不强制所有模型能力。
5. 收敛千行反射扫描为域方向/公开接口测试，保留真实业务负例。分开历史实验资料检查与本次生产短测试。
6. 受影响回归、独立agent审最终完整差异并修完；形成包含源码/接口/资源/测试的自包含commit。不要只提交测试。

## TDD重点

|用例|验收|
|---|---|
|lifecycle/services fake没有私有runner/store/client|正常功能成功；改回私有访问则测试失败|
|改DTO嵌套dict/list；访问返回句柄`.store/.client/.task/.__dict__`|owner不变；未声明状态不可普通读取|
|原paid响应，无key/新额度不可用|逐题保存/补封/交付成功，新增模型/搜索0|
|两公司、两任务、answered/pending/delivered混合|已付分支0重发；never_sent按原授权首次发，unknown先查不盲重试；不串主体/伪报全完成|
|原响应保存前后中断；ACK已存但本地未标记|新进程从公开操作恢复，保留原时间/hash/ACK|
|fresh与expired时钟分支|fresh不发；expired新请求仍需有效凭证与预算，缺key保留旧结果并报无法刷新；查询不续期|
|合法兼容minor/optional能力，错误major/必要操作缺失|可兼容者通过，真正不支持在claim/HTTP前失败|
|具体实现移动，公开API不变|消费者仍能执行，不依赖内部路径|

现有短组入口：

```powershell
python -B -m pytest -q tests/unit/test_quick_scan_company_api.py tests/unit/test_quick_scan_company_contract.py tests/unit/test_quick_scan_company_task_factory.py tests/unit/test_quick_scan_module_boundaries.py tests/unit/test_shared_company_entry.py tests/integration/test_owner_research_services.py -p no:cacheprovider
```

使用短临时basetemp和原仓标准检查；逐步只跑受影响项。接口测试不存在于canonical HEAD但存在于候选时应带入，不可删掉命令或跳过后称通过。本包不进行收费API。

## 独立交付

自己的`.planning/modularity-closeout-20261111/`三份PWF；最终`docs/handoff/MC-QA/handoff.md`。列候选来源、接口1.8实际操作、兼容floor、RED/GREEN、独审与自包含commit。总控从commit整合，不读本机未提交候选作最终证明。若CA/RT未交，只用公开fake完成本包；真实组合留总控，不代写它们。
