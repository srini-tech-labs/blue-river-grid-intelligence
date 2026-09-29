# Stage 4 Authorization and Resource Contract

## Principle

There are two separate authorization questions:

1. Is a person allowed to open the Databricks App?
2. What Databricks resources is the app itself allowed to use?

For Stage 4 v1, data/resource access is performed by the application's dedicated service principal.

## End-user flow

```text
User opens Databricks App URL
        |
Databricks authenticates the user
        |
Databricks checks CAN USE on the app
        |
Blue River Grid Intelligence loads
        |
Browser calls only same-origin /api/* routes
```

The user does not receive or supply an OAuth key.

## Backend flow

```text
FastAPI process
      |
Databricks App dedicated service principal
      |
      +--> SQL warehouse
      +--> selected Unity Catalog tables
      +--> existing AI Search index
      +--> system.ai.gpt-oss-20b
```

Databricks injects the app authentication environment automatically. Code should use Databricks unified authentication rather than reading or displaying credentials.

## Required application resource bindings

### SQL warehouse

- resource type: SQL warehouse
- resource key: `sql-warehouse`
- permission: `CAN USE`
- app environment variable:

```yaml
env:
  - name: DATABRICKS_WAREHOUSE_ID
    valueFrom: sql-warehouse
```

### AI Search index

- resource type: AI Search / Vector Search index
- resource key: `vector-search-index`
- object: `workspace.brp_knowledge.utility_knowledge_index`
- permission: `CAN SELECT`
- app environment variable:

```yaml
env:
  - name: DATABRICKS_AI_SEARCH_INDEX
    valueFrom: vector-search-index
```

## Unity Catalog access required for structured queries

The app service principal needs only read access to required data.

Required catalog/schema privileges:

- `USE CATALOG` on `workspace`
- `USE SCHEMA` on `workspace.brp_gold`
- `USE SCHEMA` on `workspace.brp_silver`
- `USE SCHEMA` on `workspace.brp_knowledge` only where needed by the application

Required `SELECT` objects:

- `workspace.brp_gold.asset_operational_summary`
- `workspace.brp_gold.asset_event_timeline`
- `workspace.brp_gold.reliability_kpis`
- `workspace.brp_gold.maintenance_summary`
- `workspace.brp_silver.outage_events`
- `workspace.brp_silver.work_orders`

Do not grant `MODIFY`, `CREATE`, `OWN`, or broad schema-management privileges.

## AI Search privileges

When the existing index is attached as an app resource, Databricks should grant the app service principal the required:

- `USE CATALOG`
- `USE SCHEMA`
- `SELECT` on the index

Verify this during deployment rather than adding broader manual permissions preemptively.

## system.ai model permissions

Use the existing Stage 3 validated model:

`system.ai.gpt-oss-20b`

No custom serving endpoint should be created.

Verify app-service-principal access before application acceptance. If default access is insufficient, grant only:

- `USE CATALOG` on `system`
- `USE SCHEMA` on `system.ai`
- `EXECUTE` on `system.ai.gpt-oss-20b`

## Secrets policy

There should be no application-specific secret required for the current architecture.

Never place in source control:

- personal access token
- service-principal secret
- OAuth client secret
- AWS credentials
- Databricks workspace URL when it can be discovered from runtime
- SQL warehouse identifiers when they can be injected as resources

## Future production note

A real multi-user enterprise deployment could use Databricks user authorization / on-behalf-of-user access when individual Unity Catalog policies must be enforced.

That is intentionally out of scope for this portfolio v1.
