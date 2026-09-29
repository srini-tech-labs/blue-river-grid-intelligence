# Blue River Grid Intelligence — Backend Contract

## General requirements

The FastAPI backend is the only layer allowed to call Databricks platform services.

All API responses should be JSON serializable.

Validate inputs, use parameterized SQL or safe bindings where available, and never concatenate arbitrary user-provided text into object names or SQL clauses.

Provide clean error responses for:

- warehouse unavailable / waking
- AI Search unavailable
- model unavailable
- unknown asset
- invalid request
- upstream timeout

Do not expose stack traces, credentials, workspace URLs, or internal authentication details to the UI.

---

## `GET /api/health`

Purpose: application readiness check.

Example response:

```json
{
  "status": "ok",
  "app": "Blue River Grid Intelligence",
  "synthetic_environment": true
}
```

Do not query expensive AI services in the basic health endpoint.

---

## `GET /api/reliability`

Backs:

`get_reliability_summary()`

Primary source:

`workspace.brp_gold.reliability_kpis`

Return:

```json
{
  "saidi": 0.0,
  "saifi": 0.0,
  "caidi": 0.0,
  "customer_base": 125000,
  "period": "...",
  "synthetic": true
}
```

---

## `GET /api/assets?limit=10`

Backs:

`get_high_risk_assets(limit=10)`

Primary source:

`workspace.brp_gold.asset_operational_summary`

Return an ordered list of asset summaries.

The UI may describe these as "Priority Assets" rather than implying the heuristic is a certified engineering risk ranking.

Required fields include:

- asset_id
- substation_id
- criticality
- asset_age_years
- avg_utilization_pct
- max_utilization_pct
- max_top_oil_temp_c
- thermal_alert_count
- outage_count
- risk_score
- risk_band

Always return a disclaimer field indicating that the score is a portfolio demonstration heuristic.

---

## `GET /api/assets/{asset_id}`

Backs:

`get_asset_360(asset_id)`

Primary sources:

- `workspace.brp_gold.asset_operational_summary`
- `workspace.brp_gold.asset_event_timeline`
- `workspace.brp_silver.work_orders`
- `workspace.brp_silver.outage_events`

Return:

```json
{
  "asset_summary": {},
  "timeline": [],
  "work_orders": [],
  "outages": [],
  "risk_disclaimer": "..."
}
```

Unknown asset:

HTTP 404 with a clean JSON error.

---

## `GET /api/assets/{asset_id}/timeline`

Backs:

`get_asset_timeline(asset_id)`

Primary source:

`workspace.brp_gold.asset_event_timeline`

Return chronological records with:

- event_date
- event_type
- severity
- component
- description

---

## `POST /api/knowledge/search`

Backs:

`search_knowledge(...)`

Request:

```json
{
  "query": "cooling system thermal condition",
  "asset_id": "TX-184",
  "document_type": null,
  "num_results": 8
}
```

Required behavior:

- existing AI Search index only
- `HYBRID` retrieval
- asset/document filters when supplied
- reasonable maximum on `num_results`
- return source metadata

Response:

```json
{
  "results": [
    {
      "chunk_id": "...",
      "document_id": "...",
      "document_type": "...",
      "title": "...",
      "asset_id": "TX-184",
      "work_order_id": "...",
      "document_date": "...",
      "source_file": "...",
      "content": "..."
    }
  ]
}
```

Do not expose raw similarity internals unless they add genuine UI value.

> **Amendment (stage4-v1.1, security hardening):** internal storage locations (`source_uri`, a Unity Catalog Volume path) are used only inside the backend. They are never returned in any API response and never included in the LLM prompt. Responses carry `source_file`, the document's file name only. This applies equally to `document_sources` in `POST /api/operations-intelligence`.

---

## `POST /api/operations-intelligence`

> **Amendment (stage4-v1.2, terminology):** the grounded-analysis capability is presented as **Operations Intelligence**. Route: `POST /api/operations-intelligence`; backend function: `ask_operations_intelligence(question, asset_id=None)`. Request, response and grounding behaviour are unchanged.


Backs:

`ask_operations_intelligence(question, asset_id=None)`

Request:

```json
{
  "question": "Why did TX-184 require corrective maintenance?",
  "asset_id": "TX-184"
}
```

Required flow:

```text
question
   |
asset resolution / validation
   |
   +-----------------------+
   |                       |
Delta structured facts     AI Search HYBRID
   |                       |
   +-----------+-----------+
               |
         labeled evidence
          [S1] + [D#]
               |
        grounded prompt
               |
 ai_query(system.ai.gpt-oss-20b)
               |
 answer + source manifest
```

Response:

```json
{
  "answer": "...",
  "asset_id": "TX-184",
  "structured_evidence": {},
  "document_sources": [],
  "warnings": [],
  "risk_disclaimer": "...",
  "synthetic": true
}
```

The backend should maintain the mapping between `[D#]` labels and actual retrieved source metadata so the UI can render clickable/expandable evidence.

## Asset resolution

If `asset_id` is explicitly provided, validate it.

If omitted, the backend may resolve an obvious asset identifier in the question such as `TX-184`.

Do not invent an asset when the question is ambiguous.

## Query safety

- Do not permit arbitrary SQL from the browser.
- Do not allow user text to select arbitrary catalogs, schemas, tables, or columns.
- Keep SQL statements server-defined.
- Apply input length limits to Operations Intelligence and search requests.
- Apply conservative result limits.
