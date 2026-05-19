<template>
  <div class="prod-page">
    <!-- Hero 区域 -->
    <section class="prod-hero">
      <div class="hero-overlay"></div>
      <div class="hero-content">
        <div class="hero-text">
          <span class="hero-overline">AgriSpatial 产品中心</span>
          <h1>秸秆腐解剂 <br/><span class="accent">四大配方，精准匹配</span></h1>
          <p>针对不同土壤类型和气候条件，提供速效、标准、保水、增肥四种配方，让秸秆高效转化为土壤有机质。</p>
          <div class="hero-tabs">
            <button :class="['tab-btn', { active: tab === 'decomposer' }]" @click="tab = 'decomposer'">
              <FlaskConical :size="16" /> 秸秆腐解剂
            </button>
            <button :class="['tab-btn', { active: tab === 'machinery' }]" @click="tab = 'machinery'">
              <Tractor :size="16" /> 农业机械
            </button>
          </div>
        </div>
        <div class="hero-visual">
          <div class="float-product">
            <ProductImage :type="heroImageType" :photo="tab === 'decomposer' ? '/decomposer_fast.jpg' : '/tractor_farm.jpg'" />
          </div>
          <div class="float-label label-1">
            <Zap :size="12" /> 腐熟效率 ↑{{ productStats.decomposer_efficiency }}
          </div>
          <div class="float-label label-2">
            <Clock :size="12" /> {{ productStats.decomposer_days }}
          </div>
          <div class="float-label label-3">
            <Leaf :size="12" /> SOC 提升 {{ productStats.soc_increase }}
          </div>
        </div>
      </div>
    </section>

    <!-- 产品展示 -->
    <section class="prod-showcase">
      <div class="showcase-inner">
        <!-- 腐解剂 -->
        <template v-if="tab === 'decomposer'">
          <div v-for="(d, i) in decomposers" :key="d.id" :class="['showcase-row', { reverse: i % 2 === 1 }]">
            <div class="showcase-visual">
              <div class="showcase-img-wrap" :style="{ '--accent': d.accent }">
                <div class="float-product-sm">
                  <ProductImage :type="d.imageType" :photo="d.photo" />
                </div>
              </div>
            </div>
            <div class="showcase-info">
              <span class="showcase-badge" :style="{ background: d.accent + '18', color: d.accent }">{{ d.type }}</span>
              <h2>{{ d.name }}</h2>
              <p class="showcase-desc">{{ d.description }}</p>
              <div class="showcase-specs">
                <div class="spec-pill"><Clock :size="14" /> {{ d.decomposition_days }}天腐解</div>
                <div class="spec-pill"><Sprout :size="14" /> {{ d.suitable_crops }}</div>
                <div class="spec-pill"><Droplets :size="14" /> {{ d.usage_guide }}</div>
              </div>
              <div class="showcase-features">
                <span v-for="f in d.features" :key="f" class="feat-tag">{{ f }}</span>
              </div>
            </div>
          </div>
        </template>

        <!-- 农机 -->
        <template v-if="tab === 'machinery'">
          <div v-for="(m, i) in machineryList" :key="m.id" :class="['showcase-row', { reverse: i % 2 === 1 }]">
            <div class="showcase-visual">
              <div class="showcase-img-wrap" :style="{ '--accent': m.accent }">
                <div class="float-product-sm">
                  <ProductImage :type="m.imageType" :photo="m.photo" />
                </div>
              </div>
            </div>
            <div class="showcase-info">
              <span class="showcase-badge" :style="{ background: m.accent + '18', color: m.accent }">{{ m.type }}</span>
              <h2>{{ m.name }}</h2>
              <p class="showcase-desc">{{ m.description }}</p>
              <div class="showcase-specs">
                <div v-for="(v, k) in m.specs" :key="k" class="spec-pill">
                  <component :is="specIcons[k] || Wrench" :size="14" /> {{ v }}
                </div>
              </div>
              <div class="text-xs text-muted" style="margin-top:8px;color:var(--surface-700)">适用：{{ m.suitableFor }}</div>
            </div>
          </div>
          <!-- 爆炸视图（仅当有 3D 模型的产品） -->
          <div v-for="m in machineryWithExploded" :key="'exp-' + m.id" class="exploded-section">
            <h3 class="section-title">{{ m.name }} — 结构爆炸图</h3>
            <div class="exploded-wrap">
              <ExplodedViewGallery :images="m.explodedViews" />
            </div>
          </div>
        </template>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'
import ProductImage from '../components/ProductImage.vue'
import { defineAsyncComponent } from 'vue'
const ExplodedViewGallery = defineAsyncComponent(() => import('../components/ExplodedViewGallery.vue'))
import { decomposers as fallbackDecomposers } from '../data/decomposers.js'
import { machinery as fallbackMachinery } from '../data/machinery.js'
import {
  FlaskConical, Tractor, Zap, Clock, Leaf, Sprout, Droplets, Wrench,
  Gauge, Ruler, Fuel, Navigation, BarChart3, Wind, Grid3X3, Timer
} from 'lucide-vue-next'

const tab = ref('decomposer')
const decomposers = ref(fallbackDecomposers)
const machineryList = ref(fallbackMachinery)
const productStats = ref({ decomposer_efficiency: '42%', decomposer_days: '7天快速腐解', soc_increase: '18%' })

const heroImageType = computed(() => tab.value === 'decomposer' ? 'decomposer-fast' : 'tractor')
const machineryWithExploded = computed(() => machineryList.value.filter(m => m.explodedViews))

const specIcons = {
  power: Gauge, width: Ruler, fuel: Fuel, nav: Navigation,
  capacity: BarChart3, loss: Wind, tank: Droplets, drones: Tractor,
  save: Leaf, depth: Ruler, rate: Grid3X3, rows: Grid3X3, spacing: Ruler, speed: Timer,
}

onMounted(async () => {
  try {
    const [dRes, mRes, sRes] = await Promise.all([
      api.get('/products/decomposers'),
      api.get('/products/machinery'),
      api.get('/products/stats'),
    ])

    if (dRes.data?.items?.length) {
      decomposers.value = dRes.data.items.map(d => ({
        ...d,
        imageType: d.image_type ?? d.imageType,
        photo: d.photo ?? '',
      }))
    }

    if (mRes.data?.items?.length) {
      const localMap = Object.fromEntries(fallbackMachinery.map(m => [m.id, m]))
      const apiIds = new Set()
      const mapped = mRes.data.items.map(m => {
        apiIds.add(m.id)
        const local = localMap[m.id]
        return {
          ...m,
          imageType: m.image_type ?? m.imageType,
          photo: m.photo ?? '',
          specs: typeof m.specs === 'string' ? JSON.parse(m.specs) : (m.specs || {}),
          suitableFor: m.suitable_for ?? m.suitableFor,
          explodedViews: local?.explodedViews,
        }
      })
      // 追加本地独有的项目（如带 3D 模型的切割小车）
      const extras = fallbackMachinery.filter(m => !apiIds.has(m.id))
      machineryList.value = [...mapped, ...extras]
    }

    if (sRes.data) productStats.value = sRes.data
  } catch {
    // API unavailable – fallback data already set
  }
})
</script>

<style scoped>
.prod-page { min-height: 100vh; background: var(--surface-50); }

/* Hero */
.prod-hero {
  position: relative; min-height: 55vh;
  background: url(/field-bg.jpg) center/cover no-repeat;
  display: flex; align-items: center;
  overflow: hidden;
}
.hero-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(135deg, rgba(12,17,23,0.92) 0%, rgba(19,28,38,0.85) 100%);
}
.hero-content {
  position: relative; z-index: 1;
  max-width: 1200px; width: 100%; margin: 0 auto;
  padding: var(--space-10) var(--space-6);
  display: flex; align-items: center; gap: var(--space-10);
}
.hero-text { flex: 1; }
.hero-overline {
  display: inline-block; font-size: 11px; font-weight: var(--weight-semibold);
  text-transform: uppercase; letter-spacing: 3px; color: var(--color-primary-300);
  margin-bottom: var(--space-4);
}
.hero-text h1 {
  font-size: clamp(2rem, 4vw, 3rem); font-weight: var(--weight-bold);
  color: #fff; line-height: 1.2; margin-bottom: var(--space-4);
}
.hero-text h1 .accent { color: var(--color-primary-300); }
.hero-text p { font-size: var(--text-base); color: rgba(255,255,255,0.6); max-width: 480px; margin-bottom: var(--space-6); }

.hero-tabs { display: flex; gap: var(--space-2); }
.tab-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 20px; border-radius: var(--radius-sm);
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.10);
  color: rgba(255,255,255,0.7); font-size: var(--text-sm); cursor: pointer;
  transition: all var(--duration-fast);
}
.tab-btn:hover { background: rgba(255,255,255,0.10); color: #fff; }
.tab-btn.active { background: var(--color-primary); border-color: var(--color-primary); color: #fff; }

.hero-visual {
  position: relative; flex-shrink: 0;
  width: 280px; height: 240px;
}
.float-product {
  animation: float 4s ease-in-out infinite;
}
.float-label {
  position: absolute; padding: 6px 14px; border-radius: var(--radius-full);
  background: rgba(255,255,255,0.10); backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.08);
  font-size: 12px; color: rgba(255,255,255,0.8);
  display: flex; align-items: center; gap: 6px;
  white-space: nowrap;
  animation: float 5s ease-in-out infinite;
}
.label-1 { top: 20px; right: -20px; animation-delay: 0.5s; }
.label-2 { bottom: 60px; left: -30px; animation-delay: 1s; }
.label-3 { bottom: 10px; right: -10px; animation-delay: 1.5s; }

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

/* Showcase */
.prod-showcase { padding: var(--space-10) 0; }
.showcase-inner { max-width: 1100px; margin: 0 auto; padding: 0 var(--space-6); display: flex; flex-direction: column; gap: var(--space-10); }

.showcase-row { display: flex; align-items: center; gap: var(--space-10); }
.showcase-row.reverse { flex-direction: row-reverse; }

.showcase-visual { flex: 0 0 320px; display: flex; justify-content: center; }
.showcase-img-wrap {
  position: relative; padding: var(--space-8);
  background: linear-gradient(135deg, var(--surface-0) 0%, var(--surface-50) 100%);
  border-radius: 20px; border: 1px solid var(--surface-200);
  box-shadow: var(--shadow-md);
}
.showcase-img-wrap::before {
  content: ''; position: absolute; inset: -1px;
  border-radius: 20px; padding: 1px;
  background: linear-gradient(135deg, var(--accent, var(--color-primary)) 0%, transparent 60%);
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask-composite: exclude; -webkit-mask-composite: xor;
  opacity: 0.3;
}
.float-product-sm { animation: float 5s ease-in-out infinite; }

.showcase-info { flex: 1; min-width: 0; }
.showcase-badge {
  display: inline-block; padding: 4px 12px; border-radius: var(--radius-full);
  font-size: 12px; font-weight: var(--weight-semibold);
  margin-bottom: var(--space-3);
}
.showcase-info h2 {
  font-size: var(--text-2xl); font-weight: var(--weight-bold);
  color: var(--surface-900); margin-bottom: var(--space-3);
  letter-spacing: var(--tracking-tight);
}
.showcase-desc {
  font-size: var(--text-base); color: var(--surface-700);
  line-height: var(--leading-relaxed); margin-bottom: var(--space-4);
}

.showcase-specs {
  display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: var(--space-4);
}
.spec-pill {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: var(--radius-full);
  background: var(--surface-50); border: 1px solid var(--surface-200);
  font-size: var(--text-xs); color: var(--surface-800);
}

.showcase-features { display: flex; flex-wrap: wrap; gap: 6px; }
.feat-tag {
  padding: 4px 12px; border-radius: var(--radius-xs);
  background: var(--color-primary-50); color: var(--color-primary-300);
  font-size: 11px; font-weight: var(--weight-medium);
}

/* 爆炸视图区域 */
.exploded-section {
  max-width: 1100px; margin: 0 auto;
  padding: 0 var(--space-6);
  margin-top: var(--space-6);
}
.section-title {
  font-size: var(--text-lg); font-weight: var(--weight-bold);
  color: var(--surface-800); margin-bottom: var(--space-4);
  text-align: center;
}
.exploded-wrap {
  max-width: 560px; margin: 0 auto;
}

@media (max-width: 768px) {
  .hero-content { flex-direction: column; text-align: center; }
  .hero-text p { margin-left: auto; margin-right: auto; }
  .hero-tabs { justify-content: center; }
  .hero-visual { width: 200px; height: 180px; }
  .showcase-row, .showcase-row.reverse { flex-direction: column; }
  .showcase-visual { flex: none; }
  .exploded-wrap { max-width: 100%; }
}
</style>
