import type { StructuredEvidence } from '../api/types'
import { date, num } from '../lib/format'
import { LevelPill } from './Badges'

function Field({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="fact">
      <dt>{k}</dt>
      <dd>{v}</dd>
    </div>
  )
}

/** Human-readable view of the [S1] structured evidence — never raw JSON. */
export function StructuredFacts({ evidence }: { evidence: StructuredEvidence }) {
  if (evidence.scope === 'asset' && evidence.asset_summary) {
    const a = evidence.asset_summary
    return (
      <div>
        <dl className="facts">
          <Field k="Asset" v={a.asset_id} />
          <Field k="Substation" v={a.substation_id} />
          <Field k="Criticality" v={<LevelPill value={a.criticality} />} />
          <Field k="Age" v={`${num(a.asset_age_years)} yrs`} />
          <Field k="Avg / max utilization" v={`${num(a.avg_utilization_pct, 1)}% / ${num(a.max_utilization_pct, 1)}%`} />
          <Field k="Max top-oil temp." v={`${num(a.max_top_oil_temp_c, 1)} °C`} />
          <Field k="Thermal alerts" v={num(a.thermal_alert_count)} />
          <Field k="Outages" v={`${num(a.outage_count)} (${num(a.outage_minutes)} min)`} />
          <Field k="Customer interruptions" v={num(a.customer_interruptions)} />
          <Field k="Last maintenance" v={date(a.last_maintenance_date)} />
          <Field
            k="Prototype priority score"
            v={
              <>
                {num(a.risk_score, 1)} <LevelPill value={a.risk_band} />
              </>
            }
          />
        </dl>
        <div className="small muted" style={{ marginTop: 8 }}>
          Also included: {evidence.timeline?.length ?? 0} timeline events, {evidence.work_orders?.length ?? 0} work orders,{' '}
          {evidence.outages?.length ?? 0} outages.
        </div>
      </div>
    )
  }
  const r = evidence.reliability
  const p = evidence.portfolio
  return (
    <div>
      <dl className="facts">
        <Field k="SAIDI" v={`${num(r?.saidi, 1)} min`} />
        <Field k="SAIFI" v={num(r?.saifi, 3)} />
        <Field k="CAIDI" v={`${num(r?.caidi, 1)} min`} />
        <Field k="Customer base (synthetic)" v={num(r?.customer_base)} />
        <Field k="Assets" v={num(p?.asset_count)} />
        <Field k="Thermal alerts" v={num(p?.thermal_alerts)} />
        <Field k="Asset outages" v={num(p?.asset_outages)} />
        <Field k="Work orders" v={num(p?.work_orders)} />
      </dl>
      {evidence.priority_assets?.length ? (
        <div className="small muted" style={{ marginTop: 8 }}>
          Top priority assets included:{' '}
          {evidence.priority_assets
            .slice(0, 5)
            .map((a) => a.asset_id)
            .join(', ')}
          {evidence.priority_assets.length > 5 ? '…' : ''} · {evidence.maintenance?.length ?? 0} maintenance summary rows
        </div>
      ) : null}
    </div>
  )
}
