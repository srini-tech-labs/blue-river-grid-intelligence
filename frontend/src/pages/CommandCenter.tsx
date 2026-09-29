import { Link } from 'react-router-dom'
import { useOperationsSummary, usePriorityAssets, useReliability } from '../api/hooks'
import type { MaintenanceRow } from '../api/types'
import { LevelPill, RiskDisclaimer } from '../components/Badges'
import { KpiCard } from '../components/KpiCard'
import { PriorityAssetsTable } from '../components/PriorityAssetsTable'
import { ErrorState, LoadingBlock, Skeleton } from '../components/States'
import { label, money, num } from '../lib/format'

function ReliabilityKpis() {
  const q = useReliability()
  if (q.isPending)
    return (
      <div className="kpi-row">
        {Array.from({ length: 4 }, (_, i) => (
          <div key={i} className="card kpi">
            <Skeleton height={14} width="50%" />
            <div style={{ height: 10 }} />
            <Skeleton height={32} width="60%" />
          </div>
        ))}
      </div>
    )
  if (q.isError) return <div className="card"><ErrorState error={q.error} onRetry={() => q.refetch()} /></div>
  const r = q.data
  return (
    <div className="kpi-row">
      <KpiCard label="SAIDI" value={num(r.saidi, 1)} unit="min" hint="Avg. interruption minutes per customer" />
      <KpiCard label="SAIFI" value={num(r.saifi, 3)} unit="int." hint="Avg. interruptions per customer" />
      <KpiCard label="CAIDI" value={num(r.caidi, 1)} unit="min" hint="Avg. restoration time per interruption" />
      <KpiCard
        label="Synthetic customer base"
        value={num(r.customer_base)}
        hint={
          <>
            {num(r.outage_events)} outage events · {r.period}
          </>
        }
      />
    </div>
  )
}

function OperationalSummary() {
  const q = useOperationsSummary()
  return (
    <section className="card">
      <div className="card-title">Operational summary</div>
      {q.isPending && <LoadingBlock lines={3} />}
      {q.isError && <ErrorState error={q.error} onRetry={() => q.refetch()} />}
      {q.data && (
        <>
          <div className="summary-strip">
            <Stat label="Assets monitored" value={num(q.data.portfolio.asset_count)} />
            <Stat label="High priority band" value={num(q.data.portfolio.high_band_assets)} />
            <Stat label="High-criticality assets" value={num(q.data.portfolio.high_criticality_assets)} />
            <Stat label="Thermal alerts" value={num(q.data.portfolio.thermal_alerts)} />
            <Stat label="Asset outages" value={num(q.data.portfolio.asset_outages)} />
            <Stat label="Work orders" value={num(q.data.portfolio.work_orders)} />
            <Stat label="Maintenance spend" value={money(q.data.portfolio.maintenance_cost)} />
          </div>
          <MaintenanceBreakdown rows={q.data.maintenance} />
        </>
      )}
    </section>
  )
}

function Stat({ label: l, value }: { label: string; value: string }) {
  return (
    <div className="stat">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{l}</div>
    </div>
  )
}

function MaintenanceBreakdown({ rows }: { rows: MaintenanceRow[] }) {
  if (!rows.length) return null
  const max = Math.max(...rows.map((r) => r.work_order_count), 1)
  return (
    <div style={{ marginTop: 16 }}>
      <div className="section-label">Maintenance by component</div>
      <table className="data compact">
        <thead>
          <tr>
            <th>Component</th>
            <th>Work type</th>
            <th>Priority</th>
            <th style={{ width: '30%' }}>Work orders</th>
            <th className="num">Actual cost</th>
            <th className="num">Avg. days</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={`${r.component}-${r.work_type}-${r.priority}`}>
              <td>{label(r.component)}</td>
              <td>{label(r.work_type)}</td>
              <td>
                <LevelPill value={r.priority} />
              </td>
              <td>
                <div className="score-cell">
                  <div className="score-bar" aria-hidden="true">
                    <span style={{ width: `${(100 * r.work_order_count) / max}%` }} />
                  </div>
                  <span className="score-num">{num(r.work_order_count)}</span>
                </div>
              </td>
              <td className="num">{money(r.actual_cost)}</td>
              <td className="num">{num(r.avg_days_to_complete, 1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function PriorityAssets() {
  const q = usePriorityAssets(10)
  const top = q.data?.assets[0]
  return (
    <section className="card">
      <div className="card-title">
        <span>Priority assets</span>
        <Link to="/assets" className="small">
          All assets →
        </Link>
      </div>
      {q.isPending && <LoadingBlock lines={6} />}
      {q.isError && <ErrorState error={q.error} onRetry={() => q.refetch()} />}
      {q.data && (
        <div className="stack">
          {top && (
            <div className="callout">
              <div>
                <div className="section-label">Highest priority</div>
                <div className="callout-title">
                  {top.asset_id} <LevelPill value={top.risk_band} prefix="Band:" />
                </div>
                <div className="small muted">
                  {top.substation_id} · {label(top.criticality)} criticality · {num(top.thermal_alert_count)} thermal alerts ·{' '}
                  {num(top.outage_count)} outages
                </div>
              </div>
              <div className="row">
                <Link className="btn" to={`/assets/${top.asset_id}`}>
                  Open Asset 360
                </Link>
                <Link className="btn btn-primary" to={`/operations-intelligence?asset=${top.asset_id}`}>
                  Investigate
                </Link>
              </div>
            </div>
          )}
          <PriorityAssetsTable assets={q.data.assets} />
          <RiskDisclaimer text={q.data.disclaimer} compact />
        </div>
      )}
    </section>
  )
}

export default function CommandCenter() {
  return (
    <div className="stack">
      <div className="page-head">
        <div>
          <h1 className="page-title">Reliability Command Center</h1>
          <p className="page-sub">Portfolio reliability, priority assets and maintenance activity for the synthetic Blue River Power grid.</p>
        </div>
      </div>
      <ReliabilityKpis />
      <PriorityAssets />
      <OperationalSummary />
    </div>
  )
}
