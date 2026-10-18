# CATL 公司画像草案 + quick facts pack（2026-10-18）

## 状态

**owner 已于 2026-10-18 确认分类：operating / energy_transition / mature。** profile.json 为确认版本（profile.draft.json 保留历史）。

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

## 下一步

1. 分类已确认，profile.json 已提升；
3. 注册 facts pack 并走 owner admission 才能真实运行；
4. 运行后 import observation、刷新画像页事实区。
## 2026-10-18 facts 上下文与授权

- facts-context.json：16/16 题覆盖，facts_context_check = ready
- facts-authority.json：facts_authority_check = valid
- 仍需 owner/facts 执行入口注册后才能做真实 facts run
