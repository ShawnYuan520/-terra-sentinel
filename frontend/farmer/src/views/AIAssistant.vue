<template>
  <div class="ws-page">
    <!-- 背景纹理 -->
    <div class="ws-bg-pattern"></div>

    <!-- 顶部状态栏 -->
    <header class="ws-topbar">
      <div class="topbar-left">
        <Bot :size="18" />
        <span class="topbar-title">AgriSpatial AI</span>
        <span class="topbar-badge">Workspace</span>
      </div>
      <div class="topbar-center">
        <select v-model="selectedFieldId" class="field-select">
          <option value="">选择分析田块</option>
          <option v-for="f in fields" :key="f.id" :value="f.id">{{ f.name }}</option>
        </select>
      </div>
      <div class="topbar-right">
        <span :class="['status-chip', aiStatus.available ? 'online' : 'offline']" :title="aiStatus.available ? `AI 模型: ${aiStatus.model}` : (aiStatus.api_key_set ? 'API 调用失败，已降级为规则模式' : '未配置 API Key，使用规则模式')">
          <span class="dot"></span>{{ aiStatus.available ? 'AI 就绪' : '规则模式' }}
        </span>
        <span class="status-chip online"><span class="dot"></span>GIS 已连接</span>
        <span class="status-chip"><Satellite :size="12" /> 遥感图层</span>
        <span class="status-chip"><Clock :size="12" /> {{ currentTime }}</span>
      </div>
    </header>

    <!-- 主体 -->
    <div class="ws-main">
      <!-- 中间对话区 -->
      <div class="ws-chat">
        <!-- 消息列表 -->
        <div class="chat-messages" ref="messagesRef">
          <!-- 空状态 -->
          <div class="chat-empty" v-if="!messages.length && !loading">
            <div class="empty-icon"><Sparkles :size="32" /></div>
            <h3>AI 农业分析助手</h3>
            <p v-if="aiStatus.available">选择田块后，AI 将自动加载土壤、天气数据，结合卫星遥感进行专业分析</p>
            <p v-else>当前为规则引擎模式。选择田块后，可使用预设分析功能。配置 DeepSeek API Key 可获得更智能的对话体验。</p>
            <div class="empty-prompts">
              <button v-for="p in quickPrompts" :key="p.type" class="prompt-chip" @click="quickAnalyze(p.type)" :disabled="!selectedFieldId">
                <component :is="p.icon" :size="14" /> {{ p.label }}
              </button>
            </div>
          </div>

          <!-- 消息气泡 -->
          <div v-for="(msg, i) in messages" :key="i" :class="['msg', msg.role]">
            <div class="msg-avatar">
              <Bot v-if="msg.role === 'ai'" :size="16" />
              <User v-else :size="16" />
            </div>
            <div class="msg-content">
              <div class="msg-name">{{ msg.role === 'ai' ? 'AI 分析助手' : '我' }}</div>
              <div class="msg-bubble" v-html="formatReply(msg.text)"></div>
            </div>
          </div>

          <!-- 思考中 -->
          <div class="msg ai" v-if="loading">
            <div class="msg-avatar"><Bot :size="16" /></div>
            <div class="msg-content">
              <div class="msg-name">AI 分析助手</div>
              <div class="msg-bubble thinking">
                <div class="think-dots"><span></span><span></span><span></span></div>
                <div class="think-text">{{ thinkText }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区 -->
        <div class="chat-input-area">
          <div class="input-wrapper">
            <input
              v-model="query"
              class="chat-input"
              :placeholder="selectedFieldId ? '输入问题，回车发送...' : '请先在右上角选择田块'"
              @keyup.enter="analyze"
              :disabled="!selectedFieldId"
            />
            <button class="send-btn" @click="analyze" :disabled="loading || !query.trim() || !selectedFieldId">
              <Send :size="18" />
            </button>
          </div>
        </div>
      </div>

      <!-- 右侧数据面板 -->
      <aside class="ws-sidebar">
        <!-- 田块数据 -->
        <div class="side-card" v-if="fieldContext">
          <div class="side-card-title"><Sprout :size="14" /> 土壤数据</div>
          <div class="side-grid">
            <div class="side-item"><span class="side-key">SOC</span><span class="side-val">{{ fieldContext.soil?.soc?.toFixed(1) || '-' }} g/kg</span></div>
            <div class="side-item"><span class="side-key">质地</span><span class="side-val">{{ fieldContext.soil?.texture_name || '-' }}</span></div>
            <div class="side-item"><span class="side-key">pH</span><span class="side-val">{{ fieldContext.soil?.ph?.toFixed(1) || '-' }}</span></div>
            <div class="side-item"><span class="side-key">坡度</span><span class="side-val">{{ fieldContext.soil?.slope?.toFixed(1) || '-' }}°</span></div>
          </div>
        </div>

        <div class="side-card" v-if="fieldContext">
          <div class="side-card-title"><CloudSun :size="14" /> 天气实况</div>
          <div class="side-grid">
            <div class="side-item"><span class="side-key">温度</span><span class="side-val">{{ fieldContext.weather?.temperature_c || '-' }}°C</span></div>
            <div class="side-item"><span class="side-key">湿度</span><span class="side-val">{{ fieldContext.weather?.humidity_pct || '-' }}%</span></div>
            <div class="side-item"><span class="side-key">降水</span><span class="side-val">{{ fieldContext.weather?.precipitation_mm || '-' }}mm</span></div>
            <div class="side-item"><span class="side-key">风速</span><span class="side-val">{{ fieldContext.weather?.wind_speed_ms || '-' }}m/s</span></div>
          </div>
        </div>

        <div class="side-card" v-if="fieldContext">
          <div class="side-card-title"><ClipboardList :size="14" /> 田块信息</div>
          <div class="side-grid">
            <div class="side-item"><span class="side-key">名称</span><span class="side-val">{{ fieldContext.field?.name }}</span></div>
            <div class="side-item"><span class="side-key">作物</span><span class="side-val">{{ fieldContext.field?.crop_type || '-' }}</span></div>
            <div class="side-item"><span class="side-key">面积</span><span class="side-val">{{ fieldContext.field?.area_ha }} ha</span></div>
            <div class="side-item"><span class="side-key">亩数</span><span class="side-val">{{ (fieldContext.field?.area_ha * 15).toFixed(0) }} 亩</span></div>
          </div>
        </div>

        <!-- 状态卡片 -->
        <div class="side-card status-card">
          <div class="side-card-title"><Activity :size="14" /> 平台状态</div>
          <div class="status-list">
            <div class="status-line"><span class="status-dot green"></span> 管理田块 {{ platformStats.field_count || 0 }} 块</div>
            <div class="status-line"><span class="status-dot blue"></span> 碳汇追踪 {{ platformStats.total_carbon_tco2e || 0 }} t</div>
            <div class="status-line"><span class="status-dot amber"></span> 农机在线 {{ platformStats.machinery_online || 0 }} 台</div>
            <div class="status-line"><span class="status-dot green"></span> 用户 {{ platformStats.user_count || 0 }} 人</div>
          </div>
        </div>

        <!-- 快捷分析 -->
        <div class="side-card">
          <div class="side-card-title"><Zap :size="14" /> 快捷分析</div>
          <div class="quick-list">
            <button v-for="p in quickPrompts" :key="p.type" class="quick-btn" @click="quickAnalyze(p.type)" :disabled="!selectedFieldId">
              <component :is="p.icon" :size="14" />
              <span>{{ p.label }}</span>
            </button>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import api from '../api'
import {
  Bot, User, Send, Sparkles, Satellite, Clock, Activity, Zap,
  ClipboardList, CloudSun, Globe, SatelliteDish, Sprout, TrendingUp, Truck
} from 'lucide-vue-next'

const fields = ref([])
const selectedFieldId = ref('')
const query = ref('')
const loading = ref(false)
const result = ref(null)
const fieldContext = ref(null)
const messages = ref([])
const messagesRef = ref(null)
const currentTime = ref('')
const thinkText = ref('正在分析遥感数据...')
const platformStats = ref({ today_operation_mu: 0, total_carbon_tco2e: 0, machinery_online: 0 })
const aiStatus = ref({ available: false, model: null, mode: 'rule-based' })

const selectedField = computed(() => fields.value.find(f => f.id === selectedFieldId.value))

const quickPrompts = [
  { type: 'soil', label: '土壤诊断', icon: Sprout },
  { type: 'carbon', label: '碳汇评估', icon: Globe },
  { type: 'yield', label: '产量预测', icon: TrendingUp },
  { type: 'ndvi', label: 'NDVI 分析', icon: SatelliteDish },
  { type: 'plan', label: '作业建议', icon: Truck },
]

const thinkTexts = [
  '正在分析遥感数据...',
  '正在匹配农机轨迹...',
  '正在生成碳汇评估...',
  '正在检索土壤剖面...',
  '正在计算最优方案...',
]

function updateTime() {
  currentTime.value = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  updateTime()
  setInterval(updateTime, 60000)
  try { const { data } = await api.get('/fields'); fields.value = data.items || [] } catch {}
  try { const { data } = await api.get('/platform/stats'); if (data) platformStats.value = data } catch {}
  try { const { data } = await api.get('/agent/status'); if (data) aiStatus.value = data } catch {}
})

watch(selectedFieldId, async (id) => {
  result.value = null
  if (!id) { fieldContext.value = null; return }
  try {
    const f = fields.value.find(x => x.id === id)
    if (!f) return
    const geom = JSON.parse(f.geom)
    const coords = geom.coordinates?.[0]?.[0]
    if (!coords) return
    const [lon, lat] = coords
    const [sRes, wRes] = await Promise.all([
      api.get('/raster/soil-profile', { params: { lon, lat } }),
      api.get('/weather/current', { params: { lat, lon } }),
    ])
    fieldContext.value = { field: f, soil: sRes.data, weather: wRes.data }
  } catch {}
})

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  })
}

async function analyze() {
  if (!query.value.trim() || loading.value || !selectedFieldId.value) return
  const userMsg = query.value
  messages.value.push({ role: 'user', text: userMsg })
  query.value = ''
  loading.value = true
  scrollToBottom()

  // 随机思考文本
  thinkText.value = thinkTexts[Math.floor(Math.random() * thinkTexts.length)]

  try {
    let message = userMsg
    if (fieldContext.value) {
      const ctx = fieldContext.value
      message = `【田块信息】名称:${ctx.field.name} 作物:${ctx.field.crop_type} 面积:${ctx.field.area_ha}公顷
【土壤数据】SOC:${ctx.soil?.soc?.toFixed(1) || '-'}g/kg pH:${ctx.soil?.ph?.toFixed(1) || '-'} 质地:${ctx.soil?.texture_name || '-'} DEM:${ctx.soil?.dem?.toFixed(0) || '-'}m 坡度:${ctx.soil?.slope?.toFixed(1) || '-'}°
【天气数据】温度:${ctx.weather?.temperature_c || '-'}°C 湿度:${ctx.weather?.humidity_pct || '-'}% 降水:${ctx.weather?.precipitation_mm || '-'}mm
【用户问题】${userMsg}`
    }
    const { data } = await api.post('/agent/chat', { message, field_id: selectedFieldId.value })
    messages.value.push({ role: 'ai', text: data?.reply || '分析完成，但未返回结果。' })
  } catch {
    messages.value.push({ role: 'ai', text: 'AI 服务暂时不可用，请稍后重试。' })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function quickAnalyze(type) {
  const prompts = {
    soil: '请根据上述土壤数据，评估地块养分状况，给出施肥和改良建议',
    carbon: '请根据土壤有机碳和作物类型，评估碳汇潜力和最优秸秆还田策略',
    yield: '请根据土壤和天气数据，预测该地块产量水平及主要限制因素',
    ndvi: '请结合土壤和天气数据，分析该地块作物生长状况和NDVI趋势',
    plan: '请综合土壤、天气数据，给出近期农机作业建议、腐解剂推荐和预计效果',
  }
  query.value = prompts[type] || ''
  analyze()
}

function formatReply(text) {
  if (!text) return ''
  const escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  return escaped.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
}
</script>

<style scoped>
.ws-page {
  height: 100vh; display: flex; flex-direction: column;
  background: #f5f7f5; color: #1a1a1a;
  position: relative; overflow: hidden;
}

/* 背景纹理 */
.ws-bg-pattern {
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image:
    linear-gradient(rgba(22,163,74,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22,163,74,0.03) 1px, transparent 1px);
  background-size: 60px 60px;
}

/* 顶栏 */
.ws-topbar {
  position: relative; z-index: 10;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 var(--space-5); height: 48px;
  background: #fff; backdrop-filter: blur(20px);
  border-bottom: 1px solid #e5e7eb;
}
.topbar-left { display: flex; align-items: center; gap: 8px; color: #16a34a; }
.topbar-title { font-size: var(--text-sm); font-weight: var(--weight-bold); color: #1a1a1a; }
.topbar-badge {
  font-size: 10px; padding: 2px 8px; border-radius: var(--radius-full);
  background: #e8f5e9; color: #16a34a;
  font-weight: var(--weight-semibold); letter-spacing: 0.5px;
}
.topbar-center { flex: 1; display: flex; justify-content: center; }
.field-select {
  padding: 6px 14px; border-radius: var(--radius-sm);
  background: #fff; border: 1px solid #e0e0e0;
  color: #333; font-size: var(--text-sm); min-width: 200px;
}
.field-select:focus { outline: none; border-color: #16a34a; }
.topbar-right { display: flex; align-items: center; gap: 8px; }
.status-chip {
  display: flex; align-items: center; gap: 4px;
  font-size: 11px; color: #888;
  padding: 3px 10px; border-radius: var(--radius-full);
  background: #f5f5f5;
}
.status-chip.online { color: #16a34a; }
.status-chip.offline { color: #D97706; }
.dot { width: 6px; height: 6px; border-radius: 50%; background: #22C55E; box-shadow: 0 0 6px rgba(34,197,94,0.4); }
.status-chip.offline .dot { background: #D97706; box-shadow: 0 0 6px rgba(217,119,6,0.4); }

/* 主体 */
.ws-main { flex: 1; display: flex; position: relative; z-index: 1; overflow: hidden; }

/* 对话区 */
.ws-chat { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.chat-messages {
  flex: 1; overflow-y: auto; padding: var(--space-5);
  display: flex; flex-direction: column; gap: var(--space-4);
}

/* 空状态 */
.chat-empty {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center; text-align: center;
  padding: var(--space-8);
}
.chat-empty .empty-icon { color: #16a34a; opacity: 0.3; margin-bottom: var(--space-4); }
.chat-empty h3 { font-size: var(--text-xl); font-weight: var(--weight-bold); color: #1a1a1a; margin-bottom: var(--space-2); }
.chat-empty p { font-size: var(--text-sm); color: #888; max-width: 400px; margin-bottom: var(--space-6); }
.empty-prompts { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.prompt-chip {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 16px; border-radius: var(--radius-full);
  background: #fff; border: 1px solid #e0e0e0;
  color: #666; font-size: var(--text-sm); cursor: pointer;
  transition: all var(--duration-fast);
}
.prompt-chip:hover { background: #e8f5e9; border-color: #16a34a; color: #16a34a; }
.prompt-chip:disabled { opacity: 0.4; cursor: not-allowed; }

/* 消息气泡 */
.msg { display: flex; gap: var(--space-3); }
.msg.user { flex-direction: row-reverse; }
.msg-avatar {
  width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: #f0f0f0; color: #888;
}
.msg.user .msg-avatar { background: #e8f5e9; color: #16a34a; }
.msg-content { max-width: 70%; min-width: 0; }
.msg.user .msg-content { text-align: right; }
.msg-name { font-size: 11px; color: #aaa; margin-bottom: 4px; }
.msg-bubble {
  padding: var(--space-3) var(--space-4); border-radius: var(--radius-md);
  font-size: var(--text-sm); line-height: var(--leading-relaxed);
  background: #fff; border: 1px solid #e5e7eb;
  color: #333;
}
.msg.user .msg-bubble {
  background: #e8f5e9; border-color: #c8e6c9;
  color: #1a5c2e;
}

/* 思考动画 */
.thinking { display: flex; align-items: center; gap: 10px; }
.think-dots { display: flex; gap: 4px; }
.think-dots span {
  width: 6px; height: 6px; border-radius: 50%;
  background: #16a34a;
  animation: dotPulse 1.4s ease-in-out infinite;
}
.think-dots span:nth-child(2) { animation-delay: 0.2s; }
.think-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotPulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}
.think-text { font-size: var(--text-xs); color: #999; }

/* 输入区 */
.chat-input-area {
  padding: var(--space-3) var(--space-5);
  border-top: 1px solid #e5e7eb;
  background: #fff;
}
.input-wrapper {
  display: flex; align-items: center; gap: 8px;
  background: #f5f5f5; border: 1px solid #e0e0e0;
  border-radius: 16px; padding: 6px 6px 6px 18px;
  transition: border-color var(--duration-fast);
}
.input-wrapper:focus-within { border-color: #16a34a; background: #fff; }
.chat-input {
  flex: 1; background: none; border: none; outline: none;
  color: #333; font-size: var(--text-sm);
  height: 40px;
}
.chat-input::placeholder { color: #bbb; }
.send-btn {
  width: 40px; height: 40px; border-radius: 12px;
  background: #16a34a; border: none;
  color: #fff; cursor: pointer; display: flex;
  align-items: center; justify-content: center;
  transition: all var(--duration-fast);
}
.send-btn:hover { background: #15803d; }
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* 右侧边栏 */
.ws-sidebar {
  width: 280px; flex-shrink: 0; overflow-y: auto;
  border-left: 1px solid #e5e7eb;
  padding: var(--space-4); display: flex;
  flex-direction: column; gap: var(--space-3);
  background: #fff;
}
.side-card {
  background: #f9faf9; border: 1px solid #e8ece8;
  border-radius: var(--radius-sm); padding: var(--space-3);
}
.side-card-title {
  display: flex; align-items: center; gap: 6px;
  font-size: 11px; font-weight: var(--weight-semibold);
  color: #888; text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  margin-bottom: var(--space-2); padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}
.side-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.side-item { display: flex; flex-direction: column; }
.side-key { font-size: 10px; color: #aaa; }
.side-val { font-size: var(--text-sm); color: #333; font-weight: var(--weight-medium); }

.status-list { display: flex; flex-direction: column; gap: 8px; }
.status-line { display: flex; align-items: center; gap: 8px; font-size: var(--text-xs); color: #888; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.status-dot.green { background: #22C55E; }
.status-dot.blue { background: #3B82F6; }
.status-dot.amber { background: #D97706; }

.quick-list { display: flex; flex-direction: column; gap: 4px; }
.quick-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; border-radius: var(--radius-xs);
  background: none; border: 1px solid transparent;
  color: #888; font-size: var(--text-xs);
  cursor: pointer; transition: all var(--duration-fast);
  text-align: left;
}
.quick-btn:hover { background: #e8f5e9; border-color: #e8ece8; color: #16a34a; }
.quick-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* 响应式 */
@media (max-width: 900px) {
  .ws-sidebar { display: none; }
  .topbar-right { display: none; }
}
</style>
