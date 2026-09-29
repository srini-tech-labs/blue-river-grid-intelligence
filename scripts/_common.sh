# Shared settings for deployment scripts. No secrets or identifiers here;
# the warehouse ID and workspace user are looked up at run time.
set -euo pipefail
export DATABRICKS_CONFIG_PROFILE="${DATABRICKS_CONFIG_PROFILE:-blue-river}"
APP_NAME="blue-river-grid-intelligence"
WAREHOUSE_NAME="${WAREHOUSE_NAME:-Serverless Starter Warehouse}"
SEARCH_INDEX="workspace.brp_knowledge.utility_knowledge_index"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE_DIR="$ROOT/.deploy"

warehouse_id() {
  databricks warehouses list -o json | python3 -c "
import sys, json
name = sys.argv[1]
ids = [w['id'] for w in json.load(sys.stdin) if w['name'] == name]
if len(ids) != 1: sys.exit(f'expected exactly one warehouse named {name!r}, found {len(ids)}')
print(ids[0])" "$WAREHOUSE_NAME"
}

workspace_source_path() {
  local me
  me=$(databricks current-user me -o json | python3 -c "import sys,json;print(json.load(sys.stdin)['userName'])")
  echo "/Workspace/Users/$me/apps/$APP_NAME"
}
