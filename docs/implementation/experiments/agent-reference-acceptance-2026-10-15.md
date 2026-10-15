# AGENT-REF-02：总控核源、直接修复及交接

2026-10-15。工程修复完成并提交，参考内容经纠正后仍是有缺口的候选。**55P 不表示真实公司问答准确率通过，也不关闭 F05/G3。**

## 交付定位

| 项目 | 当前证据 |
|---|---|
| 工作目录 | `C:/Users/郑曾波/Projects/iqs-agent-reference-lab` |
| 分支 | `codex/agent-ref-02` |
| 收件基线 | 首次 d0dd719；外包继续提交后另冻结 `5a6aacbdbd60f713d560be843aa12dd729cb6603` |
| 修复源码提交 | `a179149a4c1517d8ddbfad9fa9d117d1c46d9e75` |
| 交接/PWF 提交 | `cc51a2631fb97a53e15ea37cd4804828b738926e` |
| 版本 | package 0.1.1；slice/public/private schema 均保持 1.0.0 |
| 交接 | `docs/handoff/AGENT-REF-02/handoff.json`、`coordinator-acceptance.json` |
| 远端 | 该 Lab 无 remote，本地提交完成；未制造远端或推送私有参考材料 |

原收件 90 文件/5,573,856 bytes 保存在 IQS `runs/agent-ref-acceptance-2026-10-15-01/source/`；后续外包修复另存 `source-worker-review/` 91 文件。两份原件、原失败反例均保持，不能把早期结论当后续版本实际状态。CodeGraph 根据本轮用户明确授权已初始化，16 files/193 nodes/177 edges；它不属于产品交付。

总控先合并外包新交付的锂价方向、ESS 来源关联和测试修复，再逐字节核对新基线与干净工作树，只发布明确的 31 文件差异。另一次提交更新 5 份本 Lab 交接/PWF 文件；未覆盖 `.gitignore`/CodeGraph、RUN/EVAL 根或外部数据库。

## 为什么不能照收原答案

原 34 项测试通过，但六个固定反例仍可被接受：跨公司事实、跨槽 rubric、修改摘录但不改 hash、截止日后事实、默认 export 跳过完整校验、私有 reviewer note 进入 public。原交接还有无效 result_commit 字符串、未来创建时间、真实 artifact 漂移。外包后续修复了部分 metadata 与其他内容问题，未解决这些复现的合同问题。

本轮补充校验公司/题目/slot/rubric/gap 绑定、targets 实际字节、摘录 hash、事实日期及未来访问时间、重复 slot 和非有限数。默认 export 必须完成全量校验；公开板不再带私有 counterevidence_note；两板都绑定输入原始 SHA。CLI 对缺失/非法输入稳定拒绝。

## 实际核源后的内容纠正

核源仅打开网页，不下载财报/PDF、不保存整页正文，不使用项目收费密钥。

- Alphabet Q2 2026 Cloud 增速由错误的 63% 纠正为 82%，收入 24,768 USD million，比较期 13,624；删除未核实的 backlog 断言。[SEC 季度公告](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000066/googexhibit991q22026.htm)
- 原单一 Revenues API URL 不再冒充多个财务标签来源。FY2025 经营现金流、资本开支、利润和年末现金/证券/非流动债务改指实际读到的相应公告表；区分当年实际与次年 capex 指引。[SEC 年度业绩公告](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000012/googexhibit991q42025.htm)
- 18,251/15,954 USD million 是经营租赁付款/负债；融资租赁 2,869/2,500 另列。债务未来两年本金为 2,000+1,000，不能写成约 6.4bn。[租赁附注](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/R63.htm)、[债务附注](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/R68.htm)
- 中信建投营收、净利、分部数字指向实际 158 版；只用可读正文支持的归母净利 94.39 亿元圆整值，不再把它当作核实到元的数字。EPS 比较中矛盾的 1.79 被撤回，未独立复核的比较仍 partial。[法定披露承载页](https://paper.cnstock.com/html/2026-03/27/content_2192811.htm)
- Alphabet 12 条私有 rubric 删除无来源的“高分区间”、经营利润率等于 ROIC、集团利润率直接归属广告等判断；只留可追溯事实、计算口径、反例与缺口。其他公司的旧 rubric 明示尚未获总控实质资格。所有补证建议保持“不下载公司文档”，不以放开 PDF 作为默认最短路径。

每项 before/after 均存 `content/coordinator-content-corrections.json`、`coordinator-rubric-corrections.json`。公开板不包含这些私有判断记录。

## 实际题投影

原三公司×12题的 36 个逻辑槽、原题 hash 与 targets 不变。单独新增 `content/routed12-private-reference.json`，用两个冻结输入 raw file_ref 绑定真实 Alphabet `OPERATING_01` / `score.operating_01` 与逻辑 `IQS_11`。

该题检查必要再投资后的现金能力。164,713−91,447=73,266 USD million 是常规 OCF−capex，不能假装是量到的维护性现金口径；不能重复扣 OCF 已包含的营运资本变动；单年度数字不能证明多年维护投入充足。原生答案保留实际题号，私有补充不能进生成 context，reference_authority 仍 null。

## 验证与清理

原测试 34P；新增反例及真实 subprocess 公共 CLI 后，隔离候选与交付后的真实源码均 **55P/0F/0skip**。交付源测试 PID14372/exit0/6.98s，环境无项目密钥、网络拒绝、SQLite query_only，写入限自有临时根。不是 mock 成功。

实际双模式 public CLI 导出成功，重复输出目录均 exit3；可搬移 replay 的实际 CLI validate exit0。17 个 artifact raw refs 核对通过。公开/私有 board SHA 分别为 `d8141e26e9f72fd4382ad9ce1f0be1aa160ea2f08cd4800b3c75a303a315e2fc` / `20b48daac1b0dbe0aab18e5c8dd2ee916a20e6fa69baf4ebf157389f39fcf8c8`。handoff 公开校验仅为形状/声明范围，不能拿其 valid 授资格。

新候选仍为 36 slots/43 facts/14 sources/36 rubrics/27 gaps；槽状态 19 checked-candidate/16 partial/1 unverified，事实 23/18/2。cncb_h IQS_16 无事实，保留缺口，不赋默认分。未生成 expected_score，所有 qualification_granted=false，未声称修复后的独立 agent 审查通过。

自有临时根清除 320 文件/27,354,250 bytes，剩余 0；原件、日志、JUnit、导出与纠错历史保留。194 个保持性核对通过，包含两份输入冻结、真实 owner 10 文件、原 B01 账本、新 S1 空预算、他人 README。无新增收费模型/搜索请求，无生产库/名单变更。

## 接续

截至本轮观察，RUN/EVAL 约定路径尚无正式 handoff，继续保留其写边界。接收后集中对接真实 RuntimePort/owner_public、Run1.1 盲评与本参考的显式资格范围；先 Alphabet 六会话对照，再按登记扩展。参考缺口必须进入评估分母/覆盖率，不能拿本轮软件测试或“有 rubric”替代数值准确性证据。owner 激活、原生确认与 S1 收费准入仍须沿原流程；不要重跑已用完的 S0 或重置旧账。
