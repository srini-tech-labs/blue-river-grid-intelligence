import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import App from './App'

describe('app shell', () => {
  it('shows the app name and the synthetic-environment label', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
    render(
      <QueryClientProvider client={new QueryClient()}>
        <MemoryRouter>
          <App />
        </MemoryRouter>
      </QueryClientProvider>,
    )
    expect(screen.getByText('Blue River Grid Intelligence')).toBeInTheDocument()
    expect(screen.getAllByRole('note')[0]).toHaveTextContent(/not a real utility/i)
  })
})
