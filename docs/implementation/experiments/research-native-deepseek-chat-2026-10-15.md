# 原生受控派发对 DeepSeek Chat 的兼容修复

日期：2026-10-15。StockQA 已正常提交并推送 `ee1f8c7896c98722e345161a6108499869a24ef3`；原基线 `41763bf1e933578f4cc214b354680950b973fdf5`。仅改传输校验、一个新测试文件、原研究传输说明共3文件，其余232个冻结文件 raw SHA 保持。本轮模型HTTP、搜索、公司文档下载均为0。

## 实际问题与修复

已完成 S0 的 ResearchChatSession 发送 `deepseek_chat_completions`，携带 `thinking.type=enabled` 与 `max_tokens`。原生 comparison v3/v4 校验却只识别 MiMo Chat、Anthropic 和 DeepSeek Responses。合法 DeepSeek Chat 在建立发送 attempt 前便被拒绝为 `controlled_generation_protocol_unverified`。S0 的预算路径没有受控工作绑定，因此 S0 通过不能排除此集成问题。

新增这个精确 provider/protocol 分支，解析其原生思考与 token 字段；畸形 thinking/type 保持拒绝。原 owner guard、模型/provider、cohort、获批目标路由及 policy、pack 上限和严格 bool/int 检查保留。没有改授权、预算、任务协议、实际SDK或供应商调用方式。

## 集中验证与提交

- 自有根 `runs/research-native-protocol-2026-10-15-01/`，先冻结234文件，核对原外包输入锁一致；测试环境去密钥、禁网、外部文件写拒绝，SQLite 仅本轮自有临时根及内存库可写。
- 实际 RED2：PID17240，exit1，3F/12P。pack cap1/3/12的合法请求全部因不识别协议失败。更早 RED 因缺少真实IQS合同依赖而整模块 skip，不计产品反例或通过。
- 首次修复 GREEN：PID2916，79P/0F/0skip。正常源提交 hook 随后发现 dict.get 参数类型问题并统一换行，未跳过。
- 显式检查 thinking.type 为字符串，增加 list/missing type 反例。最终 PID25016，exit0，**81P/0F/0skip，110.17秒进程墙钟**；覆盖新测试、原 controlled-generation、comparison target、ResearchChatSession、controlled-refresh 五个文件。原日志、JUnit与PID收据均保留，不将两次测试分母相加。
- 最后正常 hooks 的格式变化与受测 Python AST 完全相同、文档文本相同；交付候选同步实际源字节，三文件最终完全一致。Black/isort/mypy/secret及其余正常 hooks 全通过后提交。首次和第二次 hook 失败原件保留；第二次仅格式调整，不新增功能修复。
- 沙箱内 Black 双/单worker无输出；只结束核实属于本轮的两个精确PID，沙箱外按 StockQA 原配置检查2文件成功。未杀其他进程或改全局工具配置。

新测试使用实际临时原生 store、owner决议和控制投影 API，但授权明确为合成 fixture；检查前后DB字节一致、新工作 attempt 为空。它验证发送前校验，不证明真人批准、真实金融答案或完整收费 RuntimePort。

## 保持与清理

245项 raw SHA 核对保持，包括真实 owner追加快照后的10文件、旧work账本、新S1空预算、他人2026-10-10 README和其余232源文件。旧13HTTP/26搜索/CNY1.268162、4 checkpoint、新S1零计数未改变。确认本轮Python进程结束后，仅清理自有temp/cache：133文件、115,552,727 bytes，剩余0；源冻结、候选、失败/成功日志、XML、提交及保持收据保留。

## 下步接续

外包三包仍用原 `inputs.lock.json` 的41763bf字节，不改锁、不要求工人追最新。最终总控集成真实发送时使用本次ee1f8c7修复，按公开协议兼容接入。

EVAL正式handoff已出现，但20:03UTC只读观察中：handoff声明f219bc6、artifact声明09a2ca6，实际HEAD48dc6c4且51个tracked路径仍变动。它是**已出现交接、尚未冻结签收**，不是“未交接”，也不能据旧79P宣称最新验收；继续避开其writer。RUN尚无约定handoff。用户已明确批准EVAL CodeGraph，初始化完成708files/15,847nodes/15,139edges；原Company Lab亦已按批准初始化115files/2,208nodes/2,093edges。

接收稳定RUN/EVAL交付后集中完成真实owner_public/RuntimePort、Run1.1盲评及参考资格范围绑定，先一家公司S1三策略各两次。不得重跑S0、把此81P当答案准确率或关闭Financial/G3/F05/生产UI/全池门；新实际owner确认与admission尚未产生。
