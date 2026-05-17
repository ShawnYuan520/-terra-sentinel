<template>
  <div class="page-light">
    <div class="page-container">
      <h1>土壤分析</h1>

      <div class="card" style="margin-bottom:var(--space-xl)">
        <div class="card-header">栅格数据点查询</div>
        <div class="card-body">
          <div style="display:flex;gap:var(--space-sm);align-items:flex-end">
            <div class="form-group" style="flex:1">
              <label>经度</label>
              <input class="form-input" v-model.number="rasterLon" type="number" step="0.0001" placeholder="如 126.33" />
            </div>
            <div class="form-group" style="flex:1">
              <label>纬度</label>
              <input class="form-input" v-model.number="rasterLat" type="number" step="0.0001" placeholder="如 45.39" />
            </div>
            <button class="btn btn-primary btn-sm" @click="queryRaster" :disabled="rasterLoading">
              {{ rasterLoading ? '查询中...' : '查询' }}
            </button>
          </div>
          <div v-if="rasterResult" style="margin-top:var(--space-md)">
            <div class="data-row"><span class="label">DEM 海拔</span><span class="value">{{ rasterResult.dem?.toFixed(0) || '-' }} m</span></div>
            <div class="data-row"><span class="label">土地覆盖</span><span class="value">{{ rasterResult.landuse_name || '-' }}</span></div>
            <div class="data-row"><span class="label">SOC 有机碳</span><span class="value">{{ rasterResult.soc?.toFixed(1) || '-' }} g/kg</span></div>
            <div class="data-row"><span class="label">pH</span><span class="value">{{ rasterResult.ph?.toFixed(1) || '-' }}</span></div>
            <div class="data-row"><span class="label">土壤质地</span><span class="value">{{ rasterResult.texture_name || '-' }}</span></div>
            <div class="data-row"><span class="label">评级</span><span class="value text-data">{{ rasterResult.soil_grade || '-' }}</span></div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">提交土壤检测数据</div>
        <div class="card-body">
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:var(--space-md)">
            <div class="form-group">
              <label>pH 值</label>
              <input class="form-input" v-model.number="form.ph" type="number" step="0.1" placeholder="如 6.5" />
            </div>
            <div class="form-group">
              <label>有机质 (g/kg)</label>
              <input class="form-input" v-model.number="form.organic_matter" type="number" step="0.1" placeholder="如 32.0" />
            </div>
            <div class="form-group">
              <label>全氮 (g/kg)</label>
              <input class="form-input" v-model.number="form.nitrogen" type="number" step="0.1" placeholder="如 2.1" />
            </div>
            <div class="form-group">
              <label>有效磷 (mg/kg)</label>
              <input class="form-input" v-model.number="form.phosphorus" type="number" step="0.1" placeholder="如 28.0" />
            </div>
            <div class="form-group">
              <label>速效钾 (mg/kg)</label>
              <input class="form-input" v-model.number="form.potassium" type="number" step="0.1" placeholder="如 150.0" />
            </div>
            <div class="form-group">
              <label>含水量 (%)</label>
              <input class="form-input" v-model.number="form.moisture" type="number" step="0.1" placeholder="如 24.0" />
            </div>
          </div>
          <button class="btn btn-primary" @click="submitRecord" :disabled="submitLoading" style="margin-top:var(--space-md)">
            {{ submitLoading ? '提交中...' : '提交数据' }}
          </button>
        </div>
      </div>

      <div class="card" v-if="records.length" style="margin-top:24px">
        <div class="card-header">历史记录</div>
        <div class="card-body">
          <div v-for="r in records" :key="r.id" class="data-row">
            <span class="label">{{ r.record_date?.slice(0,10) }}</span>
            <span class="value">pH:{{ r.ph }} 有机质:{{ r.organic_matter }}g/kg</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { useAppStore } from '../stores/appStore'

const store = useAppStore()
const rasterLon = ref(126.33)
const rasterLat = ref(45.39)
const rasterLoading = ref(false)
const rasterResult = ref(null)
const submitLoading = ref(false)
const records = ref([])
const form = ref({ ph: '', organic_matter: '', nitrogen: '', phosphorus: '', potassium: '', moisture: '' })

onMounted(async () => {
  try { const { data } = await api.get('/fields'); if (data.items?.length) store.setFields(data.items) } catch (e) { console.error('加载田块失败', e) }
  loadRecords()
})

async function loadRecords() {
  const fid = store.state.selectedField?.id || store.state.fields?.[0]?.id
  if (!fid) return
  try { const { data } = await api.get(`/soil/records/${fid}`); records.value = data || [] } catch (e) { console.error('加载土壤记录失败', e) }
}

async function queryRaster() {
  rasterLoading.value = true
  try {
    const { data } = await api.get('/raster/soil-profile', { params: { lon: rasterLon.value, lat: rasterLat.value } })
    rasterResult.value = data
  } catch (e) { console.error('栅格查询失败', e) } finally { rasterLoading.value = false }
}

async function submitRecord() {
  const fid = store.state.selectedField?.id || store.state.fields?.[0]?.id
  if (!fid) { alert('请先选择田块'); return }
  submitLoading.value = true
  try {
    await api.post('/soil/records', { field_id: fid, ...form.value })
    alert('提交成功')
    loadRecords()
  } catch {} finally { submitLoading.value = false }
}
</script>

<style scoped>
.page-light { min-height: 100vh; overflow-y: auto; background: var(--surface-50); color: var(--surface-900); }
.page-container { max-width: 840px; margin: 0 auto; padding: var(--space-8) var(--space-6); }
h1 { font-size: var(--text-2xl); font-weight: var(--weight-bold); margin-bottom: var(--space-6); letter-spacing: var(--tracking-tight); }
</style>
