const nf = (digits: number) => new Intl.NumberFormat('en-US', { maximumFractionDigits: digits })

export function num(v: number | null | undefined, digits = 0): string {
  return v === null || v === undefined || Number.isNaN(v) ? '—' : nf(digits).format(v)
}

export function money(v: number | null | undefined): string {
  return v === null || v === undefined
    ? '—'
    : new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(v)
}

export function date(v: string | null | undefined): string {
  if (!v) return '—'
  const d = new Date(v.length === 10 ? `${v}T00:00:00` : v)
  return Number.isNaN(d.getTime())
    ? v
    : d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

export function dateTime(v: string | null | undefined): string {
  if (!v) return '—'
  const d = new Date(v)
  return Number.isNaN(d.getTime())
    ? v
    : d.toLocaleString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const ACRONYMS = new Set(['DGA', 'RCA', 'MVA', 'KV', 'SCADA', 'P1', 'P2', 'P3'])

/** 'INSPECTION_REPORT' -> 'Inspection report'; keeps known acronyms ('DGA_TREND' -> 'DGA trend'). */
export function label(v: string | null | undefined): string {
  if (!v) return '—'
  const words = v.split('_').map((w) => (ACRONYMS.has(w.toUpperCase()) ? w.toUpperCase() : w.toLowerCase()))
  const s = words.join(' ')
  return s.charAt(0).toUpperCase() + s.slice(1)
}

/** Collapse the blank-line padding that parsed PDF chunks carry. */
export function tidyExcerpt(text: string): string {
  return text.replace(/[ \t]+\n/g, '\n').replace(/\n{2,}/g, '\n').trim()
}

export function levelClass(v: string | null | undefined): 'high' | 'medium' | 'low' | '' {
  const s = (v ?? '').toUpperCase()
  if (s === 'HIGH' || s === 'P1' || s === 'CRITICAL') return 'high'
  if (s === 'MEDIUM' || s === 'P2') return 'medium'
  if (s === 'LOW' || s === 'P3') return 'low'
  return ''
}
