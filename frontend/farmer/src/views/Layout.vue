<template>
  <div class="gis-shell">
    <!-- 顶部状态栏 -->
    <header class="topbar">
      <div class="topbar-left">
        <img src="/logo.jpg" alt="AgriSpatial" class="logo-icon-img" />
        <span class="logo-text">AgriSpatial</span>
      </div>
      <div class="topbar-center">
        <span v-if="store.state.selectedField"><MapPin :size="14" /> {{ store.state.selectedField.name }}</span>
        <span class="text-dim" v-else>点击地图或用左侧列表选择田块</span>
      </div>
      <nav class="topbar-right">
        <router-link to="/" class="nav-link">概览</router-link>
        <router-link to="/map/products" class="nav-link">产品</router-link>
        <router-link to="/map/ai" class="nav-link">AI</router-link>
        <router-link to="/map/knowledge" class="nav-link">知识库</router-link>
        <router-link to="/map/settings" class="nav-link">设置</router-link>
        <router-link to="/map/help" class="nav-link">帮助</router-link>
      </nav>
    </header>

    <!-- 主体：flex 行，面板通顶通底，地图内部竖向堆叠 -->
    <div class="main-area">
      <div :class="['panel-wrapper left', isMapView ? 'open' : '']">
        <aside class="panel">
          <LayerToggle
            :activeLayers="store.state.activeLayers"
            :activeBasemap="store.state.basemap"
            @toggle="store.actions.toggleLayer"
            @basemap="store.actions.setBasemap"
          />
          <FieldSelector
            :fields="store.state.fields"
            :selectedId="store.state.selectedField?.id"
            @select="loadFieldData"
            @new-field="() => store.actions.triggerDraw()"
          />
        </aside>
      </div>

      <div class="map-stack">
        <main :class="isMapView ? 'map-container' : 'page-container'">
          <router-view v-slot="{ Component }">
            <component :is="Component" />
          </router-view>
        </main>
        <div class="timeline-bar" v-if="isMapView && store.state.ndviData.length">
          <Timeline
            :data="store.state.ndviData"
            :modelValue="store.state.timelineIndex"
            @update:modelValue="store.actions.setTimelineIndex"
          />
          <ChartsMini
            :ndviData="store.state.ndviData"
            :forecast="store.state.forecast"
            :soilProfile="store.state.soilProfile"
          />
        </div>
      </div>

      <div :class="['panel-wrapper right', isMapView ? 'open' : '']">
        <aside class="panel">
          <DataPanel
            :field="store.state.selectedField"
            :soil="store.state.soilProfile"
            :weather="store.state.weather"
            :decision="store.state.decision"
            :agriWeather="store.state.agriWeather"
            :landCover="store.state.landCover"
            :clickedPoint="store.state.clickedPoint"
            :landEval="store.state.landEval"
            :carbonModel="store.state.carbonModel"
            :machineryPath="store.state.machineryPath"
            @delete="handleDeleteField"
          />
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'
import { provideStore, provideSelectFieldFn } from '../stores/appStore'
import LayerToggle from '../components/LayerToggle.vue'
import FieldSelector from '../components/FieldSelector.vue'
import DataPanel from '../components/DataPanel.vue'
import Timeline from '../components/Timeline.vue'
import ChartsMini from '../components/ChartsMini.vue'
import { ArrowRight, MapPin } from 'lucide-vue-next'

const route = useRoute()
const isMapView = computed(() => route.name === 'MapView')
const provider = provideStore()
const store = { state: provider.state, actions: provider }

async function loadFields() {
  try {
    const { data } = await api.get('/fields')
    provider.setFields(data.items || [])
    if (data.items?.length && !store.state.selectedField) loadFieldData(data.items[0])
  } catch (err) { console.error('加载田块列表失败', err) }
}

async function loadFieldData(f) {
  let coords = null
  try {
    const geom = JSON.parse(f.geom)
    coords = geom.coordinates?.[0]?.[0]
  } catch {}

  if (!coords) return

  const [lon, lat] = coords

  // 先显示田块信息（立即渲染）
  provider.selectField(f)
  provider.setClickedPoint(null)

  // 所有数据一次性并行加载
  try {
    const [sRes, dRes, wRes, ndviRes, fcRes, agriRes, lcRes, algoRes] = await Promise.allSettled([
      api.get('/raster/soil-profile', { params: { lon, lat } }),
      api.get('/raster/decision', { params: { lon, lat, crop: f.crop_type || '玉米', area_mu: (f.area_ha || 10) * 15 } }),
      api.get('/weather/current', { params: { lat, lon } }),
      api.get(`/geo/ndvi/${f.id}`),
      api.get('/weather/forecast', { params: { lat, lon } }),
      api.get('/weather/agricultural', { params: { lat, lon } }),
      api.get(`/geo/landcover/${f.id}`),
      api.get(`/algorithms/analysis/${f.id}`),
    ])

    const get = (r) => r.status === 'fulfilled' ? r.value.data : null

    const soilData = get(sRes)
    const decisionData = get(dRes)
    const weatherData = get(wRes)

    if (soilData) provider.setSoilProfile(soilData)
    if (decisionData) provider.setDecision(decisionData)
    if (weatherData) provider.setWeather(weatherData)

    const ndviData = get(ndviRes)
    provider.setNdvData(Array.isArray(ndviData) ? ndviData : [])
    if (get(fcRes)) provider.setForecast(get(fcRes))
    if (get(agriRes)) provider.setAgriWeather(get(agriRes))
    if (get(lcRes)) provider.setLandCover(get(lcRes))
    if (get(algoRes)) provider.setAlgoResults(get(algoRes))
  } catch (err) { console.error('加载数据失败', err) }
}

async function handleDeleteField(f) {
  if (!confirm(`确定删除田块「${f.name}」？`)) return
  try {
    await api.delete(`/fields/${f.id}`)
    provider.selectField(null)
    await loadFields()
  } catch (err) {
    console.error('删除田块失败', err)
    alert('删除失败: ' + (err.response?.data?.detail || err.message))
  }
}

provideSelectFieldFn(loadFieldData)
onMounted(loadFields)
</script>

<style scoped>
.gis-shell {
  display: grid;
  grid-template-rows: var(--topbar-h) 1fr;
  height: 100vh;
  overflow: hidden;
}

/* ══════ Topbar ══════ */
.topbar {
  display: flex; align-items: center; gap: var(--space-4);
  padding: 0 var(--space-4);
  background: var(--gis-bg-deep);
  border-bottom: 1px solid var(--gis-border);
  z-index: 200;
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
}
.topbar-left { display: flex; align-items: center; gap: var(--space-2); min-width: 160px; }
.logo-icon-img { width: 28px; height: 28px; border-radius: 50%; object-fit: cover; flex-shrink: 0; box-shadow: 0 0 10px rgba(45,106,79,0.25); }
.logo-text {
  font-size: var(--text-sm); font-weight: var(--weight-bold);
  color: var(--color-primary-200); letter-spacing: var(--tracking-wide);
}
.topbar-center { flex: 1; text-align: center; font-size: var(--text-sm); color: var(--gis-text); }
.topbar-center :deep(svg) { opacity: 0.5; vertical-align: -3px; }
.topbar-right { display: flex; align-items: center; gap: 2px; }
.nav-link {
  font-size: var(--text-xs); color: var(--gis-text-muted);
  padding: 6px 12px; border-radius: var(--radius-sm);
  text-decoration: none; font-weight: var(--weight-medium);
  transition: all var(--duration-fast) var(--ease-out);
  position: relative;
}
.nav-link:hover { color: var(--gis-text); background: var(--gis-surface-hover); }
.nav-link.router-link-active {
  color: var(--gis-text);
  background: var(--gis-surface-active);
}
.nav-link.router-link-active::after {
  content: ''; position: absolute; bottom: -1px; left: 12px; right: 12px;
  height: 2px; background: var(--color-primary-200); border-radius: 1px;
}

/* ══════ Main Area ══════ */
.main-area {
  display: flex; overflow: hidden; min-height: 0;
}

/* Panels */
.panel-wrapper {
  width: 0; overflow: hidden;
  transition: width var(--duration-normal) var(--ease-out);
  flex-shrink: 0;
}
.panel-wrapper.open { width: var(--layer-panel-w); }
.panel-wrapper.right.open { width: var(--data-panel-w); }
.panel-wrapper .panel {
  width: var(--layer-panel-w); height: 100%;
  background: var(--gis-surface); overflow-y: auto;
  display: flex; flex-direction: column;
}
.panel-wrapper.right .panel { width: var(--data-panel-w); }
.panel-wrapper.left { border-right: 1px solid var(--gis-border); }
.panel-wrapper.right { border-left: 1px solid var(--gis-border); }

/* Map Stack */
.map-stack { flex: 1; display: flex; flex-direction: column; min-width: 0; overflow: hidden; }
.map-container { flex: 1; position: relative; overflow: hidden; background: var(--gis-bg); }
.page-container { flex: 1; overflow-y: auto; background: var(--surface-50); }
.timeline-bar {
  height: var(--timeline-h); flex-shrink: 0;
  background: var(--gis-surface); border-top: 1px solid var(--gis-border);
  overflow: hidden; display: grid; grid-template-columns: 1fr 260px;
}
</style>
