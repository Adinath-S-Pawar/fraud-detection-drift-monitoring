import { useEffect, useState } from 'react'
import { refreshDriftStatus } from '../api'

async function getDriftStatus() {
  const res = await fetch('http://localhost:8000/drift-status')
  return res.json()
}

export default function DriftPanel() {
  const [drift, setDrift] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    getDriftStatus()
      .then(setDrift)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const handleRefresh = async () => {
  setRefreshing(true)
  try {
    const fresh = await refreshDriftStatus()
    setDrift(fresh)
  } catch (err) {
    setError(err.message)
  } finally {
    setRefreshing(false)
  }
}

  if (error) {
    return (
      <div className="bg-console-panel border border-console-border rounded-xl p-5">
        <p className="text-red-400 text-sm">{error}</p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="bg-console-panel border border-console-border rounded-xl p-5 animate-pulse">
        <div className="h-4 bg-console-border rounded w-24 mb-4"></div>
        <div className="h-8 bg-console-border rounded w-16"></div>
      </div>
    )
  }

  if (drift?.error) {
    return (
      <div className="bg-console-panel border border-console-border rounded-xl p-5">
        <h2 className="font-display text-lg font-medium mb-2">Drift Status</h2>
        <p className="text-console-muted text-sm">{drift.error}</p>
      </div>
    )
  }

  const sharePct = (drift.drift_share * 100).toFixed(1)
  const isHealthy = drift.drift_share < 0.1
  const isReliable = drift.reliable

  return (
    <div className="bg-console-panel border border-console-border rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-console-border">
        <h2 className="font-display text-lg font-medium">Drift Status</h2>
        <div className="flex items-center gap-2">
        <button
      onClick={handleRefresh}
      disabled={refreshing}
      className="px-3 py-1 text-xs rounded-md border border-console-border text-console-muted hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition"
    >
      {refreshing ? 'Checking...' : 'Check Now'}
    </button>
        <span className={`px-2 py-0.5 rounded-full text-xs border whitespace-nowrap ${
        !drift.reliable
          ? 'text-console-muted bg-console-muted/10 border-console-muted/30'
          : isHealthy
            ? 'text-emerald-400 bg-emerald-400/10 border-emerald-400/30'
            : 'text-amber-400 bg-amber-400/10 border-amber-400/30'
      }`}>
        {!drift.reliable ? 'Low Sample' : isHealthy ? 'Stable' : 'Attention'}
      </span>
        </div>
      </div>

      
      <div className="p-5 space-y-4">
        {!drift.reliable && (
        <div className="bg-amber-400/10 border border-amber-400/30 rounded-lg px-3 py-2 text-xs text-amber-400">
          Sample size ({drift.n_current_rows} rows) is below the recommended minimum ({drift.min_reliable_sample_size}) for reliable drift detection. Results may be noisy.
        </div>
      )}

        <div className="flex items-baseline gap-2">
          <span className="font-mono text-3xl font-medium">{sharePct}%</span>
          <span className="text-console-muted text-sm">of columns drifted</span>
        </div>

        <div className="text-xs text-console-muted font-mono">
          {drift.n_current_rows.toLocaleString()} live rows vs {drift.n_reference_rows.toLocaleString()} reference rows
        </div>

        {drift.drifted_columns.length > 0 && (
          <div className="pt-2 border-t border-console-border">
            <p className="text-xs uppercase tracking-wide text-console-muted mb-2">Drifted columns</p>
            <div className="space-y-1.5">
              {drift.drifted_columns.map((col) => (
                <div key={col.column} className="flex items-center justify-between text-sm">
                  <span className="font-mono text-xs">{col.column}</span>
                  <span className="font-mono text-xs text-amber-400">{col.score.toFixed(4)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {drift.timestamp && (
          <p className="text-xs text-console-muted pt-1">
            Last checked: {new Date(drift.timestamp).toLocaleString()}
          </p>
        )}
      </div>
    </div>
  )
}