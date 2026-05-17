import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5174,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  },
  build: {
    target: 'es2020',
    rollupOptions: {
      output: {
        manualChunks: {
          // 地图引擎 (157KB) — 仅在 MapView 使用时加载
          leaflet: ['leaflet'],
          // 图表引擎 (1MB) — 仅在 Dashboard/Soil 使用时加载
          echarts: ['echarts'],
          // Vue 核心 — 所有页面共享
          vendor: ['vue', 'vue-router'],
        },
      },
    },
    // 提高 chunk 大小警告阈值
    chunkSizeWarningLimit: 800,
  },
})
