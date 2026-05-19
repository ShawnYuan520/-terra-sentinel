<template>
  <div class="help-page">
    <!-- 左侧导航 -->
    <aside class="help-sidebar">
      <nav class="sidebar-nav">
        <a v-for="item in navItems" :key="item.key"
           :class="['sidebar-link', { active: activeNav === item.key }]"
           @click="switchNav(item.key)">
          <component :is="item.icon" :size="18" />
          <span>{{ item.label }}</span>
        </a>
      </nav>
      <div class="sidebar-support">
        <div class="support-icon"><HeadphonesIcon :size="28" /></div>
        <h4>需要进一步帮助？</h4>
        <p>我们的支持团队随时为您提供帮助</p>
        <button class="btn-support" @click="showContactModal = true">联系客服</button>
      </div>
    </aside>

    <!-- 主内容区 -->
    <div class="help-main">
      <!-- Hero 搜索区（仅首页显示） -->
      <section v-if="activeNav === 'home'" class="help-hero">
        <div class="hero-bg"></div>
        <div class="hero-inner">
          <h1>您好！需要什么帮助？</h1>
          <p>查找使用指南、教程和常见问题的答案</p>
          <div class="search-bar">
            <Search :size="18" class="search-icon" />
            <input v-model="searchQuery" type="text" placeholder="搜索帮助文档、功能或问题..."
                   @keyup.enter="doSearch" />
            <button class="btn-search" @click="doSearch" :disabled="searching">
              {{ searching ? '搜索中...' : '搜索' }}
            </button>
          </div>
          <div class="hot-tags">
            <span class="hot-label">热门搜索：</span>
            <a v-for="tag in hotTags" :key="tag" class="hot-tag" @click="searchQuery = tag; doSearch()">{{ tag }}</a>
          </div>
        </div>
      </section>

      <!-- 搜索结果 -->
      <section v-if="searchResults.length" class="help-section">
        <div class="section-header">
          <h2>搜索结果 ({{ searchResults.length }})</h2>
          <a class="view-all" @click="clearSearch">清除搜索</a>
        </div>
        <div class="search-results">
          <div v-for="r in searchResults" :key="r.id" class="search-item" @click="openArticle(r)">
            <h4>{{ r.title }}</h4>
            <p v-if="r.summary">{{ r.summary }}</p>
            <div class="search-meta">
              <span class="search-cat">{{ r.category }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- ===== 首页内容 ===== -->
      <template v-if="activeNav === 'home' && !searchResults.length">
        <!-- 快速访问 -->
        <section class="help-section">
          <div class="section-header">
            <h2>快速访问</h2>
          </div>
          <div class="quick-cards">
            <div v-for="card in quickCards" :key="card.title" class="quick-card" @click="switchNav(card.nav)">
              <div class="quick-icon" :style="{ background: card.color + '14', color: card.color }">
                <component :is="card.icon" :size="24" />
              </div>
              <h3>{{ card.title }}</h3>
              <p>{{ card.desc }}</p>
              <a class="card-link" :style="{ color: card.color }">查看指南 →</a>
            </div>
          </div>
        </section>

        <!-- 新手入门 + 常见问题 -->
        <div class="help-bottom">
          <section class="help-section getting-started">
            <h2>新手入门</h2>
            <p class="section-sub">跟随这些步骤快速上手 AgriSpatial 平台</p>
            <div class="steps">
              <div v-for="(step, i) in steps" :key="i" class="step-item">
                <div class="step-num">{{ i + 1 }}</div>
                <h4>{{ step.title }}</h4>
                <p>{{ step.desc }}</p>
              </div>
            </div>
            <div class="steps-connector"></div>
            <div class="btn-center">
              <button class="btn-tutorial" @click="switchNav('quickstart')">查看详细教程</button>
            </div>
          </section>

          <section class="help-section faq-section">
            <div class="faq-header">
              <h2>常见问题</h2>
              <p class="section-sub">浏览用户最常遇到的问题</p>
            </div>
            <div class="faq-list">
              <div v-for="(faq, i) in faqs.slice(0, 5)" :key="i" class="faq-item-wrap">
                <div class="faq-item" @click="toggleFaq(i)">
                  <span>{{ faq.question }}</span>
                  <ChevronDown :size="16" :class="['faq-arrow', { open: openFaq === i }]" />
                </div>
                <div class="faq-answer" v-if="openFaq === i">
                  <p>{{ faq.answer || '暂无详细解答，请联系客服获取帮助。' }}</p>
                </div>
              </div>
            </div>
            <a class="view-all" @click="switchNav('faq')">查看所有常见问题 →</a>
          </section>
        </div>
      </template>

      <!-- ===== 快速入门 ===== -->
      <template v-if="activeNav === 'quickstart' && !searchResults.length">
        <section class="help-section content-page">
          <h2>快速入门</h2>
          <p class="section-sub">5 分钟了解平台核心功能</p>
          <div class="guide-steps">
            <div v-for="(s, i) in quickstartGuide" :key="i" class="guide-item">
              <div class="guide-num">{{ i + 1 }}</div>
              <div class="guide-body">
                <h3>{{ s.title }}</h3>
                <p>{{ s.content }}</p>
                <div v-if="s.tips" class="guide-tips">
                  <div v-for="(tip, j) in s.tips" :key="j" class="tip-item">
                    <CheckCircle :size="14" /> {{ tip }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </template>

      <!-- ===== 功能指南 ===== -->
      <template v-if="activeNav === 'guide' && !searchResults.length">
        <section class="help-section content-page">
          <h2>功能指南</h2>
          <p class="section-sub">各功能的详细操作说明</p>
          <div v-if="loadingArticles" class="loading-state">加载中...</div>
          <div v-else-if="guideArticles.length" class="article-list">
            <div v-for="a in guideArticles" :key="a.id" class="article-item" @click="openArticle(a)">
              <h3>{{ a.title }}</h3>
              <p>{{ a.summary }}</p>
              <div class="article-meta">
                <span class="search-cat">{{ a.category }}</span>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <BookOpen :size="40" />
            <p>暂无功能指南文章</p>
          </div>
        </section>
      </template>

      <!-- ===== 常见问题 ===== -->
      <template v-if="activeNav === 'faq' && !searchResults.length">
        <section class="help-section content-page">
          <h2>常见问题</h2>
          <p class="section-sub">浏览用户最常遇到的问题</p>
          <div v-if="faqs.length" class="faq-full-list">
            <div v-for="(faq, i) in faqs" :key="i" class="faq-item-wrap">
              <div class="faq-item" @click="toggleFaq(i)">
                <span>{{ faq.question }}</span>
                <ChevronDown :size="16" :class="['faq-arrow', { open: openFaq === i }]" />
              </div>
              <div class="faq-answer" v-if="openFaq === i">
                <p>{{ faq.answer || '暂无详细解答，请联系客服获取帮助。' }}</p>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <HelpCircle :size="40" />
            <p>暂无常见问题</p>
          </div>
        </section>
      </template>

      <!-- ===== 视频教程 ===== -->
      <template v-if="activeNav === 'video' && !searchResults.length">
        <section class="help-section content-page">
          <h2>视频教程</h2>
          <p class="section-sub">手把手教你使用平台</p>
          <div class="video-grid">
            <div v-for="(v, i) in videoTutorials" :key="i" class="video-card" @click="openVideo(v)">
              <div class="video-thumb" :style="{ background: v.color }">
                <Play :size="32" />
              </div>
              <div class="video-info">
                <h4>{{ v.title }}</h4>
                <p>{{ v.desc }}</p>
                <span class="video-duration">{{ v.duration }}</span>
              </div>
            </div>
          </div>
        </section>
      </template>

      <!-- ===== 更新日志 ===== -->
      <template v-if="activeNav === 'changelog' && !searchResults.length">
        <section class="help-section content-page">
          <h2>更新日志</h2>
          <p class="section-sub">平台版本更新记录</p>
          <div class="changelog-list">
            <div v-for="(c, i) in changelog" :key="i" class="changelog-item">
              <div class="cl-head">
                <span class="cl-version">{{ c.version }}</span>
                <span class="cl-date">{{ c.date }}</span>
              </div>
              <div class="cl-changes">
                <div v-for="(ch, j) in c.changes" :key="j" class="cl-change">
                  <span :class="['cl-type', ch.type]">{{ ch.type === 'add' ? '新增' : ch.type === 'fix' ? '修复' : '优化' }}</span>
                  {{ ch.desc }}
                </div>
              </div>
            </div>
          </div>
        </section>
      </template>

      <!-- ===== 联系我们 ===== -->
      <template v-if="activeNav === 'contact' && !searchResults.length">
        <section class="help-section content-page">
          <h2>联系我们</h2>
          <p class="section-sub">我们的支持团队随时为您提供帮助</p>
          <div class="contact-grid">
            <div class="contact-card">
              <div class="contact-icon" style="background:#e8f5e9;color:#16a34a"><Phone :size="22" /></div>
              <h4>电话支持</h4>
              <p>400-888-9999</p>
              <span class="contact-time">工作日 9:00 - 18:00</span>
            </div>
            <div class="contact-card">
              <div class="contact-icon" style="background:#e8f0fe;color:#3b82f6"><Mail :size="22" /></div>
              <h4>邮箱支持</h4>
              <p>support@agrispatial.cn</p>
              <span class="contact-time">24 小时内回复</span>
            </div>
            <div class="contact-card">
              <div class="contact-icon" style="background:#fef3c7;color:#d97706"><MessageCircle :size="22" /></div>
              <h4>在线客服</h4>
              <p>工作日 9:00 - 21:00</p>
              <button class="btn-contact" @click="showContactModal = true">开始对话</button>
            </div>
          </div>
          <div class="contact-form-wrap">
            <h3>提交问题反馈</h3>
            <div class="form-group">
              <label>您的姓名</label>
              <input v-model="contactForm.name" placeholder="请输入姓名" />
            </div>
            <div class="form-group">
              <label>联系邮箱</label>
              <input v-model="contactForm.email" type="email" placeholder="请输入邮箱" />
            </div>
            <div class="form-group">
              <label>问题描述</label>
              <textarea v-model="contactForm.message" rows="4" placeholder="请详细描述您遇到的问题..."></textarea>
            </div>
            <button class="btn-green" @click="submitContact" :disabled="!contactForm.message || contactSubmitting">
              {{ contactSubmitting ? '提交中...' : '提交反馈' }}
            </button>
            <span class="action-msg success" v-if="contactSuccess">{{ contactSuccess }}</span>
            <span class="action-msg error" v-if="contactError">{{ contactError }}</span>
          </div>
        </section>
      </template>
    </div>

    <!-- 文章详情弹窗 -->
    <div v-if="showArticleModal" class="modal-overlay" @click.self="closeArticleModal">
      <div class="modal-box article-modal">
        <div class="modal-head">
          <h3>{{ articleDetail?.title || '文章详情' }}</h3>
          <button class="modal-close" @click="closeArticleModal"><X :size="18" /></button>
        </div>
        <div class="modal-body">
          <div v-if="loadingArticle" class="loading-text">加载中...</div>
          <template v-else-if="articleDetail">
            <p v-if="articleDetail.summary" class="article-summary">{{ articleDetail.summary }}</p>
            <div v-if="articleDetail.tags" class="article-tags">
              <span v-for="t in articleDetail.tags.split(',')" :key="t" class="tag-chip">{{ t.trim() }}</span>
            </div>
            <div class="article-content" v-html="renderMarkdown(articleDetail.content || '')"></div>
          </template>
        </div>
      </div>
    </div>

    <!-- 视频播放弹窗 -->
    <div v-if="showVideoModal" class="modal-overlay" @click.self="closeVideoModal">
      <div class="modal-box video-modal">
        <div class="modal-head">
          <h3>{{ currentVideo?.title || '视频教程' }}</h3>
          <button class="modal-close" @click="closeVideoModal"><X :size="18" /></button>
        </div>
        <div class="modal-body">
          <div v-if="currentVideo?.url" class="video-player-wrap">
            <video
              v-if="videoLoaded"
              :src="currentVideo.urlWebm || currentVideo.url"
              controls
              autoplay
              class="video-player"
            ></video>
            <div v-else class="video-start-screen" @click="videoLoaded = true">
              <div class="big-play-btn">
                <Play :size="40" />
              </div>
              <p>点击播放 {{ currentVideo.title }}</p>
              <span>{{ currentVideo.desc }}</span>
            </div>
          </div>
          <div v-else class="video-placeholder">
            <Play :size="48" />
            <p>视频即将上线，敬请期待</p>
            <span>{{ currentVideo?.desc }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 联系客服弹窗 -->
    <div v-if="showContactModal" class="modal-overlay" @click.self="showContactModal = false">
      <div class="modal-box">
        <div class="modal-head">
          <h3>联系客服</h3>
          <button class="modal-close" @click="showContactModal = false"><X :size="18" /></button>
        </div>
        <div class="modal-body">
          <div class="chatbot-placeholder">
            <Bot :size="48" />
            <p>智能客服即将接入...</p>
            <span>您也可以通过电话 400-888-9999 联系我们</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import {
  Home, Rocket, BookOpen, HelpCircle, Video, Clock, Phone,
  Search, Map, ClipboardList, BarChart3, Bot, Download,
  ChevronDown, Headphones as HeadphonesIcon, CheckCircle,
  Play, Mail, MessageCircle, X
} from 'lucide-vue-next'
import api from '../api'

const activeNav = ref('home')
const searchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)
const openFaq = ref(null)
const loadingArticles = ref(false)
const guideArticles = ref([])
const showContactModal = ref(false)
const contactSubmitting = ref(false)
const contactSuccess = ref('')
const contactError = ref('')

const contactForm = ref({ name: '', email: '', message: '' })

// 文章详情弹窗
const showArticleModal = ref(false)
const articleDetail = ref(null)
const loadingArticle = ref(false)

const navItems = [
  { key: 'home', icon: Home, label: '帮助首页' },
  { key: 'quickstart', icon: Rocket, label: '快速入门' },
  { key: 'guide', icon: BookOpen, label: '功能指南' },
  { key: 'faq', icon: HelpCircle, label: '常见问题' },
  { key: 'video', icon: Video, label: '视频教程' },
  { key: 'changelog', icon: Clock, label: '更新日志' },
  { key: 'contact', icon: Phone, label: '联系我们' },
]

const hotTags = ref(['NDVI分析', '田块管理', 'AI分析', '数据导出', '处方图生成'])

const quickCards = [
  { icon: Map, title: '地图操作', desc: '学习如何在地图上浏览、测量和分析农田数据', color: '#16a34a', nav: 'guide' },
  { icon: ClipboardList, title: '田块管理', desc: '创建、编辑和管理您的农田边界和作物信息', color: '#16a34a', nav: 'guide' },
  { icon: BarChart3, title: '数据分析', desc: '使用AI和卫星数据进行智能分析和决策支持', color: '#3b82f6', nav: 'guide' },
  { icon: Bot, title: 'AI助手', desc: '了解如何使用AI助手获得专业的农业建议', color: '#8b5cf6', nav: 'guide' },
  { icon: Download, title: '数据导出', desc: '导出分析结果和报告，支持多种格式', color: '#d97706', nav: 'guide' },
]

const steps = [
  { title: '注册登录', desc: '创建账户并登录到您的工作空间' },
  { title: '添加田块', desc: '在地图上标记您的农田边界' },
  { title: '查看数据', desc: '加载卫星数据查看农田状况' },
  { title: 'AI 分析', desc: '使用AI工具进行智能分析' },
  { title: '导出报告', desc: '生成并导出您的分析报告' },
]

const quickstartGuide = [
  {
    title: '注册并登录',
    content: '访问平台首页，点击"注册"创建新账户。填写用户名、密码和手机号完成注册。已有账户直接登录即可。',
    tips: ['支持手机号注册', '密码至少6位', '登录后自动跳转到地图页面']
  },
  {
    title: '创建您的第一个田块',
    content: '进入地图页面后，点击左侧"新建田块"按钮，在地图上依次点击顶点绘制田块边界。绘制完成后填写田块名称和作物类型。',
    tips: ['鼠标滚轮缩放地图', '点击顶点闭合多边形', '支持玉米、小麦、水稻等作物']
  },
  {
    title: '查看土壤和天气数据',
    content: '选中田块后，系统自动加载该区域的土壤剖面数据（SOC、pH、质地等）和实时天气数据（温度、湿度、降水）。',
    tips: ['点击地图任意位置查询该点数据', '右侧面板查看详细信息', '底部时间轴查看NDVI变化']
  },
  {
    title: '使用 AI 智能分析',
    content: '点击顶栏"AI"进入智能分析页面。选择田块后，可以使用快捷分析按钮或自由提问，AI将综合多源数据给出专业建议。',
    tips: ['支持土壤诊断、碳汇评估、产量预测', '结合卫星遥感数据', '可导出分析报告']
  },
  {
    title: '导出碳汇报告',
    content: '在碳汇页面选择田块，系统自动生成碳汇评估报告。支持PDF格式下载，包含SOC变化趋势、碳汇潜力预测和秸秆还田建议。',
    tips: ['PDF格式一键下载', '包含图表和数据', '适合申报和存档']
  },
]

const faqs = ref([])

const videoTutorials = [
  { title: '平台概览', desc: '了解AgriSpatial的核心功能和界面布局', duration: '5:30', color: '#16a34a', url: '/platform-overview.mp4', urlWebm: '/platform-overview.webm' },
  { title: '田块创建教程', desc: '手把手教你绘制和管理农田边界', duration: '8:15', color: '#3b82f6', url: '' },
  { title: 'AI 分析演示', desc: '使用AI助手进行土壤诊断和碳汇评估', duration: '12:00', color: '#8b5cf6', url: '' },
  { title: '数据导出指南', desc: '如何导出分析报告和原始数据', duration: '4:45', color: '#d97706', url: '' },
  { title: 'NDVI 时序分析', desc: '解读卫星遥感植被指数变化趋势', duration: '7:20', color: '#22c55e', url: '' },
  { title: '碳汇报告生成', desc: '生成并下载完整的碳汇评估PDF报告', duration: '6:10', color: '#16a34a', url: '' },
]
// 视频播放弹窗
const showVideoModal = ref(false)
const currentVideo = ref(null)
const videoLoaded = ref(false)

function openVideo(v) {
  currentVideo.value = v
  videoLoaded.value = false
  showVideoModal.value = true
}

function closeVideoModal() {
  showVideoModal.value = false
  currentVideo.value = null
  videoLoaded.value = false
}

const changelog = [
  {
    version: 'v0.2.0', date: '2026-05-15',
    changes: [
      { type: 'add', desc: 'AI智能分析助手，支持多轮对话' },
      { type: 'add', desc: '碳汇评估与PDF报告导出' },
      { type: 'add', desc: '耕地质量智能评级（AHP+TOPSIS）' },
      { type: 'fix', desc: '修复NDVI时间轴加载慢的问题' },
    ]
  },
  {
    version: 'v0.1.0', date: '2026-04-20',
    changes: [
      { type: 'add', desc: 'GIS地图浏览与田块管理' },
      { type: 'add', desc: '土壤剖面数据查看' },
      { type: 'add', desc: '天气实况与预报' },
      { type: 'add', desc: '腐解剂产品中心' },
      { type: 'optimize', desc: '地图加载性能优化' },
    ]
  },
]

function switchNav(key) {
  activeNav.value = key
  searchResults.value = []
  openFaq.value = null
  if (key === 'guide') loadGuideArticles()
}

async function loadGuideArticles() {
  loadingArticles.value = true
  try {
    const res = await api.get('/help/search', { params: { q: '指南' } })
    guideArticles.value = res.data.items || []
  } catch {
    guideArticles.value = []
  } finally {
    loadingArticles.value = false
  }
}

async function doSearch() {
  const q = searchQuery.value.trim()
  if (!q) return
  searching.value = true
  try {
    const res = await api.get('/help/search', { params: { q } })
    searchResults.value = res.data.items || []
  } catch {
    searchResults.value = []
  } finally {
    searching.value = false
  }
}

function clearSearch() {
  searchResults.value = []
  searchQuery.value = ''
}

async function openArticle(article) {
  showArticleModal.value = true
  loadingArticle.value = true
  articleDetail.value = { title: article.title, summary: article.summary, tags: article.tags, content: '' }
  try {
    const { data } = await api.get(`/knowledge/articles/${article.id}`)
    articleDetail.value = data
  } catch {
    articleDetail.value = { ...articleDetail.value, content: '加载失败，请稍后重试' }
  } finally {
    loadingArticle.value = false
  }
}

function closeArticleModal() {
  showArticleModal.value = false
  articleDetail.value = null
}

function renderMarkdown(md) {
  if (!md) return ''
  return md
    .replace(/^### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
    .replace(/\n{2,}/g, '</p><p>')
    .replace(/\n/g, '<br>')
}

function toggleFaq(i) {
  openFaq.value = openFaq.value === i ? null : i
}

async function submitContact() {
  if (!contactForm.value.message) return
  contactSubmitting.value = true
  contactSuccess.value = ''
  contactError.value = ''
  try {
    await api.post('/help/contact', contactForm.value)
    contactSuccess.value = '感谢您的反馈，我们会尽快联系您！'
    contactForm.value = { name: '', email: '', message: '' }
  } catch {
    contactError.value = '提交失败，请稍后重试'
  } finally {
    contactSubmitting.value = false
  }
}

onMounted(async () => {
  try {
    const res = await api.get('/help/faqs')
    if (res.data.items?.length) {
      faqs.value = res.data.items
    } else {
      faqs.value = [
        { question: '如何导入和管理我的农田数据？', answer: '登录后进入GIS地图页面，点击"新建田块"在地图上绘制田块边界，填写名称和作物类型即可完成田块创建。' },
        { question: 'NDVI指数是什么，如何解读？', answer: 'NDVI（归一化植被指数）是利用卫星遥感数据计算的反映植被生长状况的指标。值越高表示植被越茂盛，0.6以上为旺盛生长期，0.2以下多为裸土。' },
        { question: 'AI分析结果的准确性如何？', answer: 'AI分析基于土壤栅格数据、卫星遥感和气象数据，结合农业专家模型。结果可作为决策参考，实际效果受多种田间因素影响。' },
        { question: '如何生成处方图和作业建议？', answer: '选择田块后，系统自动根据土壤数据、坡度和作物类型生成诊断→处方→预测的完整决策链，包括腐解剂推荐和产量预估。' },
        { question: '支持哪些数据格式导出？', answer: '碳汇报告支持PDF格式下载。土壤数据和遥感数据可通过数据面板查看，更多导出格式持续开发中。' },
      ]
    }
  } catch {
    faqs.value = [
      { question: '如何导入和管理我的农田数据？', answer: '登录后进入GIS地图页面，点击"新建田块"在地图上绘制田块边界，填写名称和作物类型即可完成田块创建。' },
      { question: 'NDVI指数是什么，如何解读？', answer: 'NDVI（归一化植被指数）是利用卫星遥感数据计算的反映植被生长状况的指标。值越高表示植被越茂盛，0.6以上为旺盛生长期，0.2以下多为裸土。' },
      { question: 'AI分析结果的准确性如何？', answer: 'AI分析基于土壤栅格数据、卫星遥感和气象数据，结合农业专家模型。结果可作为决策参考，实际效果受多种田间因素影响。' },
      { question: '如何生成处方图和作业建议？', answer: '选择田块后，系统自动根据土壤数据、坡度和作物类型生成诊断→处方→预测的完整决策链，包括腐解剂推荐和产量预估。' },
      { question: '支持哪些数据格式导出？', answer: '碳汇报告支持PDF格式下载。土壤数据和遥感数据可通过数据面板查看，更多导出格式持续开发中。' },
    ]
  }

  try {
    const res = await api.get('/help/hot-tags')
    if (res.data.tags?.length) hotTags.value = res.data.tags
  } catch {}
})
</script>

<style scoped>
.help-page { display: flex; min-height: 100%; background: #f8faf8; }

/* ═══ Sidebar ═══ */
.help-sidebar {
  width: 220px; flex-shrink: 0; padding: 24px 16px;
  display: flex; flex-direction: column; justify-content: space-between;
  border-right: 1px solid #e8ece8; background: #fff;
  position: sticky; top: 0; height: 100vh; overflow-y: auto;
}
.sidebar-nav { display: flex; flex-direction: column; gap: 2px; }
.sidebar-link {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px; border-radius: 8px;
  font-size: 14px; color: #555; cursor: pointer;
  text-decoration: none; transition: all 0.15s;
}
.sidebar-link:hover { background: #f0f5f0; color: #222; }
.sidebar-link.active { background: #e8f5e9; color: #16a34a; font-weight: 600; }
.sidebar-support {
  background: #f0f9f0; border-radius: 12px; padding: 20px 16px;
  text-align: center; margin-top: 24px;
}
.support-icon {
  width: 48px; height: 48px; border-radius: 50%;
  background: #dcfce7; color: #16a34a;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 12px;
}
.sidebar-support h4 { font-size: 14px; font-weight: 700; color: #1a1a1a; margin-bottom: 4px; }
.sidebar-support p { font-size: 12px; color: #666; margin-bottom: 14px; line-height: 1.5; }
.btn-support {
  width: 100%; padding: 10px; border-radius: 8px; border: none;
  background: #16a34a; color: #fff; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: background 0.15s;
}
.btn-support:hover { background: #15803d; }

/* ═══ Main ═══ */
.help-main { flex: 1; min-width: 0; overflow-y: auto; }

/* Hero */
.help-hero {
  position: relative; padding: 48px 40px 40px;
  background: linear-gradient(135deg, #1a3a2a 0%, #0f2a1a 60%, #162e1e 100%);
  overflow: hidden;
}
.hero-bg {
  position: absolute; inset: 0;
  background: url(/field-bg.jpg) center/cover no-repeat;
  opacity: 0.25;
}
.hero-inner { position: relative; z-index: 1; text-align: center; }
.hero-inner h1 { font-size: 28px; font-weight: 700; color: #fff; margin-bottom: 8px; }
.hero-inner > p { font-size: 15px; color: rgba(255,255,255,0.7); margin-bottom: 24px; }
.search-bar {
  display: flex; align-items: center; max-width: 560px; margin: 0 auto 16px;
  background: #fff; border-radius: 10px; overflow: hidden;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}
.search-icon { margin-left: 14px; color: #999; flex-shrink: 0; }
.search-bar input {
  flex: 1; border: none; outline: none; padding: 14px 12px;
  font-size: 14px; background: transparent; color: #333;
}
.search-bar input::placeholder { color: #aaa; }
.btn-search {
  padding: 14px 28px; background: #16a34a; color: #fff;
  border: none; font-size: 14px; font-weight: 600; cursor: pointer;
  transition: background 0.15s;
}
.btn-search:hover { background: #15803d; }
.btn-search:disabled { opacity: 0.6; cursor: not-allowed; }
.hot-tags { display: flex; align-items: center; justify-content: center; gap: 8px; flex-wrap: wrap; }
.hot-label { font-size: 13px; color: rgba(255,255,255,0.5); }
.hot-tag {
  font-size: 13px; color: rgba(255,255,255,0.75); cursor: pointer;
  padding: 4px 12px; border-radius: 20px;
  background: rgba(255,255,255,0.1); transition: all 0.15s; text-decoration: none;
}
.hot-tag:hover { background: rgba(255,255,255,0.2); color: #fff; }

/* Sections */
.help-section { padding: 32px 40px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.section-header h2, .help-section h2 { font-size: 18px; font-weight: 700; color: #1a1a1a; margin: 0; }
.section-sub { font-size: 13px; color: #888; margin: 4px 0 0; }
.view-all { font-size: 13px; color: #16a34a; text-decoration: none; font-weight: 500; cursor: pointer; }
.view-all:hover { text-decoration: underline; }

/* Quick Cards */
.quick-cards { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; }
.quick-card {
  background: #fff; border: 1px solid #e8ece8; border-radius: 12px;
  padding: 24px 16px; text-align: center; transition: all 0.2s; cursor: pointer;
}
.quick-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.06); transform: translateY(-2px); }
.quick-icon {
  width: 48px; height: 48px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 14px;
}
.quick-card h3 { font-size: 14px; font-weight: 700; color: #1a1a1a; margin-bottom: 6px; }
.quick-card p { font-size: 12px; color: #777; line-height: 1.5; margin-bottom: 12px; }
.card-link { font-size: 13px; font-weight: 500; text-decoration: none; }
.card-link:hover { text-decoration: underline; }

/* Bottom layout */
.help-bottom { display: grid; grid-template-columns: 1.2fr 1fr; gap: 24px; padding: 0 40px 40px; }

/* Getting Started */
.getting-started { padding: 28px; background: #fff; border-radius: 12px; border: 1px solid #e8ece8; position: relative; }
.steps { display: flex; gap: 8px; margin: 24px 0 20px; position: relative; }
.steps-connector {
  position: absolute; top: 38px; left: 60px; right: 60px; height: 2px;
  background: repeating-linear-gradient(90deg, #d4d4d4 0, #d4d4d4 6px, transparent 6px, transparent 12px);
  z-index: 0;
}
.step-item { flex: 1; text-align: center; position: relative; z-index: 1; }
.step-num {
  width: 36px; height: 36px; border-radius: 50%;
  background: #f0f9f0; color: #16a34a; font-weight: 700; font-size: 14px;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 10px; border: 2px solid #dcfce7;
}
.step-item h4 { font-size: 13px; font-weight: 600; color: #1a1a1a; margin-bottom: 4px; }
.step-item p { font-size: 11px; color: #888; line-height: 1.4; }
.btn-center { text-align: center; }
.btn-tutorial {
  padding: 10px 28px; border-radius: 8px; border: none;
  background: #16a34a; color: #fff; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: background 0.15s;
}
.btn-tutorial:hover { background: #15803d; }

/* FAQ */
.faq-section { padding: 28px; background: #fff; border-radius: 12px; border: 1px solid #e8ece8; }
.faq-header { margin-bottom: 16px; }
.faq-list { display: flex; flex-direction: column; }
.faq-item-wrap { border-bottom: 1px solid #f0f0f0; }
.faq-item-wrap:last-child { border-bottom: none; }
.faq-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 0; font-size: 14px; color: #333; cursor: pointer; transition: color 0.15s;
}
.faq-item:hover { color: #16a34a; }
.faq-arrow { color: #999; transition: transform 0.2s; flex-shrink: 0; }
.faq-arrow.open { transform: rotate(180deg); }
.faq-answer { padding: 0 0 14px 0; font-size: 13px; color: #555; line-height: 1.7; }

/* Search results */
.search-results { display: flex; flex-direction: column; gap: 12px; }
.search-item {
  background: #fff; border: 1px solid #e8ece8; border-radius: 10px;
  padding: 16px 20px; cursor: pointer; transition: all 0.15s;
}
.search-item:hover { border-color: #16a34a; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.search-item h4 { font-size: 14px; font-weight: 600; color: #1a1a1a; margin-bottom: 6px; }
.search-item p { font-size: 13px; color: #666; margin-bottom: 8px; }
.search-meta { display: flex; gap: 12px; align-items: center; }
.search-cat { font-size: 11px; color: #16a34a; background: #e8f5e9; padding: 2px 8px; border-radius: 4px; }
.search-views { font-size: 11px; color: #999; }

/* Content pages */
.content-page { max-width: 800px; }
.content-page h2 { margin-bottom: 4px; }

/* Guide steps */
.guide-steps { display: flex; flex-direction: column; gap: 20px; margin-top: 20px; }
.guide-item { display: flex; gap: 16px; background: #fff; border: 1px solid #e8ece8; border-radius: 12px; padding: 20px; }
.guide-num {
  width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0;
  background: #e8f5e9; color: #16a34a; font-weight: 700; font-size: 14px;
  display: flex; align-items: center; justify-content: center;
}
.guide-body h3 { font-size: 15px; font-weight: 700; color: #1a1a1a; margin-bottom: 6px; }
.guide-body p { font-size: 13px; color: #555; line-height: 1.6; margin-bottom: 10px; }
.guide-tips { display: flex; flex-direction: column; gap: 4px; }
.tip-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #16a34a; }
.tip-item :deep(svg) { flex-shrink: 0; }

/* Article list */
.article-list { display: flex; flex-direction: column; gap: 12px; margin-top: 16px; }
.article-item {
  background: #fff; border: 1px solid #e8ece8; border-radius: 10px;
  padding: 16px 20px; cursor: pointer; transition: all 0.15s;
}
.article-item:hover { border-color: #16a34a; }
.article-item h3 { font-size: 14px; font-weight: 600; color: #1a1a1a; margin-bottom: 4px; }
.article-item p { font-size: 13px; color: #666; margin-bottom: 6px; }
.article-meta { display: flex; gap: 12px; font-size: 11px; color: #999; }

/* Video grid */
.video-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 16px; }
.video-card {
  background: #fff; border: 1px solid #e8ece8; border-radius: 12px;
  overflow: hidden; transition: all 0.2s; cursor: pointer;
}
.video-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.06); transform: translateY(-2px); }
.video-thumb {
  height: 120px; display: flex; align-items: center; justify-content: center;
  color: rgba(255,255,255,0.9);
}
.video-info { padding: 14px; }
.video-info h4 { font-size: 13px; font-weight: 700; color: #1a1a1a; margin-bottom: 4px; }
.video-info p { font-size: 12px; color: #777; margin-bottom: 6px; }
.video-duration { font-size: 11px; color: #999; }

/* Changelog */
.changelog-list { display: flex; flex-direction: column; gap: 20px; margin-top: 16px; }
.changelog-item { background: #fff; border: 1px solid #e8ece8; border-radius: 12px; padding: 20px; }
.cl-head { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.cl-version { font-size: 15px; font-weight: 700; color: #16a34a; }
.cl-date { font-size: 12px; color: #999; }
.cl-changes { display: flex; flex-direction: column; gap: 6px; }
.cl-change { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #555; }
.cl-type {
  font-size: 11px; padding: 1px 6px; border-radius: 4px; font-weight: 500; flex-shrink: 0;
}
.cl-type.add { background: #e8f5e9; color: #16a34a; }
.cl-type.fix { background: #fef3c7; color: #d97706; }
.cl-type.optimize { background: #e8f0fe; color: #3b82f6; }

/* Contact */
.contact-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 16px; margin-bottom: 32px; }
.contact-card {
  background: #fff; border: 1px solid #e8ece8; border-radius: 12px;
  padding: 24px; text-align: center;
}
.contact-icon {
  width: 48px; height: 48px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 12px;
}
.contact-card h4 { font-size: 14px; font-weight: 700; color: #1a1a1a; margin-bottom: 4px; }
.contact-card p { font-size: 13px; color: #555; margin-bottom: 4px; }
.contact-time { font-size: 11px; color: #999; }
.btn-contact {
  margin-top: 8px; padding: 8px 20px; border-radius: 8px; border: 1px solid #16a34a;
  background: transparent; color: #16a34a; font-size: 13px; font-weight: 500;
  cursor: pointer; transition: all 0.15s;
}
.btn-contact:hover { background: #16a34a; color: #fff; }

.contact-form-wrap {
  background: #fff; border: 1px solid #e8ece8; border-radius: 12px; padding: 24px;
}
.contact-form-wrap h3 { font-size: 16px; font-weight: 700; color: #1a1a1a; margin-bottom: 16px; }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 13px; font-weight: 500; color: #333; margin-bottom: 6px; }
.form-group input, .form-group textarea {
  width: 100%; padding: 10px 12px; border: 1px solid #e0e0e0; border-radius: 8px;
  font-size: 13px; color: #333; background: #fff; font-family: inherit;
  transition: border-color 0.15s;
}
.form-group input:focus, .form-group textarea:focus { outline: none; border-color: #16a34a; }
.form-group textarea { resize: vertical; }
.btn-green {
  padding: 10px 24px; border-radius: 8px; border: none;
  background: #16a34a; color: #fff; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: background 0.15s;
}
.btn-green:hover { background: #15803d; }
.btn-green:disabled { opacity: 0.5; cursor: not-allowed; }
.action-msg { font-size: 12px; margin-left: 12px; }
.action-msg.success { color: #16a34a; }
.action-msg.error { color: #ef4444; }

/* Empty & loading */
.empty-state {
  text-align: center; padding: 48px; color: #999;
}
.empty-state p { margin-top: 12px; font-size: 14px; }
.loading-state { text-align: center; padding: 48px; color: #999; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal-box {
  background: #fff; border-radius: 16px; width: 420px; max-height: 80vh;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}
.modal-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid #f0f0f0;
}
.modal-head h3 { font-size: 16px; font-weight: 700; color: #1a1a1a; }
.modal-close { background: none; border: none; color: #999; cursor: pointer; padding: 4px; }
.modal-close:hover { color: #333; }
.modal-body { padding: 24px 20px; }
.chatbot-placeholder { text-align: center; color: #999; padding: 20px; }
.chatbot-placeholder p { font-size: 15px; font-weight: 600; color: #333; margin: 12px 0 4px; }
.chatbot-placeholder span { font-size: 12px; }

/* 文章详情弹窗 */
.article-modal { width: 640px; max-width: 90vw; max-height: 80vh; overflow-y: auto; }
.article-summary { color: #666; font-size: 14px; margin-bottom: 12px; line-height: 1.6; }
.article-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; }
.tag-chip { background: #f0fdf4; color: #16a34a; font-size: 12px; padding: 2px 10px; border-radius: 12px; }
.article-content { font-size: 14px; line-height: 1.8; color: #333; }
.article-content h3 { font-size: 16px; font-weight: 700; margin: 20px 0 8px; color: #1a1a1a; }
.article-content h4 { font-size: 14px; font-weight: 700; margin: 16px 0 6px; color: #333; }
.article-content ul { padding-left: 20px; margin: 8px 0; }
.article-content li { margin: 4px 0; }
.article-content strong { color: #16a34a; }
.loading-text { text-align: center; color: #999; padding: 40px; }

/* 视频播放弹窗 */
.video-modal { width: 720px; max-width: 90vw; }
.video-player-wrap { position: relative; width: 100%; }
.video-player { width: 100%; border-radius: 8px; background: #000; }
.video-placeholder {
  text-align: center; color: #999; padding: 60px 20px;
  background: #f9fafb; border-radius: 8px;
}
.video-placeholder p { font-size: 15px; font-weight: 600; color: #333; margin: 12px 0 4px; }
.video-placeholder span { font-size: 13px; color: #666; }

.video-start-screen {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 80px 20px; background: #0f1a14; border-radius: 8px; cursor: pointer;
}
.big-play-btn {
  width: 72px; height: 72px; border-radius: 50%;
  background: #16a34a; color: #fff;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 16px; transition: transform 0.2s, background 0.2s;
}
.big-play-btn :deep(svg) { margin-left: 3px; }
.video-start-screen:hover .big-play-btn { transform: scale(1.1); background: #15803d; }
.video-start-screen p { font-size: 16px; font-weight: 600; color: #fff; margin-bottom: 4px; }
.video-start-screen span { font-size: 13px; color: rgba(255,255,255,0.6); }

/* Responsive */
@media (max-width: 1024px) {
  .quick-cards { grid-template-columns: repeat(3, 1fr); }
  .help-bottom { grid-template-columns: 1fr; }
  .video-grid { grid-template-columns: repeat(2, 1fr); }
  .contact-grid { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .help-page { flex-direction: column; }
  .help-sidebar { width: 100%; flex-direction: row; overflow-x: auto; padding: 12px; border-right: none; border-bottom: 1px solid #e8ece8; }
  .sidebar-nav { flex-direction: row; gap: 4px; }
  .sidebar-support { display: none; }
  .quick-cards { grid-template-columns: repeat(2, 1fr); }
  .help-hero, .help-section, .help-bottom { padding-left: 20px; padding-right: 20px; }
}
</style>
