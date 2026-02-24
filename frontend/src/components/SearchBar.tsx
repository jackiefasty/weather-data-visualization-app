import { useState, useCallback, useEffect, useRef } from 'react'
import type { LocationResult } from '../types'

const API_BASE = import.meta.env.VITE_API_URL || ''

interface SearchBarProps {
  onSearch: (query: string, selected?: LocationResult) => void
  loading: boolean
}

export default function SearchBar({ onSearch, loading }: SearchBarProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<LocationResult[]>([])
  const [showResults, setShowResults] = useState(false)
  const [selectedResult, setSelectedResult] = useState<LocationResult | null>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout>>()

  const searchLocations = useCallback(async () => {
    if (query.trim().length < 2) return
    try {
      const res = await fetch(
        `${API_BASE}/api/search?q=${encodeURIComponent(query.trim())}`
      )
      if (!res.ok) return
      const data = await res.json()
      setResults(data.results || [])
      setShowResults(true)
      setSelectedResult(null)
    } catch {
      setResults([])
    }
  }, [query])

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([])
      setShowResults(false)
      return
    }
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      searchLocations()
    }, 300)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [query, searchLocations])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    if (selectedResult) {
      onSearch(query, selectedResult)
      setShowResults(false)
    } else {
      onSearch(query)
      setShowResults(false)
    }
  }

  const handleSelect = (r: LocationResult) => {
    setSelectedResult(r)
    setQuery(r.display_name)
    setShowResults(false)
    onSearch(r.display_name, r)
  }

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <div className="search-input-wrapper">
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setShowResults(false)
          }}
          onBlur={() => setTimeout(() => setShowResults(false), 200)}
          onFocus={() => results.length > 0 && setShowResults(true)}
          placeholder="Address, city, postal code, or coordinates (e.g. Stockholm, 12345, 59.3, 18.0)"
          disabled={loading}
          autoComplete="off"
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Loading…' : 'Search'}
        </button>
      </div>
      {showResults && results.length > 0 && (
        <ul className="search-results">
          {results.map((r, i) => (
            <li
              key={i}
              onClick={() => handleSelect(r)}
              onMouseDown={(e) => e.preventDefault()}
            >
              <strong>{r.display_name}</strong>
              <span className="coords">{r.lat.toFixed(4)}, {r.lon.toFixed(4)}</span>
            </li>
          ))}
        </ul>
      )}
    </form>
  )
}
