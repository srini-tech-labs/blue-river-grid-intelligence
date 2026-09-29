import { ApiError } from '../api/client'

export function Skeleton({ height = 16, width = '100%' }: { height?: number; width?: number | string }) {
  return <div className="skeleton" style={{ height, width }} aria-hidden="true" />
}

export function LoadingBlock({ lines = 4, label = 'Loading' }: { lines?: number; label?: string }) {
  return (
    <div className="stack" style={{ gap: 10 }} role="status" aria-label={label}>
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton key={i} width={`${90 - i * 12}%`} />
      ))}
    </div>
  )
}

const TITLES: Record<string, string> = {
  WAREHOUSE_UNAVAILABLE: 'Data warehouse is warming up',
  SEARCH_UNAVAILABLE: 'Document search unavailable',
  MODEL_UNAVAILABLE: 'Answer generation unavailable',
  UPSTREAM_TIMEOUT: 'This is taking longer than expected',
  UNKNOWN_ASSET: 'Asset not found',
  INVALID_REQUEST: 'Check your request',
  NETWORK: 'Connection problem',
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const e = error instanceof ApiError ? error : null
  const title = (e && TITLES[e.code]) || 'Something went wrong'
  const message = e?.message ?? 'Please try again.'
  return (
    <div className="state-box" role="alert">
      <h3>{title}</h3>
      <p className="small">{message}</p>
      {onRetry && (!e || e.retryable) && (
        <button className="btn" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  )
}

export function EmptyState({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <div className="state-box">
      <h3>{title}</h3>
      {children && <div className="small">{children}</div>}
    </div>
  )
}
