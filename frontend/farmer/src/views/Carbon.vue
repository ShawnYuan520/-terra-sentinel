<template>
  <div class="page-light">
    <div class="page-container">
      <h1>碳汇报告</h1>

      <div class="card" style="margin-bottom:var(--space-xl)">
        <div class="card-header">生成碳汇报告</div>
        <div class="card-body">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-md)">
            <div class="form-group">
              <label>田块</label>
              <select class="form-input" v-model="form.field_id">
                <option value="">选择田块</option>
                <option v-for="f in fields" :key="f.id" :value="f.id">{{ f.name }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>起始日期</label>
              <input class="form-input" v-model="form.period_start" type="date" />
            </div>
            <div class="form-group">
              <label>结束日期</label>
              <input class="form-input" v-model="form.period_end" type="date" />
            </div>
            <div class="form-group">
              <label>秸秆还田量 (吨)</label>
              <input class="form-input" v-model.number="form.straw_amount" type="number" min="0" />
            </div>
          </div>
          <button class="btn btn-primary" @click="generate" :disabled="loading" style="margin-top:var(--space-md)">
            {{ loading ? '生成中...' : '生成报告' }}
          </button>
        </div>
      </div>

      <h2 style="font-size:16px;font-weight:600;margin-bottom:16px">历史报告</h2>
      <div v-if="reports.length" style="display:flex;flex-direction:column;gap:var(--space-sm)">
        <div v-for="r in reports" :key="r.id" class="report-item">
          <div class="report-main">
            <div class="report-field">{{ getFieldName(r.field_id) || r.field_id?.slice(0,8) }}</div>
            <div class="report-period">{{ r.period_start?.slice(0,10) }} ~ {{ r.period_end?.slice(0,10) }}</div>
          </div>
          <div class="report-stats">
            <div class="stat"><span class="label">秸秆量</span> <span class="value">{{ r.straw_amount }}t</span></div>
            <div class="stat"><span class="label">碳汇量</span> <span class="value text-primary">{{ r.carbon_amount }} tCO₂e</span></div>
            <span :class="['badge', r.status === 'generated' ? 'badge-success' : 'badge-warning']">{{ r.status }}</span>
            <button class="btn btn-ghost btn-sm" @click="downloadPdf(r.id)" :disabled="pdfLoading === r.id">{{ pdfLoading === r.id ? '下载中...' : '下载 PDF' }}</button>
          </div>
        </div>
      </div>
      <div v-else class="text-muted" style="text-align:center;padding:var(--space-3xl)">暂无报告数据</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { useAppStore } from '../stores/appStore'

const store = useAppStore()
const fields = ref([])
const reports = ref([])
const loading = ref(false)
const pdfLoading = ref(null)
const form = ref({ field_id: '', period_start: '2024-01-01', period_end: '2024-12-31', straw_amount: 100 })

onMounted(async () => {
  try {
    const { data } = await api.get('/fields')
    fields.value = data.items || []
    store.setFields(data.items || [])
    if (data.items?.length) form.value.field_id = data.items[0].id
  } catch {}
  loadReports()
})

function getFieldName(id) { return fields.value.find(f => f.id === id)?.name }

async function loadReports() {
  try { const { data } = await api.get('/carbon/reports'); reports.value = data.items || [] } catch {}
}

async function generate() {
  if (!form.value.field_id) { alert('请选择田块'); return }
  loading.value = true
  try {
    await api.post('/carbon/reports', form.value)
    alert('报告生成成功')
    loadReports()
  } catch { alert('生成失败') } finally { loading.value = false }
}

async function downloadPdf(reportId) {
  pdfLoading.value = reportId
  try {
    const resp = await api.get(`/carbon/reports/${reportId}/pdf`, { responseType: 'blob' })
    const url = URL.createObjectURL(resp.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `carbon_report_${reportId.slice(0, 8)}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch { alert('PDF 下载失败') } finally { pdfLoading.value = null }
}
</script>

<style scoped>
.page-light { min-height: 100vh; overflow-y: auto; background: var(--surface-50); color: var(--surface-900); }
.page-container { max-width: 840px; margin: 0 auto; padding: var(--space-8) var(--space-6); }
h1 { font-size: var(--text-2xl); font-weight: var(--weight-bold); margin-bottom: var(--space-6); letter-spacing: var(--tracking-tight); }
h2 { font-size: var(--text-lg); font-weight: var(--weight-semibold); margin-bottom: var(--space-5); }
.report-item {
  background: var(--surface-0); border: 1px solid var(--surface-200);
  border-radius: var(--radius-md); padding: var(--space-5);
  display: flex; justify-content: space-between; align-items: center;
  transition: all var(--duration-normal) var(--ease-out);
}
.report-item:hover { box-shadow: var(--shadow-md); border-color: var(--surface-300); }
.report-main { flex: 1; }
.report-field { font-weight: var(--weight-semibold); font-size: var(--text-base); color: var(--surface-900); }
.report-period { font-size: var(--text-sm); color: var(--surface-700); margin-top: 4px; }
.report-stats { display: flex; align-items: center; gap: var(--space-6); }
.stat { text-align: center; }
.stat .label { font-size: var(--text-xs); color: var(--surface-700); display: block; }
.stat .value { font-size: var(--text-base); font-weight: var(--weight-semibold); color: var(--surface-900); display: block; margin-top: 2px; }
</style>
