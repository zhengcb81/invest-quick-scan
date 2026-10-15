# 查看器启动与企业快照导航

2026-10-15。已具备查看既有导出的简易启动入口。此步骤不表示生产扫描、query2.6、完整股票池或金融评分验收完成。

## 使用

在 IQS 目录运行，无需配置 PYTHONPATH：

```powershell
python -B -X utf8 scripts/view_quick_scan.py --bundle "已有导出/bundle.json" --open
```

`--open` 可选；不传就只打印本机 URL。默认同级 `iqs-viewer-lab`，不同位置用 `--viewer-root`；默认随机端口，可显式 `--port`。首行 JSON 保留 URL/PID/bundle hash；Ctrl+C 结束服务。浏览器启动失败只提示手动打开 URL，服务继续。

复看已保留的真实 Alphabet 导出：

```powershell
python -B -X utf8 scripts/view_quick_scan.py --bundle runs/view-owner-integration-2026-10-15-01/native-export-01/bundle.json --open
```

它是先前真实 owner 读取的不可变导出，不会重新读 owner、刷新名单、调用 LLM 或付费搜索。当前该导出只有 1 主体/12 缺口/0 观察；页面不会填造分数。服务在测试后已关闭，用户运行命令才会启动。

## 行为

复用既有 VIEW bundle 加载器、组件和 HTTP 服务；IQS 新脚本只定位该包并转交原 `serve` 命令，没有第二套 server、SQLite 读取器或 API 客户端。VIEW 原 CLI 新增 `--open`，协议仍为 1.0.0，package 0.2.0。

顶栏“已载入企业”使用完整 subject_key，保留 store/snapshot/revision/perimeter 作用域，不按名称、ticker 或最后一次 sid 合并。选项仅来自本次导出，不冒充完整股票池；同一主体的不同快照保留不同选项。只有 profiles、没有 pool 页时，空根网址默认进入已载入企业详情；显式 URL 不被自动替换。错误企业/快照明确提示未载入，用户可以从顶栏重新选择。profile-only 页面不再引导至不存在的股票池。

真实受控延迟复现了旧异步问题：选择第二个企业后，前一个企业响应迟到会覆盖详情。现在页面代次控制所有异步结果及错误；切换主体立即清除旧内容，迟到结果丢弃，不串公司。数据及评分规则保持原样。

## 证据

冻结 VIEW 源 `8ceb0d4b548e1455cdf0bf447cd9317b91b072c2` 的 227 文件，在自有副本中开发；发布前再核 HEAD、干净工作树和全部原文件 SHA，精确交付 9 文件。其余 220 个原文件不变，源码与最终候选原字节匹配。正常本地提交 **`847bcbe03d5d92124629aa962ebd8d99a0e6f95d`**（codex/view-01）；该 Lab 无 remote，未推送或制造远端。

| 验证范围 | 实际结果 |
|---|---|
| VIEW 单元/集成（含真实监听、浏览器失败仍可访问、默认不打开、释放端口） | 163 项：162P/1 Windows 符号链接权限 skip；PID16052/exit0 |
| 全部既有浏览器回归 + 新导航/迟到响应反例 | 26P；PID14052/exit0 |
| IQS 薄入口（缺源拒绝、默认同级目录、显式覆盖目录、无用户 PYTHONPATH、退出释放端口） | 3P；PID29416/exit0；默认路径实际读取已提交 VIEW 源 |
| 真实 Alphabet 导出的公开薄入口 + Chromium | 1P；PID2052/exit0，0 外网/0 页面异常，12 缺口/0 分数、390 宽度、错误身份拒收后可选回、POST405、端口释放 |

全部测试无项目密钥；仅允许 loopback，SQLite query_only，写入限制在本轮自有目录。真实页面使用原 owner 导出，没有合成公司替代身份；另行的 26 项明确为合成软件回归，不是金融准确率。

失败历史保留：沙箱内已有 serve 用例 socket10013 是环境失败，未当产品 RED；缺 `--open` 有独立未实现反例。首轮旧 E2E 23P/1F 的 Failed-to-fetch 根因未定，保留原日志并加 requestfailed 诊断；修复迟到响应后的完整 26P 不等于专门证明该网络故障已治愈。导航测试准备阶段曾误用 Playwright 参数、重叠 route 回调及测试派发分支；这些不是产品反例。修正后 red3 才实证迟到响应覆盖。真实 owner 初次测试错误地期待 HTTP 错误，实际前端先拒收无效键；最终验证采用明确产品预期，不弱化“不回退其他企业”。

视觉检查桌面与 390px 截图：企业选择与缺口均可使用，没有页面横向溢出。原保守 trust banner、技术元数据及写操作禁用仍保留；最终面向完整股票池的生产文案/供数仍待主线，不将当前只读导出升级为已核验结果。

## 清理与接续

自有临时目录及独占 profile 清除 **4,001 文件/30,067,467 bytes，剩余 0**；截图、trace、失败/成功原日志、JUnit、原件与候选保留在 `runs/view-launch-2026-10-15-01/`。240 个保持性核对通过，包含 VIEW 原件、owner 10 文件、原 B01 账本、新 S1 空预算与他人 README。无收费调用、公司文档下载或名单/生产库写入。

RUN/EVAL 约定 handoff 仍未出现，继续保留外包写边界。主线继续接真实执行桥/盲评和 REF 的显式资格，再进行首家公司 S1。启动导航属于独立产品进展，不增加新的逐 helper 审查门，不代替 G3/F05 或准确性实验。
