import { useEffect, useState } from 'react'
import { getPredictions } from '../api'

function riskLevel(prob) {
  if (prob >= 0.5) return { label: 'High', color: 'text-red-400 bg-red-400/10 border-red-400/30' }
  if (prob >= 0.15) return { label: 'Elevated', color: 'text-amber-400 bg-amber-400/10 border-amber-400/30' }
  return { label: 'Normal', color: 'text-slate-400 bg-slate-400/10 border-slate-400/20' }
}

export default function PredictionsTable() {
  const [predictions, setPredictions] = useState([])
  const [sortByRisk, setSortByRisk] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    getPredictions(sortByRisk, 25)
      .then(setPredictions)
      .finally(() => setLoading(false))
  }, [sortByRisk])

  return (
    <div className="bg-console-panel border border-console-border rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-console-border">
        <h2 className="font-display text-lg font-medium">Live Predictions</h2>
        <div className="flex gap-1 bg-black/30 rounded-lg p-1">
          <button
            onClick={() => setSortByRisk(false)}
            className={`px-3 py-1 text-sm rounded-md transition ${!sortByRisk ? 'bg-console-info/15 text-console-info' : 'text-console-muted hover:text-white'}`}
          >
            Recent
          </button>
          <button
            onClick={() => setSortByRisk(true)}
            className={`px-3 py-1 text-sm rounded-md transition ${sortByRisk ? 'bg-console-info/15 text-console-info' : 'text-console-muted hover:text-white'}`}
          >
            Highest Risk
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-console-muted text-xs uppercase tracking-wide border-b border-console-border">
              <th className="px-5 py-3 font-medium">Time</th>
              <th className="px-5 py-3 font-medium">Probability</th>
              <th className="px-5 py-3 font-medium">Risk</th>
              <th className="px-5 py-3 font-medium">Top Signal</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={4} className="px-5 py-8 text-center text-console-muted">Loading...</td></tr>
            ) : predictions.length === 0 ? (
              <tr><td colSpan={4} className="px-5 py-8 text-center text-console-muted">No predictions logged yet.</td></tr>
            ) : (
              predictions.map((p) => {
                const risk = riskLevel(p.fraud_probability)
                const topFeature = Object.entries(p.top_shap_contributors)[0]
                return (
                  <tr key={p.id} className="border-b border-console-border/60 hover:bg-white/[0.02] transition">
                    <td className="px-5 py-3 font-mono text-console-muted text-xs">
                      {new Date(p.timestamp).toLocaleString()}
                    </td>
                    <td className="px-5 py-3 font-mono">{(p.fraud_probability * 100).toFixed(2)}%</td>
                    <td className="px-5 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs border ${risk.color}`}>
                        {risk.label}
                      </span>
                    </td>
                    <td className="px-5 py-3 font-mono text-xs text-console-muted">
                      {topFeature ? topFeature[0].replace(/^(num|cat)__/, '') : '—'}
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}