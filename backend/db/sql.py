"""Statement Execution API wrapper.

- Statements are server-defined (see queries.py); values are bound only
  through named parameter markers (`:name`).
- Concurrency is deliberately conservative for a small Free Edition warehouse.
- Long statements (warehouse cold start, ai_query) are polled up to a deadline
  and cancelled if it is exceeded.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

from databricks.sdk.errors import DatabricksError
from databricks.sdk.service.sql import (
    Disposition,
    ExecuteStatementRequestOnWaitTimeout,
    Format,
    StatementParameterListItem,
    StatementState,
)

from ..config import get_settings, get_workspace_client
from ..errors import AppError, UpstreamTimeout, WarehouseUnavailable

log = logging.getLogger(__name__)

# At most two statements in flight from this app process at once.
_SQL_SLOTS = threading.BoundedSemaphore(2)

_POLL_INTERVAL_S = 1.0

Param = Any  # a plain value, or a (value, sql_type) tuple


def _to_param_items(params: dict[str, Param] | None) -> list[StatementParameterListItem]:
    items = []
    for name, spec in (params or {}).items():
        value, sql_type = spec if isinstance(spec, tuple) else (spec, None)
        if sql_type is None:
            sql_type = "INT" if isinstance(value, int) and not isinstance(value, bool) else "STRING"
        items.append(
            StatementParameterListItem(
                name=name, value=None if value is None else str(value), type=sql_type
            )
        )
    return items


_INT_TYPES = {"INT", "LONG", "SHORT", "BYTE", "BIGINT", "SMALLINT", "TINYINT", "INTEGER"}
_FLOAT_TYPES = {"DOUBLE", "FLOAT", "DECIMAL"}


def _convert(value: str | None, type_name: str | None) -> Any:
    if value is None:
        return None
    t = (type_name or "").upper()
    try:
        if t in _INT_TYPES:
            return int(value)
        if t in _FLOAT_TYPES:
            return float(value)
        if t == "BOOLEAN":
            return value.lower() == "true"
    except ValueError:
        return value
    return value


def run_query(
    statement: str,
    params: dict[str, Param] | None = None,
    *,
    timeout_s: float = 60.0,
    row_limit: int = 1000,
    failure_error: type[AppError] = WarehouseUnavailable,
) -> list[dict[str, Any]]:
    """Execute a server-defined statement and return rows as dicts.

    `failure_error` is raised when the statement itself FAILS (e.g. pass
    ModelUnavailable for ai_query statements).
    """
    warehouse_id = get_settings().require_warehouse()
    w = get_workspace_client()
    deadline = time.monotonic() + timeout_s

    with _SQL_SLOTS:
        try:
            resp = w.statement_execution.execute_statement(
                statement=statement,
                warehouse_id=warehouse_id,
                parameters=_to_param_items(params),
                wait_timeout="30s",
                on_wait_timeout=ExecuteStatementRequestOnWaitTimeout.CONTINUE,
                disposition=Disposition.INLINE,
                format=Format.JSON_ARRAY,
                row_limit=row_limit,
            )
            while resp.status and resp.status.state in (StatementState.PENDING, StatementState.RUNNING):
                if time.monotonic() > deadline:
                    try:
                        w.statement_execution.cancel_execution(resp.statement_id)
                    except DatabricksError:
                        log.warning("cancel failed for timed-out statement")
                    raise UpstreamTimeout()
                time.sleep(_POLL_INTERVAL_S)
                resp = w.statement_execution.get_statement(resp.statement_id)
        except DatabricksError as exc:
            log.error("statement execution error: %s", exc)
            raise WarehouseUnavailable() from exc

        state = resp.status.state if resp.status else None
        if state != StatementState.SUCCEEDED:
            err = resp.status.error if resp.status else None
            log.error("statement %s: %s", state, err.message if err else "no detail")
            raise failure_error()

        columns = [(c.name, c.type_name.value if c.type_name else None) for c in resp.manifest.schema.columns]
        rows: list[list[str | None]] = list((resp.result and resp.result.data_array) or [])
        next_chunk = resp.result.next_chunk_index if resp.result else None
        while next_chunk is not None:
            chunk = w.statement_execution.get_statement_result_chunk_n(resp.statement_id, next_chunk)
            rows.extend(chunk.data_array or [])
            next_chunk = chunk.next_chunk_index

    return [{name: _convert(v, t) for (name, t), v in zip(columns, row)} for row in rows]
