# EVID-LAB-01 summary（离线证据质量评测与下一轮实验设计）

任务 L02 的离线支撑交付。工作目录：`C:/Users/郑曾波/Projects/iqs-evidence-lab`
（新建源仓，分支 `codex/evid-lab-01`，无 remote）。
起点 commit `cc3c38824c90a210196d63242797113247094b22`；
结果 commit `35b98cd443c0adf05fae1ebc2bd6cc0e28760019`（本交接证据所在提交为随后的证据提交，
按规范不把自身hash写入文件）。

## 最终行为

- `replay`：先严格验证输入锁（224项SHA）与三归档自校验，再计算，**最后**才创建独占输出目录；
  产出 `input-verification.json`、`metrics.json`、`recoverability.json`、`review-join.json`、
  `diagnostics.json`（经 `evidence-diagnostic-v1` schema 校验）、`summary.json`。
  对冻结 `final-statistics.json` 六段逐字段重算比对，`equal_to_published=true`。
- 结构指标与评审分层报告：整包成功率（unit=模型请求）、逐项可恢复率（三归档
  53被拒包/264在包项全部 `not_measurable`，绝不虚构有效答案）、claim事实支持一律
  abstain（`snippet_not_available`）、agent评审标签只以 `agent_review_only` 出现。
- 语义检查（`semantic-rules/1`）：只在输入显式给出两侧时机械判矛盾并定位错误码；
  缺信息 abstain；单位缩放（50%≡0.5、亿/万）不误判；unknown 带 claim 仍被诊断。
- `validate-fixtures`：34 fixtures（synthetic 28 / historical 5 / real_source_snippet 1
  且 `collected=false`）、350 条期望全部命中；历史fixture与归档指纹回链。
- 下一轮预注册：`experiment-proposal.md` + `experiment-proposal.config.json`
  （**`execution_enabled=false`、`live_not_run=true`**，60模型请求/24搜索/封顶
  model60、search24、USD4、seed 20261007、失败不补齐、四层分母不混用）。

## 准确入口命令（Lab 根执行）

```bash
PYTHONPATH=src python -m iqs_evidence_lab replay --input index --output <new_dir>
PYTHONPATH=src python -m iqs_evidence_lab replay --input fixtures/synthetic/FX-001.json --output <new_dir>
PYTHONPATH=src python -m iqs_evidence_lab validate-fixtures
python -m pytest tests/ -q
python -X utf8 tools/make_fixtures.py     # 确定性重建 fixtures
```

退出码：0 成功；2 输入漂移/索引未锁定；3 输出目录已存在或越出Lab根；
4 fixture/诊断schema失败；5 用法错误；6 离线守卫拦截网络。
复现所需只读输入：IQS `5edf5eb` 锁定的三归档、结果索引、review/join、价格与生成配置
（路径与SHA见 `inputs.lock.json`；本仓 `input-verification.json` 记录实际核验值）。

## 边界与兼容/回退

- 零网络、零付费、零key读取、零下载；其他仓全程只读；未建 remote/服务/数据库/`.env`。
- 诊断是研究工具输出：不改公司分数/状态，不发生产字段，不宣称60家公司校准，不启动L03。
- **回退 = 删除或停用本 Lab 仓即可**：原三归档、评审、生产策略、公司结果完全未被修改
  （输入hash前后一致有测试证据），无需回滚任何生产代码。

## 已做 / 未做

已做：输入锁与索引SHA核验、三归档离线重算（与已发布统计一致）、整包成功率与逐项可恢复率、
有限语义矛盾检查、诊断schema v1、34-fixture目录与provenance回链、只读重放CLI、
326评审join重算（两分区互斥、非inter-rater gold）、metric定义、实验预注册、
RED/GREEN与隔离日志、54项测试全绿（`logs/final-regression-GREEN.log`）。

未做（`not_run`，留总控）：新真实搜索/模型实验（提案未授权）、人类gold与inter-rater校准、
真实来源短片段抓取、生产采用、总控联合验收与G3/F05等门。
`review.status=not_run`（worker 不自审自批）。

## 授权与PWF

- 写授权：用户在分派会话中确认“授权创建并作为唯一writer”该Lab根（仅此根）。
- PWF：`PLAN_ID=EVID-LAB-01`、`PWF_PLAN_ROOT=<Lab根>` 实测 fail-closed（不回落他计划）；
  计划文件位于本目录 `planning/`（本安装版本 resolver 无法直接寻址该路径，已在
  `planning/task_plan.md` 记录pin方式）。
