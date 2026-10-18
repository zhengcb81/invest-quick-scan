# Real saved-research publication — 2026-10-18

状态：真实零 HTTP、非评分研究出版已在原 owner namespace 完成并 ACK；两题 delivered。本文只记录可复核的薄证据与边界，不含答文正文、完整 context、数据库副本或密钥。

## 范围与边界

- 只复用原 WorkDecisionOwner 的 preview / confirmation / inspection / apply 路径，没有新建权限服务、账本、调度器或任务回执。
- 发布内容为已保存的原 native safe 响应；没有调用模型、搜索或下载公司文档（API_requests=0，dispatch_started=false）。
- 未修改原答案、未补搜索证明、未清未决费用、未续 lease。原 101 预算行与两笔/一笔未决保持；本次只新增 schema-v3 research-only checkpoint 与 sealed delivery。
- StockWiki observation 仍为 insufficient_evidence、score=null、evidence_review_status=unreviewed、search_status=unverified；不是正式评分或 verified-search 结果。

## 执行证据（本机）

目录：`runs/shared-engine-production-2026-10-18/real-publication-2026-10-18/`

| 项 | 值 |
|---|---|
| capability | `stockwiki.saved_research_publication_capability/1.0.0`，固定 task/authority hash、4 小时有效期、`native_owner_delegated_agent` |
| request sha256 | `54d0e288ce5da567a57426bb2effe46dc10e1c56adb0d38f52460ddf49291bfa` |
| preview | `wdp1_316c92c10a29e8384c07ce41f71821c349d5846ded6eec5bb67077b7e6c15473` |
| confirmation | `rc1_dcb42b768a62d3a2a6c17baa71b142c305adc8f81f08057c8e15480b766d5bb8` |
| inspection | protocol 1.1.0，API 0，DB writes 0，request 相等，owner store `qsobs_35c706134415180d`，1 anchor / 2 item |
| apply | 2 work、2 package，`formal_search_checkpoint_created=false` |
| delivery | 两包均 import accepted；ACK 与重放完全相等；work/item 均 delivered |
| 账本 | schema 25；102 预算行与迁移前备份逐行一致；attempt 14；其余 12 work 仍 leased；2 v3 checkpoint；2 delivered；0 新增预算/尝试/费用；0 HTTP |
| StockWiki | 2 observation、2 subject binding、2 import item |

迁移前备份与逐表对照：`backup-record.json`（源 SHA 960e9eb0…，逻辑摘要 7d74049c…，48 表 739 行）与 `migration-rehearsal.json`（24→25 保留全部行；v3 默认读取被 `research_only_checkpoint_does_not_satisfy_verified_search` 拒绝）。

## 过程中修复的产品接缝

1. **事务内二次鉴权自锁**：publish 在写事务内再次调用 owner inspection 会 spawn 读进程并与自身写锁冲突。修复为复用同事务刚获得的 grant，并仍校验 confirmation id、request hash 与已存储 grant（StockQAbyLLM `8c166a6`）。
2. **CLI 命令形状**：原 StockWiki 命令是扁平 `observation-import`，候选测试里的 `quick-scan observation-import` 从未执行过；真实运行按实际 parser 修正。
3. **研究型答案的原始校验缺口**：原 IQS 合同禁止非评分回答携带数字。新增默认关闭的 `research_only` 通道（`standard_answers.validate_content`、`query_contract._validate_original_semantics`、`subject_dispatch_contract.bind_original`、`subject_dispatch_cli`），SW 仅在 observation 为 `unreviewed` + `unverified` 时传入；单位、期间、来源、截止日与 score/items 规则不变（invest-quick-scan `eaf96e7`，StockWiki `dcc70ce`）。

## 复现入口

- `orchestrate.py`：写固定 capability → preview → confirm → inspect gate → apply。
- `deliver.py`：对 ready/send_uncertain 的 sealed delivery 执行 import、ACK、幂等重放；不重新生成 package。
- 首次 preview 因 15 分钟 TTL 过期，重试用新 action key 重新派生请求与 capability；真实运行记录见 `outer-request-02.json` 与 `confirmation.json`。

## 未完成/不得宣称

- 该节点完成不等于正式评分、verified-search、金融准确性或全池能力；两答仍为 partial/insufficient。
- 未执行 StockWiki ACK 之后的消费者交付或 UI 展示验证。
- 三张新施工包仍在独立审查整改中，未派发、未实施。
