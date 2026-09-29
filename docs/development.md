# Development and deployment guide

Operational intelligence app for the **synthetic** Blue River Power portfolio (not a real utility).
It is one Databricks App: a FastAPI backend that serves the React production bundle from the same origin.
It runs over the frozen Stage 1–3 backend (`stage3-v1`, `hybrid-rag-v1`).

- Architecture: [architecture.md](architecture.md) · Design contracts: [design/](design/) · Stage 3 port details: [stage3-port-notes.md](stage3-port-notes.md)

## Layout

| Path | What |
|---|---|
| `backend/` | FastAPI app. `db/queries.py` holds every SQL statement (parameterized only). `services/` holds the data, search and Operations Intelligence logic. |
| `frontend/` | Vite + React + TypeScript. Builds into `backend/static/` and is not uploaded as source. |
| `app.yaml` | Uvicorn command and resource env vars via `valueFrom` (`sql-warehouse`, `vector-search-index`) |
| `scripts/` | build, stage, create-app (one-time), deploy, `grants.sql`, `smoke.py` |

## Local development

```bash
uv venv .venv && uv pip install --python .venv -r requirements-dev.txt
(cd frontend && npm ci)

# backend: runs as YOUR identity via the CLI profile (for development only)
export DATABRICKS_CONFIG_PROFILE=blue-river
export DATABRICKS_WAREHOUSE_ID=<from `databricks warehouses list`>   # never commit
export DATABRICKS_AI_SEARCH_INDEX=workspace.brp_knowledge.utility_knowledge_index
.venv/bin/uvicorn backend.main:app --reload --port 8000

# frontend dev server with /api proxy -> :8000
(cd frontend && npm run dev)
```

## Tests

```bash
.venv/bin/python -m pytest -q backend          # fakes only, no live calls
(cd frontend && npm test && npm run lint)
python3 scripts/smoke.py --base http://localhost:8000   # live checks
```

## Prerequisites

- The Stage 1–3 Blue River Power backend already in the workspace: Gold/Silver tables, `document_chunks` and the AI Search index.
- Databricks CLI 0.229+ with a profile for the workspace (examples use `blue-river`), Python 3.11+, Node 20+ and `uv`.

## Deploy (Databricks App)

1. **One-time, needs approval:** run `scripts/create_app.sh`. It creates the app, its service principal and both resource bindings.
2. Apply `scripts/grants.sql` with the printed service-principal application ID. The grants are read-only and least-privilege.
3. Run `scripts/deploy.sh`. It builds, stages to `.deploy/`, syncs to the workspace and runs `apps deploy`.
4. Run `python3 scripts/smoke.py --app`. This validates as the **app service principal**.

Before a demo: make sure the app is started, then open the Command Center once to warm the warehouse.
