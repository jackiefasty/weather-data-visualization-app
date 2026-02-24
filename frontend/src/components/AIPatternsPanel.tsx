
interface Pattern {
  name: string
  probability: number
}

interface AIPatternsData {
  patterns: Pattern[]
  convective_risk: number
  summary: string
}

interface AIPatternsPanelProps {
  patterns: Record<string, unknown>
}

export default function AIPatternsPanel({ patterns }: AIPatternsPanelProps) {
  const data = patterns as unknown as AIPatternsData
  if (!data?.patterns?.length) return null

  return (
    <section className="ai-patterns-section">
      <h2>AI Atmospheric Pattern Analysis</h2>
      <p className="ai-summary">{data.summary}</p>
      <div className="risk-badge">
        Convective / Lightning Risk: <strong>{(data.convective_risk * 100).toFixed(1)}%</strong>
      </div>
      <div className="patterns-grid">
        {data.patterns.map((p) => (
          <div key={p.name} className="pattern-card">
            <span className="pattern-name">{p.name.replace(/_/g, ' ')}</span>
            <div className="pattern-bar">
              <div
                className="pattern-fill"
                style={{ width: `${p.probability * 100}%` }}
              />
            </div>
            <span className="pattern-pct">{(p.probability * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>
      <p className="ai-note">
        Deep learning model trained on SMHI historical data to identify non-linear atmospheric patterns.
      </p>
    </section>
  )
}
