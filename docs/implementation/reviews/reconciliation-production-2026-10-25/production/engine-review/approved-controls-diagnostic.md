# generation2 approved-controls 阻断：独立只读诊断

审查者 `/root/review_bank21`。本次只读源码、当前失败日志、公开交接文件及原账本的精确 work/binding 元数据；未运行 owner、SDK、preflight、测试或 API，未改源码/数据库。原账本 mode=ro 读取前后 SHA 相同；详细文件 SHA 和已脱敏字段在 `approved-controls-diagnostic.json`。没有输出 prompt、safe 正文、lease token、环境变量或密钥。

**结论：原生授权记录没有缺失，不是1.2协议不兼容；调用者遗漏了原公开执行控制登记步骤。原 guard 拒绝正确。**

## 因果链

1. `StockQAbyLLM/src/utils/quick_scan_refresh_execution.py:209` 在 `ApprovedRefreshSession` 构造时将 `_execution_controls` 设为 None。
2. 同文件 `:281–288` 的 `check()` 对 `iqs.refresh_request/1.2.0` / `1.3.0` 且还有 pending dispatch 的工作要求调用方先经原公开 `assert_execution_controls(...)`；字段仍为 None 就准确拒绝 `refresh_execution_approved_controls_required`。
3. 本轮 `run_generation2.py:235–283` 从 `prepare_execution` 到 `factory.create_company_scan_task` 没有调用这个公开方法。`scripts/shared_company_task.py:263` 一进入 factory 就 `owner.check()`，故在构建任务、native attempt 或模型请求之前触发该 guard。
4. 原公开 `assert_execution_controls`（StockQA `:371–404`）验证原注册 binding3.0/4.0、当前 cohort；如有 `comparison_controls` 则还要求具体控制值及类型完全相等。最后登记调用者实际采用的控制，之后每次 `check()` 仍会重核，不把登记当可缓存的人类权限。

## 原记录核实

- 当前 `WORK_c9374943a7c44990ba69d67fa7346529` 是 IQS_05/generation2/pending。
- 原账本 binding 为 `stockqa.owner_refresh_binding/3.0.0`，`owner_control.purpose=retry_unusable_answer`、target generation2，cohort 与原 refresh1.2 request 相同。
- `comparison_controls=null` 符合本次用途；它不是缺失的 comparison 授权。原 `retry_unusable_answer` 本来就不附加 comparison 控制，不应为了过检查改用途或伪造比较参数。
- 实际原 refresh preview 为 ready/`dispatch_new_generation`；原 rc2 admission 为 accepted、permission authenticated、registered；原 rc1 retry decision 与 owner_control 已有绑定。不得把本错误重新描述成人类没有批准，也不得新增用户审批询问。

## 最小正确路线

在 shared factory 首次 `owner.check()` **之前**，由真正持有冻结执行计划的调用方调用原公开方法：

```python
owner.assert_execution_controls(
    pack_size=1,
    thinking_enabled=True,
    max_output_tokens=16384,
)
```

这些值必须来自本次已经冻结的 singleton pack、实际开思考参数与单请求输出 token 上限，不能拿待批准 control JSON 自证。可由当前 generation2 driver 在构造完这些具体运行参数后显式履行该调用合同；若改共享 factory，则其 API 必须有可核的实际执行参数并确保实际 SDK/pack 与之相同，不能猜测每个任务都采用相同控制。

**不能**给 `owner._execution_controls` 直接赋字典、删除/延后 `owner.check()` 直到发送后、对 refresh1.2 整体跳过、改 binding/原 rc1/rc2 或把 null 补成虚构 comparison 授权。也不需要升级原 owner policy、换预算、重建工作或改原 task 上限。

这是本轮 caller 对原公开方法的接线遗漏；原 StockQA 方法与已批准协议本身能够表达这条 retry。建议在原 driver/factory 的整节点定向验证中覆盖“未登记先 check 仍拒”“公开登记后原检查继续运行”“与实际冻结/SDK配置不同仍拒”，不增加独立小节点审批门或重跑无关全量套件。此报告没有执行该正确路线，不宣称 generation2 preflight 或真实请求已成功。

已将根因与原接口位置发给 `/root/inspect_production`，由其与总控决定最小落点及修复；本 reviewer 不改施工中的源码。
