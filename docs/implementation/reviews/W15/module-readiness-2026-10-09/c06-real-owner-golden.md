# C06 真实 owner 身份与查询 golden

2026-10-10。当前为私有候选软件与真实现有身份记录的交叉验证，未发布生产源，未关闭完整 C06。

四份现有 StockWiki 身份库从 `a5a97d6efbf5f0ee79122a1ec375def388700690` 对应工作区只读复制，源和克隆逐份字节一致；明确拒有 WAL/shm/journal 的不稳定文件。来源见 `intake/W15/c06-query-2026-10-09/real-owner-inputs-01.json`。当前唯一 analysis subject 从真实主档读取，没有按名称猜选发行人，没有创建主体、verified receipt、观察或财务回答。跨文件仅是顺序读取及前后字节校验，不冒充跨库原子快照。

StockWiki 的实际身份导出 parser/handler 经薄公开入口 `stockwiki.identity_g2b_cli` 复用，避免总CLI在身份导出前加载无关LLM配置。旧总CLI保留；首轮失败终态与原日志保留。实际 owner binding 使用既有 `stockwiki.quick_scan_routes_cli quick-scan-route-binding`；新能力入口公开其配置下的独立 store_id，用来验证实际查询结果，不能从查询结果本身抄期望 owner。

生成及校验顺序如下，具体绝对路径、参数、时间、PID和原始输出SHA都记录在 `real-owner-golden-02/generation.json` 的6条 command，不把脚本模板当已执行命令：

```text
python -m stockwiki.identity_g2b_cli --root <owned-clone> identity-export-g2b --entity-id <实际primary issuer> --as-of <实际UTC>
python <IQS>/scripts/identity_contract_cli.py --input <identity-export.stdout.json> --schema-version 2.2.0
python -m stockwiki.quick_scan_routes_cli --root <owned-clone> quick-scan-route-binding --subject-key <实际subject key> --iqs-code-root <IQS>
python -m stockwiki.quick_scan_query_v2_cli --root <owned-clone> --iqs-code-root <IQS> --capabilities
python -m stockwiki.quick_scan_query_v2_cli --root <owned-clone> --iqs-code-root <IQS> --request <query-request.json>
python <IQS>/scripts/query_contract_cli.py --operation response --input <query-validation-input.json>
```

身份 package2.2.0 经 IQS CLI1.1.0 返回 valid。Query2.0.0 经公开纯CLI返回 validated，但实际 result.status 是 **unavailable**：源没有 observation namespace，scores_available/facts_available 都为 false。正确身份可以展示，评分与事实不能展示成有效结果；没有借初始化空库、合成答案或重写旧记录制造“真实正例”。这不证明金融准确性、模型横向比较、当前白名单资格或200家公司扫描完成。

`real-owner-negatives-01/checks-final.json` 收齐14条真实 CLI终态：1次跨进程重启保持原捕获，13个拒绝反例覆盖错发行人、挂牌ticker/来源绑定冲突、截断/重复JSON键、错主体revision/范围摘要、独立owner/水位错配、模型筛选改变、未知snapshot以及过期缓存禁止live替换。主体/水位错误的副本重新封摘要后仍被拒绝，不只测试旧hash。原实际 golden 不变。模型项只验证 cache query绑定，源没有真实模型答案，不能宣称已比较模型回答。过期项是自有缓存元数据故障注入；finally恢复原缓存字节，不声称等待两小时。

负例控制器在13条已完成后调用不存在的序列化helper失败，恢复缓存后只补尚未执行的过期项，未重跑已绿13条。原错误与终态原件保留。所有源DB/克隆原四库字节保持，0API、0费用、0公司文档采集。当前 c15a/real-owner-01仍服务同一C06大节点，收尾后按原隔离清理协议清除，不删除外仓数据。

下一步继续原C06剩余公开操作和明确授权的刷新预览/确认链，之后同一大节点集中审查与源发布。当前capabilities只声明 get_profiles，full_C06_milestone_accepted/facts_producer_ready 都为 false；TH/IN、G3/F05/L03/B01和全池门仍按原前置。Git跨仓快照导出的具体授权问题还未获答，旧34份publisher已过时，不盲跑。


## 2026-10-10 接续补记

刷新预览新增实施没有改写任何真实golden/四库/原capture。当前真实正例仍仅身份与真实缺覆盖；不能借25项合成预览测试或8项账本测试变成真实回答正例。本文已获明确文档发布授权，不包含真实golden原件/数据库。
