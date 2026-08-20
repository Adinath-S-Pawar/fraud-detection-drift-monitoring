import { useEffect, useState } from 'react'
import { getModelInfo } from './api'
import PredictionsTable from './components/PredictionsTable'

function App() {
  const [modelInfo, setModelInfo] = useState(null)

  useEffect(() => {
    getModelInfo().then(setModelInfo)
  }, [])

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <header className="border-b border-[var(--border)] px-8 py-5 flex items-center justify-between">
        <div>
          <h1 className="font-display text-xl font-bold tracking-tight">Fraud Detection Console</h1>
          <p className="text-[var(--muted)] text-sm mt-0.5">Real-time monitoring & drift oversight</p>
        </div>
        {modelInfo && (
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[var(--info)] animate-pulse" />
              <span className="font-mono text-[var(--info)]">{modelInfo.live_version}</span>
            </div>
            <div className="text-[var(--muted)] font-mono text-xs">
              PR-AUC {modelInfo.pr_auc.toFixed(3)}
            </div>
          </div>
        )}
      </header>

      <main className="p-8 max-w-6xl mx-auto space-y-6">
        <PredictionsTable />
      </main>
    </div>
  )
}

export default App