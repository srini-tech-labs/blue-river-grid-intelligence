from types import SimpleNamespace as NS

import pytest
from databricks.sdk.service.sql import StatementState

from backend.db import sql
from backend.errors import ModelUnavailable, UpstreamTimeout


class FakeStatements:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.cancelled = False

    def execute_statement(self, **kw):
        self.calls.append(kw)
        return self.responses.pop(0)

    def get_statement(self, _id):
        return self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]

    def cancel_execution(self, _id):
        self.cancelled = True


def _resp(state, rows=None, cols=None):
    cols = cols or []
    return NS(
        statement_id="s1",
        status=NS(state=state, error=None),
        manifest=NS(schema=NS(columns=[NS(name=n, type_name=NS(value=t)) for n, t in cols])),
        result=NS(data_array=rows, next_chunk_index=None),
    )


@pytest.fixture
def fake(monkeypatch):
    def install(*responses):
        stmts = FakeStatements(responses)
        monkeypatch.setattr(sql, "get_workspace_client", lambda: NS(statement_execution=stmts))
        monkeypatch.setattr(sql, "get_settings", lambda: NS(require_warehouse=lambda: "wh"))
        monkeypatch.setattr(sql, "_POLL_INTERVAL_S", 0)
        return stmts

    return install


def test_params_are_bound_not_interpolated_and_types_converted(fake):
    stmts = fake(_resp(StatementState.SUCCEEDED, [["TX-184", "3", "0.5", None]],
                       [("asset_id", "STRING"), ("n", "INT"), ("x", "DOUBLE"), ("z", "STRING")]))
    rows = sql.run_query("SELECT * FROM t WHERE asset_id = :asset_id LIMIT :lim", {"asset_id": "TX-184'; DROP", "lim": 5})
    call = stmts.calls[0]
    assert "DROP" not in call["statement"]
    by_name = {p.name: p for p in call["parameters"]}
    assert by_name["asset_id"].value == "TX-184'; DROP" and by_name["asset_id"].type == "STRING"
    assert by_name["lim"].type == "INT"
    assert rows == [{"asset_id": "TX-184", "n": 3, "x": 0.5, "z": None}]


def test_polls_until_success(fake):
    fake(_resp(StatementState.PENDING), _resp(StatementState.RUNNING),
         _resp(StatementState.SUCCEEDED, [["1"]], [("a", "INT")]))
    assert sql.run_query("SELECT 1") == [{"a": 1}]


def test_timeout_cancels(fake):
    stmts = fake(_resp(StatementState.RUNNING))
    with pytest.raises(UpstreamTimeout):
        sql.run_query("SELECT 1", timeout_s=0)
    assert stmts.cancelled


def test_failed_statement_raises_requested_error(fake):
    fake(_resp(StatementState.FAILED))
    with pytest.raises(ModelUnavailable):
        sql.run_query("SELECT ai_query(...)", failure_error=ModelUnavailable)
