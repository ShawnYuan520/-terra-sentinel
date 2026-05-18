import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  { path: '/register', name: 'Register', component: () => import('../views/Register.vue') },
  // 首页 — 展示页（无需登录）
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
  // GIS 平台 — 带侧边栏
  {
    path: '/map',
    component: () => import('../views/Layout.vue'),
    children: [
      { path: '', name: 'MapView', component: () => import('../views/MapView.vue') },
      { path: 'dashboard', name: 'DataDashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'products', name: 'Products', component: () => import('../views/Products.vue') },
      { path: 'knowledge', name: 'Knowledge', component: () => import('../views/Knowledge.vue') },
      { path: 'ai', name: 'AIAssistant', component: () => import('../views/AIAssistant.vue') },
      { path: 'soil', name: 'Soil', component: () => import('../views/Soil.vue') },
      { path: 'carbon', name: 'Carbon', component: () => import('../views/Carbon.vue') },
      { path: 'settings', name: 'Settings', component: () => import('../views/Settings.vue') },
      { path: 'help', name: 'Help', component: () => import('../views/Help.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }
  if (token && to.meta.requiresAuth) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      if (payload.exp && payload.exp * 1000 < Date.now()) {
        localStorage.removeItem('token')
        next('/login')
        return
      }
    } catch {
      localStorage.removeItem('token')
      next('/login')
      return
    }
  }
  if ((to.path === '/login' || to.path === '/register') && token) {
    next('/')
  } else {
    next()
  }
})

export default router
