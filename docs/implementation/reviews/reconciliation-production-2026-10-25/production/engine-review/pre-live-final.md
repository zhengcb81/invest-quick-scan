# 最终真实小样本实验前独立审查

审查人：`/root/fix_bank21`。结论：**可以启动本次有边界的 cold 实验**，未关闭发现为 0。机器可读结论见 `pre-live-final.json`，本审查没有调用模型或搜索 API，也没有读取密钥或修改原始数据库。

- 已逐一重算 **32 个**锁定文件的实际 SHA，全部匹配，无重复；最终 preflight 与同一份 source-pins SHA 一致且模型/搜索 HTTP 均为 0。
- 最终 driver SHA：`f6607fb2afd6f3e5a4beec0759d7ef3baaf723bf7a152095b711b4e8fa717dbc`。
- source-pins 文件 SHA：`39d92b881a890b99758ae8b7a4fcf7c8069fda1b5225911f461b6b6d26c5c80b`。
- 原 manifest 文件 SHA、独立重算的 canonical 内容 SHA、identity 文件 SHA 分别与 owner authority 的对应字段匹配；search plan 使用文件 SHA，driver 从原 owner authority 独立取值并提前核对。
- 已用原函数重新投影基础 model budget + search policy，结果与获准 composite budget 逐项相等；模型路由、总费用/请求上限、并发和 policy_id 未改变。原 rate-card resolver 可识别给定价格引用。
- thinking 在真实 SDK 发包前强制检查开启；恢复阶段删除 API 环境变量并禁止网络，要求原 crash proof 的 source-pins SHA 未变，核对完整预算、搜索操作和 native response 行摘要；两次 finalization 都必须实际封包为 ready/delivered。
- 原软件 E2E XML 为 **1 项通过、0 失败/错误/跳过**，648.869 秒。审查人另以 `mode=ro` 打开真实合成 executor SQLite，独立确认 scored 1、schema 2 检查点 1、ready delivery 1、原检索 dispatch/result/use 各 1；数据库前后 SHA 不变，16 个导出/会话文件未发现私有 thinking 标记。

本结论仅适用于**宁德时代 / IQS_05 / 截止日 2026-10-18 / MiMo mimo-v2.6-pro 开启 thinking + DeepSeek Search**的隔离实验。可以开始付费冷启动，不代表真实 cold/recover 已验收。后续仍须审查真实证据；ready 只是本地封包完成，金融正确性、StockWiki ACK、全池扫描和多题批包生产均未由本结论授予。
