# Blue River Grid Intelligence — Stage 4 release notes

**Release:** `stage4-v1.2` (current baseline; builds on `stage4-v1.1` and `stage4-v1`)
**Built on:** `stage3-v1` / `hybrid-rag-v1` (unchanged)
**Status:** PASS, accepted 2026-09-28
**Environment:** synthetic Blue River Power utility portfolio

## Delivered

- One Databricks App: a FastAPI backend serving the React production bundle from the same origin.
- **Reliability Command Center:**
  - SAIDI / SAIFI / CAIDI.
  - Priority assets with the heuristic disclaimer.
  - Operational and maintenance summary.
- **Asset 360:**
  - Identity and condition metrics, plus the prototype score with its disclaimer.
  - Chronological timeline, work orders and outages.
  - Live HYBRID document evidence.
  - An Operations Intelligence action scoped to the asset.
- **Operations Intelligence:**
  - Live hybrid RAG: Delta `[S1]` + AI Search `[D#]` → `ai_query('system.ai.gpt-oss-20b')`.
  - Citation validation, clickable citations and an evidence panel.
  - Warnings, and insufficient-evidence and error states.
- **Least privilege:**
  - The app service principal reads only via its bindings: warehouse CAN USE, index SELECT.
  - Its UC grants are SELECT on six tables.
  - No secrets exist anywhere in the application.

## Validation

- Deployed acceptance as the app service principal: 25/25 (v1.2 and v1.1); 20/20 (v1). This includes the Stage 3 retrieval regression (4/4) and the flagship grounding checks.
- 24 backend and 8 frontend automated tests. Lint and type-check are clean.
- Hands-on UI acceptance approved.

Details: [validation-results.md](validation-results.md).

## Not changed

No Stage 1–3 object was modified. No pipeline, table, search endpoint, index, serving endpoint or secret was created. The only new Databricks object is the app, plus its service principal.

## Important limitation

The prototype `risk_score` is a transparent portfolio demonstration heuristic. It is **not** a production engineering, protection, safety or asset-health model.

## stage4-v1.1: security hardening

- `source_uri`, the internal storage location from the AI Search index, is no longer returned by any API or sent to the LLM. Responses and the prompt carry `source_file`, a sanitized file name.
- Shared automated leak detection ([`scripts/leak_scan.py`](../scripts/leak_scan.py)) now runs in the backend tests, the frontend build, the deployment staging guard and the live smoke suite.
- No changes to Stages 1–3, the index, the warehouse, the RAG flow, resources or grants. Re-validated: 24 backend and 8 frontend tests, plus 25/25 deployed checks as the app service principal, including the flagship grounding checks.

## stage4-v1.2: Operations Intelligence

- The grounded-analysis module is now **Operations Intelligence**. It sits alongside Command Center and Asset 360, and combines structured operational data with retrieved utility documents to provide grounded, source-linked explanations and investigation support.
- The UI navigation, headings, actions and screenshots are updated, and so are the API route (`POST /api/operations-intelligence`), the service module and the documentation.
- This is a terminology change only. The warehouse, Delta data, AI Search index, HYBRID retrieval, `[S1]`/`[D#]` evidence, `system.ai.gpt-oss-20b` via `ai_query`, resources and grants are unchanged, as are Stages 1–3.
- Re-validated: 24 backend and 8 frontend tests, a clean leak scan, and 25/25 deployed checks as the app service principal, including the flagship grounding checks.
