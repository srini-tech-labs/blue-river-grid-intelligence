from concurrent.futures import ThreadPoolExecutor

from ..cache import ttl_cache
from ..config import RISK_DISCLAIMER
from ..db import queries
from ..db.sql import run_query
from ..errors import UnknownAsset
from . import asset_resolver

MAX_LIMIT = 100


@ttl_cache()
def get_high_risk_assets(limit: int = 10) -> dict:
    rows = run_query(queries.PRIORITY_ASSETS, {"limit": limit})
    return {"assets": rows, "disclaimer": RISK_DISCLAIMER, "synthetic": True}


@ttl_cache()
def get_asset_timeline(asset_id: str) -> dict:
    asset_id = asset_resolver.validate(asset_id)
    return {"asset_id": asset_id, "timeline": run_query(queries.ASSET_TIMELINE, {"asset_id": asset_id})}


@ttl_cache()
def get_asset_360(asset_id: str) -> dict:
    asset_id = asset_resolver.validate(asset_id)
    summary = run_query(queries.ASSET_SUMMARY, {"asset_id": asset_id})
    if not summary:
        raise UnknownAsset(asset_id)
    # Limited parallelism (2): measured ~4.0s -> ~1.5s median on the Free Edition
    # warehouse with no instability; run_query also caps in-flight statements at 2.
    params = {"asset_id": asset_id}
    with ThreadPoolExecutor(max_workers=2) as pool:
        timeline, work_orders, outages = pool.map(
            lambda q: run_query(q, params),
            (queries.ASSET_TIMELINE, queries.ASSET_WORK_ORDERS, queries.ASSET_OUTAGES),
        )
    return {
        "asset_summary": summary[0],
        "timeline": timeline,
        "work_orders": work_orders,
        "outages": outages,
        "risk_disclaimer": RISK_DISCLAIMER,
        "synthetic": True,
    }
