# EVID-LAB-01 summary（2026-10-08 整改后）

唯一工作目录 `C:/Users/郑曾波/Projects/iqs-evidence-lab`，分支 `codex/evid-lab-01`，无remote。
**源码结果 commit `62fe8b2f51bf498d0925b65e998c7b0a4dba7192`**（tool 0.2.0）；
本交接证据在随后的证据 commit 中（按规范不把自身hash写入文件；证据HEAD = 交付后
`git log` 的 tip，`handoff.json.snapshot.result_commit` 指向源码结果 commit）。
历史链：起点 `cc3c388…` → 原交付 `35b98cd…` → 总控验收点 `d87cf71…` →
整改代码 `f5149b9…` → 版本提升 `62fe8b2…`（= result_commit）→ 证据 commit。
开工核验：整改卡要求的 HEAD=d87cf71 一致、工作树当时clean、无活动writer。

## 整改结论（EL-01…EL-06 全部修复，既有功能不退化）

| 组 | 修复 |
|---|---|
| EL-01 | `normalize_period` dict 保留 `half/quarter`；kind冲突即矛盾；子期间/年份缺一侧按具体理由 abstain（`claim/expected_period_year_missing` 等）；不靠关键词补年。Q1 vs Q4、H1 vs H2 → fail；`2026H1` vs `H1` → abstain |
| EL-02 | 无期间窗口 → abstain `source_window_not_stated`；无claim目标 → 同报告比较列/同URL不同内容片段互补 pass；仅 claim目标与**全部**引用窗口冲突 → `E_URL_WINDOW_CONFLICT`；`source_counts` URL去重与片段hash分离，独立来源数不因URL复用增加 |
| EL-03 | 全部公共JSON入口经 `strict_loads`（重复键/NaN/Infinity）；fixture路径→exit4、锁定输入→exit2；historical fixture 深度绑定原归档**全字段投影** + `provenance.chunk_sha256`，改 score/rationale 立即被拒 |
| EL-04 | 发布改为 staging（`.temp-roots/staging-<pid>-<uuid>`）写齐 → 逐文件严格回读 → `os.rename` 原子发布；写盘失败清staging、目标不出现、同路径可重试（反例内建重试断言），不是单纯 catch 返回1 |
| EL-05 | 预注册升 `1.1.0`/`draft_not_signed`：60请求×5=**300计划槽**主分母 + sent/not_sent/失败包内/unknown/结构有效/带claim分层，answered-only 仅条件指标；mixed/themed 四组具体题号；题面/身份/截止日 canonical hash；12条冻结query+24搜索共享规则；context与表头/单位约束；逐模型 token 上界×冻结价公式（0.48276 USD ≤ 0.49）；检索缓存 key/version/TTL 与模型revision缺口；unknown预约禁自动重发；Phase96差异说明；**`execution_enabled=false`** |
| EL-06 | fixture 回放输出原字节 `input_sha256`、在场答案 `answer_sha256`、semantic 记录 `expected_field/observed_field` 定位；`evidence_kind` 不再被硬编码为 historical、agent 标签 → `agent_review`；校验口径更正为 **224次校验/127不同路径/含lock共128独立文件**；34 fixtures/42 expectations/350 诊断记录；`pyproject` 声明运行依赖 `jsonschema>=4`；artifacts 双hash见下 |

## 版本

`iqs_evidence_lab 0.2.0`；diagnostic schema **1.1.0**；fixture schema **1.1.0**；
`semantic-rules/2`；`structure-rules/2`；`metric-definitions/1`；
`plan_slots/1`；预注册 `1.1.0`。

## 准确入口命令（Lab 根）

```bash
PYTHONPATH=src python -m iqs_evidence_lab replay --input index --output <new_dir>
PYTHONPATH=src python -m iqs_evidence_lab replay --input fixtures/synthetic/FX-001.json --output <new_dir>
PYTHONPATH=src python -m iqs_evidence_lab validate-fixtures
python -m pytest tests/ -q                       # 81 = 原54 + 总控反例9 + 整改新增18
python -X utf8 tools/make_fixtures.py            # 确定性重建 fixtures
python -X utf8 tools/gen_proposal_config.py      # 从锁定输入再生预注册配置
```

退出码：0 成功；1 意外/发布失败（staging已清、目标未建、可重试）；2 输入漂移/非严格/
非索引；3 输出目录冲突或越界；4 fixture失败；5 用法错误；6 网络守卫拦截。

## 证据（logs/remediation-2026-10-08/，原 logs/ 全部保留）

- `RED-controller-counterexamples.log`：stash 回 `d87cf71` 快照对总控9反例复现
  **8 failed / 1 passed / 0 error**（与总控一致）。
- `GREEN-controller-counterexamples.log`：修复后 **9 passed**。
- `final-regression.log`：`python -m pytest tests/ -q` → **81 passed**（一次集中回归）。
- `validate-fixtures.log`：34 fixtures / 42 expectations / 350 records，`problems=[]`。
- `replay-index-a.log`/`replay-index-b.log`/`public-cli-runs.json`：三归档双新根重放
  exit0、五payload字节一致、34 fixture 全 exit0、input hash 前后不变、
  `network_attempts=0`、`equal_to_published=true`。
- `cleanup-receipt-p<pid>.json`：逐文件清单+manifest_sha256、`links_or_junctions=[]`、
  `verified_absent=true`、`gaps=[]`（严格清理，不再 ignore_errors）。

## 边界与回退

零网络/付费/key读取/下载；IQS等其他仓只读（前后hash一致）；只提交本仓获授权路径；
不创建remote；不写IQS PWF；不自关 L02/G3/F05。
**回退 = 删除或停用本 Lab 仓**：原三归档、评审、生产策略、公司结果未被修改。
EOL 口径：`artifacts.json`（102条）同时给出工作树原字节 `worktree_sha256`+`eol`
与 `git hash-object --path` 的 `git_blob_oid`，并按 `diff_vs_result_commit` 分类：
`identical=77`、`not_in_result_commit=16`（证据文件，随证据commit入库）、
`updated_after_result_commit=9`（整改后更新的交接文件）；`eol_counts` 记录80个CRLF文件。
总控在旧快照上测得的37项差异为纯CRLF/LF——本工具如实申报两类hash与EOL标记，
**不称内容篡改**，不做全仓行尾改动；导出/恢复方法见 `artifacts.json.export_restore`。

## 已做 / 未做

已做：六组修复、9反例 RED→GREEN、81集中回归、公开CLI三归档/34fixture重放、
双根稳定与失败路径、严格清理回执、预注册实质冻结（非执行）。
未做（`not_run`，留总控）：新真实搜索/模型实验与60/24草案执行、Phase96重跑、
人类gold/inter-rater校准、真实来源短片段、生产采用、总控集中回验。
预注册状态 = **draft_not_signed**（未签核，不是已签预注册）。
