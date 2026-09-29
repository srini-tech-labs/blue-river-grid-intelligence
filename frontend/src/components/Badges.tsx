import { label, levelClass } from '../lib/format'

/** Level pill: color is always paired with the text label (never color alone). */
export function LevelPill({ value, prefix }: { value: string | null | undefined; prefix?: string }) {
  return (
    <span className={`pill ${levelClass(value)}`}>
      {prefix ? `${prefix} ` : ''}
      {label(value)}
    </span>
  )
}

export function RiskDisclaimer({ text, compact }: { text: string; compact?: boolean }) {
  return (
    <div className={`notice ${compact ? 'small' : ''}`} role="note" aria-label="Risk score disclaimer">
      <strong>Prototype heuristic.</strong> {text}
    </div>
  )
}
