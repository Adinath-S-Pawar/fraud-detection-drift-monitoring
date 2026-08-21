import { useEffect, useState } from 'react'
import { getModelInfo } from './api'
import PredictionsTable from './components/PredictionsTable'
import DriftPanel from './components/DriftPanel'
import ShapDetail from './components/ShapDetail'

function App() {
  const [modelInfo, setModelInfo] = useState(null)
  const [selectedPrediction, setSelectedPrediction] = useState(null)

  useEffect(() => {
    getModelInfo().then(setModelInfo)
  }, [])

  return (
    <div className="min-h-screen bg-console-bg text-console-text">
      <header className="border-b border-console-border px-8 py-5 flex items-center justify-between">
        <div>
          <h1 className="font-display text-xl font-bold tracking-tight">Fraud Detection Console</h1>
          <p className="text-console-muted text-sm mt-0.5">Real-time monitoring & drift oversight</p>
        </div>
        {modelInfo && (
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-console-info animate-pulse" />
              <span className="font-mono text-console-info">{modelInfo.live_version}</span>
            </div>
            <div className="text-console-muted font-mono text-xs">
              PR-AUC {modelInfo.pr_auc.toFixed(3)}
            </div>
          </div>
        )}
      </header>

    <main className="p-8 max-w-6xl mx-auto space-y-6">
  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <div className="lg:col-span-2">
      <PredictionsTable onSelectRow={setSelectedPrediction} selectedId={selectedPrediction?.id} />
    </div>
    <div>
      <DriftPanel />
    </div>
  </div>
</main>
<ShapDetail prediction={selectedPrediction} onClose={() => setSelectedPrediction(null)} />
    </div>
  )
}

export default App