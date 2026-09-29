import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { linkifyCitations } from '../lib/citations'
import { analysis, asset360 } from '../test/fixtures'
import Asset360 from './Asset360'
import OperationsIntelligence from './OperationsIntelligence'

function mockFetch(routes: Record<string, { status?: number; body: unknown }>) {
  const fn = vi.fn(async (url: string, _init?: RequestInit) => {
    const key = Object.keys(routes).find((k) => url.startsWith(k))
    const r = key ? routes[key] : { status: 404, body: { error: { code: 'NOT_FOUND', message: 'nope' } } }
    return new Response(JSON.stringify(r.body), { status: r.status ?? 200 })
  })
  vi.stubGlobal('fetch', fn)
  return fn
}

function renderAt(path: string, route: string, el: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path={route} element={el} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

afterEach(() => vi.unstubAllGlobals())

describe('citations', () => {
  it('linkifies S1/D# labels but leaves existing links alone', () => {
    expect(linkifyCitations('a [S1] b [D12] c [D1](x)')).toBe('a [S1](#cite-S1) b [D12](#cite-D12) c [D1](x)')
  })
})

describe('Asset 360', () => {
  it('renders identity, disclaimer, timeline, work orders and Operations Intelligence action', async () => {
    mockFetch({
      '/api/assets/TX-184': { body: asset360 },
      '/api/meta/document-types': { body: { document_types: ['POLICY'] } },
      '/api/knowledge/search': { body: { results: [] } },
    })
    renderAt('/assets/TX-184', '/assets/:assetId', <Asset360 />)
    expect(await screen.findByText('Operating & condition metrics')).toBeInTheDocument()
    expect(screen.getByRole('note', { name: 'Risk score disclaimer' })).toHaveTextContent(/heuristic/)
    expect(screen.getByText('Minor airflow degradation.')).toBeInTheDocument()
    expect(screen.getByText('WO-2841')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Analyze this asset in Operations Intelligence/ })).toHaveAttribute(
      'href',
      '/operations-intelligence?asset=TX-184',
    )
    expect(await screen.findByText('No evidence found')).toBeInTheDocument()
  })

  it('shows a clean unknown-asset message without retry', async () => {
    mockFetch({
      '/api/assets/TX-999': {
        status: 404,
        body: { error: { code: 'UNKNOWN_ASSET', message: "No asset 'TX-999' exists in the Blue River Power portfolio." } },
      },
    })
    renderAt('/assets/TX-999', '/assets/:assetId', <Asset360 />)
    expect(await screen.findByText('Asset not found')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Retry' })).not.toBeInTheDocument()
  })
})

describe('Operations Intelligence', () => {
  it('sends the scoped question and renders answer, chips, sources and warnings', async () => {
    const fetchFn = mockFetch({ '/api/operations-intelligence': { body: analysis } })
    renderAt('/operations-intelligence?asset=TX-184', '/operations-intelligence', <OperationsIntelligence />)
    expect(screen.getByText('Asset TX-184')).toBeInTheDocument()
    await userEvent.type(screen.getByLabelText('Question'), 'Why did TX-184 need maintenance?')
    await userEvent.click(screen.getByRole('button', { name: 'Analyze' }))

    expect(await screen.findByText('Generated synthesis')).toBeInTheDocument()
    const body = JSON.parse(fetchFn.mock.calls[0][1]!.body as string)
    expect(body).toEqual({ question: 'Why did TX-184 need maintenance?', asset_id: 'TX-184' })

    expect(screen.getByRole('button', { name: 'Citation D1' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Unverified citation D7' })).toBeInTheDocument()
    expect(screen.getByText('Field Inspection Report — TX-184')).toBeInTheDocument()
    expect(screen.getByText('Retrieved but not cited (1)')).toBeInTheDocument()
    expect(screen.getByText(/do not match any retrieved source/)).toBeInTheDocument()
    // only the file name is shown; no storage location is rendered
    expect(screen.getByText('INS-1.pdf')).toBeInTheDocument()
    expect(document.body.textContent).not.toMatch(/dbfs:|\/Volumes\/|s3:\/\//)
    expect(screen.getByRole('note', { name: 'Risk score disclaimer' })).toBeInTheDocument()
    expect(document.body.textContent).not.toMatch(/[{}]"/) // no raw JSON

    await userEvent.click(screen.getByRole('button', { name: 'Citation D1' }))
    await waitFor(() => expect(document.getElementById('source-D1')).toHaveClass('highlighted'))
  })

  it('shows a non-technical model-unavailable message', async () => {
    mockFetch({
      '/api/operations-intelligence': {
        status: 503,
        body: { error: { code: 'MODEL_UNAVAILABLE', message: 'The answer-generation model is temporarily unavailable.' } },
      },
    })
    renderAt('/operations-intelligence', '/operations-intelligence', <OperationsIntelligence />)
    await userEvent.click(screen.getAllByRole('button', { name: /TX-184 considered high risk/ })[0])
    expect(await screen.findByText('Answer generation unavailable')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
  })
})
