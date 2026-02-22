import { useMemo, useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  AreaChart,
  Area,
} from 'recharts'
import { format, parseISO } from 'date-fns'
import type { WeatherData, TimeSeriesPoint } from '../types'

type AggregationType = 'hourly' | 'daily' | 'monthly'

interface ChartDataPoint {
  label: string
  cloud_cover_pct: number
  lightning_prob_pct: number
  timestamp: string
}

function aggregateData(
  series: TimeSeriesPoint[],
  agg: AggregationType
): ChartDataPoint[] {
  if (agg === 'hourly' || series.length <= 24) {
    return series.map((p) => ({
      label: format(parseISO(p.timestamp), 'dd/MM HH:mm'),
      cloud_cover_pct: p.cloud_cover_pct,
      lightning_prob_pct: p.lightning_prob_pct,
      timestamp: p.timestamp,
    }))
  }
  const grouped: Record<string, { cloud: number[]; lightning: number[] }> = {}
  series.forEach((p) => {
    const d = parseISO(p.timestamp)
    const key =
      agg === 'daily'
        ? format(d, 'yyyy-MM-dd')
        : format(d, 'yyyy-MM')
    if (!grouped[key]) grouped[key] = { cloud: [], lightning: [] }
    grouped[key].cloud.push(p.cloud_cover_pct)
    grouped[key].lightning.push(p.lightning_prob_pct)
  })
  return Object.entries(grouped).map(([key, v]) => ({
    label: key,
    cloud_cover_pct: v.cloud.reduce((a, b) => a + b, 0) / v.cloud.length,
    lightning_prob_pct: v.lightning.reduce((a, b) => a + b, 0) / v.lightning.length,
    timestamp: key,
  }))
}

interface WeatherChartsProps {
  data: WeatherData
}

export default function WeatherCharts({ data }: WeatherChartsProps) {
  const [aggregation, setAggregation] = useState<AggregationType>('hourly')

  const chartData = useMemo(
    () => aggregateData(data.time_series, aggregation),
    [data.time_series, aggregation]
  )

  return (
    <section className="charts-section">
      <div className="charts-header">
        <h2>Cloud Cover & Lightning Probability</h2>
        {data.location && (
          <p className="location-name">{data.location}</p>
        )}
        <p className="coords-info">
          {data.latitude.toFixed(4)}, {data.longitude.toFixed(4)}
        </p>
        <div className="aggregation-tabs">
          {(['hourly', 'daily', 'monthly'] as const).map((agg) => (
            <button
              key={agg}
              className={aggregation === agg ? 'active' : ''}
              onClick={() => setAggregation(agg)}
            >
              {agg.charAt(0).toUpperCase() + agg.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="chart-grid">
        <div className="chart-card">
          <h3>Cloud Cover (%)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
              <XAxis dataKey="label" stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" domain={[0, 100]} fontSize={12} />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #475569' }}
                formatter={(value: number) => [`${value.toFixed(1)}%`, 'Cloud cover']}
                labelFormatter={(label) => label}
              />
              <Area
                type="monotone"
                dataKey="cloud_cover_pct"
                stroke="#38bdf8"
                fill="#38bdf8"
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Lightning Probability (%)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
              <XAxis dataKey="label" stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" domain={[0, 100]} fontSize={12} />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #475569' }}
                formatter={(value: number) => [`${value.toFixed(1)}%`, 'Lightning']}
                labelFormatter={(label) => label}
              />
              <Area
                type="monotone"
                dataKey="lightning_prob_pct"
                stroke="#fbbf24"
                fill="#fbbf24"
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="chart-card full-width">
        <h3>Combined View</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
            <XAxis dataKey="label" stroke="#94a3b8" fontSize={12} />
            <YAxis stroke="#94a3b8" domain={[0, 100]} fontSize={12} />
            <Tooltip
              contentStyle={{ background: '#1e293b', border: '1px solid #475569' }}
              formatter={(value: number, name: string) => [
                `${value.toFixed(1)}%`,
                name === 'cloud_cover_pct' ? 'Cloud cover' : 'Lightning',
              ]}
              labelFormatter={(label) => label}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="cloud_cover_pct"
              name="Cloud Cover %"
              stroke="#38bdf8"
              strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="lightning_prob_pct"
              name="Lightning %"
              stroke="#fbbf24"
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
