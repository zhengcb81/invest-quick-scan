# S2 IQS 供应商传输失败诊断

从正式远端 `master@05f95a249eebd591ede74f552dd62db58c1b0e1d` 接续，隔离分支 `codex/s2-iqs-provider`。此合并已包含原 F4 与跨 ID 回跳。本次只改 `scripts/iqs_scan/providers/provider_transport.py`、定向测试和本记录。原 cross-id 工作区、D00、作业执行、收费、回告实现及安装副本保留。

## 根因和原契约

真实 `post_json` 会返回上游错误正文或 URI/系统异常正文。模型和搜索调用方只使用 HTTP 状态和已有错误标记，未能从 F4 冷读传输故障的类型及原位置。现在沿原传输返回形状保留 HTTP 状态、超时与通用失败标记，把异常类型、帧和已知 errno 从现有 foundation 公开入口写入原 F4。HTTPError 关闭响应，原错误正文字节留在上游边界。

同一已关联运行与尝试内，相同稳定错误分类复用原发生记录。不同 HTTP 状态、超时、I/O 和坏响应的分类分别可查。纯诊断没有已验证的业务结算，原 `reconcile` 继续返回 `cost_unknown`、`job_status=unconfirmed`，本次冷读的新增模型、搜索、费用均为零。

## 定向验证

- 基线用真实传输入口加离线 `urllib.request.urlopen` 替身得到 6 红、1 个正常成功绿。反例覆盖 HTTP 文本及 JSON 错误正文、URI I/O errno、超时、坏 JSON、同一运行尝试分类。正常模型结果继续保留原已知 token 数。
- 用独立进程执行 `scripts/iqs_feedback_owner.py --runs-root RUN get-diagnostic REF` 两次并执行绑定原观察的 `reconcile`，核对状态和原定位。验证调用计数不变，出箱与 CLI 无合成正文、URL 或密钥。
- 定向套件为 `tests/test_iqs_provider_transport_diagnostics.py`、`tests/test_thin_scan_search.py`、`tests/test_runtime_feedback_boundaries.py`。常规 AppContainer 长临时路径让既有 workbench 三个编码样例命中 Windows 文件名限制。改用候选内独占短临时目录复验，结束后清理，现有 workbench 保持原样。
- 最终短根组合 36 项通过，用时 16.36 秒。ROOT 核对两个冻结摘要并复跑本轮 7 个用例，全部通过。独审确认成功回执原样、同类诊断聚合、原作业支付未知、新用量零。未请求真实网络服务。发布前只读核对远端 master 与上述基线一致。
