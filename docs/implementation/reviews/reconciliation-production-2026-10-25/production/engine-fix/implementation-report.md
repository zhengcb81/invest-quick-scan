# 共享引擎显式生产封存：实施记录（2026-10-25）

## 范围与公开接口

- 主仓：`scripts/shared_company_engine.py`；新增 `tests/test_shared_company_engine_finalization.py`；更新 `tests/test_company_scan_native_e2e.py`。
- StockQA：`src/utils/quick_scan_owner_research.py`、`src/runners/llm_runner.py`；新增 `tests/unit/test_owner_finalization.py`；更新 `tests/unit/test_owner_native_inspection.py`。
- 未修改 PWF、其他外仓；未提交或推送。本分工不执行收费 API。

新公开 API：`finalize_shared_engine(task, services, export_dir)`。

原 `execute_shared_engine` / `resume_shared_engine` 默认仍只产生研究导出。显式封存重新核验原 task bundle、checkpoint、journal 和 runtime sidecars；答案必须与原 native safe output 完全相同，并属于该题原 work 的成功 attempt。原 native 引用不能被另一题、另一个 batch 成员或后改答案替代。

StockQA 新公开方法 `restore_finalization_handle(question_id, *, native_reference)` 只恢复原 successful attempt 的同一 token/epoch、未过期租约到原服务内存。不 claim、不 renew、不写数据库、不发请求。编排层没有复制 StockQA 私有租约逻辑。

写入统一复用原 `commit_standard_answers` → 原 `lifecycle.after_question` → 原标准答案/上下文/receipt 校验 → 原 checkpoint 和封包流程。已保存同原 receipt、同完整标准答案的 checkpoint 走幂等补封；不会为补封创建租约或模型请求。

## 状态语义

- `completed`：所有原 checkpoint 已存在，且各题原 delivery 状态为 `ready` 或 `delivered`。
- `checkpointed_delivery_pending`：checkpoint 已保存，但至少一题 delivery 不在上述两态；回执列出 `pending_delivery_question_ids` 和每题原 `delivery_state`。
- `ready` 表示封包待发送，不宣称 StockWiki 已接收。`send_uncertain` / `rejected` / `conflict` 保留原状，封存 API 不发送 delivery。
- 多题写入保留逐题原子性。第 2 题失败时第 1 题已保存的 checkpoint 留存；再次调用复用第 1 题并只处理余项。没有自动模型重发。
- runtime summary 的 `owner_authority_verified=false`、费用 unknown、金融资格 false 均未伪造改写。

## 本轮真实发现并修复的回归

当前 StockQA `7dd3eb0` 的 Q09 修复将 ordinary `own_reservation` 标志收进 `dispatch_context`。研究 singleton 也经过该 scope，研究 SDK 随后按原预算 guard 拒绝 ordinary reservation，导致原实际软件测试出现一次脚本化检索、零 model attempt、`native_persistence_uncertain`。

修复为显式 `dispatch_context(..., research_budget_managed=False)`：默认 Q09 保留；研究服务明确传 True，此分支要求原 Approved session、原 native owner、同一 store、预算与 route，随后仍由原 SDK 强制 durable budget binding 并进行原预算预留。缺预算、外来 owner/store、外来 native 均拒绝。没有删除 SDK 预算检查。

外部搜索预算必须在 public admission 之前由 `build_shared_external_budget_policy(base_model_policy, search_policy)` 合成并冻结；owner 和 lifecycle 使用同一合成策略，`external_retrieval.model_policy` 保留未合成 base。不得修改已 confirm 的预算文件背后字节。原公开入口使用规范化 `manifest['manifest_sha256']`，并非 manifest 文件 SHA。

检索通过原 lifecycle 的 `external_retrieval` 注入，研究 SDK 的原 renderer 将检索 sources 放入实际发送的 user message，并加 system untrusted-data 规则。scope test 的正例要求输出 `scored=6`，其 evidence id/url 来自实际脚本化检索 context；不是空 evidence / not_applicable 正例。

## 已运行的测试与限制

- 原租约恢复方法：先 8 RED（缺方法），后通过原临时 SQLite 正反例。
- 编排 API：先缺函数/缺验证 seam 的 RED，后快速单元与旧 engine 回归共 29 passed（`main-tests-final.xml`）。
- StockQA 公共恢复、检查、幂等补封和 scope 单元：最终 **36 passed / 10.60s**（`native-unit-tests-final.xml`），包含 foreign-native 入口一致性反例。
- 随后的正常提交 hooks 仅以 isort 整理 `tests/unit/test_owner_finalization.py` 的 import 顺序；总控重跑该文件 **14 passed**（`owner-finalization-after-hook.xml`）。原 36 项结果对应格式化前的测试文件字节，不能称为格式化后 36 项重新全跑；生产源码和最终 actual 软件测试的 8 项源字节没有变化。主仓 3 个实现/测试文件已由总控提交 `23a05c8`，StockQA 4 个文件已正常提交 `8af0c86`；本分工不直接提交。
- 首个长路径 actual 软件测试是失败记录，不能当生产正例；它使用旧 ordinary flag + base-only admission，结果如上。原 sandbox 另曾拒绝题库 `os.link`，隔离测试改在沙箱外短路径运行，不修改产品硬链接语义。
- 最终 actual 软件 E2E 在 `C:/Temp/iqs-eng25-v679d1cb/t2` 自有源码/合成 fixture 环境 **1 passed、1 deselected / 649.21s**，进程 exit 0；`native-actual-finalization.xml` 为最终记录。第二轮在原 fixture 的 80 秒 `--install-delegation` 等待上限退出，尚未搜索/模型；只把测试 CLI wait 放宽为 240 秒后重跑必要 case，产品超时和权限检查不变。最终断言原 public owner + 检索 journal + 研究 SDK 实际发送的 context + `scored=6` 且 canonical 搜索 source ID + schema 2 checkpoint + 原 `ready` 封包；fresh 服务恢复同租约并重复封存后，checkpoint/delivery/attempt 不变，检索和模型脚本 wire 各 1 次。mapper/编排 doubles 不授予生产或金融资格。
- `actual-source-observation.json` 在最终必要 case 启动前记录 8 项实际执行源码 SHA；短路径 runtime 的两个 StockQA 执行文件与最终源字节相同。此前短路径快照缺最后防御性 native 类型/store 镜像的差异已在 `actual-source-observation-before-final-mirror.json` 保留；不把那一轮称最终字节全等。
- `actual-finalization-thin-result.json` 结束后重新核对 8 项 SHA 均未变化、均与最终源字节相同。原隔离库计数：1 个 `response_available` attempt、1 个 schema 2 checkpoint、1 个 `ready` delivery、1 个标准答案、1 个原 external dispatch/result/use intent；checkpoint 的 `search_binding=external-context-use-v1_1`。导出/session 共 16 个文件未检出私有思考 marker。只留状态计数、源 SHA、canonical source ID，不留答案正文。

原外部 context binding 明确拒绝 question packs，因此本轮实际搜索正例限制 singleton。没有实现 agent 自主多轮搜索，也没有以 search_exposure 空值声称执行了搜索。真实公司/API/准确性验收由总控另行执行并记录。

独立 reviewer 在最终合成原库清理前以 `mode=ro` 核对上述正式状态计数、16 个文件的无思考 marker 结果，且 DB 前后 SHA 相同，见 `../engine-review/actual-software-independent-db.json`。随后已精确清理本任务的旧长路径 runtime/pytest tmp 及 `C:/Temp/iqs-eng25-v679d1cb` 短根，保留所有现存 XML/薄元数据/本报告；`cleanup.json` 记录范围与无活动进程检查，未碰生产数据库或其他进程目录。

## 早期失败记录的留存边界

核对后当前 6 份 XML 全部是通过记录。早期 `os.link` 权限失败、长路径 `native_persistence_uncertain`、短根 fixture 80 秒等待失败，没有各自独立保留的原始 XML/trace；后两次使用的 `native-actual-finalization.xml` 已被最终 passed 必要 case 覆盖。该最终 XML **仅证明最后一次通过**，不能当旧失败日志。早期失败目前只有本报告的具体诊断摘要及当时工具执行输出，没有补造原始日志；`actual-source-observation-before-final-mirror.json` 只证明中间源快照差异，也不是失败测试回执。

## 最终必要 case 命令

在自有短 runtime 的 `qa` 目录执行，原 public owner 的硬链接发布需要在已授权沙箱外运行。所有外部 HTTP 都由测试脚本 wire 替换，未访问收费 API。

```powershell
$taskRoot = 'C:/Temp/iqs-eng25-v679d1cb'
$env:TEMP = "$taskRoot/temp"
$env:TMP = "$taskRoot/temp"
$env:PYTHONPATH = "$taskRoot/qa;$taskRoot/sw"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:IQS_C06_RUN_INTEGRATION = '1'
$env:IQS_C06_OWN = $taskRoot
$env:IQS_C06_COMPOSITION_CODE_ROOT = 'C:/Users/郑曾波/Projects/invest-quick-scan'
$env:IQS_C06_COMPANY_ROOT = 'C:/Users/郑曾波/Projects/iqs-company-agent-lab'
$env:IQS_C06_BRIDGE_ROOT = 'C:/Users/郑曾波/Projects/iqs-agent-runtime-lab'
python -B -X utf8 -m pytest -q C:/Users/郑曾波/Projects/invest-quick-scan/tests/test_company_scan_native_e2e.py -k explicit_finalization --basetemp C:/Temp/iqs-eng25-v679d1cb/t2 -p no:cacheprovider --tb=short -o faulthandler_timeout=240 --junitxml=C:/Users/郑曾波/Projects/invest-quick-scan/runs/reconcile-production-2026-10-25/engine-fix/native-actual-finalization.xml
```
