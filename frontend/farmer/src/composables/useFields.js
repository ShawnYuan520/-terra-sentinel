import { ref } from 'vue'
import api from '../api'

// 全局缓存：避免多个组件同时请求 /fields
let _fieldsPromise = null
let _fieldsCache = null
let _fieldsCacheTime = 0
const CACHE_TTL = 5000 // 5 秒内复用缓存

export function useFields() {
  const fields = ref([])
  const drawMode = ref(false)
  const drawVertices = ref([])
  const newField = ref({ name: '', crop_type: '玉米', area_ha: 0 })
  const loading = ref(false)

  async function fetchFields(force = false) {
    const now = Date.now()
    // 有有效缓存直接返回
    if (!force && _fieldsCache && (now - _fieldsCacheTime) < CACHE_TTL) {
      fields.value = _fieldsCache
      return
    }
    // 有正在进行的请求则复用
    if (!force && _fieldsPromise) {
      fields.value = await _fieldsPromise
      return
    }
    _fieldsPromise = api.get('/fields').then(r => r.data?.items || []).catch(() => [])
    try {
      fields.value = await _fieldsPromise
      _fieldsCache = fields.value
      _fieldsCacheTime = Date.now()
    } catch {} finally {
      _fieldsPromise = null
    }
  }

  async function createField(geojson) {
    loading.value = true
    try {
      const { data } = await api.post('/fields', {
        name: newField.value.name,
        crop_type: newField.value.crop_type,
        area_ha: newField.value.area_ha,
        geojson,
      })
      fields.value = [data, ...fields.value]
      return data
    } finally {
      loading.value = false
    }
  }

  async function deleteField(id) {
    await api.delete(`/fields/${id}`)
    fields.value = fields.value.filter(f => f.id !== id)
  }

  function polygonArea(latlngs) {
    if (latlngs.length < 3) return 0
    const R = 6371000
    let area = 0
    for (let i = 0; i < latlngs.length; i++) {
      const j = (i + 1) % latlngs.length
      const [lng1, lat1] = [latlngs[i].lng || latlngs[i][0], latlngs[i].lat || latlngs[i][1]]
      const [lng2, lat2] = [latlngs[j].lng || latlngs[j][0], latlngs[j].lat || latlngs[j][1]]
      const y1 = lat1 * Math.PI / 180
      const y2 = lat2 * Math.PI / 180
      const dx = (lng2 - lng1) * Math.PI / 180
      area += dx * (2 + Math.sin(y1) + Math.sin(y2))
    }
    return Math.abs(area * R * R / 2) / 10000 // hectares
  }

  function startDraw() { drawMode.value = true; drawVertices.value = [] }
  function addVertex(ll) { drawVertices.value = [...drawVertices.value, ll] }
  function cancelDraw() { drawMode.value = false; drawVertices.value = [] }

  async function finishDraw() {
    if (drawVertices.value.length < 3) return
    newField.value.area_ha = +polygonArea(drawVertices.value).toFixed(2)
    drawMode.value = false
  }

  return {
    fields, drawMode, drawVertices, newField, loading,
    fetchFields, createField, deleteField, polygonArea,
    startDraw, addVertex, finishDraw, cancelDraw,
  }
}
