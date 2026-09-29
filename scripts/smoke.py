"""Live acceptance checks against a running Blue River Grid Intelligence app.

Deployed:  python scripts/smoke.py --app            (resolves URL + a user OAuth token via the CLI)
Local:     python scripts/smoke.py --base http://localhost:8000

When run against the deployed app, every data/search/model call is executed by
the app's service principal, so this validates the SP's access end to end.
Tokens are held in memory only and never printed.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from leak_scan import find_leaks, live_identifiers  # noqa: E402

PROFILE = os.environ.get("DATABRICKS_CONFIG_PROFILE", "blue-river")
APP = "blue-river-grid-intelligence"

FLAGSHIP = (
    "Why is TX-184 considered high risk, what led to the corrective maintenance decision, "
    "and was there evidence of the problem before June 2026?"
)

# Stage 3 retrieval evaluation cases (30_stage3_evaluation), top_k=6, gate >= 75%.
RETRIEVAL_CASES = [
    ("R1", "What historical evidence shows TX-184 had cooling or thermal concerns before June 2026?",
     {"asset_id": "TX-184"}, {"HISTORICAL_FINDING", "INSPECTION_REPORT"}),
    ("R2", "What evidence led to corrective maintenance for TX-184 and work order WO-2841?",
     {"asset_id": "TX-184"}, {"INSPECTION_REPORT", "EMAIL_THREAD", "RCA_REPORT"}),
    ("R3", "What policy applies to repeated elevated transformer temperature alerts and inspection escalation?",
     {"document_type": "POLICY"}, {"POLICY"}),
    ("R4", "What happened after the cooling-system maintenance on TX-184?",
     {"asset_id": "TX-184"}, {"RCA_REPORT", "EMAIL_THREAD", "OPERATOR_NOTE"}),
]


def cli_json(*args):
    out = subprocess.run(["databricks", *args, "-p", PROFILE, "-o", "json"], check=True, capture_output=True, text=True)
    return json.loads(out.stdout)


class Client:
    def __init__(self, base, token=None):
        self.base = base.rstrip("/")
        self.token = token

    def call(self, method, path, body=None, timeout=240):
        req = urllib.request.Request(self.base + path, method=method,
                                     data=json.dumps(body).encode() if body is not None else None)
        req.add_header("Content-Type", "application/json")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        t = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read().decode()
                status = r.status
        except urllib.error.HTTPError as e:
            raw, status = e.read().decode(), e.code
        return status, raw, time.monotonic() - t


results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'}  {name}{('  — ' + detail) if detail else ''}")


LIVE_IDS: dict[str, str] = {}


def no_leaks(name, raw):
    hits = find_leaks(raw, LIVE_IDS)
    check(f"no internal values leaked: {name}", not hits, ", ".join(sorted(set(hits))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base")
    ap.add_argument("--app", action="store_true")
    ap.add_argument("--skip-analysis", action="store_true")
    a = ap.parse_args()

    token = None
    base = a.base
    if a.app:
        base = cli_json("apps", "get", APP)["url"]
        token = cli_json("auth", "token")["access_token"]
    c = Client(base, token)
    # Live identifiers are looked up (never printed) so responses can be checked for them too.
    LIVE_IDS.update(live_identifiers(PROFILE))
    # The app's own host is intentionally public to its users; it may appear only in the URL we call.
    LIVE_IDS.pop("app host", None)

    s, raw, dt = c.call("GET", "/api/health")
    check("health", s == 200 and json.loads(raw).get("synthetic_environment") is True, f"{dt:.1f}s")

    s, raw, dt = c.call("GET", "/")
    check("UI served same-origin with app name", s == 200 and "Blue River Grid Intelligence" in raw)

    s, raw, dt = c.call("GET", "/api/reliability")
    body = json.loads(raw)
    check("reliability KPIs (SQL warehouse + Gold table access)",
          s == 200 and body.get("saidi") is not None and body.get("customer_base"), f"{s} {dt:.1f}s")
    no_leaks("reliability", raw)

    s, raw, dt = c.call("GET", "/api/assets?limit=10")
    body = json.loads(raw)
    ids = [x["asset_id"] for x in body.get("assets", [])]
    check("priority assets include TX-184 with disclaimer", s == 200 and "TX-184" in ids and body.get("disclaimer"),
          f"{s} {dt:.1f}s")

    s, raw, dt = c.call("GET", "/api/operations/summary")
    check("operations summary (maintenance_summary access)", s == 200 and json.loads(raw).get("maintenance"), f"{s}")

    s, raw, dt = c.call("GET", "/api/assets/TX-184")
    body = json.loads(raw)
    check("Asset 360 TX-184 (timeline, work orders, outages — Silver access)",
          s == 200 and body.get("timeline") and body.get("work_orders") and body.get("outages") is not None
          and body.get("risk_disclaimer"), f"{s} {dt:.1f}s")

    s, raw, _ = c.call("GET", "/api/assets/TX-184/timeline")
    check("timeline endpoint", s == 200 and json.loads(raw).get("timeline"))

    s, raw, _ = c.call("GET", "/api/assets/TX-999")
    check("unknown asset -> clean 404", s == 404 and json.loads(raw)["error"]["code"] == "UNKNOWN_ASSET")
    no_leaks("404", raw)

    hits = 0
    search_raw: list[str] = []
    for cid, q, filters, expected in RETRIEVAL_CASES:
        s, raw, dt = c.call("POST", "/api/knowledge/search", {"query": q, "num_results": 6, **filters})
        types = {r["document_type"] for r in json.loads(raw).get("results", [])} if s == 200 else set()
        search_raw.append(raw)
        hit = bool(types & expected)
        hits += hit
        print(f"      {cid}: {'hit' if hit else 'miss'} {sorted(types)} ({dt:.1f}s)")
    check("AI Search HYBRID retrieval regression (Stage 3 gate >= 75%)", hits / len(RETRIEVAL_CASES) >= 0.75,
          f"{hits}/{len(RETRIEVAL_CASES)}")
    no_leaks("knowledge search", "".join(search_raw))
    check("search results carry source_file, never source_uri",
          all('"source_uri"' not in r for r in search_raw) and any('"source_file"' in r for r in search_raw))

    s, raw, _ = c.call("GET", "/api/assets/TX-184")
    no_leaks("asset 360", raw)
    s, raw, _ = c.call("GET", "/")
    bundle = raw
    for js in re.findall(r'src="(/_app/[^"]+\.js)"', raw):
        bundle += c.call("GET", js)[1]
    no_leaks("served UI bundle", bundle)

    if not a.skip_analysis:
        s, raw, dt = c.call("POST", "/api/operations-intelligence", {"question": FLAGSHIP})
        body = json.loads(raw) if raw else {}
        ok = s == 200
        check("Operations Intelligence flagship answered (ai_query system.ai.gpt-oss-20b)", ok, f"{s} {dt:.1f}s")
        if ok:
            cit = body["citations"]
            check("Operations Intelligence scoped to TX-184", body.get("asset_id") == "TX-184")
            check("grounding: substantive answer", cit["substantive"])
            check("grounding: [S1] structured citation", cit["structured_cited"])
            check("grounding: >= 2 document citations", len(cit["document_labels_cited"]) >= 2,
                  ",".join(cit["document_labels_cited"]))
            check("grounding: no unknown citation labels", not cit["unknown_labels"])
            check("source manifest has metadata", all(d.get("title") and d.get("document_type")
                                                      for d in body["document_sources"]))
            check("risk disclaimer present", bool(body.get("risk_disclaimer")))
            print("      warnings:", body.get("warnings"))
        else:
            print("      error:", raw[:300])
        no_leaks("operations intelligence", raw)
        check("operations intelligence sources carry source_file, never source_uri", '"source_uri"' not in raw)

    failed = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
