import { forwardRef } from 'react'
import type { DocumentSource } from '../api/types'
import { date, label, tidyExcerpt } from '../lib/format'

interface Props {
  source: DocumentSource
  citationLabel?: string
  cited?: boolean
  highlighted?: boolean
  excerptChars?: number
}

export const SourceCard = forwardRef<HTMLElement, Props>(function SourceCard(
  { source, citationLabel, cited, highlighted, excerptChars = 420 },
  ref,
) {
  const content = tidyExcerpt(source.content ?? '')
  const excerpt = content.length > excerptChars ? `${content.slice(0, excerptChars).trimEnd()}…` : content
  return (
    <article
      ref={ref}
      id={citationLabel ? `source-${citationLabel}` : undefined}
      className={`source ${highlighted ? 'highlighted' : ''} ${cited === false ? 'uncited' : ''}`}
    >
      <header className="source-head">
        {citationLabel && <span className="cite-tag">{citationLabel}</span>}
        <span className="source-title">{source.title ?? 'Untitled document'}</span>
      </header>
      <dl className="source-meta">
        <div>
          <dt>Type</dt>
          <dd>{label(source.document_type)}</dd>
        </div>
        <div>
          <dt>Date</dt>
          <dd>{date(source.document_date)}</dd>
        </div>
        {source.asset_id && (
          <div>
            <dt>Asset</dt>
            <dd>{source.asset_id}</dd>
          </div>
        )}
        {source.work_order_id && (
          <div>
            <dt>Work order</dt>
            <dd>{source.work_order_id}</dd>
          </div>
        )}
      </dl>
      {excerpt && <blockquote className="source-excerpt">{excerpt}</blockquote>}
      {source.source_file && <div className="source-file">{source.source_file}</div>}
    </article>
  )
})
