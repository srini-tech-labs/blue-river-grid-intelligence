-- Least-privilege Unity Catalog grants for the app service principal (read-only).
-- Replace <APP_SP_APPLICATION_ID> with the value printed by scripts/create_app.sh.
-- The AI Search index privileges come from the app resource binding (verify, don't pre-grant).

GRANT USE CATALOG ON CATALOG workspace TO `<APP_SP_APPLICATION_ID>`;
GRANT USE SCHEMA ON SCHEMA workspace.brp_gold TO `<APP_SP_APPLICATION_ID>`;
GRANT USE SCHEMA ON SCHEMA workspace.brp_silver TO `<APP_SP_APPLICATION_ID>`;

GRANT SELECT ON TABLE workspace.brp_gold.asset_operational_summary TO `<APP_SP_APPLICATION_ID>`;
GRANT SELECT ON TABLE workspace.brp_gold.asset_event_timeline TO `<APP_SP_APPLICATION_ID>`;
GRANT SELECT ON TABLE workspace.brp_gold.reliability_kpis TO `<APP_SP_APPLICATION_ID>`;
GRANT SELECT ON TABLE workspace.brp_gold.maintenance_summary TO `<APP_SP_APPLICATION_ID>`;
GRANT SELECT ON TABLE workspace.brp_silver.outage_events TO `<APP_SP_APPLICATION_ID>`;
GRANT SELECT ON TABLE workspace.brp_silver.work_orders TO `<APP_SP_APPLICATION_ID>`;

-- Only if the model check in scripts/smoke.py fails with MODEL_UNAVAILABLE:
-- GRANT USE CATALOG ON CATALOG system TO `<APP_SP_APPLICATION_ID>`;
-- GRANT USE SCHEMA ON SCHEMA system.ai TO `<APP_SP_APPLICATION_ID>`;
-- GRANT EXECUTE ON FUNCTION system.ai.`gpt-oss-20b` TO `<APP_SP_APPLICATION_ID>`;
