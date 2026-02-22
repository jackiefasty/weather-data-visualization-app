import { useState } from 'react'
import SearchBar from './components/SearchBar'
import './App.css'
import WeatherCharts from './components/WeatherCharts'
import AIPatternsPanel from './components/AIPatternsPanel'
import type { WeatherData, LocationResult } from './types'

const API_BASE = import.meta.env.VITE_API_URL || ''

function App() {
  const [weatherData, setWeatherData] = useState<WeatherData | null>(null)
  const [aiPatterns, setAiPatterns] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchWeatherByCoords = async (lat: number, lon: number) => {
    setLoading(true)
    setError(null)
    try {
      const [weatherRes, aiRes] = await Promise.all([
        fetch(`${API_BASE}/api/weather?lat=${lat}&lon=${lon}`),
        fetch(`${API_BASE}/api/ai-patterns?lat=${lat}&lon=${lon}`),
      ])
      if (!weatherRes.ok) throw new Error('Failed to fetch weather')
      const weather = await weatherRes.json()
      setWeatherData(weather)
      if (aiRes.ok) {
        const ai = await aiRes.json()
        setAiPatterns(ai)
      } else {
        setAiPatterns(null)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      setWeatherData(null)
      setAiPatterns(null)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async (query: string, selected?: LocationResult) => {
    setLoading(true)
    setError(null)
    try {
      if (selected) {
        await fetchWeatherByCoords(selected.lat, selected.lon)
      } else {
        const res = await fetch(`${API_BASE}/api/weather/by-address?q=${encodeURIComponent(query)}`)
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || 'Location not found')
        }
        const data = await res.json()
        setWeatherData(data)
        const aiRes = await fetch(`${API_BASE}/api/ai-patterns?lat=${data.latitude}&lon=${data.longitude}`)
        if (aiRes.ok) {
          setAiPatterns(await aiRes.json())
        } else {
          setAiPatterns(null)
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      setWeatherData(null)
      setAiPatterns(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Weather Data Visualization</h1>
        <p>Cloud cover & lightning probability • SMHI data • Nordic region</p>
      </header>

      <SearchBar onSearch={handleSearch} loading={loading} />

      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      {loading && (
        <div className="loading">Loading weather data…</div>
      )}

      {weatherData && !loading && (
        <>
          <WeatherCharts data={weatherData} />
          {aiPatterns && <AIPatternsPanel patterns={aiPatterns} />}
        </>
      )}

      {!weatherData && !loading && !error && (
        <div className="empty-state">
          Enter an address, city, postal code, or coordinates (e.g. 58.0, 16.0) to view cloud cover and lightning probability.
          <br />
          <small>Note: SMHI API covers Nordic region (Sweden, Norway, Finland, etc.)</small>
        </div>
      )}
    </div>
  )
}

export default App
