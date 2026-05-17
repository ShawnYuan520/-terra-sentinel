<template>
  <div class="charts-mini">
    <!-- 面板1：NDVI 趋势 -->
    <div class="mini-panel" :class="{ active: activeTab === 'ndvi' }" @click="activeTab = 'ndvi'">
      <div class="mini-label">
        <span class="mini-dot" style="background:#22C55E"></span> NDVI
        <span class="mini-val" v-if="ndviData.length">{{ latestNDVI }}</span>
      </div>
      <div class="mini-chart" ref="ndviEl"></div>
    </div>
    <!-- 面板2：气温降水 -->
    <div class="mini-panel" :class="{ active: activeTab === 'weather' }" @click="activeTab = 'weather'">
      <div class="mini-label">
        <span class="mini-dot" style="background:#F59E0B"></span> 气温降水
        <span class="mini-val" v-if="forecast.length">5日</span>
      </div>
      <div class="mini-chart" ref="weatherEl"></div>
    </div>
    <!-- 面板3：土壤剖面 -->
    <div class="mini-panel" :class="{ active: activeTab === 'soil' }" @click="activeTab = 'soil'">
      <div class="mini-label">
        <span class="mini-dot" style="background:#8B5E3C"></span> 土壤
        <span class="mini-val" v-if="soilText">{{ soilText }}</span>
      </div>
      <div class="mini-chart" ref="soilEl"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, computed } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  ndviData: { type: Array, default: () => [] },
  forecast: { type: Array, default: () => [] },
  soilProfile: { type: Object, default: null },
})

const activeTab = ref('ndvi')
const ndviEl = ref(null)
const weatherEl = ref(null)
const soilEl = ref(null)
let c1 = null, c2 = null, c3 = null

const latestNDVI = computed(() => {
  const d = props.ndviData?.[props.ndviData.length - 1]
  return d ? d.ndvi?.toFixed(2) : ''
})

const soilText = computed(() => {
  const s = props.soilProfile
  if (!s) return ''
  return s.texture_name || s.soil_grade?.slice(0, 4) || ''
})

function drawNDVI() {
  if (!ndviEl.value || !props.ndviData?.length) return
  if (!c1) c1 = echarts.init(ndviEl.value)
  const slice = props.ndviData.slice(-60)
  c1.setOption({
    grid: { top: 2, right: 2, bottom: 2, left: 2 },
    xAxis: { show: false, data: slice.map((_, i) => i) },
    yAxis: { show: false, min: 0, max: 1 },
    series: [{
      type: 'line', data: slice.map(d => d.ndvi || 0),
      smooth: true, symbol: 'none',
      lineStyle: { color: '#22C55E', width: 1.5 },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'rgba(34,197,94,0.35)' },
        { offset: 1, color: 'rgba(34,197,94,0.03)' },
      ])},
    }],
  })
}

function drawWeather() {
  if (!weatherEl.value || !props.forecast?.length) return
  if (!c2) c2 = echarts.init(weatherEl.value)
  const temps = props.forecast.map(d => d.temperature_c ?? d.temp ?? 0)
  const precips = props.forecast.map(d => d.precipitation_mm ?? 0)
  c2.setOption({
    grid: { top: 2, right: 2, bottom: 2, left: 2 },
    xAxis: { show: false, data: temps.map((_, i) => i) },
    yAxis: { show: false },
    series: [
      {
        type: 'line', data: temps,
        smooth: true, symbol: 'none',
        lineStyle: { color: '#F59E0B', width: 1.5 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(245,158,11,0.25)' },
          { offset: 1, color: 'rgba(245,158,11,0.02)' },
        ])},
      },
      {
        type: 'bar', data: precips,
        itemStyle: { color: '#3B82F6', borderRadius: [2, 2, 0, 0] },
        barWidth: '60%', barGap: '-100%',
      },
    ],
  })
}

function drawSoil() {
  if (!soilEl.value || !props.soilProfile) return
  if (!c3) c3 = echarts.init(soilEl.value)
  const s = props.soilProfile
  const bars = [
    { name: 'SOC', value: s.soc ?? 0, max: 40, color: '#22C55E' },
    { name: '砂粒', value: s.sand ?? 0, max: 100, color: '#D97706' },
    { name: '粉粒', value: s.silt ?? 0, max: 100, color: '#8B5E3C' },
    { name: '粘粒', value: s.clay ?? 0, max: 100, color: '#3B82F6' },
  ].filter(b => b.value > 0)
  c3.setOption({
    grid: { top: 2, right: 6, bottom: 2, left: 6 },
    yAxis: { type: 'category', show: false, data: bars.map(b => b.name), inverse: true },
    xAxis: { show: false, max: 100 },
    series: [{
      type: 'bar', data: bars.map(b => ({ value: b.value, itemStyle: { color: b.color, borderRadius: [0, 2, 2, 0] } })),
      barWidth: '50%',
      label: { show: true, position: 'right', fontSize: 8, color: '#94A3B8',
        formatter: p => bars[p.dataIndex].value.toFixed(0) },
    }],
  })
}

let resizeTimer
function onResize() {
  clearTimeout(resizeTimer)
  resizeTimer = setTimeout(() => { c1?.resize(); c2?.resize(); c3?.resize() }, 150)
}

onMounted(() => {
  nextTick(() => { drawNDVI(); drawWeather(); drawSoil() })
  window.addEventListener('resize', onResize)
})

watch(() => [props.ndviData, props.forecast, props.soilProfile], () => {
  nextTick(() => { drawNDVI(); drawWeather(); drawSoil() })
}, { deep: true })
</script>

<style scoped>
.charts-mini {
  display: flex; flex-direction: column;
  height: 100%; padding: var(--space-xs);
  gap: 2px;
}
.mini-panel {
  flex: 1; display: flex; flex-direction: column;
  background: rgba(255,255,255,0.02);
  border-radius: var(--radius-sm);
  overflow: hidden;
  cursor: pointer;
  border: 1px solid transparent;
  transition: border-color 0.15s;
}
.mini-panel:hover { background: rgba(255,255,255,0.04); }
.mini-panel.active { border-color: rgba(255,255,255,0.08); }
.mini-label {
  display: flex; align-items: center; gap: 4px;
  font-size: 9px; color: var(--gis-text-dim);
  text-transform: uppercase; letter-spacing: 0.5px;
  padding: 2px var(--space-sm);
}
.mini-dot { width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; }
.mini-val { margin-left: auto; font-family: var(--font-mono); font-size: 8px; }
.mini-chart { flex: 1; }
</style>
