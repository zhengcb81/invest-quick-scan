# EVID-LAB-01 progress

## 2026-10-07（会话1）
- 读卡、handoff-rules、interfaces、inputs.lock、README、结果报告模板与实验结果MD。
- 向用户确认Lab目录授权 → 回答“授权创建并作为唯一writer”。
- 建仓：`C:/Users/郑曾波/Projects/iqs-evidence-lab`，分支 `codex/evid-lab-01`，
  起点commit `cc3c38824c90a210196d63242797113247094b22`（README/.gitignore/pyproject）。
- PWF pin 实测 fail-closed：`PWF_PLAN_ROOT=<lab根> PLAN_ID=EVID-LAB-01` 输出为空，不回落。
- 勘察三归档/review/join/价格/生成策略/final-statistics 结构（见 findings.md）。
- 下一步：验证 inputs.lock 全部 SHA → Phase 3 schema/metric。

（每完成一个 Phase 追加一条：时间、做了什么、命令、结果、测试计数、错误。）

## 2026-10-07（会话1 续）
- Chunk A：inputs/hashing/errors/guards + 5 tests GREEN（224项SHA核验、只读快照对比）。
- Chunk B：archive/stats 重算与已发布 final-statistics 六段逐字段一致（186/24/2.877381/0.392538）；8 tests GREEN。
- Chunk C：recoverability（整包=模型请求；三归档53被拒包、264在包项全部 not_measurable）；4 tests GREEN。
- Chunk D：diagnostic schema v1 + semantic-rules/1 + review join 重算（326=196+130互斥、非gold）；24 tests GREEN（含4次RED修复）。
- Chunk E：34 fixtures（synthetic 28/historical 5/real 1 collected=false）+ catalog 校验 + provenance 指纹回链；4 tests GREEN。
- Chunk F：CLI replay/validate-fixtures + 9 E2E GREEN（独占输出、字节级稳定、hash不变、网络/key/付费0、subprocess离线）。
- 最终集中回归：`python -m pytest tests/ -q` → 54 passed，exit0（logs/final-regression-GREEN.log）。
- CLI 日志：validate-fixtures exit0（34/350/problems=[]）、replay index exit0（equal_to_published=true）。
- 交付文档：metric-definitions、experiment-proposal(+config execution_enabled=false)、fixture-catalog、interfaces、case-map、isolation、RED/GREEN 日志。
- 下一步：handoff.json/artifacts.json/summary.md 与最终提交。

## 2026-10-07（会话1 终）
- 交接件齐备：handoff.json（通过IQS handoff.schema.json校验）、summary/interfaces/case-map/isolation、
  metric-definitions、fixture-catalog、experiment-proposal(+config)、logs（RED/GREEN/CLI/验证）。
- 总控预检 `scripts/parallel_handoff_cli.py --package-id EVID-LAB-01` → status=valid（errors=[]）；
  首次 changed_path_out_of_scope 已改为绝对路径后通过。
- 提交链：cc3c388(起点) → 5bff8cd(实现) → 35b98cd(交付文档,result_commit) →
  f582e43(交接证据) → 最终提交(预检修正与计划收尾)。
- 最终回归 54 passed exit0；artifacts.json 82项hash复核一致；.temp-roots 空。
- Phase 7 → complete。剩余全部为 not_run（等总控）。

## 2026-10-08（会话2：整改开工）
- 读整改卡/验收/独审/9反例。开工核验：Lab HEAD=d87cf718（与卡一致），工作树clean，无其他writer。
- 计划：先把总控反例复制+适配为Lab RED（8失败/1通过原样保留），再按EL-01..EL-06一批修复。

## 2026-10-08（会话2：整改实施）
- EL-01：period dict保留half/quarter、缺年份/子期按具体理由abstain（claim/expected_period_year_missing等）。
- EL-02：无窗口→source_window_not_stated abstain；无claim目标→比较列互补pass；
  仅当claim目标与全部引用窗口冲突→fail；source_counts URL去重与片段hash分离。
- EL-03：strict_loads（重复键/NaN/Inf）覆盖全部公共JSON入口；fixture/lock错误分别映射4/2；
  historical fixture深度绑定归档全字段投影+provenance.chunk_sha256；锁文件校验=224次/128独立文件。
- EL-04：staging(.temp-roots/staging-*)写齐并严格复读后os.rename原子发布；失败清staging、
  目标不变、同路径可重试（反例内含重试断言）。
- EL-05：config 1.1.0 = 60请求×5=300计划槽分层分母、mixed/themed四组题号、题面/身份/截止日
  hash、12条冻结query+24共享规则、context/表头约束、token上界公式0.48276、检索缓存key/version/TTL、
  模型revision缺口、unknown预约禁自动重发、Phase96差异、execution_enabled=false。
- EL-06：fixture input/answer SHA入diagnostic；semantic expected/observed字段定位；
  evidence_kind不再被硬编码historical；agent标签→agent_review；artifacts双hash口径（见交接）；
  pyproject声明jsonschema运行依赖；schema/rules升1.1.0/2。
- 严格清理：conftest清单(逐文件hash)+link/junction检测+失败打印[cleanup-gap]+cleanup-receipt；
  控制器用例根atexit清理；无残留。
- 结果commit f5149b9；公开CLI三归档×2根+34 fixture重放全绿（public-cli-runs.json）。
