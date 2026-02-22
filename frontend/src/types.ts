export interface LocationResult {
  lat: number
  lon: number
  display_name: string
  type?: string
  importance?: number
}

export interface TimeSeriesPoint {
  timestamp: string
  cloud_cover_pct: number
  lightning_prob_pct: number
}

export interface WeatherData {
  approvedTime?: string
  referenceTime?: string
  longitude: number
  latitude: number
  location?: string
  time_series: TimeSeriesPoint[]
}
