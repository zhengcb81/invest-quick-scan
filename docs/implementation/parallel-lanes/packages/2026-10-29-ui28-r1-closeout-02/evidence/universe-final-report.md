# UI-UNIVERSE-28-R1 重新验收：需继续整改

- C `1a6d345017c0f6bf5d006eb5a26e9470f0903b83`，M `be7e1ee07b6366d31e1b7eae60942b8d00f58be8`；源树clean且7业务文件SHA保持，源业务/测试/helper/旧交接零修改。
- **旧5项真实反例全部转绿。** 原交付完整功能组实际166 unit +82 Python +6真实DOM/浏览器 =254P，0fail/0skip；独立再跑的同5项不重复增加分母。
- 仍有两个同根因相邻业务反例失败、两个新CLI拒绝反例被错误接受，以及最终独审证据未闭合。

| ID | 剩余问题 | 证据 |
|---|---|---|
| UNIV-R2-ASYNC-DIGEST | R1 checks selection epoch after preview response, then awaits real canonical SHA256. A selection change during that digest still receives the old A preview/token on selected B. The digest is only gated and then performs its real hash, not replaced by a constant. | async-adjacency.test.mjs::R1-ADJ-01 |
| UNIV-R2-STALE-RESOLVE-UNKNOWN | A resolve started while row was preview_ready returns after an apply times out. It overwrites unknown state and owner_result. Saving and loading this draft into a new machine then allows a second apply with zero inspect calls. Existing in-memory pin does not preserve the record across remount because row state was erased. | async-adjacency.test.mjs::R1-ADJ-02 |
| UNIV-R2-REVIEWER-CROSS-BINDING | Changing only final.reviewer_agent_id to a foreign non-author reviewer distinct from the actual invocation leaves the actual new R1 CLI returning exit0/status valid. Both documents are checked individually, but not tied together. | cli-probes.py::cli-r1-reject-final-invocation-reviewer-mismatch |
| UNIV-R2-SIBLING-HANDOFF | An otherwise identical handoff in checkout-sibling/remediation-01 is accepted by the actual R1 CLI with exit0 because str.startswith treats the sibling prefix as inside checkout. Probe files were exclusively owned and removed afterward. | cli-probes.py::cli-r1-reject-sibling-prefix-target |
| UNIV-R2-FINAL-REVIEW-DELTA | Final/invocation point to C1a6d345, but the actual referenced round02 payload is5ff13480. Source/schema trees are equal, but remediation.py changed19lines and Python validator tests12lines. The round validator SHA720d... differs from final2d356..., so delta_note claiming unchanged validator is insufficient to prove the final validator was independently reviewed. | review-chain-check.json plus actual reviewed-to-final Git diff |

## 已修与未修的区别

- 旧的单证券有效期、直接跨行并发、在途换文件、直接unknown重置、preview响应前改选五个基本路径已修；不能把本轮新相邻失败说成旧5原样没修。
- 新业务反例依然是R1要求的resolve/preview交错、异步digest、unknown跨draft归属；没有扩大到生产接线或另加新功能。
- R1-ADJ-01只证明组件A/B预览绑定错；R1-ADJ-02在真实machine/loader上通过fake输运重现无inspect的第二POST，均未调用真实owner。
- 新CLI正例0；旧目录、旧ID、错R1锁、缺锁明确2；外部兄弟前缀和错final reviewer仍0，故自报valid不能签收。

## 独审证据

- 实际round02停在5ff；final/invocation写最终1a6。src/schema tree同值，但validator源码19行与对应测试12行确实改变，SHA不同，不能用旧round签最终validator。
- 保留原记录，不指控伪造；返修后真正调用不同agent审最终C或实证的最终delta，绑定实际工件。

## 清理与范围

- 一次正常真实浏览器功能组6P（约69.91秒），source helper一字未改；本人profile/进程/端口/临时根全部清理，18772释放。
- 两份锁均显式使用；独立本地Git副本避免祖先index错误。runtime-browser/runtime-nonbrowser、checkout/.tmp/cache已清，冻结副本只作审计输入留存。
- 未恢复主线108任务；真实名单、UI8766、owner数据库和收费API均未触碰。
- 建议合并为一份R1补交02收口（正式package_id仍为UI-UNIVERSE-28-R1，目录/CLI/锁协议不另开一套）：所有异步提交点再核当前状态；保留unknown不可被晚读清空；路径用组件边界判断；最终/调用/有效round跨文件严格一致；所有本轮有效红转绿后集中独审交接。

正式交付ID与 `remediation-01/` 路径保持；本报告 `UNIV-R2-*` 仅为发现定位ID，不表示另建R2协议。旧round/invocation保留，新实际审查新增记录并由final精确引用。
