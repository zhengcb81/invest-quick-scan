# VIEW-01 R2：验收后直接修复并签收软件范围

**已签收本包G2—G5软件修复，真实owner/生产接线仍pending。** 原交付有缺口，用户明确要求“如果验收还不通过你就直接修复吧，不要再给整改施工卡了”；总控已在隔离候选修复、回归并精确写回VIEW Lab，没有追加整改卡。G1和比較已绿部分保留。

## 原交付与问题

仓 `C:/Users/郑曾波/Projects/iqs-viewer-lab`、branch codex/view-01、无remote。实际接收HEAD `ec62e13a3c2eb1cedbeb9d281455e3a99a7f83a2`，原产品f26a60bf88d9d3da64d59fb187ef1c547a6cdc5c、交接9ccd376d9c78ca52656e2592e0ac971b02ccd159。214跟踪/18冻结输入匹配，原完整suite PID32336/exit0、96.63秒：158项157P/1skip（unit115/integration20/真实Chromium23）。

本轮原artifacts.json缺失；原R1清单被183项改写为211项，README/git-baseline仍155而JUnit158。20既有公开CLI控制与追加4控制、实际页面/API验证确认：caps1.1非法true会授合成关系formal资格；同key不同完整ref/实际owner冲突仍拼接；完整范围API404而key API200；不同operation页合成150行（虽诚实incomplete）；分组后同snapshot第二组无法准确选、池同key身份覆盖、合法字符串None与null游标碰撞。原坏形状/请求ID/快照错配/断链不完整改善保留，未把它们回炉。

## 已直接修复

- capabilities1.1消费原契约facts_producer_ready=false，非法true稳定拒收。未来owner wire继续unsupported，不造正式facts或比较资格。
- actual owner冲突保留原报文/冲突说明、不提取。缺owner的池行用明确viewer-only unverified-owner命名空间隔离，保留query也不能加入已核owner族；不冒称真实owner ID。
- 池索引与profile连接都检查完整subject_ref，身份/范围冲突拒收。同owner/query/operation/universe合并分页与比较水位；null和不透明"None"游标区分。
- Lab view_key/selector_key贯通meta、pool API snapshot_key和真实UI选择器；同snapshot两范围分别可选，旧唯一snapshot兼容，歧义明确提示，不静默取首组。owner snapshot/cursor原值不改。
- 完整perimeter范围API与key API结果一致；adapter只消费已核raw缓存，无重复磁盘读取越过预算。
- 生成器要求显式remediation目录且刷新须--overwrite，排除动态设施/依赖/缓存；原R1清单精确恢复，本轮清单真实生成。最终计数与字段映射同步，历史158/130/124及原日志不覆盖。

## 实际验证与发布

新增10项初始RED（PID80192），范围三项后续RED保留；13定向GREEN，最后完整回归 **173项172P/1 Windows symlink权限skip，0失败/错误**（unit128/integration21/真实Chromium24），PID24348/exit0、63.39秒。新增真实浏览器选择器分别返回100/50行，完整owner snapshot不变；正常详情API两入口一致。原G1/比较演示、键盘/真实Back/390布局均保留。

原查询隔离正例仅改raw store、未同步expected owner，实际是owner冲突；已改成真正同owner的不同query正例，独立坏owner反例仍保留。一次保护器误把候选API子进程指旧源码的9P/1F日志保留，修正路径后真实候选验证；不冒充产品RED。中间回归真实失败也保留，不声称所有尝试都绿。

源代码10文件正常精确提交 **`cd7bf1a6545c2b51f65ac6b02d10c90e77cdcb50`**；交接20文件正常提交 **`cfdfd705cb66859a3d2f123bae6ac0a7954795c9`**，即最终HEAD。226跟踪、223清单工件bytes/raw SHA全匹配；源状态仍只有既有`.codegraph/`，无remote所以未造push。候选运行源码与写回源码raw SHA一致。

公开handoff CLI最终PID76564/exit0，只验shape/声明范围，不授金融或owner资格。最终Lab交接位于 `docs/handoff/VIEW-01/remediation-02/`，最终JUnit `logs/junit-coordinator-final.xml`、coordinator-receipt/git-baseline/明确interfaces及实际artifacts均可查。Git检查保留默认空白规则，仅识别Windows CRLF；真实RED stdout的四处原始尾空白按原字节保留，不改日志，正常hooks未禁用。

## 隔离与边界

自有 `C:/Users/郑曾波/Projects/invest-quick-scan/runs/view-r2-acceptance-2026-10-11-01/` 保留原冻结source、候选代码、必要截图trace、小反例和原PID/stdout/stderr/JUnit。首次清理3346文件303目录；修复后再清15259文件1100目录，逐文件核绝对范围/ID/硬链接闭合集合/raw SHA。自有命令行匹配的Python/Node/Chrome进程0，六个明确端口释放；不清源个人设施/浏览器安装/B01/其他writer。清理后的TEMP有后续CLI空目录重建，不存测试下载物。

模型/收费搜索/下载公司文档/生产DB/名单写0，测试父子去key，浏览器路由拦外网、仅owned loopback。唯一外仓源码写为用户授权VIEW修复。原报文/锁/schema保持，旧R1清单恢复SHA `557ef3af957adad5f39a5b96fd1e991f2578ec395918d03e9ba9ed5e6c3ef900`。

[独立审查](VIEW-01-R2-independent-review.md)、[源仓交付记录](VIEW-01-coordinator-repair.md)。此签收关闭VIEW软件余项；正式StockWiki供数、真实owner E2E、金融准确性、生产UI/一键/全池仍按主线计划推进。
