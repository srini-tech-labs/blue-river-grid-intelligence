from ..cache import ttl_cache
from ..db import queries
from ..db.sql import run_query


@ttl_cache()
def get_reliability_summary() -> dict:
    rows = run_query(queries.RELIABILITY_KPIS)
    if not rows:
        return {"saidi": None, "saifi": None, "caidi": None, "customer_base": None,
                "period": None, "as_of_date": None, "synthetic": True}
    r = rows[0]
    return {
        "saidi": r["saidi_minutes"],
        "saifi": r["saifi_interruptions"],
        "caidi": r["caidi_minutes"],
        "customer_base": r["synthetic_customer_base"],
        "period": f"as of {r['as_of_date']}",
        "as_of_date": r["as_of_date"],
        "outage_events": r["outage_events"],
        "customer_interruptions": r["customer_interruptions"],
        "customer_interruption_minutes": r["customer_interruption_minutes"],
        "synthetic": True,
    }


@ttl_cache()
def get_operations_summary() -> dict:
    agg = run_query(queries.PORTFOLIO_AGGREGATES)
    maint = run_query(queries.MAINTENANCE_SUMMARY)
    return {"portfolio": agg[0] if agg else {}, "maintenance": maint, "synthetic": True}
