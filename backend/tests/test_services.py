"""Service and route tests with fake SQL and search backends (no live calls)."""

import json
from types import SimpleNamespace as NS

import pytest
from fastapi.testclient import TestClient

from backend import main
from backend.db import queries
from backend.errors import ModelUnavailable
from backend.services import asset_resolver, assets, knowledge, operations_intelligence, reliability
from backend.services.citations import citation_warnings, validate_citations

KNOWN = ["TX-184", "TX-123", "TX-148"]

ASSET_ROW = {
    "asset_id": "TX-184", "substation_id": "SUB-07", "criticality": "HIGH", "asset_age_years": 31,
    "avg_utilization_pct": 65.99, "max_utilization_pct": 97.26, "max_top_oil_temp_c": 92.85,
    "thermal_alert_count": 26, "outage_count": 4, "outage_minutes": 360, "customer_interruptions": 4400,
    "last_maintenance_date": "2026-07-02", "risk_score": 100.0, "risk_band": "HIGH",
}

DOCS = [
    {"chunk_id": f"c{i}", "chunk_to_retrieve": f"evidence {i}", "document_id": f"DOC-{i}",
     "document_type": "INSPECTION_REPORT", "title": f"Doc {i}", "asset_id": "TX-184",
     "work_order_id": None, "document_date": "2026-06-14", "source_uri": f"dbfs:/Volumes/x/{i}.pdf"}
    for i in range(1, 9)
]
POLICY = [
    {"chunk_id": "p1", "chunk_to_retrieve": "policy text", "document_id": "POL-1",
     "document_type": "POLICY", "title": "Thermal policy", "asset_id": None, "work_order_id": None,
     "document_date": "2025-01-01", "source_uri": "dbfs:/Volumes/x/p1.pdf"},
    DOCS[0],  # duplicate chunk must be removed
]


class FakeSQL:
    def __init__(self, answer="x"):
        self.calls = []
        self.answer = answer

    def __call__(self, statement, params=None, **kw):
        self.calls.append((statement, params, kw))
        if statement == queries.ASSET_IDS:
            return [{"asset_id": a} for a in KNOWN]
        if statement == queries.ASSET_SUMMARY:
            return [ASSET_ROW] if params["asset_id"] == "TX-184" else []
        if statement == queries.AI_QUERY:
            if isinstance(self.answer, Exception):
                raise self.answer
            return [{"answer": self.answer}]
        if statement == queries.RELIABILITY_KPIS:
            return [{"as_of_date": "2026-09-02", "outage_events": 34, "customer_interruptions": 51905,
                     "customer_interruption_minutes": 7718200, "synthetic_customer_base": 125000,
                     "saidi_minutes": 61.746, "saifi_interruptions": 0.4152, "caidi_minutes": 148.699}]
        if statement == queries.PORTFOLIO_AGGREGATES:
            return [{"asset_count": 60}]
        if statement == queries.PRIORITY_ASSETS:
            return [ASSET_ROW][: params["limit"]]
        return []


@pytest.fixture
def fake_sql(monkeypatch):
    fake = FakeSQL()
    for mod in (asset_resolver, assets, reliability, operations_intelligence):
        monkeypatch.setattr(mod, "run_query", fake)
    for fn in (asset_resolver.known_asset_ids, assets.get_asset_360, assets.get_asset_timeline,
               assets.get_high_risk_assets, reliability.get_reliability_summary,
               reliability.get_operations_summary):
        fn.cache_clear()
    return fake


@pytest.fixture
def fake_search(monkeypatch):
    calls = []

    def search(query, filters, n):
        calls.append((query, filters, n))
        if filters == {"document_type": "POLICY"}:
            return [dict(r) for r in POLICY]
        return [dict(r) for r in DOCS[:n]]

    monkeypatch.setattr(knowledge, "hybrid_search", search)
    return calls


# ---------- resolver ----------

def test_find_in_question_only_known_assets(fake_sql):
    q = "Why did tx-184 need WO-2841 before June 2026? Compare TX 123."
    assert asset_resolver.find_in_question(q) == ["TX-184", "TX-123"]


def test_validate_rejects_malformed_and_unknown(fake_sql):
    from backend.errors import InvalidRequest, UnknownAsset
    with pytest.raises(InvalidRequest):
        asset_resolver.validate("x'; DROP TABLE t")
    with pytest.raises(UnknownAsset):
        asset_resolver.validate("TX-999")


# ---------- citations ----------

def test_citation_validation_matches_stage3_checks():
    ans = "Summary [S1]. Found in [D1] and [D3]; also [D12]." + "x" * 300
    check = validate_citations(ans, {"D1", "D2", "D3"})
    assert check["structured_cited"]
    assert check["document_labels_cited"] == ["D1", "D3"]
    assert check["unknown_labels"] == ["D12"]
    warnings = citation_warnings(check, 3)
    assert any("[D12]" in w for w in warnings)


def test_normalize_citation_variants():
    from backend.services.citations import normalize_citations
    src = "a (D1) b (S1) c [D2, D3] d (D4; D10) e [D5] f (see note) g RCA-D1 h (D)"
    assert normalize_citations(src) == "a [D1] b [S1] c [D2][D3] d [D4][D10] e [D5] f (see note) g RCA-D1 h (D)"


# ---------- operations intelligence ----------

def test_operations_intelligence_asset_flow(fake_sql, fake_search):
    fake_sql.answer = "Executive Summary [S1] cooling degraded [D1] [D2] policy [D9]. " + "x" * 300
    out = operations_intelligence.ask_operations_intelligence("Why did TX-184 require corrective maintenance?")
    assert out["asset_id"] == "TX-184" and out["scope"] == "asset"
    # Stage 3 retrieval pattern: asset filter x8, POLICY x4, dedupe, cap 10
    assert fake_search[0][1] == {"asset_id": "TX-184"} and fake_search[0][2] == 8
    assert fake_search[1][1] == {"document_type": "POLICY"} and fake_search[1][2] == 4
    labels = [d["citation_label"] for d in out["document_sources"]]
    assert labels == [f"D{i}" for i in range(1, 10)]  # 8 asset + 1 new policy (dup removed)
    assert out["document_sources"][8]["document_type"] == "POLICY"
    assert {d["citation_label"] for d in out["document_sources"] if d["cited"]} == {"D1", "D2", "D9"}
    assert out["warnings"] == []
    assert "heuristic" in out["risk_disclaimer"]
    # prompt passed as bound parameter, includes S1 block and D labels
    stmt, params, kw = [c for c in fake_sql.calls if c[0] == queries.AI_QUERY][0]
    assert "[S1] STRUCTURED OPERATIONAL DATA" in params["prompt"] and "[D9] DOCUMENT EVIDENCE" in params["prompt"]
    assert kw["failure_error"] is ModelUnavailable


def test_operations_intelligence_ambiguous_question_goes_portfolio(fake_sql, fake_search):
    fake_sql.answer = "[S1] [D1] [D2] " + "x" * 300
    out = operations_intelligence.ask_operations_intelligence("Compare TX-184 and TX-123")
    assert out["asset_id"] is None and out["scope"] == "portfolio"
    assert any("several assets" in w for w in out["warnings"])
    assert fake_search[0][1] is None


def test_operations_intelligence_explicit_asset_mismatch_and_unknown_warns(fake_sql, fake_search):
    fake_sql.answer = "[S1] [D1] [D2] " + "x" * 300
    out = operations_intelligence.ask_operations_intelligence("What about TX-123 and TX-999?", asset_id="TX-184")
    assert out["asset_id"] == "TX-184"
    assert any("TX-999 is not an asset" in w for w in out["warnings"])
    assert any("scoped to TX-184" in w for w in out["warnings"])


def test_operations_intelligence_no_documents_and_empty_answer(fake_sql, monkeypatch):
    monkeypatch.setattr(knowledge, "hybrid_search", lambda *a: [])
    fake_sql.answer = None
    out = operations_intelligence.ask_operations_intelligence("Why did TX-184 need maintenance?")
    assert out["answer"] == "" and out["document_sources"] == []
    assert any("No document evidence" in w for w in out["warnings"])
    assert any("did not return an answer" in w for w in out["warnings"])


# ---------- knowledge ----------

def test_hybrid_search_uses_existing_index_hybrid_and_filters(monkeypatch):
    captured = {}

    def query_index(**kw):
        captured.update(kw)
        cols = knowledge.COLUMNS + ["score"]
        row = [f"v-{c}" for c in knowledge.COLUMNS] + [0.9]
        return NS(manifest=NS(columns=[NS(name=c) for c in cols]), result=NS(data_array=[row]))

    monkeypatch.setattr(knowledge, "get_settings", lambda: NS(require_index=lambda: "idx"))
    monkeypatch.setattr(knowledge, "get_workspace_client", lambda: NS(vector_search_indexes=NS(query_index=query_index)))
    out = knowledge.search_knowledge("cooling", "TX-184", "INSPECTION_REPORT", 5)
    assert captured["query_type"] == "HYBRID" and captured["index_name"] == "idx"
    assert json.loads(captured["filters_json"]) == {"asset_id": "TX-184", "document_type": "INSPECTION_REPORT"}
    res = out["results"][0]
    assert res["content"] == "v-chunk_to_retrieve" and "score" not in res
    assert "source_uri" not in res and res["source_file"] == "v-source_uri"


# ---------- routes ----------

def test_routes_contract_shapes_and_errors(fake_sql, fake_search):
    c = TestClient(main.app)
    rel = c.get("/api/reliability").json()
    assert rel["saidi"] == 61.746 and rel["customer_base"] == 125000 and rel["synthetic"] is True
    lst = c.get("/api/assets?limit=10").json()
    assert lst["assets"][0]["asset_id"] == "TX-184" and "heuristic" in lst["disclaimer"]
    assert c.get("/api/assets?limit=0").status_code == 422
    a360 = c.get("/api/assets/tx-184").json()
    assert set(a360) >= {"asset_summary", "timeline", "work_orders", "outages", "risk_disclaimer"}
    r = c.get("/api/assets/TX-999")
    assert r.status_code == 404 and r.json()["error"]["code"] == "UNKNOWN_ASSET"
    assert c.get("/api/assets/bad!id").status_code == 422
    r = c.post("/api/knowledge/search", json={"query": "x" * 501})
    assert r.status_code == 422 and "Traceback" not in r.text
    r = c.post("/api/knowledge/search", json={"query": "cooling", "document_type": "SECRETS"})
    assert r.status_code == 422
    r = c.post("/api/knowledge/search", json={"query": "cooling", "num_results": 500})
    assert r.status_code == 422
    r = c.post("/api/operations-intelligence", json={"question": "hi", "sql": "SELECT 1"})
    assert r.status_code == 422  # unknown fields rejected


def test_upstream_errors_are_clean(fake_sql, fake_search, monkeypatch):
    from backend.errors import WarehouseUnavailable

    def boom(*a, **k):
        raise WarehouseUnavailable()

    monkeypatch.setattr(reliability, "run_query", boom)
    r = TestClient(main.app).get("/api/reliability")
    assert r.status_code == 503 and r.json()["error"]["code"] == "WAREHOUSE_UNAVAILABLE"
