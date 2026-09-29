import { useNavigate } from 'react-router-dom'
import type { AssetSummary } from '../api/types'
import { num } from '../lib/format'
import { LevelPill } from './Badges'

export function PriorityAssetsTable({ assets, compact }: { assets: AssetSummary[]; compact?: boolean }) {
  const navigate = useNavigate()
  const max = Math.max(...assets.map((a) => a.risk_score ?? 0), 1)
  return (
    <table className="data">
      <thead>
        <tr>
          <th>#</th>
          <th>Asset</th>
          <th>Substation</th>
          <th>Criticality</th>
          {!compact && <th className="num">Age (yrs)</th>}
          <th className="num">Max util.</th>
          <th className="num">Max top-oil</th>
          <th className="num">Thermal alerts</th>
          <th className="num">Outages</th>
          <th style={{ width: 170 }}>Priority score</th>
        </tr>
      </thead>
      <tbody>
        {assets.map((a, i) => (
          <tr
            key={a.asset_id}
            className="clickable"
            tabIndex={0}
            onClick={() => navigate(`/assets/${a.asset_id}`)}
            onKeyDown={(e) => e.key === 'Enter' && navigate(`/assets/${a.asset_id}`)}
            aria-label={`Open Asset 360 for ${a.asset_id}`}
          >
            <td className="muted">{i + 1}</td>
            <td>
              <strong>{a.asset_id}</strong>
            </td>
            <td>{a.substation_id}</td>
            <td>
              <LevelPill value={a.criticality} />
            </td>
            {!compact && <td className="num">{num(a.asset_age_years)}</td>}
            <td className="num">{num(a.max_utilization_pct, 1)}%</td>
            <td className="num">{num(a.max_top_oil_temp_c, 1)} °C</td>
            <td className="num">{num(a.thermal_alert_count)}</td>
            <td className="num">{num(a.outage_count)}</td>
            <td>
              <div className="score-cell">
                <div className="score-bar" aria-hidden="true">
                  <span style={{ width: `${(100 * (a.risk_score ?? 0)) / max}%` }} />
                </div>
                <span className="score-num">{num(a.risk_score, 1)}</span>
                <LevelPill value={a.risk_band} />
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
