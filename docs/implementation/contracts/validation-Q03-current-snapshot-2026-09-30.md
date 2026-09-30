# Q03 current-snapshot regression record

Date: 2026-09-30 (UTC)
Owner repository: StockQAbyLLM, branch `master`, HEAD `3c685dda28f67a00bd653ad257a121d3b8edebb8`; tested files were the working tree, not HEAD alone.
Status: **Focused offline regression passed; independent review of this exact snapshot is pending.**

## Scope and execution

After Q02's first-provider task-level acceptance, ran the Q03 parser/result path through unit and public-entry tests for the parser, answer service, runner, models, `main_with_llm`, quick-scan CLI, and QA pipeline.

- Result: **166 passed in 4.91s**, exit code 0, no skips.
- Command shape: `python -B -X utf8 -m pytest -p no:base_url -p no:cacheprovider -o addopts= -c <StockQAbyLLM>/pyproject.toml --rootdir=<StockQAbyLLM> --basetemp=<unique TEMP>/pytest -q <seven test files listed below>`.
- Test files: `tests/unit/test_llm_response_parser.py`; `tests/unit/test_services.py`; `tests/unit/test_llm_runner.py`; `tests/unit/test_models.py`; `tests/unit/test_main_with_llm.py`; `tests/integration/test_quick_scan_cli.py`; `tests/integration/test_qa_pipeline.py`.
- Isolation: unique system TEMP was used as CWD and pytest basetemp. `PYTHONPATH` pointed to StockQA. The third-party `base_url` pytest plugin and project coverage/cache addopts were disabled. `STOCKQA_RUN_LIVE_E2E`, `STOCKQA_OPENAI_API_KEY`, `OPENAI_API_KEY`, `MIMO_API_KEY`, `MIMO_PLAN_API_KEY`, `MINIMAX_API_KEY`, and `DEEPSEEK_API_KEY` were removed from the child environment.
- No live/API/network call was made. HTTP edges use the tests' own fixtures. The temporary root was removed after the run. StockQA HEAD was unchanged and its Git status remained 55 entries before and after.

## Exact working-tree snapshot

| File | SHA-256 |
|---|---|
| `main_with_llm.py` | `7405CE99A61FF5C665F5635C61C992F059F50C5D8A4DC9DA4D8EBC7929813EF1` |
| `src/core/models.py` | `BE8F52B8E1FC99C99079319ED3FB73858CAC34098F8640F170033C47B0010668` |
| `src/providers/async_llm_provider.py` | `CD0A56C7025D48F26038217F3BEE0ED228ECA42939F3F9092D21027667051F8F` |
| `src/providers/llm_provider.py` | `03B6D303311F211FF4D0AA7FD95C8BDA749446CDD558EE51812BCADCB737FCAF` |
| `src/providers/llm_response_parser.py` | `9D5EB7D58DACFED1DFFB605ECA504D8A9EC6B6C39A5E2F4341D0A9B6F58AA867` |
| `src/runners/llm_runner.py` | `E63FDD5890DBCE16A057D0140170E3E1E95C9227E45BD8CC1CD14ABCD8ED0ACC` |
| `src/services/answer_generator.py` | `B59840DA063D00D7BCAAB4BA960B88797F6466A4EAD868BA0A7110E4D8FD44F4` |
| `tests/integration/test_qa_pipeline.py` | `002374F669C3D73059EC954403057C82CBCAF7271C608B6D6D91972E7C67ADDC` |
| `tests/integration/test_quick_scan_cli.py` | `2D146FACE169DD130722DFF182982BCDA9FF7AC9CBCE022F80CE310EA553DD90` |
| `tests/unit/test_llm_response_parser.py` | `3BF0D736CCE8696CAA2F70AD201A3C7BEA1CDA118CE43EC8C10252A174A8259` |
| `tests/unit/test_llm_runner.py` | `098A060E54AB6F2612EAA8B05CDBDA68DDA03F1CE95318FF60C8C6F74F94BB33` |
| `tests/unit/test_main_with_llm.py` | `76E70CB411B8430B29AF7B45C2D90FE24EF26921E435B6A35C2717805BC24DE8` |
| `tests/unit/test_models.py` | `3719D9DB38524D4F4144986C8A0F5EF2C9F01C0F10E9F116B048F159653500CA` |
| `tests/unit/test_services.py` | `C4D99935E48AD2F065DCEF547B4B0444524090F40C7BD6181FD2F755E6179FF8` |

## Review handoff and limits

The earlier Q01/Q03 r2 review at `docs/implementation/reviews/Q01-Q03/r2-follow-up-review.md` approved the fixed parser cases at its then-current snapshot. The parser, answer generator, runner, and parser unit-test hashes still match that report, but `test_quick_scan_cli.py` and other owner files have since changed. Its conclusion is useful prior evidence, not a review of this current snapshot. The next action is a new read-only review bound to the hashes above. No task-receipt v2 artifact is created or refreshed because that workflow was retired on 2026-09-29.

This batch does not exercise live search, prove a cited URL supports a claim, measure provider cost, or close cross-repository identity/observation delivery.
