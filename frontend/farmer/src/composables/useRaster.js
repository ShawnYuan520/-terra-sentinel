import { ref } from 'vue'
import api from '../api'

export function useRaster() {
  const soilProfile = ref(null)
  const weather = ref(null)
  const forecast = ref(null)
  const decision = ref(null)
  const ndviData = ref([])
  const loading = ref(false)

  async function queryPoint(lon, lat) {
    loading.value = true
    try {
      const [soilRes, decRes, weatherRes] = await Promise.all([
        api.get('/raster/soil-profile', { params: { lon, lat } }),
        api.get('/raster/decision', { params: { lon, lat, crop: '玉米', area_mu: 100 } }),
        api.get('/weather/current', { params: { lat, lon } }),
      ])
      soilProfile.value = soilRes.data
      decision.value = decRes.data
      weather.value = weatherRes.data
    } catch {} finally {
      loading.value = false
    }
  }

  async function fetchWeather(lat, lon) {
    try {
      const { data } = await api.get('/weather/current', { params: { lat, lon } })
      weather.value = data
    } catch {}
  }

  async function fetchForecast(lat, lon) {
    try {
      const { data } = await api.get('/weather/forecast', { params: { lat, lon } })
      forecast.value = data
    } catch {}
  }

  async function fetchNDVI(fieldId) {
    try {
      const { data } = await api.get(`/geo/ndvi/${fieldId}`)
      ndviData.value = Array.isArray(data) ? data : []
    } catch {
      ndviData.value = []
    }
  }

  return {
    soilProfile, weather, forecast, decision, ndviData, loading,
    queryPoint, fetchWeather, fetchForecast, fetchNDVI,
  }
}
