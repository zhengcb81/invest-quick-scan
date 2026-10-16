# Desk 独立最终复审：passed

精确绑定23文件CAS rawSHA `8611c3a55ef498830f99c55e886c532c50763f927499a940b719d035d166b6ee`，before对originals/、after对最后冻结候选和自有desk3/副本全部匹配，签收时再核候选after未变；actual after逐文件见desk-result.json/desk3-cas-check.json。审查者未实现或修改候选。

实际独立重跑最后完整组229 passed / 0 fail / 1 skipped，唯一文件symlink权限跳过；真实junction、T0/T1、公开CLI/serve、真实Chromium1280/390交互、恶意文本、外联阻断、再生入口全部执行。desk-harness3/independent-full.json有真实命令/UTC/退出码/stdout-stderr原SHA。另独立重放自有12反例全部通过：6全锁、3未知协议、3一致重封结构错误；没有用作者通过日志代替本次执行，也不把重复测试数相加。

DESK-F01与F02均关闭。新core_validation完整源码和server调用已审读：manifest/view直接复用packaged闭合schema；details自有wrapper必填与闭合类型复用view定义，并核row_order/rows/sessions/events镜像及每行slot/session绑定。Opaque原答案/题面/审查载体保持typed object与诊断语义，未把原非法答案升级正确。整组额外22容器/嵌套/索引反例也实际运行。未知协议走版本拒绝，合法协议但结构坏走输入拒绝。

来源锁来源commit/null理由、UTC、未登记consumer与Windows source/destination路径统一检查通过。固定144 registered /108 supplied /19 legal /125 missing、匿名aggregate与行级unreviewed、费用unknown、comparison accuracy/winner=null的原有语义在真实集成与浏览器继续保留。

如实保留一项环境偶发限制：作者首结构全组在build_bundle临时os.rename遇到WinError5，发生于load_bundle前，teardown后无staging/完整output。作者未取得当时OS handle trace，外部句柄、扫描器或race均不能证明或排除；本次独立全绿不把未确认根因说成已关闭。事件原字节windows-publish-incident.json已保留。该失败为可见失败并清理输出，没有证据表明它绕过本轮校验；仍作为环境偶发限制披露。

全部397冻结输入最终rawSHA与清理/进程/端口记录在shared证据；保留最小反例、实际日志、截图/请求捕获，移除自有重复测试副本。工程候选签收不授予production/financial/rating-gold资格。此前两轮needs_revision和RED历史保留如下，当前结论由本轮闭环取代。

# Desk 独立最终复审（首轮，待同闭环修复）

第二轮更新：22文件CAS rawSHA `a7ad3e2d4f6eb78facab8714388f33244b9179154bf5b30764bda7360515dc32`，before/after均匹配。独立完整204P/1S（仅文件symlink权限），含浏览器/CLI/再生。但增强同组12反例为9P/3F：6种锁错误与3个未知core协议均已拒绝，DESK-F02关闭；DESK-F01结构仍未闭合。view.rows错误类型、manifest.registrations错误类型、details缺rows在所有hash/ref一致重封后仍被load_bundle接纳。见desk-harness2/independent-core-probes.*，最小组desk2/tests/test_final_independent.py。作者正在同F01补完整schema/结构入口，未签收。此更新不新增节点或产品范围。

结论 needs_revision。独立于原作者和1.0.1修复作者，不修改候选，测试全部在自有desk/副本。17CAS的before对originals/、after对冻结候选逐字节一致，expected_head匹配snapshot；raw文件范围desk-files.json。全部397冻结输入实核保持，发布锁6b8d7e88df3cbc4aa9fb92bf7a181d4bee67f9bc098a59fa1bedd1e4591ce591保持。

实际重跑完整单元/真实T0-T1/CLI/loopback/Chromium/窄屏/再生：167 passed / 1 skipped（仅文件symlink系统权限）。desk-harness/independent-full.json含argv/cwd/UTC/exit/日志rawSHA。读取卡、共用契约、接口、CAS、报告、原23项RED清单、最终日志；审读服务器/输入锁/公开API/bundle/manifest和carrier/view/UI的全部修复diff，以及相关回归和再生测试。实际查看本轮1280x900与390x844截图，正文未知/分母/合法≠正确标识可见，无整页横溢出，交互断言由真实浏览器测试完成。

DESK-F01：server.load_bundle未检查manifest/view/details的protocol。三个反例分别将其protocol改为iqs.unknown/9.9.9，重封内容hash、全部文件rawSHA/bytes与跨文档refs保持一致，入口仍接受。违反未知载体版本拒绝及严格serve语义；并非hash篡改而是漏协议边界。应共享固定core协议/结构校验，不靠UI晚报错。

DESK-F02：load_lock/_check_relposix的全共享锁结构仍漏六种原契约约束。invalid commit、null commit无理由、prepared_at非UTC+08、consumers含未登记package、source_path为AUX.json或folder./x.json均被derive_view_and_details接受。反例只改自有synthetic锁/manifest并重封，对真实397输入无写入。应统一全锁来源/日期/Windows路径检查。

9项集中RED见desk-harness/independent-core-probes.{json,stdout.txt,stderr.txt}，最小测试desk/tests/test_final_independent.py。已发总控安排原作者同闭环修复，不另立节点。新CAS冻结后再核、跑9反例和受影响整组，关闭所有有效发现才passed。

已验证原修复涉及的合法答案分母、匿名aggregate不擅自逐行、review冲突、当前修订一致、subject全键、company/security筛选、GET/HEAD与405、启动后资产篡改拒绝、安全文本、生成入口；完整suite真实通过并不覆盖上述新增协议/锁反例。没有搜索、模型请求、收费API、T4/private/DB读取或生产接入。financial_qualification/production_ready/rating_gold均不授予。
