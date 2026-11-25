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

## S5 复查 2026-11-25

从正式 `master@3a078328e594775b15d1fabc9a47a485c1c9bd01` 起步。原工作区 `codex/cross-id-dashboard-return-20261121@50fe2b1` 与其三份未提交 PWF 属并行线，保持原状。

- 用实际传输入口复现两个漏接异常。非法地址在发送前抛 `ValueError`，模拟已返回但正文不完整时抛 `IncompleteRead`。两者现在都返回现有传输失败形状。经 F4 冷读可见原异常类型，网络地址、凭据及正文未进入日志。正文读取失败的原付费结论仍由原作业决定。
- 模拟一次真实 thin scan 内两题各发生同一种故障。已继承关联号时原实现四次尝试只落一条。每题现有自己的稳定发生记录，同题的重复尝试合并。共同根因仍归到同一个 issue。直接启动时生成一组运行与尝试关联号，已有宿主关联号时原样使用。
- 明确请求 StockWiki 活体验真却少参数时，公开 CLI 给出所缺协议选项。只有完全未要求现场验真时才走现有冻结样本回放。Owner 返回空 stdout 时保留公开错误码或有效 traceback 的异常类型，忽略原始正文、文件路径和续行。原来成功结果及正反黄金样本继续验证。
- `stockwiki.quick_scan_freshness` 的 `freshness_status` 和 `ttl_valid_until` 均是 StockWiki `dd5b033` 显式公开导出。现有 IQS 兼容比较可以通过该已配置接口完成。直接使用两个已发布接口，无需将邻仓根加入路径或按固定发布版本拒绝。用 `8527bc7` 与 `dd5b033` Git 对象交叉核对 IQS 使用的五个 freshness 组合和三个 TTL 值，结果一致。新增两个独立进程用例覆盖有无版本声明两种兼容形态，更新比较结果的调用来源名称。
- 首次运行五条反例全部失败，修复后定向运行 52 项通过。补测真实子进程的 traceback 先复现一条漏报。最终七个回归文件 92 项通过，包含基础架构边界、搜索截止期及模型搜索兼容。已有契约和这批新增反例纳入首个轻量 `quality` 工作流。没有供应商调用、下载、付费或 StockWiki 原工作区写入。

F4 原运行引用 `.worktrees/f4-runtime@aa847ac` 早于本次修复与现行公开验真。ROOT 接收并发布后可从新进程冷读既有运行的同一发生引用，再切换代码绑定。原诊断文件和业务作业保持原样。本记录只对应本仓隔离候选。
