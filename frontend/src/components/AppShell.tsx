import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'

export function SyntheticBanner() {
  return (
    <div className="synthetic-banner" role="note">
      <strong>Synthetic environment.</strong> All data belongs to the fictional Blue River Power portfolio used for
      demonstration. Blue River Power is not a real utility.
    </div>
  )
}

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="shell">
      <SyntheticBanner />
      <header className="topbar">
        <div className="brand">
          <img src="/favicon.svg" alt="" width={28} height={28} />
          <div>
            <div className="brand-name">Blue River Grid Intelligence</div>
            <div className="brand-sub">Blue River Power · synthetic portfolio</div>
          </div>
        </div>
        <nav className="nav" aria-label="Primary">
          <NavLink to="/" end>
            Command Center
          </NavLink>
          <NavLink to="/assets">Asset 360</NavLink>
          <NavLink to="/operations-intelligence">Operations Intelligence</NavLink>
        </nav>
      </header>
      <main className="content">{children}</main>
    </div>
  )
}
