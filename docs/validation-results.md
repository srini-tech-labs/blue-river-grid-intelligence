# Validation results — Stage 4 (`stage4-v1.2`)

All results were recorded on 2026-09-28 against the synthetic Blue River Power environment. `stage4-v1.2` is the current accepted baseline. It renames the grounded-analysis module to **Operations Intelligence**, with no architectural change. It builds on `stage4-v1.1`, which stopped exposing storage locations and automated leak detection. Each release was re-validated end to end.

## 1. Deployed acceptance, as the app's service principal

`python3 scripts/smoke.py --app` calls the **deployed** Databricks App. Every warehouse, table, search and model call therefore runs under the app's dedicated service principal and its least-privilege grants, not under a developer identity.

**Result: 25 / 25 checks passed** on `stage4-v1.2` and on `stage4-v1.1`. The 20 functional checks also passed three times on `stage4-v1`.

| Check | Result |
|---|---|
| `/api/health` (no warehouse/AI calls) | PASS |
| UI bundle served same-origin with app name | PASS |
| Reliability KPIs: warehouse + `reliability_kpis` | PASS |
| Priority assets include TX-184, disclaimer present | PASS |
| Operations summary: `maintenance_summary` | PASS |
| Asset 360 TX-184: timeline, work orders, outages (Silver) | PASS |
| Timeline endpoint | PASS |
| Unknown asset `TX-999` → clean 404 `UNKNOWN_ASSET` | PASS |
| AI Search HYBRID retrieval regression (Stage 3 cases, gate ≥ 75%) | PASS, **4 / 4** |
| Operations Intelligence flagship answered via `ai_query('system.ai.gpt-oss-20b')` | PASS |
| Operations Intelligence scoped to TX-184 | PASS |
| Grounding: substantive answer | PASS |
| Grounding: `[S1]` structured citation present | PASS |
| Grounding: ≥ 2 document citations | PASS (7–10 of 10 across runs) |
| Grounding: no unknown citation labels | PASS |
| Source manifest carries title + type for every source | PASS |
| Risk disclaimer present | PASS |
| No internal values leaked: reliability, 404, knowledge search, Asset 360, Operations Intelligence responses, and the served UI bundle | PASS ×6 |
| Search results carry `source_file`, never `source_uri` | PASS |
| Operations Intelligence sources carry `source_file`, never `source_uri` | PASS |

### Retrieval regression (Stage 3 `30_stage3_evaluation` cases, top-k 6)

| Case | Question | Filter | Expected any of | Returned | Hit |
|---|---|---|---|---|---|
| R1 | Historical cooling/thermal concerns for TX-184 before June 2026 | asset TX-184 | Historical finding, Inspection report | Historical finding, Inspection report, RCA report | ✅ |
| R2 | Evidence that led to corrective maintenance / WO-2841 | asset TX-184 | Inspection, Email, RCA | Email, Historical finding, Operator note, RCA | ✅ |
| R3 | Policy for repeated elevated temperature alerts | type POLICY | Policy | Policy | ✅ |
| R4 | What happened after the cooling-system maintenance | asset TX-184 | RCA, Email, Operator note | Historical finding, Inspection, Operator note, RCA | ✅ |

### Flagship question

> Why is TX-184 considered high risk, what led to the corrective maintenance decision, and was there evidence of the problem before June 2026?

- Scope resolved to TX-184 from the question and the asset context.
- 10 evidence chunks were assembled: 8 asset-filtered and 2 new POLICY chunks after dedupe.
- Every run cited `[S1]` plus between 7 and 10 of the 10 retrieved documents, with no invented labels and no warnings.
- End-to-end latency: 10–24s with a warm warehouse. Expect about 30s or more on a cold start.

The answer is generated live on every request. Wording varies between runs; the grounding checks do not.

## 2. Automated tests

| Suite | Scope | Result |
|---|---|---|
| Backend `pytest` (fakes, no live calls) | SQL binding and type conversion, polling, timeout-cancel, resolver (never guesses), citation checks and normalization, Operations Intelligence orchestration (Stage 3 retrieval pattern), HYBRID + filters, route contracts, 404/422/503 mapping, SPA fallback, path traversal, **no storage paths in search or Operations Intelligence responses or in the LLM prompt**, leak-pattern coverage | **24 passed** |
| Frontend Vitest + Testing Library | App shell labelling, Asset 360 content and unknown-asset state, Operations Intelligence request scoping, citation chips → source highlight, unverified labels, no raw JSON, no internal paths, model-unavailable state, formatting | **8 passed** |
| Lint / type-check | `oxlint`, `tsc -b` | clean |

## 3. UI acceptance (hands-on)

The project owner approved the hands-on walkthrough of the nine demo acceptance steps on the deployed app:

1. Command Center loads.
2. TX-184 opens in Asset 360.
3. Timeline, work orders and outages load.
4. Knowledge search returns real indexed evidence.
5. Operations Intelligence answers the flagship question.
6. Operations Intelligence shows structured and document evidence.
7. No credentials or internal workspace URLs appear.
8. The risk disclaimer is visible.
9. Synthetic labeling is visible.

## 4. Security review and leak detection

The "no internal values leaked" results above come from automated checks, not manual inspection. All of them use one shared pattern set, [`scripts/leak_scan.py`](../scripts/leak_scan.py), which flags:
- storage locations: Databricks file-system paths, Unity Catalog Volume paths, cloud object-store URIs and workspace user folders;
- Databricks workspace and app hosts;
- tokens, keys and JWTs;
- local filesystem paths, personal emails and stack traces;
- when a Databricks profile is supplied, this workspace's live identifiers: workspace host, warehouse IDs, app host, the app service principal's IDs and deployment IDs. These are looked up at run time and never written anywhere.

| Where it runs | What it checks | Result |
|---|---|---|
| `pytest` (`backend/tests/test_leaks.py`) | Search and Operations Intelligence API responses and the LLM prompt, fed realistic internal Volume paths | pass |
| `scripts/build.sh` | Built frontend bundle (`backend/static`), with live identifiers | clean |
| `scripts/stage_deploy.sh` | Exact deployment upload, with live identifiers; blocks the deploy on any hit | clean |
| `scripts/smoke.py --app` | Every live API response, plus the served HTML and JS bundle, with live identifiers | clean |
| Repository / public package scan | All source, docs and scripts, with live identifiers | clean |

**Storage paths.** The index's `source_uri` is used only inside the backend, to derive a sanitized `source_file` name. It is not part of any API response model, and it was removed from the LLM prompt, so the model can't echo it. Screenshots carry no metadata. The app service principal holds only the grants in [`scripts/grants.sql`](../scripts/grants.sql), plus SELECT on the index from its resource binding.

## 5. Known limitations

- The risk score is a transparent prototype heuristic and is labelled as such everywhere it appears.
- Operations Intelligence answers are synchronous (no streaming). The first request after the serverless warehouse has been idle includes its warm-up time.
- On Databricks Free Edition the app and warehouse stop when idle and must be started before a demo.
- v1 uses app authorization, so every viewer sees the same synthetic data. Per-user Unity Catalog enforcement (on-behalf-of-user access) is a documented future option.
