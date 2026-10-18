# 三个独立研究包验收报告（2026-10-18）

## 验收范围

核对 PROMPT-TRUST-09、LOCALE-ROBUSTNESS-09、TAXONOMY-CROSSWALK-09 的正式交接、离线测试/数据、独立审查和最终元数据。总控按用户授权直接修复交接问题。没有调用真实模型/搜索 API、没有下载文件、没有写入 StockQA、StockWiki、生产数据库或股票名单。

本报告是 IQS 外部控制器记录：它把每个 Lab 的最终交接提交和关键文件 SHA-256 绑定起来，避免 Lab 的交接 JSON 试图引用包含它自身的 Git commit。

## 结果

| 包 | 最终 Lab HEAD | 独立审查与离线证据 | 验收边界 |
|---|---|---|---|
| PROMPT-TRUST-09 | e37755f78a29315ca97ba95367bbd00340c3211d | review_prompt_trust09 对 round-7 元数据闭环 PASS；34 项离线测试为既有交付记录 | 真实模型抗注入实验因无 dispatch lock 未运行；指标 not_assessed |
| LOCALE-ROBUSTNESS-09 | 9389f276b2b1244dde26beda3682fbac0023cc41 | review_locale09 对最终 Lab HEAD 元数据复核 PASS；95 passed、1 warning 的离线全套测试；59 项 inventory 和 104 项 payload 全部通过 hash 核对 | 真实双语模型对照因 dispatch lock 和已批准 gold/reference 缺失而未运行；指标 not_assessed |
| TAXONOMY-CROSSWALK-09 | 8a96153ac88d49c2ff5a66ed59263620e8b430b8 | review_taxonomy09 round-5 对 release 1.0.2 的 173/173 行复核 PASS；96 项隔离离线测试通过；最终 handoff metadata 复核无待整改 | 只接受为离线分类候选；dispatch lock 缺失，禁止将其作为生产公司映射/路由或主题分类 |

### PROMPT-TRUST-09

正式 metadata review 绑定 HEAD e37755f78a29315ca97ba95367bbd00340c3211d。Final SHA-256：a687b425a8f33d1f0b178364c3c8091aab74b5524a7b7cdfd0c8db8fe6a08c55；inventory SHA-256：e6504d13d3ffd38a99078ac869c2e2266dba995752e4ea7f5dc26be41e742c92；round-7 report SHA-256：1da7f598f0685c9fb36ae5c071e1873e06ced986a125bc7f7ed418a1613ca412。59 项 inventory 与最终工作树/Git blob 一致。独立 reviewer 明确说明 live experiment blocked_pending_dispatch_lock，相关准确性/安全率、时延和成本未评估。

### LOCALE-ROBUSTNESS-09

最终元数据提交 9389f276b2b1244dde26beda3682fbac0023cc41。Final SHA-256：526bf61ee00c30dad731bf654d5535f7c503457221e118116a2e370fc5a7def7；inventory SHA-256：3b30dd081ce468e8c6e818e375bdd566bd986db42bea963d032c178d93fd9c03；正式与根目录 payload manifests 均为 SHA-256 d82eeedc41a71983c51219d025944ca58cadf69ab5f8b7b007c6cf6a5ee2ad48，两份逐字节相同。独立 reviewer 在该 HEAD 上确认 59/59 inventory、104/104 payload 都匹配，round-7 结论只绑定其实际审过的旧 HEAD，并确认当前元数据没有自引用承诺。95 passed、1 warning 是既有实现测试结果，本次仅元数据更新未重跑。

### TAXONOMY-CROSSWALK-09

不可变 release 1.0.2 的源码/数据提交为 964ca88b9c36a1b17d6566324837d8029c5c4f0e；元数据提交为 8a96153ac88d49c2ff5a66ed59263620e8b430b8。Final SHA-256：27cd09e491c7ce1b5df3c22e99abdea679c780e9676735d32b9eec7ba76a97a4；invocation evidence SHA-256：bd21b3493b25436b50475ae02727642cfb62a2c819e662539235cc884191089f；review round-5 JSON SHA-256：8c7bd8f2d565ad6e6a1d1f49a7aad74d83c1564e32461abe921e5449902cb66e；round-5 report SHA-256：2d19980cd4b650901403e96241b454b099caddafcb0b88dfc15714c94562802d。独立 reviewer 支持 173/173 行（12 条更正、161 条原样复核），open_findings=[]；round-4 的 changes-requested 记录作为历史保留。96 项全套测试和 CLI 验证由独立审查运行。reviewer_status 保持 unreviewed，不得误读为 release 标签。

## 未解除的限制

- 三包都没有因此获得真实公司扫描、生产数据库、名单或金融结论资格。
- PROMPT-TRUST、LOCALE 的真实模型实验未运行；准确性、抗注入率、语言稳定性、时延、费用、缓存影响均 not_assessed。
- TAXONOMY 的 dispatch-lock 缺失按治理偏差如实记录；离线候选可供后续研究参考，但正式实验或生产路由前仍须总控按施工契约解决。
- Taxonomy Lab 的测试临时目录、tmp/、.pytest_cache/、.codegraph/ 和 bytecode 按 cleanup manifest 保留；本次未删除。
