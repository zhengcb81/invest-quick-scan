# IQS 未提交、未并线与工作树盘点

2026-11-11，基线 `master@5c8ba432a4798eff259da52c6a372f6edc1a9665`。只核本地 Git refs，不将 origin 缓存当实时远端。源码修改未被本轮覆盖；分支谱系、patch 等价和当前文件内容分别核对。

## 已提交和未提交是两件事

- `bb20529`、`e0b8633`、`fbe5b39`、`5c8ba43` 已在本地主线，尚未发布到已知 origin/master；它们不是待合侧枝。前三项中共享引擎修改仍需 QA/Runtime 同一组合，不能为了发布文档而把依赖未就绪的消费者一起推成可用产品。
- 本轮开始有 **28 个 tracked 修改**：26 个源码/测试文件、1 个 query capabilities schema、1 个旧施工包 README。不是28个未知垃圾文件。
- 未跟踪列表有31,268项；这是Git路径数，不能当作31,268份新功能。大部分是pytest隔离输出、旧验收材料和harness本地状态。正常 `scripts/`、`tests/`、`schemas/` 下没有额外未跟踪源码。

## 当前源码 WIP → MC-IQS

|组|路径|处理和最小验证|
|---|---|---|
|题库/路由公共操作|module_contract、module_registry、question_manifest、question_selection、question_sets、routing、refresh_contract_cli、route_store_handoff、stockqa_adapter|公共parse/read/validate/select替代跨模块私有调用；保留兼容alias。沿MC-IQS题库/路由短组归拢，不回退|
|实验观察上下文|batching_benchmark、accuracy_pilot、accuracy_followup及3个pilot/benchmark测试|用可嵌套context manager恢复observer，替代直接改线程局部变量；已有WIP，不启动新付费实验|
|共享引擎/已付恢复|shared_company_ports、shared_company_task、shared_company_engine、answer_validation及7个恢复/边界测试|IQS需要QA≥1.7，task构造交回owner，语义资源用公开投影。依赖MC-QA的自包含1.8与MC-RT/CA组合，不只提交consumer一半|
|能力schema|schemas/quick_scan/query-capabilities.schema.json|supported_query_wires移除固定7项并放宽上界；保留，按MC-IQS能力增量/未知版本测试验收，不以schema放宽代owner实现|
|旧日期记录|2026-10-10/README.md|4行旧验收/R1链接说明，属于历史文档修订；保留，不覆盖当前9包状态|

完整初始tracked清单：

```text
docs/implementation/parallel-lanes/packages/2026-10-10/README.md
schemas/quick_scan/query-capabilities.schema.json
scripts/accuracy_followup.py
scripts/accuracy_pilot.py
scripts/answer_validation.py
scripts/batching_benchmark.py
scripts/module_contract.py
scripts/module_registry.py
scripts/question_manifest.py
scripts/question_selection.py
scripts/question_sets.py
scripts/refresh_contract_cli.py
scripts/route_store_handoff.py
scripts/routing.py
scripts/shared_company_engine.py
scripts/shared_company_ports.py
scripts/shared_company_task.py
scripts/stockqa_adapter.py
tests/test_batching_benchmark.py
tests/test_company_scan_guards.py
tests/test_mimo_pilot_extension.py
tests/test_mimo_pro_pilot.py
tests/test_read_only_replay_boundaries.py
tests/test_shared_answer_semantics.py
tests/test_shared_company_engine.py
tests/test_shared_company_engine_finalization.py
tests/test_shared_company_task_api.py
tests/test_shared_public_boundaries.py
```

## 全部侧枝的处理

|分支/提交|实际状态|决定|
|---|---|---|
|d00-b03-iqs-service `fb262e0`；x-b03-live-owner-verify-01 `fccbc4f`|主线真祖先|不用再合|
|f05-mainline-closeout-20261109 `3f085bc`；f05-query-paged-response-01 `18a8ad7`|主线真祖先|F05已并，不能重新列待并|
|e12-safe-job-closeout-20261109 `9caccb4`；x-b03-live-owner-verify-repair-01 `f917b6d`|独有提交均 `git cherry -`|已摘取等价补丁，不做重复merge|
|iqs-job-facade-01 `23d20b8`|10个独有commit，但产品经 `8ea7c37/59c1dd5` 对齐并继续增强；当前facade/tests比旧分支有313增69删|不整支合回旧PWF/旧代码；原交接资料留在旧分支|
|d00-all31-universe-service / dashboard-iqs-deeplink-service，均 `e55fdbc`|12个旧独有commit；link功能经 `0b70ac6/cdff0fa/fe489ea` 进入并改造，不能由cherry的“+”断言都漏合|MC-IQS只复核仍有意义的旧API反例；旧 `test_dashboard_iqs_link_api.py` 不在当前主线，测试覆盖迁移需明确，不恢复旧service实现|
|dashboard-owner-iqs-b03-company `8e14a48`|旧link祖先加B03；最后4修复patch等价，B03主体已被主线移植增强|不整支覆盖当前公开owner边界|
|dashboard-owner-iqs-c1-authority `59e8619` / dashboard-c38-iqs-release `b851111`|**两分支tree完全相同，真实功能仍未并**：8f6a5ee↔418bb94、59e8619↔b851111；当前缺membership_request及其两组测试|只选C38一个来源，加入MC-IQS的明确并线项；与MC-SW@4532b0d配套，不重复合两线|

### 唯一明确新增的跨仓并线组：名单请求 authority

IQS候选：`codex/dashboard-c38-iqs-release@b851111`，实质提交 `418bb94`，测试分组 `b851111`。涉及 `dashboard_membership_request.py`、`dashboard_owner.py`、`dashboard_service.py`、`test_dashboard_config_refusal.py`、`test_dashboard_membership_request.py`、`tests/suites.json`。

先由MC-SW把C38的公开membership read/request/history与当前DDL/事务合流，提交自包含owner；MC-IQS再移植请求wire、精确幂等lookup优先、preview/apply、显式错误配置不落默认库。不能整文件覆盖现有慢锁隔离、E12、B03和公开CLI；不能把旧历史pin校验作为新门。Dashboard消费端已在main，无需再做一套。

两端使用隔离名单库测试：同键同请求回放、同键不同请求冲突、expected-version竞争、中断后查回、history分页、错配置不切另一真实库；最后走当前Dashboard公开名单入口。旧卡范围测试通过不等于生产名单迁移。本轮不启动真实名单写入。

## 15 个注册工作树

- canonical根有上列28项；`_b03live/service`、`_b03live/service-repair`、`d00-b03-iqs-service`、B03/C1/C38和deeplink源树均无非忽略未提交改动。
- IQS内 `.worktrees/e12-safe-job-closeout-20261109`、`.worktrees/f05-mainline-closeout-20261109`干净。
- `.worktrees/f05-page-response`显示7份release/routing JSON修改，但**磁盘原字节全部等于各自HEAD且等于当前根文件，文件名hash也匹配**。属于Git行尾/索引表示差异，没有待丢弃的新题义；不把这些修改提交成新功能。
- `iqs-job-facade-wt01`显示6份release JSON修改；原字节全部等于其HEAD。旧3.0与当前root不同，不覆写旧发布物，也不拿旧锁失败追加本轮门。
- Temp `giqs01-final/svc-base-full`、`svc-full`以及B-read-projection嵌套runtime树显示大量D，是旧不完整隔离检出，不能把数千个删除并回主线。保留登记根，未执行worktree prune/remove。
- `.worktrees/stockqa-delivery-port-20261109`只是旧源码副本，不能通过向上找到IQS的Git结果当作其自身已并线；归属MC-QA，详见[执行链补查](execution.md)。

## 未跟踪内容的处置

|内容|结论|
|---|---|
|52个root pytest basetemp + QA候选10个 + Runtime候选9个|本轮已删71目录，20,728物理文件、1,526,513,329字节。删除前核精确边界、无reparse/内嵌.git、pytest子节点和无活动进程引用|
|`.tmp-stockqa-current-wt-20261110`、`.tmp-modularity-runtime-20261110`|独立Git候选，完整保留；只删其中已证实的测试输出|
|较早 `.tmp-stockqa-modularity-20261110*`、`.tmp-runtime-modularity-20261110`、delivery-port副本|旧源码快照；交MC-QA/RT比较归拢，不能按tmp名字删除，见执行链补查|
|约4,268份docs未跟踪项|旧W15/B01/parallel验收副本、报告和交接；保留原证据，不夹带到本轮文档提交；也不把原件存在视为当前测试通过|
|`.mimosa`约11,986项|harness hook-state/baseline/锁与本地状态；未读取个人内容，保留，不由IQS自行注销其它会话|
|根 `.tmp-*.log`|此前测试诊断，保留作为候选排错来源；不与pytest可再生内部数据混删|
|`csc-financial-source-report.md`|76,058字节研究报告，保留；不属于本轮源码|
|`opencode.json`、`nul`|本地配置/特殊名称文件，保留，不因未跟踪或Windows设备名误判为空|
|`audit_out_path.txt`|内容仅旧 `/tmp/tmp.PzekN3KQuL`，21字节，无产品含义；本轮删除|

目录盘点、清理日志与前后保护摘要保存在本机忽略的 `runs/modularity-intake-20261111/`。这只是本轮操作记录，不新增任务回执、许可证或日常审查门。
