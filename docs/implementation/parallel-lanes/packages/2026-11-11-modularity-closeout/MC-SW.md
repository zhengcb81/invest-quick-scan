# MC-SW：StockWiki五能力域与公开数据owner

可独立交harness。先读 [总路线](README.md)、[契约/TDD](contracts-and-tdd.md)、[调查](architecture-audit.md)、[交接](integration-and-handoff.md)。本包不重做已经通过的事实CLI与数据库设计。

## 2026-11-11 入场盘点与并线清单

详见[存储/消费者完整实查](intake-audit/store-consumers.md)：`master@12c441e` tracked clean；7个未跟踪运行库/日志全部保留且不入Git。36个分支、30个worktree已核对；18条非祖先分支并非18个独立缺口。

**真实主候选是C38 `codex/dashboard-c38-sw-release@4532b0d`**：136条变更路径中当前master缺129条，另7条内容不同。不是已全部并线。C1的7be0c97/60a85ef已patch等价进入C38，不能重复合两线。

- 先在隔离树把名单`dashboard_membership_request_cli.py`、`quick_scan_membership_read.py/request.py`与DDL/事务/universe/backup依赖并到当前master。公开wire `stockwiki.membership_request/1.0.0` 的apply/lookup/history保持，交IQS C38消费者配对。精确测试命令与同键/错键/分页/断线/并发场景见报告。
- C38余下已交付research/identity/onboarding/proof/binding/source-link/analysis-subject源码也列入本卡并线清单：逐能力域比对当前实现，缺失的沿原公开接口合入，自包含提交；若与D00当前writer重叠，记精确剩余提交/范围移交D00，不用“C38已验”跳过。只归拢已有功能，不新增业务研究或真实迁移。
- 两条B03的3个最终源文件相同且已被master移植增强；保留当前只读CLI/分离operator，不合回旧公开写入口。F05等真祖先不重合。B34剩余07fbb8a仅三份文档，可在C38收齐后纳入历史，不将它变成运行门。
- 含junction的backup测试目录、旧实验库/证据与`.d00-audit`源码保留。没有运行生产库迁移，不把clean源码误记为“所有分支已上线”。


## 工作范围

- 源仓：`C:/Users/郑曾波/Projects/StockWiki`，调查HEAD `12c441e`、tracked clean；开工重新核实。
- 独立树：`C:/Users/郑曾波/Projects/iqs-modularity-worktrees-20261111/MC-SW`；`codex/modularity-stockwiki-20261111`，尚未创建。
- 允许：`stockwiki/quick_scan_*`及必要纯规则/port、相关tests、现有测试分组、公开schema资源的必要兼容说明与本包PWF。身份/名单已有实现只在具体失败时修改，不开新功能。
- 禁止：写IQS/QA/CA/RT/Theme/Industry/company-wiki；动正式SQLite、名单、原观察；添加新状态库或授权系统。

## 目标架构

五能力域：身份名单、观察入库/ACK、刷新准备、查询投影、交付对账。CLI/组合根装配，纯规则下沉。域内helper不用逐文件version/export；域间只传所需DTO/port。公开query/prepare/import协议继续按C4，2.8不能借重构自动宣称上线。

已确认`inspect_publication(control, outer)`依赖整个control；publication反向import owner、delegation反向import owner；observation/import/qualification/dispatch也形成环。不要只延迟import或将私有名改公有。源码目录有效性检查由composition通过公开入口/能力完成，publication只看结果。

## 步骤

1. 将67个quick_scan文件映射到五能力域与基础设施，记录实际跨域边/事务owner；不追求所有文件绝对无环。
2. 先给publication写纯DTO/最小port正例（缺其它control属性仍可运行），以及错误身份/权限/原receipt负例；提取需要的值和effects，移除万能control。
3. 先用现有入库事务/ACK行为锁住import循环，再把纯校验/装配移到正确层；避免复制状态机、重建SQLite或改原历史。
4. 替换对CA/RT `src/<package>/__init__.py`的业务判断；composition只需公开入口可调用，路径可配置，不要求内部目录名。
5. 将边界测试改成能力域方向与owner数据隔离，保留必要负例；按C4明确本仓config/quick_scan_facts_query.schema.json的2.7来源，并在tests/fixtures/public_contracts/facts-2.7/交付少量公开JSON正反例及预期说明，供TH/IN同向量复测。保留当前closed字段规则，不强推2.8。
6. 独立审查最终设计/差异和事务反例，自包含提交。没有remote则只交本地commit，不创建remote。

## TDD

|用例|应有结果|
|---|---|
|publication输入只有所需DTO/窄port|正常通过；不访问整个owner对象|
|对方实现目录换名，公开命令不变|准备/对账继续可用|
|跨能力反向依赖mutation|架构测试失败；域内helper协作通过|
|事务提交前/后中断、ACK重复、局部题失败|原ACK可恢复，不重复入库，不拖住已封存题|
|错主体/挂牌、错观察摘要、错snapshot/query/operation|真实冲突拒绝|
|只读query/分页/export/reopen|owner库不变，capture只写消费者根|
|候选事实和缺可选诊断|explore可看，strict不升级信任；有效旧结果不因诊断缺失消失|
|同义schema格式变化/兼容optional字段|符合C4则接受；错误major/必要语义仍拒|

现有短组：

```powershell
python -B -m pytest -q tests/test_f05_module_api_boundaries.py tests/test_quick_scan_prepare_cli.py tests/test_quick_scan_subject_dispatch.py tests/test_quick_scan_query_v2.py tests/test_quick_scan_facts_wire.py tests/test_quick_scan_delivery.py tests/test_quick_scan_store.py -p no:cacheprovider
```

针对变化选择运行；完成节点再用现有`python scripts/checks.py --help`确认daily入口后跑常规短检查，不每步全套。新测试在本仓正常组注册。

## 交接

本仓命名PWF、`docs/handoff/MC-SW/handoff.md`：能力域映射、public schema路径/版本、最终commit、真实测试及独立agent结论。无新源文件布局许可或逐题审核凭证。总控之后用隔离真owner运行公开查询到两个消费者，本包不能自报G3/G4或金融资格完成。
