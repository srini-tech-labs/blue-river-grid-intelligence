import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError } from '../api/client'
import { useAsset360, useDocumentTypes, useKnowledgeSearch, type SearchParams } from '../api/hooks'
import type { Asset360 as Asset360Data, Outage, TimelineEvent, WorkOrder } from '../api/types'
import { LevelPill, RiskDisclaimer } from '../components/Badges'
import { MetricTile } from '../components/KpiCard'
import { SourceCard } from '../components/SourceCard'
import { EmptyState, ErrorState, LoadingBlock } from '../components/States'
import { date, dateTime, label, money, num } from '../lib/format'

export default function Asset360() {
  const { assetId = '' } = useParams()
  const id = assetId.toUpperCase()
  const q = useAsset360(id)

  if (q.isPending)
    return (
      <div className="stack">
        <h1 className="page-title">{id}</h1>
        <div className="card">
          <LoadingBlock lines={6} label="Loading asset" />
        </div>
      </div>
    )
  if (q.isError) {
    const unknown = q.error instanceof ApiError && q.error.code === 'UNKNOWN_ASSET'
    return (
      <div className="card">
        <ErrorState error={q.error} onRetry={unknown ? undefined : () => q.refetch()} />
        {unknown && (
          <p className="state-box small">
            <Link to="/assets">Browse all assets</Link>
          </p>
        )}
      </div>
    )
  }
  return <AssetView data={q.data} />
}

function AssetView({ data }: { data: Asset360Data }) {
  const a = data.asset_summary
  return (
    <div className="stack">
      <div className="page-head">
        <div>
          <div className="crumbs small">
            <Link to="/assets">Asset 360</Link> / {a.asset_id}
          </div>
          <h1 className="page-title">
            {a.asset_id} <span className="title-sub">{label(a.asset_type)}</span>
          </h1>
          <p className="page-sub">
            Substation <strong>{a.substation_id}</strong> · <LevelPill value={a.criticality} prefix="Criticality:" /> ·{' '}
            {a.manufacturer} · {num(a.rated_mva)} MVA · {num(a.primary_kv)}/{num(a.secondary_kv, 1)} kV · status{' '}
            {label(a.status)}
          </p>
        </div>
        <Link className="btn btn-primary" to={`/operations-intelligence?asset=${a.asset_id}`}>
          Analyze this asset in Operations Intelligence
        </Link>
      </div>

      <div className="asset-top">
        <section className="card">
          <div className="card-title">Operating & condition metrics</div>
          <div className="metric-grid">
            <MetricTile label="Asset age" value={`${num(a.asset_age_years)} yrs`} sub={`Installed ${date(a.install_date)}`} />
            <MetricTile
              label="Utilization"
              value={`${num(a.avg_utilization_pct, 1)}%`}
              sub={`avg · max ${num(a.max_utilization_pct, 1)}%`}
            />
            <MetricTile
              label="Top-oil temperature"
              value={`${num(a.max_top_oil_temp_c, 1)} °C`}
              sub={`max · avg ${num(a.avg_top_oil_temp_c, 1)} °C`}
            />
            <MetricTile label="Thermal alerts" value={num(a.thermal_alert_count)} />
            <MetricTile label="Outages" value={num(a.outage_count)} sub={`${num(a.outage_minutes)} outage minutes`} />
            <MetricTile
              label="Customer interruptions"
              value={num(a.customer_interruptions)}
              sub={`${num(a.total_mw_interrupted, 1)} MW interrupted`}
            />
            <MetricTile label="Work orders" value={num(a.work_order_count)} sub={`last maintenance ${date(a.last_maintenance_date)}`} />
            <MetricTile label="Maintenance cost" value={money(a.maintenance_cost)} />
          </div>
        </section>
        <section className="card risk-card">
          <div className="card-title">Prototype priority score</div>
          <div className="risk-score">
            {num(a.risk_score, 1)}
            <span className="kpi-unit">/ 100</span>
          </div>
          <LevelPill value={a.risk_band} prefix="Band:" />
          <div style={{ marginTop: 14 }}>
            <RiskDisclaimer text={data.risk_disclaimer} />
          </div>
        </section>
      </div>

      <div className="asset-main">
        <section className="card">
          <div className="card-title">
            Event timeline <span className="muted small">{data.timeline.length} events · oldest first</span>
          </div>
          <Timeline events={data.timeline} />
        </section>
        <div className="stack">
          <HistoryTabs workOrders={data.work_orders} outages={data.outages} />
          <RelatedDocuments assetId={a.asset_id} />
        </div>
      </div>
    </div>
  )
}

function Timeline({ events }: { events: TimelineEvent[] }) {
  if (!events.length) return <EmptyState title="No recorded events" />
  return (
    <ol className="timeline">
      {events.map((e, i) => (
        <li key={e.record_id ?? i} className={`tl-item sev-${(e.severity ?? '').toLowerCase()}`}>
          <div className="tl-date">{date(e.event_date)}</div>
          <div className="tl-body">
            <div className="row" style={{ gap: 8 }}>
              <strong>{label(e.event_type)}</strong>
              <LevelPill value={e.severity} />
              <span className="muted small">{label(e.component)}</span>
            </div>
            <div className="tl-desc">{e.description}</div>
          </div>
        </li>
      ))}
    </ol>
  )
}

function HistoryTabs({ workOrders, outages }: { workOrders: WorkOrder[]; outages: Outage[] }) {
  const [tab, setTab] = useState<'wo' | 'out'>('wo')
  return (
    <section className="card">
      <div className="tabs" role="tablist">
        <button role="tab" aria-selected={tab === 'wo'} className={tab === 'wo' ? 'active' : ''} onClick={() => setTab('wo')}>
          Work orders ({workOrders.length})
        </button>
        <button role="tab" aria-selected={tab === 'out'} className={tab === 'out' ? 'active' : ''} onClick={() => setTab('out')}>
          Outages ({outages.length})
        </button>
      </div>
      {tab === 'wo' ? (
        workOrders.length ? (
          <div className="stack" style={{ gap: 10 }}>
            {workOrders.map((w) => (
              <div key={w.work_order_id} className="record">
                <div className="row" style={{ gap: 8 }}>
                  <strong>{w.work_order_id}</strong>
                  <LevelPill value={w.priority} />
                  <span className="pill">{label(w.work_type)}</span>
                  <span className="muted small">{label(w.component)}</span>
                </div>
                <div className="small">{w.summary}</div>
                <div className="small muted">
                  Created {date(w.created_date)} · completed {date(w.completed_date)} · {label(w.status)} · actual{' '}
                  {money(w.actual_cost)} (est. {money(w.estimated_cost)})
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="No work orders recorded" />
        )
      ) : outages.length ? (
        <table className="data compact">
          <thead>
            <tr>
              <th>Start</th>
              <th className="num">Minutes</th>
              <th className="num">Customers</th>
              <th className="num">MW</th>
              <th>Cause</th>
            </tr>
          </thead>
          <tbody>
            {outages.map((o) => (
              <tr key={o.outage_id}>
                <td>
                  {dateTime(o.start_ts)}
                  {o.reportable && <span className="pill" style={{ marginLeft: 6 }}>Reportable</span>}
                </td>
                <td className="num">{num(o.duration_minutes)}</td>
                <td className="num">{num(o.customers_affected)}</td>
                <td className="num">{num(o.mw_interrupted, 1)}</td>
                <td>{label(o.cause_category)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <EmptyState title="No outages recorded" />
      )}
    </section>
  )
}

const DEFAULT_DOC_QUERY = 'inspection findings thermal condition maintenance history'

function RelatedDocuments({ assetId }: { assetId: string }) {
  const types = useDocumentTypes()
  const [draft, setDraft] = useState(DEFAULT_DOC_QUERY)
  const [docType, setDocType] = useState('')
  const [params, setParams] = useState<SearchParams>({ query: DEFAULT_DOC_QUERY, asset_id: assetId, num_results: 6 })
  const q = useKnowledgeSearch(params)

  const run = (query = draft, document_type = docType) =>
    setParams({ query, asset_id: assetId, document_type: document_type || null, num_results: 6 })

  return (
    <section className="card">
      <div className="card-title">
        Related document evidence <span className="muted small">AI Search · hybrid</span>
      </div>
      <form
        className="row"
        style={{ marginBottom: 12 }}
        onSubmit={(e) => {
          e.preventDefault()
          run()
        }}
      >
        <input
          className="input"
          style={{ flex: 1, minWidth: 180 }}
          value={draft}
          maxLength={500}
          onChange={(e) => setDraft(e.target.value)}
          aria-label="Document search query"
        />
        <select
          className="input"
          value={docType}
          onChange={(e) => {
            setDocType(e.target.value)
            run(draft, e.target.value)
          }}
          aria-label="Document type"
        >
          <option value="">All types</option>
          {types.data?.document_types.map((t) => (
            <option key={t} value={t}>
              {label(t)}
            </option>
          ))}
        </select>
        <button className="btn" type="submit" disabled={draft.trim().length < 2}>
          Search
        </button>
      </form>
      {q.isFetching && <LoadingBlock lines={3} label="Searching documents" />}
      {q.isError && !q.isFetching && <ErrorState error={q.error} onRetry={() => q.refetch()} />}
      {q.data && !q.isFetching &&
        (q.data.results.length ? (
          <div className="stack" style={{ gap: 10 }}>
            {q.data.results.map((s, i) => (
              <SourceCard key={s.chunk_id ?? i} source={s} excerptChars={260} />
            ))}
          </div>
        ) : (
          <EmptyState title="No evidence found">No indexed documents match this search for {assetId}.</EmptyState>
        ))}
    </section>
  )
}
