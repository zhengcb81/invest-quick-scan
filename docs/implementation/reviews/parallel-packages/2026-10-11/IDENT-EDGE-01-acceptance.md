# IDENT-EDGE-01 包级接收结论（2026-10-11）

结论：**changes_requested，保留有效候选成果，按一份 R1 集中整改**。本包的六类身份边界方向可复用，但目前“可读候选资料”还存在实际来源、时期和输入绑定错误，不能仅凭 43 个测试通过签收整个交付。

唯一源仓 `C:/Users/郑曾波/Projects/iqs-identity-case-lab`；接收实际 HEAD 为 `3a2a26b8f6ade8cebf1e2deb60f5410ca0d567b0`，分支 `codex/ident-edge-01`。summary 所述产品 commit 为 `f8c5fee9af912d4a27a4eac18f6815408136cc9d`；handoff.json 所述 result_commit 为 `0152ed786728a692e59fa47354e41d337b01a835`，review.snapshot_commit 为 `640db9c81acfecdc62540623b8bea1fdf5d649a3`。需要按真实产品/交接/审查快照角色说明，不能混称同一提交。

详细独立内容审查和短来源核对见 [independent-review.md](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/intake/parallel-acceptance-2026-10-11/ident-edge/independent-review.md)。实际命令/退出码、锁和清理见 [result-final.json](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/intake/parallel-acceptance-2026-10-11/ident-edge/result-final.json)，受控字节见 [source-freeze.json](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/intake/parallel-acceptance-2026-10-11/ident-edge/source-freeze.json)，清单文件 raw SHA `86d0197e9e41c8437544ad1777a18ac6407f28f10a79f95237588e67f9a700c8`。独立内容审查结束，67 个冻结源文件 bytes/raw SHA 仍完全匹配。

## 已经完成且应保留的部分

- 总控公开 baseline validate exit 0，15 个输入锁源/冻结字节匹配，公开 handoff schema 校验通过。
- 原包相关回归最终 **43 passed**，实际 PID `44196`、终态 exit `0`；前置 controller/隔离配置失败保留原日志，不混算产品失败或通过分母。
- 六类候选边界区分 issuer/security/listing/集团关系；固定 `candidate_artifact_only / not_mapped / not_run`。历史 owner golden 保持只读，未签发正式身份或扫描资格。
- 原离线 guard SHA `abc0128dc92a2bf99e57dbbbfe2355aea376b584f67e9e51c0bd0ebbc871e682`；模型/搜索收费 API 为 `0`，没有将密钥环境传给测试，没有公司文档下载或生产库/名单写入。
- 总控自有 `runs/ia01` 已按实际清理回执移除，源仓保留；独立内容审查未新建 run 或重复测试。

## 四类同包整改

| 类别 | 实际证据与影响 | 必需整改 |
| --- | --- | --- |
| IE-01 主体、locator 和短事实引用闭合 | alias 的 `FACT-MISSING` 被 locator 自己“定义”，公开 validate 实际 PID `73148`/exit `0`，应 exit `4`。原 00999 合成控制借 8039 退市事实自报 source_checked；Alphabet cross-reference 借 SMIC fact 支撑名称。 | 对实际短事实记录、保存字节及主体/locator/字段/时期支持范围闭合；合成控制不能借真实不相关出处自签。证据不足保留 partial/unknown，不冒充 owner。 |
| IE-02 事件类别与有效期 | 早于 valid_from 的 active 公开反例实际 PID `11792`/exit `0`，应 exit `4`。8039 停牌日冒充挂牌起点；Citi 两种公司行动的日期配错；89988 柜台起点沿用香港上市日无对应支持。 | 检查每个具体时点与正确挂牌的 `[valid_from,valid_to)`；区分挂牌存续、停牌交易状态、公告日和生效日；未知日期不填。保留香港取消上市 09:00 的来源精度政策。 |
| IE-03 严格 JSON | 根 schema_version 先 9.9.9 再 1.0.0，实际 PID `28716`/exit `0`，应 exit `2`；普通 json.loads 静默取后值。 | 共用文件入口拒根与嵌套重复键、超界 JSON；未来版本拒绝，不靠覆盖后合法值放行。 |
| IE-04 资料包与交接绑定 | candidate 缺共同 pack_id、inputs_lock_sha256、source_refs、limitations；artifacts 多项缺 bytes/完整 raw SHA，collection-plan 仅 SHA 前16位；实际提交角色不一致。 | 按共同规则做内容寻址、明确锁/来源/限制绑定；归档旧版本原字节；最终 PWF 完成后生成完整逐文件清单并解释产品/交接 HEAD。 |

I06 的判断须准确：原 Quant Memo 页确有 Apple CUSIP、ISIN、Nasdaq AAPL，**不是编号伪造**；当前问题是保存短事实只记通用原则、secondary 来源不能充当官方核实，且 control 把 partial 材料升为 source_checked/无需解决。AMEC/SMIC 指定页本轮不可读，SSE 指定页本轮只有模板，这些只能记录复核 partial，不能据此断言原来源为假。详细可支持与不能支持的范围和具体 URL 均在独立报告中，不在公文复制网页正文。

`source-status-upgrade` 反例先因 foreign/未闭合引用 exit 4 被遮挡，**不作为资格升级机制的有效鉴别证据**。43P、公开 baseline 成功与三条错误放行分别陈述，不将“命令成功”当作全部 case expectations_met。

下一步只交 [IDENT-EDGE-01-R1.md](C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/reviews/parallel-packages/2026-10-11/IDENT-EDGE-01-R1.md) 给唯一 Lab writer；稳定候选后集中一次针对这四类的正常控制/反例及独立复核，不重新做六类预研、不增加小节点 gate。本次不关闭 StockWiki 身份、G2b/C06/G3/O01、真实 owner DTO、金融准确性或全池门。
