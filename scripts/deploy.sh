#!/usr/bin/env bash
# Build, stage, upload and deploy the app (reversible: redeploy any earlier commit).
source "$(dirname "$0")/_common.sh"
"$ROOT/scripts/build.sh"
"$ROOT/scripts/stage_deploy.sh"
SRC=$(workspace_source_path)
# Replace this app's own source folder wholesale (no stale files). `databricks sync`
# is not used because it honours .gitignore, which excludes .deploy/ and the bundle.
databricks workspace delete "$SRC" --recursive 2>/dev/null || true
databricks workspace mkdirs "$SRC"
databricks workspace import-dir "$STAGE_DIR" "$SRC" --overwrite > /dev/null
state=$(databricks apps get "$APP_NAME" -o json | python3 -c "import sys,json;print(json.load(sys.stdin).get('compute_status',{}).get('state',''))")
if [[ "$state" != "ACTIVE" ]]; then
  # Starting a stopped app deploys the current source folder (just uploaded above),
  # so a separate `apps deploy` would be rejected as a duplicate.
  databricks apps start "$APP_NAME" > /dev/null
else
  databricks apps deploy "$APP_NAME" --source-code-path "$SRC" -o json | python3 -c "import sys,json;d=json.load(sys.stdin);print('deployment:',d.get('status',{}).get('state'),'-',d.get('status',{}).get('message'))"
fi
databricks apps get "$APP_NAME" -o json | python3 -c "import sys,json;a=json.load(sys.stdin);print('status:',a.get('app_status',{}).get('state'),'| url:',a.get('url'))"
