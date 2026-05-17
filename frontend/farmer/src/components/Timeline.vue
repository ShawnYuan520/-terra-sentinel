<template>
  <div class="timeline-bar">
    <div class="tl-left">
      <div class="tl-ndvi-label">NDVI</div>
      <div class="tl-ndvi-value" :style="{ color: ndviColor }">{{ currentNDVI }}</div>
    </div>

    <div class="tl-center">
      <div class="tl-chart" ref="sparkEl"></div>
      <input
        type="range"
        :min="0"
        :max="Math.max(0, (data?.length || 1) - 1)"
        :value="modelValue"
        @input="$emit('update:modelValue', +$event.target.value)"
        class="tl-slider"
      />
      <div class="tl-ticks">
        <span v-for="m in markers" :key="m.label" class="tl-tick" :style="{ left: m.pos + '%' }">
          <span class="tl-tick-dot" :style="{ background: m.color }"></span>
          <span class="tl-tick-label">{{ m.label }}</span>
        </span>
      </div>
    </div>

    <div class="tl-right">
      <div class="tl-date">{{ currentDate }}</div>
      <div class="tl-source text-xs text-dim">{{ currentSource }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] },
  modelValue: { type: Number, default: 0 },
})
defineEmits(['update:modelValue'])

const sparkEl = ref(null)
let chart = null

const currentPoint = computed(() => props.data?.[props.modelValue])
const currentNDVI = computed(() => currentPoint.value?.ndvi?.toFixed(3) || '--')
const currentDate = computed(() => currentPoint.value?.timestamp?.slice(0, 10) || '')
const currentSource = computed(() => currentPoint.value?.source || '')

const ndviColor = computed(() => {
  const v = parseFloat(currentNDVI.value)
  if (isNaN(v)) return 'var(--gis-text-muted)'
  if (v >= 0.6) return '#4ADE80'
  if (v >= 0.3) return '#FBBF24'
  return '#F87171'
})

const markers = [
  { label: '播种', pos: 15, color: '#8B5E3C' },
  { label: '生长期', pos: 40, color: '#22C55E' },
  { label: '抽穗', pos: 65, color: '#3B82F6' },
  { label: '成熟', pos: 85, color: '#D97706' },
]

function drawSpark() {
  if (!sparkEl.value || !props.data?.length) return
  if (!chart) { chart = echarts.init(sparkEl.value) }
  const ndviValues = props.data.map(d => d.ndvi || 0)
  chart.setOption({
    grid: { top: 2, right: 2, bottom: 2, left: 2 },
    xAxis: { type: 'category', show: false, data: ndviValues.map((_, i) => i) },
    yAxis: { type: 'value', show: false, min: 0, max: 1 },
    series: [{
      type: 'line', data: ndviValues,
      smooth: true, symbol: 'none',
      lineStyle: { color: '#22C55E', width: 1.5 },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'rgba(34,197,94,0.3)' },
        { offset: 1, color: 'rgba(34,197,94,0.02)' },
      ])},
    }],
  })
}

watch(() => props.data, () => nextTick(drawSpark), { deep: true })
onMounted(() => nextTick(drawSpark))
</script>

<style scoped>
.timeline-bar {
  display: flex; align-items: center; gap: var(--space-md);
  padding: var(--space-sm) var(--space-lg);
  background: var(--gis-surface);
  border-top: 1px solid var(--gis-border);
  height: 100%;
}
.tl-left {
  width: 80px; flex-shrink: 0; text-align: center;
}
.tl-ndvi-label {
  font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;
  color: var(--gis-text-dim);
}
.tl-ndvi-value {
  font-size: var(--text-xl); font-weight: 700;
  font-family: var(--font-mono);
}
.tl-center {
  flex: 1; display: flex; flex-direction: column; gap: 2px;
  min-width: 0;
}
.tl-chart {
  width: 100%; height: 120px;
}
.tl-slider {
  width: 100%; height: 4px;
  -webkit-appearance: none; appearance: none;
  background: rgba(255,255,255,0.1);
  border-radius: 2px;
  outline: none; cursor: pointer;
}
.tl-slider::-webkit-slider-thumb {
  -webkit-appearance: none; appearance: none;
  width: 14px; height: 14px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  border: 2px solid var(--gis-text);
}
.tl-ticks {
  position: relative; height: 16px;
  margin-top: 2px;
}
.tl-tick {
  position: absolute; transform: translateX(-50%);
  display: flex; flex-direction: column; align-items: center; gap: 1px;
}
.tl-tick-dot {
  width: 5px; height: 5px; border-radius: 50%;
}
.tl-tick-label {
  font-size: 9px; color: var(--gis-text-dim);
  white-space: nowrap;
}
.tl-right {
  width: 100px; flex-shrink: 0; text-align: right;
}
.tl-date {
  font-size: var(--text-sm);
  color: var(--gis-text);
  font-family: var(--font-mono);
}
.tl-source { margin-top: 2px; }
</style>
