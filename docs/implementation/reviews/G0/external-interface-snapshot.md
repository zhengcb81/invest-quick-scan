# G0 External Interface Snapshot

Captured: 2026-09-23

Scope: read-only inspection of the working trees that `invest-quick-scan` will integrate with. This document records observed interfaces; it does not assert that downstream integration tasks are implemented.

## StockQAbyLLM

- Repository: `C:\Users\郑曾波\Projects\StockQAbyLLM`
- Git HEAD observed: `3c685dda28f67a00bd653ad257a121d3b8edebb8`
- The working tree contains untracked local content. No files were changed.
- `LLMClient.send_request` and `AsyncLLMClient.send_request_async` post only `model`, `messages`, `temperature`, and `max_tokens` to a chat-completions-compatible endpoint. No search-tool declaration, search mode, citation contract, or provider-specific web-search metadata is present in these methods.
- `BaseLLMProvider`/`LLMProvider` asks the model for a JSON object containing a score and description and returns `SearchResult.score`.
- `answer_generator.generate_answer` currently replaces a normal result score with the constant `5` (and uses `1` for no-results), so the current end-to-end answer path cannot preserve the model's score.
- `ProviderCascade` accepts an ordered provider-name list and maintains failure/success counters and the current index in process memory. This is useful as a fallback primitive, but it is not a durable quota ledger, request journal, or cross-run resume mechanism.
- `JSONConfigManager.load_questions` returns `List[str]`. Its accepted JSON shapes are category objects, arrays of category objects, or an object with `categories`; it extracts question text rather than preserving the richer question identity, rubric, evidence, and schema metadata required by quick scan.
- The repository exposes an in-memory `BatchProgress`/`BatchStrategy` abstraction, but the inspected source did not establish a durable quick-scan job ledger, quota ledger, request deduplication key, or restart/resume checkpoint.

### G0 implication

The quick-scan contracts must treat StockQAbyLLM as a transport/provider owner that needs adapter work in downstream tasks. G0 must not claim production web-search grounding, score preservation, durable provider fallback, or rich question-schema support from the current implementation.

## StockWiki

- Repository: `C:\Users\郑曾波\Projects\StockWiki`
- Git HEAD observed: `f5b8526c78ef0bc7df27885da043ce5a2534fffb`
- The working tree is substantially modified and contains untracked files. No files were changed.
- Repository guidance assigns research semantics, accepted/rejected evidence, and knowledge state to StockWiki, while `company-wiki` owns source discovery, downloads, raw artifacts, manifests, and source spans.
- No quick-scan entry point was established by the first structural survey. A narrower route/state search remains part of this snapshot audit.
- `Company` is currently keyed operationally by a ticker-derived `safe_id` and carries ticker, name, exchange, industry, aliases, document root, news keywords, and tags. It does not expose a cross-listing issuer ID in this model.
- StockWiki already has its own workspace/job runtime and commands such as `doctor`, `init-workspace`, `ui`, and `add-company`. These are StockWiki operations; no `quick_scan`, `candidate_set`, or quick-scan resume command was found by literal search.

### G0 implication

Quick-scan owns its lightweight scan observations and execution ledger. StockWiki integration must be explicit and must not create a second mutable owner for StockWiki research state.

## company-wiki

- Repository: `C:\Users\郑曾波\Projects\company-wiki`
- Git HEAD observed: `bf0c8b27e83c3ee7e533c6031fefad8e27e5e121`
- The working tree has pre-existing modifications. No files were changed.
- `SecurityMasterStore` publishes versioned per-market JSON snapshots through atomic replacement.
- `SecurityRecord` exposes canonical name, market, exchange, ticker, security ID, aliases, active state, source provenance, and identifiers.
- `SecurityIdentityResolver.identify` resolves one security record using exact or fuzzy matching plus optional market/exchange hints. Multiple exact records remain ambiguous, and market-specific candidates remain distinct. This resolver therefore does not by itself collapse multiple listings into one issuer.
- `SourceManifest` records immutable raw-source provenance and entity IDs.
- The current on-disk `resolver.py` contains `_AMBIGUOUS_ISSUER` at line 1249, `_load_issuer_index` at lines 1253-1303, the `_issuer_index` load around line 1699, and issuer-anchored `_entity_matches` logic at lines 1738-1747. The index maps ticker, security ID, aliases, and issuer tokens to canonical issuer directories and fails closed when a token is ambiguous. This helps sibling-listing and alias source lookup, but it does not create the quick-scan issuer/listing master or by itself establish an auditable cross-listing collapse for the scan database.

### G0 implication

Quick-scan should consume company-wiki identity/source contracts and reference immutable provenance when available. It must not store downloaded filings or become a competing raw-document repository.

## Research skills

- `analyze-theme-value-chain` and `industry-research` were inspected read-only from `C:\Users\郑曾波\Projects\local-skills` at Git HEAD `ec4db38a0f87717d66567eb83febe23cd9dfa601`.
- Their current workflows assemble company universes from primary research, framework material, and wiki/company directories. A quick-scan query contract is not yet wired into those workflows.
- CodeGraph is not initialized in these two skill directories. Initialization would write external repositories and was therefore not performed under read-only authorization.

### G0 implication

Theme and industry integration is downstream work. G0 should freeze a read-only candidate/query interface that those skills can later consume without transferring ownership of the scan database. Literal searches found no current quick-scan references in either skill.

## Verification boundary

This is a source inspection of current working trees, not an external integration test. External commands that could create caches, databases, reports, or other artifacts were deliberately not run.

## Inspected file fingerprints

The hashes below bind the observations to exact working-tree bytes because several repositories contain pre-existing changes.

| Repository | File | SHA-256 |
|---|---|---|
| StockQAbyLLM | `src/providers/llm_client.py` | `093A5DA419DDD6B9BDB4C04CFCFA67F19F9DD1E57025F26A9CFE788559147D94` |
| StockQAbyLLM | `src/providers/llm_provider.py` | `C6FB82FED70DF5AF1F88F0D7B4D4EC17033B54F322B01EAFBD05ED45F9D72A25` |
| StockQAbyLLM | `src/providers/async_llm_provider.py` | `B0DFC2F5F13B21B2672486617F75034CB50A77991DE1A33A9491BEEF63B6D270` |
| StockQAbyLLM | `src/services/answer_generator.py` | `122D5F987BDF4B41CE05AADDB662551AEB438EEE7BA3BA83E4E6FAB2D711E965` |
| StockQAbyLLM | `src/config/json_config_manager.py` | `29554E76EF13FA5F854234E67B1E0D0F78A8741358395D1FCAC284159D43A47E` |
| StockQAbyLLM | `src/utils/llm_integration.py` | `0F4DC268935DD44A765F9179E46C9AE4A5443A2FE0DA1A3A4E56B7A1A937122C` |
| StockQAbyLLM | `src/interfaces/batch_strategy.py` | `ED141508A48C6ECF17F3F1B280180AB38DC6D2FE1A5063ECE2A1C6EA44C132D3` |
| StockWiki | `stockwiki/config.py` | `D6AB49BBF406E77DC6AC39F5155154DF8AA98BC1EE4F006496B33C8F82A5D613` |
| StockWiki | `stockwiki/cli_registry.py` | `8C32A478FF065488170D31E8D4E7103727B20A70453B32AAB52A1B40D5E2ECE9` |
| StockWiki | `stockwiki/cli_parsers/core.py` | `D0488B5F53986BB5BE174C61E3458FF9B0E8EDB158033E2C283890EF6B09C220` |
| StockWiki | `stockwiki/cli_parsers/company.py` | `3C25DC34EF8A0088F91813FB962319F2B92ACF009BA78978033441CB2A071F84` |
| StockWiki | `stockwiki/runtime.py` | `689742D08CCF1A5463AAED1D247428254D3EB131CBD054A36B7E418D4D6641EA` |
| company-wiki | `src/company_wiki/source_catalog/security_identity.py` | `656CB235CEEBBC6788342E80E74200D324D95E182481CA924AEC9333C8F30EAC` |
| company-wiki | `src/company_wiki/source_catalog/resolver.py` | `783460A9F21679B439073FC6B82F4D5A43F583423D59E9EE627B0C9F149BE21A` |
| company-wiki | `src/company_wiki/source_contract/source_manifest.py` | `A7285B3401AB0BFB58BEE50DF27A53B964227F46609AE1FCF961AE7E1C2D0699` |
| analyze-theme-value-chain | `SKILL.md` | `3E2767BAA381CD8DC6F25323BA167F15510F9088343CA2BD38B585CC329084BB` |
| industry-research | `SKILL.md` | `1E1970C24AD6766DCAF6CDC453D16AE2667450F39F53B474F4DA5A80D88D580C` |
