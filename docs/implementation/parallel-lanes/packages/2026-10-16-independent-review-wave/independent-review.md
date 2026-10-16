# 必须执行的独立整包审查

这是用户新增的硬要求。实施agent完成payload及单元/集成/公开CLI E2E后，实际调用另一个独立agent做**一次整包全面检查**。审查agent不能是同一agent改名；应使用fresh/no-history上下文，获得施工卡、共同规范、输入锁、最终payload commit、全部源码/schema/数据、实际测试与清理证据。可复现测试和检查临时环境，但只写本Lab自己的review工作区，不改实现或任何上游。审查结论不是金融真值认证。

审查至少覆盖：需求是否完整；公共API/CLI/schema/版本及失败行为；原文/期间/单位/来源与上下文是否保留；反例是否独立于实现、预期是否合理；注入故障是否真的发生、未发/已发未知是否分清；是否复用原依赖而非另造状态机/账本；只读/禁网/secret/进程/路径/清理；输入锁、实际日志、artifact hash与payload是否吻合；文档能否让下一harness独立复现。CONTEXT另外查裁剪丢义/虚报缓存；REVIEW另外查事实vs推断、主观评分无唯一gold及金融口径；CHAOS另外查发送次数、未知预约、不重发和假恢复。

发现**各种有效问题都要修复**，不限严重级别。实施者在本根修复，保留问题ID、根因、修改与测试证据；独立agent再核最终payload，直到全部有效问题关闭并明确passed。误报可以由独立agent有理由撤回，不能实施者单方面降级为“可接受风险”。上游/权限外问题修不了就blocked，不得绕规则或交completed。缺独立agent能力、关键测试未跑或报告仍有open finding都不能交接完成。

本包只保留一个整包审查节点。复审属于同一闭环，重跑受影响测试即可；不要每个函数/小提交设审查门，也不要无限追加与任务无关的检查。

正式交接必须有：

- `review/invocation-evidence.json`：implementer_agent_id、reviewer_agent_id、harness名称、真实调用时间/工具返回标识、可核对的调用记录位置/摘要及raw hash。仅写“已review”不算证据；不要保存隐藏思考/密钥或整份私有聊天。
- `review/round-01.md`及后续实际轮次：审查范围、检查命令、具体发现、定位和结论，不能只有模板勾选。
- `review/fixes.json`：每个finding的修复commit/测试/复核结果；无发现时为空数组并说明真正完成了哪些检查。
- `review/final.json`：package_id、status=`passed`、两个不同agent ID、reviewed_payload_commit、input_lock_raw_sha256、实际round文件列表及hash、检查范围、open_findings=[]、closed/retracted findings、真实完成UTC。

上述记录由实际工作生成，不得自己编造agent身份或伪造调用证据。final必须绑定最终实现；独审后再改源码/数据/schema/行为性文档，则先跑受影响检查并由独立agent确认新payload，旧final不能冒用。交接报告链接这些文件，artifacts.json纳入它们，总控可据此复核，但不新建每一步回执审批。
