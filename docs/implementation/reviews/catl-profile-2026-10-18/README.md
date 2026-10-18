# CATL 公司画像草案 + quick facts pack（2026-10-18）

## 状态

**DRAFT，未获 owner 分类确认。** 仅用于 F05 离线验证，不进入生产注册或真实运行。

## profile.draft.json

- company_type: operating
- industry_modules: [energy_transition]
- stage: mature
- routing_rationale: cninfo 所属行业为电气机械和器材制造业；主营动力电池与储能，暂归 energy_transition
- routing_confidence: medium
- sources: catl.com、cninfo.com.cn（official）

## facts pack（quick）

- fact_questions: 16
- answer_format: standard-1
- question_ids 见 manifest
- 生成命令：python scripts/facts_compose.py --profile <profile> --mode quick --output <fresh dir>
- source_sha256 校验：{"questions/facts.json": true, "schemas/answer-content.schema.json": true, "questions/metric-registry.json": true}

## 下一步（需 owner）

1. 确认 CATL 分类口径（industry/stage）；
2. 确认后把 profile 从 draft 提升为正式 profile；
3. 注册 facts pack 并走 owner admission 才能真实运行；
4. 运行后 import observation、刷新画像页事实区。
