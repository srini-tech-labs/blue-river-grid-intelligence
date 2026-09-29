"""Every SQL statement the app can run. Server-defined; values bind via :params.

Object names are fixed constants here and are never derived from request input.
"""

G = "workspace.brp_gold"
S = "workspace.brp_silver"

RELIABILITY_KPIS = f"""
SELECT as_of_date, outage_events, customer_interruptions, customer_interruption_minutes,
       synthetic_customer_base, saidi_minutes, saifi_interruptions, caidi_minutes
FROM {G}.reliability_kpis
ORDER BY as_of_date DESC
LIMIT 1
"""

_ASSET_COLUMNS = """
asset_id, asset_type, substation_id, manufacturer, install_date, asset_age_years, rated_mva,
primary_kv, secondary_kv, criticality, status, avg_utilization_pct, max_utilization_pct,
avg_top_oil_temp_c, max_top_oil_temp_c, thermal_alert_count, outage_count, outage_minutes,
customer_interruptions, total_mw_interrupted, work_order_count, last_maintenance_date,
maintenance_cost, risk_score, risk_band
"""

PRIORITY_ASSETS = f"""
SELECT {_ASSET_COLUMNS}
FROM {G}.asset_operational_summary
ORDER BY risk_score DESC, asset_id
LIMIT :limit
"""

ASSET_IDS = f"SELECT asset_id FROM {G}.asset_operational_summary"

ASSET_SUMMARY = f"""
SELECT {_ASSET_COLUMNS}
FROM {G}.asset_operational_summary
WHERE asset_id = :asset_id
"""

ASSET_TIMELINE = f"""
SELECT record_id, event_date, event_type, severity, component, summary AS description
FROM {G}.asset_event_timeline
WHERE asset_id = :asset_id
ORDER BY event_date, record_id
LIMIT 500
"""

ASSET_WORK_ORDERS = f"""
SELECT work_order_id, created_date, completed_date, priority, work_type, component, status,
       estimated_cost, actual_cost, summary
FROM {S}.work_orders
WHERE asset_id = :asset_id
ORDER BY created_date, work_order_id
LIMIT 500
"""

ASSET_OUTAGES = f"""
SELECT outage_id, start_ts, end_ts, duration_minutes, customers_affected, mw_interrupted,
       cause_category, reportable
FROM {S}.outage_events
WHERE asset_id = :asset_id
ORDER BY start_ts, outage_id
LIMIT 500
"""

MAINTENANCE_SUMMARY = f"""
SELECT component, work_type, priority, work_order_count, actual_cost, avg_days_to_complete
FROM {G}.maintenance_summary
ORDER BY work_order_count DESC, component, work_type, priority
LIMIT 100
"""

PORTFOLIO_AGGREGATES = f"""
SELECT count(*) AS asset_count,
       count_if(risk_band = 'HIGH') AS high_band_assets,
       count_if(criticality = 'HIGH') AS high_criticality_assets,
       sum(thermal_alert_count) AS thermal_alerts,
       sum(outage_count) AS asset_outages,
       sum(outage_minutes) AS outage_minutes,
       sum(work_order_count) AS work_orders,
       sum(maintenance_cost) AS maintenance_cost
FROM {G}.asset_operational_summary
"""

# The validated Stage 3 generation path: system.ai model through ai_query on the warehouse.
AI_QUERY = "SELECT ai_query('system.ai.gpt-oss-20b', :prompt) AS answer"
