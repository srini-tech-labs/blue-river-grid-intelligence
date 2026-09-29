# Stage 3 → Stage 4 port notes

Operations Intelligence's retrieval, prompt and citation logic was ported from the validated Stage 3 notebooks: `10_hybrid_retrieval`, `20_hybrid_rag_generation` and `30_stage3_evaluation`. This page records what was carried over verbatim and what was deliberately generalized for a live application.

## Ported as-is

| Stage 3 (notebook) | Stage 4 (`backend/`) |
|---|---|
| `10_hybrid_retrieval`, structured retrieval: asset summary; timeline ordered by `event_date`; outages by `start_ts`; work orders by `created_date` | `services/assets.py`, `services/operations_intelligence.py::_asset_structured` |
| `10`, HYBRID asset search (`filters={"asset_id": A}`, 8 results) + POLICY search (`filters={"document_type": "POLICY"}`, 4 results), dedupe on `chunk_id`, cap 10 | `services/operations_intelligence.py::_retrieve_documents` |
| `10`, `[D#]` labels in retrieval order; source manifest fields | `services/operations_intelligence.py` |
| `20_hybrid_rag_generation`, `[S1]` structured text block, `[D#]` document blocks (content capped at 2200 chars), grounded prompt with rules 1–9 and the six answer sections | `services/prompt.py` (text kept verbatim) |
| `20`, `ai_query('system.ai.gpt-oss-20b', prompt)`; answer returned as a plain string | `services/operations_intelligence.py::_generate` |
| `20`/`30`: citation validation (`[S1]` present, ≥2 distinct `[D#]`, no unknown labels, answer ≥300 chars) | `services/citations.py` |
| `30_stage3_evaluation`, retrieval cases R1–R4 | example prompts + `scripts/smoke.py` regression |

## Runtime differences (approved generalizations, not redesign)

1. **Context is rebuilt on every request.** `stage3_latest_context` and `stage3_latest_answer` are used only as reference and regression artifacts.
2. **Policy search uses the user's question.** Stage 3 used a fixed, flagship-specific policy query text. Filter and size are unchanged (`POLICY`, 4).
3. **Failed citation checks become warnings.** In Stage 3 they raised assertions. At runtime they appear in `warnings`, and the UI shows them.
4. **Portfolio mode applies when no single asset is resolved.** Stage 3 only covered the asset path. In this mode:
   - `[S1]` holds reliability KPIs, the top priority assets and the maintenance summary.
   - Document search is unfiltered (8 results) plus POLICY (4).
   - The grounding rules are the same, with portfolio-appropriate section headings.
5. **No storage paths in the prompt.** The Stage 3 `[D#]` blocks included a `Source URI` line holding the document's internal storage path. Stage 4 replaces that line with `Source file: <file name>`, so internal locations are never sent to the model and cannot appear in answers. Document ID, title, type, date, asset, work order and content are unchanged.
6. **Parameterized SQL.** The prompt is passed as a bound `:prompt` parameter instead of an escaped SQL string literal.
7. **Databricks SDK client.** Search goes through `WorkspaceClient().vector_search_indexes.query_index`, with `query_type="HYBRID"` and dict `filters_json` (the endpoint `brp-ai-search` is STANDARD). Stage 3 used the `databricks-ai-search` client. The index, retrieval mode and filters are the same.

## Schema mappings to the Stage 4 contract

- `asset_event_timeline.summary` → returned as `description` (contract field name).
- `reliability_kpis`: `saidi_minutes`→`saidi`, `saifi_interruptions`→`saifi`, `caidi_minutes`→`caidi`, `synthetic_customer_base`→`customer_base`, `as_of_date`→`period` ("as of …").
- Search `content` = `chunk_to_retrieve`.

## Document types in the index (40 chunks)

EMAIL_THREAD, HISTORICAL_FINDING, INSPECTION_REPORT, OPERATOR_NOTE, POLICY, RCA_REPORT, STORM_REPORT.
POLICY and STORM_REPORT chunks have no `asset_id`.

## Citation normalization (added after the first live run)

The first live flagship run returned citations such as `(D1)` rather than `[D1]`. The Stage 3 regex `\[(D\d+)\]` therefore detected only 1 citation, even though 9 were used. Common variants (`(D3)`, `(S1)`, `[D1, D3]`, `(D1; D2)`) are now rewritten to the canonical bracket form before running the unchanged Stage 3 checks. The prompt text is untouched. Free-form mentions such as `RCA-D1` are deliberately not treated as citations.
