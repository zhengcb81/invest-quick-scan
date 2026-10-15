# 真实 owner 历史快照已入库，首家公司范围已准备

日期2026-10-15。本轮沿现有 StockWiki 和 StockQA 公共 API 推进真实准入，不改三个施工中的 Lab，也不新增源仓代码。

## 实际结果

- `QuickScanRouteStore.record_snapshot` 将[新截止日候选](company-agent-route13-candidate-2026-10-15.md)的原始 route/manifest 字节追加到真实 owner 历史库，状态 recorded；回读字节完全一致。它保留真实主体和周界绑定，不是复制 fixture 或合成 golden。
- **没有调用 set_current。** 当前仍是原旧路由、anchor_version=1，current_history 完全一致。旧 policy 原字节及另外9个原owner文件未改，旧B01账本和新S1预算未改。
- 新policy候选的12个实际field、DeepSeek flash、原principal和真实成员关系均已核对；`refresh_contract.validate_policy` 和原查询合同通过。候选没有安装，也不是 owner grant。
- `inspect_refresh` 对新独立S1账本真实只读检查通过：work_items为空，reservation_created=false，API_requests=0，共享剩余上限144 HTTP / USD14.40。此值是阶段预算上限，不是首家公司预计价格、模型账单或可绕过会话限额的授权。
- 首家公司执行配置已形成：fixed3/free_agent/evidence_agent各2次，6会话×12逻辑槽=72槽，最多48 HTTP，计入原S1 144次。每会话8次/900秒、输入240000、输出含思考48000、单次输出含思考16384，S1搜索0；思考开启且仅存私有内存。第二重复反向运行三策略，不宣称供应商冷缓存。

真实短证据、参考资格、RuntimePort/owner服务、各策略cohort/generation和新admission尚未装配，执行配置中对应引用为null、live_enabled=false。预注册、原targets及worker冻结输入不变。不在依赖未齐时提前创建只有一小时寿命的capture，也不编造snapshot_id或原生终端确认。

## 本机交付及原件

目录：`runs/company-agent-owner-2026-10-15-01/owner-stage-01/`。

| 文件 | 用途 |
|---|---|
| owner-policy.candidate.json | 12个实际field/DeepSeek及原Q13预算绑定，未安装 |
| qa-inspect-request.json、qa-inspection.json | 原生只读报价请求与回执 |
| profile-query.candidate.json | 通过原合同的实际主体/field查询，snapshot_id=null，不能直接充当刷新申请 |
| first-company.execution-plan.json | 六会话/72槽/48请求与原阶段144上限、缺少的准入引用 |
| transition-plan.json | 当前真实前置、CAS切换和恢复语义；未执行切换 |
| transition-before.json、owner-files-after.json | 写入前后原件SHA和当前anchor历史 |
| backup/scan.sqlite | 追加前原库精确原字节备份，仅供事故恢复，不能覆盖新历史来“回滚授权” |
| snapshot-record-result.json、summary.json | 真实recorded结果及未执行事项 |

真实写入进程PID29824/exit0，7.83秒；无密钥、禁网，SQLite只允许原scan.sqlite写入，其他连接query_only。原生route校验子进程也沿相同限制。唯一原库变化为追加新快照，未手工SQL改状态。原scan.sqlite SHA由 `5f308ea36539993aae064c498eba52366214d2934b096c54079e967236b288e7` 变为 `0b48e0201660d9fec4b525220ff77328110fb5f27994ca1464ca8b9c8303eff4`；前者精确备份保留。之前报告“原10文件不变”是写入前历史，此后应以owner-files-after作为新读核基线，不重跑一次性stage脚本。

准备配置程序仅调用原合同，未读取密钥或创建网络请求；不能把它表述为已经运行三策略。没有新增逐helper审查或重跑S0；原成功/失败和费用均保留。

## 切换时必须保留的语义

原namespace只有一份生效policy，current anchor按版本递增。后续在完整运行桥和实际cohort/策略绑定准备好后，重新核原件/主体/principal/成员，通过原set_current的独立旧anchor CAS显式激活新路由，再显式安装新policy、捕获实际query结果、原生preview/真人终端确认及QA admission。

返回旧路由必须保留递增版本和切换历史。**还原旧policy字节、甚至将当前route设回旧ID，都不会恢复原anchor_version=1的旧确认。** 恢复旧25项时仍需原生重新预览/确认；不能重置版本、回写旧确认或用整个备份覆盖新历史来复活权限。现在仅record、未activate，所以这一权限变化尚未发生。

三包交付后做一次完整链路集中集成与审查，再运行首家公司S1配对对照并独立核源。当前金融准确性/G3/F05/生产UI/一键/全池均未关闭，真实公司请求仍为0。
