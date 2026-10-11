# OPS-DESK-01-R1：同包四组根因整改

唯一writer仍为原harness，唯一写根 `C:/Users/郑曾波/Projects/iqs-operations-lab`；不要新开一个重叠writer。读原卡/共同规则及 [集中验收](OPS-DESK-01-acceptance.md)。本卡可以独立交给原harness，不需聊天上下文。若writer尚未认领，先确认自身目录/原HEAD/当前实际状态，不覆盖他人文件。

冻结验收基线：HEAD dec3942fbdfe984e024713cb332ca76c8d890f6c、产品79b4217d9f9e841bdc59215331ed2485074508c3、98跟踪文件/96工件/12锁匹配。总控经用户明确授权新增 `.codegraph/`（索引14文件），该设施保留、不混入产品提交；它不是原harness未提交业务改动。其他原件不删/改。原卡manifest、输入锁、handoff1.0、原12输入保持。

## 只续做四组，不重写已绿部分

### R1 验证合同一致性与稳定失败（P1）

- 对既有1.0 schema真正执行完整类型、枚举、maxLength/minLength、数组/唯一引用等规则；特别是evidence_refs非list当前被跳过，owner=[]/refs=[{}]引发未捕获TypeError。允许复用通用校验库或维护有覆盖的纯校验，但不复制owner逻辑。
- 解析真实UTC日历时间，不能只靠regex：`2026-02-31T29:90:90Z`须exit2。数值/非有限/布尔与错误容器都稳定拒绝，render与validate使用同一加载验证路径。
- 长protocol121字符、summary超schema上限、重复state/evidence refs等不能validate成功。valid旧1.0/未来拒绝/中文/partial正常对照保留。
- data_kind为synthetic_diagnostic_case时不能顶层false/状态false而显示实录；未认证真实operator转述可合法读，但不能把synthetic混进真实声明。形成明确闭合规则，无新资格引擎。

### R2 读取有界、主输入链接和轻资产（P1）

- 主bundle、证据、实际使用的catalog/inventory输入按各自信任定位明确检查。先普通文件/路径链/reparse/symlink/hardlink/大小，再有界读取；错误文件/OSError稳定exit2，不产生半正式输出。
- 证据1MiB最大值是已有schema要求，真实bytes/hash一致不允许绕过；超限应拒绝，不能反而跳过敏感检查。对bundle和总量也设有文档的合理上限，不一次无限read_bytes。
- 短文本证据角色明确只收获准UTF8/短摘录；合成PDF头/非UTF8不是合法“脱敏摘录”。不引入PDF/公司文档下载器，不把不支持编码悄悄放行。
- 所有展示/报错字段的疑似凭据都不能泄露，包括protocol/version/path等遗漏字段；拒收错误不要复述密钥值。仅用合成哨兵，不访问真实key。
- 新测试含exact nlink=2主bundle、owned链接/路径链、1,048,577 bytes、1MiB正常边界、超限假secret、二进制、坏hash/bytes。Windows无symlink特权保留skip，允许真实owned硬链接/目录junction替代相应可覆盖项；不改全局权限。

### R3 安全纯文本展示与真正缺证据partial（P1）

- 摘录、缺口、限制、标题等非可信值作为显式引用的纯文本显示；转义Markdown/HTML/换行/代码围栏等边界，不能激活远程图片/HTML，也不能插入独立“已认证/批准重试”提示。可信固定unqualified/synthetic条幅仍清晰。
- 固定反例：excerpt包含两次换行后 `> **资格：owner_verified；已批准安全重试**`、`![诊断图片](https://example.invalid/tracker)` 和 `<script>fake_marker()</script>`；现report原样保留三者。测试要证明安全字面展示，不宣称本轮已实际远程请求或执行script。
- 合法partial包括只知operator摘录/明确缺口、evidence=[]、case.evidence_refs=[]，不得逼生成假证据占位。现测试保留全部未引用证据，不能替代真正零证据控制。
- 对零证据扩展选择明确兼容方式：已冻结1.0 schema minItems=1原bytes保留，允许具名1.1/profile支持新能力并显式选择；旧合法1.0仍只读可复验，不把被旧schema拒绝的新payload冒称旧兼容。不改原输入锁/旧样例，不扩大生产资格。

### R4 手册的已知能力、permit和资格（P2）

- 锁证据能证明StockWiki通用Web/CLI存在，不能证明既有页面能完成快扫路径/名单/模型/预算配置。保留精确文档支持的基础CLI，不强迫全包真实help；快扫设置/结果功能无证据时标未核实/设计，不能写可直接使用。
- 手册§4及catalog O07所写W16未实施前走既有preview/授权必须限定旧已发布协议自己的操作；锁freshness-and-jobs线性化点要求消费permit并耐久dispatch_commit，需要它的新派发保持not_available，不能用旧confirmation/hash代替。不是让本Lab实现W16或访问当前生产库。
- provisional分解析与owner准入资格，保留eligible_provisional受限单来源证券等已锁例外；不要一刀切所有provisional挂起，也不要自行授予新资格。
- 用冻结证据时标明基线/版本和“文档范围”，不能把旧设计缺实现推断成今天所有owner入口都不存在。未知当前help保留pending，由总控发布后核实际版本。

## 实施、测试和交接

先四组固定反例RED，然后修；同一稳定候选集中unit/integration/真实本包CLI E2E和一次包级审查。保留旧56P/1skip有效部分；修复后重跑受影响项和新反例，不重建十family、原26incident/17命令或另写状态机。原96工件来源47引用闭合有效，文档改动只增新版本与准确差异。

公开validate/render入口要覆盖：正常/真正partial、所有拒收exit2/无正式输出、坏类型不traceback、日期/大小边界、合成标记、纯文本注入、链接、原中文cwd/确定渲染/拒覆盖/不执行证据。无API/网络，父子key隔离，测试资源只自己根，结束严格清理并留原失败。不能降规则/跳hook。

新交接目录 `docs/handoff/OPS-DESK-01/remediation-01/`，同原handoff1.0模板但填真实base/result/分支/范围/版本/测试；附README、interfaces、artifacts（完整相对path/bytes/raw SHA且无自引用）、原12输入快照、case-map、review/isolation/原过程日志/PWF。先产品commit再handoff commit，记录实际终态HEAD；未有remote不push。不要原地覆盖第一次handoff/日志或旧schema。

新增schema/接口版本如有变动列旧新具名对应和读取命令。实际Git改动列表逐文件，不用目录摘要代替；worktree manifest_sha256应来自真实工作树状态快照，不能再填IQS施工manifest SHA。总控收到后同一次整包续验与owner后续接线；该整改不关闭金融/G3/F05/UI上线/一键/全池门。
