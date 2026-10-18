# Search-backed 评分接线：现状与缺口 — 2026-10-18

## 已验证

- DeepSeek Search 真实调用成功：5 条结果，receipt ok，cost 5000 micro-CNY，route=deepseek_search。
- receipt ↔ exposure ↔ checkpoint 绑定 bound。
- 证据：docs/implementation/reviews/deepseek-search-2026-10-18/real-search-receipt-2026-10-18.json

## 引擎侧现状

1. QuickScanWorkLifecycle 接受 require_search / search_policy / external_retrieval；require_search=True 时需要 entity_id、search policy、external retrieval 配置。
2. OwnerResearchServices 接受 search_service；owner 1.4/1.5 的 assert_research_task 在 cell 的 search_policy_sha256 非 NO_EXTERNAL_SEARCH 时，要求 task 的 execution_profile.search_exposure 与 cell hash 一致、search_service 非空。
3. build_external_question_context 要求 SearchPolicy.execution_plan 有该题的 frozen query plan，并从 durable retrieval records 重建 bounded context；需要 work item lease 与 operation_ids。

## 缺口

1. DeepSeek search policy schema 没有 execution_plan / frozen queries，policy.execution_plan 为 None，external context builder 会拒绝。
2. direct driver 没有传 require_search / search_policy / external_retrieval / search_service。
3. owner admission 的 cell 仍未携带 exposure hash；create_company_scan_task 需要显式 search_exposure 且 limits 搜索数 >0。
4. retrieval records（operation_ids）还没有在 work store 落盘；DeepSeek client 目前只产 receipt，不写 retrieval 记录。

## 最小接线步骤

1. 给 DeepSeek policy 增加 execution_plan（每题 frozen query、max_queries、route_id）。
2. 搜索执行后把 receipt + bounded results 写入 work store retrieval records，返回 operation_ids。
3. admission 用 exposure hash 替换 NO_EXTERNAL_SEARCH，limits 设 1。
4. driver 构造 lifecycle 时传 require_search=True、search_policy、external_retrieval，并把 search_service 传给 OwnerResearchServices。
5. 跑 1 题（如 IQS_07），验证 checkpoint search_status=executed + receipt id。
6. 导入 search-backed observation（1.2.0，search_status=executed）。

## 边界

- 不能用固定 public board 冒充 search-backed；search_status=executed 必须有 receipt。
- 当前真实搜索只证明 provider/费用/receipt 可用，不等于评分链路已接。
