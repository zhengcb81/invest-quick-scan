# IQS 整改候选交接

候选以 `e0ad75760ff14ce135a7857b090fda9b4663c92f` 冻结。总控候选目录 `C:/Users/郑曾波/Projects/company-wiki/.planning/r25/iq`。源码和测试在同一补丁及 SHA-256 清单中。原生运行树及在途主工作区仅作只读基线。

在候选目录用本机 Python 复跑。短 `--basetemp` 适配 Windows 进程和锁测试。各命令用不同的临时目录。

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
python -B -m pytest -q -p no:cacheprovider --basetemp ../iq-review-a -c pytest.ini --confcutdir . tests/test_runtime_recovery_contract.py tests/test_runtime_feedback_boundaries.py tests/test_dashboard_module_boundaries.py tests/test_shared_public_boundaries.py
python -B -m pytest -q -p no:cacheprovider --basetemp ../iq-review-b -c pytest.ini --confcutdir . tests/test_dashboard_batches.py tests/test_dashboard_product_prepare_api.py tests/test_dashboard_prepare_ordered_routes.py tests/test_dashboard_prepare_owner_boundary.py tests/test_dashboard_http.py
python -B -m pytest -q -p no:cacheprovider --basetemp ../iq-review-c -c pytest.ini --confcutdir . tests/test_iqs_provider_transport_diagnostics.py tests/test_stockwiki_g2b_frozen_golden.py tests/test_legacy_freshness_owner_port.py tests/test_scan_result_check.py
```

人工对照时，从原 GET 取得 `failure_diagnostic.details_ref`，用 `python -B scripts/iqs_feedback_owner.py get-diagnostic <ref> --state-root <root>` 验证异常类型和帧。`get-run-trace <run_id> <attempt_id> --state-root <root>` 冷读已保留阶段。两个读命令采用统一 JSON 输出。重投诊断仍走独立的 `republish-diagnostic`。

验收重点是实际准备 POST、锁持有期间退出、新进程重复 GET 及重提原请求。检查同一个原异常引用、一个 apply、零新的模型或下载、无新增 outbox 文件。另检查本地立刻有记录但 F4 投递失败、强停之前尚无原异常、配置拒绝无原配置内容、成功输出未被日志改写。批协调显式恢复后核对旧错误没有附到新 attempt。通过后由总控协调本仓发布，本次候选交接未跑生产请求。
