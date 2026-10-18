# 原账本下的 owner 批次续行：只读根因设计

状态：只读设计完成，待总控决定下一大节点TDD实施；仅本目录设计文件可写，不实现、不访问密钥、不发 API、不修改原库或 PWF。总控拥有主计划。

确认的现状：原 `quick_scan_work_store._reserve_budget_attempt_tx` 全局检查 unreconciled；旧 `quick_scan_uncertain_seal.continuation_exclusion` 是独立研究机制，不能用于绑定 work 的 owner 请求。HTTP 200 缺 usage 的 response_unpriced 不能冒充 unknown HTTP，也不能填零费用。

设计结论：旧S1原work为空，旧两请求范围不能映射，不猜disjoint。第一阶段原固定owner配置/公开原生control在refresh preview前安装精确repeat-exposure decision；第二阶段新quote据其重算，原TTY/明确委托确认精确新cohort，取得原ApprovedRefreshSession。保留两旧行费用NULL、预约0.2USD、请求100和原累计上限；不重发旧intent。原native同题未决work仍按原守卫拒绝。不是依靠尚不存在的ready preview自举授权。

文件：

- `design.md`：精确根因、两阶段原权威、协议/配置/源路径、守恒公式、范围边界、一次大节点TDD与真实旧账只读backup迁移验收。
- `real-baseline-readonly.json`：原schema20/100请求/2未决/原work零行；原库SHA79ae…85e检查前后相同。
- `source-bindings.json`：本次只读调查的原源码精确字节与当前提交，用于实现前复核漂移，不作为授权凭证。

未执行迁移、测试、付费调用或任何源仓/真实数据库写入；没有生成新的外包卡，也没有重复审批门。原生能力/规范版本均为设计提案，不能当交付。下一步由总控在原native能力节点先写失败反例，再实现与整节点独审。
