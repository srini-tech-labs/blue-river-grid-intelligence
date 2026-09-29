import { useMemo, useState } from 'react'
import { usePriorityAssets } from '../api/hooks'
import { RiskDisclaimer } from '../components/Badges'
import { PriorityAssetsTable } from '../components/PriorityAssetsTable'
import { EmptyState, ErrorState, LoadingBlock } from '../components/States'

export default function AssetIndex() {
  const q = usePriorityAssets(100)
  const [filter, setFilter] = useState('')
  const rows = useMemo(() => {
    const f = filter.trim().toUpperCase()
    return (q.data?.assets ?? []).filter(
      (a) => !f || a.asset_id.includes(f) || a.substation_id?.toUpperCase().includes(f) || a.criticality?.includes(f),
    )
  }, [q.data, filter])

  return (
    <div className="stack">
      <div className="page-head">
        <div>
          <h1 className="page-title">Asset 360</h1>
          <p className="page-sub">Select an asset to see its condition, history, maintenance and document evidence.</p>
        </div>
        <input
          className="input"
          style={{ width: 280 }}
          placeholder="Filter by asset, substation, criticality"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          aria-label="Filter assets"
        />
      </div>
      <section className="card">
        {q.isPending && <LoadingBlock lines={8} />}
        {q.isError && <ErrorState error={q.error} onRetry={() => q.refetch()} />}
        {q.data && (
          <div className="stack">
            {rows.length ? (
              <PriorityAssetsTable assets={rows} />
            ) : (
              <EmptyState title="No matching assets">Try a different filter.</EmptyState>
            )}
            <RiskDisclaimer text={q.data.disclaimer} compact />
          </div>
        )}
      </section>
    </div>
  )
}
