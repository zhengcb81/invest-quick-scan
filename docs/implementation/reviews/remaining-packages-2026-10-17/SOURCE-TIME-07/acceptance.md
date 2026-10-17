# SOURCE-TIME-07 总控独立验收与隔离修复

结论：原交付不直接签收；以下有效缺口已在本目录 `snapshot/` 修完，候选通过，等待总控以 `patch-cas.json` 精确写回源仓、正常提交并绑定新 payload。未修改源仓、PWF、其他实验或生产数据。

源仓 HEAD `2ead794b368cedd6884072217fd58709581b8596`；payload `fee56b3f1854ebf4820af1a0447782c3c1a4a363`；锁 `21c1bb768f608e8b6cca512ed92da50c46b20e4b301b086a5b00d6713a49c8a2`。79份冻结文件读前后稳定；74份manifest逐项raw SHA/bytes匹配，其中payload项逐项与Git blob核对（Markdown明确换行转换按规范化字节核对）。源仓初始干净，结束所有79份原字节未变。final_head记录payload而metadata另commit是明确自引用约定，不据此强造缺陷。

35条案例（19真实记录/16明确合成）逐条检查目标命题、主体/报告期/口径/时点、unknown、同源独立性、局部支持、反事实与官方角色。独立解析JSON pointer和片段位置核40条真实引用的连续片段、UTF8摘要及冻结文件绑定，见 `independent-excerpts.json`、`case-audit.json`。不存在从自报expected推出真值的推断。本包仍只是未获金融金标准的离线挑战材料，H股官方正文缺口保留。

## 有效发现与修复

1. **P2 严格“之前”被误判**：ST07-SYN-009主张3月10日之前未公开，3月10日公开不能否定此前状态。保留原命题，标签contradicted改not_assessable，理由与unresolved明示严格边界。没有改题维持旧答案。
2. **P2 角色判断偷换为正文判断**：ST07-SYN-013命题是第三方转录可等同交易所原件，材料明确第三方且未核原件。按既有角色错属规则修contradicted，理由仅反驳权威/证据角色等同，绝不据此推断转录数字与原件不一致。
3. **P2 畸形锁崩溃**：copy_relpath=5触发AttributeError/exit1/traceback。发布闭合input-lock schema此前未执行，现嵌入并校验，错类型/未知核心字段/布尔冒充bytes/非hex拒绝2，未知协议仍4；合法1.0.0保持有效。schema生成器同时维护两份嵌入schema，避免下一次同步抹掉校验。
4. **P2 非新目录与partial被覆盖**：原CLI对已存在空输出目录返回0，还覆盖并移动既有coverage.json.partial-tmp。现所有已有根拒绝3，根独占创建、partial用xb，不改原sentinel。
5. **P2 realpath掩盖输入junction**：真实Windows junction复现输出链接已拒绝，但输入根链接仍validate exit0。现在解析前检查输入根/锁/案例/输出路径组件；真实junction输入与输出均公开CLI拒绝3。普通符号链接因Windows权限未能创建，限制明确保留，junction不是mock。
6. **P3 上游审查口径旧句**：limitations仍称两家自审，与同文件逐家qualification最新描述不一致；改为逐包引用，不修改冻结上游或升级资格。

## 实际验证与历史失败

原169测试复跑全部通过，说明不能只重跑作者测试。额外公开CLI原13链12过，畸形锁失败；另现存目录与partial两个独立反例均原返回0；真实junction根原返回0。这些是有效RED。修复后原169测试通过、另6个独立回归通过；合法validate/coverage、任意cwd搬迁业务文件byte-identical、错锁/篡改一字/未知major/重复JSON/未知日期补填/保护输出均实际跑过。

最后完整套件见 `final-r3-r2-author-tests.json`、`green-final-r3-author-suites.log`；6回归见 `green-post-generator-regressions.log`。其余每次argv/返回码在execution JSON和日志。最后schema生成器二次生成byte-identical且6回归再通过。曾有一次schema首次生成只因LF正规化触发本验收脚本原字节断言失败；未当作成功隐去。曾因验收guard错误拒绝继承最小环境的env=None子进程导致169套件1error；已修guard（继承已隔离环境）并全套复跑通过。junction原RED只保留在实际工具调用输出；同名probe文件被第二次GREEN运行替换，现文件只证明GREEN，不能伪装为保留的RED日志。

进程使用不含secret的显式最小环境，HOME/TEMP只指本验收根；所有子Python（含作者测试再起的CLI）强制继承禁网络/外根写audit hook。0真实API、0下载，不读取真实密钥。曾只读Git受sandbox拒绝，获准升级后只读核验并在本验收根写副本。真实junction创建也因sandbox拒绝后获准只在自有根建立，关闭时仅os.rmdir删除链接，未递归进入目标。

历史外包独审有不同agent ID、四轮19项关闭记录，调用证据明确自述部分为orchestrator转述且时钟差，不能冒称密码学证明。此轮由总控实际独立agent `/root/accept_source_time07` 全面重查和修复闭环补实际独审，不能重写历史独审为已审新候选。

`patch-cas.json` 共9文件，before SHA对应已冻结原交付，after对应候选，新增回归文件before=null。不得把旧handoff/review/final原payload宣称覆盖新修复。所有自有tmp已清，保留隔离候选、薄日志/CAS；原环境不声称全局复原，见cleanup.json。
