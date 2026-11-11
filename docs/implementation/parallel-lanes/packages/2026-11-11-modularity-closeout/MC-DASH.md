# MC-DASH：统一Dashboard的m0/m6/m8边界收口

交给Dashboard侧harness/D00协调，不覆盖其原九模块计划。先读 [总路线](README.md)、[契约/TDD](contracts-and-tdd.md)、[调查](architecture-audit.md)、[交接](integration-and-handoff.md)，以及本仓AGENTS和`.planning/unified-dashboard-2026-10-26/START_HERE.md`/`OWNERSHIP.md`。

## 工作树与归属

- 源仓：`C:/Users/郑曾波/Projects/investment-dashboard`，调查HEAD `b707473`，不是旧0dcf61f；dirty状态开工核。
- 建议工作树：`C:/Users/郑曾波/Projects/iqs-modularity-worktrees-20261111/MC-DASH`，分支`codex/modularity-dashboard-20261111`。若D00已有隔离树，使用其指定树并回报。
- 写入限m0共享ports/composition必要接线、m6 quickscan、m8 jobs、application/service中相关依赖/存储注入及对应tests/文档。D00在既有ownership中登记具体路径，避免D01/D03/D04正在同改。
- 不重开m1–m5/m7/m9建设、不改RF/company-wiki、不手写generated合同、不修改IQS或其它owner、不动生产配置。
- 包作者只更新D00分配的子计划/交接，**D00独占该仓总PWF**；无需再问用户权限。

## 目标与步骤

1. 保留ports→HTTP/CLI adapters与当前iqs/包；核实应用层是否仍依赖具体SavedViewStore、过宽Mapping或owner实现。
2. 先写方向和替换TDD：application/domain只能依赖domain/ports；用最小QuickScanPort/JobPort及内存view store驱动m6/m8，不导入adapter。
3. 必要时补最小存储协议及构造注入，在现有composition创建SavedViewStore。不要新建DI容器/框架；application/ops内部helper调用不算跨域。
4. 按C6与owner真实合同检查额外字段/版本/链接：有协议依据的封闭shape保持，允许的扩展不能误拒。镜像owner内部白名单改为公共约束；身份/scope/command/安全URL仍核。
5. 真CLI stub进程与HTTP server替换测试，不能全靠monkeypatch私有run_cli。GET/渲染不执行任务；未知提交只查询原键。
6. 短测试组包括默认pytest没收集的adapter测试。一次独立agent审查最终差异，交D00并线；IQS只接收版本和集成结果。

## TDD重点

- 非法application→adapters、domain→transport mutation被检测；合法ports导入通过。
- fake→实际HTTP/CLI adapter替换不改application/UI；没有owner源码/目录仍可做消费者测试。
- DTO嵌套修改不影响domain/持久状态；存储可替换。
- 允许optional字段/兼容版本通过；错误身份/作用域/命令键拒绝。
- 请求超时未知、重启、重复点击保原键，不假成功、不自动再发。
- IQS不可用只影响相关卡片，其他Dashboard页正常。
- 不为当前功能要求旧文档计数、实现文件名或独审receipt。

现有入口：

```powershell
python -m pytest -q tests/integration/test_module_boundaries.py tests/adapters/test_iqs_job_reply_protocol.py tests/adapters/b03_company_result/test_iqs_company_result.py tests/integration/m8-jobs-integrate/test_iqs_job_adapter.py tests/integration/m8-jobs-integrate/test_factory_jobs_wiring.py --basetemp=.test-runs/mc-dash -p no:cacheprovider
```

在`apps/web`运行：

```powershell
npm run typecheck
npm test -- src/features/quickscan src/features/jobs src/shared/capabilities.test.tsx
```

测试用自有临时root/端口；不触碰既有Dashboard部署。架构测试收敛到层次和public ports，不再扩Python反射解释器。

## 交付

按D00既有handoff方式，向IQS提供绝对路径、最终实现commit、合同是否变化、短测/独审结果和真实I7待验项。D00负责本仓并线/远端，IQS负责跨仓组合；禁止双方同时改总PWF。已无缺陷的模块验证即可，不为了本卡进行无意义重构。
