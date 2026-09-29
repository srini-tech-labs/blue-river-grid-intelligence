import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useOperationsIntelligence } from '../api/hooks'
import type { OperationsIntelligenceResponse } from '../api/types'
import { AnswerView } from '../components/AnswerView'
import { RiskDisclaimer } from '../components/Badges'
import { SourceCard } from '../components/SourceCard'
import { EmptyState, ErrorState } from '../components/States'
import { StructuredFacts } from '../components/StructuredFacts'

const PORTFOLIO_EXAMPLES = [
  'Why is TX-184 considered high risk, what led to the corrective maintenance decision, and was there evidence of the problem before June 2026?',
  'What policy applies to repeated elevated transformer temperature alerts and inspection escalation?',
  'Which assets show the most thermal stress across the portfolio, and what do the documents say about it?',
  'What happened after the cooling-system maintenance on TX-184?',
]

const assetExamples = (id: string) => [
  `Why is ${id} a priority asset, and what does the document evidence show?`,
  `What historical evidence shows ${id} had cooling or thermal concerns?`,
  `What led to the most recent corrective maintenance on ${id}?`,
  `What happened after maintenance on ${id}, and is any uncertainty remaining?`,
]

const MAX_LEN = 1000

export default function OperationsIntelligence() {
  const [searchParams, setSearchParams] = useSearchParams()
  const contextAsset = searchParams.get('asset')?.toUpperCase() || null
  const [question, setQuestion] = useState('')
  const mutation = useOperationsIntelligence()

  const examples = contextAsset ? assetExamples(contextAsset) : PORTFOLIO_EXAMPLES

  const ask = (q: string) => {
    const text = q.trim()
    if (text.length < 3 || mutation.isPending) return
    setQuestion(text)
    mutation.mutate({ question: text, asset_id: contextAsset })
  }

  const clearContext = () => {
    searchParams.delete('asset')
    setSearchParams(searchParams)
  }

  return (
    <div className="stack">
      <div className="page-head">
        <div>
          <h1 className="page-title">Operations Intelligence</h1>
          <p className="page-sub">
            Combines structured operational data <span className="cite-chip structured static">S1</span> with retrieved
            utility documents <span className="cite-chip static">D#</span> to provide grounded, source-linked explanations
            and investigation support.
          </p>
        </div>
      </div>

      <section className="card">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            ask(question)
          }}
          className="stack"
          style={{ gap: 10 }}
        >
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <div className="row" style={{ gap: 8 }}>
              <span className="small muted">Context:</span>
              {contextAsset ? (
                <span className="context-chip">
                  Asset {contextAsset}
                  <button type="button" onClick={clearContext} aria-label="Clear asset context">
                    ×
                  </button>
                </span>
              ) : (
                <span className="context-chip neutral">Portfolio · asset detected from question if named</span>
              )}
              {contextAsset && (
                <Link className="small" to={`/assets/${contextAsset}`}>
                  Open Asset 360
                </Link>
              )}
            </div>
            <span className="small muted">
              {question.length}/{MAX_LEN}
            </span>
          </div>
          <textarea
            className="input question"
            rows={3}
            maxLength={MAX_LEN}
            placeholder={contextAsset ? `Ask about ${contextAsset}…` : 'Ask about reliability, an asset, maintenance or policy…'}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) ask(question)
            }}
            aria-label="Question"
          />
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <div className="examples">
              {examples.map((ex) => (
                <button key={ex} type="button" className="example" onClick={() => ask(ex)} disabled={mutation.isPending}>
                  {ex}
                </button>
              ))}
            </div>
            <button className="btn btn-primary" type="submit" disabled={mutation.isPending || question.trim().length < 3}>
              {mutation.isPending ? 'Analyzing…' : 'Analyze'}
            </button>
          </div>
        </form>
      </section>

      {mutation.isPending && <PendingState />}
      {mutation.isError && (
        <section className="card">
          <ErrorState error={mutation.error} onRetry={() => ask(question)} />
        </section>
      )}
      {mutation.data && !mutation.isPending && <Result data={mutation.data} />}
      {mutation.isIdle && (
        <section className="card">
          <EmptyState title="Ask a question to begin">
            Answers typically take 20–40 seconds while facts are retrieved, documents are searched and a grounded answer is
            generated.
          </EmptyState>
        </section>
      )}
    </div>
  )
}

function PendingState() {
  const [elapsed, setElapsed] = useState(0)
  useEffect(() => {
    const t = setInterval(() => setElapsed((s) => s + 1), 1000)
    return () => clearInterval(t)
  }, [])
  return (
    <section className="card pending" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <div>
        <strong>Building a grounded answer</strong> <span className="muted small">{elapsed}s</span>
        <ol className="pipeline small">
          <li>Retrieve structured operational facts from Delta</li>
          <li>Search indexed documents (hybrid retrieval)</li>
          <li>Generate an answer that cites the evidence</li>
        </ol>
        {elapsed > 45 && <div className="small muted">Still working — the warehouse may be waking up.</div>}
      </div>
    </section>
  )
}

function Result({ data }: { data: OperationsIntelligenceResponse }) {
  const [active, setActive] = useState<string | null>(null)
  const refs = useRef<Record<string, HTMLElement | null>>({})
  const validLabels = useMemo(
    () => new Set(['S1', ...data.document_sources.map((d) => d.citation_label)]),
    [data.document_sources],
  )
  const cited = data.document_sources.filter((d) => d.cited)
  const uncited = data.document_sources.filter((d) => !d.cited)

  const focus = (label: string) => {
    setActive(label)
    refs.current[label]?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }

  const noAnswer = !data.answer.trim()

  return (
    <div className="analysis-result">
      <div className="stack">
        {data.warnings.length > 0 && (
          <div className="notice warn" role="status">
            <strong>Review notes</strong>
            <ul>
              {data.warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          </div>
        )}
        <section className="card">
          <div className="card-title">
            <span>
              Generated synthesis{' '}
              <span className="muted small">
                · {data.scope === 'asset' ? `scoped to ${data.asset_id}` : 'portfolio scope'} · Databricks-managed model via ai_query
              </span>
            </span>
            <span className="small muted">
              {data.citations.structured_cited ? 'S1 cited' : 'S1 not cited'} · {data.citations.document_labels_cited.length}{' '}
              of {data.document_sources.length} documents cited
            </span>
          </div>
          {noAnswer ? (
            <EmptyState title="No answer could be generated">
              The evidence that was retrieved is listed alongside. Try rephrasing, or name a specific asset.
            </EmptyState>
          ) : (
            <AnswerView answer={data.answer} validLabels={validLabels} onCite={focus} />
          )}
        </section>
        <RiskDisclaimer text={data.risk_disclaimer} />
      </div>

      <aside className="evidence-panel" aria-label="Evidence">
        <div className="panel-head">
          <strong>Evidence</strong>
          <span className="small muted">Observed facts & retrieved sources</span>
        </div>
        <article
          ref={(el) => {
            refs.current.S1 = el
          }}
          className={`source structured ${active === 'S1' ? 'highlighted' : ''}`}
        >
          <header className="source-head">
            <span className="cite-tag structured">S1</span>
            <span className="source-title">
              Structured operational data (Delta){data.structured_evidence.scope === 'asset' ? ` — ${data.asset_id}` : ' — portfolio'}
            </span>
          </header>
          <StructuredFacts evidence={data.structured_evidence} />
        </article>

        {data.document_sources.length === 0 && (
          <EmptyState title="No document evidence found">Only structured data was available for this question.</EmptyState>
        )}
        {cited.length > 0 && <div className="section-label">Cited documents ({cited.length})</div>}
        {cited.map((s) => (
          <SourceCard
            key={s.citation_label}
            ref={(el) => {
              refs.current[s.citation_label] = el
            }}
            source={s}
            citationLabel={s.citation_label}
            cited
            highlighted={active === s.citation_label}
          />
        ))}
        {uncited.length > 0 && <div className="section-label">Retrieved but not cited ({uncited.length})</div>}
        {uncited.map((s) => (
          <SourceCard
            key={s.citation_label}
            ref={(el) => {
              refs.current[s.citation_label] = el
            }}
            source={s}
            citationLabel={s.citation_label}
            cited={false}
            highlighted={active === s.citation_label}
            excerptChars={200}
          />
        ))}
      </aside>
    </div>
  )
}
