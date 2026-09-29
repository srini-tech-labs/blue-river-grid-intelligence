#!/usr/bin/env bash
# Build the React bundle into backend/static (served by FastAPI).
set -euo pipefail
cd "$(dirname "$0")/../frontend"
npm ci --silent
npm run lint
npm test
npm run build
# Fail the build if the bundle contains internal locations, hosts, identifiers or secrets.
python3 ../scripts/leak_scan.py ../backend/static ${DATABRICKS_CONFIG_PROFILE:+--databricks-profile "$DATABRICKS_CONFIG_PROFILE"}
