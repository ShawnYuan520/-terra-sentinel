<template>
  <div class="data-panel" v-if="field || clickedPoint">
    <div class="panel-header" v-if="clickedPoint">
      <div class="panel-title"><MapPin :size="14" /> {{ clickedPoint.lat }}, {{ clickedPoint.lon }}</div>
      <div class="panel-subtitle">
        {{ clickedPoint.landuse_name || '地图点查询' }}
        <span class="text-dim"> · {{ clickedPoint.dem?.toFixed(0) || '-' }}m</span>
      </div>
    </div>
    <div class="panel-header" v-else>
      <div class="panel-title">{{ field.name }}</div>
      <div class="panel-subtitle">{{ field.crop_type || '未指定' }} · {{ field.area_ha }}ha</div>
    </div>

    <div class="panel-sections">
      <!-- 田块信息 - 仅选中田块时显示 -->
      <div class="section" v-if="field">
        <div class="section-title" @click="toggle('info')">
          <span>田块信息</span>
          <span class="toggle-arrow">{{ openSections.info ? '▾' : '▸' }}</span>
        </div>
        <div class="section-body" v-show="openSections.info">
          <div class="data-row"><span class="label">ID</span><span class="value text-mono">{{ field.id?.slice(0, 8) }}</span></div>
          <div class="data-row"><span class="label">作物</span><span class="value">{{ field.crop_type || '-' }}</span></div>
          <div class="data-row"><span class="label">面积</span><span class="value">{{ field.area_ha }} ha</span></div>
          <button class="btn btn-danger btn-sm" @click="$emit('delete', field)" style="margin-top:6px">删除田块</button>
        </div>
      </div>

      <!-- 耕地评级（算法） -->
      <div class="section" v-if="landEval">
        <div class="section-title" @click="toggle('eval')">
          <span>耕地综合评级</span>
          <span class="toggle-arrow">{{ openSections.eval ? '▾' : '▸' }}</span>
        </div>
        <div class="section-body" v-show="openSections.eval">
          <div class="eval-score">
            <span class="eval-num">{{ landEval.score }}</span>
            <span class="eval-unit">分</span>
            <span class="eval-grade">{{ landEval.grade }}</span>
          </div>
          <div class="data-row" v-if="landEval.strengths?.length">
            <span class="label">优势</span>
            <span class="value text-success text-xs">{{ landEval.strengths.join(' · ') }}</span>
          </div>
          <div class="data-row" v-if="landEval.weaknesses?.length">
            <span class="label">短板</span>
            <span class="value text-warning text-xs">{{ landEval.weaknesses.join(' · ') }}</span>
          </div>
          <div class="text-xs text-dim" style="margin-top:2px">{{ landEval._meta }}</div>
        </div>
      </div>

      <!-- 土壤剖面 -->
      <div class="section" v-if="soil">
        <div class="section-title" @click="toggle('soil')">
          <span>土壤剖面</span>
          <span class="toggle-arrow">{{ openSections.soil ? '▾' : '▸' }}</span>
        </div>
        <div class="section-body" v-show="openSections.soil">
          <div class="data-row"><span class="label">DEM 海拔</span><span class="value">{{ soil.dem?.toFixed(0) || '-' }} m</span></div>
          <div class="data-row"><span class="label">有机碳</span><span class="value">{{ soil.soc?.toFixed(1) || '-' }} g/kg</span></div>
          <div class="data-row"><span class="label">pH 值</span><span class="value">{{ soil.ph?.toFixed(1) || '-' }}</span></div>
          <div class="data-row"><span class="label">质地</span><span class="value">{{ soil.texture_name || '-' }}</span></div>
          <div class="data-row"><span class="label">土地覆盖</span><span class="value">{{ soil.landuse_name || '-' }}</span></div>
          <div class="data-row"><span class="label">评级</span><span class="value text-data">{{ soil.soil_grade || '-' }}</span></div>
        </div>
      </div>

      <!-- 天气 -->
      <div class="section" v-if="weather">
        <div class="section-title" @click="toggle('weather')">
          <span>天气实况</span>
          <span class="toggle-arrow">{{ openSections.weather ? '▾' : '▸' }}</span>
        </div>
        <div class="section-body" v-show="openSections.weather">
          <div class="data-row"><span class="label">温度</span><span class="value">{{ weather.temperature_c }}°C</span></div>
          <div class="data-row"><span class="label">湿度</span><span class="value">{{ weather.humidity_pct }}%</span></div>
          <div class="data-row"><span class="label">降水</span><span class="value">{{ weather.precipitation_mm }}mm</span></div>
          <div class="data-row"><span class="label">风速</span><span class="value">{{ weather.wind_speed_ms }} m/s</span></div>
          <div class="data-row"><span class="label">天气</span><span class="value">{{ weather.description }}</span></div>
          <span :class="['badge', weather.source === 'OpenWeather' ? 'badge-success' : 'badge-warning']" style="margin-top:4px">{{ weather.source === 'OpenWeather' ? '实时数据' : '模拟数据' }}</span>
        </div>
      </div>

      <!-- 土地覆盖 -->
      <div class="section" v-if="landCover && !landCover.error">
        <div class="section-title" @click="toggle('lc')">
          <span>土地覆盖</span>
          <span class="toggle-arrow">{{ openSections.lc ? '▾' : '▸' }}</span>
        </div>
        <div class="section-body" v-show="openSections.lc">
          <div class="data-row"><span class="label">分类</span><span class="value">{{ landCover.landuse_name || '-' }}</span></div>
          <div class="data-row"><span class="label">海拔</span><span class="value">{{ landCover.elevation_m || '-' }} m</span></div>
          <div class="data-row"><span class="label">有机碳</span><span class="value">{{ landCover.soc_g_per_kg || '-' }} g/kg</span></div>
          <div class="text-xs text-dim" style="margin-top:4px">{{ landCover.source }}</div>
        </div>
      </div>

      <!-- 农业气象 -->
      <div class="section" v-if="agriWeather">
        <div class="section-title" @click="toggle('agri')">
          <span>农业气象</span>
          <span class="toggle-arrow">{{ openSections.agri ? '▾' : '▸' }}</span>
        </div>
        <div class="section-body" v-show="openSections.agri">
          <div class="data-row"><span class="label">积温 GDD</span><span class="value">{{ agriWeather.growing_degree_days }} °C·d</span></div>
          <div class="data-row"><span class="label">土壤水分</span><span class="value">{{ agriWeather.soil_moisture_percentile }}%</span></div>
          <div class="data-row">
            <span class="label">干旱风险</span>
            <span :class="['badge', agriWeather.drought_risk === 'high' ? 'badge-danger' : agriWeather.drought_risk === 'moderate' ? 'badge-warning' : 'badge-success']">{{ {high:'高', moderate:'中', low:'低'}[agriWeather.drought_risk] || agriWeather.drought_risk }}</span>
          </div>
          <div class="data-row">
            <span class="label">霜冻风险</span>
            <span :class="['badge', agriWeather.frost_risk === 'high' ? 'badge-danger' : agriWeather.frost_risk === 'low' ? 'badge-warning' : 'badge-success']">{{ {high:'高', low:'低', none:'无'}[agriWeather.frost_risk] || agriWeather.frost_risk }}</span>
          </div>
        </div>
      </div>

      <!-- 农机作业评估 -->
      <div class="section" v-if="soil || weather">
        <div class="section-title" @click="toggle('mach')">
          <span>农机作业评估</span>
          <span class="toggle-arrow">{{ openSections.mach ? '▾' : '▸' }}</span>
        </div>
        <div class="section-body" v-show="openSections.mach">
          <div v-for="(item, i) in machineryChecks" :key="i"
            :class="['diag-item', item.ok ? 'diag-ok' : item.warn ? 'diag-warn' : 'diag-danger']">
            {{ item.label }}
          </div>
        </div>
      </div>

      <!-- 智能诊断 -->
      <div class="section" v-if="decision?.diagnoses?.length">
        <div class="section-title" @click="toggle('diag')">
          <span>智能诊断</span>
          <span class="toggle-arrow">{{ openSections.diag ? '▾' : '▸' }}</span>
        </div>
        <div class="section-body" v-show="openSections.diag">
          <div v-for="(d, i) in decision.diagnoses" :key="i"
            :class="['diag-item', d.level === 'warn' ? 'diag-warn' : d.level === 'danger' ? 'diag-danger' : 'diag-ok']">
            {{ d.msg }}
          </div>
        </div>
      </div>

      <!-- 处方建议 -->
      <div class="section" v-if="decision?.prescriptions?.length">
        <div class="section-title" @click="toggle('presc')">
          <span>处方建议</span>
          <span class="toggle-arrow">{{ openSections.presc ? '▾' : '▸' }}</span>
        </div>
        <div class="section-body" v-show="openSections.presc">
          <div v-for="(p, i) in decision.prescriptions" :key="i" class="presc-item">
            <div class="presc-action">{{ p.action }}</div>
            <div class="presc-detail">{{ p.detail }}</div>
            <div class="presc-days" v-if="p.decomposer?.days">
              <Timer :size="14" /> 预计腐解周期：<b>{{ p.decomposer.days }} 天</b>
              <span class="text-dim"> · 用量 {{ p.decomposer.dosage }} kg/亩</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 预测 -->
      <div class="section" v-if="decision?.predictions">
        <div class="section-title" @click="toggle('pred')">
          <span>产量与碳汇预测</span>
          <span class="toggle-arrow">{{ openSections.pred ? '▾' : '▸' }}</span>
        </div>
        <div class="section-body" v-show="openSections.pred">
          <div class="data-row"><span class="label">预计产量</span><span class="value text-data">{{ decision.predictions.yield_kg_per_mu }} kg/亩</span></div>
          <div class="data-row"><span class="label">碳汇量</span><span class="value text-primary">{{ decision.predictions.carbon_tco2e_per_year }} tCO₂e/年</span></div>
        </div>
      </div>

      <!-- 碳汇模型预测（RothC简化版） -->
      <div class="section" v-if="carbonModel">
        <div class="section-title" @click="toggle('cmodel')">
          <span>碳汇趋势预测</span>
          <span class="toggle-arrow">{{ openSections.cmodel ? '▾' : '▸' }}</span>
        </div>
        <div class="section-body" v-show="openSections.cmodel">
          <div class="data-row">
            <span class="label">SOC 变化</span>
            <span class="value text-data">{{ carbonModel.soc_trajectory?.[0] }} <ArrowRight :size="14" /> {{ carbonModel.soc_trajectory?.[carbonModel.soc_trajectory?.length-1] }} g/kg</span>
          </div>
          <div class="data-row"><span class="label">累计碳汇</span><span class="value text-primary">{{ carbonModel.total_carbon_seq_tco2e }} tCO₂e</span></div>
          <div class="data-row"><span class="label">年均固碳</span><span class="value text-data">{{ carbonModel.annual_avg_seq }} tCO₂e/年</span></div>
          <div class="presc-item" style="margin-top:4px">{{ carbonModel.recommendation }}</div>
          <div class="text-xs text-dim" style="margin-top:2px">{{ carbonModel.model }} | 矿化速率 k={{ carbonModel.parameters?.k_effective }}</div>
        </div>
      </div>
    </div>
  </div>
  <div class="data-panel data-panel-loading" v-else-if="field && !soil && !weather && !decision && !clickedPoint">
    <div class="empty-state">
      <div class="loading-spinner"></div>
      <p class="text-muted">加载数据中…</p>
    </div>
  </div>
  <div class="data-panel data-panel-empty" v-else>
    <div class="empty-state">
      <div class="empty-icon"><Map :size="22" /></div>
      <p class="text-muted">选择田块或点击地图查询</p>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'
import { ArrowRight, Map, MapPin, Timer } from 'lucide-vue-next'

const props = defineProps({
  field: Object, soil: Object, weather: Object, decision: Object, agriWeather: Object, landCover: Object, clickedPoint: Object, landEval: Object, carbonModel: Object, machineryPath: Object,
})
defineEmits(['delete'])

const openSections = reactive({
  info: true,
  eval: false,
  soil: false,
  weather: false,
  mach: false,
  agri: false,
  diag: false,
  presc: true,
  pred: false,
  cmodel: false,
})

const machineryChecks = computed(() => {
  const checks = []
  const slope = props.soil?.slope
  const dem = props.soil?.dem
  const precip = props.weather?.precipitation_mm
  const wind = props.weather?.wind_speed_ms
  const temp = props.weather?.temperature_c
  const moisture = props.agriWeather?.soil_moisture_percentile

  // 坡度
  if (slope != null) {
    if (slope > 25) checks.push({ label: `坡度 ${slope.toFixed(1)}° — 坡度过陡，禁止大型农机作业`, ok: false, warn: false })
    else if (slope > 15) checks.push({ label: `坡度 ${slope.toFixed(1)}° — 坡度较大，仅限中小型农机`, ok: true, warn: true })
    else checks.push({ label: `坡度 ${slope.toFixed(1)}° — 地势平坦，适宜农机作业`, ok: true, warn: false })
  }

  // 土壤湿度
  if (moisture != null) {
    if (moisture > 80) checks.push({ label: `土壤水分 ${moisture}% — 土壤过湿，易陷车，不宜作业`, ok: false, warn: false })
    else if (moisture > 60) checks.push({ label: `土壤水分 ${moisture}% — 湿度偏高，注意低洼地`, ok: true, warn: true })
    else checks.push({ label: `土壤水分 ${moisture}% — 墒情适宜，可正常作业`, ok: true, warn: false })
  }

  // 降水
  if (precip != null) {
    if (precip > 10) checks.push({ label: `近期降水 ${precip}mm — 有强降水，建议暂停作业`, ok: false, warn: false })
    else if (precip > 3) checks.push({ label: `近期降水 ${precip}mm — 有小雨，不影响作业`, ok: true, warn: true })
    else checks.push({ label: `近期降水 ${precip}mm — 天气晴好，适合作业`, ok: true, warn: false })
  }

  // 风速
  if (wind != null) {
    if (wind > 12) checks.push({ label: `风速 ${wind} m/s — 大风预警，禁止喷洒作业`, ok: false, warn: false })
    else if (wind > 6) checks.push({ label: `风速 ${wind} m/s — 风力偏大，谨慎喷洒`, ok: true, warn: true })
    else checks.push({ label: `风速 ${wind} m/s — 风力适中，可正常作业`, ok: true, warn: false })
  }

  // 温度
  if (temp != null) {
    if (temp <= 0) checks.push({ label: `气温 ${temp}°C — 零下温度，机械启动困难`, ok: false, warn: false })
    else if (temp < 5) checks.push({ label: `气温 ${temp}°C — 温度偏低，注意防冻`, ok: true, warn: true })
    else if (temp > 38) checks.push({ label: `气温 ${temp}°C — 高温预警，注意人员防暑`, ok: true, warn: true })
    else checks.push({ label: `气温 ${temp}°C — 温度适宜，可正常作业`, ok: true, warn: false })
  }

  // 海拔
  if (dem != null) {
    if (dem > 1000) checks.push({ label: `海拔 ${dem.toFixed(0)}m — 高海拔地区，注意动力衰减`, ok: true, warn: true })
  }

  return checks
})

function toggle(key) { openSections[key] = !openSections[key] }
</script>

<style scoped>
.data-panel {
  height: 100%;
  display: flex; flex-direction: column;
  overflow: hidden;
}
.panel-header {
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--gis-border);
  flex-shrink: 0;
  background: rgba(17, 25, 34, 0.50);
  backdrop-filter: blur(12px);
}
.panel-title {
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
  color: var(--gis-text);
  display: flex; align-items: center; gap: 6px;
}
.panel-title :deep(svg) { opacity: 0.45; }
.panel-subtitle {
  font-size: var(--text-xs);
  color: var(--gis-text-muted);
  margin-top: 2px;
}
.panel-sections {
  flex: 1; overflow-y: auto;
  padding: var(--space-2);
  display: flex; flex-direction: column; gap: var(--space-2);
}
.section {
  background: rgba(255,255,255,0.025);
  border: 1px solid var(--gis-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  flex-shrink: 0;
  transition: border-color var(--duration-fast) var(--ease-out);
}
.section:hover { border-color: var(--gis-border-light); }
.section-title {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px var(--space-4);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--gis-text-muted);
  cursor: pointer;
  user-select: none;
  background: rgba(46, 200, 93, 0.06);
  transition: background var(--duration-fast) var(--ease-out);
}
.section-title:hover { background: rgba(46, 200, 93, 0.10); color: var(--gis-text); }
.toggle-arrow { font-size: 10px; color: var(--gis-text-dim); transition: transform var(--duration-fast) var(--ease-out); }
.section-body { padding: var(--space-3) var(--space-4) var(--space-4); }
.data-row {
  display: flex; justify-content: space-between;
  padding: 4px 0;
  font-size: var(--text-xs);
}
.data-row .label { color: var(--gis-text-dim); }
.data-row .value { color: var(--gis-text); font-weight: var(--weight-medium); font-family: var(--font-mono); }

.diag-item {
  font-size: var(--text-xs);
  padding: 4px 8px; border-radius: var(--radius-xs);
  margin-bottom: 4px;
  line-height: 1.4;
}
.diag-ok { background: rgba(34, 197, 94, 0.08); color: #4ADE80; }
.diag-warn { background: rgba(217, 119, 6, 0.08); color: #FBBF24; }
.diag-danger { background: rgba(220, 38, 38, 0.08); color: #F87171; }

.presc-item { padding: 4px 0; font-size: var(--text-xs); }
.presc-action { font-weight: var(--weight-semibold); color: var(--gis-text); }
.presc-detail { color: var(--gis-text-muted); margin-top: 2px; line-height: 1.4; }
.presc-days {
  font-size: var(--text-xs); color: var(--data-blue);
  margin-top: 6px; padding: 6px 8px;
  background: rgba(59, 130, 246, 0.06);
  border-radius: var(--radius-xs);
  display: flex; align-items: center; gap: 6px;
}
.presc-days b { color: var(--data-blue); }
.eval-score { display: flex; align-items: baseline; gap: 6px; margin-bottom: 8px; }
.eval-num { font-size: 32px; font-weight: var(--weight-bold); color: var(--color-primary-200); font-family: var(--font-mono); }
.eval-unit { font-size: var(--text-xs); color: var(--gis-text-muted); margin-right: var(--space-2); }
.eval-grade { font-size: var(--text-sm); font-weight: var(--weight-semibold); color: var(--gis-text); }
.data-panel-empty, .data-panel-loading { justify-content: center; align-items: center; }
.empty-state { text-align: center; padding: var(--space-8); }
.empty-icon { margin-bottom: var(--space-4); opacity: 0.3; }
.loading-spinner {
  width: 28px; height: 28px;
  border: 2px solid var(--gis-border);
  border-top-color: var(--color-primary-200);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  margin: 0 auto var(--space-4);
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
