# B01：厂商请求身份兼容候选，尚未部署

本次推进同一个 B01 工程节点。真实首轮证明：厂商 HTTP header 的 request ID 可以缺失，即使模型返回了合法的“证据不足”答案；旧协议因此阻止封存。解决办法是增加具名的 `vendor-http-identity-v1` 执行协议，而不是填造 ID 或修改历史结果。

截至 checkpoint31，仅 IQS 导出/校验及 StockQA 冻结上下文的版本选择在隔离副本中完成。真实回执装配、事前主体登记、完整封存/入库、查询及执行检查尚未完成；没有部署候选，没有新付费调用，不能宣称整条链通过或答案准确。

## 版本与兼容约束

- 新 Observation `1.2.0` 单独存放，旧 `1.1.0` schema、回答 schema、指标与归档模块保持原字节。
- `execution.request_id` 必须有键；真实非空 header 或明确 `null`，不得使用 completion ID、UUID 或逻辑 work ID 补造。
- `response_id`、真实 physical attempt、request payload/response/receipt SHA 分开保留。格式符合不等于执行已验证，真实原件验证是后续步骤。
- 新导出必须显式选择 `1.2.0`；旧默认 `1.1.0` 的输出保持一致。authority/context 的既有外形不变，新的实例明确绑定新的 Observation schema SHA。
- IQS 注册同时锁旧基础资源与新 schema 摘要；文件变动、重复键及非有限 JSON 拒绝。StockQA 使用逐字一致的新 schema，显式 metadata 版本与整个上下文的 schema SHA 同时核验，混合版本及未来版本拒绝。
- 旧四个 blocked 检查点不能套用新 authority/context；本方案不追认过去的事前登记，也不救回原件后伪称新的有效链。

## 测试证据及范围

原始 PID、时间、退出码、stdout/stderr SHA 都在本机 `runs/b01-engineering-2026-10-11-01/logs`，全部失败保留。下列结果分别属于独立批次，不相加为金融准确率或一次全绿。

| 批次 | 实际结果 | 解释 |
|---|---|---|
| profile-red | 7 setup errors | guard 未识别 Windows 扩展路径，未到产品断言 |
| profile-red-actual，PID33860 | 顶层5F/2P；pytest含子测试为7failed/2passed/15subtests passed | 修环境后，新版本参数与发布校验确实不支持，有效 RED |
| profile-green，PID45296 | 40P/2F，41子测试通过 | 新协议测试通过；两项原兼容测试因 sandbox hardlink 权限及缺原 fixture 失败 |
| profile-affected-env，PID76044 | 2P | 仅补原 fixture、使用所需执行权限后复测上述两项；产品断言未放宽 |
| qa-context-profile-red，PID42096 | 2F/7P | 新 IQS 导出被原 StockQA 拒绝，有效 RED |
| qa-context-profile-green，PID58684 | 64P | 9项新增版本/哈希互操作测试及55项原上下文回归 |
| profile-affected-strict，PID34936 | 10P，27子测试通过 | 仅复测新协议受影响项：缺键/错类型、注册资源漂移、重复键、溢出数字及历史兼容 |

合成身份和回答只用于软件测试；没有真实公司金融 oracle、模型回答质量或生产 owner 正例。没有新增小节点审查；完整跨仓软件候选完成后做一次集中审查。

## 冻结与当前留档

自有工程根为 `runs/b01-engineering-2026-10-11-01`。初始冻结 IQS255、StockQA197、StockWiki360 个已跟踪文本文件，源 HEAD 分别 `6ce86d3`、`0a0493e`、`2d0f1db`；未复制真实库、密钥、vendor 正文或思考文本。`examples/profile.json` 和 `main_questions.json` 是后来显式补入的原兼容 fixture，不计入初始255。候选共9个产品/测试路径，另有上述两份 fixture；实际清单、源字节保护与日志 SHA 见自有 `attestations/checkpoint31.json`。

读取外仓 Git 状态时曾遇到 sandbox 权限限制，首次两次 checkpoint 控制器均在落盘和写 PWF 之前终止；随后使用只读外仓所需权限核验。第三次被 VIEW 动态 dirty 状态的旧 clean 断言拦下，也未写 checkpoint/PWF；改为记录当前实际状态、保护原 writer，并未放宽产品规则。活动工程副本继续保留，不清除原 c16b/live/owner/预算库。

VIEW 用户授权的 CodeGraph 已存在且健康，本次只读确认23文件/431节点/当前1119边，不重复 init。源 HEAD 仍 `dff4105`，当前已有16项未提交改动，保留原 writer 的动态状态，不套用上次 clean 快照。此前 init 日志的408边是当时统计，不改历史证据。VIEW/FIN/OPS 仍需各自原 R1 整改。

## 同一节点的下一步

1. 从原 `QuickScanWorkStore.get_attempt_response` 读取经过现有原件校验的 receipt，核 checkpoint 的 physical attempt、模型、真实 header/response、时间与三摘要；payload SHA 从 receipt/pack journal 取，不能由模型或新 metadata 补造。
2. 贯通具名事前登记 `subject_dispatch_request1.2`、binding1.1、StockWiki 原生导入和 query2.6/capabilities1.2/inspection。旧公开协议字节保持，未知 profile 必须明确拒绝；新查询不能把未支持的行静默丢弃。
3. 同节点补已知响应但无有效答案的耐久逻辑终态、真实 owner retry/comparison 决议和 CNY refresh 与旧 USD 兼容；原已结算预算不清零。
4. 完整隔离软件正反例与一次集中审查后，重核各源 writer/HEAD/文件摘要，才做精确源码部署和正常提交。StockQA 新 JSON 需要精确忽略例外；不提交当前 private runs 或他人 README。
5. 最后走原公开 owner preview、授权 operator 的真实 TTY 确认、admission 和原 main，三题固定 IQS_01/02/04，先 max32768 的 pack3，再相同上限 pack1。原完整30题、13 HTTP、26搜索、CNY1.268162、4不足证据、0评分及ACK0基线不重放、不修改；金融/G3/F05/facts/UI/一键/全池继续开放。
