import { Link, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { EmptyState } from './components/States'
import Asset360 from './pages/Asset360'
import AssetIndex from './pages/AssetIndex'
import CommandCenter from './pages/CommandCenter'
import OperationsIntelligence from './pages/OperationsIntelligence'

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<CommandCenter />} />
        <Route path="/assets" element={<AssetIndex />} />
        <Route path="/assets/:assetId" element={<Asset360 />} />
        <Route path="/operations-intelligence" element={<OperationsIntelligence />} />
        <Route
          path="*"
          element={
            <EmptyState title="Page not found">
              <Link to="/">Back to the Command Center</Link>
            </EmptyState>
          }
        />
      </Routes>
    </AppShell>
  )
}
