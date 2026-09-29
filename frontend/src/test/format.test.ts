import { describe, expect, it } from 'vitest'
import { label, tidyExcerpt } from '../lib/format'

describe('format', () => {
  it('labels keep acronyms', () => {
    expect(label('DGA_TREND')).toBe('DGA trend')
    expect(label('RCA_REPORT')).toBe('RCA report')
    expect(label('INSPECTION_REPORT')).toBe('Inspection report')
  })
  it('tidies excerpt padding', () => {
    expect(tidyExcerpt('a\n\n\nb  \n\nc')).toBe('a\nb\nc')
  })
})
