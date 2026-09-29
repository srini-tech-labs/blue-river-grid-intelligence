#!/usr/bin/env bash
# Assemble the minimal upload: app.yaml + requirements.txt + backend (incl. built static).
# No package.json is uploaded, so the Apps runtime only pip-installs Python deps.
source "$(dirname "$0")/_common.sh"
[[ -f "$ROOT/backend/static/index.html" ]] || { echo "Run scripts/build.sh first"; exit 1; }
rm -rf "$STAGE_DIR" && mkdir -p "$STAGE_DIR"
cp "$ROOT/app.yaml" "$ROOT/requirements.txt" "$STAGE_DIR/"
rsync -a --exclude '__pycache__' --exclude 'tests' "$ROOT/backend" "$STAGE_DIR/"
# Guard: nothing internal or secret may ship (shared patterns + this workspace's live identifiers).
python3 "$ROOT/scripts/leak_scan.py" "$STAGE_DIR" --databricks-profile "$DATABRICKS_CONFIG_PROFILE" \
  || { echo "Refusing to deploy: leak scan failed"; exit 1; }
echo "Staged $(find "$STAGE_DIR" -type f | wc -l) files in $STAGE_DIR"
