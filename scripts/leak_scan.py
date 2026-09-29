"""Leak detection for internal storage locations, hosts, identifiers and secrets.

One pattern set is shared by:
  - backend tests (API responses and LLM prompts)
  - scripts/smoke.py (live API responses from the deployed app)
  - scripts/build.sh (the built frontend bundle)
  - scripts/stage_deploy.sh (the deployment upload)
  - repository / public-package scans

CLI:
  python3 scripts/leak_scan.py PATH [PATH ...] [--repo] [--databricks-profile NAME]

  --repo                 skip the small allowlist of files that must contain the patterns
                         (this scanner, and test fixtures that prove sanitization works)
  --databricks-profile   also look for this workspace's live identifiers (host, warehouse IDs,
                         app host, app service-principal IDs, deployment IDs). They are
                         fetched at run time and never printed or written anywhere.
Exit code 1 if anything is found. Matches are reported by pattern name and file, and the
matched values are masked.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PATTERNS: dict[str, str] = {
    # internal storage / locations
    "dbfs path": r"dbfs:/",
    "UC volume path": r"/Volumes/",
    "object-store URI": r"\b(?:s3a?|abfss?|gs|wasbs?)://",
    "workspace user path": r"/Workspace/Users/(?![$<{])",  # concrete folders; templates like $me are fine
    # hosts
    "Databricks workspace host": r"[a-z0-9-]+\.(?:cloud\.databricks\.com|azuredatabricks\.net|gcp\.databricks\.com)",
    "Databricks workspace id host": r"\bdbc-[0-9a-f]{8}",
    "Databricks app host": r"[a-z0-9-]+\.[a-z0-9]+\.databricksapps\.com",
    # secrets / tokens
    "Databricks PAT": r"\bdapi[0-9a-f]{32}",
    "bearer token": r"Bearer\s+[A-Za-z0-9._~+/-]{20,}",
    "JWT": r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.",
    "AWS access key": r"\bAKIA[0-9A-Z]{16}\b",
    "private key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "client secret assignment": r"client_secret\s*[=:]\s*['\"]?[A-Za-z0-9]",
    # local filesystem
    "local home path": r"(?:/home/[a-z_][a-z0-9_-]*/|/Users/[A-Za-z][A-Za-z0-9._-]*/|[A-Z]:\\Users\\)",
    # personal email (the GitHub noreply address is allowed)
    "personal email": r"[A-Za-z0-9._%+-]+@(?!users\.noreply\.github\.com)[A-Za-z0-9-]+\.(?:com|net|org|io)\b",
    # stack traces
    "stack trace": r"Traceback \(most recent call last\)",
}

_COMPILED = {name: re.compile(p) for name, p in PATTERNS.items()}

# Files that legitimately contain the patterns: this scanner, and test fixtures that feed
# internal paths in to prove they are stripped.
REPO_ALLOWLIST = {
    "scripts/leak_scan.py",
    "backend/tests/test_services.py",
    "backend/tests/test_leaks.py",
    "frontend/src/test/fixtures.ts",
    "frontend/src/pages/pages.test.tsx",
    "frontend/package-lock.json",  # public npm registry URLs only
}

SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", ".pytest_cache", ".deploy", ".discovery"}
BINARY_EXT = {".jpg", ".jpeg", ".png", ".gif", ".ico", ".woff", ".woff2"}


def find_leaks(text: str, extra_literals: dict[str, str] | None = None) -> list[str]:
    """Names of every leak pattern (and live identifier) found in `text`."""
    hits = [name for name, rx in _COMPILED.items() if rx.search(text)]
    for name, literal in (extra_literals or {}).items():
        if literal and literal in text:
            hits.append(name)
    return hits


def live_identifiers(profile: str) -> dict[str, str]:
    """This workspace's identifiers, fetched via the Databricks CLI (never persisted)."""

    def cli(*args):
        out = subprocess.run(["databricks", *args, "-p", profile, "-o", "json"], capture_output=True, text=True)
        return json.loads(out.stdout) if out.returncode == 0 and out.stdout.strip() else None

    ids: dict[str, str] = {}
    cfg = subprocess.run(["databricks", "auth", "describe", "-p", profile, "-o", "json"], capture_output=True, text=True)
    try:
        host = json.loads(cfg.stdout).get("details", {}).get("host", "")
        if host:
            ids["workspace host"] = host.split("://")[-1].rstrip("/")
    except (json.JSONDecodeError, AttributeError):
        pass
    for i, w in enumerate(cli("warehouses", "list") or []):
        ids[f"warehouse id #{i + 1}"] = w.get("id", "")
    app = cli("apps", "get", "blue-river-grid-intelligence")
    if app:
        ids["app host"] = (app.get("url") or "").split("://")[-1]
        ids["app SP client id"] = app.get("service_principal_client_id", "")
        ids["app SP id"] = str(app.get("service_principal_id", "") or "")
        ids["app SP name"] = app.get("service_principal_name", "")
    deps = cli("apps", "list-deployments", "blue-river-grid-intelligence") or []
    for i, d in enumerate(deps if isinstance(deps, list) else []):
        ids[f"deployment id #{i + 1}"] = d.get("deployment_id", "")
    return {k: v for k, v in ids.items() if v and len(v) >= 6}


def scan_paths(paths: list[Path], root: Path, repo_mode: bool, extra: dict[str, str]) -> list[tuple[str, list[str]]]:
    findings = []
    for base in paths:
        files = [base] if base.is_file() else [p for p in base.rglob("*") if p.is_file()]
        for f in files:
            if any(part in SKIP_DIRS for part in f.parts) or f.suffix.lower() in BINARY_EXT:
                continue
            rel = os.path.relpath(f, root).replace(os.sep, "/")
            if repo_mode and rel in REPO_ALLOWLIST:
                continue
            try:
                text = f.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            hits = find_leaks(text, extra)
            if hits:
                findings.append((rel, hits))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--repo", action="store_true")
    ap.add_argument("--databricks-profile")
    ap.add_argument("--root", default=".")
    a = ap.parse_args()

    extra = live_identifiers(a.databricks_profile) if a.databricks_profile else {}
    root = Path(a.root).resolve()
    findings = scan_paths([Path(p).resolve() for p in a.paths], root, a.repo, extra)
    checked = f"{len(PATTERNS)} patterns" + (f" + {len(extra)} live identifiers" if extra else "")
    if findings:
        for rel, hits in findings:
            print(f"LEAK  {rel}: {', '.join(sorted(set(hits)))}")
        print(f"leak scan FAILED ({checked})")
        return 1
    print(f"leak scan clean ({checked})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
