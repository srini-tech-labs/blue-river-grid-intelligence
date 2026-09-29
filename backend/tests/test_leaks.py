"""Internal storage paths must never reach API responses or the LLM prompt."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

from fastapi.testclient import TestClient

from backend import main
from backend.db import queries
from backend.services import knowledge

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from leak_scan import find_leaks  # noqa: E402

from .test_services import fake_search, fake_sql  # noqa: F401,E402  (pytest fixtures)

INTERNAL = "dbfs:/Volumes/workspace/brp_raw/landing/unstructured/inspections/IR-TX184-20260614.pdf"


def _index_row(**over):
    row = {c: f"v-{c}" for c in knowledge.COLUMNS}
    row.update(source_uri=INTERNAL, document_type="INSPECTION_REPORT", asset_id="TX-184")
    row.update(over)
    return row


def test_source_file_is_basename_only():
    assert knowledge.source_file(INTERNAL) == "IR-TX184-20260614.pdf"
    assert knowledge.source_file("s3://bucket/key/doc.pdf") == "doc.pdf"
    assert knowledge.source_file(None) is None
    assert knowledge.source_file("x/<script>.pdf") is None


def test_to_source_never_exposes_location():
    src = knowledge.to_source(_index_row())
    assert "source_uri" not in src
    assert src["source_file"] == "IR-TX184-20260614.pdf"
    assert find_leaks(json.dumps(src)) == []


def test_search_api_response_has_no_internal_paths(monkeypatch, fake_sql):  # noqa: F811
    def query_index(**kw):
        cols = knowledge.COLUMNS + ["score"]
        row = [_index_row()[c] for c in knowledge.COLUMNS] + [0.9]
        return NS(manifest=NS(columns=[NS(name=c) for c in cols]), result=NS(data_array=[row]))

    monkeypatch.setattr(knowledge, "get_settings", lambda: NS(require_index=lambda: "idx"))
    monkeypatch.setattr(knowledge, "get_workspace_client", lambda: NS(vector_search_indexes=NS(query_index=query_index)))
    r = TestClient(main.app).post("/api/knowledge/search", json={"query": "cooling", "asset_id": "TX-184"})
    assert r.status_code == 200
    assert "source_uri" not in r.text
    assert find_leaks(r.text) == []
    assert r.json()["results"][0]["source_file"] == "IR-TX184-20260614.pdf"


def test_operations_intelligence_response_and_prompt_have_no_internal_paths(monkeypatch, fake_sql):  # noqa: F811
    monkeypatch.setattr(knowledge, "hybrid_search", lambda q, f, n: [_index_row(chunk_id=f"c{i}") for i in range(3)])
    fake_sql.answer = "[S1] facts [D1] [D2] " + "x" * 300
    r = TestClient(main.app).post("/api/operations-intelligence", json={"question": "Why did TX-184 need maintenance?"})
    assert r.status_code == 200
    assert "source_uri" not in r.text
    assert find_leaks(r.text) == []

    prompt = [c for c in fake_sql.calls if c[0] == queries.AI_QUERY][0][1]["prompt"]
    assert "Source URI" not in prompt
    assert "dbfs:" not in prompt and "/Volumes/" not in prompt
    assert find_leaks(prompt) == []
    assert "Source file: IR-TX184-20260614.pdf" in prompt


def test_leak_patterns_catch_internal_values_but_not_templates():
    must_flag = [
        INTERNAL, "/Volumes/workspace/x", "s3://bucket/key", "abfss://c@acct.dfs.core.windows.net/x",
        "https://abc-123.cloud.databricks.com", "dbc-a1b2c3d4", "my-app-123.aws.databricksapps.com",
        "dapi" + "0" * 32, "Bearer abcdefghijklmnopqrstuvwxyz0123", "/home/someone/project", "/Users/someone/x",
        "someone@gmail.com", "/Workspace/Users/someone@example.com/apps", "Traceback (most recent call last)",
    ]
    for value in must_flag:
        assert find_leaks(value), value
    must_pass = ['echo "/Workspace/Users/$me/apps"', "a@users.noreply.github.com", "IR-TX184-20260614.pdf"]
    for value in must_pass:
        assert find_leaks(value) == [], value
    assert find_leaks("wh 1234abcd5678", {"warehouse id": "1234abcd5678"}) == ["warehouse id"]
