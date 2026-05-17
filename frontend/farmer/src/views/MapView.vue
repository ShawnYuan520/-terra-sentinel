<template>
  <div class="map-view">
    <div id="gis-map" ref="mapContainer"></div>

    <DrawBar
      v-if="drawMode"
      :vertexCount="drawVertices.length"
      @finish="finishDraw"
      @cancel="cancelDraw"
    />

    <Dialog :visible="showSaveDialog" title="保存田块" @close="showSaveDialog = false">
      <FieldForm :modelValue="newField" @save="saveField" @cancel="showSaveDialog = false" />
    </Dialog>

    <div class="map-actions" v-if="!drawMode">
      <button class="btn btn-primary btn-sm" @click="startDraw"><Pen :size="16" /> 绘制田块</button>
    </div>
    <div class="map-hint" v-if="!drawMode">
      点击地图查询土壤数据 · 点击「绘制田块」进入绘制模式
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import L from 'leaflet'
import api from '../api'
import { useAppStore, useSelectFieldFn } from '../stores/appStore'
import DrawBar from '../components/DrawBar.vue'
import Dialog from '../components/Dialog.vue'
import FieldForm from '../components/FieldForm.vue'
import { Pen } from 'lucide-vue-next'

const store = useAppStore()
const loadFieldData = useSelectFieldFn()
const mapContainer = ref(null)
const showSaveDialog = ref(false)
const drawMode = ref(false)
const drawVertices = ref([])
const newField = ref({ name: '', crop_type: '玉米', area_ha: 0 })

let map = null
let geoJsonLayer = null
let rasterTile = null
let drawMarkers = []
let drawLine = null
let savedVertices = []
let currentBaseLayer = null

const BASEMAPS = {
  satellite: { url: 'https://webst01.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}', attr: '© 高德地图' },
  dark: { url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png', attr: '© OpenStreetMap' },
  terrain: { url: 'https://webst01.is.autonavi.com/appmaptile?style=8&x={x}&y={y}&z={z}', attr: '© 高德地图' },
}

function initMap() {
  map = L.map('gis-map', {
    center: [45.39, 126.33],
    zoom: 10,
    zoomControl: true,
    attributionControl: false,
  })
  currentBaseLayer = L.tileLayer(BASEMAPS.satellite.url, { maxZoom: 18, attribution: BASEMAPS.satellite.attr }).addTo(map)
  L.control.scale({ position: 'bottomleft', imperial: false }).addTo(map)

  map.on('click', async (e) => {
    if (drawMode.value) {
      addVertex(e.latlng)
      return
    }
    const { lat, lng } = e.latlng

    // 先加载数据，保留旧数据显示（不提前清空）
    const [sRes, dRes, wRes] = await Promise.allSettled([
      api.get('/raster/soil-profile', { params: { lon: lng, lat } }),
      api.get('/raster/decision', { params: { lon: lng, lat, crop: '玉米', area_mu: 100 } }),
      api.get('/weather/current', { params: { lat, lon: lng } }),
    ])

    const soilData = sRes.status === 'fulfilled' ? sRes.value.data : null
    const decisionData = dRes.status === 'fulfilled' ? dRes.value.data : null
    const weatherData = wRes.status === 'fulfilled' ? wRes.value.data : null

    // 数据到齐后原子性替换 — 无闪烁切换
    store.selectField(null)
    if (soilData) store.setSoilProfile(soilData)
    if (decisionData) store.setDecision(decisionData)
    if (weatherData) store.setWeather(weatherData)
    store.setClickedPoint({ lon: lng.toFixed(4), lat: lat.toFixed(4), ...(soilData || {}) })

    if (!soilData && !weatherData) {
      L.popup()
        .setLatLng(e.latlng)
        .setContent('<div style="font-family:Inter,sans-serif;font-size:12px;color:#F87171">查询失败，请稍后重试</div>')
        .openOn(map)
    } else {
      L.popup()
        .setLatLng(e.latlng)
        .setContent(`<div style="font-family:Inter,sans-serif;font-size:12px;color:#E2E8F0"><b>${soilData?.landuse_name || '未知'}</b><br>海拔 ${soilData?.dem?.toFixed(0) || '-'}m · SOC ${soilData?.soc?.toFixed(1) || '-'}g/kg<br>${weatherData?.temperature_c ?? '-'}°C · ${weatherData?.description || ''}</div>`)
        .openOn(map)
    }
  })
}

function renderFields() {
  if (geoJsonLayer) { map.removeLayer(geoJsonLayer); geoJsonLayer = null }
  if (!store.state.fields?.length) return
  const features = store.state.fields.map(f => {
    let geom
    try { geom = JSON.parse(f.geom) } catch { return null }
    return { ...geom, properties: { id: f.id, name: f.name, crop: f.crop_type } }
  }).filter(Boolean)
  geoJsonLayer = L.geoJSON(features, {
    style: feat => ({
      color: feat.properties.id === store.state.selectedField?.id ? '#2EC85D' : '#8B5E3C',
      weight: feat.properties.id === store.state.selectedField?.id ? 2.5 : 1.5,
      fillColor: feat.properties.id === store.state.selectedField?.id ? '#2EC85D' : '#3B82F6',
      fillOpacity: feat.properties.id === store.state.selectedField?.id ? 0.15 : 0.05,
    }),
    onEachFeature: (feat, layer) => {
      layer.bindTooltip(`${feat.properties.name}`, { direction: 'top' })
      layer.on('click', () => {
        const f = store.state.fields.find(x => x.id === feat.properties.id)
        if (f && loadFieldData) loadFieldData(f)
      })
    },
  }).addTo(map)
}

function fitToField(f) {
  if (!f) return
  try {
    const geom = JSON.parse(f.geom)
    const coords = geom.coordinates?.[0]
    if (coords) map.fitBounds(L.latLngBounds(coords.map(([lng, lat]) => [lat, lng])), { padding: [80, 80], maxZoom: 14 })
  } catch {}
}

// --- Raster layer management ---
function setRasterLayer(key) {
  if (rasterTile) { map.removeLayer(rasterTile); rasterTile = null }
  if (!key) return
  rasterTile = L.tileLayer(`/api/v1/raster/${key}/tile/{z}/{x}/{y}?colormap=viridis`, {
    opacity: 0.65, maxZoom: 18, attribution: '',
  }).addTo(map)
}

watch(() => store.state.activeLayers, (layers) => {
  const activeKey = layers.length > 0 ? layers[layers.length - 1] : null
  setRasterLayer(activeKey)
}, { deep: true })

watch(() => store.state.basemap, (bm) => {
  if (!map) return
  if (currentBaseLayer) map.removeLayer(currentBaseLayer)
  const cfg = BASEMAPS[bm] || BASEMAPS.satellite
  currentBaseLayer = L.tileLayer(cfg.url, { maxZoom: 18, attribution: cfg.attr }).addTo(map)
  currentBaseLayer.setZIndex(0)
})

// --- Drawing ---
function addVertex(ll) {
  drawVertices.value = [...drawVertices.value, ll]
  L.circleMarker([ll.lat, ll.lng], { radius: 5, color: '#22C55E', fillOpacity: 0.6 }).addTo(map)
  if (drawVertices.value.length >= 2) {
    if (drawLine) map.removeLayer(drawLine)
    drawLine = L.polygon(drawVertices.value.map(v => [v.lat, v.lng]), {
      color: '#22C55E', dashArray: '5 5', fillOpacity: 0.1,
    }).addTo(map)
  }
}

function startDraw() {
  drawMode.value = true
  drawVertices.value = []
}

function cancelDraw() {
  drawMode.value = false
  drawVertices.value = []
  savedVertices = []
  if (drawLine) { map.removeLayer(drawLine); drawLine = null }
}

function finishDraw() {
  if (drawVertices.value.length < 3) return
  // 必须在清理前保存顶点
  savedVertices = [...drawVertices.value]
  // 手动清理绘制状态（不调用 cancelDraw，避免清空 savedVertices）
  drawMode.value = false
  drawVertices.value = []
  if (drawLine) { map.removeLayer(drawLine); drawLine = null }
  const area = polygonArea(savedVertices)
  newField.value = { name: '', crop_type: '玉米', area_ha: +area.toFixed(2) }
  showSaveDialog.value = true
}

async function saveField(formData) {
  const coords = savedVertices.map(v => [v.lng, v.lat])
  coords.push(coords[0])
  const geojson = { type: 'Polygon', coordinates: [coords] }
  try {
    await api.post('/fields', { name: formData.name, crop_type: formData.crop_type, area_ha: formData.area_ha, geojson })
    showSaveDialog.value = false
    savedVertices = []
    const { data } = await api.get('/fields')
    store.setFields(data.items || [])
  } catch (err) {
    console.error('保存田块失败', err)
    const msg = err.response?.data?.detail || err.message || '未知错误'
    alert('保存失败: ' + msg)
  }
}

function polygonArea(latlngs) {
  if (latlngs.length < 3) return 0
  const R = 6371000
  let area = 0
  for (let i = 0; i < latlngs.length; i++) {
    const j = (i + 1) % latlngs.length
    const y1 = latlngs[i].lat * Math.PI / 180
    const y2 = latlngs[j].lat * Math.PI / 180
    const dx = (latlngs[j].lng - latlngs[i].lng) * Math.PI / 180
    area += dx * (2 + Math.sin(y1) + Math.sin(y2))
  }
  return Math.abs(area * R * R / 2) / 10000
}

onMounted(async () => {
  await nextTick()
  initMap()
  // 初始图层
  if (store.state.activeLayers.length) setRasterLayer(store.state.activeLayers[store.state.activeLayers.length - 1])
  // 从 store 加载田块（由 Layout 的 onMounted 填充）
  if (store.state.fields.length) renderFields()
})

watch(() => store.state.fields, () => nextTick(renderFields), { deep: true })
watch(() => store.state.shouldStartDraw, (v) => { if (v) startDraw() })
watch(() => store.state.selectedField, (f) => { if (f) { fitToField(f); renderFields() } })

onUnmounted(() => { if (map) { map.remove(); map = null } })
</script>

<style scoped>
.map-view {
  width: 100%; height: 100%; position: relative;
}
#gis-map {
  width: 100%; height: 100%;
}
.map-actions {
  position: absolute; top: 12px; left: 50%; transform: translateX(-50%);
  z-index: 1000;
}
.map-hint {
  position: absolute; bottom: 50px; left: 50%; transform: translateX(-50%);
  background: rgba(12, 17, 23, 0.85); color: var(--gis-text-muted);
  font-size: var(--text-xs); padding: var(--space-sm) var(--space-lg);
  border-radius: var(--radius-sm); pointer-events: none;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}
</style>
