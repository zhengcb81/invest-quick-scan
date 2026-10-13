# 每个 harness 都必须遵守的施工与交接规则

## 开工与输入

1. 只写 manifest.json 中自己包的 write_scope。新目录不存在才能新建；存在则核实是自己已接续的仓，归属不明暂停写入并报告。新 Git 分支用 codex/<包名小写>，不添加远端、不全局安装包。不自动接其他包。
2. 读取 inputs.lock.json，验证每份冻结文件 raw SHA256 和 bytes，再复制到自己的 fixtures/iqs；复制件必须相同。锁中的源 HEAD 是编制时的 29f6458 对应完整 commit，源有一项他人 README 改动，未追踪文件未纳入；不得清理源目录。源仓之后变化不要求重新冻结，也不允许无声换版本。
3. 本包内建立自己的 task_plan.md/progress.md/findings.md，记录 base commit、本地时区与 UTC、依赖锁 SHA、实际 writer 和初始 Git 状态。共享 IQS 的 PWF、源码、runs、其他 Lab、StockQA、StockWiki、company-wiki、主题/行业仓均只读。CodeGraph 若未初始化按 AGENTS.md 先询问，其他工作可继续。
4. 所有 CLI/源码调用只对本包复制件执行，脚本 ROOT 指向完整 fixtures/iqs。已有入口不支持所需行为时报告 unsupported，不补造 owner 回执或在源仓修复。不要运行 publish-*、激活发布指针、真实 main/刷新/导入/恢复或模型请求。

## 研究与信息边界

ROUTE/SCORE 用明确合成情景，不访问网络。CHAIN 可用现有浏览/检索工具阅读公开网页做人工核证，不调用任何额外模型、付费搜索 API、生产执行器；不读取环境密钥。不下载或归档财报/PDF/网页全文，只记录结构事实、URL、定位与必要短摘录。没有读到正文就是未核实；不能用搜索摘要或另一 LLM 自述当事实。

冻结原题的 ID、顺序、题义、anchors、metric、scope、类型替代和正式 schema 均不改。提案用包自己的 candidate_id；正式 ModuleRelease/TermRelease/Observation/Score/owner golden、身份 DTO 不由 Lab 签发。合成主体用 SYN-*，真实研究仅使用卡指定三家公司，不新增正式名单成员。身份未获真实 owner 映射时明确 not_mapped。

缺失是 null/具名 gap，不是 5 或 0。周期低谷、永久损伤、未兑现增长和资金期限分开，不因亏损就抹去护城河，也不因反转故事忽略偿付风险。来源正确、结构合法、金融结论可信是三个不同检查。

## 开发、测试和环境恢复

先用少量有业务意义的反例跑 RED，再实施；一个稳定候选集中运行 unit/integration/公开 CLI E2E 和一次包级内容审查。修复只补受影响回归，不每行、每题设审查门。测例预期要解释业务原因，不能仅重复 schema 或把自己写的标签当独立金融真值。

用 python -B -X utf8、pytest 禁 cache；TEMP/TMP、pytest basetemp、浏览器配置、工具 HOME/cache 若需要均指本包 runs/test-<随机值>。不更改父进程或 Windows 持久环境变量，不在外仓生成 __pycache__。测试子进程去掉 key/token 类环境变量，阻止非本机网络；CHAIN 的人工研究与离线测试分开。无需复制密钥/生产 SQLite/公司文档。

E2E 至少包含中文空格路径、随机 cwd、实际子进程退出码、相同输入两次导出一致、坏输入零正式输出、已有输出拒覆盖。工具要严格 JSON、duplicate key/NaN/Infinity/1e400 拒绝，限制单文件大小及集合长度，检查跨文件引用、路径穿越和 symlink/junction 逃逸。建议上限由各卡给出，超限不截断后当完整。

清理仅本包本轮真实创建的临时路径；执行前核 resolved 绝对路径在自己的测试根内、无外部链接/硬链接目标，停止自己的子进程后按精确记录删除。保留输入、原失败/通过日志、交付物和研究记录；严禁清共享 TEMP 或别人的缓存。cleanup.json 写实际创建/删除/保留、恢复前后检查及未恢复项。发生意外外写如实列出，不填 false 掩盖。

## 交接与验收

交付目录固定 docs/handoff/<包 ID>/。保留正常本地提交，不 git add 全部临时目录、不推送未知远端。result_commit 是交付内容 commit，handoff 自身后续 commit 另记，避免自引用。产品变动、已读来源、测试日志与 SHA 必须实际可复查，测试模板不填假通过。

共同交付：handoff.json、report.md、artifact-manifest.json、tests.json、cleanup.json、inputs-used.json；各包另交 content/* 和 schemas/*、实现/测试。artifact-manifest 列相对路径、bytes、raw SHA；排除自身、Git/缓存/临时数据库/秘密。inputs-used 保留冻结相对路径和 SHA，异机路径映射另写、不改锁。

handoff 使用 IQS 已有 1.0.0 schema 和本目录模板，interfaces 指向版本化候选协议。verification.checks 保持原封闭字段 name/command/scope/result/passed/failed/skipped，不另加 exit_code 或 log_path；name 等于本包 tests.json 的 check_id，command 写实际命令，scope 写检验范围，result 只能 passed/failed/not_run。退出码、原日志相对路径/bytes/raw SHA、摘要、耗时、实际计数和测试环境详情放 tests.json，不能为了留档扩展正式 handoff schema。只有自审时 review.status=not_run，review.findings 写明 self_review 和实际发现，不使用不存在的 self_review 枚举；独立包级审查后才按原enum如实写 approved/changes_requested/insufficient_evidence，不伪称独审。status=complete 仅本包交付范围完成，不能宣称全局门关闭。真实来源不可得可 partial，必须完整保留卡指定分母和逐项终止理由。

公开形状校验命令（换自己的包 ID/工作根）：

```powershell
C:/Miniconda/python.exe -B -X utf8 C:/Users/郑曾波/Projects/invest-quick-scan/scripts/parallel_handoff_cli.py --catalog C:/Users/郑曾波/Projects/invest-quick-scan/docs/implementation/parallel-lanes/packages/2026-10-13-quality/manifest.json --package-id ROUTE-COVER-02 --input C:/Users/郑曾波/Projects/iqs-route-coverage-lab/docs/handoff/ROUTE-COVER-02/handoff.json
```

这是只读形状/声明范围检查。总控再核实际 Git/输入锁、来源、产品行为和未决项；真正接入由总控单 writer 完成。
