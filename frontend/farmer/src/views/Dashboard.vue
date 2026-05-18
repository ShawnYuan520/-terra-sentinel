<template>
  <div class="dashboard">
    <!-- ═══════ Hero — 全屏照片背景 ═══════ -->
    <section class="hero">
      <div class="hero-bg" style="background-image:url('/hero-bg.jpg')"></div>
      <div class="hero-content">
        <div class="hero-logo">
          <img src="/logo.jpg" alt="AgriSpatial" class="logo-img" />
        </div>
        <div class="hero-badge">东北玉米带 · 秸秆综合利用 · 遥感精准管理</div>
        <h1>让每一亩秸秆<span class="hero-accent"> 变废为宝</span></h1>
        <p class="hero-desc">
          卫星遥感评估地块 <ArrowRight :size="14" /> AI匹配腐解剂 <ArrowRight :size="14" /> 农机精准作业 <ArrowRight :size="14" /> 碳汇量化交易<br>
          覆盖黑龙江、吉林、辽宁、内蒙古东部玉米主产区
        </p>
        <div class="hero-actions">
          <router-link to="/map" class="btn-primary-hero">进入 GIS 平台</router-link>
          <a href="#decomposer" class="btn-outline-hero">了解腐解剂</a>
          <router-link v-if="!isLoggedIn" to="/login" class="btn-outline-hero"><LogIn :size="14" /> 登录</router-link>
          <router-link v-if="!isLoggedIn" to="/register" class="btn-outline-hero"><UserPlus :size="14" /> 注册</router-link>
        </div>
      </div>
      <div class="hero-scroll-hint">
        <span></span>
      </div>
    </section>

    <!-- ═══════ 痛点引入 — 大图+文字 ═══════ -->
    <section class="section section-white">
      <div class="section-inner pain-grid">
        <div class="pain-text">
          <span class="overline">东北玉米带的挑战</span>
          <h2>每年数亿吨秸秆<br>烧不得、埋不掉、用不好</h2>
          <p>东北三省一区玉米播种面积超 <b>2.6亿亩</b>，年产秸秆约 <b>1.8亿吨</b>。传统焚烧已被全面禁止，直接还田面临低温腐解慢、病虫害累积、影响下茬出苗三大难题。</p>
          <p>我们的方案：<b>遥感精准诊断 × 腐解剂定向匹配 × 农机标准化作业 × 碳汇量化追踪</b>——把秸秆处理从"负担"变成"资产"。</p>
        </div>
        <div class="pain-photo" style="background-image:url('/corn_harvest.jpg')">
          <div class="pain-photo-label">东北玉米收获后 · 秸秆还田现场</div>
        </div>
      </div>
    </section>

    <!-- ═══════ 技术底图穿插 — 全幅照片+毛玻璃卡片 ═══════ -->
    <section class="section section-photo" style="background-image:url('/tech-bg.jpg')">
      <div class="section-photo-overlay"></div>
      <div class="section-inner section-photo-content">
        <span class="overline overline-light">技术底座</span>
        <h2>卫星从天上看，算法在地上算</h2>
        <p>10层30米分辨率栅格覆盖东北全境，从太空到田块的数字化</p>
        <div class="tech-grid">
          <div class="tech-glass-card" v-for="t in techs" :key="t.title">
            <div class="tech-glass-icon"><component :is="t.icon" :size="20" /></div>
            <h3>{{ t.title }}</h3>
            <p>{{ t.desc }}</p>
            <span class="tech-tag">{{ t.tag }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════ 腐解剂产品 — 浅色底 ═══════ -->
    <section class="section section-light" id="decomposer">
      <div class="section-inner">
        <div class="section-head">
          <span class="overline">核心产品</span>
          <h2>秸秆腐解剂系列 — 四款配方，精准匹配</h2>
          <p>基于东北黑土区土壤栅格数据 + 作物类型，AI 推荐最优腐解剂</p>
        </div>
        <div class="decomposer-grid">
          <div v-for="d in decomposers" :key="d.id" class="d-card">
            <div class="d-img-wrap">
              <img :src="d.photo" :alt="d.name" class="d-photo" />
              <div class="d-badge-top" :style="{ background: d.accent }">{{ d.type }}</div>
            </div>
            <div class="d-body">
              <h3>{{ d.name }}</h3>
              <p>{{ d.description }}</p>
              <div class="d-features">
                <span v-for="f in d.features" :key="f" class="d-feat">{{ f }}</span>
              </div>
              <div class="d-meta">
                <div><b>腐解周期</b> {{ d.decomposition_days }} 天</div>
                <div><b>适用作物</b> {{ d.suitable_crops }}</div>
                <div><b>适用土壤</b> {{ d.suitable_soil }}</div>
                <div><b>推荐用量</b> {{ d.usage_guide }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════ 作业流程 ═══════ -->
    <section class="section section-white">
      <div class="section-inner">
        <div class="section-head">
          <span class="overline">标准化作业</span>
          <h2>从秸秆到碳汇，四步闭环</h2>
        </div>
        <div class="flow-row">
          <div v-for="(step, i) in workflow" :key="i" class="flow-step">
            <div class="flow-num-ring">
              <span class="flow-num">{{ i + 1 }}</span>
            </div>
            <div class="flow-photo" :style="{ backgroundImage: 'url(' + step.photo + ')' }"></div>
            <h3>{{ step.title }}</h3>
            <p>{{ step.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════ 农机装备 — 深色照片底 ═══════ -->
    <section class="section section-dark-photo" style="background-image:url('/field-bg.jpg')">
      <div class="section-photo-overlay dark"></div>
      <div class="section-inner section-photo-content">
        <span class="overline overline-light">智能装备</span>
        <h2>北斗导航 + AI视觉，精准到厘米</h2>
        <p>适配120-180马力拖拉机，覆盖耕、种、管、收全环节</p>
        <div class="mach-grid">
          <div v-for="m in machineryList.slice(0,4)" :key="m.id" class="m-glass-card">
            <div class="m-photo" :style="{ backgroundImage: 'url(' + m.photo + ')' }"></div>
            <div class="m-body">
              <span class="badge badge-outline" :style="{borderColor:m.accent, color:m.accent}">{{ m.type }}</span>
              <h3>{{ m.name }}</h3>
              <p>{{ m.description }}</p>
              <div class="m-specs">
                <span v-for="(v,k) in m.specs" :key="k" class="m-spec">{{ specLabels[k] || k }}: <b>{{ v }}</b></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════ 平台能力 ═══════ -->
    <section class="section section-light">
      <div class="section-inner">
        <div class="section-head">
          <span class="overline">平台能力</span>
          <h2>从卫星到田块，全链路数据贯通</h2>
        </div>
        <div class="data-showcase">
          <div class="data-show-item" v-for="item in platformPowers" :key="item.label" :style="{ '--accent': item.color }">
            <div class="show-accent"></div>
            <div class="show-body">
              <span class="show-icon"><component :is="item.icon" :size="22" /></span>
              <span class="show-label">{{ item.label }}</span>
              <span class="show-sub">{{ item.sub }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════ CTA — 全幅照片 ═══════ -->
    <section class="cta" style="background-image:url('/soil-bg.jpg')">
      <div class="cta-overlay"></div>
      <div class="cta-content">
        <h2>准备好让秸秆变碳汇了吗</h2>
        <p>免费注册，画一块地，看看你的田适合哪种腐解剂</p>
        <router-link to="/register" class="btn-primary-hero">免费注册</router-link>
        <p class="cta-sub">已有账号？<router-link to="/login">立即登录</router-link></p>
      </div>
    </section>

    <!-- ═══════ Footer ═══════ -->
    <footer class="footer">
      <div class="footer-inner">
        <div class="footer-grid">
          <div class="footer-col">
            <b>AgriSpatial</b>
            <p>秸秆腐解 · 农机协同<br>遥感空间数据平台</p>
          </div>
          <div class="footer-col">
            <b>产品</b>
            <p>腐解剂系列 · 农机装备<br>GIS平台 · AI分析</p>
          </div>
          <div class="footer-col">
            <b>技术</b>
            <p>Sentinel-2遥感 · 30m栅格<br>RothC碳汇 · CUSUM物候</p>
          </div>
          <div class="footer-col">
            <b>联系</b>
            <p>东北农业遥感实验室<br>哈尔滨</p>
          </div>
        </div>
        <p class="footer-bottom">© 2026 AgriSpatial · NASA DEM · 武大CLCD · SoilGrids · OpenWeather · ESA Sentinel-2</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, computed } from 'vue'
import { ArrowRight, ChartBar, ClipboardList, CloudSun, FlaskConical, Globe, LogIn, SatelliteDish, Sparkles, UserPlus } from 'lucide-vue-next'

const isLoggedIn = computed(() => !!localStorage.getItem('token'))
// Dashboard 是独立全宽页面，需要覆盖全局的 overflow:hidden
onMounted(() => {
  document.documentElement.style.overflow = 'auto'
  document.body.style.overflow = 'auto'
})
onUnmounted(() => { document.documentElement.style.overflow = 'hidden'; document.body.style.overflow = 'hidden' })

const platformPowers = [
  { icon: SatelliteDish, label: '卫星遥感时序分析', sub: 'Sentinel-2 NDVI 时序', color: '#16a34a' },
  { icon: FlaskConical, label: '土壤有机碳空间分布', sub: '30m SOC 栅格', color: '#a16207' },
  { icon: ChartBar, label: '碳汇模型逐年追踪', sub: 'RothC 碳汇预测', color: '#2563eb' },
  { icon: ClipboardList, label: '一键生成碳汇报告', sub: 'PDF 碳汇报告', color: '#ea580c' },
  { icon: Sparkles, label: '耕地质量智能评级', sub: 'AHP+TOPSIS', color: '#7c3aed' },
]

const decomposers = [
  {
    id: 'd-001', name: '高活性腐解剂 · 北方型', type: '速效型',
    description: '专为东北黑土区低温环境设计。在5°C以上即可启动腐解，15天内完成秸秆纤维分解，同步抑制土壤病原菌和地下害虫，减少下茬病虫害发生率40%以上。',
    suitable_crops: '玉米、小麦、水稻', suitable_soil: '黑土、草甸土、白浆土',
    usage_guide: '每亩 5kg，秸秆还田后均匀喷施',
    decomposition_days: 15,
    features: ['快速腐解', '抑菌驱虫', '耐低温启动', '促根壮苗'],
    accent: '#2EC85D',
    photo: '/lab_science.jpg',
  },
  {
    id: 'd-002', name: '温和型腐解剂 · 标准', type: '标准型',
    description: '适合有机质含量丰富的地块，温和释放养分，维持土壤微生态平衡。避免养分过快释放导致的烧苗和淋失，尤其适合大豆等对氮敏感的作物前茬。',
    suitable_crops: '小麦、大豆、甜菜', suitable_soil: '棕壤、褐土、暗棕壤',
    usage_guide: '每亩 3kg，与秸秆混合翻压',
    decomposition_days: 25,
    features: ['维持微生态', '缓释养分', '减少板结', '保墒保水'],
    accent: '#8B5E3C',
    photo: '/soil_earth.jpg',
  },
  {
    id: 'd-003', name: '保水型腐解剂 · 旱作区', type: '保水型',
    description: '针对松嫩平原西部和吉林西部旱作区，增强土壤保水能力，减少蒸发损失30%，提高水分利用效率。配合覆土灌溉使用效果更佳。',
    suitable_crops: '玉米、高粱、马铃薯、谷子', suitable_soil: '栗钙土、风沙土、黄绵土',
    usage_guide: '每亩 4kg，覆土后灌溉',
    decomposition_days: 20,
    features: ['保水抗旱', '缓释腐解', '提高出苗率', '抗风蚀'],
    accent: '#3B82F6',
    photo: '/field_rows.jpg',
  },
  {
    id: 'd-004', name: '高肥型腐解剂 · 增产型', type: '增肥型',
    description: '加速秸秆碳向土壤有机质转化，显著提升SOC含量。针对有机质偏低的中低产田，连续使用2-3季可提升土壤有机碳15-25%，增产10-15%。',
    suitable_crops: '水稻、玉米、大豆', suitable_soil: '水稻土、潮土、草甸土',
    usage_guide: '每亩 5kg，灌水后施用效果最佳',
    decomposition_days: 18,
    features: ['增碳培肥', '活化养分', '增产10-15%', '改善团粒结构'],
    accent: '#D97706',
    photo: '/corn_harvest.jpg',
  },
]

const specLabels = {
  power: '功率', width: '幅宽', fuel: '燃料', nav: '导航',
  capacity: '效率', loss: '损失率', tank: '药箱', drones: '无人机', save: '节省',
  depth: '耕深', rate: '碎土率', rows: '行数', spacing: '行距', speed: '速度',
}

const machineryList = [
  {
    id: 'm-001', name: 'AgriTrac X500 智能拖拉机', type: '整地机械',
    description: '搭载北斗导航自动驾驶，精度±2.5cm，支持夜间作业。配套旋耕机、播种机、中耕机实现耕整播一体化，日作业效率300-500亩。',
    specs: { power: '150 马力', width: '3.6m 幅宽', fuel: '柴油/国四', nav: '北斗+GPS' },
    suitableFor: '大面积耕整地、播种、中耕追肥',
    accent: '#2EC85D',
    photo: '/tractor_farm.jpg',
  },
  {
    id: 'm-002', name: 'AgriHarvest H300 联合收割机', type: '收获机械',
    description: '全喂入自走式，割幅3.2m，适配玉米小麦大豆。损失率低于1.5%，标配秸秆粉碎还田装置，收割同时完成秸秆抛撒。',
    specs: { power: '180 马力', width: '3.2m 割幅', capacity: '8-12亩/h', loss: '<1.5%' },
    suitableFor: '玉米、小麦、大豆、水稻收获+秸秆粉碎',
    accent: '#D97706',
    photo: '/corn_harvest.jpg',
  },
  {
    id: 'm-003', name: 'AgriSpray S200 智能喷雾器', type: '植保机械',
    description: 'AI视觉识别杂草，变量精准喷施腐解剂和农药，节省药剂30%。无人机+地面自走双模式，适配不同地块大小。',
    specs: { tank: '500L 药箱', width: '12m 喷幅', drones: '2架T40', save: '节药30%' },
    suitableFor: '腐解剂喷施、除草杀虫、叶面肥喷施',
    accent: '#3B82F6',
    photo: '/sprayer_field.jpg',
  },
  {
    id: 'm-004', name: 'AgriTill R150 旋耕机', type: '耕作机械',
    description: '配套120-180马力拖拉机，深耕25cm，碎土率≥85%。专为秸秆还田设计，可将粉碎秸秆与土壤充分混合，加速腐解进程。',
    specs: { power: '120-180hp', depth: '25cm', width: '2.5m', rate: '碎土≥85%' },
    suitableFor: '旋耕灭茬、秸秆还田、平整土地',
    accent: '#8B5E3C',
    photo: '/tractor_working.jpg',
  },
]

const techs = [
  {
    icon: SatelliteDish, title: 'NDVI 植被监测',
    desc: 'ESA Sentinel-2 卫星每5天过境一次，10m分辨率NDVI/EVI双指数，覆盖4年完整时序。自动识别作物出苗、拔节、抽穗、成熟期。',
    tag: 'Sentinel-2 · 10m分辨率',
    photo: '/satellite_view.jpg',
  },
  {
    icon: FlaskConical, title: '土壤数字画像',
    desc: 'NASA SRTM 30m DEM、SoilGrids全球土壤数据库、武大CLCD土地覆盖。每块地8项土壤指标一键查询：SOC、pH、砂粒、粉粒、粘粒、质地、坡度、坡向。',
    tag: '30m栅格 · 8项指标',
    photo: '/soil_earth.jpg',
  },
  {
    icon: CloudSun, title: '农业气象服务',
    desc: '接入OpenWeather实时API，提供当前温度/湿度/降水/风速 + 5日预报 + 积温GDD、干旱风险、霜冻风险等农业专属指标。',
    tag: '实时数据 · 5日预报',
    photo: '/farm_landscape.jpg',
  },
  {
    icon: Globe, title: '碳汇量化评估',
    desc: '基于RothC土壤碳周转模型 + 张丹丹(2024)东北农田实测矿化参数，精准计算秸秆还田碳汇量。输出符合IPCC Tier 1标准的碳汇报告。',
    tag: 'RothC模型 · IPCC标准',
    photo: '/soil_earth.jpg',
  },
]

const workflow = [
  {
    title: '遥感评估', desc: '卫星NDVI+土壤栅格分析地块状态，AI自动推荐腐解剂类型和用量。生成地块诊断报告。',
    photo: '/drone_farm.jpg',
  },
  {
    title: '秸秆还田', desc: '联合收割机收割同时粉碎秸秆，拖拉机配套旋耕机翻压入土25cm，确保秸秆与土壤充分混合。',
    photo: '/harvest_combine.jpg',
  },
  {
    title: '喷施腐解剂', desc: '智能喷雾器按处方精准喷施腐解剂，北斗导航确保全覆盖无遗漏，每亩用量精准到±0.1kg。',
    photo: '/agri_machine.jpg',
  },
  {
    title: '碳汇追踪', desc: '平台持续监测SOC变化，RothC模型逐年预测碳汇趋势，一键生成碳汇报告对接双碳政策。',
    photo: '/satellite_view.jpg',
  },
]


</script>

<style scoped>
/* ═══════════════════════════════════════════
   Dashboard — Linear/Vercel 风格
   大幅照片 · 毛玻璃 · 暗色叠加 · 交错的节奏
   ═══════════════════════════════════════════ */

.dashboard {
  min-height: 100vh; overflow-y: auto;
  background: #fff;
  color: #1a1a1a;
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
}

/* ══════ Layout ══════ */
.section { padding: 140px 24px; position: relative; }
.section-white { background: #fff; }
.section-light { background: #F7F8F5; }
.section-inner { max-width: 1200px; margin: 0 auto; }

.section-photo {
  background-size: cover; background-position: center; background-attachment: fixed;
  padding: 120px 24px; position: relative;
}
.section-photo-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(5,16,8,0.85) 0%, rgba(13,36,24,0.80) 50%, rgba(5,16,8,0.90) 100%);
}
.section-photo-overlay.dark {
  background: linear-gradient(180deg, rgba(5,16,8,0.92) 0%, rgba(10,20,16,0.88) 100%);
}
.section-photo-content { position: relative; z-index: 1; color: #fff; }
.section-photo-content h2 { color: #fff; }
.section-photo-content p { color: rgba(255,255,255,0.55); }

.section-dark-photo {
  background-size: cover; background-position: center; background-attachment: fixed;
  padding: 120px 24px; position: relative;
}

.section-head { text-align: center; margin-bottom: 64px; }
.section-head h2 { font-size: clamp(28px, 4vw, 40px); font-weight: 800; margin-bottom: 14px; letter-spacing: -0.03em; line-height: 1.2; }
.section-head p { font-size: 15px; color: #6b7280; max-width: 520px; margin: 0 auto; }

.overline {
  display: inline-block; font-size: 11px; text-transform: uppercase;
  letter-spacing: 3px; color: #22C55E; font-weight: 700; margin-bottom: 16px;
}
.overline-light { color: rgba(255,255,255,0.5); }

/* ══════ Hero ══════ */
.hero {
  position: relative; min-height: 100vh;
  display: flex; align-items: center; justify-content: center;
  text-align: center; overflow: hidden;
}
.hero-bg {
  position: absolute; inset: 0;
  background-size: cover; background-position: center;
  transform: scale(1.05);
  animation: heroZoom 8s cubic-bezier(0.16,1,0.3,1) both;
}
@keyframes heroZoom { from { transform: scale(1.2); } to { transform: scale(1.05); } }
.hero::after {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(5,16,8,0.75) 0%, rgba(10,24,18,0.70) 50%, rgba(5,16,8,0.85) 100%);
  z-index: 0;
}
.hero-content { position: relative; z-index: 1; max-width: 800px; padding: 0 24px; }
.hero-logo { margin-bottom: 24px; }
.logo-img { width: 88px; height: 88px; border-radius: 50%; object-fit: cover; box-shadow: 0 0 40px rgba(74,222,128,0.20); }
.hero-badge {
  display: inline-block; padding: 5px 16px;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 20px; font-size: 12px; color: rgba(255,255,255,0.50);
  margin-bottom: 28px; letter-spacing: 1px;
  backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
}
.hero h1 { font-size: clamp(40px, 6vw, 64px); font-weight: 900; color: #fff; margin-bottom: 24px; letter-spacing: -0.04em; line-height: 1.05; }
.hero-accent { color: #4ADE80; }
.hero-desc { font-size: 16px; color: rgba(255,255,255,0.45); max-width: 600px; margin: 0 auto 44px; line-height: 1.8; }
.hero-desc :deep(svg) { opacity: 0.4; vertical-align: -2px; }
.hero-actions { display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; }

.btn-primary-hero {
  display: inline-flex; align-items: center;
  background: #4ADE80; color: #051008; border: none;
  font-size: 15px; padding: 16px 40px; border-radius: 8px;
  font-weight: 700; text-decoration: none;
  box-shadow: 0 4px 24px rgba(74,222,128,0.25);
  transition: all 0.2s cubic-bezier(0.16,1,0.3,1), transform 0.1s cubic-bezier(0.34,1.56,0.64,1);
}
.btn-primary-hero:hover { background: #6EE7A7; box-shadow: 0 8px 32px rgba(74,222,128,0.35); transform: translateY(-2px); }
.btn-primary-hero:active { transform: scale(0.97); }

.btn-outline-hero {
  display: inline-flex; align-items: center;
  background: transparent; color: #fff;
  border: 1px solid rgba(255,255,255,0.15);
  font-size: 15px; padding: 16px 40px; border-radius: 8px;
  font-weight: 600; text-decoration: none;
  backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px);
  transition: all 0.2s;
}
.btn-outline-hero:hover { border-color: rgba(255,255,255,0.35); background: rgba(255,255,255,0.04); }

.hero-scroll-hint {
  position: absolute; bottom: 32px; left: 50%; z-index: 1; transform: translateX(-50%);
}
.hero-scroll-hint span {
  display: block; width: 1px; height: 40px;
  background: linear-gradient(180deg, rgba(255,255,255,0.3), transparent);
  animation: scrollPulse 2s ease-in-out infinite;
}
@keyframes scrollPulse {
  0%, 100% { opacity: 0.3; transform: scaleY(1); }
  50% { opacity: 1; transform: scaleY(1.3); }
}

/* ══════ Pain Point ══════ */
.pain-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 80px; align-items: center; }
.pain-text h2 { font-size: clamp(28px, 4vw, 38px); font-weight: 800; margin: 16px 0 24px; line-height: 1.15; letter-spacing: -0.03em; }
.pain-text p { font-size: 15px; color: #4b5563; line-height: 1.8; margin-bottom: 16px; }
.pain-text b { color: #166534; font-weight: 700; }
.pain-photo {
  height: 480px; border-radius: 20px;
  background-size: cover; background-position: center;
  position: relative; overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.12);
}
.pain-photo-label {
  position: absolute; bottom: 16px; left: 16px;
  padding: 8px 16px; background: rgba(0,0,0,0.55);
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  color: #fff; font-size: 12px; border-radius: 8px; font-weight: 500;
}

/* ══════ Tech Glass Cards ══════ */
.tech-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 48px; }
.tech-glass-card {
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px; padding: 28px 22px;
  transition: all 0.3s cubic-bezier(0.16,1,0.3,1);
  position: relative;
}
.tech-glass-card::before {
  content: ''; position: absolute; inset: -1px;
  border-radius: 16px; padding: 1px;
  background: linear-gradient(135deg, rgba(74,222,128,0.15) 0%, transparent 50%);
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask-composite: exclude; -webkit-mask-composite: xor;
  opacity: 0; transition: opacity 0.3s;
}
.tech-glass-card:hover::before { opacity: 1; }
.tech-glass-card:hover {
  background: rgba(255,255,255,0.10);
  border-color: rgba(255,255,255,0.15);
  transform: translateY(-4px);
}
.tech-glass-icon { margin-bottom: 16px; opacity: 0.6; }
.tech-glass-icon :deep(svg) { color: #4ADE80; }
.tech-glass-card h3 { font-size: 15px; font-weight: 700; color: #fff; margin-bottom: 10px; }
.tech-glass-card p { font-size: 13px; color: rgba(255,255,255,0.45); line-height: 1.7; margin-bottom: 14px; }
.tech-tag {
  display: inline-block; font-size: 10px; color: rgba(255,255,255,0.4);
  background: rgba(255,255,255,0.06); padding: 3px 10px;
  border-radius: 4px; font-weight: 500;
}

/* ══════ Decomposer Cards ══════ */
.decomposer-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; }
.d-card {
  background: #fff; border: 1px solid #e5e7eb;
  border-radius: 16px; overflow: hidden;
  transition: all 0.3s cubic-bezier(0.16,1,0.3,1);
  perspective: 800px;
}
.d-card:hover { transform: translateY(-6px); box-shadow: 0 20px 48px rgba(0,0,0,0.08); border-color: rgba(46,200,93,0.20); }
.d-img-wrap { height: 200px; position: relative; overflow: hidden; }
.d-photo { width: 100%; height: 100%; object-fit: cover; transition: transform 0.6s cubic-bezier(0.16,1,0.3,1); }
.d-card:hover .d-photo { transform: scale(1.06); }
.d-badge-top {
  position: absolute; top: 12px; left: 12px;
  padding: 4px 14px; color: #fff; font-size: 10px;
  border-radius: 20px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
}
.d-body { padding: 22px; }
.d-body h3 { font-size: 15px; font-weight: 700; margin-bottom: 10px; }
.d-body p { font-size: 13px; color: #6b7280; line-height: 1.7; margin-bottom: 14px; }
.d-features { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }
.d-feat { font-size: 11px; color: #166534; background: #DCFCE7; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
.d-meta {
  font-size: 11px; color: #9ca3af;
  display: flex; flex-direction: column; gap: 4px;
  border-top: 1px solid #f3f4f6; padding-top: 14px;
}
.d-meta b { color: #374151; margin-right: 4px; font-weight: 600; }

/* ══════ Workflow ══════ */
.flow-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 32px; }
.flow-step { text-align: center; }
.flow-num-ring {
  width: 44px; height: 44px; border-radius: 50%;
  background: #fff; border: 2px solid #e5e7eb;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 20px;
}
.flow-num { font-size: 16px; font-weight: 800; color: #166534; }
.flow-photo {
  height: 220px; border-radius: 16px; background-size: cover; background-position: center;
  margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}
.flow-step h3 { font-size: 16px; font-weight: 700; margin-bottom: 8px; }
.flow-step p { font-size: 13px; color: #6b7280; line-height: 1.7; }

/* ══════ Machinery Glass Cards ══════ */
.mach-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; margin-top: 48px; }
.m-glass-card {
  background: rgba(255,255,255,0.05);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px; overflow: hidden;
  transition: all 0.3s cubic-bezier(0.16,1,0.3,1);
}
.m-glass-card:hover {
  background: rgba(255,255,255,0.09);
  border-color: rgba(255,255,255,0.14);
  transform: translateY(-4px);
}
.m-glass-card .m-photo { height: 180px; background-size: cover; background-position: center; }
.m-glass-card .m-body { padding: 20px; }
.m-glass-card .m-body h3 { font-size: 15px; font-weight: 700; color: #fff; margin-bottom: 8px; }
.m-glass-card .m-body p { font-size: 13px; color: rgba(255,255,255,0.40); line-height: 1.7; margin-bottom: 14px; }
.m-specs { display: flex; flex-wrap: wrap; gap: 4px 14px; }
.m-spec { font-size: 11px; color: rgba(255,255,255,0.55); }
.m-spec b { color: rgba(255,255,255,0.8); font-weight: 600; }

/* ══════ Data Showcase ══════ */
.data-showcase { display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; margin-top: 24px; }
.data-show-item {
  width: 190px;
  background: #fff;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid #f0f0f0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  transition: transform 0.3s cubic-bezier(0.16,1,0.3,1), box-shadow 0.3s;
  cursor: default;
}
.data-show-item:hover { transform: translateY(-4px); box-shadow: 0 12px 32px rgba(0,0,0,0.08); }
.show-accent { height: 3px; background: var(--accent, #16a34a); }
.show-body {
  display: flex; flex-direction: column; align-items: center;
  padding: 28px 16px 24px; gap: 10px;
}
.show-icon :deep(svg) { color: var(--accent, #16a34a); }
.show-label { font-size: 14px; color: #1f2937; font-weight: 600; text-align: center; line-height: 1.4; }
.show-sub { font-size: 11px; color: #9ca3af; letter-spacing: 0.3px; }

/* ══════ CTA ══════ */
.cta {
  position: relative; padding: 160px 24px; text-align: center;
  background-size: cover; background-position: center; background-attachment: fixed;
  overflow: hidden;
}
.cta-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(5,16,8,0.80) 0%, rgba(10,24,18,0.75) 100%);
  z-index: 0;
}
.cta-content { position: relative; z-index: 1; }
.cta h2 { font-size: clamp(32px, 5vw, 48px); color: #fff; margin-bottom: 16px; font-weight: 900; letter-spacing: -0.03em; }
.cta p { color: rgba(255,255,255,0.45); margin-bottom: 40px; font-size: 17px; }
.cta-sub { margin-top: 24px; font-size: 13px; color: rgba(255,255,255,0.25); }
.cta-sub a { color: #4ADE80; font-weight: 600; }

/* ══════ Footer ══════ */
.footer { padding: 64px 24px 48px; background: #0C1117; }
.footer-inner { max-width: 1120px; margin: 0 auto; }
.footer-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 48px; }
.footer-col b { color: rgba(255,255,255,0.60); display: block; margin-bottom: 12px; font-size: 12px; text-transform: uppercase; letter-spacing: 1.5px; }
.footer-col p { font-size: 13px; line-height: 1.8; color: rgba(255,255,255,0.30); margin: 0; }
.footer-bottom { margin-top: 48px; font-size: 11px; color: rgba(255,255,255,0.15); text-align: center; }

/* ══════ Responsive ══════ */
@media (max-width: 960px) {
  .pain-grid { grid-template-columns: 1fr; gap: 40px; }
  .pain-photo { height: 320px; }
  .decomposer-grid, .tech-grid, .mach-grid { grid-template-columns: 1fr 1fr; }
  .flow-row { grid-template-columns: 1fr 1fr; }
  .footer-grid { grid-template-columns: 1fr 1fr; }
  .section-photo, .section-dark-photo { background-attachment: scroll; }
  .cta { background-attachment: scroll; }
}
@media (max-width: 600px) {
  .hero { min-height: 90vh; }
  .hero h1 { font-size: 32px; }
  .section { padding: 80px 16px; }
  .decomposer-grid, .tech-grid, .flow-row, .mach-grid, .footer-grid { grid-template-columns: 1fr; }
  .hero-actions { flex-direction: column; align-items: center; }
}
</style>
