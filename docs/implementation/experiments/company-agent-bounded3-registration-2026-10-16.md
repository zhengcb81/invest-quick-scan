# Alphabet 隔离研究 T1：bounded3/具体反馈处理组

登记于2026-10-16，首次T1请求前。用户已明确选择先隔离研究后生产owner，并已将三张独立工具卡发给其他harness；本线不改其Lab，不重复紧凑codec/新评测适配/缓存分析候选。

## 固定条件及比较范围

沿T0同一Alphabet真实主体、2026-10-13 cutoff、实际routed12（含OPERATING_01）、原题原锚点、10公开facts/6来源。问题、证据、答案schema、指标表逐字节复制T0，原数据SHA不变。无检索调用；不能评价Brave/Tavily/ZAI或宣称生产联网研究完成。所有模型调用使用StockQA原ResearchChatSession及现有S1预算/路由/发送登记，思考开启，DeepSeek flash，隐藏思考不留存；不写正式评分/owner/名单，不冒充ResearchRun1.1。

六会话：fixed3/free_agent/evidence_agent各2重复；repeat1正序，repeat2逆序。每会话8 SDK step、每次max16384输出token（含思考）、会话输入240000/输出48000/900秒，客户端单HTTP超时180秒；本次最多48实际HTTP。SDK调用数和真实HTTP数分别留档。没有自动重发或跨模型切换；未对账/未计价/并发残留停止后续会话。新输出根必须独占创建。

**处理组同时改变四项，不能归因于单一变量**：整个响应最多3题；反馈给具体安全schema字段/业务错误码；公开证据已在上下文所以取消重复read_evidence工具；静态规则/schema/模块前置、公司范围/证据后置。free仍自己选择当前剩余题，evidence按原依赖组，fixed按原3题序列，free/evidence预算内一次全局自查。最终标准答案schema、验证和原子提交保持。

新载体显式 `iqs.isolated-company-research/1.1.0`，config1.1；不能将T0当成同处理组重复。新增公开草稿留存，只有原Company漏检规则通过且大小有界时才保存，拒绝隐藏思考；不通过只留hash。T0丢失的早期失败正文不补造。1.1 revision额外保留原生attempt/model/completed_at，原答案正文不注入工程字段。

## 预算、定价与停止

复用 `company-agent-s1-20261015` 现有144请求/USD14.40预算，**累计已用21次/USD0.100300**，预留/并发/未对账均0。T1发送前再次从原接口读核，不重新初始化或修改上限；每次USD0.10预留，最多2并发的原策略不变（本轮顺序会话）。T1的单独消耗用本轮原生前后值及每attempt回执核对。

官方价以 `https://api-docs.deepseek.com/quick_start/pricing/` 2026-10-16核查为准，USD/百万token：缓存0.003/0.006、非缓存0.15/0.30、输出含思考0.60/1.20（谷/峰）。现金账单未知。T1预计在当日06:00–10:00 UTC高峰完成，逐次实际发送前建立原价格resolver窗口，HTTP若跨费率窗口仍保持未知并暂停，不猜官方边界规则。这是修复上一版整个会话绑定窗口的保守估算范围，不改变原预算对账协议。

## 质量与结论

沿已冻结company-agent-accuracy-rules-2026-10-16.md：72目标槽不丢，合法结构/语义覆盖/事实正确性/合理拒答分别计；金融盲评前accuracy和winner必须null。新增草稿可复核不等于质量已通过。公开客观参考仅核十个独立主标量，不把复合父记录或评分全部升级为gold。准确性优先，然后比较真实费用/时间/cache；总控后续以独立盲评及跨模型/检索实验形成手册，不凭本轮单公司宣布通用最优。

运行根 `runs/company-agent-isolated-2026-10-16-02/`，冻结config/源Python及schema清单/原题证据/规则/驱动原始字节和hash。预检默认禁网；live显式开启，仅api.deepseek.com DNS/443，写入只准本轮根和现有预算SQLite精确路径。启动时不把API key写入配置/日志，不下载财报或全文HTML，临时文件结束清理，保留真实失败、pid/时间、预算前后与原始公开回执。
