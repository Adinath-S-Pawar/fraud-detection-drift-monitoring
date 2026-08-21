import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Rectangle } from 'recharts'

function ColoredBar(props) {
  const { fill, ...rest } = props
  const color = props.value > 0 ? '#EF4444' : '#38BDF8'
  return <Rectangle {...rest} fill={color} />
}

export default function ShapDetail({ prediction }) {
  if (!prediction) {
    return (
      <div className="bg-console-panel border border-console-border rounded-xl p-8 flex items-center justify-center h-full min-h-[200px]">
        <p className="text-console-muted text-sm">Select a prediction to see its explanation.</p>
      </div>
    )
  }

  const chartData = Object.entries(prediction.top_shap_contributors)
    .map(([feature, value]) => ({
      feature: feature.replace(/^(num|cat)__/, ''),
      value,
    }))
    .sort((a, b) => a.value - b.value)

  return (
    <div className="bg-console-panel border border-console-border rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-console-border">
        <h2 className="font-display text-lg font-medium">Prediction Explanation</h2>
        <p className="text-console-muted text-xs font-mono mt-1">
          {new Date(prediction.timestamp).toLocaleString()} · {(prediction.fraud_probability * 100).toFixed(2)}% fraud probability
        </p>
      </div>

      <div className="p-5">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#262E3D" horizontal={false} />
            <XAxis type="number" tick={{ fill: '#8A93A3', fontSize: 11 }} axisLine={{ stroke: '#262E3D' }} />
            <YAxis
              type="category"
              dataKey="feature"
              tick={{ fill: '#E7E9EC', fontSize: 11, fontFamily: 'JetBrains Mono' }}
              width={150}
              axisLine={{ stroke: '#262E3D' }}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]} shape={<ColoredBar />} />
          </BarChart>
        </ResponsiveContainer>

        <div className="flex items-center gap-4 mt-3 text-xs text-console-muted">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-red-400" /> Pushes toward fraud
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-sky-400" /> Pushes away from fraud
          </div>
        </div>
      </div>
    </div>
  )
}