# 已验收查看器接入真实只读主体资料

2026-10-15。三个公司agent包仍在用户派发的独立Lab施工，约定handoff目录尚未见正式handoff.json。总控避开其writer，利用等待接口交付的期间推进不重叠的UI接线；不重做三策略、SDK、参考集或盲评桥。

## 真实读取与页面

在真实Alphabet owner namespace调用原 `QueryReader.get_profiles` 与 `IqsQueryContract`，得到1个实际主体，query2.0返回 coverage_gap：12字段未覆盖、0观察、0分数。原生owner/principal/周界沿既有实际库，未复制合成身份或导入测试答案；本次读取不创建持久capture，也不写任何owner库。

将原request/response和实际校验元数据封入原VIEW的 `owner_export_unqualified` bundle，复用原组件、服务器及只读API，未另造HTTP服务或SQLite读取器。bundle完整性、来源读取和金融资格仍分开；它不具有白名单/比较/正式facts资格。页面原保守banner保留，未因原件hash自洽升级信任。

真实Chromium检查了Alphabet详情、缺口页和390像素窄屏：12缺口显示，分数控件0、观察0、外网请求0、页面异常0；POST写入口405，服务器关闭并释放。截图与原件在本机 `runs/view-owner-integration-2026-10-15-01/`，没有将真实owner数据库、完整导出或密钥推送到远端。

这只是当前query2.0资料到既有组件的实际接通，不等于生产UI/完整query2.6/全股票池/多模型历史已交付。当前没有答案，不能展示准确率或伪造分数；股票池入口没有自动生成大名单。原组件的演示标题、技术字段展示和未核验提示仍需在正式生产接线时统一，不拿本次页面检查关闭UI全门。

## 实际发现与直接修复

VIEW原适配器只汇总pool查询的字段缺口，遗漏get_profiles原生覆盖信息。修复后按原查询范围显示缺口，保留原status/reason/field，不创建任何题目答案或观察。多主体查询的aggregate缺口保持query级别，不武断分配给每家公司。

兼容旧样例里题号与field不一致的字符串：保留原值并标注“不是本次请求字段”，不改成正常field或当成答案。坏类型拒收；错误owner、未来wire依旧不提取。未知/不合法request字段列表不会因字符串子串等逻辑被当作已匹配。

改动3文件：`src/iqs_viewer_lab/adapter.py`、新增 `tests/unit/test_profile_coverage.py`、`tests/unit/test_wire_validation.py`。后者移除recovery用例混入的另一种坏coverage输入；整数列表的拒绝另有显式回归，原recovery异常仍必须显示而不崩溃。

## 集中验证与源码交付

从VIEW源HEAD `cfdfd705cb66859a3d2f123bae6ac0a7954795c9` 冻结105文件/1299544字节；先跑新边界RED（4失败/2通过），再修复。最终精确候选单元+集成 **158项：157通过/1 Windows符号链接权限skip、0失败/错误**；最终真实owner浏览器检查另1项通过。旧24项synthetic浏览器回归本轮未重跑，不混进本轮分母。

最终suite PID18168/exit0，33.72秒；真实浏览器PID28432/exit0，3.21秒（页面计量2.61秒）。计量不是模型速度。所有测试无密钥、限制loopback；owner读取进程PID25016/exit0、2.49秒且禁网/SQLite query_only。临时目录在本轮独占根，结束后清理；实际导出、截图、源快照、失败/成功日志及JUnit保留。

中间失败不隐藏：测试launcher路径拼接TypeError及pytest默认日志路径被隔离guard拒绝，均是工具准备错误；旧语义过严导致第一整组82F/10E，改为保留越界字符串诊断；下一组153P/1F/1skip，单一失败源于recovery夹具同时塞坏coverage，现已拆开测试。首次沙箱内浏览器启动180秒超时，根因未确定；父进程终态后核原PID，已不在匹配进程中，未终止任何外部进程。沙箱外仍无密钥/仅loopback、使用有界launcher成功，不把启动超时或后续成功当金融结论。

源交付前核HEAD、全部105个原文件SHA及空暂存区；精确写回3文件。默认Git whitespace对保留的CRLF误报，保留原默认空白规则，仅命令级增加cr-at-eol识别；不改全局配置或跳hook。正常本地提交 **`8ceb0d4b548e1455cdf0bf447cd9317b91b072c2`**（codex/view-01），源码与最终候选原字节相同，其余原文件未变。该Lab无remote，未猜测远端或推送。

## 本机复看

已提交VIEW源码可读取保留导出；浏览器服务不会重新扫描、调用模型或刷新数据库：

```powershell
$env:PYTHONPATH='C:/Users/郑曾波/Projects/iqs-viewer-lab/src'
C:/Miniconda/python.exe -B -X utf8 -m iqs_viewer_lab serve --bundle C:/Users/郑曾波/Projects/invest-quick-scan/runs/view-owner-integration-2026-10-15-01/native-export-01/bundle.json --host 127.0.0.1 --port 0
```

它输出本机随机端口。当前导出没有pool页，实际主体key在 `/api/meta` 的subjects内；详情使用原 `#/detail?subject=<URL编码的subject_key>`。这个限制保留为生产启动/导航接线待办，不冒称已达到一键方便查看全池。

主线继续等三包真实交付后集中集成，再沿已准备owner方案办理真实admission、运行首家公司S1并核源。G3/F05/金融准确性/正式facts/生产UI/一键/全池仍开放。
