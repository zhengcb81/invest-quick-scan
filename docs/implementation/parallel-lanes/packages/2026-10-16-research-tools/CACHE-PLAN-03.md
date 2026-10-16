# CACHE-PLAN-03：真实计量复算与缓存规划

唯一可写根：`C:/Users/郑曾波/Projects/iqs-cache-planner-lab`。先读共同规范/输入锁。读 trial、iqs、evaluation、rules、pricing；不依赖 CODEC/JUDGE 的新交付。不写/连接原生预算或生产 SQLite，不调用模型/搜索，不读取key，不实现新的模型SDK/发送调度器。

## 要交付什么

做一个离线诊断工具：准确复算已发生请求的token/价格/耗时，分析前缀共享的理论上界，提出下一轮可证伪的实验矩阵。**不要把离线字符串公共前缀长度当真实缓存命中，也不要把模拟价格当实际账单**。现有T0的缓存很高但交卷很少；研究要解释费用花在哪里，而不是预设缓存越高方案越好。

包名 `iqs_cache_planner`，公开接口：

```python
def measure(runs: list, *, rate_card: dict) -> dict: ...
def analyze_prefixes(prefixes: list, *, scenarios: list) -> dict: ...
def propose_experiments(measurements: dict, *, constraints: dict) -> dict: ...
```

新载体分别 `iqs.research-metering-analysis/1.0.0`、`iqs.prefix-scenario-analysis/1.0.0`、`iqs.cache-experiment-proposals/1.0.0`。CLI `python -m iqs_cache_planner measure|prefixes|propose`，显式输入/新输出目录，关闭式schema、样例及可复算命令。所有run适配遵循实际1.0/1.1，protocol/usage未知不猜。

## 计量规则

- native_receipts 由 attempt_id 去重；相同ID完全一致可去重，相同ID内容冲突拒绝。不把events与result中同次receipt重复计费。result无usage的协议拒绝HTTP200仍可能耗费，先看receipt。SDK调用数另列；未知send不能当无请求。
- **两种 usage 不能混算**：原生receipt.usage 的 input_tokens 是非缓存输入、cached_input_tokens 是缓存输入；usage_observations 的 prompt_tokens 是总输入。按已锁协议显式分支，验证和是否一致。reasoning_output_tokens是 output_tokens 的子集，不能再相加；没有reasoning明细就是unknown，不是0。
- 费用用 Decimal/整数micros，不用float累积。给 rate-card本地schema，价格/币种/每百万token/缓存类/有效UTC窗口/source URL/核查日期显式记录；复用冻结价格模块中已定义的单位与窗口语义。无官方结算边界规则时，跨峰谷HTTP费用保持unknown并展示上下界，不能用完成时间猜。保留原native estimate原值及复算差值，不能修改原账。
- 固定 historical rate-card可复算T0；不需要上网追今天价格，本包不做收费调用。峰谷/假期规则只接受显式带出处日历配置，缺假期证据不得假定；测试可用标明synthetic日历。`rate_card`缺少币种/单位/来源时拒绝给精确价格。
- 输出现金invoice/null、native估算、复算公开价估算、预留/未对账、计量覆盖率分别列。不能把native累计budget余额减法当单会话账单。
- 墙钟区间/会话耗时/各HTTP耗时分开，跨并发不能简单把会话和叫总时长。未知区间/耗时保留，拒绝负数和反序。真实冷/热状态未知，不能用 repeat1 标冷。

T0校准锚：21真实HTTP、25 SDK调用、总输入451880、缓存416768、output含思考156285、reasoning77260，原生公开价估算USD0.100300，sessionwall总747.387165699969秒。**这些值来自一次真实试验，复算要从六result/events推导，不从measurements.json直接复制；汇总仅用于交叉检查。** 逐请求计价舍入与汇总后舍入会有差别，解释差值。金融准确性/winner=null；4合法答案不能给出金融“每正确题成本”。可列每合法答案成本但明确结构指标。

## 前缀与规划规则

`prefixes` 输入每项显式 id、UTF-8 text、scope（global/module/company/session）、information_cutoff、evidence_sha、question_sha、tokenizer_ref或null。只读输入字符串，分析最长公共**字节**前缀与分组；不声称等于provider缓存块/token。UTF-8中文边界不能截坏。可提供实际可用tokenizer的显式可选插件；没有时仅报告bytes/chars，不能字符数换token。

对比全局schema→模块→公司证据→动态指令的层级顺序；证据变化/题库版本变化应局部失效。**不能为了跨公司缓存将A公司的证据留给B公司**，也不能复用过期cutoff的证据或跨模型/provider计缓存。只提出静态执行顺序/并发场景，不发请求、不操作锁或预算。

输出observed / deterministic_bytes / simulated_bounds三种依据分开；缓存TTL/最小块/路由节点不明则写未知和敏感性，不编默认实测。价格、时间、质量目标分开；先质量的候选策略不能因预测速度而放宽证据。`propose_experiments`给有限小矩阵，明确模型/搜索/问题/证据/提示版本、重复顺序、token cap、预算区间、停止条件和需要总控实测的字段，不能自行建立新批准。

## 测试与交接

1. 单元RED：重复收据/冲突ID、receipt与observation输入口径混淆、reasoning双计、unknown0化、峰谷交界、舍入、币种不同、失联send、并发墙钟和中文前缀边界。
2. 集成从六真实结果复算上述锚，详细差异可解释；注入合成崩溃/缺usage/缓存字段不全时保持unknown和总分母。原文件SHA必须保持。
3. 前缀模拟：三家公司/两个模块/单条证据升级/模型切换/过期cutoff，不能跨主体偷复用；没有tokenizer也能正常只报字节。
4. E2E实际公开CLI输出JSON+简明Markdown诊断；已有输出目录/路径逃逸/坏JSON非零且不部分覆盖。禁网与外根写保护、finally清理。整包集中一次验证。
5. 交 `docs/handoff/CACHE-PLAN-03/`，用对应模板和共同规范；报告真实锚复算、成本构成、可执行实验建议及不可推出的结论。不要把离线模拟报告写成模型真实准确率/成本优胜。
