# Q09 follow-up independent review

Date: 2026-09-27  
Review type: read-only, exact-snapshot follow-up  
Scope: close the three P2 findings from the initial Q09 design review; no code edits, test execution, or API calls by the reviewer.

The reviewer confirmed that all eight supplied SHA-256 values matched the reviewed snapshot and reported no actionable P0–P2 findings. The reported issues are closed:

- Id-less Responses search events are counted when their action is classifiable. Unclassifiable events or provider usage that conflicts with observed events remain unknown rather than being undercounted.
- JSON rate values are parsed directly as Decimal; bounded inputs are calculated using exact integer arithmetic, including the upward micro-unit ledger ceiling.
- The v4 terminal-outcome ledger makes reconciliation outcomes immutable: matching replays are idempotent and changed outcomes are rejected. Older settled rows are explicitly `legacy_unverified` because prior schemas did not preserve outcome.

Reviewed SHA-256 values:

| File | SHA-256 |
|---|---|
| `src/providers/llm_client.py` | `5D410CCBEE307E62A4C9999B681957822EB8EC6EE5ED89284D71FA5116CFFA8F` |
| `src/utils/quick_scan_cost_resolver.py` | `EFAD8808C236C056071075A22C828B6366143AE98E2DBAE4BCBADA6EEFE79535` |
| `src/utils/quick_scan_work_store.py` | `66FF215358CFF222476C07CFD9874333CA8A62617861574FD69DFC06CB0B216B` |
| `tests/unit/test_llm_client.py` | `4BBC4EF78CFC250AB7419173B48BC3C37B200D62E2071669D277E19859770A81` |
| `tests/unit/test_quick_scan_cost_resolver.py` | `2A9988D65FDB6A7D4F6FE8285D2D8678536E04AC2A9B21CDCC325EDF1A1228FE` |
| `tests/unit/test_quick_scan_budget.py` | `EF4A48BFEA940AFB035BD6C5715733C61D45AB15799BA472C0DF46EF746D021B` |
| `tests/unit/test_quick_scan_work_store.py` | `05300EF9BA8046559EB1CB2EFFA2275BEA3DDFD5D719084A0F0AE55FE2214873` |
| `docs/quick_scan_rate_cards.md` | `ADAD414AB26465B256EB8668B74EB7D2065CCE81AFE2DD50237C70265FCAFC0C` |

The implementation's isolated verification remains the evidence recorded in [`validation-Q09-usage-and-rate-cards-2026-09-27.log`](../../contracts/validation-Q09-usage-and-rate-cards-2026-09-27.log): provider/runner 371 passed, budget/store 86 passed, both strict isolated groups exited cleanly. The reviewer did not rerun these tests.

This review closes only the follow-up findings in the reviewed code. Q09 remains partial until account-specific pricing and invoice reconciliation are configured and remaining production gates are met.
