# Blue River Power — Stage 3 Release Notes

**Release:** `stage3-v1`  
**Architecture:** `hybrid-rag-v1`  
**Status:** PASS  
**Environment:** synthetic Blue River Power utility portfolio environment

## What is frozen

Stage 3 proves an end-to-end hybrid RAG pattern that combines governed structured operational data with Databricks AI Search / Vector Search over enterprise-style documents.

Implemented and validated capabilities:

- Structured operational retrieval from Delta Gold/Silver tables.
- Databricks AI Search / Vector Search using `HYBRID` retrieval.
- Metadata filtering, including asset and document-type filters.
- Databricks-native document search baseline through `ai_search()`.
- Hybrid context assembly using `[S1]` for structured evidence and `[D#]` labels for document evidence.
- Databricks-hosted model generation using `system.ai.gpt-oss-20b`.
- Citation validation against the actual retrieved evidence manifest.
- Representative retrieval evaluation: 4/4 test cases passed.
- RAG grounding checks passed:
  - substantive answer
  - structured citation present
  - multiple document citations present
  - no unknown document citation labels

## Flagship question validated

> Why is TX-184 considered high risk, what led to the corrective maintenance decision, and was there evidence of the problem before June 2026?

The final answer combined structured operational facts with retrieved historical findings, inspection evidence, emails, policies, RCA/operator evidence, and corrective-maintenance information.

## Important limitation

The prototype `risk_score` is a transparent portfolio demonstration heuristic. It is **not** a production engineering, protection, safety, or asset-health model and must never be presented as one.

## Stable boundary

After this release, Stages 1–3 should be treated as a stable backend unless a deliberate enhancement is approved. Stage 4 should consume the backend rather than reconstruct it.
