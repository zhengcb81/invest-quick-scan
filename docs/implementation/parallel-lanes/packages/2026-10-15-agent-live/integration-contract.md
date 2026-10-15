# 三包共同接口、边界与交接规范

版本：`iqs.agent-live-wave-contract/1.0.0`，2026-10-15。三个包必须先读本文件、自己的卡/targets、manifest与inputs.lock。这里描述待交付接口，不把候选当成已存在的生产能力。

## 1. 不重做的成果与输入优先级

- IQS输入基线为已推送 `54d44a0` 所在版本，实际完整HEAD见inputs.lock；本包准备期间IQS他人10-10 README有4行未提交改动且不在输入/写范围内。不要提交或清理它。
- StockQA `41763bf1e933578f4cc214b354680950b973fdf5`：`src/providers/llm_research_client.py` 的 ResearchChatSession 已实现，原hooks通过，真实DeepSeek/MiMo Pro思考/工具回传已验证。不得另造HTTP/计费/重试。
- Company Lab `51b5b3e18ef3d30c1f240b988d64a0b28fc001b1`：0.2.0/execution_revision=2，RuntimePort model/search request1.0，ResearchRun/checkpoint1.1；原1.0按历史兼容，原schema/题目/fixture/交接不重签。
- BLIND-INPUT `281b7a64a01acbdf8184240f5b9005e146086dce`：Observation1.2/wrapper显式桥已有；ResearchRun未接，不得自动猜成Observation。冻结目录含其既有盲评依赖。
- FIN-PROVENANCE `5dc988bdb42f717009ed3dc4822b2e7ece7e2ab7`：可搬迁参考原件已有，90个expected_score仍null、来源候选不自带oracle资格。不能重做整套90题/重新签旧manifest。

输入以锁定字节为准，HEAD只是定位，不替代rawSHA。快照只包含manifest列出的选择范围；源码中的当前状态说明可能早于S0，真实是否运行以本轮S0报告/回执为准。发现接口需要改动，交 proposal 与反例，总控决定；不写源仓、不改其他包合同。

## 2. 固定研究目标与身份边界

原开发集：catl（宁德时代300750）、cncb_h（中信建投H06066）、alphabet（Alphabet GOOGL）。12道原题按原顺序：IQS_01、02、04、05、06、07、10、11、12、16、18、20。共36个公司×问题槽，原完整题干/锚点/module版本/hash在冻结原targets，不从简称重建题目。

信息截止2026-10-13，公开发布时间必须早于2026-10-14T00:00:00Z；访问时间可以更晚，不能以抓取时间替代公开时间。公司名/ticker只是研究定位提示，不是 StockWiki 实际 identity DTO、上市实体合并依据或执行授权。多地上市按真正issuer主体处理，不能把A/H ticker当两个公司或将不同行业同名公司合并。

用户总体授权仍有效，三个工人只获得自己新根的施工范围。真实主体、当前权限、原生确认、价格/额度预留与最终收费派发由总控接现有公开owner接口。任何合成owner fixture都必须标synthetic，不能作为真实正例、grant或G3/F05关闭凭据。

## 3. 版本与交接载体

三包沿用原题和原答案schema，原ResearchRun1.1是共同消费边界。内部确需扩展task/receipt时用**新的显式版本**，保留旧读行为，不原地向封闭旧schema加字段。未知未来版本、重复JSON key、超界题号/题目hash、单位/期间/主体冲突必须拒绝。

本波新增三个外部载体（各工人实现其严格schema，protocol固定）：

| 载体 | 所属包 | 必须有的内容 |
|---|---|---|
| `iqs.agent_runtime_bridge/1.0.0` | RUN | package_id、source_bases、supported_protocols、entry_points、required_owner_services、candidate_patches、limitations、qualification_granted=false |
| `iqs.agent_reference_slice/1.0.0` | REF | cutoff、targets_ref、36个slots、sources、fact_records、rubric_checks、gap_records、qualification_granted=false |
| `iqs.agent_evaluation_bundle/1.0.0` | EVAL | cutoff、declared_input_formats、original_refs、adaptation_ledger、blind_input_refs、metrics、limitations、qualification_granted=false |

共同 file_ref 为 `{path, bytes, sha256}`：POSIX相对路径、原字节数与小写64位SHA256；显式input-root约束，拒绝绝对/drive-relative/UNC/`..`、symlink/junction越界与已有输出覆盖。URL是source属性，不是本机file_ref。移动目录后验证同字节，不把canonical hash冒raw hash。外部载体不替代原Run/answer，不自行获得生产资格。

REF的 `slots` 固定为36项，至少含company_key、question_id、question_object_sha256、fact_ids、rubric_check_ids、gap_ids；每槽字段可为空但不能删槽。每fact至少含fact_id、company_key、question_ids、claim、source_ids、period、unit、accounting_basis、publication_check、candidate_state、qualification_granted=false。unknown应显式保留，不使用0/空字符串冒已知值。`candidate_state`只取source_checked_candidate、partial、unverified、contradicted；source_checked_candidate是工人核源候选，不是总控签收。

每source至少有source_id、official_url、publisher、title、publication_date及其basis（未知可null并说明）、accessed_at_utc、bounded_excerpt、excerpt_sha256、supports_fact_ids、limitations。只存短摘录/链接/元数据；每源2000字符是**上限而非引用许可**，仍遵守搜索工具的逐源引用额度。禁止下载/留存PDF、财报、全文HTML或原始网页响应。

`rubric_checks`只描述原锚点要求的可核观察、反例、适用/不适用与判断限制；不填唯一正确的1–10分。评分主观性与可验证事实分开。`reference-private/`保留盲评/参考判断；供模型检索的短证据另放`evidence-public/`，二者不能混入同一个agent上下文。

EVAL只用已由调用方显式声明的ResearchRun1.1与完整原件sidecar做适配；成功/证据不足/未解析/拒绝/超时/搜索失败/未派发每个原槽均可追溯。具体研究状态先从冻结Run schema列举后写映射表，不猜状态名。原始失败、原答案与修订链保留；共享attempt的成本只计一次。评分oracle未经实际独立资格核验时，指标为not_qualified/null，不能得到0%或100%。

EVAL的参考资格由调用方注入可信 `reference_authority.assess(reference_ref, *, input_root, cutoff)` 接缝，缺省为not_qualified；复用现有BLIND/来源核查资格机制，返回值必须绑定参考原件SHA、fact/source IDs和独立审查记录。它不是JSON里的自填true，也不由EVAL生成“真实签收”。本包实现验证/消费及明确synthetic正反例；总控随后提供实际独立核源资格。此接缝不要求REF等待EVAL，也不新增逐fact审批流程。

## 4. RUN与总控的依赖注入接缝

RUN导出 `create_runtime_port(services, *, task, session_config)`，返回与原RuntimePort一致的四方法对象：`model_step(envelope)`、`search(envelope)`、`inspect_attempt(attempt_ref)`、`request_resume(attempt_ref)`。envelope须完整验证model/search request1.0的稳定前缀、原题、动态证据、公司和截止绑定，不只取intent短指令。

`services`由总控提供现有StockQA/owner配置对象，至少提供：

- `generation_scope(envelope)`：上下文管理器，内部绑定原生work/pack、当前owner guard、subject registrar、budget/route；缺能力在HTTP前拒绝。协议探针的budget-only路径不能变成公司研究路径。
- `client_for(envelope)`：返回已冻结实际路由的StockQA LLMClient配置，供ResearchChatSession复用；不得读自建key文件或暗换端点/模型。
- `search(envelope)`：委托现有外搜端口并返回实际first-party receipt；S1禁止搜索，S2按主搜索配置，不能本包造HTTP。
- `inspect_attempt(ref)` / `request_resume(ref)`：委托既有原attempt核验/恢复；未知态不靠新建session盲发。

这些是**本波待实现的注入接缝，不是声称现有StockQA已有同名服务**。RUN需提供可执行适配和明确native调用映射，不能只有Protocol/占位stub；实际生产服务对象和原生grant由总控整合。离线端到端可注入明确synthetic的临时原生store/HTTP测试替身，但不能伪装真实owner正例。

一个company/strategy/segment对应一个私有SDK会话；跨公司/策略不得共享动态证据与答案。多tool响应必须完整执行对应调用或明确拒绝，不得丢第二个tool、猜call_id、重复收费或伪造assistant历史。重启无思考上下文时新segment，保留已完成slot及原费用，按原attempt状态决定是否允许新发。公开输出仍为可由EVAL独立读取的ResearchRun1.1。

## 5. 测试与权限纪律

先为关键边界写失败用例再实现，整包结束集中测/审一次。单元测试验证状态/绑定/计量；集成测试走实际冻结公开代码；E2E从新包公开CLI到导出、搬迁、恢复和清理。仅schema/交接模板通过不代表产品通过。

RUN/EVAL默认keyless、禁网；REF仅允许harness自带浏览/搜索核官方HTML，记录实际访问与未能取得，不用环境key或付费provider。测试全部用本包临时目录和隔离配置；没有下载也记录0。只清自己的已核绝对路径，不清外仓的tmp、.claude或其他进程文件。记录PID+创建时间；观察超时不等于进程终止，不重启活任务。

新仓采用自己的PWF和 `codex/<package-id小写>` 分支。CodeGraph未初始化时按AGENTS要求询问，不能因等待索引而停止读取已知文件/离线工作。不要修改全局git/config、系统环境或任何源仓。新根若已存在，先确认其归属；不能凭“新卡”覆盖一个活动writer。

## 6. 独立交接与总控集成

每包交 `docs/handoff/<PACKAGE-ID>/`：

1. handoff.json：按独立模板填写真实base/result commit、changed_paths、实际检查、未完成项；不填future提交。先提交代码结果，再交接元数据，另记录handoff提交，避免自引用hash循环。
2. report.md、integration-notes.md、interfaces-used.json：公开入口、精确协议、候选文件→未来上游路径/baseSHA、集成命令与局限；不隐式依赖别包未交内容。
3. inputs-used.json、artifacts.json：实际输入锁和输出file_ref，artifact清单不含自身hash；旧原件不重签。命令/日志与PID、UTC、exit、stdout/stderr SHA留档。
4. tests.json、test-evidence/、最小可搬迁replay-pack、cleanup.json：测试真实结果、未跑/失败、生成物清理与源只读证明。不保留key或思考正文。
5. 跨包建议只写proposal，不改其他包；候选能力、真实数据资格、生产上线分别报告。正常本地提交，不擅自新增/推送远端。

公开形状校验（在各包自己的cwd，用自己的ID）：

```powershell
python -B -X utf8 C:/Users/郑曾波/Projects/invest-quick-scan/scripts/parallel_handoff_cli.py --catalog C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-15-agent-live/manifest.json --package-id AGENT-RUN-02 --input docs/handoff/AGENT-RUN-02/handoff.json
```

替换为REF/EVAL对应ID即可。它仅验证交接结构。总控收到后三包分别一次集中验收，再处理上游writer/CAS和真正跨仓正反例；只有真实公司实验与独立核源完成后才能讨论策略选择，不能用离线包关闭金融/G3/F05。
