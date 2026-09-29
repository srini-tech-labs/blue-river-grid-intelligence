#!/usr/bin/env bash
# ONE-TIME: create the Databricks App with its two resource bindings.
# This creates the app's dedicated service principal. Requires explicit approval.
source "$(dirname "$0")/_common.sh"
WID=$(warehouse_id)
cat > "$STAGE_DIR.create.json" <<JSON
{
  "name": "$APP_NAME",
  "description": "Blue River Grid Intelligence — synthetic Blue River Power portfolio demo (Stage 4).",
  "resources": [
    {"name": "sql-warehouse", "sql_warehouse": {"id": "$WID", "permission": "CAN_USE"}},
    {"name": "vector-search-index",
     "uc_securable": {"securable_full_name": "$SEARCH_INDEX", "securable_type": "TABLE", "permission": "SELECT"}}
  ]
}
JSON
databricks apps create --json @"$STAGE_DIR.create.json" --no-compute --no-wait
rm -f "$STAGE_DIR.create.json"
databricks apps get "$APP_NAME" -o json | python3 -c "
import sys, json
a = json.load(sys.stdin)
print('app:', a['name'])
print('service principal application id:', a.get('service_principal_client_id'))
print('resources:', [r['name'] for r in a.get('resources', [])])"
