import { useEffect, useState } from 'react'

function App() {
  const [modelInfo, setModelInfo] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('http://localhost:8000/model-info')
      .then((res) => res.json())
      .then(setModelInfo)
      .catch((err) => setError(err.message))
  }, [])

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">
      <h1 className="text-3xl font-bold mb-6">Fraud Drift Dashboard</h1>
      {error && <p className="text-red-400">Error: {error}</p>}
      {modelInfo && (
        <div className="bg-gray-900 rounded-lg p-4 max-w-sm">
          <p>Live version: <span className="font-mono">{modelInfo.live_version}</span></p>
          <p>ROC-AUC: {modelInfo.roc_auc.toFixed(4)}</p>
          <p>PR-AUC: {modelInfo.pr_auc.toFixed(4)}</p>
        </div>
      )}
    </div>
  )
}

export default App