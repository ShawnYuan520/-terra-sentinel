import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'https://yuanxinke-agrispatial-backend.hf.space/api/v1',
  timeout: 15000,
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      // GET 请求不跳转登录页（公开浏览模式）
      if (err.config?.method !== 'get') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

// ── 请求去重 + 响应缓存 ──
const pending = new Map()   // key → Promise (进行中去重)
const cache = new Map()     // key → { data, ts, ttl }

function makeKey(url, params) {
  return `${url}|${JSON.stringify(params || {})}`
}

// 路由级缓存TTL (毫秒)
const TTL = {
  '/fields': 3000,
  '/raster/soil-profile': 60000,
  '/raster/decision': 30000,
  '/weather/current': 60000,
  '/weather/forecast': 300000,
  '/weather/agricultural': 300000,
  '/geo/ndvi': 120000,
  '/geo/landcover': 300000,
  '/raster/list': 300000,
}

function getTTL(url) {
  for (const [k, v] of Object.entries(TTL)) {
    if (url.includes(k)) return v
  }
  return 0
}

// 包装 GET 请求，自动去重和缓存
async function cachedGet(url, config = {}) {
  const params = config.params
  const key = makeKey(url, params)
  const ttl = getTTL(url)

  // 1. 响应缓存命中
  if (ttl > 0) {
    const entry = cache.get(key)
    if (entry && Date.now() - entry.ts < ttl) {
      return { data: entry.data, status: 200, cached: true }
    }
  }

  // 2. 请求去重：相同请求复用进行中的Promise
  if (pending.has(key)) {
    return pending.get(key)
  }

  // 3. 发起请求
  const promise = api.get(url, config)
    .then(res => {
      pending.delete(key)
      if (ttl > 0 && res.status === 200) {
        cache.set(key, { data: res.data, ts: Date.now() })
      }
      return res
    })
    .catch(err => {
      pending.delete(key)
      throw err
    })

  pending.set(key, promise)
  return promise
}

// 挂载到 api 实例
api.cachedGet = cachedGet

export default api
