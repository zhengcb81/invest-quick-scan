# 回归：owner 查询对既有 CATL subject 也开始拒绝 — 2026-10-18

## 现象

用 `stockwiki.quick_scan_query_v2_cli` 对 CATL 的既有 subject 做 get_profiles（字段 score.iqs_12/16，和当初成功的那次完全相同），现在返回：

```
{"status":"rejected","error_code":"subject_contract_output_invalid","API_requests":0}
```

000026 的任何字段同样被拒。既有 2 条 CATL observation、画像页、身份数据都还在，**只是新查询/capture 被拒**。

## 已排除

1. **不是 current package 切换**：把 `questions/releases/current.json` 临时改回旧包 `pkg_24f0…`，仍然 rejected。
2. **不是 000026 subject 导入**：用导入前的 `analysis_subjects.sqlite` 备份做副本，仍然 rejected。
3. **不是 release 校验本身**：手动跑 `scripts/subject_dispatch_cli.py --operation release` 返回 validated，且 release 结果与 CATL manifest 的 `pkg_b5a41…` 一致。

## 尚未定位

- 失败点在 `quick_scan_subject_authority.IqsSubjectContract._call`：CLI 子进程返回被 `parse_package` 判为无效，或输出字段不满足 `protocol/status/API_requests=0/database_writes=0/identity_attested=false` 之一。
- 追踪包装没有捕获到 subprocess 调用（说明失败可能发生在更早的请求校验或另一个 contract 实例），需要进一步 bisect。
- 时间上可疑的改动：routing 包发布（新 release 文件/current 切换）、`subject_dispatch_contract.py` 的 research_only seam、以及本次会话早先的 publication 改动。

## 影响

- **新公司画像/新题运行被阻塞**；已有观察、画像页、身份/金融复核不受影响。
- 没有付费调用被发出（API_requests=0）。

## 下一步（根因修复，不猜）

1. 在副本里把 release/current/代码逐项回退到“CATL capture 成功时”的状态，二分定位；
2. 给 `IqsSubjectContract._call` 加临时诊断（记录 operation、returncode、stdout/stderr sha），找到具体失败的 CLI 操作；
3. 修复后先验证 CATL 原字段 capture 恢复，再做任何新题运行；
4. 未恢复前不做真实 policy/admission/付费 run。

## 边界

- 没有回滚任何真实业务数据；current.json 当前是旧包（临时测试状态，待根因结论后决定）。
- 没有模型调用；只有本地 CLI 调用。
