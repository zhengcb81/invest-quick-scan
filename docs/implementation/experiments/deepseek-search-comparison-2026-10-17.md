# DeepSeek Search/Fetch与四源小样本对照

状态：真实搜索已启动，工程边界修复中；尚未完成固定模型回答及四源比较，不预设赢家。

首阶段实际17条搜索发送，16条原生账本settled，官网参考成本CNY0.55。首条DeepSeek Search约1.715秒，参考CNY0.005。第17条CSC Brave q2响应抵达后因短记录URL校验不一致无法落账；CNY1预约保持，原进程已停止，不重发该槽、不伪造HTTP状态或费用。模型HTTP仍0，ZAI MCP尚未发送。细节和逐请求状态在本机`runs/deepseek-search-compare-2026-10-17/live-status.json`。下述36槽设计保持原分母；早期SDK/配置/账本不改写。

用户确认ZAI为GLM Coding Plan，主要使用MCP。新显式prepaid组件分别登记工具额度、现金未知和保留现金预约；不得把credits写成CNY或现金0。初步证据已见官方URL对应访问限制提示、查询跨期间及混入其他公司，进一步说明URL命中和数字命中不能代替引用支持审查。

用户授权2026-10-17：接入StockQA，使用环境DEEPSEEK_API_KEY做真实小样本，与Brave/Tavily/ZAI比较；准确性第一，费用与速度其次；更新PWF、搜索规范，交付互不重叠外包卡，最终独立agent审查修复后交接。

## 固定设计

复用已有宁德时代300750、Alphabet、CSC Financial06066三个公司样本，不新增股票池成员。每司两道精确事实题与一道证据内ROIC−WACC拒答控制；合计9题。宁德时代/Alphabet参考官方HTML本轮只读重核，CSC使用2026-10-07已审HKEX参考，明确未新下载PDF，不冒称今日重核。provisional身份保持provisional，不借研究派发授生产身份资格。

每司3条查询、每源count=5，四源逐字相同，查询不含参考数值。36次冷搜索、12个公司/来源证据板；臂间不共享证据，不用失败路由的对手结果补齐该臂。实际返回数、错误、非空率、截断和发表日期缺失分别记录。固定一款deepseek-flash开启思考、无原生搜索，按同一三题包/答案schema生成12次；参考值与人工标签绝不进入模型context。

Fetch是独立增量组，所有搜索臂都可使用相同DeepSeek Fetch：只选本臂已落账搜索返回的最多两个唯一HTTPS HTML链接；禁止PDF/附件/私网/带凭据URL，不为凑样本改查询。只保留有界必要片段、元数据和hash，原网页/Markdown仅内存处理，不下载财报或存整页。Search-only与Search+common-Fetch分开报告；同一URL被多个臂命中时可按明确缓存契约复用，但分别列冷/暖增量，不伪造本次HTTP。

主指标为全部24个已知数值槽中，被证据完整支持且主体/期间/币种/单位/会计定义正确的回答数。另列已答准确率、覆盖率、错误确定回答和12个证据依赖控制的审慎拒答。ROIC-WACC控制不是断言世界上不存在数据；若本次证据真的充分，按实际证据判断。参考数字相同但所引来源缺表头/口径，不算完整支持。独审保留争议，不用多数票或模型自评代替来源核验。失败/未启动保留原分母，零可评不是零准确率。

费用分为接口请求、套餐credits、公布费率参考与实际现金；未读控制台账单，现金未知不填零。计入失败、协议握手/发现、重试、Fetch、模型tokens（含思考）和等待时间。冷/暖缓存分开，缓存命中仅用真实usage，不由输入相似推定。DeepSeek模型官方映射今天已更新为DeepSeek-V4.1-Flash-1017，旧实验不回写新费率。

## 登记与稳健性

真实请求仅用StockQA原ExternalSearchProvider、单次HTTPpermit、Q09预算和journal；不在IQS另造客户端或账本。新增独立source研究工作与注册不重放T4旧任务；旧owner只读核98笔已结算USD0.655435、两笔未知各USD0.1预约，总上界USD0.855435保持，并计入累计预算检查。CNY/美元换算仅为冻结参考：ECB2026-10-16 EURUSD1.1253/EURCNY7.5240；保守预算8CNY/USD不当成交价或实际扣费。

未知发送/未计价保留预约、不盲重发；明确可重试失败才新登记有界退避，不覆盖原attempt。DeepSeek账号Search/Fetch各5QPS，独立类别与目标域名限制如实实现/注明作用域。ZAI REST/MCP协议不同；真实当前余额未知，无法计价或准入时记录阻断，不能设置免费以绕闸。

## 原件与交付

本机登记根：runs/deepseek-search-compare-2026-10-17/，preregistration.json、questions.json、reference-private.json与pricing-snapshot.json分离；后续actual runner/source输入另锁hash，不改已冻结旧实验。暂定搜索策略新1.2显式启用Search/Fetch，旧1.0/1.1 schema与行为保持。原StockQA起点21cf8b05b0a388af08425d685c079451bc3012dd，tracked clean；候选只在自有隔离根修复，未写源。

三张互不相交施工卡入口：[搜索来源波次](../parallel-lanes/packages/2026-10-17-search-source-wave/README.md)。不自动派发、不创建其Lab，不写活动REVIEW-CAL/RESUME仓。只设本轮整包独审：检查接入、真实证据/计量/实验分母、规范与施工卡完整度，修复全部有效发现再签收；不新增逐helper审批。

官方依据：[Search/Fetch](https://api-docs.deepseek.com/zh-cn/guides/search/)、[模型费率](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)、[Brave](https://brave.com/search/api/)、[Tavily](https://docs.tavily.com/documentation/api-credits)、[ZAI Coding Plan](https://docs.z.ai/devpack/overview)、[ECB参考汇率](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html)。本页方法不是实测完成证明。
