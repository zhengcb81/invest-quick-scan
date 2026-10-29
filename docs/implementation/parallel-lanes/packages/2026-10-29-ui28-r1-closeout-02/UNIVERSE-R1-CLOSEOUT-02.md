# UNIVERSE-R1补交02

唯一写根 `C:/Users/郑曾波/Projects/iqs-universe-import-ui-lab`，分支 `codex/ui-universe-28`。本轮HEAD `be7e1ee07b6366d31e1b7eae60942b8d00f58be8`，当前C `1a6d345017c0f6bf5d006eb5a26e9470f0903b83`。正式ID继续 `UI-UNIVERSE-28-R1`、交回 `docs/handoff/UI-UNIVERSE-28/remediation-01/handoff.json`。读 [共同约定](handoff-rules.md)、[锁](inputs.lock.json)、[实测报告](evidence/universe-final-report.md)。旧5项反例已修，完整166unit+82Python+6真实DOM/browser=254项通过，0skip；额外再跑原5P不重复加分母。

## U-CLOSE-01 所有异步提交点都重核当前选择和unknown归属

[两个有效相邻反例](evidence/universe-async.test.mjs)仍2F，原machine约316–385/488–562；只gate真实crypto.digest或fake外部输运，不替换状态机/哈希输出：

1. **R1-ADJ-01**：预览response后先核epoch，再await canonical SHA；hash等待时改选B，hash结束仍提交A预览/token给B。需要在最后实际发布前再校draft/row/选择/连接和当前状态，不能仅在前一个await后查一次。允许拒绝冲突编辑或抛弃旧reply，不能造新token。
2. **R1-ADJ-02**：resolve在timeout前启动、timeout后迟到，清掉unknown及owner_result。save→新machine loadDraft后未知归属消失，在inspect=0时又允许apply。所有晚读提交须保留权威写结果/unknown；不能靠易丢的内存pin抵挡，恢复草稿也要保留归属。原member/list/history核对仍是解除unknown的前提。

修同一领域/异步提交边界，不只禁按钮。回归到resolve/preview/hash交错、save/remount/loadDraft、unknown与observed_active_needs_reconciliation、确认期间版本变化；用entered gates控制，拒绝或安全排队均可，不绑特定错误码。只证明合成组件行为，无真实owner错误写入。

## U-CLOSE-02 R1校验必须绑定真实reviewer且拒绝兄弟前缀路径

实际7个CLI探针中：正确新目标/双锁0；旧目录/旧ID/交换锁/缺锁均2，已正确。另两项仍错误接受，见 [原命令/实测输出](evidence/universe-cli-probes.json)：

- 只把final.reviewer改为不同于invocation且不等于author的另一ID，CLI仍0/valid。需要final、实际invocation、有效最终round的reviewer/C/锁/manifest相互一致，分别检查“非作者”不够。
- 将合法handoff放在本人checkout-sibling/remediation-01，str.startswith把它当本人checkout，CLI仍0/valid。用真实规范化路径组件/包含关系验证，拒绝兄弟前缀、`..`、junction/symlink外跳；不能靠字符串前缀。路径越界按已声明exit3，元数据非法按2。

最小范围：现 `tools/iqs_universe_import_ui_tools/cli.py:147` 与 `remediation.py:258–398`、针对性负例。所有变体只在本人临时副本修改/复制，finally恢复/清理，不碰用户目录或真实名单。原21锁/新锁角色、旧入口兼容、mutable基线与最终C规则保持，不另造验证平台。

## U-CLOSE-03 最终review须真实覆盖实际validator

- 当前final/invocation写最终1a6，但实际被引用round02.payload_commit仍5ff13480；只有final_payload_commit别名和delta_note提最终C。
- Git实核：src/schema tree确实不变；`remediation.py`却实际19行、对应Python测试12行变化，validator rawSHA也变。不能把它混称validator byte-identical。见 [Git差异](evidence/universe-reviewed-to-final-validator-diff.txt) / [链核查](evidence/universe-review-chain-check.json)。不指控伪造，只是不能用这个记录签最终validator。
- 本轮代码/工具/回归先冻结新C，再真正调用非作者agent审最终C或有实证的最终delta；新增真实round/invocation，当前final指向有效的新记录。保留旧round，不把旧primary C改成新值，不靠重命名或改日期签收。
- 校验器也要拒绝“外层final/invocation新C、最终引用round旧C”及错reviewer；历史round允许旧C，但不能被冒作最终有效round。

## 完成与交回

修上述原R1范围，保留已绿原5/邻接回归与完整功能组。一次本包正常真实DOM/browsermock及安全失败路径，记录真实新计数/环境，不读真实公司库/owner、不放开费用、不接原UI。所有本轮有效红转绿、全部发现修尽、最终独审passed/open[]后用同一R1路径补交，package ID/CLI不变；不要额外建立-R2协议、Lab或生产能力。
