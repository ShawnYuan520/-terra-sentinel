<template>
  <div class="know-page">
    <!-- Hero 搜索区 -->
    <div class="know-hero">
      <div class="hero-inner">
        <h1>农业知识中心</h1>
        <p class="hero-desc">快速获取秸秆还田、腐解剂使用、农机操作专业指导</p>
        <div class="search-box">
          <Search :size="18" class="search-icon" />
          <input
            v-model="searchQuery"
            class="search-input"
            placeholder="搜索农业问题，例如：秸秆腐解剂怎么使用？"
          />
        </div>
      </div>
    </div>

    <div class="know-container">
      <!-- 热门问题 -->
      <section class="know-section">
        <h2 class="section-title"><Flame :size="18" /> 热门问题</h2>
        <div class="hot-grid">
          <button v-for="q in hotQuestions" :key="q" class="hot-card" @click="searchQuery = q">
            <HelpCircle :size="16" class="hot-icon" />
            <span>{{ q }}</span>
          </button>
        </div>
      </section>

      <!-- 分类入口 -->
      <section class="know-section">
        <h2 class="section-title"><Grid3X3 :size="18" /> 知识分类</h2>
        <div class="cat-grid">
          <button v-for="c in categories" :key="c.key" :class="['cat-card', { active: activeCategory === c.key }]" @click="activeCategory = activeCategory === c.key ? '' : c.key">
            <div class="cat-icon" :style="{ background: c.bg, color: c.color }">
              <component :is="c.icon" :size="22" />
            </div>
            <span class="cat-label">{{ c.label }}</span>
            <span class="cat-count">{{ c.count }} 篇</span>
          </button>
        </div>
      </section>

      <!-- 文章列表 -->
      <section class="know-section">
        <div class="section-head">
          <h2 class="section-title"><BookOpen :size="18" /> {{ activeCategory ? '分类文章' : '推荐知识' }}</h2>
          <button v-if="activeCategory" class="btn btn-ghost btn-sm" @click="activeCategory = ''">查看全部</button>
        </div>

        <div class="article-grid" v-if="displayArticles.length">
          <div v-for="a in displayArticles" :key="a.id" class="article-card" @click="showArticle(a)">
            <div class="article-top">
              <span :class="['badge', 'badge-info']">{{ categoryLabel(a.category) }}</span>
              <span class="article-date" v-if="a.publish_time">{{ a.publish_time?.slice(0, 10) }}</span>
            </div>
            <h3 class="article-title">{{ a.title }}</h3>
            <p class="article-summary" v-if="a.summary">{{ a.summary }}</p>
            <div class="article-tags" v-if="a.tags_list?.length">
              <span v-for="t in a.tags_list" :key="t" class="tag">#{{ t }}</span>
            </div>
            <div class="article-meta">
              <span><Eye :size="12" /> {{ a.views || 0 }}</span>
              <span><Clock :size="12" /> {{ a.publish_time?.slice(0, 10) || '—' }}</span>
            </div>
          </div>
        </div>

        <div v-else class="empty-state">
          <FileSearch :size="40" style="opacity:0.2" />
          <p>暂无相关文章</p>
        </div>
      </section>
    </div>

    <!-- 浮动 AI 助手按钮 -->
    <button class="ai-fab" @click="aiOpen = !aiOpen" :title="aiOpen ? '关闭' : 'AI 农业助手'">
      <Bot :size="24" />
    </button>

    <!-- AI 快速问答浮窗 -->
    <div class="ai-popup" v-if="aiOpen">
      <div class="ai-popup-head">
        <Bot :size="16" /> AI 农业助手
        <button class="ai-popup-close" @click="aiOpen = false"><X :size="16" /></button>
      </div>
      <div class="ai-popup-body">
        <p class="ai-popup-hint">输入农业问题，AI 将为你推荐相关知识</p>
        <div class="ai-popup-input">
          <input v-model="aiQuery" placeholder="例如：腐解剂什么时候喷？" @keyup.enter="askAI" />
          <button @click="askAI" :disabled="!aiQuery.trim()">提问</button>
        </div>
        <div class="ai-popup-answer" v-if="aiAnswer">
          <div v-html="formatReply(aiAnswer)"></div>
        </div>
      </div>
    </div>

    <Dialog :visible="!!selectedArticle" :title="selectedArticle?.title" @close="selectedArticle = null" width="640px">
      <div style="line-height:1.8;white-space:pre-wrap">{{ selectedArticle?.content }}</div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'
import Dialog from '../components/Dialog.vue'
import {
  Search, Flame, HelpCircle, Grid3X3, BookOpen, Eye, Clock, FileSearch,
  Bot, X, Tractor, Wheat, Satellite, Sprout, TrendingUp, FileText,
  MessageCircle, GraduationCap, Folder,
} from 'lucide-vue-next'

const articles = ref([])
const activeCategory = ref('')
const selectedArticle = ref(null)
const searchQuery = ref('')
const aiOpen = ref(false)
const aiQuery = ref('')
const aiAnswer = ref('')
const aiLoading = ref(false)

const hotQuestions = ref([])
const categories = ref([])

const iconMap = {
  BookOpen, FileText, MessageCircle, GraduationCap, Folder, Tractor, Wheat, Satellite, Sprout, TrendingUp,
}
const iconColorMap = {
  usage_guide: { bg: 'rgba(34,197,94,0.08)', color: '#22C55E', icon: BookOpen },
  policy: { bg: 'rgba(239,68,68,0.08)', color: '#EF4444', icon: FileText },
  faq: { bg: 'rgba(245,158,11,0.08)', color: '#F59E0B', icon: MessageCircle },
  tutorial: { bg: 'rgba(59,130,246,0.08)', color: '#3B82F6', icon: GraduationCap },
  general: { bg: 'rgba(139,92,246,0.08)', color: '#8B5CF6', icon: Folder },
}

function categoryLabel(key) {
  const map = { usage_guide: '使用指南', policy: '政策解读', faq: '常见问题', tutorial: '新手教程', general: '综合' }
  return map[key] || key || '其他'
}

const displayArticles = computed(() => {
  let list = articles.value
  if (activeCategory.value) {
    list = list.filter(a => a.category === activeCategory.value)
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(a => a.title?.toLowerCase().includes(q) || a.content?.toLowerCase().includes(q))
  }
  return list
})

onMounted(async () => {
  try {
    const [artRes, catRes, hotRes] = await Promise.all([
      api.get('/knowledge/articles'),
      api.get('/knowledge/categories'),
      api.get('/knowledge/hot-questions'),
    ])
    articles.value = artRes.data?.items || []
    hotQuestions.value = hotRes.data?.questions || []
    const apiCategories = catRes.data?.categories || []
    categories.value = apiCategories.map(c => ({
      ...c,
      bg: iconColorMap[c.key]?.bg || 'rgba(100,116,139,0.08)',
      color: iconColorMap[c.key]?.color || '#64748B',
      icon: iconColorMap[c.key]?.icon || Folder,
    }))
  } catch {}
})

async function showArticle(a) {
  try {
    const { data } = await api.get(`/knowledge/articles/${a.id}`)
    selectedArticle.value = data || a
  } catch {
    selectedArticle.value = a
  }
}

async function askAI() {
  if (!aiQuery.value.trim() || aiLoading.value) return
  aiLoading.value = true
  aiAnswer.value = ''
  try {
    const { data } = await api.post('/agent/chat', { message: aiQuery.value, field_id: null })
    aiAnswer.value = data?.reply || '抱歉，暂时无法回答您的问题'
  } catch {
    aiAnswer.value = 'AI服务暂时不可用，请稍后再试'
  } finally {
    aiLoading.value = false
  }
}

async function searchArticles() {
  if (!searchQuery.value.trim()) {
    onMounted()
    return
  }
  try {
    const { data } = await api.get('/knowledge/articles', { params: { q: searchQuery.value.trim() } })
    articles.value = data?.items || []
  } catch {}
}

function formatReply(text) {
  if (!text) return ''
  const escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  return escaped.replace(/\n/g, '<br>').replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
}
</script>

<style scoped>
.know-page { min-height: 100vh; overflow-y: auto; background: #F7F8F5; color: var(--surface-900); }

/* Hero */
.know-hero {
  background: linear-gradient(135deg, var(--color-primary-50) 0%, #F7F8F5 50%, var(--surface-50) 100%);
  padding: var(--space-10) var(--space-6) var(--space-8);
  border-bottom: 1px solid var(--surface-200);
}
.hero-inner { max-width: 640px; margin: 0 auto; text-align: center; }
.know-hero h1 { font-size: var(--text-3xl); font-weight: var(--weight-bold); letter-spacing: var(--tracking-tight); margin-bottom: var(--space-2); }
.hero-desc { font-size: var(--text-base); color: var(--surface-700); margin-bottom: var(--space-6); }
.search-box {
  display: flex; align-items: center; gap: 10px;
  background: var(--surface-0); border: 1px solid var(--surface-200);
  border-radius: var(--radius-full); padding: 6px 6px 6px 20px;
  box-shadow: var(--shadow-sm);
  transition: border-color var(--duration-fast), box-shadow var(--duration-fast);
}
.search-box:focus-within { border-color: var(--color-primary-300); box-shadow: var(--shadow-glow-md); }
.search-icon { color: var(--surface-700); flex-shrink: 0; }
.search-input {
  flex: 1; border: none; outline: none; background: none;
  font-size: var(--text-base); color: var(--surface-900);
  height: 44px;
}
.search-input::placeholder { color: var(--surface-700); }

/* Container */
.know-container { max-width: 1000px; margin: 0 auto; padding: var(--space-6); }

/* Section */
.know-section { margin-bottom: var(--space-8); }
.section-title {
  display: flex; align-items: center; gap: 8px;
  font-size: var(--text-lg); font-weight: var(--weight-bold);
  margin-bottom: var(--space-4); color: var(--surface-900);
}
.section-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-4); }
.section-head .section-title { margin-bottom: 0; }

/* Hot Questions */
.hot-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-3); }
.hot-card {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 16px; border-radius: var(--radius-md);
  background: var(--surface-0); border: 1px solid var(--surface-200);
  cursor: pointer; text-align: left;
  font-size: var(--text-sm); color: var(--surface-800);
  transition: all var(--duration-fast) var(--ease-out);
}
.hot-card:hover { border-color: var(--color-primary-300); box-shadow: var(--shadow-md); transform: translateY(-1px); }
.hot-icon { color: var(--color-primary-300); flex-shrink: 0; }

/* Categories */
.cat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-3); }
.cat-card {
  display: flex; flex-direction: column; align-items: center; gap: var(--space-2);
  padding: var(--space-5); border-radius: var(--radius-md);
  background: var(--surface-0); border: 1px solid var(--surface-200);
  cursor: pointer; transition: all var(--duration-fast) var(--ease-out);
}
.cat-card:hover { border-color: var(--color-primary-300); box-shadow: var(--shadow-md); transform: translateY(-2px); }
.cat-card.active { border-color: var(--color-primary); background: var(--color-primary-50); }
.cat-icon {
  width: 52px; height: 52px; border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
}
.cat-label { font-size: var(--text-sm); font-weight: var(--weight-semibold); color: var(--surface-900); }
.cat-count { font-size: 11px; color: var(--surface-700); }

/* Articles */
.article-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--space-4); }
.article-card {
  background: var(--surface-0); border: 1px solid var(--surface-200);
  border-radius: var(--radius-md); padding: var(--space-5);
  cursor: pointer; transition: all var(--duration-normal) var(--ease-out);
  display: flex; flex-direction: column; gap: var(--space-2);
}
.article-card:hover { border-color: var(--color-primary-300); box-shadow: var(--shadow-md); transform: translateY(-2px); }
.article-top { display: flex; justify-content: space-between; align-items: center; }
.article-date { font-size: 11px; color: var(--surface-700); }
.article-title { font-size: var(--text-base); font-weight: var(--weight-semibold); color: var(--surface-900); line-height: var(--leading-snug); }
.article-summary { font-size: var(--text-sm); color: var(--surface-700); line-height: var(--leading-relaxed); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.article-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tag {
  font-size: 11px; padding: 2px 8px; border-radius: var(--radius-xs);
  background: var(--color-primary-50); color: var(--color-primary-300);
  font-weight: var(--weight-medium);
}
.article-meta { display: flex; gap: var(--space-4); font-size: 11px; color: var(--surface-700); margin-top: auto; padding-top: var(--space-2); }

/* Empty */
.empty-state { text-align: center; padding: var(--space-12); display: flex; flex-direction: column; align-items: center; gap: var(--space-3); color: var(--surface-700); }

/* AI FAB */
.ai-fab {
  position: fixed; bottom: 28px; right: 28px;
  width: 56px; height: 56px; border-radius: 50%;
  background: var(--color-primary); border: none; color: #fff;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 20px rgba(46,200,93,0.30);
  transition: all var(--duration-fast);
  z-index: 100;
}
.ai-fab:hover { transform: scale(1.08); box-shadow: 0 6px 28px rgba(46,200,93,0.40); }

/* AI Popup */
.ai-popup {
  position: fixed; bottom: 96px; right: 28px;
  width: 360px; border-radius: var(--radius-lg);
  background: var(--surface-0); border: 1px solid var(--surface-200);
  box-shadow: var(--shadow-xl); z-index: 101;
  overflow: hidden;
  animation: fadeInUp var(--duration-normal) var(--ease-out);
}
.ai-popup-head {
  display: flex; align-items: center; gap: 8px;
  padding: 14px 16px; font-size: var(--text-sm); font-weight: var(--weight-semibold);
  background: var(--color-primary-50); color: var(--surface-900);
  border-bottom: 1px solid var(--surface-200);
}
.ai-popup-close { margin-left: auto; background: none; border: none; cursor: pointer; color: var(--surface-700); padding: 2px; }
.ai-popup-body { padding: 16px; }
.ai-popup-hint { font-size: var(--text-xs); color: var(--surface-700); margin-bottom: 12px; }
.ai-popup-input { display: flex; gap: 8px; margin-bottom: 12px; }
.ai-popup-input input {
  flex: 1; padding: 8px 12px; border: 1px solid var(--surface-200);
  border-radius: var(--radius-sm); font-size: var(--text-sm); outline: none;
}
.ai-popup-input input:focus { border-color: var(--color-primary-300); }
.ai-popup-input button {
  padding: 8px 16px; border-radius: var(--radius-sm);
  background: var(--color-primary); color: #fff; border: none;
  font-size: var(--text-sm); cursor: pointer;
}
.ai-popup-input button:disabled { opacity: 0.5; cursor: not-allowed; }
.ai-popup-answer {
  padding: 12px; background: var(--surface-50); border-radius: var(--radius-sm);
  font-size: var(--text-sm); color: var(--surface-800); line-height: var(--leading-relaxed);
}

@keyframes fadeInUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

@media (max-width: 768px) {
  .hot-grid { grid-template-columns: 1fr; }
  .cat-grid { grid-template-columns: repeat(2, 1fr); }
  .article-grid { grid-template-columns: 1fr; }
  .ai-popup { right: 16px; left: 16px; width: auto; }
}
</style>
