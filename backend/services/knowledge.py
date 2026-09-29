"""HYBRID retrieval against the existing AI Search index (no other search stack)."""

import json
import logging
import re

from databricks.sdk.errors import DatabricksError

from ..config import get_settings, get_workspace_client
from ..errors import SearchUnavailable

log = logging.getLogger(__name__)

# Document types present in the frozen index (see docs/stage3-port-notes.md).
DOCUMENT_TYPES = (
    "EMAIL_THREAD",
    "HISTORICAL_FINDING",
    "INSPECTION_REPORT",
    "OPERATOR_NOTE",
    "POLICY",
    "RCA_REPORT",
    "STORM_REPORT",
)

# Same retrieval columns as Stage 3 (10_hybrid_retrieval). `source_uri` is retrieved
# for internal use only (to derive a file name); it never leaves the backend.
COLUMNS = [
    "chunk_id",
    "chunk_to_retrieve",
    "document_id",
    "document_type",
    "title",
    "asset_id",
    "substation_id",
    "work_order_id",
    "event_id",
    "document_date",
    "source_uri",
]

MAX_RESULTS = 20


def hybrid_search(query: str, filters: dict | None, num_results: int) -> list[dict]:
    """Raw HYBRID search; returns rows keyed by column name (score dropped)."""
    index = get_settings().require_index()
    try:
        resp = get_workspace_client().vector_search_indexes.query_index(
            index_name=index,
            columns=COLUMNS,
            query_text=query,
            query_type="HYBRID",
            filters_json=json.dumps(filters) if filters else None,
            num_results=num_results,
        )
    except DatabricksError as exc:
        log.error("AI Search query failed: %s", exc)
        raise SearchUnavailable() from exc

    names = [c.name for c in (resp.manifest.columns or [])] if resp.manifest else COLUMNS
    rows = (resp.result.data_array if resp.result else None) or []
    return [{k: v for k, v in zip(names, row) if k in COLUMNS} for row in rows]


_SAFE_FILE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def source_file(uri: str | None) -> str | None:
    """Basename only (e.g. 'IR-TX184-20260614.pdf'); never a storage path or location."""
    if not uri:
        return None
    name = str(uri).replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
    return name if _SAFE_FILE_RE.match(name) else None


def to_source(row: dict) -> dict:
    """Public source metadata. Internal storage locations are deliberately excluded."""
    return {
        "chunk_id": row.get("chunk_id"),
        "document_id": row.get("document_id"),
        "document_type": row.get("document_type"),
        "title": row.get("title"),
        "asset_id": row.get("asset_id"),
        "work_order_id": row.get("work_order_id"),
        "document_date": row.get("document_date"),
        "source_file": source_file(row.get("source_uri")),
        "content": row.get("chunk_to_retrieve"),
    }


def search_knowledge(query: str, asset_id: str | None, document_type: str | None, num_results: int) -> dict:
    filters = {}
    if asset_id:
        filters["asset_id"] = asset_id
    if document_type:
        filters["document_type"] = document_type
    rows = hybrid_search(query, filters or None, num_results)
    return {"results": [to_source(r) for r in rows], "synthetic": True}
