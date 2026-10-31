"""Machine-readable semantics of the evolved time fields (TIME-SEMANTICS-30).

Each field states: meaning, accepted precision, trusted sources, and what it
must never be used to claim. Mirrors contracts/time-field-semantics.md; the
table below is the operative vocabulary for policy construction.

`searched_at` / `verified_at` do not exist as production observation fields
today; candidate policies may require them, but a missing receipt stays
conservative and observed_at / imported_at / answer text never substitute.
"""

from __future__ import annotations

TIME_FIELD_SEMANTICS_VERSION = "iqs.time_field_semantics/1.0.0"

TIME_FIELDS: tuple[dict, ...] = (
    {
        "field_id": "observed_at",
        "meaning": "本次模型回答被真实执行并持久化观察的UTC时刻（执行外壳回执）",
        "precision": "UTC datetime，秒或微秒，必须Z或+00:00",
        "trusted_sources": ["StockQA执行回执 execution.answered_at", "观察库observed_at列（含hash校验）"],
        "cannot_represent": "资料本身的新旧；真实复核；任何续期依据",
        "refresh_use": "legacy TTL 的观察时刻腿；candidate 不作为验证证据",
    },
    {
        "field_id": "metric_period_start_end",
        "meaning": "财报/经营指标所属的会计或经营期间端点（period_start/period_end）",
        "precision": "ISO date（period_end为日精度；期间含端点日）",
        "trusted_sources": ["answer.period_start/period_end", "answer.metrics[].period_start/period_end（经cutoff校验）"],
        "cannot_represent": "今天已重新核实；指标必定仍适合今天使用",
        "refresh_use": "reporting_period_clock 的读数来源；下一期披露覆盖该指标后刷新",
    },
    {
        "field_id": "evidence_published_at",
        "meaning": "每条被引来源首次公开的时间及其cutoff内可获得性",
        "precision": "UTC datetime优先；date可接受并按cutoff当日UTC结束解释（与原source_available_as_of一致）",
        "trusted_sources": ["真实抓取/搜索回执的来源元数据", "evidence[].published_at（仅当有来源回执绑定时可信）"],
        "cannot_represent": "网页mtime；模型自称的发布时间；指标必然仍新鲜",
        "refresh_use": "publication_clock：严格cutoff要求 published_at ≤ cutoff；未知发布时间不满足严格cutoff",
    },
    {
        "field_id": "information_as_of",
        "meaning": "答案结论自身声明适用的时点（fact_valid_as_of 的现有承载字段）",
        "precision": "ISO date或UTC datetime；date-only按当日T00:00:00Z解释（与冻结legacy一致）",
        "trusted_sources": ["answer.information_as_of（经 information_as_of ≤ cutoff 校验）"],
        "cannot_represent": "导入/观察时刻；无证据支撑的当前性；三个不同时钟的合并",
        "refresh_use": "legacy TTL 的信息时刻腿；candidate 行情题用作 market_clock，fact_valid_clock 保留 observed_at 执行腿，不将信息日期当核查日期",
    },
    {
        "field_id": "searched_at",
        "meaning": "真实工具/搜索实际执行的时刻、查询内容与覆盖范围",
        "precision": "UTC datetime + 查询描述 + 覆盖scope（来源清单/关键词/时段）",
        "trusted_sources": ["execution.search_status=executed 且有可核验 search_receipt_id 的真实回执"],
        "cannot_represent": "搜索完整、结果可信或事实未变化；空搜索结果；模型自称已搜索",
        "refresh_use": "verification_clock 的下位证据；必须由 verification_verifier 核验",
    },
    {
        "field_id": "verified_at",
        "meaning": "原生可信复核流程完成本题所需核查的时间，并绑定覆盖证据、subject/field/scope与policy版本",
        "precision": "UTC datetime + 覆盖回执引用 + policy版本 + 可核hash",
        "trusted_sources": ["原owner侧签发并可独立查验的核查回执（当前生产不存在，不伪造）"],
        "cannot_represent": "模型自称核查；导入时间；任意续期按钮；对旧观察补日期",
        "refresh_use": "verification_clock 的权威读数；缺回执一律保守，不自动变fresh",
    },
    {
        "field_id": "event_invalidated_at",
        "meaning": "已确认重大事件使观察提前失效的UTC时刻",
        "precision": "UTC datetime",
        "trusted_sources": ["owner侧事件记录（追加不可变事件，不改原观察）"],
        "cannot_represent": "推测事件；未确认传闻",
        "refresh_use": "任何时钟内 event_invalidated_at ≤ now 即提前失效",
    },
)

CLOCKS: tuple[str, ...] = (
    "fact_valid_clock",
    "market_clock",
    "reporting_period_clock",
    "publication_clock",
    "verification_clock",
)

CLOCK_READING_SOURCES: dict[str, str] = {
    "fact_valid_clock": "candidate: observed_at（原执行时刻腿，非核查）；legacy: min(observed_at+TTL, information_as_of+TTL)",
    "market_clock": "answer.information_as_of（行情类题的报价时点声明）或 answer.metrics[].as_of",
    "reporting_period_clock": "answer.period_end / answer.metrics[].period_end",
    "publication_clock": "answer.evidence[].published_at（逐条约束，不取最大日期）",
    "verification_clock": "verification_verifier核验后的回执 verified_at（searched_at为其下位证据）",
}

KNOWLEDGE_KINDS: tuple[str, ...] = (
    "market_sensitive",
    "periodic_financial",
    "structural",
    "event_sensitive",
    "mixed",
)

QUESTION_KINDS: tuple[str, ...] = ("score", "fact")

DECISIONS: tuple[str, ...] = (
    "reuse_candidate",
    "refresh_required",
    "not_assessable",
    "not_applicable",
    "blocked_context",
)
